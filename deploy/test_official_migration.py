import copy
import unittest
from contextlib import nullcontext
from unittest.mock import patch

import aws_federation as federation
import official_cutover as cutover


class FederationTests(unittest.TestCase):
    app = "11111111-1111-4111-8111-111111111111"
    client = "22222222-2222-4222-8222-222222222222"

    def test_entra_assignment_required_application_only_no_secrets(self):
        app = federation.entra_application(self.app)
        sp = federation.entra_service_principal(self.app)
        self.assertTrue(sp["appRoleAssignmentRequired"])
        self.assertEqual(app["api"]["requestedAccessTokenVersion"], 2)
        self.assertEqual(app["appRoles"][0]["allowedMemberTypes"], ["Application"])
        self.assertNotIn("passwordCredentials", app)

    def test_v2_trust_maps_azp_aud_and_original_audience_oaud(self):
        issuer = f"https://login.microsoftonline.com/{federation.TENANT}/v2.0"
        result = federation.trust_policy(
            issuer=issuer, audience=self.app, subject="observed-not-oid",
            client_id=self.client, version="2.0", resource_app_id=self.app)
        conditions = result["trust"]["Statement"][0]["Condition"]["StringEquals"]
        provider = issuer.removeprefix("https://")
        self.assertEqual(conditions, {f"{provider}:aud": self.client,
                                      f"{provider}:oaud": self.app,
                                      f"{provider}:sub": "observed-not-oid"})
        self.assertEqual(result["provider"]["ClientIDList"], [self.client])
        self.assertNotIn("appid", str(conditions))

    def test_policy_batch_only_exact_workgroup_owned_results_and_required_discovery(self):
        statements = federation.runtime_policy()["Statement"]
        self.assertEqual(statements[0]["Resource"], federation.WORKGROUP)
        self.assertEqual(statements[1]["Action"], ["redshift-serverless:GetCredentials"])
        self.assertEqual(statements[2]["Action"], "redshift-serverless:ListWorkgroups")
        self.assertEqual(statements[3]["Condition"]["StringEquals"],
                         {"redshift-data:statement-owner-iam-userid": "${aws:userid}"})
        self.assertEqual(statements[-1]["Effect"], "Deny")
        self.assertEqual(statements[-1]["Action"], "redshift-data:ExecuteStatement")
        self.assertNotIn("secretsmanager", str(statements).lower())
        self.assertNotIn("RedshiftOgeMcpTaskRole", str(statements))


