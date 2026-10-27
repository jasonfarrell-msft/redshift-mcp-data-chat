"""Memory-only ACA system identity -> AWS STS credential_process.

Claim comparisons are defense in depth, NOT JWT signature verification. STS
verifies the signed token against the exact OIDC provider and role trust.
Never use DefaultAzureCredential or an operator/shared AWS credential chain.
"""

import base64
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

TENANT = "e90bd921-0e00-4e6f-b87c-713670ee27bf"
REGION = "us-east-2"
ROLE = "arn:aws:iam::684925376801:role/RedshiftAzureOfficialMcpRole"
APP_ROLE = "Redshift.ReadOnly"
# The approved role permits one hour. Fifteen-minute sessions fall immediately
# inside botocore's fifteen-minute advisory refresh window on every API call.
SESSION_DURATION_SECONDS = 3600


class FederationError(Exception):
    """Fixed classification only; never carry provider exception text."""


def require(condition, code):
    if not condition:
        raise FederationError(code)


def guid(value):
    try:
        require(str(UUID(value)) == value, "configuration_invalid")
    except (ValueError, TypeError, AttributeError):
        raise FederationError("configuration_invalid") from None
    return value


@dataclass(frozen=True)
class Settings:
    resource_app: str
    client_id: str
    principal_id: str
    issuer: str
    audience: str
    subject: str
    version: str
    role: str = ROLE
    region: str = REGION

    @classmethod
    def from_env(cls, env=None):
        env = os.environ if env is None else env
        try:
            require(env["REDSHIFT_AZURE_TENANT_ID"] == TENANT, "configuration_invalid")
            require(env["REDSHIFT_AWS_ROLE_ARN"] == ROLE, "configuration_invalid")
            require(env["AWS_REGION"] == REGION, "configuration_invalid")
            resource = guid(env["REDSHIFT_AZURE_RESOURCE_APP_ID"])
            issuer = env["REDSHIFT_AWS_OIDC_ISSUER"]
            if issuer == f"https://login.microsoftonline.com/{TENANT}/v2.0":
                version, audience = "2.0", resource
            elif issuer == f"https://sts.windows.net/{TENANT}/":
                version, audience = "1.0", f"api://{resource}"
            else:
                raise FederationError("configuration_invalid")
            require(env["REDSHIFT_AWS_OIDC_AUDIENCE"] == audience, "configuration_invalid")
            subject = env["REDSHIFT_AWS_OIDC_SUBJECT"]
            require(bool(re.fullmatch(r"[A-Za-z0-9._-]{1,256}", subject)),
                    "configuration_invalid")
            return cls(resource, guid(env["REDSHIFT_AZURE_MI_CLIENT_ID"]),
                       guid(env["REDSHIFT_AZURE_MI_PRINCIPAL_ID"]),
                       issuer, audience, subject, version)
        except KeyError:
            raise FederationError("configuration_missing") from None


def token_claims(token):
    try:
        require(isinstance(token, str) and len(token) <= 32768, "token_invalid")
        pieces = token.split(".")
        require(len(pieces) == 3 and all(pieces), "token_invalid")
        claims = json.loads(base64.urlsafe_b64decode(pieces[1] + "=" * (-len(pieces[1]) % 4)))
        require(isinstance(claims, dict), "token_invalid")
        return claims
    except (ValueError, UnicodeError, TypeError):
        raise FederationError("token_invalid") from None


