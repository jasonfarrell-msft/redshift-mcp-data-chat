"""Credential-free deployment tests. No cloud operations or dotenv access."""

import asyncio
import copy
import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.error import HTTPError

import chat_deploy as chat


class SourceFile:
    def __init__(self, name, value=b"synthetic", linked=False):
        self.name = name
        self.suffix = Path(name).suffix
        self.parents = ()
        self.linked = linked
        self.read_bytes = MagicMock(return_value=value)

    def __lt__(self, other):
        return self.name < other.name

    def relative_to(self, directory):
        return Path(self.name)

    def is_symlink(self):
        return self.linked

    def is_dir(self):
        return False


class ChatDeployTests(unittest.TestCase):
    REFERENCE = {
        "oil_bbl_sum": "1234.56", "gas_mcf_sum": "7890.12", "operating_cost_usd_sum": "987.65",
        "january_oil": "123.45", "well_id": "synthetic-well", "top_gas": "678.90",
        "state": "TX", "state_oil": "234.56", "oil_usd_per_bbl_avg": "60.59",
        "wells_count": "1000",
    }

    def setUp(self):
        self.enterContext(patch.object(chat, "analytics_reference", return_value=dict(self.REFERENCE)))

    @staticmethod
    def dataset_results():
        def result(source, items, truncated=False):
            return SimpleNamespace(isError=False, structuredContent={
                "version": "1", "executed": True, "status": "truncated" if truncated else "ok",
                "source": "oge_synthetic." + source, "items": items, "truncated": truncated,
            })
        r = ChatDeployTests.REFERENCE
        return [
            SimpleNamespace(isError=False, structuredContent={"connected": True}),
            SimpleNamespace(isError=False, structuredContent={"schema": "oge_synthetic"}),
            result("daily_production", [{key: r[key] for key in
                                        ("oil_bbl_sum", "gas_mcf_sum", "operating_cost_usd_sum")}]),
            result("monthly_production", [{"oil_bbl_sum": r["january_oil"]}]),
            result("annual_production", [{"oil_bbl_sum": r["oil_bbl_sum"]}]),
            result("daily_production", [{"gas_mcf_sum": r["top_gas"], "well_id": r["well_id"]}],
                   truncated=True),
            result("daily_production", [{"oil_bbl_sum": r["state_oil"], "state": r["state"]}],
                   truncated=True),
            result("monthly_prices", [{"oil_usd_per_bbl_avg": r["oil_usd_per_bbl_avg"]}]),
            result("wells", [{"wells_count": r["wells_count"]}]),
        ]

    def run_mcp_acceptance(self, results):
        client = AsyncMock()
        client.list_tools.return_value = SimpleNamespace(
            tools=[SimpleNamespace(name=name) for name in chat.MCP_TOOLS],
        )
        client.call_tool.side_effect = results
        session = MagicMock()
        session.__aenter__.return_value = client
        transport = MagicMock()
        transport.__aenter__.return_value = (None, None, None)
        with (patch("mcp.ClientSession", return_value=session),
              patch("mcp.client.streamable_http.streamable_http_client",
                    return_value=transport) as stream):
            asyncio.run(chat.mcp_acceptance(self.REFERENCE))
        stream.assert_called_once_with(chat.MCP_URL)
        return client

    def test_direct_mcp_requires_all_five_sources_and_independent_numbers(self):
        client = self.run_mcp_acceptance(self.dataset_results())
        calls = [call.args for call in client.call_tool.await_args_list]
        self.assertEqual(calls[:2], [("test_connection", {}), ("get_data_context", {})])
        self.assertEqual(len(calls), 9)
        self.assertTrue(all(call[0] == "analyze_data" and set(call[1]) == {"plan"}
                            for call in calls[2:]))
        self.assertEqual(calls[3][1]["plan"]["time_bucket"], "month")
        self.assertEqual(calls[4][1]["plan"]["time_bucket"], "year")

    def test_direct_mcp_rejects_incorrect_numbers_empty_wrong_source_and_missing_execution(self):
        for stage in range(2, 9):
            for defect in ("empty", "wrong_number", "error", "not_executed", "text_only",
                           "wrong_scope"):
                with self.subTest(stage=stage, defect=defect):
                    results = self.dataset_results()
                    value = results[stage]
                    if defect == "empty":
                        value.structuredContent["items"] = []
                    elif defect == "wrong_number":
                        for key in value.structuredContent["items"][0]:
                            value.structuredContent["items"][0][key] = "999999.99"
                    elif defect == "error":
                        value.isError = True
                    elif defect == "not_executed":
                        value.structuredContent["executed"] = False
                    elif defect == "text_only":
                        value.structuredContent = None
                    else:
                        value.structuredContent["source"] = "another_schema.daily_production"
                    with self.assertRaises(chat.DeploymentError):
                        self.run_mcp_acceptance(results)

    def test_direct_mcp_rejects_missing_or_incorrect_context(self):
        for value in (None, {"schema": "other"}, {}):
            results = self.dataset_results()
            results[1].structuredContent = value
            with self.subTest(value=value), self.assertRaises(chat.DeploymentError):
                self.run_mcp_acceptance(results)

    def test_agent_answer_requires_exact_numeric_value_unit_period_and_actual_tool_evidence(self):
        good = {"reply": "In 2025: 1,234.56 bbl.", "toolNames": ["analyze_data"]}
        chat.agent_answer(good, "1234.56", "bbl")
        for change in (
            {"reply": ""}, {"reply": "The schema contains production tables."},
            {"reply": "2025: 1234.57 bbl"}, {"reply": "2025: 1234.56 USD"},
            {"reply": "2024: 1234.56 bbl"}, {"toolNames": []},
            {"toolNames": ["test_connection"]}, {"toolNames": ["analyze_data", "query"]},
            {"toolNames": ["analyze_data"] * 5},
            {"toolNames": "analyze_data"}, {"toolNames": [None]}, {"truncated": True},
        ):
            with self.subTest(change=change), self.assertRaises(chat.DeploymentError):
                chat.agent_answer(dict(good, **change), "1234.56", "bbl")

    def test_agent_followup_requires_new_analysis_exact_number_and_continuation(self):
        good = {"reply": "For 2025: 7890.12 Mcf.", "toolNames": ["analyze_data"], "continued": True}
        chat.agent_answer(good, "7890.12", "Mcf", continued=True)
        for change in ({"continued": False}, {"continued": None},
                       {"toolNames": ["get_data_context"]}, {"reply": "No gas data"}):
            with self.subTest(change=change), self.assertRaises(chat.DeploymentError):
                chat.agent_answer(dict(good, **change), "7890.12", "Mcf", continued=True)

    def test_non_data_templates_cannot_pass_numeric_release_acceptance(self):
        for reply in (
            "Which inclusive date range should I analyze?",
            "That calculation is not supported.",
            "The executed analysis returned no observations. No total or zero value can be inferred.",
            "The executed analysis returned a partial result. Narrow the date range or grouping and ask again; no complete answer is available.",
            '{"kind":"answer","reply":"In 2025: 1234.56 bbl."}',
        ):
            with self.subTest(reply=reply), self.assertRaises(chat.DeploymentError):
                chat.agent_answer({"reply": reply, "toolNames": ["analyze_data"]}, "1234.56", "bbl")

    def test_verify_dataset_conversation_uses_same_cookie_and_persists_only_success(self):
        origin = "https://app.azurewebsites.net"
        state = {"agent_sha256": chat.sha(chat.agent_definition()), "agent_version": "1",
                 "deployed_source_sha256": "source", "source_sha256": "source",
                 "deployed_zip_sha256": "zip", "zip_sha256": "zip"}
        first = {"reply": "2025: 1234.56 bbl", "toolNames": ["analyze_data"]}
        second = {"reply": "2025: 7890.12 Mcf", "toolNames": ["analyze_data"], "continued": True}
        cookie = SimpleNamespace(
            secure=True, has_nonstandard_attr=lambda name: name == "HttpOnly",
            get_nonstandard_attr=lambda name, default: "Strict",
        )
        from contextlib import ExitStack
        for defect in (None, "schema_empty", "tables_empty", "no_continuation", "no_table_tool"):
            with self.subTest(defect=defect), ExitStack() as stack:
                for name, value in (
                    ("inventory", ("endpoint", "app.azurewebsites.net", "mi")),
                    ("read_state", state), ("data_plane", {"definition": chat.agent_definition()}),
                    ("verify_app_settings", None), ("verify_cors", None),
                    ("arm", {"properties": {"configuration": {
                        "ingress": {"corsPolicy": chat.cors_policy(origin)},
                    }}}), ("source_manifest", ({}, "source")),
                ):
                    stack.enter_context(patch.object(chat, name, return_value=value))
                direct = stack.enter_context(patch.object(chat, "mcp_acceptance", new_callable=AsyncMock))
                stack.enter_context(patch.object(chat.http.cookiejar, "CookieJar", return_value=[cookie]))
                opener = stack.enter_context(patch.object(chat, "build_opener")).return_value
                save = stack.enter_context(patch.object(chat, "save_state"))
                first_response, second_response = dict(first), dict(second)
                if defect == "schema_empty":
                    first_response["reply"] = "No schemas."
                elif defect == "tables_empty":
                    second_response["reply"] = "No tables."
                elif defect == "no_continuation":
                    second_response["continued"] = False
                elif defect == "no_table_tool":
                    second_response["toolNames"] = []
                responses = [
                    (200, {}, b"ok"), (200, {}, b"ok"),
                    {"status": "healthy", "connected": True,
                     "checkedAt": datetime.now(timezone.utc).isoformat()},
                    first_response, second_response,
                ]
                request = stack.enter_context(patch.object(chat, "request", side_effect=responses))
                if defect:
                    with self.assertRaises(chat.DeploymentError):
                        chat.verify()
                    save.assert_not_called()
                else:
                    with redirect_stdout(io.StringIO()):
                        chat.verify()
                    save.assert_called_once()
                    self.assertEqual(save.call_args.kwargs["verified_source_sha256"], "source")
                    chats = [call for call in request.call_args_list if call.args[0] == "POST"]
                    self.assertEqual(len(chats), 2)
                    self.assertIn("same period", chats[1].args[2]["message"])
                    self.assertIn("exact unrounded total in Mcf", chats[1].args[2]["message"])
                    for call in chats:
                        self.assertIs(call.kwargs["opener"], opener)
                        self.assertEqual(call.kwargs["headers"], {"Origin": origin})
                        self.assertEqual(call.kwargs["timeout"], 120)
                direct.assert_awaited_once()

    @staticmethod
    def source(extra=()):
        directory = MagicMock()
        directory.is_dir.return_value = True
        directory.is_symlink.return_value = False
        selected = [SourceFile(name) for name in (
            "package.json", "package-lock.json", "client/index.html", "server/index.ts",
        )]
        directory.rglob.return_value = selected + list(extra)
        return directory, selected

    def test_source_allowlist_never_opens_dotenv_hidden_tests_or_modules(self):
        excluded = [SourceFile(name, b"never-read") for name in (
            ".env", ".env.production", ".git/config", ".squad/team.md",
            "tests/test.ts", "node_modules/pkg/index.js", "dist/server/index.js",
            "server/.env", "server/not-allowlisted.pem", "credentials.json",
        )]
        directory, selected = self.source(excluded)
        files, digest = chat.source_manifest(directory)
        self.assertEqual(set(files), {file.name for file in selected})
        self.assertEqual(len(digest), 64)
        for file in excluded:
            file.read_bytes.assert_not_called()

    def test_source_rejects_links_before_read(self):
        link = SourceFile("server/linked.ts", linked=True)
        directory, _ = self.source([link])
        with self.assertRaisesRegex(chat.DeploymentError, "Linked source"):
            chat.source_manifest(directory)
        link.read_bytes.assert_not_called()

    def test_source_scan_rejects_credential_patterns_without_printing_them(self):
        file = SourceFile("server/example.ts", b'const api_key = "syntheticcredentialvalue";')
        directory, _ = self.source([file])
        with self.assertRaisesRegex(chat.DeploymentError, "^Possible credential"):
            chat.source_manifest(directory)

    def test_source_manifest_changes_when_runtime_source_changes(self):
        directory, files = self.source()
        first = chat.source_manifest(directory)[1]
        files[-1].read_bytes.return_value = b"changed code"
        second = chat.source_manifest(directory)[1]
        self.assertNotEqual(first, second)

    def test_source_requires_complete_application(self):
        directory, _ = self.source()
        directory.rglob.return_value = [SourceFile("package.json")]
        with self.assertRaisesRegex(chat.DeploymentError, "incomplete"):
            chat.source_manifest(directory)

    def test_default_is_read_only(self):
        with patch.object(chat, "preflight") as preflight, patch.object(chat, "prerequisites") as mutate:
            self.assertEqual(chat.main([]), 0)
            preflight.assert_called_once()
            mutate.assert_not_called()

    def test_mutations_require_both_apply_and_gate_attestation(self):
        for stage in ("prerequisites", "agent", "app", "configure", "verify", "all"):
            for flags in ([], ["--apply"], ["--gates-approved"]):
                with self.subTest(stage=stage, flags=flags), redirect_stderr(io.StringIO()):
                    self.assertEqual(chat.main(["--stage", stage, *flags]), 1)

    def test_all_stages_are_ordered_and_explicit(self):
        names = ["prerequisites", "agent", "build", "deploy_app", "configure", "verify"]
        calls = []
        from contextlib import ExitStack
        with ExitStack() as stack:
            for name in names:
                stack.enter_context(patch.object(chat, name, side_effect=lambda name=name: calls.append(name)))
            self.assertEqual(chat.main(["--stage", "all", "--apply", "--gates-approved"]), 0)
        self.assertEqual(calls, names)

    def test_unexpected_error_never_prints_raw_details(self):
        output = io.StringIO()
        with patch.object(chat, "preflight", side_effect=ValueError("sensitive-value")), redirect_stderr(output):
            self.assertEqual(chat.main([]), 1)
        self.assertNotIn("sensitive-value", output.getvalue())

    def test_cli_captures_output_and_scopes_every_call(self):
        result = SimpleNamespace(returncode=0, stdout='{"status":"ok"}')
        with patch.object(chat.subprocess, "run", return_value=result) as run:
            self.assertEqual(chat.cli("account", "show"), {"status": "ok"})
        args = run.call_args
        self.assertIn(chat.SUB, args.args[0])
        self.assertTrue(args.kwargs["capture_output"])
        self.assertEqual(args.kwargs["env"]["TMPDIR"], str(chat.DEPLOY))
        self.assertEqual(args.kwargs["timeout"], 300)

    def test_cli_failures_are_sanitized(self):
        result = SimpleNamespace(returncode=1, stdout="secret-body", stderr="secret-error")
        with patch.object(chat.subprocess, "run", return_value=result):
            with self.assertRaisesRegex(chat.DeploymentError, "details suppressed"):
                chat.cli("webapp", "deploy")

    def test_no_http_or_out_of_subscription_arm(self):
        with self.assertRaises(chat.DeploymentError):
            chat.request("GET", "http://example.invalid")
        with self.assertRaises(chat.DeploymentError):
            chat.arm("GET", "/subscriptions/other/resources", chat.WEB_API)

    def test_no_redirects(self):
        self.assertIsNone(chat.NoRedirect().redirect_request(None, None, 302, "", {}, "https://other.invalid"))

    def test_http_403_is_terminal_and_body_not_read(self):
        body = MagicMock()
        opener = MagicMock()
        opener.open.side_effect = HTTPError("https://example.invalid", 403, "forbidden", {}, body)
        with self.assertRaisesRegex(chat.DeploymentError, "HTTP 403.*no fallback"):
            chat.request("POST", "https://example.invalid", {}, opener=opener)
        body.read.assert_not_called()
        self.assertEqual(opener.open.call_count, 1)

    def test_rate_limit_server_error_and_timeout_are_terminal_without_retry(self):
        for error in (
            HTTPError("https://example.invalid", 429, "limited", {}, None),
            HTTPError("https://example.invalid", 503, "unavailable", {}, None),
            TimeoutError("sensitive timeout details"),
        ):
            with self.subTest(error=type(error).__name__):
                opener = MagicMock()
                opener.open.side_effect = error
                with self.assertRaises(chat.DeploymentError) as raised:
                    chat.request("POST", "https://example.invalid/api/chat", {},
                                 opener=opener, timeout=120)
                self.assertNotIn("sensitive", str(raised.exception))
                self.assertEqual(opener.open.call_count, 1)
                self.assertEqual(opener.open.call_args.kwargs["timeout"], 120)

    def test_only_explicit_404_is_optional(self):
        opener = MagicMock()
        opener.open.side_effect = HTTPError("https://example.invalid", 404, "", {}, None)
        self.assertIsNone(chat.request("GET", "https://example.invalid", missing=True, opener=opener))
        with self.assertRaises(chat.DeploymentError):
            chat.request("GET", "https://example.invalid", opener=opener)

    def test_non_json_response_still_fails_for_json_requests(self):
        opener = MagicMock()
        response = opener.open.return_value.__enter__.return_value
        response.read.return_value = b"ok\n"
        with self.assertRaisesRegex(chat.DeploymentError, "HTTPS transport/JSON failure"):
            chat.request("GET", "https://example.invalid/api/health", opener=opener)

    def test_tokens_stay_in_http_headers(self):
        opener = MagicMock()
        response = opener.open.return_value.__enter__.return_value
        response.read.return_value = b'{"ok":true}'
        with patch.object(chat, "token", return_value="synthetic-token"):
            self.assertEqual(chat.request("GET", "https://example.invalid", scope="scope", opener=opener), {"ok": True})
        request = opener.open.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer synthetic-token")
        self.assertNotIn("synthetic-token", request.full_url)

    def test_actual_endpoint_required_not_synthesized(self):
        endpoint = f"https://{chat.ACCOUNT}.services.ai.azure.com/api/projects/{chat.PROJECT}"
        self.assertEqual(chat.project_endpoint({"properties": {"endpoints": {"api": endpoint}}}), endpoint)
        for bad in ({}, {"properties": {"endpoints": {"api": endpoint + "?key=bad"}}},
                    {"properties": {"endpoints": {"api": endpoint.replace(chat.PROJECT, "another-project")}}}):
            with self.assertRaises(chat.DeploymentError):
                chat.project_endpoint(bad)

    def test_hostname_is_actual_azure_host(self):
        host = chat.APP + "-abc.eastus2-01.azurewebsites.net"
        self.assertEqual(chat.hostname({"properties": {"defaultHostName": host}}), host)
        for value in ("https://example.invalid", "evil.azurewebsites.net/path", "example.invalid"):
            with self.assertRaises(chat.DeploymentError):
                chat.hostname({"properties": {"defaultHostName": value}})

    def test_agent_exact_tool_scope_and_scoped_no_approval(self):
        definition = chat.agent_definition()
        self.assertEqual(definition["kind"], "prompt")
        self.assertEqual(definition["model"], chat.MODEL)
        self.assertEqual(len(definition["tools"]), 1)
        tool = definition["tools"][0]
        self.assertEqual(tool["server_url"], chat.MCP_URL)
        self.assertEqual(tool["server_label"], "redshift")
        self.assertEqual(tool["allowed_tools"], {"tool_names": list(chat.TOOLS)})
        self.assertEqual(tool["require_approval"], {"never": {"tool_names": list(chat.TOOLS)}})
        self.assertNotIn("headers", tool)
        self.assertNotIn("project_connection_id", tool)

    def test_agent_instructions_match_fail_closed_bff_protocol(self):
        instructions = chat.agent_definition()["instructions"]
        for example in (
            '{"kind":"answer","reply":"<concise grounded natural-language answer>"}',
            '{"kind":"clarification","reason":"missing_period"}',
            '{"kind":"clarification","reason":"ambiguous_request"}',
            '{"kind":"unsupported","reason":"unsupported_metric"}',
            '{"kind":"unsupported","reason":"unsupported_scope"}',
        ):
            with self.subTest(example=example):
                self.assertIn(example, instructions)
        self.assertIn("execution in THIS response", instructions)
        self.assertIn("Non-data objects must have no reply or other fields", instructions)
        self.assertIn("For every data answer", instructions)

    def test_agent_definition_digest_is_stable(self):
        self.assertEqual(chat.sha(chat.agent_definition()), chat.sha(chat.agent_definition()))
        changed = chat.agent_definition()
        changed["tools"][0]["allowed_tools"]["tool_names"].append("query")
        self.assertNotEqual(chat.sha(changed), chat.sha(chat.agent_definition()))
        self.assertFalse(chat.agent_matches({"definition": changed}, chat.agent_definition()))

    def test_chat_artifact_is_source_addressed_and_never_the_previous_static_zip(self):
        first = chat.package_path("a" * 64)
        second = chat.package_path("b" * 64)
        self.assertNotEqual(first, second)
        self.assertEqual(first.parent, chat.ARTIFACTS)
        self.assertEqual(first.name, "redshift-chat-" + "a" * 64 + ".zip")
        self.assertNotEqual(first.name, "redshift-chat.zip")
        for bad in ("", "../other", "x" * 64, None):
            with self.subTest(bad=bad), self.assertRaises(chat.DeploymentError):
                chat.package_path(bad)

    def immutable_build_fixture(self):
        files = {"package.json": b"synthetic package", "server/index.ts": b"synthetic source"}
        artifacts = MagicMock()
        artifacts.is_symlink.return_value = False
        target = MagicMock()
        target.is_symlink.return_value = False
        target.exists.return_value = True
        target.read_bytes.return_value = b"synthetic immutable ZIP"
        archive = MagicMock()
        archive.namelist.return_value = list(files)
        archive.getinfo.side_effect = lambda name: SimpleNamespace(file_size=len(files[name]))
        archive.read.side_effect = lambda name: files[name]
        manager = MagicMock()
        manager.__enter__.return_value = archive
        self.enterContext(patch.object(chat, "ARTIFACTS", artifacts))
        self.enterContext(patch.object(chat, "package_path", return_value=target))
        self.enterContext(patch.object(chat, "source_manifest", return_value=(files, "a" * 64)))
        self.enterContext(patch.object(chat, "local_check"))
        save = self.enterContext(patch.object(chat, "save_state"))
        zip_open = self.enterContext(patch.object(chat.zipfile, "ZipFile", return_value=manager))
        return target, archive, save, zip_open

    def test_build_reuses_matching_immutable_zip_without_overwriting(self):
        target, archive, save, zip_open = self.immutable_build_fixture()
        with redirect_stdout(io.StringIO()):
            chat.build()
        zip_open.assert_called_once_with(target)
        archive.writestr.assert_not_called()
        save.assert_called_once()

    def test_build_rejects_tampered_existing_zip_without_overwriting(self):
        target, archive, save, zip_open = self.immutable_build_fixture()
        archive.read.side_effect = None
        archive.read.return_value = b"tampered"
        with self.assertRaisesRegex(chat.DeploymentError, "differs from reviewed source"):
            chat.build()
        zip_open.assert_called_once_with(target)
        archive.writestr.assert_not_called()
        save.assert_not_called()

    def test_data_plane_is_v1_and_memory_credential(self):
        endpoint = f"https://{chat.ACCOUNT}.services.ai.azure.com/api/projects/{chat.PROJECT}"
        with patch.object(chat, "request", return_value={}) as request:
            chat.data_plane("GET", endpoint, "/agents/redshift-chat-agent/versions?limit=100")
        self.assertEqual(request.call_args.args[1], endpoint + "/agents/redshift-chat-agent/versions?limit=100&api-version=v1")
        self.assertEqual(request.call_args.kwargs["scope"], "https://ai.azure.com/.default")

    def test_agent_version_is_idempotently_reused_and_read_back(self):
        endpoint = f"https://{chat.ACCOUNT}.services.ai.azure.com/api/projects/{chat.PROJECT}"
        version = {"version": "1", "definition": chat.agent_definition()}
        version["definition"]["tools"][0]["allowed_tools"] = {
            "tool_names": list(chat.TOOLS),
        }
        self.assertTrue(chat.agent_matches(version, chat.agent_definition()))
        with (patch.object(chat, "inventory", return_value=(endpoint, "app.azurewebsites.net", "mi")),
              patch.object(chat, "data_plane", side_effect=[{"data": [version]}, version]) as data,
              patch.object(chat, "save_state") as save, redirect_stdout(io.StringIO())):
            chat.agent()
        self.assertTrue(all(call.args[0] == "GET" for call in data.call_args_list))
        self.assertEqual(save.call_args.kwargs["agent_version"], "1")
        self.assertIsNone(save.call_args.kwargs["verified_at"])

    def test_agent_canonical_filter_rejects_extra_tools_or_filter_fields(self):
        for allowed in (
            {"tool_names": [*chat.TOOLS, "query"]},
            {"tool_names": list(chat.TOOLS), "read_only": True},
            {"tool_names": list(chat.TOOLS[:-1])},
            list(chat.TOOLS),
        ):
            with self.subTest(allowed=allowed):
                changed = chat.agent_definition()
                changed["tools"][0]["allowed_tools"] = allowed
                self.assertFalse(chat.agent_matches({"definition": changed}, chat.agent_definition()))

    def test_agent_new_version_never_trusts_metadata_alone(self):
        desired = {"version": "2", "definition": chat.agent_definition()}
        wrong = copy.deepcopy(desired)
        wrong["definition"]["model"] = "unapproved"
        wrong["metadata"] = {"redshift_definition_sha256": chat.sha(chat.agent_definition())}
        with (patch.object(chat, "inventory", return_value=(
                f"https://{chat.ACCOUNT}.services.ai.azure.com/api/projects/{chat.PROJECT}",
                "app.azurewebsites.net", "mi")),
              patch.object(chat, "data_plane", side_effect=[{"data": [wrong]}, desired, desired]) as data,
              patch.object(chat, "save_state"), redirect_stdout(io.StringIO())):
            chat.agent()
        self.assertEqual(data.call_args_list[1].args[0], "POST")
        self.assertIn("/versions", data.call_args_list[1].args[2])

    @staticmethod
    def role(scope=None, definition=chat.CONSUMER, principal=chat.APP_PRINCIPAL):
        return {"principalId": principal, "scope": scope or chat.PROJECT_ID,
                "roleDefinitionId": chat.BASE + "/providers/Microsoft.Authorization/roleDefinitions/" + definition}

    def approved_roles(self):
        return [self.role(definition=role) for role in sorted(chat.RUNTIME_ROLES)]

    def test_exact_two_project_roles_can_pass_role_gate(self):
        with patch.object(chat, "cli", return_value=self.approved_roles()) as cli:
            chat.verify_roles(chat.APP_PRINCIPAL)
        self.assertIn("--include-inherited", cli.call_args.args)
        self.assertIn("--include-groups", cli.call_args.args)

    def test_inherited_broad_or_group_grants_cannot_mask_smoke(self):
        for role in (
            self.role(chat.ACCOUNT_ID), self.role(chat.FOUNDRY_GROUP), self.role(chat.BASE),
            self.role(chat.ACCOUNT_ID, chat.COGNITIVE_SERVICES_USER),
            self.role(chat.FOUNDRY_GROUP, chat.COGNITIVE_SERVICES_USER),
            self.role(chat.BASE, chat.COGNITIVE_SERVICES_USER),
            self.role(chat.PROJECT_ID + "/other", chat.COGNITIVE_SERVICES_USER),
            self.role(definition="owner"), self.role(principal="group"),
            self.role(definition=chat.COGNITIVE_SERVICES_USER, principal="group"),
            dict(self.role(), condition="restricted"),
            dict(self.role(definition=chat.COGNITIVE_SERVICES_USER), condition="restricted"),
            dict(self.role(), roleDefinitionId="/subscriptions/other/providers/"
                 "Microsoft.Authorization/roleDefinitions/" + chat.CONSUMER),
            None,
        ):
            with self.subTest(role=role), patch.object(chat, "cli", return_value=[*self.approved_roles(), role]):
                with self.assertRaises(chat.DeploymentError):
                    chat.verify_roles(chat.APP_PRINCIPAL)

    def test_project_identity_account_grant_is_not_implicitly_accepted(self):
        with patch.object(chat, "cli", side_effect=[self.approved_roles(), [self.role(chat.ACCOUNT_ID)]]):
            with self.assertRaises(chat.DeploymentError):
                chat.verify_roles(chat.APP_PRINCIPAL, "project-mi")

    def test_project_identity_without_account_grants_passes(self):
        with patch.object(chat, "cli", side_effect=[self.approved_roles(), []]):
            chat.verify_roles(chat.APP_PRINCIPAL, "project-mi")

    def test_either_missing_role_or_duplicate_fails_closed(self):
        for roles in ([], [self.role()], [self.role(definition=chat.COGNITIVE_SERVICES_USER)],
                      [*self.approved_roles(), self.role()], {}, None):
            with self.subTest(roles=roles), patch.object(chat, "cli", return_value=roles):
                with self.assertRaises(chat.DeploymentError):
                    chat.verify_roles(chat.APP_PRINCIPAL)

    def test_role_gate_rejects_replaced_identity_before_enumeration(self):
        with patch.object(chat, "cli") as cli:
            with self.assertRaises(chat.DeploymentError):
                chat.verify_roles("mi")
            cli.assert_not_called()

    def test_role_enumeration_failure_is_not_assumed_safe(self):
        with patch.object(chat, "cli", side_effect=chat.DeploymentError("enumeration failed")):
            with self.assertRaises(chat.DeploymentError):
                chat.verify_roles(chat.APP_PRINCIPAL)

    def test_cors_is_exact_origin_and_transport_headers(self):
        policy = chat.cors_policy("https://app.azurewebsites.net")
        self.assertEqual(policy["allowedOrigins"], ["https://app.azurewebsites.net"])
        self.assertFalse(policy["allowCredentials"])
        self.assertEqual(set(policy["allowedMethods"]), {"GET", "POST", "DELETE", "OPTIONS"})
        self.assertEqual(policy["maxAge"], 600)
        self.assertIn("MCP-Protocol-Version", policy["allowedHeaders"])
        self.assertEqual(policy["exposeHeaders"], ["Mcp-Session-Id"])
        self.assertNotIn("*", json.dumps(policy))

    @staticmethod
    def mcp():
        return {"identity": {"principalId": "unchanged"}, "location": "brazilsouth", "tags": {},
                "properties": {"configuration": {"ingress": {"fqdn": "mcp", "allowInsecure": False},
                                                   "secrets": [{"name": "ref", "keyVaultUrl": "https://vault.invalid/secret"}]},
                               "template": {"containers": [{"image": "original-digest", "env": [{"secretRef": "ref"}]}]}}}

    def test_cors_patch_changes_only_ingress_cors(self):
        before = self.mcp()
        after = copy.deepcopy(before)
        policy = chat.cors_policy("https://app.azurewebsites.net")
        after["properties"]["configuration"]["ingress"]["corsPolicy"] = policy
        with (patch.object(chat, "inventory", return_value=("endpoint", "app.azurewebsites.net", "mi")),
              patch.object(chat, "arm", side_effect=[before, {}]) as arm,
              patch.object(chat, "wait_resource", return_value=after),
              patch.object(chat, "save_state"), redirect_stdout(io.StringIO())):
            chat.configure()
        self.assertEqual(arm.call_args.args, ("PATCH", chat.MCP_ID, chat.ACA_API,
                         {"properties": {"configuration": {"ingress": {"corsPolicy": policy}}}}))
        self.assertEqual(chat.protected_mcp(before), chat.protected_mcp(after))

    def test_cors_roundtrip_detects_image_or_secret_reference_change(self):
        for change in ("identity", "template", "configuration"):
            before = self.mcp()
            after = copy.deepcopy(before)
            if change == "identity":
                after["identity"]["principalId"] = "changed"
            elif change == "template":
                after["properties"]["template"]["containers"][0]["image"] = "changed"
            else:
                after["properties"]["configuration"]["secrets"] = []
            self.assertNotEqual(chat.protected_mcp(before), chat.protected_mcp(after))

    def test_cors_preflight_requires_actual_headers(self):
        origin = "https://app.azurewebsites.net"
        headers = {"Access-Control-Allow-Origin": origin,
                   "Access-Control-Allow-Methods": "GET,POST,DELETE,OPTIONS",
                   "Access-Control-Allow-Headers": "Content-Type,Mcp-Session-Id,MCP-Protocol-Version"}
        with patch.object(chat, "request", side_effect=[(204, headers, b""), (204, {}, b"")]):
            chat.verify_cors(origin)
        headers["Access-Control-Allow-Origin"] = "*"
        with patch.object(chat, "request", return_value=(204, headers, b"")):
            with self.assertRaises(chat.DeploymentError):
                chat.verify_cors(origin)

    def test_nonsecret_settings_have_only_server_owned_target(self):
        settings = chat.app_settings("endpoint", "actual.azurewebsites.net", "3")
        self.assertEqual(settings["PUBLIC_ORIGIN"], "https://actual.azurewebsites.net")
        self.assertEqual(settings["PORT"], "8080")
        self.assertEqual(settings["FOUNDRY_AGENT_VERSION"], "3")
        self.assertTrue(all(not any(s in name for s in ("KEY", "SECRET", "PASSWORD")) for name in settings))
        self.assertEqual(settings["SCM_DO_BUILD_DURING_DEPLOYMENT"], "true")
        self.assertEqual(settings["NPM_CONFIG_PRODUCTION"], "false")
        self.assertIn("npm prune", settings["POST_BUILD_COMMAND"])

    def test_health_requires_actual_connection_and_recent_timestamp(self):
        now = datetime.now(timezone.utc)
        good = {"status": "healthy", "connected": True, "checkedAt": now.isoformat()}
        self.assertTrue(chat.current_health(good))
        for change in (
            {"status": "stale"}, {"connected": False}, {"connected": None},
            {"checkedAt": (now - timedelta(seconds=36)).isoformat()},
            {"checkedAt": (now + timedelta(seconds=20)).isoformat()},
            {"checkedAt": "not-a-date"}, {"checkedAt": None},
        ):
            self.assertFalse(chat.current_health(dict(good, **change)))

    def process_health_fixture(self, app_status=200, mcp_status=200):
        origin = "https://app.azurewebsites.net"
        state = {
            "agent_sha256": chat.sha(chat.agent_definition()), "agent_version": "1",
            "deployed_source_sha256": "source", "source_sha256": "source",
            "deployed_zip_sha256": "zip", "zip_sha256": "zip",
        }
        for name, value in (
            ("inventory", ("endpoint", "app.azurewebsites.net", "mi")),
            ("read_state", state),
            ("data_plane", {"definition": chat.agent_definition()}),
            ("verify_app_settings", None),
            ("arm", {"properties": {"configuration": {
                "ingress": {"corsPolicy": chat.cors_policy(origin)},
            }}}),
            ("verify_cors", None),
        ):
            self.enterContext(patch.object(chat, name, return_value=value))
        opener = MagicMock()
        responses = []
        for status, content_type, body in (
            (app_status, "application/json", b'{"status":"alive"}'),
            (mcp_status, "text/plain", b"ok\n"),
        ):
            response = MagicMock()
            response.status = status
            response.headers = {"Content-Type": content_type}
            response.read.return_value = body
            manager = MagicMock()
            manager.__enter__.return_value = response
            responses.append(manager)
        opener.open.side_effect = responses
        self.enterContext(patch.object(chat, "build_opener", return_value=opener))
        acceptance = self.enterContext(patch.object(
            chat, "mcp_acceptance", new_callable=AsyncMock,
            side_effect=chat.DeploymentError("MCP acceptance reached"),
        ))
        return opener, acceptance

    def test_verify_accepts_plaintext_mcp_and_json_app_process_health(self):
        opener, acceptance = self.process_health_fixture()
        with self.assertRaisesRegex(chat.DeploymentError, "^MCP acceptance reached$"):
            chat.verify()
        self.assertEqual(
            [call.args[0].full_url for call in opener.open.call_args_list],
            ["https://app.azurewebsites.net/healthz", chat.MCP_ORIGIN + "/healthz"],
        )
        acceptance.assert_awaited_once_with(self.REFERENCE)

    def test_verify_rejects_non_200_process_health_before_mcp_acceptance(self):
        for app_status, mcp_status in ((204, 200), (200, 204), (200, 503)):
            with self.subTest(app_status=app_status, mcp_status=mcp_status):
                _, acceptance = self.process_health_fixture(app_status, mcp_status)
                with self.assertRaisesRegex(chat.DeploymentError, "Process health.*HTTP 200"):
                    chat.verify()
                acceptance.assert_not_awaited()

    def test_runtime_settings_query_never_returns_unrecognized_values(self):
        expected = chat.app_settings("endpoint", "actual.azurewebsites.net", "3")
        with patch.object(chat, "cli", side_effect=[
            list(expected), [{"name": key, "value": value} for key, value in expected.items()],
        ]) as cli:
            chat.verify_app_settings("endpoint", "actual.azurewebsites.net", "3")
        self.assertEqual(cli.call_args_list[0].args[-1], "[].name")
        self.assertIn("contains(", cli.call_args_list[1].args[-1])

    def test_runtime_credential_override_names_block_smoke_without_reading_values(self):
        for name in ("AZURE_CLIENT_SECRET", "IDENTITY_ENDPOINT", "OPENAI_API_KEY", "FOUNDRY_API_KEY"):
            with self.subTest(name=name), patch.object(chat, "cli", return_value=[name]) as cli:
                with self.assertRaisesRegex(chat.DeploymentError, "mask managed-identity"):
                    chat.verify_app_settings("endpoint", "actual.azurewebsites.net", "3")
                self.assertEqual(cli.call_count, 1)

    def test_validation_rejects_existing_account_or_mcp_mutation(self):
        for resource in (chat.ACCOUNT_ID, chat.MCP_ID):
            result = {"status": "Succeeded", "changes": [{"resourceId": resource, "changeType": "Modify"}]}
            with self.subTest(resource=resource), patch.object(chat, "cli", side_effect=[{}, result]):
                with self.assertRaisesRegex(chat.DeploymentError, "out-of-scope"):
                    chat.validate()

    def test_validation_rejects_delete_even_for_owned_resource(self):
        result = {"status": "Succeeded", "changes": [{"resourceId": chat.APP_ID, "changeType": "Delete"}]}
        with patch.object(chat, "cli", side_effect=[{}, result]):
            with self.assertRaisesRegex(chat.DeploymentError, "destructive"):
                chat.validate()

    def test_validation_checks_new_project_app_and_role(self):
        result = {"status": "Succeeded", "changes": [
            {"resourceId": chat.APP_ID, "changeType": "Create"},
            {"resourceId": chat.PROJECT_ID, "changeType": "Create"},
            *[{"resourceId": resource, "changeType": "Create"}
              for resource in chat.ROLE_ASSIGNMENT_IDS],
        ]}
        with patch.object(chat, "cli", side_effect=[{}, result]), redirect_stdout(io.StringIO()):
            chat.validate()

    def test_assignment_ids_match_arm_guid_known_inputs(self):
        prefix = chat.PROJECT_ID + "/providers/Microsoft.Authorization/roleAssignments/"
        self.assertEqual(chat.ROLE_ASSIGNMENT_IDS, {
            prefix + "a2b0451e-4de4-5b0d-8dad-8567fe0633e2",
            prefix + "1d0a3438-808c-535c-a6da-79dda6fc03c0",
        })

    def test_validation_allows_ignore_only_in_approved_group_roots_and_children(self):
        resources = [chat.GROUP, chat.FOUNDRY_GROUP, chat.MCP_ID, chat.ACCOUNT_ID,
                     chat.ACCOUNT_ID + "/deployments/existing"]
        result = {"status": "Succeeded", "changes": [
            {"resourceId": resource.upper(), "changeType": "Ignore"} for resource in resources
        ]}
        with patch.object(chat, "cli", side_effect=[{}, result]), redirect_stdout(io.StringIO()) as output:
            chat.validate()
        self.assertIn('"Ignore": 5', output.getvalue())

    def test_validation_rejects_ignore_outside_approved_group_boundaries(self):
        for resource in (chat.BASE, chat.GROUP + "-other", chat.FOUNDRY_GROUP + "-other/resource",
                         chat.GROUP.replace(chat.SUB, "another-subscription") + "/resource",
                         f"{chat.BASE}/resourceGroups/other/providers/Microsoft.Web/sites/other", ""):
            result = {"status": "Succeeded", "changes": [
                {"resourceId": resource, "changeType": "Ignore"}
            ]}
            with self.subTest(resource=resource), patch.object(chat, "cli", side_effect=[{}, result]):
                with self.assertRaises(chat.DeploymentError):
                    chat.validate()

    def test_validation_rejects_out_of_scope_changes_even_inside_approved_groups(self):
        for resource in (chat.MCP_ID, chat.ACCOUNT_ID, chat.GROUP + "/providers/Microsoft.Web/sites/other",
                         f"{chat.BASE}/resourceGroups/other/providers/Microsoft.Web/sites/other"):
            for kind in ("Create", "Modify", "Delete", "Unsupported", "NoChange", "Unknown"):
                result = {"status": "Succeeded", "changes": [
                    {"resourceId": resource, "changeType": kind}
                ]}
                with self.subTest(resource=resource, kind=kind), patch.object(chat, "cli", side_effect=[{}, result]):
                    with self.assertRaises(chat.DeploymentError):
                        chat.validate()

    def test_validation_rejects_unsupported_unknown_or_malformed_owned_changes(self):
        for change in ({"resourceId": chat.APP_ID, "changeType": "Unsupported"},
                       {"resourceId": chat.APP_ID, "changeType": "Unknown"},
                       {"resourceId": chat.APP_ID}, {"resourceId": None, "changeType": "Ignore"},
                       None, {}):
            result = {"status": "Succeeded", "changes": [change]}
            with self.subTest(change=change), patch.object(chat, "cli", side_effect=[{}, result]):
                with self.assertRaises(chat.DeploymentError):
                    chat.validate()

    def test_validation_requires_concrete_project_scoped_role_assignment_id(self):
        prefix = chat.PROJECT_ID + "/providers/Microsoft.Authorization/roleAssignments/"
        for resource in (prefix, prefix + "[guid(project, principal, role)]",
                         prefix + "11111111-2222-3333-4444-555555555555",
                         prefix + "11111111-2222-3333-4444-555555555555/child",
                         chat.ACCOUNT_ID + "/providers/Microsoft.Authorization/roleAssignments/"
                         "11111111-2222-3333-4444-555555555555"):
            result = {"status": "Succeeded", "changes": [
                {"resourceId": resource, "changeType": "Create"}
            ]}
            with self.subTest(resource=resource), patch.object(chat, "cli", side_effect=[{}, result]):
                with self.assertRaises(chat.DeploymentError):
                    chat.validate()

    def test_state_rejects_unrecognized_fields_before_writing(self):
        with self.assertRaises(chat.DeploymentError):
            chat.save_state(api_key="not-allowed")

    def test_state_rejects_symlinks(self):
        state = MagicMock()
        state.is_symlink.return_value = True
        with patch.object(chat, "STATE", state):
            with self.assertRaises(chat.DeploymentError):
                chat.read_state()

    def test_wait_has_finite_poll_bound(self):
        with (patch.object(chat, "arm", return_value={"properties": {"provisioningState": "Updating"}}),
              patch.object(chat.time, "sleep") as sleep):
            with self.assertRaises(chat.DeploymentError):
                chat.wait_resource(chat.APP_ID, chat.WEB_API)
        self.assertEqual(sleep.call_count, 60)

    def test_template_contains_only_approved_new_resources(self):
        project = (chat.ROOT / "infra/chat-project.bicep").read_text()
        role = (chat.ROOT / "infra/chat-role.bicep").read_text()
        app = (chat.ROOT / "infra/chat-app.bicep").read_text()
        self.assertIn("existing =", project)
        self.assertIn("scope: project", role)
        self.assertIn(chat.CONSUMER, role)
        self.assertIn(chat.COGNITIVE_SERVICES_USER, role)
        self.assertIn("@allowed(['" + chat.APP_PRINCIPAL + "'])", role)
        self.assertIn("param includeConsumerAssignment bool = true", role)
        self.assertIn("= if (includeConsumerAssignment)", role)
        self.assertEqual(role.count("'Microsoft.Authorization/roleAssignments@"), 2)
        self.assertIn("name: guid(project.id, appId, consumerId)", role)
        self.assertIn("name: guid(project.id, appId, cognitiveServicesUserId)", role)
        self.assertNotIn("guid(project.id, principalId", role)
        self.assertIn("'rg-redshift-bs01', 'Microsoft.Web/sites', '" + chat.APP + "'", role)
        self.assertIn("principalId: principalId", role)
        self.assertNotIn("capabilityHosts", project)
        self.assertNotIn("SecurityControl", project + app)
        self.assertIn("allow: false", app)
        self.assertIn("'NODE|24-lts'", app)
        template = (chat.ROOT / "infra/chat.bicep").read_text()
        parameters = json.loads((chat.ROOT / "infra/chat.parameters.json").read_text())
        for content in (template, app):
            self.assertIn("@allowed(['eastus2'])", content)
        self.assertEqual(parameters["parameters"]["appLocation"]["value"], chat.APP_REGION)
        self.assertEqual(app.count("location: appLocation"), 2)

    def test_inventory_requires_both_app_and_plan_in_approved_region(self):
        endpoint = f"https://{chat.ACCOUNT}.services.ai.azure.com/api/projects/{chat.PROJECT}"
        app = {"identity": {"type": "SystemAssigned", "principalId": "mi"},
               "location": "eastus2", "properties": {
                   "httpsOnly": True, "serverFarmId": chat.PLAN_ID,
                   "defaultHostName": "actual.eastus2-01.azurewebsites.net"}}
        plan = {"location": "eastus2", "sku": {"name": "B1", "capacity": 1},
                "properties": {"reserved": True}}
        project = {"location": "swedencentral", "identity": {"type": "SystemAssigned"},
                   "properties": {"endpoints": {"api": endpoint}}}
        config = {"properties": {"linuxFxVersion": "NODE|24-lts", "alwaysOn": True,
                                "ftpsState": "Disabled", "minTlsVersion": "1.2",
                                "scmMinTlsVersion": "1.2"}}
        for app_region, plan_region in (("eastus2", "eastus2"), ("brazilsouth", "eastus2"),
                                        ("eastus2", "brazilsouth"), ("westus2", "westus2")):
            with self.subTest(app_region=app_region, plan_region=plan_region):
                app["location"], plan["location"] = app_region, plan_region
                with (patch.object(chat, "arm", side_effect=[
                        app, plan, project, config, {"properties": {"allow": False}},
                        {"properties": {"allow": False}}]),
                      patch.object(chat, "verify_roles")):
                    if app_region == plan_region == "eastus2":
                        self.assertEqual(chat.inventory(), (endpoint, "actual.eastus2-01.azurewebsites.net", "mi"))
                    else:
                        with self.assertRaisesRegex(chat.DeploymentError, "location"):
                            chat.inventory()


if __name__ == "__main__":
    unittest.main()
