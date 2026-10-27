import asyncio
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest
from mcp import ClientSession
from mcp.shared.memory import create_client_server_memory_streams
from starlette.testclient import TestClient

from redshift_mcp_server import database, official, server
from redshift_mcp_server.official import (
    OfficialCursor,
    QuarantinedError,
    RedshiftError,
    bind,
    child_environment,
    literal,
)


@pytest.fixture
def warm_runtime(monkeypatch):
    """Task-affine SDK stand-in; transaction state is isolated per SDK session."""
    sessions = []
    env = {"REDSHIFT_WORKGROUP": "default-workgroup", "REDSHIFT_DATABASE": "dev"}
    monkeypatch.setattr(official, "child_environment", lambda: env.copy())

    @asynccontextmanager
    async def streams(*args, **kwargs):
        yield (None, None)

    class Session:
        def __init__(self, *args):
            self.calls = []
            self.transactions = set()
            self.delay = {}
            self.fail = set()
            self.error_results = set()
            self.closed = False
            self.initializations = 0
            self.bad_schema = False
            sessions.append(self)

        async def __aenter__(self):
            self.owner = asyncio.current_task()
            self.thread_id = threading.get_ident()
            return self

        async def __aexit__(self, *args):
            assert asyncio.current_task() is self.owner
            self.closed = True

        async def initialize(self):
            self.initializations += 1

        async def list_tools(self):
            return SimpleNamespace(tools=[
                SimpleNamespace(name=name, inputSchema={"properties": (
                    {} if self.bad_schema else dict.fromkeys([
                        "sql", "begin_transaction", "in_transaction", "rollback_transaction",
                    ], {})
                )})
                for name in official.TOOLS
            ])

        async def call_tool(self, name, args):
            assert name == "execute_query"
            assert asyncio.current_task() is self.owner
            assert threading.get_ident() == self.thread_id
            self.calls.append(args)
            action = next(key for key in (
                "begin_transaction", "in_transaction", "rollback_transaction",
            ) if key in args)
            await asyncio.sleep(self.delay.get(action, 0))
            if action in self.fail:
                raise RuntimeError("PRIVATE upstream failure body")
            if action in self.error_results:
                return SimpleNamespace(isError=True)
            transaction = args[action]
            if action == "begin_transaction":
                assert not self.transactions
                self.transactions.add(transaction)
            else:
                assert transaction in self.transactions
                if action == "rollback_transaction":
                    self.transactions.remove(transaction)
            value = {
                "columns": ["exact"] if "sql" in args else [],
                "rows": [["21157564.26"]] if "sql" in args else [],
                "row_count": 1 if "sql" in args else 0,
                "query_id": "offline-query",
            }
            return SimpleNamespace(isError=False, structuredContent=value,
                                   content=[SimpleNamespace(type="text", text=json.dumps(value))])

    monkeypatch.setattr(official, "stdio_client", streams)
    monkeypatch.setattr(official, "ClientSession", Session)
    return sessions


def test_sequential_reuse_has_one_initialize_and_fresh_transactions(warm_runtime):
    workers, transactions = [], []
    for _ in range(3):
        with database._cursor() as cursor:
            workers.append(cursor.worker)
            transactions.append(cursor.transaction)
            cursor.execute("SELECT 1")
    assert len({id(worker) for worker in workers}) == 1
    assert len(set(transactions)) == 3
    assert len(warm_runtime) == 1 and warm_runtime[0].initializations == 1
    assert not warm_runtime[0].transactions
    assert len(warm_runtime[0].calls) == 9  # Fresh BEGIN, SELECT, ROLLBACK for every lease.
    assert not warm_runtime[0].closed


def test_concurrent_leases_are_exclusive_and_saturation_has_no_queue(warm_runtime):
    barrier = threading.Barrier(3)

    def operation():
        with database._cursor() as cursor:
            cursor.execute("SELECT 1")
            barrier.wait(timeout=2)
            barrier.wait(timeout=2)
            return cursor.worker

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(operation) for _ in range(2)]
        barrier.wait(timeout=2)
        try:
            with pytest.raises(RedshiftError, match="busy"):
                with database._cursor():
                    pytest.fail("A third lease must not be admitted.")
        finally:
            barrier.wait(timeout=2)
        workers = [future.result(timeout=2) for future in futures]
    assert len({id(worker) for worker in workers}) == 2
    assert len({session.thread_id for session in warm_runtime}) == 2
    assert all(not session.transactions for session in warm_runtime)