def validate_claims(token, settings, *, now=None, inspect=False):
    now = time.time() if now is None else now
    claims = token_claims(token)
    expected = {"tid": TENANT, "iss": settings.issuer, "aud": settings.audience,
                "ver": settings.version, "oid": settings.principal_id,
                "azp" if settings.version == "2.0" else "appid": settings.client_id}
    require(all(claims.get(k) == v for k, v in expected.items()), "identity_mismatch")
    require(claims.get("roles") == [APP_ROLE], "assignment_mismatch")
    require(isinstance(claims.get("sub"), str) and
            bool(re.fullmatch(r"[A-Za-z0-9._-]{1,256}", claims["sub"])), "identity_mismatch")
    require(inspect or claims["sub"] == settings.subject, "identity_mismatch")
    require(all(type(claims.get(k)) is int for k in ("exp", "nbf", "iat")), "token_invalid")
    require(claims["nbf"] <= now + 30 and claims["iat"] <= now + 30 and
            now + 120 < claims["exp"] <= now + 90000, "token_expired")
    return {k: claims[k] for k in (*expected, "sub", "exp", "nbf", "iat")}


def acquire_token(settings):
    # No client_id: select the candidate's SYSTEM identity, not registry pull UMI.
    # These are ACA platform-injected endpoint credentials; no VM/CLI fallback.
    require(bool(os.environ.get("IDENTITY_ENDPOINT")) and
            bool(os.environ.get("IDENTITY_HEADER")), "aca_identity_unavailable")
    try:
        from azure.identity import ManagedIdentityCredential

        with ManagedIdentityCredential() as identity:
            return identity.get_token(f"api://{settings.resource_app}/.default").token
    except Exception:
        raise FederationError("azure_identity_failed") from None


def exchange(settings, token, *, client=None, now=None):
    validate_claims(token, settings, now=now)
    try:
        if client is None:
            import boto3
            from botocore import UNSIGNED
            from botocore.config import Config

            client = boto3.client(
                "sts", region_name=REGION,
                endpoint_url=f"https://sts.{REGION}.amazonaws.com",
                aws_access_key_id="unsigned", aws_secret_access_key="unsigned",
                config=Config(signature_version=UNSIGNED, connect_timeout=3,
                              read_timeout=10, retries={"total_max_attempts": 2}),
            )
        response = client.assume_role_with_web_identity(
            RoleArn=ROLE, RoleSessionName="redshift-aca-runtime", WebIdentityToken=token,
            DurationSeconds=SESSION_DURATION_SECONDS,
        )
    except Exception:
        raise FederationError("sts_exchange_failed") from None
    try:
        credentials = response["Credentials"]
        expiration = credentials["Expiration"]
        require(isinstance(expiration, datetime) and expiration.tzinfo is not None,
                "sts_response_invalid")
        instant = time.time() if now is None else now
        require(instant + SESSION_DURATION_SECONDS - 60 < expiration.timestamp()
                <= instant + SESSION_DURATION_SECONDS + 60,
                "sts_response_invalid")
        require(response["AssumedRoleUser"]["Arn"] ==
                "arn:aws:sts::684925376801:assumed-role/RedshiftAzureOfficialMcpRole/"
                "redshift-aca-runtime", "sts_response_invalid")
        require(all(isinstance(credentials.get(k), str) and credentials[k] and
                    len(credentials[k]) <= 16384
                    for k in ("AccessKeyId", "SecretAccessKey", "SessionToken")),
                "sts_response_invalid")
        return {"Version": 1, **{k: credentials[k] for k in
                                ("AccessKeyId", "SecretAccessKey", "SessionToken")},
                "Expiration": expiration.astimezone(UTC).isoformat()}
    except (KeyError, TypeError, AttributeError):
        raise FederationError("sts_response_invalid") from None


def main(argv=None):
    logging.disable(logging.CRITICAL)
    args = sys.argv[1:] if argv is None else argv
    try:
        require(args in ([], ["--inspect-claims"]), "arguments_invalid")
        settings = Settings.from_env()
        token = acquire_token(settings)
        if args:
            # Bootstrap only: selected nonsecret claims; never the encoded JWT.
            result = validate_claims(token, settings, inspect=True)
        else:
            result = exchange(settings, token)
        print(json.dumps(result, separators=(",", ":")))
        return 0
    except FederationError as exc:
        print(f"AWS federation unavailable: {exc}", file=sys.stderr)
        return 1
    except Exception:
        print("AWS federation unavailable: internal_failure", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
