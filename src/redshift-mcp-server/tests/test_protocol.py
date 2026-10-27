import asyncio
import json
import logging
import os
import signal
import socket
import sys
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest
import pytest_asyncio
import uvicorn
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from redshift_mcp_server import analytics, database, server


@asynccontextmanager
async def http_session(url: str) -> AsyncIterator[ClientSession]:
    async with asyncio.timeout(15):
        async with httpx.AsyncClient(trust_env=False, timeout=5) as client:
            async with streamable_http_client(url, http_client=client) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    yield session


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def http_url() -> AsyncIterator[str]:
    """Serve the actual SDK app on an OS-assigned, reserved loopback socket."""
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        listener.setblocking(False)
        port = listener.getsockname()[1]
        app = server.mcp.streamable_http_app()
        http_server = uvicorn.Server(
            uvicorn.Config(app, log_level="warning", lifespan="on", timeout_graceful_shutdown=2)
        )
        task = asyncio.create_task(http_server.serve(sockets=[listener]))
        try:
            async with asyncio.timeout(10):
                while not http_server.started:
                    if task.done():
                        await task
                        pytest.fail("HTTP server exited before startup")
                    await asyncio.sleep(0.01)
            yield f"http://127.0.0.1:{port}/mcp"
        finally:
            http_server.should_exit = True
            try:
                await asyncio.wait_for(task, timeout=10)
            finally:
                if not task.done():
                    task.cancel()
                    with suppress(asyncio.CancelledError):
                        await task


async def wait_for_protocol(url: str, process: asyncio.subprocess.Process) -> None:
    """Probe initialize itself, then close the probe's MCP session."""
    async with httpx.AsyncClient(trust_env=False, timeout=1) as client:
        async with asyncio.timeout(15):
            while True:
                if process.returncode is not None:
                    pytest.fail(f"HTTP subprocess exited early: {process.returncode}")
                try:
                    response = await client.post(
                        url,
                        headers={"Accept": "application/json, text/event-stream"},
                        json={
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "initialize",
                            "params": {
                                "protocolVersion": "2025-03-26",
                                "capabilities": {},
                                "clientInfo": {"name": "readiness-test", "version": "1"},
                            },
                        },
                    )
                except httpx.TransportError:
                    await asyncio.sleep(0.05)
                    continue
                response.raise_for_status()
                assert '"serverInfo"' in response.text
                session_id = response.headers["mcp-session-id"]
                closed = await client.delete(url, headers={"mcp-session-id": session_id})
                assert closed.status_code == 200
                return