def test_idle_workers_are_leased_fifo(warm_runtime):
    first, second = OfficialCursor(), OfficialCursor()
    first.open()
    second.open()
    workers = [first.worker, second.worker]
    second.close()
    first.close()
    with database._cursor() as cursor:
        assert cursor.worker is workers[1]
    with database._cursor() as cursor:
        assert cursor.worker is workers[0]


@pytest.mark.parametrize("action,mode", [
    ("in_transaction", "exception"),
    ("rollback_transaction", "exception"),
    ("rollback_transaction", "tool_error"),
])
def test_failed_settlement_removes_capacity_without_replacement(warm_runtime, action, mode):
    with pytest.raises(QuarantinedError, match="capacity quarantined") as error:
        with database._cursor() as cursor:
            broken = cursor.worker
            failures = (
                warm_runtime[0].fail if mode == "exception" else warm_runtime[0].error_results
            )
            failures.add(action)
            cursor.execute("SELECT 1")
    assert "PRIVATE" not in str(error.value)
    assert broken.closed.wait(timeout=2)
    assert broken in official._pool.workers and broken not in official._pool.available
    # Losing a second worker exhausts the original cap, not a replenished pool.
    with pytest.raises(QuarantinedError):
        with database._cursor() as cursor:
            warm_runtime[1].fail.add("rollback_transaction")
    with pytest.raises(RedshiftError, match="busy"):
        with database._cursor():
            pytest.fail("Quarantined slots must not be replaced.")
    assert len(warm_runtime) == 2


def test_absolute_deadline_includes_cleanup_and_quarantines(warm_runtime):
    cursor = OfficialCursor()
    cursor.open()
    worker = cursor.worker
    warm_runtime[0].delay["rollback_transaction"] = 1
    cursor.deadline = time.monotonic() + 0.05
    start = time.monotonic()
    with pytest.raises(QuarantinedError):
        cursor.close()
    assert time.monotonic() - start < 0.3
    assert worker not in official._pool.available
    official.shutdown_workers()
    assert worker.closed.is_set() and not worker.thread.is_alive()


def test_absolute_deadline_also_bounds_startup(monkeypatch, warm_runtime):
    original = official.ClientSession

    def slow(*args):
        session = original(*args)
        async def initialize():
            await asyncio.sleep(1)
        session.initialize = initialize
        return session

    monkeypatch.setattr(official, "ClientSession", slow)
    monkeypatch.setattr(official, "OPERATION_SECONDS", 0.05)
    start = time.monotonic()
    with pytest.raises(RedshiftError):
        with database._cursor():
            pytest.fail("No transaction may start after the startup deadline.")
    assert time.monotonic() - start < 0.3
    official.shutdown_workers()
    assert warm_runtime[0].closed and not warm_runtime[0].calls


def test_shutdown_before_supervisor_starts_settles_initialization(monkeypatch, warm_runtime):
    original = official._Worker.start

    def cancelled_start(worker):
        create = worker.loop.create_task

        def cancelled_task(coroutine, **kwargs):
            task = create(coroutine, **kwargs)
            task.cancel()
            return task

        monkeypatch.setattr(worker.loop, "create_task", cancelled_task)
        original(worker)

    monkeypatch.setattr(official._Worker, "start", cancelled_start)
    start = time.monotonic()
    with pytest.raises(RedshiftError):
        with database._cursor():
            pytest.fail("A cancelled supervisor cannot issue a transaction.")
    assert time.monotonic() - start < 0.3
    assert not warm_runtime
    assert official._pool.workers[0].closed.is_set()


@pytest.mark.parametrize("stage", ["initialize", "list_tools", "schema"])
def test_initialization_failure_closes_task_affine_contexts(monkeypatch, warm_runtime, stage):
    original = official.ClientSession

    def failing(*args):
        session = original(*args)
        if stage == "schema":
            session.bad_schema = True
        else:
            async def fail():
                raise RuntimeError("PRIVATE initialization body")
            setattr(session, stage, fail)
        return session

    monkeypatch.setattr(official, "ClientSession", failing)
    with pytest.raises(RedshiftError, match="verification failed"):
        with database._cursor():
            pytest.fail("Initialization must fail closed.")
    assert warm_runtime[0].closed and not warm_runtime[0].calls
    assert not official._pool.workers  # Known no-BEGIN failure is safe to rebuild.
    monkeypatch.setattr(official, "ClientSession", original)
    with database._cursor():
        pass
    assert len(warm_runtime) == 2


