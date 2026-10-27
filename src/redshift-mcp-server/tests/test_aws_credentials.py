import base64
import io
import json
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest

from redshift_mcp_server import aws_credentials as auth

NOW = 1800000000
APP = "11111111-1111-4111-8111-111111111111"
CLIENT = "22222222-2222-4222-8222-222222222222"
PRINCIPAL = "33333333-3333-4333-8333-333333333333"
SETTINGS = auth.Settings(APP, CLIENT, PRINCIPAL,
                         f"https://login.microsoftonline.com/{auth.TENANT}/v2.0",
                         APP, "real-pairwise-subject", "2.0")


def claims(**changes):
    value = {"tid": auth.TENANT, "iss": SETTINGS.issuer, "aud": APP, "ver": "2.0",
             "oid": PRINCIPAL, "azp": CLIENT, "sub": SETTINGS.subject,
             "roles": ["Redshift.ReadOnly"], "iat": NOW - 10, "nbf": NOW - 10,
             "exp": NOW + 3600}
    value.update(changes)
    return value


def token(**changes):
    encoded = base64.urlsafe_b64encode(json.dumps(claims(**changes)).encode()).decode().rstrip("=")
    return f"header.{encoded}.signature"


def env():
    return {"REDSHIFT_AZURE_TENANT_ID": auth.TENANT, "REDSHIFT_AWS_ROLE_ARN": auth.ROLE,
            "AWS_REGION": auth.REGION, "REDSHIFT_AZURE_RESOURCE_APP_ID": APP,
            "REDSHIFT_AZURE_MI_CLIENT_ID": CLIENT, "REDSHIFT_AZURE_MI_PRINCIPAL_ID": PRINCIPAL,
            "REDSHIFT_AWS_OIDC_ISSUER": SETTINGS.issuer,
            "REDSHIFT_AWS_OIDC_AUDIENCE": APP, "REDSHIFT_AWS_OIDC_SUBJECT": SETTINGS.subject}


def response():
    return {"Credentials": {"AccessKeyId": "temporary-access",
                            "SecretAccessKey": "temporary-secret",
                            "SessionToken": "temporary-session",
                            "Expiration": datetime.fromtimestamp(NOW + 3600, UTC)},
            "AssumedRoleUser": {"Arn": "arn:aws:sts::684925376801:assumed-role/"
                                      "RedshiftAzureOfficialMcpRole/redshift-aca-runtime"}}


def test_pinned_settings():
    assert auth.Settings.from_env(env()) == SETTINGS


@pytest.mark.parametrize("name,value", [
    ("REDSHIFT_AZURE_TENANT_ID", APP), ("AWS_REGION", "us-east-1"),
    ("REDSHIFT_AWS_ROLE_ARN", "arn:aws:iam::684925376801:role/RedshiftOgeMcpTaskRole"),
    ("REDSHIFT_AZURE_MI_CLIENT_ID", "bad"), ("REDSHIFT_AWS_OIDC_SUBJECT", "*"),
    ("REDSHIFT_AWS_OIDC_AUDIENCE", "https://management.azure.com"),
    ("REDSHIFT_AWS_OIDC_ISSUER", "https://attacker.invalid"),
])
def test_configuration_rejects_drift(name, value):
    values = env()
    values[name] = value
    with pytest.raises(auth.FederationError):
        auth.Settings.from_env(values)


@pytest.mark.parametrize("changes", [
    {"tid": APP}, {"aud": CLIENT}, {"oid": APP}, {"azp": APP}, {"sub": PRINCIPAL},
    {"iss": "https://attacker.invalid"}, {"ver": "1.0"}, {"roles": []},
    {"roles": ["Redshift.ReadOnly", "Other"]}, {"exp": NOW + 60},
    {"exp": True}, {"nbf": NOW + 100}, {"iat": NOW + 100},
])
def test_wrong_identity_expiry_and_assignment_never_reach_sts(changes):
    client = Mock()
    with pytest.raises(auth.FederationError):
        auth.exchange(SETTINGS, token(**changes), client=client, now=NOW)
    client.assume_role_with_web_identity.assert_not_called()


