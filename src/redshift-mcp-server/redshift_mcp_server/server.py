"""Streamable HTTP MCP entry point; database access is lazy and off-thread."""

import argparse
import asyncio
import logging
import os
import re
import sys
import threading
import time
from collections import deque
from collections.abc import AsyncIterator, Callable
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any, TypeVar

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import Field
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Mount

from redshift_mcp_server import analytics, database
from redshift_mcp_server.analytics import AnalysisPlan
from redshift_mcp_server.config import ConfigurationError, load_environment
from redshift_mcp_server.official import WORKER_LIMIT, QuarantinedError, shutdown_workers


@asynccontextmanager
async def _worker_lifespan() -> AsyncIterator[None]:
    try:
        yield
    finally:
        await asyncio.to_thread(shutdown_workers)


class ApplicationMCP(FastMCP):
    """Own shared workers at application scope, never at MCP-session scope."""

    def streamable_http_app(self) -> Starlette:
        app = super().streamable_http_app()

        @asynccontextmanager
        async def lifespan(app: Starlette) -> AsyncIterator[None]:
            # Mounted apps do not run their own lifespan. Run the SDK's public
            # session manager once, then dispose workers after sessions stop.
            async with _worker_lifespan():
                async with self.session_manager.run():
                    yield

        return Starlette(routes=[Mount("/", app=app)], lifespan=lifespan)

    async def run_stdio_async(self) -> None:
        async with _worker_lifespan():
            await super().run_stdio_async()


mcp = ApplicationMCP(
    "Redshift analytics",
    host="127.0.0.1",
    port=8000,
    streamable_http_path="/mcp",
)
Limit = Annotated[int, Field(strict=True, ge=1, le=500, description="Maximum items, from 1 to 500")]
Name = Annotated[str, Field(strict=True, min_length=1, max_length=127)]
T = TypeVar("T")
_workers = ThreadPoolExecutor(max_workers=WORKER_LIMIT, thread_name_prefix="redshift")
_permits = threading.BoundedSemaphore(WORKER_LIMIT)
_admission_lock = threading.Lock()
_admissions: deque[float] = deque()
_analysis_admissions: deque[float] = deque()


@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(request: Request) -> PlainTextResponse:
    """Process-only probe, intentionally outside MCP Host/Origin validation."""
    return PlainTextResponse("ok\n", headers={"Cache-Control": "no-store"})


def _transport_security(host: str) -> TransportSecuritySettings:
    security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=["127.0.0.1:*", "localhost:*", "[::1]:*"],
        allowed_origins=["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*"],
    )
    if host == "127.0.0.1":
        return security
    configured = os.environ.get("REDSHIFT_MCP_ALLOWED_HOSTS", "")
    if not configured:
        return security  # Allow health-only bootstrap before the actual FQDN is known.
    for value in configured.split(","):
        hostname = value.strip().lower()
        labels = hostname.split(".")
        if (
            len(hostname) > 253
            or len(labels) < 2
            or all(label.isdigit() for label in labels)
            or any(
                not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label) for label in labels
            )
        ):
            raise ConfigurationError(
                "REDSHIFT_MCP_ALLOWED_HOSTS must be comma-separated exact DNS names "
                "without schemes, ports, paths, IP addresses, or wildcards."
            )
        security.allowed_hosts.extend([hostname, f"{hostname}:443"])
        security.allowed_origins.extend([f"https://{hostname}", f"https://{hostname}:443"])
    return security