def test_shutdown_closes_sessions_threads_and_loops(monkeypatch, warm_runtime):
    cursors = [OfficialCursor(), OfficialCursor()]
    for cursor in cursors:
        cursor.open()
    workers = [cursor.worker for cursor in cursors]
    for cursor in cursors:
        cursor.close()
    stops = []
    for worker in workers:
        original = worker.stop

        def stop(*, cancel=False, worker=worker, original=original):
            stops.append(worker)
            original(cancel=cancel)

        monkeypatch.setattr(worker, "stop", stop)
    official.shutdown_workers()
    official.shutdown_workers()
    assert stops == workers
    assert all(session.closed for session in warm_runtime)
    assert all(worker.closed.is_set() and worker.loop.is_closed()
               and not worker.thread.is_alive() for worker in workers)
    with pytest.raises(RedshiftError, match="shutting down"):
        with database._cursor():
            pytest.fail("Shutdown cannot restore capacity.")


def test_http_sessions_preserve_warm_pool_until_application_shutdown(monkeypatch, warm_runtime):
    """Actual SDK HTTP initialize/DELETE must not own the process-wide pool."""
    app = server.ApplicationMCP("http-lifecycle", json_response=True)
    app.tool()(server.list_schemas)
    shutdowns = []

    def shutdown():
        shutdowns.append(True)
        official.shutdown_workers()

    monkeypatch.setattr(server, "shutdown_workers", shutdown)
    with TestClient(app.streamable_http_app(), base_url="http://localhost:8000") as client:
        def initialize(request_id):
            response = client.post("/mcp", headers={
                "Accept": "application/json, text/event-stream",
            }, json={
                "jsonrpc": "2.0", "id": request_id, "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26", "capabilities": {},
                    "clientInfo": {"name": "lifecycle-test", "version": "1"},
                },
            })
            assert response.status_code == 200
            assert "serverInfo" in response.json()["result"]
            headers = {
                "Accept": "application/json, text/event-stream",
                "Mcp-Session-Id": response.headers["mcp-session-id"],
                "Mcp-Protocol-Version": response.json()["result"]["protocolVersion"],
            }
            initialized = client.post("/mcp", headers=headers, json={
                "jsonrpc": "2.0", "method": "notifications/initialized",
            })
            assert initialized.status_code == 202
            return headers

        def query(headers, request_id):
            response = client.post("/mcp", headers=headers, json={
                "jsonrpc": "2.0", "id": request_id, "method": "tools/call",
                "params": {"name": "list_schemas", "arguments": {}},
            })
            assert response.status_code == 200
            result = response.json()["result"]
            assert not result.get("isError")
            assert result["structuredContent"] == {
                "items": [{"exact": "21157564.26"}], "truncated": False,
            }

        session_a = initialize(1)
        query(session_a, 2)
        worker = official._pool.workers[0]
        session_b = initialize(3)
        assert session_a["Mcp-Session-Id"] != session_b["Mcp-Session-Id"]
        assert client.delete("/mcp", headers=session_a).status_code == 200
        query(session_b, 4)
        assert not official._pool.stopping and not worker.closed.is_set()
        assert not shutdowns
        assert client.delete("/mcp", headers=session_b).status_code == 200
        session_c = initialize(5)
        query(session_c, 6)
        assert len(warm_runtime) == 1 and warm_runtime[0].initializations == 1
        transactions = [
            call["begin_transaction"] for call in warm_runtime[0].calls
            if "begin_transaction" in call
        ]
        assert len(set(transactions)) == 3
        assert not warm_runtime[0].transactions
        # Leave C open: application teardown must also close remaining sessions.
    assert shutdowns == [True]
    assert official._pool.stopping and not official._pool.available
    assert worker.closed.is_set() and warm_runtime[0].closed
    assert worker.loop.is_closed() and not worker.thread.is_alive()