def test_inspection_only_allows_unknown_subject_not_wrong_mi():
    assert auth.validate_claims(token(sub="observed-sub"), SETTINGS, now=NOW,
                                inspect=True)["sub"] == "observed-sub"
    with pytest.raises(auth.FederationError):
        auth.validate_claims(token(oid=APP), SETTINGS, now=NOW, inspect=True)


def test_v1_claims_explicitly_supported_without_sub_oid_assumption():
    settings = replace(SETTINGS, version="1.0", issuer=f"https://sts.windows.net/{auth.TENANT}/",
                       audience=f"api://{APP}")
    encoded = token(ver="1.0", iss=settings.issuer, aud=settings.audience, appid=CLIENT)
    assert auth.validate_claims(encoded, settings, now=NOW)["sub"] != PRINCIPAL


def test_temporary_process_response_has_expiration_and_exact_sts_target():
    client = Mock()
    client.assume_role_with_web_identity.return_value = response()
    result = auth.exchange(SETTINGS, token(), client=client, now=NOW)
    assert result["Version"] == 1
    assert datetime.fromisoformat(result["Expiration"]).timestamp() == NOW + 3600
    assert "token" not in result and "RoleArn" not in result
    assert client.assume_role_with_web_identity.call_args.kwargs == {
        "RoleArn": auth.ROLE, "RoleSessionName": "redshift-aca-runtime",
        "WebIdentityToken": token(), "DurationSeconds": 3600}


def test_second_invocation_exchanges_again_no_persistent_crossprocess_cache():
    client = Mock()
    client.assume_role_with_web_identity.return_value = response()
    for _ in range(2):
        auth.exchange(SETTINGS, token(), client=client, now=NOW)
    assert client.assume_role_with_web_identity.call_count == 2


def test_sts_provider_failure_never_carries_provider_exception():
    client = Mock()
    client.assume_role_with_web_identity.side_effect = RuntimeError("PRIVATE_STS_BODY")
    with pytest.raises(auth.FederationError, match="^sts_exchange_failed$") as raised:
        auth.exchange(SETTINGS, token(), client=client, now=NOW)
    assert "PRIVATE_STS_BODY" not in str(raised.value)


@pytest.mark.parametrize("expiration", [None, datetime.fromtimestamp(NOW + 900),
                                      datetime.fromtimestamp(NOW + 50, UTC),
                                      datetime.fromtimestamp(NOW + 900, UTC),
                                      datetime.fromtimestamp(NOW + 3540, UTC),
                                      datetime.fromtimestamp(NOW + 3661, UTC)])
def test_bad_sts_expiration_fails(expiration):
    client = Mock()
    result = response()
    result["Credentials"]["Expiration"] = expiration
    client.assume_role_with_web_identity.return_value = result
    with pytest.raises(auth.FederationError):
        auth.exchange(SETTINGS, token(), client=client, now=NOW)


def test_failures_never_emit_token_provider_body_or_credentials():
    secret = "PRIVATE_PROVIDER_BODY"
    stdout, stderr = io.StringIO(), io.StringIO()
    with patch.object(auth.Settings, "from_env", return_value=SETTINGS), \
            patch.object(auth, "acquire_token", side_effect=RuntimeError(secret)), \
            redirect_stdout(stdout), redirect_stderr(stderr):
        assert auth.main([]) == 1
    assert not stdout.getvalue()
    assert secret not in stderr.getvalue()
    assert "internal_failure" in stderr.getvalue()


def test_missing_aca_identity_does_not_use_cli_or_vm_fallback():
    with patch.dict(auth.os.environ, {}, clear=True), pytest.raises(
            auth.FederationError, match="aca_identity_unavailable"):
        auth.acquire_token(SETTINGS)


@pytest.mark.parametrize("value", ["not-a-jwt", "a.e30.b", "a.@@.b", "a." + "a" * 33000 + ".b"])
def test_invalid_tokens_fail_closed(value):
    with pytest.raises(auth.FederationError):
        auth.validate_claims(value, SETTINGS, now=NOW)
