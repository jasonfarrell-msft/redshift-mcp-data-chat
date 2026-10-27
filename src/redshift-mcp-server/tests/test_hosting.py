from unittest.mock import MagicMock

import httpx
import pytest
from mcp.server.transport_security import TransportSecurityMiddleware
from starlette.requests import Request

from redshift_mcp_server import server


@pytest.mark.parametrize(
    "value",
    [
        "*",
        "*.azurecontainerapps.io",
        "https://poc.example.com",
        "poc.example.com:443",
        "poc.example.com/path",
        "poc.example.com,",
        "poc.example.com,,other.example.com",
        "127.0.0.1",
        "[::1]",
        "poc..example.com",
        "-poc.example.com",
        "poc.example.com\nforged.example.com",
        "synthetic-secret",
    ],
)
def test_public_allowlist_rejects_invalid_configuration(
    value: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("REDSHIFT_MCP_ALLOWED_HOSTS", value)
    run = MagicMock()
    monkeypatch.setattr(server.mcp, "run", run)
    with pytest.raises(SystemExit) as error:
        server.main(["--host", "0.0.0.0"])
    assert error.value.code == 2
    assert value not in capsys.readouterr().err.split("error:", 1)[1]
    run.assert_not_called()


def test_public_allowlist_is_exact_and_preserves_loopback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "REDSHIFT_MCP_ALLOWED_HOSTS", "poc.synthetic.azurecontainerapps.io, other.example.com"
    )
    security = server._transport_security("0.0.0.0")
    assert security.enable_dns_rebinding_protection
    middleware = TransportSecurityMiddleware(security)
    for name in ("poc.synthetic.azurecontainerapps.io", "other.example.com"):
        assert middleware._validate_host(name)
        assert middleware._validate_host(f"{name}:443")
        assert middleware._validate_origin(f"https://{name}")
        assert middleware._validate_origin(f"https://{name}:443")
        assert not middleware._validate_host(f"{name}:8000")
        assert not middleware._validate_host(f"{name}.evil.invalid")
        assert not middleware._validate_origin(f"http://{name}")
    for name in ("127.0.0.1:8000", "localhost:8000", "[::1]:8000"):
        assert middleware._validate_host(name)
        assert middleware._validate_origin(f"http://{name}")
    assert not middleware._validate_host("0.0.0.0:8000")
    assert not middleware._validate_origin("null")
    assert not middleware._validate_host(None)


def test_public_bootstrap_stays_restricted_without_allowlist() -> None:
    security = server._transport_security("0.0.0.0")
    assert security.enable_dns_rebinding_protection
    assert security.allowed_hosts == ["127.0.0.1:*", "localhost:*", "[::1]:*"]


async def test_health_is_process_only_without_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connect = MagicMock(side_effect=AssertionError("Health must not connect"))
    monkeypatch.setattr(server.database, "OfficialCursor", connect)
    monkeypatch.setattr(
        server.database, "test_connection", MagicMock(side_effect=AssertionError("No DB probe"))
    )
    request = Request({"type": "http", "method": "GET", "path": "/healthz", "headers": []})
    response = await server.healthz(request)
    assert response.status_code == 200
    assert response.body == b"ok\n"
    connect.assert_not_called()


async def test_health_bootstrap_accepts_replica_host_and_only_get() -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=server.mcp.streamable_http_app()),
        base_url="http://10.0.0.7:8000",
    ) as client:
        assert (await client.get("/healthz")).status_code == 200
        assert (await client.post("/healthz")).status_code == 405
