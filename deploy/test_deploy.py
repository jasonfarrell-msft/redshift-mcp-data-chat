"""Synthetic tests only: no dotenv reads, cloud calls, or temporary directories."""

import json
import copy
import os
import unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import deploy


def config():
    return SimpleNamespace(
        host="redshift.example.invalid", port=5439, database="synthetic",
        user="reader", password="synthetic-password-never-in-arm",
        auth_mode="password", timeout=10, region=None, cluster_identifier=None,
    )


class DeploymentTests(unittest.TestCase):
    @staticmethod
    def revision(name="latest", active=True, health="Healthy", running="Running"):
        return {"name": name, "properties": {
            "active": active, "healthState": health, "runningState": running,
        }}

    def test_revision_accepts_only_healthy_executing_states(self):
        for running in ("Running", "RunningAtMaxScale"):
            with self.subTest(running=running):
                self.assertTrue(deploy.sole_healthy_running_revision(
                    [self.revision(running=running)], "latest",
                ))

    def test_revision_rejects_failed_provisioning_degraded_and_unknown_states(self):
        for running in (
            "Failed", "Provisioning", "Degraded", "Stopped", "Processing",
            "Deprovisioning", "Unknown", "RunningAtMinScale", "RunningUnknown", "", None,
        ):
            with self.subTest(running=running):
                self.assertFalse(deploy.sole_healthy_running_revision(
                    [self.revision(running=running)], "latest",
                ))
        revision = self.revision()
        del revision["properties"]["runningState"]
        self.assertFalse(deploy.sole_healthy_running_revision([revision], "latest"))

    def test_revision_requires_healthy_with_either_accepted_running_state(self):
        for running in ("Running", "RunningAtMaxScale"):
            for health in ("Unhealthy", "Failed", "Provisioning", "Degraded", "Unknown", "", None):
                with self.subTest(running=running, health=health):
                    self.assertFalse(deploy.sole_healthy_running_revision(
                        [self.revision(health=health, running=running)], "latest",
                    ))
            revision = self.revision(running=running)
            del revision["properties"]["healthState"]
            self.assertFalse(deploy.sole_healthy_running_revision([revision], "latest"))

    def test_revision_requires_sole_active_latest_with_either_accepted_running_state(self):
        for running in ("Running", "RunningAtMaxScale"):
            latest = self.revision(running=running)
            old = self.revision(name="old", running=running)
            inactive = self.revision(active=False, running=running)
            for revisions in ([], [old], [inactive], [latest, old], [latest, latest]):
                with self.subTest(running=running, revisions=revisions):
                    self.assertFalse(deploy.sole_healthy_running_revision(revisions, "latest"))
            self.assertTrue(deploy.sole_healthy_running_revision(
                [latest, self.revision(name="old", active=False)], "latest",
            ))

    @staticmethod
    def infrastructure():
        return {
            deploy.GROUP: {"location": deploy.LOCATION},
            deploy.REGISTRY: {
                "location": deploy.LOCATION, "sku": {"name": "Basic"}, "properties": {
                    "adminUserEnabled": False, "anonymousPullEnabled": False,
                    "publicNetworkAccess": "Enabled",
                    "roleAssignmentMode": "LegacyRegistryPermissions",
                    "policies": {"azureADAuthenticationAsArmPolicy": {"status": "enabled"}},
                },
            },
            deploy.VAULT_ID: {
                "location": deploy.LOCATION, "tags": {"SecurityControl": "Ignore"},
                "properties": {
                    "enableRbacAuthorization": True, "enablePurgeProtection": True,
                    "enableSoftDelete": True, "sku": {"name": "standard"},
                    "publicNetworkAccess": "Enabled",
                },
            },
            deploy.IDENTITY: {
                "location": deploy.LOCATION, "properties": {"principalId": "synthetic"},
            },
            deploy.ENV_ID: {"location": "Brazil South", "properties": {
                "provisioningState": "Succeeded", "infrastructureResourceGroup": None,
                "vnetConfiguration": None,
                "appLogsConfiguration": {"destination": None, "logAnalyticsConfiguration": None},
                "workloadProfiles": [{
                    "name": "Consumption", "workloadProfileType": "Consumption", "enableFips": False,
                }],
            }},
        }

    def verify_resources(self, resources, inventory=None):
        with (
            patch.object(deploy, "arm", side_effect=lambda method, resource, api: resources[resource]),
            patch.object(deploy, "cli", return_value=inventory or []),
        ):
            deploy.verify_infrastructure()

    def test_environment_accepts_only_legacy_or_single_builtin_consumption(self):
        for profiles in (
            None, [],
            [{"name": "Consumption", "workloadProfileType": "Consumption", "enableFips": False}],
            [{"name": "Consumption", "workloadProfileType": "Consumption",
              "minimumCount": 0, "maximumCount": 0}],
        ):
            with self.subTest(profiles=profiles):
                resources = self.infrastructure()
                resources[deploy.ENV_ID]["properties"]["workloadProfiles"] = profiles
                self.verify_resources(resources)
        resources = self.infrastructure()
        del resources[deploy.ENV_ID]["properties"]["workloadProfiles"]
        self.verify_resources(resources)

    def test_environment_rejects_dedicated_multiple_unexpected_profiles_and_capacity(self):
        consumption = {"name": "Consumption", "workloadProfileType": "Consumption"}
        dedicated = {"name": "dedicated", "workloadProfileType": "D4"}
        for profiles in (
            [dedicated], [consumption, dedicated], [consumption, consumption],
            [{**consumption, "name": "custom"}],
            [{**consumption, "workloadProfileType": "D4"}],
            [{**consumption, "minimumCount": 1}],
            [{**consumption, "maximumCount": 1}],
            [{**consumption, "minimumCount": -1}],
            [{**consumption, "maximumCount": "0"}],
            [{}], [None], {}, "", False,
        ):
            with self.subTest(profiles=profiles):
                resources = self.infrastructure()
                resources[deploy.ENV_ID]["properties"]["workloadProfiles"] = profiles
                with self.assertRaises(deploy.DeploymentError):
                    self.verify_resources(resources)

    def test_consumption_profile_does_not_relax_region_network_or_logs_guards(self):
        for field, value in (
            ("infrastructureResourceGroup", "unexpected-infra-rg"),
            ("vnetConfiguration", {"infrastructureSubnetId": "synthetic-subnet"}),
            ("vnetConfiguration", {"internal": True}),
            ("appLogsConfiguration", {"destination": "log-analytics"}),
        ):
            with self.subTest(field=field, value=value):
                resources = self.infrastructure()
                resources[deploy.ENV_ID]["properties"][field] = value
                with self.assertRaises(deploy.DeploymentError):
                    self.verify_resources(resources)
        resources = self.infrastructure()
        resources[deploy.ENV_ID]["location"] = "eastus"
        with self.assertRaises(deploy.DeploymentError):
            self.verify_resources(resources)
        for resource_type in ("Microsoft.Network/virtualNetworks",
                              "Microsoft.OperationalInsights/workspaces"):
            with self.subTest(resource_type=resource_type), self.assertRaises(deploy.DeploymentError):
                self.verify_resources(self.infrastructure(), [{"type": resource_type}])

    def test_vault_requires_exact_policy_exclusion_tag_and_public_access(self):
        for tags in (None, {}, {"SecurityControl": "ignore"}, {"SecurityControl": "Other"}):
            with self.subTest(tags=tags):
                resources = self.infrastructure()
                resources[deploy.VAULT_ID]["tags"] = tags
                with self.assertRaises(deploy.DeploymentError):
                    self.verify_resources(resources)
        resources = self.infrastructure()
        resources[deploy.VAULT_ID]["properties"]["publicNetworkAccess"] = "Disabled"
        with self.assertRaises(deploy.DeploymentError):
            self.verify_resources(resources)

    def test_prerequisites_tag_only_new_vault_and_preserve_existing_resources(self):
        for existing in (False, True):
            with self.subTest(existing=existing):
                resources = self.infrastructure()
                with (
                    patch.object(deploy, "arm", side_effect=lambda method, resource, api, *a, **k:
                                 resources[resource] if existing and method == "GET" else None) as arm,
                    patch.object(deploy, "wait_resource",
                                 side_effect=lambda resource, api: resources[resource]),
                    patch.object(deploy, "role"),
                    patch.object(deploy, "cli", return_value=[]) as cli,
                    patch.object(deploy, "verify_infrastructure"),
                    patch.object(deploy, "quota"),
                    patch.object(deploy, "save_state"),
                ):
                    deploy.prerequisites()
                puts = [call for call in arm.call_args_list if call.args[0] == "PUT"]
                if existing:
                    self.assertEqual(puts, [])
                    self.assertFalse(any(call.args[:3] == ("containerapp", "env", "create")
                                         for call in cli.call_args_list))
                else:
                    vault_put = next(call for call in puts if call.args[1] == deploy.VAULT_ID)
                    self.assertEqual(vault_put.args[3]["tags"], {"SecurityControl": "Ignore"})
                    self.assertEqual(vault_put.args[3]["properties"]["publicNetworkAccess"], "Enabled")
                    self.assertTrue(all("tags" not in call.args[3] for call in puts
                                        if call.args[1] != deploy.VAULT_ID))
                    cli.assert_any_call(
                        "containerapp", "env", "create", "--name", deploy.ENV,
                        "--resource-group", deploy.RG, "--location", deploy.LOCATION,
                        "--enable-workload-profiles", "false", "--logs-destination", "none",
                    )

    def test_bootstrap_has_no_password_and_configure_uses_reference(self):
        with patch.object(deploy, "read_state", return_value={"digest": "sha256:" + "a" * 64}):
            bootstrap = deploy.app_document(config())
            configured = deploy.app_document(config(), True, "app.example.invalid")
        for document in (bootstrap, configured):
            self.assertNotIn(config().password, json.dumps(document))
            self.assertNotIn("AZURE_CLIENT_ID", json.dumps(document))
        self.assertEqual(bootstrap["properties"]["configuration"]["secrets"], [])
        env = configured["properties"]["template"]["containers"][0]["env"]
        password = next(e for e in env if e["name"] == "REDSHIFT_PASSWORD")
        self.assertEqual(password, {"name": "REDSHIFT_PASSWORD", "secretRef": "redshift-password"})
        self.assertEqual(
            configured["properties"]["configuration"]["secrets"][0]["identity"], "system"
        )
        self.assertIn({"name": "REDSHIFT_MCP_ALLOWED_HOSTS", "value": "app.example.invalid"}, env)
        self.assertFalse(any(e["name"].startswith("AWS_") for e in env))

    def test_cli_subscription_scope_excludes_only_azure_directory_commands(self):
        cases = (
            (("ad", "signed-in-user", "show"), True,
             ["az", "ad", "signed-in-user", "show", "--only-show-errors",
              "--output", "json"]),
            (("group", "show", "--name", deploy.RG), True,
             ["az", "group", "show", "--name", deploy.RG, "--only-show-errors",
              "--subscription", deploy.SUB, "--output", "json"]),
            (("ec2", "describe-security-group-rules"), False,
             ["aws", "ec2", "describe-security-group-rules",
              "--region", "us-east-2", "--output", "json"]),
        )
        for args, azure, expected in cases:
            with self.subTest(args=args, azure=azure), patch.object(
                deploy.subprocess, "run",
                return_value=SimpleNamespace(
                    returncode=0, stdout='{"id": "synthetic"}', stderr="",
                ),
            ) as run:
                self.assertEqual(deploy.cli(*args, azure=azure), {"id": "synthetic"})
                self.assertEqual(run.call_args.args, (expected,))
                self.assertTrue(run.call_args.kwargs["capture_output"])
                self.assertTrue(run.call_args.kwargs["text"])
                self.assertFalse(run.call_args.kwargs["check"])

    def test_cli_never_passes_password_and_suppresses_error_output(self):
        with (
            patch.dict(os.environ, {"REDSHIFT_PASSWORD": config().password}),
            patch.object(deploy.subprocess, "run") as run,
        ):
            run.return_value = SimpleNamespace(returncode=0, stdout="{}", stderr="")
            deploy.cli("account", "show")
            self.assertNotIn(config().password, repr(run.call_args))
            self.assertNotIn("REDSHIFT_PASSWORD", run.call_args.kwargs["env"])
            self.assertEqual(run.call_args.kwargs["env"]["TMPDIR"], str(deploy.DEPLOY_DIR))
            run.return_value = SimpleNamespace(returncode=1, stdout="", stderr=config().password)
            with self.assertRaises(deploy.DeploymentError) as raised:
                deploy.cli("account", "show")
            self.assertNotIn(config().password, str(raised.exception))

    def test_role_reuses_exact_existing_assignment(self):
        assignment = {"id": "existing", "properties": {
            "scope": deploy.REGISTRY, "principalId": "principal",
            "roleDefinitionId": deploy.PULL,
        }}
        with patch.object(deploy, "arm", return_value={"value": [assignment]}) as arm:
            self.assertEqual(deploy.role("principal", deploy.REGISTRY, deploy.PULL),
                             ("existing", False))
            self.assertEqual(arm.call_count, 1)
            self.assertEqual(arm.call_args.args[0], "GET")

    def test_aws_existing_equivalent_rule_does_not_mutate(self):
        existing = {"IsEgress": False, "IpProtocol": "tcp", "FromPort": 5439,
                    "ToPort": 5439, "CidrIpv4": "0.0.0.0/0"}
        with patch.object(deploy, "cli", return_value={"SecurityGroupRules": [existing]}) as cli:
            deploy.aws_rule()
            self.assertEqual(cli.call_count, 1)
            self.assertEqual(cli.call_args.args[1], "describe-security-group-rules")

    def test_aws_only_authorized_rule_is_created_and_recorded(self):
        unrelated = {"IsEgress": False, "IpProtocol": "tcp", "FromPort": 443,
                     "ToPort": 443, "CidrIpv4": "0.0.0.0/0"}
        with (
            patch.object(deploy, "cli", side_effect=[
                {"SecurityGroupRules": [unrelated]},
                {"SecurityGroupRules": [{"SecurityGroupRuleId": "sgr-synthetic"}]},
            ]) as cli,
            patch.object(deploy, "save_state") as save,
        ):
            deploy.aws_rule()
            self.assertEqual(cli.call_args.args, (
                "ec2", "authorize-security-group-ingress", "--group-id", deploy.SG,
                "--protocol", "tcp", "--port", "5439", "--cidr", "0.0.0.0/0",
            ))
            save.assert_called_once_with(owned_aws_rule="sgr-synthetic")

    def test_check_never_calls_apply_stages_or_settings(self):
        with (
            patch.object(deploy, "check") as check,
            patch.object(deploy, "settings") as settings,
            patch.object(deploy, "arm", return_value={"value": []}) as arm,
        ):
            deploy.main(["--validate"])
            check.assert_called_once_with(False)
            settings.assert_not_called()
            arm.assert_not_called()

    def test_apply_requires_explicit_stage(self):
        with patch.object(deploy, "check") as check:
            with self.assertRaises(deploy.DeploymentError):
                deploy.main(["--apply"])
            check.assert_not_called()

    def test_all_stage_order(self):
        order = []
        with patch.object(deploy, "check"), self.stage_stack(order):
            deploy.main(["--apply", "--stage", "all"])
        self.assertEqual(order, list(deploy.STAGES))

    @staticmethod
    def stage_stack(order):
        stack = ExitStack()
        for name in deploy.STAGES:
            stack.enter_context(patch.object(deploy, name, side_effect=lambda *a, n=name: order.append(n)))
        return stack

    def test_state_refuses_configuration_values(self):
        with self.assertRaises(deploy.DeploymentError):
            deploy.save_state(password=config().password)

    def test_same_source_and_digest_skip_cloud_build(self):
        digest = "sha256:" + "a" * 64
        with (
            patch.object(deploy, "source_manifest", return_value="synthetic-source-hash"),
            patch.object(deploy, "read_state", return_value={
                "source_sha256": "synthetic-source-hash", "digest": digest,
            }),
            patch.object(deploy, "cli", return_value={"digest": digest}) as cli,
        ):
            deploy.build()
        cli.assert_called_once_with("acr", "repository", "show", "--name", deploy.ACR,
                                    "--image", "redshift-mcp-server:v1")

    def test_source_manifest_uses_only_runtime_allowlist(self):
        opened = []
        text = {
            ".dockerignore": "**\n!Dockerfile\n**/.env*\n",
            "Dockerfile": "FROM python@sha256:" + "a" * 64 + "\n"
                          "COPY requirements.lock ./\nUSER 10001\n"
                          'CMD ["server", "--host", "0.0.0.0"]\n',
        }

        def read_text(path):
            opened.append(path.name)
            return text[path.name]

        with (
            patch.object(Path, "is_file", return_value=True),
            patch.object(Path, "is_symlink", return_value=False),
            patch.object(Path, "exists", return_value=False),
            patch.object(Path, "read_text", read_text),
            patch.object(Path, "read_bytes", lambda path: opened.append(path.name) or b"synthetic"),
        ):
            deploy.source_manifest()
        self.assertFalse(any(name.startswith(".env") for name in opened))

    def test_temporary_secret_officer_removed_even_after_sdk_failure(self):
        class ResponseError(Exception):
            def __init__(self, status_code):
                self.status_code = status_code

        client = MagicMock()
        client.get_secret.side_effect = [
            ResponseError(403), SimpleNamespace(value="previous-synthetic")
        ]
        client.set_secret.side_effect = RuntimeError(config().password)
        fake_modules = {
            "azure": SimpleNamespace(),
            "azure.core": SimpleNamespace(),
            "azure.core.exceptions": SimpleNamespace(HttpResponseError=ResponseError),
            "azure.keyvault": SimpleNamespace(),
            "azure.keyvault.secrets": SimpleNamespace(SecretClient=lambda *a, **k: client),
        }
        with (
            patch.dict(deploy.sys.modules, fake_modules),
            patch.object(deploy, "credential"),
            patch.object(deploy, "cli", return_value={"id": "synthetic-principal"}),
            patch.object(deploy, "read_state", return_value={}),
            patch.object(deploy, "save_state") as save,
            patch.object(deploy, "arm", return_value={"value": []}) as arm,
            patch.object(deploy.time, "sleep"),self.assertRaises(RuntimeError)
        ):
            deploy.upload_password(config())
        puts = [c for c in arm.call_args_list if c.args[0] == "PUT"]
        self.assertEqual(len(puts), 1)
        self.assertEqual(arm.call_args_list[-1].args[0], "DELETE")
        self.assertEqual(puts[0].args[1], arm.call_args_list[-1].args[1])
        save.assert_called_with(owned_officer=None)
        self.assertNotIn(config().password, repr(arm.call_args_list))