def test_http_application_shutdown_closes_idle_and_active_workers(monkeypatch, warm_runtime):
    entered = threading.Event()
    original = official._Worker._call

    async def slow_call(self, deadline, **args):
        if "sql" in args:
            entered.set()
            await asyncio.sleep(10)
        return await original(self, deadline, **args)

    monkeypatch.setattr(official._Worker, "_call", slow_call)
    app = server.ApplicationMCP("http-active-shutdown")
    with ThreadPoolExecutor(max_workers=1) as executor:
        with TestClient(app.streamable_http_app(), base_url="http://localhost:8000"):
            active = executor.submit(database.test_connection)
            assert entered.wait(timeout=2)
            with database._cursor():
                pass  # A second worker is idle while the first is executing.
            workers = list(official._pool.workers)
            assert len(workers) == 2 and len(official._pool.available) == 1
            start = time.monotonic()
        assert time.monotonic() - start < 2
        with pytest.raises(QuarantinedError):
            active.result(timeout=2)
    assert official._pool.stopping and not official._pool.available
    assert all(session.closed for session in warm_runtime)
    assert all(worker.closed.is_set() and worker.loop.is_closed()
               and not worker.thread.is_alive() for worker in workers)


async def test_stdio_application_eof_closes_warm_workers(monkeypatch, warm_runtime):
    app = server.ApplicationMCP("stdio-lifecycle")
    app.tool()(server.list_schemas)
    async with create_client_server_memory_streams() as (client_streams, server_streams):
        @asynccontextmanager
        async def streams():
            yield server_streams

        monkeypatch.setattr("mcp.server.fastmcp.server.stdio_server", streams)
        task = asyncio.create_task(app.run_stdio_async())
        try:
            async with ClientSession(*client_streams) as client:
                await client.initialize()
                result = await client.call_tool("list_schemas", {})
                assert not result.isError
                worker = official._pool.workers[0]
                assert not worker.closed.is_set()
            await client_streams[1].aclose()  # Same end-of-input boundary as stdio EOF.
            await asyncio.wait_for(task, timeout=2)
        finally:
            if not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
    assert official._pool.stopping and warm_runtime[0].closed
    assert worker.closed.is_set() and worker.loop.is_closed() and not worker.thread.is_alive()


def test_shutdown_cancels_active_local_call_without_replenishing_capacity(
    monkeypatch, warm_runtime,
):
    entered = threading.Event()
    original = official._Worker._call

    async def slow_call(self, deadline, **args):
        if "sql" in args:
            entered.set()
            await asyncio.sleep(10)
        return await original(self, deadline, **args)

    monkeypatch.setattr(official._Worker, "_call", slow_call)
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(database.test_connection)
        assert entered.wait(timeout=2)
        workers = list(official._pool.workers)
        official.shutdown_workers()
        with pytest.raises(QuarantinedError):
            future.result(timeout=2)
    assert all(worker.closed.is_set() and not worker.thread.is_alive() for worker in workers)
    assert warm_runtime[0].closed and not official._pool.available


def test_shutdown_settles_queued_local_requests_and_rejects_new_calls(warm_runtime):
    cursor = OfficialCursor()
    cursor.open()
    worker = cursor.worker
    pending = official.Future()
    worker.loop.call_soon_threadsafe(
        worker.commands.put_nowait,
        ({"sql": "SELECT 1", "in_transaction": cursor.transaction}, cursor.deadline, pending),
    )
    worker.stop(cancel=True)
    with pytest.raises(QuarantinedError):
        worker.call(cursor.deadline, sql="SELECT 1")
    # Either the already-queued call finished, or shutdown must explicitly fail it.
    try:
        pending.result(timeout=2)
    except QuarantinedError:
        pass
    assert pending.done()
    cursor.close(uncertain=True)
    official.shutdown_workers()
    assert worker.closed.is_set() and not worker.thread.is_alive()


def test_configuration_change_never_reuses_existing_worker(monkeypatch, warm_runtime):
    with database._cursor():
        pass
    monkeypatch.setattr(official, "child_environment", lambda: {
        "REDSHIFT_WORKGROUP": "changed", "REDSHIFT_DATABASE": "dev",
    })
    with pytest.raises(RedshiftError, match="restart required"):
        with database._cursor():
            pytest.fail("A worker must remain tied to its startup configuration.")
    assert len(warm_runtime) == 1


