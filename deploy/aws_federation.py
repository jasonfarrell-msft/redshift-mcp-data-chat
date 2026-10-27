#!/usr/bin/env python3
"""Generate review-only, target-pinned federation artifacts. No mutation executor."""

import argparse
import json
import re
import subprocess
from uuid import UUID

ACCOUNT = "684925376801"
TENANT = "e90bd921-0e00-4e6f-b87c-713670ee27bf"
REGION = "us-east-2"
ROLE_NAME = "RedshiftAzureOfficialMcpRole"
ROLE_ARN = f"arn:aws:iam::{ACCOUNT}:role/{ROLE_NAME}"
WORKGROUP = (f"arn:aws:redshift-serverless:{REGION}:{ACCOUNT}:workgroup/"
             "10f4dfe2-659f-47f4-ba40-2c3946bd14b9")
APP_ROLE_ID = "c1852013-21ec-4a80-aa83-e64d20a852f9"
TABLES = ("daily_production", "monthly_production", "annual_production",
          "monthly_prices", "wells")


class ArtifactError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise ArtifactError(message)


def guid(value):
    try:
        require(str(UUID(value)) == value, "Invalid exact object/application ID.")
    except (ValueError, TypeError, AttributeError):
        raise ArtifactError("Invalid exact object/application ID.") from None
    return value


def entra_application(resource_app_id):
    guid(resource_app_id)
    return {
        "displayName": "redshift-official-aca-federation",
        "signInAudience": "AzureADMyOrg",
        "identifierUris": [f"api://{resource_app_id}"],
        "api": {"requestedAccessTokenVersion": 2},
        "appRoles": [{"id": APP_ROLE_ID, "allowedMemberTypes": ["Application"],
                      "displayName": "Redshift read-only candidate",
                      "description": "Federate only the governed Redshift candidate.",
                      "isEnabled": True, "value": "Redshift.ReadOnly"}],
    }


def entra_service_principal(resource_app_id):
    return {"appId": guid(resource_app_id), "appRoleAssignmentRequired": True}


def entra_assignment(resource_sp_id, candidate_principal_id):
    return {"principalId": guid(candidate_principal_id), "resourceId": guid(resource_sp_id),
            "appRoleId": APP_ROLE_ID}


def trust_policy(*, issuer, audience, subject, client_id, version, resource_app_id):
    guid(resource_app_id)
    guid(client_id)
    require(bool(re.fullmatch(r"[A-Za-z0-9._-]{1,256}", subject)), "Invalid verified subject.")
    if version == "2.0":
        require(issuer == f"https://login.microsoftonline.com/{TENANT}/v2.0"
                and audience == resource_app_id, "Issuer/audience/version mismatch.")
        # AWS maps azp to :aud and original aud to :oaud, not arbitrary :azp.
        mapped = {"aud": client_id, "oaud": audience, "sub": subject}
        provider_audience = client_id
    elif version == "1.0":
        require(issuer == f"https://sts.windows.net/{TENANT}/"
                and audience == f"api://{resource_app_id}", "Issuer/audience/version mismatch.")
        mapped = {"aud": audience, "sub": subject}
        provider_audience = audience
    else:
        raise ArtifactError("Unsupported token version.")
    provider = issuer.removeprefix("https://")
    return {
        "provider": {"Url": issuer, "ClientIDList": [provider_audience]},
        "trust": {"Version": "2012-10-17", "Statement": [{
            "Effect": "Allow",
            "Principal": {"Federated": f"arn:aws:iam::{ACCOUNT}:oidc-provider/{provider}"},
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {"StringEquals": {f"{provider}:{k}": v for k, v in mapped.items()}},
        }]},
    }


def runtime_policy():
    return {"Version": "2012-10-17", "Statement": [
        {"Sid": "BatchOnlyFixedWorkgroup", "Effect": "Allow",
         "Action": ["redshift-data:BatchExecuteStatement"], "Resource": WORKGROUP},
        {"Sid": "TemporaryDatabaseIdentity", "Effect": "Allow",
         "Action": ["redshift-serverless:GetCredentials"],
         "Resource": WORKGROUP},
        {"Sid": "RequiredOfficialTargetDiscovery", "Effect": "Allow",
         "Action": "redshift-serverless:ListWorkgroups", "Resource": "*"},
        {"Sid": "OnlyOwnStatementResults", "Effect": "Allow",
         "Action": ["redshift-data:DescribeStatement", "redshift-data:GetStatementResult"],
         "Resource": "*", "Condition": {"StringEquals": {
             "redshift-data:statement-owner-iam-userid": "${aws:userid}"}}},
        {"Sid": "NoLegacyFallback", "Effect": "Deny",
         "Action": "redshift-data:ExecuteStatement", "Resource": "*"},
    ]}


def database_review_queries():
    """Read-only operator evidence; no CREATE/GRANT/ALTER or production write tests."""
    return [
        "SELECT current_user, current_database()",
        "SHOW statement_timeout",
        "SELECT usename, usesuper, usecreatedb FROM pg_user WHERE usename = current_user",
        "SELECT * FROM svv_user_grants",
        "SELECT * FROM svv_schema_privileges WHERE namespace_name = 'oge_synthetic'",
        "SELECT * FROM svv_relation_privileges WHERE namespace_name = 'oge_synthetic'",
        "SELECT * FROM svv_default_privileges",
    ]


def preflight():
    """Operator diagnostics only. Never return credentials, tokens, or provider bodies."""
    results = {}
    commands = {
        "aws_identity": ["aws", "sts", "get-caller-identity", "--region", REGION,
                         "--output", "json", "--no-cli-pager"],
        "entra_applications_read": [
            "az", "ad", "app", "list", "--filter",
            "displayName eq 'redshift-official-aca-federation'",
            "--query", "[].{id:id,appId:appId}", "--output", "json", "--only-show-errors"],
    }
    for label, command in commands.items():
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=60, check=False)
            if result.returncode:
                # Only classify known codes; never replay stderr which could contain tokens.
                message = result.stderr
                code = next((c for c in ("Authorization_RequestDenied", "Insufficient privileges",
                                         "ExpiredToken", "InvalidClientTokenId",
                                         "AADSTS700082", "AADSTS50076") if c in message),
                            "provider_read_failed")
                results[label] = {"ok": False, "code": code}
                continue
            value = json.loads(result.stdout)
            if label == "aws_identity":
                require(value.get("Account") == ACCOUNT, "Unexpected AWS operator account.")
                results[label] = {"ok": True, "account": ACCOUNT,
                                  "operator_root_diagnostic_only": value.get("Arn", "").endswith(":root")}
            else:
                results[label] = {"ok": True, "matching_resource_apps": value,
                                  "write_permission": "NOT_PROVEN_BY_READ"}
        except (OSError, subprocess.TimeoutExpired, ValueError):
            results[label] = {"ok": False, "code": "preflight_unavailable"}
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("policy", "preflight"))
    args = parser.parse_args()
    if args.stage == "preflight":
        print(json.dumps(preflight(), indent=2))
    else:
        print(json.dumps({"role": ROLE_ARN, "policy": runtime_policy(),
                          "database": "dev", "schema": "oge_synthetic", "tables": TABLES,
                          "read_only_catalog_queries": database_review_queries(),
                          "apply": "BLOCKED: independent review and actual claims/budget proof required"},
                         indent=2))


if __name__ == "__main__":
    try:
        main()
    except ArtifactError as exc:
        raise SystemExit(str(exc)) from None
