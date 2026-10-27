import json
import importlib.util
import unittest
from unittest.mock import patch, MagicMock

import chat_deploy as c
import runtime_package as r


class PackageTests(unittest.TestCase):
    def test_pem_parser_label_is_not_key_material(self):
        self.assertFalse(r.credential_signature(b"const label = '-----BEGIN PRIVATE KEY-----';"))
        self.assertTrue(r.credential_signature(b"-----BEGIN PRIVATE KEY-----\n" + b"A" * 64))
        self.assertTrue(r.credential_signature(b"-----BEGIN PRIVATE KEY-----\\n" + b"A" * 64))

    def test_submitted_id_not_unrelated_completed_record(self):
        spec = importlib.util.spec_from_file_location("package_release_test", c.ARTIFACTS / "run-package-release.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        submitted = "11111111-2222-3333-4444-555555555555"
        self.assertEqual(module.deployment_id({"properties": {"deploymentId": submitted}}), submitted)
        for value in ({}, {"id": "unattributable"},
                      {"id": submitted, "deploymentId": "66666666-7777-8888-9999-000000000000"}):
            with self.assertRaises(c.DeploymentError):
                module.deployment_id(value)

    def test_link_guard_precedes_file_read(self):
        with patch("pathlib.Path.is_symlink", return_value=True):
            with self.assertRaises(c.DeploymentError):
                r.safe_path(c.ARTIFACTS / "linked.zip")

    def test_source_zip_guard_before_cloud(self):
        with patch.object(c, "source_manifest", return_value=({}, r.SOURCE)), \
                patch.object(r, "safe_path") as path, patch.object(c, "request") as request:
            path.return_value.read_bytes.return_value = b"changed-source-zip"
            with self.assertRaises(c.DeploymentError):
                r.validate_artifact({})
            request.assert_not_called()

    def test_exact_two_mode_changes(self):
        before = c.app_settings("endpoint", "host", "2")
        after = c.app_settings("endpoint", "host", "2", deployment_mode="run_from_package")
        changed = {key for key in before.keys() | after.keys() if before.get(key) != after.get(key)}
        self.assertEqual(changed, {"SCM_DO_BUILD_DURING_DEPLOYMENT", "WEBSITE_RUN_FROM_PACKAGE"})
        self.assertEqual(after["WEBSITE_RUN_FROM_PACKAGE"], "1")
        self.assertEqual(after["SCM_DO_BUILD_DURING_DEPLOYMENT"], "false")

    def test_unknown_mode_rejected(self):
        with self.assertRaises(c.DeploymentError):
            c.app_settings("a", "b", "2", deployment_mode="unsafe")

    def test_paths_fail_closed(self):
        for name in ("/abs", "../bad", "dist/../bad", "node_modules/x/.env",
                     "node_modules/x/.npmrc", "server/config.ts", "node_modules/.bin/tsc"):
            self.assertFalse(r.allowed(name), name)
        for name in ("package.json", "package-lock.json", "dist/server/index.js",
                     "dist/client/index.html", "node_modules/@azure/identity/package.json"):
            self.assertTrue(r.allowed(name), name)

    def test_manifest_guard_before_cloud(self):
        with patch.object(r, "MANIFEST") as manifest, patch.object(c, "request") as request:
            manifest.read_text.return_value = "{}"
            with self.assertRaises(c.DeploymentError):
                r.verify_mount({"runtime_manifest_sha256": "wrong"})
            request.assert_not_called()

    def test_mount_writable_or_wrong_package_fails(self):
        for report in ({"readonly": False}, {"readonly": True, "package_sha256": "wrong"}):
            with patch.object(r, "MANIFEST") as manifest, patch.object(c, "request") as request:
                manifest.read_text.return_value = "{}"
                request.return_value = {"ExitCode": 0, "Output": json.dumps(report)}
                with self.assertRaises(c.DeploymentError):
                    r.verify_mount({"runtime_manifest_sha256": c.sha({}), "zip_sha256": "expected"})

    def test_new_state_schema_explicit(self):
        self.assertTrue({"deployment_mode", "runtime_manifest_sha256", "source_zip_sha256"} <= c.STATE_KEYS)


if __name__ == "__main__":
    unittest.main()