def test_fork_hook_discards_inherited_pool(warm_runtime):
    with database._cursor():
        pass
    parent_pool = official._pool
    try:
        official._after_fork()
        assert official._pool is not parent_pool
        assert not official._pool.workers
    finally:
        parent_pool.shutdown()


def test_safe_literals_and_internal_placeholders():
    assert literal("TX'); DROP TABLE wells; --") == "'TX''); DROP TABLE wells; --'"
    assert literal("é") == "'é'"
    assert bind("SELECT %s LIMIT %s", ["a'b", 501]) == "SELECT 'a''b' LIMIT 501"
    for bad in ["\\", "\n", "\x00", True, 1.5, None, "x" * 129]:
        with pytest.raises(ValueError):
            literal(bad)
    with pytest.raises(ValueError):
        bind("SELECT %s", [])


def test_lazy_health_and_configuration_are_fail_closed():
    with pytest.raises(RedshiftError, match="not configured"):
        database.test_connection()


def test_environment_removes_other_credentials(monkeypatch, tmp_path):
    executable = tmp_path / "official"
    executable.touch()
    for key, value in {
        "REDSHIFT_WORKGROUP": "default-workgroup", "REDSHIFT_DATABASE": "dev",
        "AWS_REGION": "us-east-2", "REDSHIFT_DB_BUDGET_VERIFIED": "10",
        "REDSHIFT_OFFICIAL_EXECUTABLE": str(executable), "AWS_ACCESS_KEY_ID": "offline-only",
        "AWS_CONTAINER_CREDENTIALS_FULL_URI": "http://invalid",
    }.items():
        monkeypatch.setenv(key, value)
    env = child_environment()
    assert "AWS_ACCESS_KEY_ID" not in env
    assert "AWS_CONTAINER_CREDENTIALS_FULL_URI" not in env
    assert env["MAX_RESULT_ROWS"] == "501"
    assert env["ACCESS_MODE"] == "read-only"
    monkeypatch.setenv("REDSHIFT_DB_BUDGET_VERIFIED", "")
    with pytest.raises(RedshiftError, match="ten-second"):
        child_environment()


@pytest.mark.parametrize("changes", [
    {"row_count": 2}, {"columns": ["a", "a"]}, {"rows": [[1, 2]]},
    {"rows": [[1]] * 502, "row_count": 502}, {"query_id": ""},
])
def test_official_result_rejects_malformed_and_quarantines(changes):
    worker = official._Worker(
        {"REDSHIFT_WORKGROUP": "default-workgroup", "REDSHIFT_DATABASE": "dev"},
        time.monotonic() + 50,
    )
    value = {"columns": ["a"], "rows": [[1]], "row_count": 1, "query_id": "offline"}
    value.update(changes)
    class Session:
        async def call_tool(self, *args):
            return SimpleNamespace(isError=False, structuredContent=value,
                                   content=[SimpleNamespace(type="text", text=json.dumps(value))])
    worker.session = Session()
    try:
        with pytest.raises(QuarantinedError):
            worker.loop.run_until_complete(worker._call(time.monotonic() + 50, sql="SELECT 1"))
    finally:
        worker.loop.close()


def test_official_exact_decimals_and_named_transaction(warm_runtime):
    cursor = OfficialCursor()
    try:
        cursor.open()
        cursor.execute("SELECT %s LIMIT %s", ["exact", 501])
        assert cursor.fetchone() == ["21157564.26"]
        call = warm_runtime[0].calls[1]
        assert call["in_transaction"] == cursor.transaction
        assert call["sql"] == "SELECT 'exact' LIMIT 501"
    finally:
        cursor.close()


async def test_unknown_settlement_quarantines_execution_capacity(monkeypatch):
    permits = threading.BoundedSemaphore(2)
    monkeypatch.setattr(server, "_permits", permits)
    def unknown():
        raise QuarantinedError("No remote settlement evidence.")
    from mcp.server.fastmcp.exceptions import ToolError
    with pytest.raises(ToolError, match="settlement"):
        await server._run(unknown)
    assert permits.acquire(blocking=False)
    assert not permits.acquire(blocking=False)
    permits.release()