class CutoverTests(unittest.TestCase):
    gates = {key: True for key in (
        "independent_security_review", "independent_correctness_review",
        "azure_validate_current", "azure_deploy_current", "actual_candidate_proof",
        "new_agent_candidate_binding", "sts_expiry_refresh", "db_budget_10s")}

    def current(self):
        current = cutover.chat_aca.definition(cutover.CHAT_IMAGE)
        current.update(id=cutover.chat_aca.APP_ID, _ready_revision=cutover.CHAT_REVISION,
                       _revision_names=[cutover.CHAT_REVISION])
        current["identity"]["principalId"] = cutover.CHAT_PRINCIPAL
        props = current["properties"]
        props["configuration"]["ingress"]["fqdn"] = cutover.chat_aca.ORIGIN[8:]
        props["latestReadyRevisionName"] = cutover.CHAT_REVISION
        props["latestRevisionName"] = cutover.CHAT_REVISION
        props["provisioningState"] = "Succeeded"
        props["runningStatus"] = "Running"
        props["configuration"]["ingress"]["traffic"] = [{"weight": 100, "latestRevision": True}]
        return current

    def prepared(self):
        return cutover.prepare_cutover(self.current(), "3", "official-test-01")

    def after(self, release):
        current = self.current()
        current["properties"]["template"] = copy.deepcopy(
            release["patch"]["properties"]["template"])
        current["_ready_revision"] = release["expected_revision"]
        current["properties"]["latestReadyRevisionName"] = release["expected_revision"]
        current["properties"]["latestRevisionName"] = release["expected_revision"]
        return current

    def test_candidate_only_one_single_replica_no_password_or_budget_claim(self):
        candidate = cutover.candidate_definition(cutover.REPOSITORY + "@sha256:" + "a" * 64)
        props = candidate["properties"]
        self.assertEqual(props["template"]["scale"], {"minReplicas": 1, "maxReplicas": 1})
        self.assertEqual(props["configuration"]["activeRevisionsMode"], "Single")
        self.assertNotIn("REDSHIFT_DB_BUDGET_VERIFIED", str(candidate))
        self.assertNotIn("password", str(candidate).lower())
        self.assertFalse(props["configuration"]["ingress"]["allowInsecure"])
        env = {e["name"]: e["value"] for e in props["template"]["containers"][0]["env"]}
        self.assertEqual(env["REDSHIFT_MCP_ALLOWED_HOSTS"],
                         cutover.CANDIDATE_URL.removeprefix("https://").removesuffix("/mcp"))

    def test_candidate_uses_separate_built_repository_not_production_repository(self):
        image = (f"{cutover.shared.ACR}.azurecr.io/redshift-official-candidate"
                 "@sha256:1afda7b8e545ca99d4131e07a9e3ae4aaa6868f0e0f04140258b55673d2348cb")
        self.assertEqual(
            cutover.candidate_definition(image)["properties"]["template"]["containers"][0]["image"],
            image)
        with self.assertRaises(cutover.shared.DeploymentError):
            cutover.candidate_definition(
                f"{cutover.shared.ACR}.azurecr.io/redshift-mcp-server@sha256:" + "a" * 64)

    def test_one_revision_binding_preserves_every_other_template_field(self):
        current = self.current()
        original = copy.deepcopy(current)
        result = cutover.prepare_cutover(current, "3", "official-test-01")
        desired = result["patch"]["properties"]["template"]
        before = result["before"]["template"]
        self.assertEqual(current, original)
        self.assertEqual(cutover.binding(desired), {
            "FOUNDRY_AGENT_VERSION": "3", "MCP_SERVER_URL": cutover.CANDIDATE_URL})
        self.assertEqual(desired["containers"][0]["image"], cutover.CHAT_RELEASE_IMAGE)
        desired["containers"][0]["image"] = before["containers"][0]["image"]
        for entry in desired["containers"][0]["env"]:
            if entry["name"] in cutover.BINDING_KEYS:
                entry["value"] = cutover.binding(before)[entry["name"]]
        self.assertEqual(desired["revisionSuffix"], "official-test-01")
        self.assertEqual(cutover.without_suffix(desired), cutover.without_suffix(before))
        self.assertNotIn("etag", result["before"])

    def test_new_agent_preserves_business_contract_and_only_changes_one_url(self):
        desired = cutover.new_agent_definition()
        desired["tools"][0]["server_url"] = cutover.OLD_URL
        self.assertEqual(desired, cutover.chat_deploy.agent_definition())

    def test_supported_patch_rechecks_then_verifies_without_unsupported_header(self):
        current = self.current()
        prepared = self.prepared()
        after = self.after(prepared)
        reads = [current, current, after, after]
        with patch.object(cutover, "read_live", side_effect=reads) as read, \
                patch.object(cutover, "operator_lock", return_value=nullcontext()), \
                patch.object(cutover.shared, "arm") as arm:
            result = cutover.apply_prepared(
                prepared, reviewed_artifact_sha256=cutover.fingerprint(prepared), gates=self.gates)
        self.assertEqual(result["status"], "verified")
        self.assertEqual(read.call_count, 4)
        self.assertEqual([c.args[0] for c in arm.call_args_list], ["PATCH"])
        self.assertEqual(arm.call_args.kwargs, {})
        self.assertEqual(cutover.binding(arm.call_args.args[3]["properties"]["template"]),
                         {"FOUNDRY_AGENT_VERSION": "3", "MCP_SERVER_URL": cutover.CANDIDATE_URL})
        self.assertEqual(arm.call_args.args[3]["properties"]["template"]["containers"][0]["image"],
                         cutover.CHAT_RELEASE_IMAGE)

    def test_release_snapshot_allows_only_two_exact_images(self):
        release = self.prepared()
        after = self.after(release)
        cutover.snapshot(after)
        after["properties"]["template"]["containers"][0]["image"] = (
            cutover.chat_aca.REPOSITORY + "@sha256:" + "f" * 64)
        with self.assertRaises(cutover.shared.DeploymentError):
            cutover.snapshot(after)

    def test_even_reviewed_artifact_cannot_substitute_other_release_image(self):
        release = self.prepared()
        template = release["patch"]["properties"]["template"]
        template["containers"][0]["image"] = cutover.CHAT_IMAGE
        release["after_template_sha256"] = cutover.fingerprint(template)
        with patch.object(cutover.shared, "arm") as arm:
            with self.assertRaises(cutover.shared.DeploymentError):
                cutover.apply_prepared(
                    release, reviewed_artifact_sha256=cutover.fingerprint(release),
                    gates=self.gates)
        arm.assert_not_called()

    def test_rollback_restores_original_image_with_original_paired_binding(self):
        release = self.prepared()
        rollback = cutover.prepare_rollback(self.after(release), release, "rollback-image-01")
        restored = rollback["patch"]["properties"]["template"]
        self.assertEqual(restored["containers"][0]["image"], cutover.CHAT_IMAGE)
        self.assertEqual(cutover.binding(restored),
                         {"FOUNDRY_AGENT_VERSION": "2", "MCP_SERVER_URL": cutover.OLD_URL})

    def test_even_reviewed_artifact_cannot_change_unrelated_fields(self):
        current = self.current()
        prepared = self.prepared()
        template = prepared["patch"]["properties"]["template"]
        template["containers"][0]["resources"]["cpu"] = 0.5
        prepared["after_template_sha256"] = cutover.fingerprint(template)
        with patch.object(cutover.shared, "arm", return_value=current) as arm:
            with self.assertRaises(cutover.shared.DeploymentError):
                cutover.apply_prepared(
                    prepared, reviewed_artifact_sha256=cutover.fingerprint(prepared),
                    gates=self.gates)
        arm.assert_not_called()

    def test_idempotent_apply_does_not_replace_original_baseline(self):
        release = self.prepared()
        after = self.after(release)
        original = copy.deepcopy(release)
        with patch.object(cutover, "read_live", return_value=after), \
                patch.object(cutover, "operator_lock", return_value=nullcontext()), \
                patch.object(cutover.shared, "arm") as arm:
            result = cutover.apply_prepared(
                release, reviewed_artifact_sha256=cutover.fingerprint(release), gates=self.gates)
        self.assertEqual(result["status"], "verified")
        arm.assert_not_called()
        self.assertEqual(release, original)
        with self.assertRaises(cutover.shared.DeploymentError):
            cutover.prepare_cutover(after, "3", "official-test-01")
        rollback = cutover.prepare_rollback(after, release, "rollback-test-01")
        self.assertEqual(cutover.without_suffix(rollback["patch"]["properties"]["template"]),
                         cutover.without_suffix(release["before"]["template"]))
        self.assertEqual(rollback["rollback_baseline"], release["before"])

    def test_drift_and_new_secret_fields_rejected(self):
        for mutator in (
            lambda c: c["properties"].update(latestRevisionName="unready-revision"),
            lambda c: c["identity"].update(principalId="other"),
            lambda c: c["properties"]["template"]["containers"][0].update(image="tag:latest"),
            lambda c: c["properties"]["template"]["containers"][0]["env"].append(
                {"name": "TOKEN", "value": "do-not-persist"}),
        ):
            current = self.current()
            mutator(current)
            with self.assertRaises(cutover.shared.DeploymentError):
                cutover.prepare_cutover(current, "3", "official-test-01")

    def test_no_cloud_writes_without_all_gates_and_exact_reviewed_hash(self):
        release = self.prepared()
        with patch.object(cutover.shared, "arm") as arm:
            with self.assertRaises(cutover.shared.DeploymentError):
                cutover.apply_prepared(
                    release, reviewed_artifact_sha256=cutover.fingerprint(release), gates={})
            arm.assert_not_called()

    def test_rollback_rejects_unrelated_concurrent_template_change(self):
        current = self.current()
        release = self.prepared()
        current["properties"]["template"] = copy.deepcopy(
            release["patch"]["properties"]["template"])
        current["properties"]["template"]["containers"][0]["resources"]["cpu"] = 0.5
        with self.assertRaises(cutover.shared.DeploymentError):
            cutover.prepare_rollback(current, release, "rollback-test-01")

    def test_immediate_recheck_observed_unrelated_configuration_drift_stops_write(self):
        current = self.current()
        changed = copy.deepcopy(current)
        changed["properties"]["configuration"]["maxInactiveRevisions"] = 99
        release = self.prepared()
        with patch.object(cutover, "read_live", side_effect=[current, changed]), \
                patch.object(cutover, "operator_lock", return_value=nullcontext()), \
                patch.object(cutover.shared, "arm") as arm:
            with self.assertRaises(cutover.shared.DeploymentError):
                cutover.apply_prepared(
                    release, reviewed_artifact_sha256=cutover.fingerprint(release),
                    gates=self.gates)
        arm.assert_not_called()

    def test_postverification_detects_unrelated_drift(self):
        release = self.prepared()
        after = self.after(release)
        after["properties"]["configuration"]["maxInactiveRevisions"] = 99
        with patch.object(cutover, "read_live", return_value=after):
            with self.assertRaises(cutover.shared.DeploymentError):
                cutover.verify_applied(release)

    def test_readiness_wait_is_bounded_and_never_resubmits_write(self):
        release = self.prepared()
        with patch.object(cutover, "read_live", return_value=self.current()), \
                patch.object(cutover.time, "monotonic", side_effect=[0, 301]), \
                patch.object(cutover.shared, "arm") as arm:
            with self.assertRaises(cutover.shared.DeploymentError):
                cutover.verify_applied(release)
        arm.assert_not_called()

    def test_replica_pending_is_polled_read_only_until_ready(self):
        release = self.prepared()
        after = self.after(release)
        pending = cutover.shared.DeploymentError("Replica readiness pending.")
        with patch.object(cutover, "read_live", side_effect=[after, pending, after, after]), \
                patch.object(cutover.time, "monotonic", side_effect=[0, 1]), \
                patch.object(cutover.time, "sleep") as sleep, \
                patch.object(cutover.shared, "arm") as arm:
            self.assertEqual(cutover.verify_applied(release)["status"], "verified")
        sleep.assert_called_once_with(5)
        arm.assert_not_called()

    def test_resource_id_casing_is_not_identity_drift(self):
        current = self.current()
        identities = current["identity"]["userAssignedIdentities"]
        current["identity"]["userAssignedIdentities"] = {
            key.lower(): value for key, value in identities.items()}
        cutover.prepare_cutover(current, "3", "official-test-01")

    def test_snapshot_hashes_configuration_outside_the_template(self):
        original = self.current()
        changed = copy.deepcopy(original)
        changed["properties"]["networking"] = {"new_setting": True}
        changed["tags"] = {"external-change": "detected"}
        self.assertNotEqual(cutover.snapshot(original)["unrelated_sha256"],
                            cutover.snapshot(changed)["unrelated_sha256"])

    def test_own_lock_contention_fails_closed_and_closes_descriptor(self):
        with patch.object(cutover.os, "open", return_value=123), \
                patch.object(cutover.os, "close") as close, \
                patch.object(cutover.fcntl, "flock", side_effect=BlockingIOError):
            with self.assertRaises(cutover.shared.DeploymentError):
                with cutover.operator_lock():
                    self.fail("Lock unexpectedly acquired")
        close.assert_called_once_with(123)

    def test_active_revision_traffic_and_replica_ready_are_actually_checked(self):
        current = self.current()
        current.pop("_ready_revision")
        revision = {"value": [{"name": cutover.CHAT_REVISION, "properties": {
            "active": True, "healthState": "Healthy", "provisioningState": "Provisioned",
            "runningState": "RunningAtMaxScale", "trafficWeight": 100}}]}
        replica = {"value": [{"properties": {"runningState": "Running",
                                            "containers": [{"ready": True, "started": True}]}}]}
        with patch.object(cutover.shared, "arm", side_effect=[current, revision, replica]):
            self.assertEqual(cutover.snapshot(cutover.read_live())["revision"],
                             cutover.CHAT_REVISION)
        replica["value"][0]["properties"]["containers"][0]["ready"] = False
        with patch.object(cutover.shared, "arm", side_effect=[current, revision, replica]):
            with self.assertRaises(cutover.shared.DeploymentError):
                cutover.read_live()

    def test_invalid_or_reused_revision_suffix_is_rejected(self):
        for suffix in ("", None, "A-uppercase", "foo--bar", "ends-", "../path"):
            with self.subTest(suffix=suffix), self.assertRaises(cutover.shared.DeploymentError):
                cutover.prepare_cutover(self.current(), "3", suffix)
        current = self.current()
        current["_revision_names"] = [cutover.CHAT_REVISION, self.prepared()["expected_revision"]]
        with patch.object(cutover, "read_live", return_value=current), \
                patch.object(cutover, "operator_lock", return_value=nullcontext()), \
                patch.object(cutover.shared, "arm") as arm:
            prepared = self.prepared()
            with self.assertRaises(cutover.shared.DeploymentError):
                cutover.apply_prepared(
                    prepared, reviewed_artifact_sha256=cutover.fingerprint(prepared),
                    gates=self.gates)
        arm.assert_not_called()


if __name__ == "__main__":
    unittest.main()