class ReleaseTests(unittest.TestCase):
    source = "b" * 64
    digest = "sha256:" + "c" * 64
    old_digest = "sha256:" + "a" * 64

    def setUp(self):
        self.state = {"image_tag": "v2", "source_sha256": self.source, "digest": self.digest}
        with patch.object(deploy, "read_state", return_value={"digest": self.old_digest}):
            self.current = deploy.app_document(config(), True, "app.example.invalid")
        self.current.update(id=deploy.APP_ID, name=deploy.APP, type="Microsoft.App/containerApps",
                            etag='"original-etag"', tags={"keep": "exact"})
        self.current["identity"].update(principalId="system-principal", tenantId=deploy.TENANT)
        self.current["identity"]["userAssignedIdentities"][deploy.IDENTITY] = {
            "principalId": "pull-principal", "clientId": "pull-client",
        }
        props = self.current["properties"]
        props.update(provisioningState="Succeeded", latestRevisionName="old",
                     latestReadyRevisionName="old", workloadProfileName="Consumption")
        props["configuration"]["ingress"].update(
            fqdn="app.example.invalid",
            corsPolicy={"allowedOrigins": ["https://custom.example.invalid"],
                        "allowCredentials": True, "allowedMethods": ["GET", "POST"],
                        "allowedHeaders": ["X-Custom"], "maxAge": 123},
            ipSecurityRestrictions=[{"name": "custom", "ipAddressRange": "192.0.2.0/24",
                                     "action": "Allow"}],
        )
        template = props["template"]
        template["revisionSuffix"] = "old"
        template["containers"][0]["resources"] = {"cpu": 0.5, "memory": "1Gi"}
        template["containers"][0]["env"].append({"name": "CUSTOM", "value": "preserve"})
        template["containers"].append({
            "name": "sidecar", "image": "sidecar.example.invalid@sha256:" + "d" * 64,
            "env": [{"name": "REF", "secretRef": "redshift-password"}],
            "resources": {"cpu": 0.25, "memory": "0.5Gi"},
            "probes": [{"type": "Liveness", "tcpSocket": {"port": 9000}}],
        })
        template["scale"] = {"minReplicas": 1, "maxReplicas": 3,
                             "rules": [{"name": "http", "http": {"metadata": {"concurrentRequests": "10"}}}]}
        template["volumes"] = [{"name": "scratch", "storageType": "EmptyDir"}]
        self.approved = deploy.app_fingerprint(self.current)
        self.original = copy.deepcopy(self.current)
        self.calls = []

    def save(self, **metadata):
        self.state.update(copy.deepcopy(metadata))

    def arm(self, method, resource, api, body=None, **kwargs):
        self.calls.append((method, resource, copy.deepcopy(body), kwargs))
        if method == "GET" and resource == deploy.IDENTITY:
            return {"properties": {"principalId": "pull-principal", "clientId": "pull-client"}}
        self.assertEqual(resource, deploy.APP_ID)
        if method == "PATCH":
            self.assertEqual(set(body), {"properties"})
            self.assertEqual(set(body["properties"]), {"template"})
            self.current["properties"]["template"] = copy.deepcopy(body["properties"]["template"])
            self.current["properties"].update(latestRevisionName="new", latestReadyRevisionName="new",
                                              latestRevisionFqdn="new.example.invalid")
            self.current["etag"] = '"new-etag"'
        else:
            self.assertEqual(method, "GET")
        return copy.deepcopy(self.current)

    def cli(self, *args, **kwargs):
        if args[:3] == ("acr", "repository", "show"):
            self.assertEqual(args[-1], "redshift-mcp-server:v2")
            return {"digest": self.digest}
        self.assertEqual(args[:3], ("containerapp", "revision", "list"))
        return [DeploymentTests.revision(name="new")]

    def stack(self):
        stack = ExitStack()
        stack.enter_context(patch.object(deploy, "arm", side_effect=self.arm))
        stack.enter_context(patch.object(deploy, "cli", side_effect=self.cli))
        stack.enter_context(patch.object(deploy, "read_state", side_effect=lambda: copy.deepcopy(self.state)))
        stack.enter_context(patch.object(deploy, "save_state", side_effect=self.save))
        stack.enter_context(patch.object(deploy, "source_manifest", return_value=self.source))
        stack.enter_context(patch.object(deploy.time, "sleep"))
        for name in ("settings", "upload_password", "role", "aws_rule", "prerequisites", "app", "configure"):
            stack.enter_context(patch.object(deploy, name, side_effect=AssertionError("Forbidden release stage")))
        return stack

    def run_update(self):
        deploy.update("v2", self.source, self.approved, apply=True)

    def test_update_preserves_every_setting_and_only_patches_captured_template(self):
        with self.stack():
            self.run_update()
        writes = [c for c in self.calls if c[0] != "GET"]
        self.assertEqual(len(writes), 1)
        self.assertEqual(writes[0][0], "PATCH")
        self.assertEqual(writes[0][3], {"if_match": '"original-etag"'})
        expected = copy.deepcopy(self.original["properties"]["template"])
        expected.pop("revisionSuffix")
        expected["containers"][0]["image"] = f"{deploy.IMAGE_REPOSITORY}@{self.digest}"
        self.assertEqual(writes[0][2], {"properties": {"template": expected}})
        self.assertEqual(self.current["identity"], self.original["identity"])
        self.assertEqual(self.current["properties"]["configuration"],
                         self.original["properties"]["configuration"])
        self.assertEqual(deploy.app_fingerprint(self.current, True),
                         deploy.app_fingerprint(self.original, True))
        self.assertEqual(self.state["revision"], "new")
        self.assertEqual(self.state["fqdn"], "app.example.invalid")
        self.assertEqual(self.state["release"]["status"], "complete")
        self.assertEqual(self.state["release"]["previous_image"],
                         f"{deploy.IMAGE_REPOSITORY}@{self.old_digest}")
        self.assertEqual(self.state["release"]["previous_revision"], "old")
        self.assertNotIn("secretRef", json.dumps(self.state))
        self.assertNotIn("CUSTOM", json.dumps(self.state))

    def test_update_retry_does_not_create_another_revision(self):
        with self.stack():
            self.run_update()
            self.run_update()
        self.assertEqual(len([c for c in self.calls if c[0] == "PATCH"]), 1)

    def test_preview_and_direct_default_are_read_only(self):
        with self.stack(), patch.object(deploy, "save_state") as save:
            deploy.update("v2")
            save.assert_not_called()
        self.assertTrue(all(c[0] == "GET" for c in self.calls))

    def test_rejects_unreviewed_source_tag_digest_or_target_before_mutation(self):
        mutations = (
            lambda: self.state.update(image_tag="v1"),
            lambda: self.state.update(source_sha256="e" * 64),
            lambda: self.state.update(digest=self.old_digest),
            lambda: self.current.update(id="/wrong-app"),
            lambda: self.current["properties"].update(environmentId="/wrong-environment"),
            lambda: self.current["identity"].pop("principalId"),
            lambda: self.current["identity"].update(principalId="changed-system-principal"),
            lambda: self.current["identity"]["userAssignedIdentities"][deploy.IDENTITY].update(
                principalId="changed-pull-principal"),
            lambda: self.current["properties"]["configuration"]["ingress"]["corsPolicy"].update(
                allowedOrigins=["https://changed.example.invalid"]),
            lambda: self.current["properties"]["template"]["containers"][0].update(
                image=f"{deploy.IMAGE_REPOSITORY}@{'sha256:' + 'e' * 64}"),
            lambda: self.current["properties"]["configuration"]["secrets"][0].update(value="forbidden"),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.setUp()
                mutation()
                with self.stack(), self.assertRaises(deploy.DeploymentError):
                    self.run_update()
                self.assertTrue(all(c[0] == "GET" for c in self.calls))

    def test_changed_source_or_registry_digest_is_rejected(self):
        with self.stack(), patch.object(deploy, "source_manifest", return_value="e" * 64):
            with self.assertRaises(deploy.DeploymentError):
                self.run_update()
        self.assertTrue(all(c[0] == "GET" for c in self.calls))
        with self.stack(), patch.object(deploy, "cli", return_value={"digest": self.old_digest}):
            with self.assertRaises(deploy.DeploymentError):
                self.run_update()

    def test_pending_retry_rejects_identity_config_image_and_release_evidence_drift(self):
        with self.stack():
            self.run_update()
        baseline = copy.deepcopy(self.current)
        baseline_state = copy.deepcopy(self.state)
        mutations = (
            lambda: self.current["identity"].update(principalId="other"),
            lambda: self.current["properties"]["template"]["scale"].update(maxReplicas=9),
            lambda: self.current["properties"]["template"]["containers"][0].update(
                image=f"{deploy.IMAGE_REPOSITORY}@{'sha256:' + 'e' * 64}"),
            lambda: self.state.update(image_tag="v3"),
            lambda: self.state.update(source_sha256="e" * 64),
            lambda: self.state.update(digest=self.old_digest),
        )
        for mutation in mutations:
            self.current = copy.deepcopy(baseline)
            self.state = copy.deepcopy(baseline_state)
            self.state["release"]["status"] = "pending"
            self.calls = []
            mutation()
            with self.stack(), self.assertRaises(deploy.DeploymentError):
                self.run_update()
            self.assertTrue(all(c[0] == "GET" for c in self.calls))

    def test_concurrent_and_post_write_drift_fail_without_recovery(self):
        original_arm = self.arm
        for post_write in (False, True):
            with self.subTest(post_write=post_write):
                self.setUp()
                app_reads = 0

                def drift(method, resource, api, body=None, **kwargs):
                    nonlocal app_reads
                    if resource == deploy.APP_ID and method == "GET":
                        app_reads += 1
                        if app_reads == (3 if post_write else 2):
                            self.current["properties"]["configuration"]["ingress"]["corsPolicy"]["maxAge"] = 999
                    return original_arm(method, resource, api, body, **kwargs)

                with self.stack(), patch.object(deploy, "arm", side_effect=drift):
                    with self.assertRaises(deploy.DeploymentError):
                        self.run_update()
                self.assertEqual(len([c for c in self.calls if c[0] == "PATCH"]),
                                 1 if post_write else 0)
                self.assertEqual(self.state["release"]["status"], "pending")

    def test_failed_readiness_preserves_rollback_and_never_restarts(self):
        with self.stack(), patch.object(deploy, "cli", side_effect=lambda *a, **k:
                {"digest": self.digest} if a[0] == "acr" else
                [DeploymentTests.revision(name="new", health="Unhealthy")]):
            with self.assertRaises(deploy.DeploymentError):
                self.run_update()
        self.assertNotIn("revision", self.state)
        self.assertEqual(self.state["release"]["status"], "pending")
        self.assertEqual(len([c for c in self.calls if c[0] == "PATCH"]), 1)

    def test_image_tag_syntax_and_default(self):
        for tag in ("v1", "v2", "release-2026.10_26", "a" * 64):
            self.assertEqual(deploy.validate_image_tag(tag), tag)
        for tag in ("", "a" * 65, "registry/repo:v2", "v2@sha256:abc", "-v2", "v2\n", "../v2"):
            with self.subTest(tag=tag), self.assertRaises(deploy.DeploymentError):
                deploy.validate_image_tag(tag)
        with patch.object(deploy, "check"), patch.object(deploy, "build") as build:
            deploy.main(["--apply", "--stage", "build"])
        build.assert_called_once_with("v1", None)

    def test_v2_build_and_pull_use_only_v2_and_preserve_v1_evidence(self):
        old_record = {"source_sha256": "e" * 64, "digest": self.old_digest, "build_run": "old-run"}
        context = deploy.DEPLOY_DIR / ".build-context"
        responses = [
            ["redshift-mcp-server"], ["v1"],
            {"status": "Succeeded", "platform": {"os": "linux", "architecture": "amd64"}, "runId": "new-run"},
            {"digest": self.digest},
        ]
        with (
            patch.object(deploy, "source_manifest", return_value=self.source),
            patch.object(deploy, "read_state", return_value=old_record),
            patch.object(deploy, "cli", side_effect=responses) as cli,
            patch.object(Path, "exists", return_value=False),
            patch.object(Path, "mkdir"),
            patch.object(Path, "is_file", return_value=True),
            patch.object(Path, "rglob", return_value=[context / n for n in deploy.RUNTIME_FILES]),
            patch.object(deploy.shutil, "copyfile"),
            patch.object(deploy.shutil, "rmtree"),
            patch.object(deploy, "save_state") as save,
        ):
            deploy.build("v2", self.source)
        images = [c.args[c.args.index("--image") + 1]
                  for c in cli.call_args_list if "--image" in c.args]
        self.assertEqual(images, ["redshift-mcp-server:v2", "redshift-mcp-server:v2"])
        metadata = save.call_args.kwargs
        self.assertEqual(metadata["image_tag"], "v2")
        self.assertEqual(metadata["image_builds"]["v1"], old_record)
        self.assertEqual(metadata["image_builds"]["v2"]["digest"], self.digest)

    def test_build_never_overwrites_existing_or_different_source_tag(self):
        for state, responses in (
            ({}, [["redshift-mcp-server"], ["v1", "v2"]]),
            (self.state, []),
        ):
            with (
                patch.object(deploy, "source_manifest", return_value="f" * 64),
                patch.object(deploy, "read_state", return_value=state),
                patch.object(deploy, "cli", side_effect=responses) as cli,
                patch.object(Path, "mkdir") as mkdir,
                self.assertRaises(deploy.DeploymentError),
            ):
                deploy.build("v2", "f" * 64)
            mkdir.assert_not_called()
            self.assertFalse(any(c.args[:2] == ("acr", "build") for c in cli.call_args_list))

    def test_v2_retry_requires_matching_tag_source_digest(self):
        with (
            patch.object(deploy, "source_manifest", return_value=self.source),
            patch.object(deploy, "read_state", return_value=self.state),
            patch.object(deploy, "cli", return_value={"digest": self.digest}) as cli,
        ):
            deploy.build("v2", self.source)
        cli.assert_called_once_with("acr", "repository", "show", "--name", deploy.ACR,
                                    "--image", "redshift-mcp-server:v2")

    def test_update_cli_is_explicit_and_excluded_from_bootstrap_all(self):
        self.assertNotIn("update", deploy.STAGES)
        with patch.object(deploy, "check"), patch.object(deploy, "update") as update:
            deploy.main(["--apply", "--stage", "update", "--image-tag", "v2",
                         "--approved-source-sha256", self.source,
                         "--approved-app-sha256", self.approved])
        update.assert_called_once_with("v2", self.source, self.approved, apply=True)
        with patch.object(deploy, "check"), patch.object(deploy, "update") as update:
            deploy.main(["--check", "--stage", "update", "--image-tag", "v2"])
        update.assert_called_once_with("v2")

    def test_verify_rejects_wrong_tag_and_release_drift_before_network_acceptance(self):
        with self.stack(), self.assertRaises(deploy.DeploymentError):
            deploy.verify("v1")
        with self.stack():
            self.run_update()
        self.current["identity"]["principalId"] = "changed"
        with self.stack(), patch.object(deploy, "verify_infrastructure"):
            with self.assertRaises(deploy.DeploymentError):
                deploy.verify("v2")

    def test_full_v2_verify_retains_all_security_and_external_acceptance_checks(self):
        self.current["properties"]["template"]["containers"][0]["resources"] = {
            "cpu": 0.25, "memory": "0.5Gi",
        }
        self.current["properties"]["template"]["scale"] = {"minReplicas": 1, "maxReplicas": 1}
        self.approved = deploy.app_fingerprint(self.current)
        with self.stack():
            self.run_update()
        original_cli = self.cli
        roles = []

        def verify_cli(*args, **kwargs):
            if args[:3] == ("role", "assignment", "list"):
                principal = args[args.index("--assignee-object-id") + 1]
                roles.append(principal)
                scope, definition = ((deploy.SECRET_SCOPE, deploy.READER)
                                     if principal == "system-principal"
                                     else (deploy.REGISTRY, deploy.PULL))
                return [{"scope": scope, "roleDefinitionId": definition}]
            if args[:2] == ("ec2", "describe-security-group-rules"):
                return {"SecurityGroupRules": [{"IsEgress": False, "IpProtocol": "tcp",
                        "FromPort": 5439, "ToPort": 5439, "CidrIpv4": "0.0.0.0/0"}]}
            return original_cli(*args, **kwargs)

        rejection_checks = []

        def endpoint(request, **kwargs):
            if isinstance(request, str):
                response = MagicMock()
                response.__enter__.return_value.status = 200
                return response
            rejection_checks.append(dict(request.header_items()))
            raise deploy.HTTPError(request.full_url, 403, "denied", {}, None)

        with (
            self.stack(),
            patch.object(deploy, "verify_infrastructure") as infrastructure,
            patch.object(deploy, "cli", side_effect=verify_cli),
            patch.object(deploy, "urlopen", side_effect=endpoint),
            patch.object(deploy, "mcp_acceptance", new_callable=AsyncMock) as acceptance,
        ):
            deploy.verify("v2")
        infrastructure.assert_called_once()
        self.assertEqual(roles, ["system-principal", "pull-principal"])
        self.assertEqual(len(rejection_checks), 2)
        acceptance.assert_awaited_once_with("app.example.invalid")

    def test_arm_forwards_etag_and_if_match_without_retries_on_conflict(self):
        token = SimpleNamespace(get_token=lambda *a: SimpleNamespace(token="synthetic-token"))
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'{"properties": {}}'
        response.__enter__.return_value.headers = {"ETag": '"read-etag"'}
        with patch.object(deploy, "credential", return_value=token), patch.object(
            deploy, "urlopen", return_value=response,
        ) as open_request:
            current = deploy.arm("GET", deploy.APP_ID, deploy.APP_API)
            self.assertEqual(current["etag"], '"read-etag"')
            open_request.side_effect = deploy.HTTPError("https://example.invalid", 412, "conflict", {}, None)
            with self.assertRaisesRegex(deploy.DeploymentError, "HTTP 412"):
                deploy.arm("PATCH", deploy.APP_ID, deploy.APP_API, {"properties": {}},
                           if_match=current["etag"])
        self.assertEqual(open_request.call_args.args[0].get_header("If-match"), '"read-etag"')
        self.assertEqual(open_request.call_count, 2)

    def test_pending_release_blocks_different_build_and_record_drift(self):
        self.state["release"] = {"status": "pending", "image_tag": "v2",
                                 "digest": self.digest, "source_sha256": self.source}
        with (
            patch.object(deploy, "read_state", return_value=self.state),
            patch.object(deploy, "source_manifest", return_value=self.source),
            patch.object(deploy, "cli") as cli,
        ):
            with self.assertRaises(deploy.DeploymentError):
                deploy.build("v3", self.source)
            cli.assert_not_called()
        self.state["image_builds"] = {"v2": {"digest": self.old_digest, "source_sha256": self.source}}
        with self.stack(), self.assertRaises(deploy.DeploymentError):
            self.run_update()


if __name__ == "__main__":
    unittest.main()