async def _run(operation: Callable[..., T], *args: Any) -> T:
    # Process-wide bounds apply to direct MCP callers, not only the chat facade.
    # No queue: reject saturation. A cancelled await never releases a running worker.
    now = time.monotonic()
    analytic = operation in (analytics.analyze_data, analytics.get_data_context)
    with _admission_lock:
        for window in (_admissions, _analysis_admissions):
            while window and now - window[0] >= 60:
                window.popleft()
        if len(_admissions) >= 120 or (analytic and len(_analysis_admissions) >= 12):
            raise ToolError("MCP request rate exceeded; retry after one minute.")
        if not _permits.acquire(blocking=False):
            raise ToolError("MCP is busy; retry after the current operations finish.")
        _admissions.append(now)
        if analytic:
            _analysis_admissions.append(now)
    try:
        future = _workers.submit(operation, *args)
    except BaseException:
        _permits.release()
        raise
    def settled(done: Any) -> None:
        if not isinstance(done.exception(), QuarantinedError):
            _permits.release()
    future.add_done_callback(settled)
    try:
        return await asyncio.shield(asyncio.wrap_future(future))
    except (ConfigurationError, database.RedshiftError, ValueError) as exc:
        raise ToolError(str(exc)) from None


@mcp.tool()
async def get_data_context() -> dict[str, Any]:
    """Get observed dates and supported semantics before planning; not a business answer."""
    return await _run(analytics.get_data_context)


@mcp.tool()
async def analyze_data(plan: AnalysisPlan) -> dict[str, Any]:
    """Execute a strict version-1 semantic plan over oge_synthetic; never accepts SQL.

    Production: sums of oil_bbl/gas_mcf/operating_cost_usd, dimensions
    well_id/state/basin/operator, inclusive dates and none/day/month/year buckets.
    Prices: avg/min/max oil_usd_per_bbl/gas_usd_per_mcf, full months, no dimensions.
    Wells: wells/count, no dates, optional dimensions. Exact decimals are strings.
    Report nulls, empty/truncated results, units and observed periods honestly.
    """
    return await _run(analytics.analyze_data, plan)


@mcp.tool()
async def test_connection() -> dict[str, bool]:
    """Run SELECT 1 through the official AWS MCP; fails closed until federation is ready."""
    return await _run(database.test_connection)


@mcp.tool()
async def list_schemas(limit: Limit = 100) -> dict[str, Any]:
    """List visible schemas except pg_catalog/information_schema; report truncation."""
    return await _run(database.list_schemas, limit)


@mcp.tool()
async def list_tables(schema: Name, limit: Limit = 100) -> dict[str, Any]:
    """List visible tables/views for an exact schema name, with bounded results."""
    return await _run(database.list_tables, schema, limit)


@mcp.tool()
async def describe_table(schema: Name, table: Name, limit: Limit = 100) -> dict[str, Any]:
    """Describe visible columns of an exact schema/table, in ordinal order; no table data."""
    return await _run(database.describe_table, schema, table, limit)


def _port(value: str) -> int:
    try:
        port = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("port must be an integer from 1 to 65535") from None
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be an integer from 1 to 65535")
    return port


def main(argv: list[str] | None = None) -> None:
    """Start HTTP MCP without connecting to Redshift or requiring credentials."""
    parser = argparse.ArgumentParser(description="Run the Redshift analytics MCP HTTP server.")
    parser.add_argument(
        "--host",
        choices=("127.0.0.1", "0.0.0.0"),
        default="127.0.0.1",
        help="bind address; use 0.0.0.0 only for explicit network hosting (default: 127.0.0.1)",
    )
    parser.add_argument("--port", type=_port, default=8000, help="HTTP port (default: 8000)")
    parser.add_argument(
        "--env-file",
        type=Path,
        help="configuration file (default: .env in the current working directory, if present)",
    )
    args = parser.parse_args(argv)
    try:
        load_environment(args.env_file)
        security = _transport_security(args.host)
    except ConfigurationError as exc:
        parser.error(str(exc))
    mcp.settings.host = args.host
    mcp.settings.port = args.port
    mcp.settings.transport_security = security
    # Dependency debug logs may contain endpoints or AWS request details. Only our
    # sanitized tool errors should cross the process boundary.
    for name in ("redshift_connector", "boto3", "botocore"):
        logger = logging.getLogger(name)
        logger.addHandler(logging.NullHandler())
        logger.propagate = False
    print(
        f"Starting Streamable HTTP MCP at http://{args.host}:{args.port}/mcp\n"
        "Keep this process running for MCP clients; stop with Ctrl-C.",
        file=sys.stderr,
        flush=True,
    )
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
