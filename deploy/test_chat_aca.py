"""Local synthetic ACA artifact tests; no cloud writes or dotenv reads."""

import unittest
from unittest.mock import patch
from pathlib import Path

import chat_aca as aca


class ChatAcaTests(unittest.TestCase):
    image = aca.REPOSITORY + "@sha256:" + "a" * 64

    def test_https_single_revision_one_replica_and_bounded_probes(self):
        body = aca.definition(self.image)
        config = body["properties"]["configuration"]
        self.assertEqual(config["activeRevisionsMode"], "Single")
        self.assertFalse(config["ingress"]["allowInsecure"])
        self.assertTrue(config["ingress"]["external"])
        template = body["properties"]["template"]
        self.assertEqual(template["scale"], {"minReplicas": 1, "maxReplicas": 1})
        probes = template["containers"][0]["probes"]
        self.assertEqual({p["type"] for p in probes}, {"Startup", "Readiness", "Liveness"})
        self.assertTrue(all(p["timeoutSeconds"] == 2 and p["httpGet"]["path"] == "/healthz" for p in probes))

    def test_separate_pull_identity_and_system_runtime_without_secrets(self):
        body = aca.definition(self.image)
        self.assertEqual(body["identity"]["type"], "SystemAssigned, UserAssigned")
        config = body["properties"]["configuration"]
        self.assertEqual(config["registries"][0]["identity"], aca.shared.IDENTITY)
        env = {e["name"]: e["value"] for e in body["properties"]["template"]["containers"][0]["env"]}
        self.assertEqual(env["PUBLIC_ORIGIN"], aca.ORIGIN)
        self.assertEqual(env["FOUNDRY_AGENT_VERSION"], "2")
        self.assertNotIn("AZURE_CLIENT_ID", env)
        self.assertNotIn("secrets", config)
        self.assertTrue(aca.PROJECT_ID.endswith("/projects/redshift-test-project"))
        self.assertEqual(set(aca.ROLES), {"eed3b665-ab3a-47b6-8f48-c9382fb1dad6",
                                        "a97b65f3-24c7-4388-baec-2e87135dc908"})

    def test_only_chat_digest_can_be_deployed(self):
        for image in ("redshift-chat:latest", self.image.replace("redshift-chat@", "redshift-mcp-server@"),
                      self.image.replace("@sha256:", ":sha256:"), self.image.upper(), None):
            with self.subTest(image=image), self.assertRaises(aca.shared.DeploymentError):
                aca.image_reference(image)

    def test_context_contains_only_container_source_not_local_runtime(self):
        files = aca.source_files()
        self.assertIn("server/index.ts", files)
        self.assertIn("client/index.html", files)
        self.assertNotIn("tests/app.test.ts", files)
        self.assertFalse(any(any(part.startswith(".") for part in Path(p).parts)
                             for p in files if p != ".dockerignore"))
        self.assertFalse(any(p.startswith(("node_modules/", "dist/", ".runtime/")) for p in files))
        self.assertEqual(len(aca.source_hash()), 64)

    def test_build_rejects_source_drift_before_cli(self):
        with patch.object(aca.shared, "cli") as cli:
            with self.assertRaises(aca.shared.DeploymentError):
                aca.build("0" * 64)
            cli.assert_not_called()

    def test_existing_app_is_never_overwritten(self):
        with patch.object(aca, "source_hash", return_value="a" * 64), \
             patch.object(aca, "EVIDENCE") as evidence, \
             patch.object(aca.shared, "cli", return_value={"digest": "sha256:" + "a" * 64}), \
             patch.object(aca.shared, "arm", return_value={"id": aca.APP_ID}) as arm:
            evidence.is_file.return_value = True
            evidence.is_symlink.return_value = False
            evidence.read_text.return_value = aca.json.dumps({
                "source_sha256": "a" * 64, "image": self.image, "tag": "reviewed",
            })
            with self.assertRaises(aca.shared.DeploymentError):
                aca.create(self.image, "a" * 64)
            self.assertEqual([call.args[0] for call in arm.call_args_list], ["GET"])

    def test_roles_only_target_project_and_new_system_principal(self):
        current = {"identity": {"principalId": "system-principal"}, "properties": {
            "environmentId": aca.shared.ENV_ID,
            "configuration": {"ingress": {"fqdn": aca.ORIGIN[8:]}},
            "template": {"containers": [{"image": self.image}]},
        }}
        with patch.object(aca.shared, "wait_resource", return_value=current), \
             patch.object(aca.shared, "role") as role:
            aca.grant_roles(self.image)
            self.assertEqual(role.call_count, 2)
            self.assertTrue(all(c.args[:2] == ("system-principal", aca.PROJECT_ID)
                                for c in role.call_args_list))


if __name__ == "__main__":
    unittest.main()