def test_real_published_sdk2_tools_over_sdk1_stdio(monkeypatch, tmp_path):
    """Real distribution, initialize/tools/list/call; ONLY the AWS boundary is offline."""
    root = Path(__file__).resolve().parents[1]
    python = root / ".upstream/venv/bin/python"
    if not python.is_file():
        pytest.skip(
            "CUTOVER BLOCKER: isolated SDK2 downloads unavailable; real protocol proof NOT passed."
        )
    launcher = tmp_path / "official-fixture"
    launcher.write_text(f"#!{python}\n" + '''
import importlib.metadata
assert importlib.metadata.version("awslabs.redshift-mcp-server") == "0.1.2"
from awslabs.redshift_mcp_server import server, redshift
async def offline(**kwargs):
    assert kwargs["enforce_read_only"] is True
    return {"columns": ["exact"], "rows": [["21157564.26"]], "row_count": 1,
            "query_id": "offline-only-no-aws-request"}
redshift.execute_query = offline
server.execute_query = offline
server.main()
''')
    launcher.chmod(0o700)
    for key, value in {
        "REDSHIFT_WORKGROUP": "default-workgroup", "REDSHIFT_DATABASE": "dev",
        "AWS_REGION": "us-east-2", "REDSHIFT_DB_BUDGET_VERIFIED": "10",
        "REDSHIFT_OFFICIAL_EXECUTABLE": str(launcher),
    }.items():
        monkeypatch.setenv(key, value)
    cursor = OfficialCursor()
    try:
        cursor.open()
        cursor.execute("SELECT %s LIMIT %s", ["exact", 501])
        assert cursor.fetchone() == ["21157564.26"]
        assert cursor.query_ids == ["offline-only-no-aws-request"] * 2
    finally:
        cursor.close()


def test_standard_stdio_lifecycle_without_aws(monkeypatch, tmp_path):
    """Local SDK1 lifecycle regression, deliberately NOT the SDK2 cutover proof."""
    launcher = tmp_path / "local-mcp"
    launcher.write_text(f"#!{os.sys.executable}\n" + '''
import os
from mcp.server.fastmcp import FastMCP
app = FastMCP("offline-lifecycle")
transactions = set()
def metadata() -> dict:
    return {}
for name in ["list_clusters","list_databases","list_schemas","list_tables",
             "list_columns","review_cluster"]:
    app.tool(name=name)(metadata)
@app.tool()
def execute_query(cluster_identifier: str, cluster_type: str, database_name: str,
                  sql: str | None = None, begin_transaction: str | None = None,
                  in_transaction: str | None = None,
                  rollback_transaction: str | None = None) -> dict:
    if begin_transaction:
        assert not transactions
        transactions.add(begin_transaction)
    elif rollback_transaction:
        transactions.remove(rollback_transaction)
    else:
        assert in_transaction in transactions
    return {"columns": ["exact"] if sql else [], "rows": [["21157564.26"]] if sql else [],
            "row_count": 1 if sql else 0, "query_id": f"offline-local-{os.getpid()}"}
app.run()
''')
    launcher.chmod(0o700)
    for key, value in {
        "REDSHIFT_WORKGROUP": "default-workgroup", "REDSHIFT_DATABASE": "dev",
        "AWS_REGION": "us-east-2", "REDSHIFT_DB_BUDGET_VERIFIED": "10",
        "REDSHIFT_OFFICIAL_EXECUTABLE": str(launcher),
    }.items():
        monkeypatch.setenv(key, value)
    workers, transactions, query_ids = [], [], []
    for _ in range(2):
        with database._cursor() as cursor:
            workers.append(cursor.worker)
            transactions.append(cursor.transaction)
            cursor.execute("SELECT 1 LIMIT 1")
            assert cursor.fetchone() == ["21157564.26"]
            query_ids.extend(cursor.query_ids)
    assert workers[0] is workers[1]
    assert transactions[0] != transactions[1]
    assert len(set(query_ids)) == 1
    pid = int(query_ids[0].rsplit("-", 1)[1])
    official.shutdown_workers()
    assert workers[0].closed.is_set() and workers[0].loop.is_closed()
    assert not workers[0].thread.is_alive()
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)