@pytest.mark.parametrize("entrypoint", ["console", "module"])
@pytest.mark.parametrize("host", ["127.0.0.1", "0.0.0.0"])
@pytest.mark.asyncio(loop_scope="module")
async def test_real_http_entrypoints_without_credentials(
    entrypoint: str, host: str, tmp_path: Path
) -> None:
    command = str(Path(sys.executable).parent / "redshift-mcp-server")
    # Select an ephemeral port instead of competing for the user's default port.
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    args = [command] if entrypoint == "console" else [sys.executable, "-m", "redshift_mcp_server"]
    url = f"http://127.0.0.1:{port}/mcp"
    environment = dict(os.environ)
    environment["REDSHIFT_MCP_ALLOWED_HOSTS"] = "poc.synthetic.azurecontainerapps.io"
    process = await asyncio.create_subprocess_exec(
        *args,
        "--host",
        host,
        "--port",
        str(port),
        cwd=tmp_path,
        env=environment,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        await wait_for_protocol(url, process)
        async with httpx.AsyncClient(trust_env=False, timeout=5) as client:
            # ACA probes can address the replica IP rather than its public FQDN.
            health = await client.get(
                url.replace("/mcp", "/healthz"),
                headers={"Host": "10.0.0.7:8000", "Origin": "http://probe.invalid"},
            )
            assert health.status_code == 200
            assert health.text == "ok\n"
            headers = {
                "Host": "poc.synthetic.azurecontainerapps.io",
                "Origin": "https://poc.synthetic.azurecontainerapps.io",
            }
            response = await client.post(url, headers=headers, json={})
            if host == "127.0.0.1":
                assert response.status_code == 421
            else:
                # A correct Host/Origin reaches the protocol handler (no MCP Accept yet).
                assert response.status_code == 406
                for forged, status in (
                    ({"Host": "poc.synthetic.azurecontainerapps.io.evil.invalid"}, 421),
                    ({"Host": "poc.synthetic.azurecontainerapps.io:8000"}, 421),
                    ({"Origin": "http://poc.synthetic.azurecontainerapps.io"}, 403),
                    ({"Origin": "https://poc.synthetic.azurecontainerapps.io.evil.invalid"}, 403),
                    ({"Origin": "https://poc.synthetic.azurecontainerapps.io:444"}, 403),
                ):
                    rejected = await client.post(url, headers=headers | forged, json={})
                    assert rejected.status_code == status
        if host == "0.0.0.0":
            async with httpx.AsyncClient(trust_env=False, timeout=5, headers=headers) as client:
                async with streamable_http_client(url, http_client=client) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        assert len((await session.list_tools()).tools) == 6
        async with http_session(url) as session:
            tools = (await session.list_tools()).tools
            assert {tool.name for tool in tools} == {
                "test_connection",
                "list_schemas",
                "list_tables",
                "describe_table",
                "get_data_context",
                "analyze_data",
            }
            for tool in tools:
                assert tool.outputSchema is not None
            schemas = next(tool for tool in tools if tool.name == "list_schemas")
            assert schemas.inputSchema["properties"]["limit"]["maximum"] == 500
            for name, arguments in (
                ("test_connection", {}),
                ("list_schemas", {}),
                ("list_tables", {"schema": "public"}),
                ("describe_table", {"schema": "public", "table": "sample"}),
            ):
                missing = await session.call_tool(name, arguments)
                assert missing.isError
                assert "Official MCP runtime target is not configured" in str(missing.content)
            for arguments in (
                {"schema": ""},
                {"schema": "public", "limit": 501},
                {"schema": "public", "limit": True},
                {"schema": "public", "limit": "2"},
            ):
                invalid = await session.call_tool("list_tables", arguments)
                assert invalid.isError
        assert process.returncode is None  # HTTP stays up even with stdin closed.
    finally:
        if process.returncode is None:
            with suppress(ProcessLookupError):
                process.terminate()
        try:
            output, _ = await asyncio.wait_for(process.communicate(), timeout=10)
        except TimeoutError:
            process.kill()
            output, _ = await process.communicate()
    assert f"Starting Streamable HTTP MCP at http://{host}:{port}/mcp" in output.decode()
    assert "Keep this process running" in output.decode()
    assert process.returncode in (0, -signal.SIGTERM)
    assert "Application shutdown complete." in output.decode()


@pytest.mark.parametrize(
    ("headers", "status", "message"),
    [
        ({"Host": "untrusted.invalid"}, 421, "Invalid Host header"),
        ({"Host": "127.0.0.1.untrusted.invalid:8000"}, 421, "Invalid Host header"),
        ({"Origin": "https://untrusted.invalid"}, 403, "Invalid Origin header"),
        ({"Origin": "http://localhost.untrusted.invalid:8000"}, 403, "Invalid Origin header"),
    ],
)
@pytest.mark.asyncio(loop_scope="module")
async def test_http_dns_rebinding_protection(
    http_url: str, headers: dict[str, str], status: int, message: str
) -> None:
    async with httpx.AsyncClient(trust_env=False) as client:
        response = await client.post(http_url, headers=headers, json={})
    assert response.status_code == status
    assert response.text == message


@pytest.mark.asyncio(loop_scope="module")
async def test_http_accepts_loopback_origin(http_url: str) -> None:
    async with asyncio.timeout(15):
        async with httpx.AsyncClient(
            trust_env=False, headers={"Origin": "http://localhost:8000"}
        ) as client:
            async with streamable_http_client(http_url, http_client=client) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    assert len((await session.list_tools()).tools) == 6


async def test_tools_offload_sync_work(monkeypatch: pytest.MonkeyPatch) -> None:
    event_thread = threading.get_ident()

    def operation() -> dict[str, bool]:
        assert threading.get_ident() != event_thread
        return {"connected": True}

    monkeypatch.setattr(database, "test_connection", operation)
    assert await server.test_connection() == {"connected": True}


@pytest.mark.asyncio(loop_scope="module")
async def test_real_http_structured_output(http_url: str, connector: MagicMock) -> None:
    cursor = connector.return_value.cursor.return_value
    async with http_session(http_url) as session:
        connected = await session.call_tool("test_connection", {})
        assert not connected.isError
        assert connected.structuredContent == {"connected": True}
        for name, arguments, column, value in (
            ("list_schemas", {"limit": 2}, "schema_name", "public"),
            ("list_tables", {"schema": "public", "limit": 2}, "table_name", "sample"),
            (
                "describe_table",
                {"schema": "public", "table": "sample", "limit": 2},
                "column_name",
                "id",
            ),
        ):
            cursor.description = [(column,)]
            cursor.fetchmany.return_value = [(value,)]
            result = await session.call_tool(name, arguments)
            expected = {"items": [{column: value}], "truncated": False}
            assert not result.isError
            assert result.structuredContent == expected
            assert json.loads(result.content[0].text) == expected
    assert cursor.open.call_count == 4


@pytest.mark.asyncio(loop_scope="module")
async def test_analysis_protocol_strict_plan_and_exact_output(
    http_url: str, connector: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(analytics, "_integrity", MagicMock(return_value=True))
    cursor = connector.return_value.cursor.return_value
    cursor.description = [
        ("oil_bbl_sum",),
        ("oil_bbl_sum_null_records",),
        ("source_records",),
        ("first_observation",),
        ("last_observation",),
    ]
    cursor.fetchmany.return_value = [(Decimal("1234.56789012"), 0, 3, None, None)]
    plan = {
        "version": "1",
        "dataset": "production",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "measures": [{"field": "oil_bbl", "aggregation": "sum"}],
    }
    async with http_session(http_url) as session:
        tools = (await session.list_tools()).tools
        schema = next(tool for tool in tools if tool.name == "analyze_data").inputSchema
        assert schema["$defs"]["AnalysisPlan"]["additionalProperties"] is False
        for changes in (
            {"sql": "DROP TABLE secret"},
            {"limit": True},
            {"dataset": "other.secret"},
            {"group_by": ["state; SELECT 1"]},
        ):
            assert (await session.call_tool("analyze_data", {"plan": {**plan, **changes}})).isError
        connector.assert_not_called()
        value = await session.call_tool("analyze_data", {"plan": plan})
        assert not value.isError
        assert value.structuredContent["items"][0]["oil_bbl_sum"] == "1234.56789012"
        assert value.structuredContent["units"] == {"oil_bbl_sum": "bbl"}
        assert len(value.model_dump_json().encode()) < analytics.MAX_BYTES


@pytest.mark.asyncio(loop_scope="module")
async def test_http_connection_uses_startup_env_file(
    http_url: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / ".env").write_text(
        "REDSHIFT_HOST=example.invalid\n"
        "REDSHIFT_DATABASE=fixture_db\n"
        "REDSHIFT_USER=fixture_user\n"
        "REDSHIFT_PASSWORD='synthetic # $ ${LITERAL}'\n",
        encoding="utf-8",
    )
    connect = MagicMock()
    connect.return_value.fetchone.return_value = [1]
    monkeypatch.setattr(database, "OfficialCursor", connect)
    monkeypatch.setattr(server.mcp, "run", MagicMock())
    server.main([])
    connect.assert_not_called()
    async with http_session(http_url) as session:
        result = await session.call_tool("test_connection", {})
        (tmp_path / ".env").write_text(
            "REDSHIFT_PASSWORD='changed-after-startup'\n", encoding="utf-8"
        )
        assert not (await session.call_tool("test_connection", {})).isError
    assert not result.isError
    assert result.structuredContent == {"connected": True}
    assert connect.call_args.kwargs == {}
    connect.return_value.execute.assert_called_with("SELECT 1")


@pytest.mark.asyncio(loop_scope="module")
async def test_http_invalid_input_never_connects(http_url: str, connector: MagicMock) -> None:
    async with http_session(http_url) as session:
        for arguments in (
            {"schema": ""},
            {"schema": "  "},
            {"schema": "a\x00b"},
            {"schema": "é" * 64},
            {"schema": "public", "limit": 0},
            {"schema": "public", "limit": 501},
            {"schema": "public", "limit": True},
            {"schema": "public", "limit": "2"},
        ):
            assert (await session.call_tool("list_tables", arguments)).isError
    connector.assert_not_called()


def test_cli_suppresses_dependency_diagnostics(monkeypatch: pytest.MonkeyPatch) -> None:
    run = MagicMock()
    monkeypatch.setattr(server.mcp, "run", run)
    for name in ("redshift_connector", "boto3", "botocore"):
        logger = logging.getLogger(name)
        monkeypatch.setattr(logger, "handlers", [])
        monkeypatch.setattr(logger, "propagate", True)
    server.main([])
    run.assert_called_once_with(transport="streamable-http")
    assert server.mcp.settings.host == "127.0.0.1"
    assert server.mcp.settings.port == 8000
    assert server.mcp.settings.streamable_http_path == "/mcp"
    security = server.mcp.settings.transport_security
    assert security is not None
    assert security.enable_dns_rebinding_protection
    for name in ("redshift_connector", "boto3", "botocore"):
        logger = logging.getLogger(name)
        assert logger.propagate is False
        assert all(isinstance(handler, logging.NullHandler) for handler in logger.handlers)


@pytest.mark.parametrize("port", ["0", "-1", "65536", "invalid"])
def test_cli_rejects_invalid_port(port: str, monkeypatch: pytest.MonkeyPatch) -> None:
    run = MagicMock()
    monkeypatch.setattr(server.mcp, "run", run)
    with pytest.raises(SystemExit) as error:
        server.main(["--port", port])
    assert error.value.code == 2
    run.assert_not_called()


@pytest.mark.parametrize("host", ["localhost", "::", "192.0.2.1", "untrusted.invalid"])
def test_cli_rejects_arbitrary_bind(host: str, monkeypatch: pytest.MonkeyPatch) -> None:
    run = MagicMock()
    monkeypatch.setattr(server.mcp, "run", run)
    with pytest.raises(SystemExit) as error:
        server.main(["--host", host])
    assert error.value.code == 2
    run.assert_not_called()
