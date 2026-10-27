"""The only execution boundary: published AWS MCP over standard stdio MCP."""

import asyncio
import atexit
import json
import os
import sys
import threading
import time
import uuid
from collections import deque
from concurrent.futures import Future, TimeoutError
from contextlib import AsyncExitStack
from datetime import date
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

WHEEL_SHA256 = "03a3fff27161cf0bd3e75765eb9c8ef5f1cfe920811015dcb2c543d712826b40"
PACKAGE = "awslabs.redshift-mcp-server==0.1.2"
TOOLS = {
    "list_clusters", "list_databases", "list_schemas", "list_tables",
    "list_columns", "execute_query", "review_cluster",
}
WORKER_LIMIT = 2
OPERATION_SECONDS = 50
SHUTDOWN_SECONDS = 8


class RedshiftError(RuntimeError):
    """Sanitized execution failure."""


class QuarantinedError(RedshiftError):
    """Remote settlement is unknown; execution permit must not be released."""


def literal(value: Any) -> str:
    if isinstance(value, date):
        return "DATE '" + value.isoformat() + "'"
    if type(value) is int and 0 <= value <= 10000:
        return str(value)
    if isinstance(value, str) and len(value) <= 128:
        if any(ord(c) < 32 or ord(c) == 127 or c == "\\" for c in value):
            raise ValueError("Unsupported filter escape/control character.")
        return "'" + value.replace("'", "''") + "'"
    raise ValueError("Unsupported SQL literal.")


def bind(sql: str, values: Any) -> str:
    parts = sql.split("%s")
    if len(parts) != len(values) + 1:
        raise ValueError("Internal SQL parameter mismatch.")
    return "".join(part + (literal(values[i]) if i < len(values) else "")
                   for i, part in enumerate(parts))


def child_environment() -> dict[str, str]:
    required = ("REDSHIFT_WORKGROUP", "REDSHIFT_DATABASE", "AWS_REGION")
    if any(not os.environ.get(key) for key in required):
        raise RedshiftError("Official MCP runtime target is not configured.")
    if (os.environ["REDSHIFT_WORKGROUP"] != "default-workgroup"
        or os.environ["REDSHIFT_DATABASE"] != "dev"
        or os.environ["AWS_REGION"] != "us-east-2"):
        raise RedshiftError("Official MCP target differs from the approved workgroup.")
    if os.environ.get("REDSHIFT_DB_BUDGET_VERIFIED") != "10":
        raise RedshiftError("Verified database ten-second budget is required.")
    executable = os.environ.get("REDSHIFT_OFFICIAL_EXECUTABLE",
                                "/opt/official/bin/awslabs.redshift-mcp-server")
    if not Path(executable).is_file():
        raise RedshiftError("Pinned official MCP executable is unavailable.")
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("AWS_", "REDSHIFT_PASSWORD"))}
    env.update({
        "AWS_REGION": os.environ["AWS_REGION"], "AWS_DEFAULT_REGION": os.environ["AWS_REGION"],
        "AWS_PROFILE": "redshift-runtime",
        "AWS_CONFIG_FILE": "/app/aws-config",
        "AWS_SHARED_CREDENTIALS_FILE": "/dev/null", "AWS_EC2_METADATA_DISABLED": "true",
        "ACCESS_MODE": "read-only", "MAX_RESULT_ROWS": "501",
        "MAX_OPEN_TRANSACTIONS_PER_TARGET": "2", "SESSION_KEEPALIVE": "60",
        "LOG_LEVEL": "ERROR", "LOG_FILE": "/dev/null",
        "REDSHIFT_OFFICIAL_EXECUTABLE": executable,
    })
    return env


class _Worker:
    """A single task owns SDK/anyio contexts and all calls for this child."""

    def __init__(self, env: dict[str, str], deadline: float) -> None:
        self.env = env
        self.deadline = deadline
        self.ready: Future[None] = Future()
        self.closed = threading.Event()
        self.cleanup_complete = False
        self.stop_lock = threading.Lock()
        self.stop_requested = False
        self.loop = asyncio.new_event_loop()
        self.commands: asyncio.Queue[Any] = asyncio.Queue()
        self.task: asyncio.Task[None] | None = None
        self.outstanding: Future[Any] | None = None
        self.thread = threading.Thread(target=self._run, name="official-mcp", daemon=True)

    def start(self) -> None:
        self.thread.start()

    def _run(self) -> None:
        asyncio.set_event_loop(self.loop)
        try:
            self.task = self.loop.create_task(self._serve())
            self.loop.run_until_complete(self.task)
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
        except BaseException:
            pass
        finally:
            with self.stop_lock:
                self.stop_requested = True
                if not self.ready.done():
                    self.ready.set_exception(RedshiftError(
                        "Official MCP initialization/contract verification failed."
                    ))
                if self.outstanding is not None and not self.outstanding.done():
                    self.outstanding.set_exception(QuarantinedError(
                        "Official MCP worker stopped; capacity quarantined."
                    ))
            self.loop.close()
            self.closed.set()

    async def _serve(self) -> None:
        stack = AsyncExitStack()
        pending: Future[Any] | None = None
        failure = RedshiftError("Official MCP initialization/contract verification failed.")
        errlog = open(os.devnull, "w")
        try:
            # Contexts must be entered and exited by this same long-lived task.
            async with asyncio.timeout(max(0, self.deadline - time.monotonic())):
                streams = await stack.enter_async_context(stdio_client(StdioServerParameters(
                    command=sys.executable, args=["-m", "redshift_mcp_server.official_stdio"],
                    env=self.env,
                ), errlog=errlog))
                self.session = await stack.enter_async_context(ClientSession(*streams))
                async with asyncio.timeout(15):
                    await self.session.initialize()
                async with asyncio.timeout(15):
                    tools = await self.session.list_tools()
            if {tool.name for tool in tools.tools} != TOOLS:
                raise RedshiftError("Official MCP tool contract changed.")
            tool = next(t for t in tools.tools if t.name == "execute_query")
            properties = tool.inputSchema.get("properties", {})
            required = {"sql", "begin_transaction", "in_transaction", "rollback_transaction"}
            if not required <= properties.keys():
                raise RedshiftError("Official transaction contract unavailable.")
            self.ready.set_result(None)
            while True:
                command = await self.commands.get()
                if command is None:
                    break
                args, deadline, pending = command
                try:
                    pending.set_result(await self._call(deadline, **args))
                except Exception:
                    pending.set_exception(QuarantinedError(
                        "Official MCP execution did not prove settlement; capacity quarantined."
                    ))
                pending = None
        except BaseException:
            pass  # Provider bodies and exception groups must never reach logs or callers.
        finally:
            with self.stop_lock:
                self.stop_requested = True
            try:
                await stack.aclose()
                self.cleanup_complete = True
            except BaseException:
                failure = QuarantinedError("Official MCP cleanup did not prove settlement.")
            finally:
                errlog.close()
                if not self.ready.done():
                    self.ready.set_exception(failure)
                if pending is not None and not pending.done():
                    pending.set_exception(QuarantinedError(
                        "Official MCP execution did not prove settlement; capacity quarantined."
                    ))
                while not self.commands.empty():
                    queued = self.commands.get_nowait()
                    if queued is not None and not queued[2].done():
                        queued[2].set_exception(QuarantinedError(
                            "Official MCP worker stopped; capacity quarantined."
                        ))

    async def _call(self, deadline: float, **args: Any) -> dict[str, Any]:
        try:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError
            async with asyncio.timeout(remaining):
                result = await self.session.call_tool("execute_query", {
                    "cluster_identifier": self.env["REDSHIFT_WORKGROUP"],
                    "cluster_type": "serverless", "database_name": self.env["REDSHIFT_DATABASE"],
                    **args,
                })
            if result.isError:
                raise ValueError("Upstream tool failed.")
            value = result.structuredContent
            if value is None:
                if len(result.content) != 1 or result.content[0].type != "text":
                    raise ValueError("Invalid upstream envelope.")
                value = json.loads(result.content[0].text)
            if not isinstance(value, dict) or len(json.dumps(value).encode()) > 1024 * 1024:
                raise ValueError("Invalid upstream result.")
            if len(result.content) != 1 or result.content[0].type != "text":
                raise ValueError("Invalid upstream text envelope.")
            if json.loads(result.content[0].text) != value:
                raise ValueError("Upstream result envelopes disagree.")
            columns, rows = value.get("columns"), value.get("rows")
            if (not isinstance(columns, list) or not all(isinstance(c, str) for c in columns)
                or len(set(columns)) != len(columns) or not isinstance(rows, list)
                or type(value.get("row_count")) is not int or value["row_count"] != len(rows)
                or len(rows) > 501 or not all(isinstance(r, list) and len(r) == len(columns)
                                             and all(v is None or type(v) in (str, int, bool)
                                                     for v in r)
                                             for r in rows)
                or not isinstance(value.get("query_id"), str) or not value["query_id"]):
                raise ValueError("Invalid upstream result fields.")
            return value
        except asyncio.CancelledError:
            raise
        except BaseException:
            raise QuarantinedError(
                "Official MCP execution did not prove settlement; capacity quarantined."
            ) from None

    def call(self, deadline: float, **args: Any) -> dict[str, Any]:
        pending: Future[dict[str, Any]] = Future()
        with self.stop_lock:
            if self.closed.is_set() or self.stop_requested:
                raise QuarantinedError("Official MCP worker stopped; capacity quarantined.")
            self.outstanding = pending
            self.loop.call_soon_threadsafe(self.commands.put_nowait, (args, deadline, pending))
        return pending.result(timeout=max(0, deadline - time.monotonic()))

    def stop(self, *, cancel: bool = False) -> None:
        with self.stop_lock:
            if self.closed.is_set() or self.stop_requested:
                return
            self.stop_requested = True
        def signal() -> None:
            if cancel and self.task is not None:
                self.task.cancel()
            else:
                self.commands.put_nowait(None)
        try:
            self.loop.call_soon_threadsafe(signal)
        except RuntimeError:
            pass  # The worker may have finished between the closed check and signal.


class _WorkerPool:
    """No waiting queue: idle workers are leased FIFO, saturation fails closed."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.workers: list[_Worker] = []
        self.available: deque[_Worker] = deque()
        self.environment: dict[str, str] | None = None
        self.stopping = False

    def acquire(self, env: dict[str, str], deadline: float) -> _Worker:
        with self.lock:
            if self.stopping:
                raise RedshiftError("Official MCP worker pool is shutting down.")
            if self.environment is not None and self.environment != env:
                raise RedshiftError("Official MCP runtime configuration changed; restart required.")
            if time.monotonic() >= deadline:
                raise RedshiftError("Official MCP operation deadline exceeded.")
            if self.available:
                return self.available.popleft()
            if len(self.workers) >= WORKER_LIMIT:
                raise RedshiftError("Official MCP is busy; capacity unavailable.")
            worker = _Worker(env, deadline)
            self.environment = env
            self.workers.append(worker)
            worker.start()
            return worker

    def release(self, worker: _Worker, *, reusable: bool) -> None:
        with self.lock:
            if reusable and not self.stopping and not worker.closed.is_set():
                self.available.append(worker)
                return
        worker.stop(cancel=True)
        # An uncertain worker remains in workers forever: disposal does not restore capacity.

    def initialization_failed(self, worker: _Worker, deadline: float) -> None:
        worker.stop(cancel=True)
        worker.thread.join(timeout=max(0, deadline - time.monotonic()))
        with self.lock:
            if worker.closed.is_set() and worker.cleanup_complete:
                self.workers.remove(worker)  # No transaction was ever submitted.
            else:
                raise QuarantinedError("Official MCP initialization cleanup is unconfirmed.")

    def shutdown(self) -> None:
        deadline = time.monotonic() + SHUTDOWN_SECONDS
        with self.lock:
            if self.stopping:
                return
            self.stopping = True
            self.available.clear()
            workers = list(self.workers)
        for worker in workers:
            worker.stop(cancel=True)
        for worker in workers:
            worker.thread.join(timeout=max(0, deadline - time.monotonic()))


_pool = _WorkerPool()


def shutdown_workers() -> None:
    """Bounded application teardown; never resets quarantined capacity while serving."""
    _pool.shutdown()


def _after_fork() -> None:
    # Inherited locks/loops belong to vanished parent threads, never to the child.
    global _pool
    _pool = _WorkerPool()


if hasattr(os, "register_at_fork"):
    os.register_at_fork(after_in_child=_after_fork)
atexit.register(shutdown_workers)


class OfficialCursor:
    """Exclusive warm-worker lease with a fresh named read-only snapshot."""

    def __init__(self) -> None:
        self.transaction = "policy-" + uuid.uuid4().hex
        self.description: list[tuple[str]] = []
        self.rows: list[list[Any]] = []
        self.query_ids: list[str] = []
        self.deadline = time.monotonic() + OPERATION_SECONDS
        self.worker: _Worker | None = None
        self.started = False
        self.uncertain = False

    def open(self) -> None:
        self.worker = _pool.acquire(child_environment(), self.deadline)
        try:
            self.worker.ready.result(timeout=max(0, self.deadline - time.monotonic()))
        except BaseException:
            worker, self.worker = self.worker, None
            _pool.initialization_failed(worker, self.deadline)
            raise RedshiftError(
                "Official MCP initialization/contract verification failed."
            ) from None
        self._call(begin_transaction=self.transaction)

    def _call(self, **args: Any) -> dict[str, Any]:
        assert self.worker is not None
        self.started = True
        try:
            value = self.worker.call(self.deadline, **args)
            self.query_ids.append(value["query_id"])
            return value
        except BaseException:
            self.uncertain = True
            raise QuarantinedError(
                "Official MCP execution did not prove settlement; capacity quarantined."
            ) from None

    def execute(self, sql: str, values: Any = ()) -> None:
        value = self._call(
            sql=bind(sql, values), in_transaction=self.transaction,
        )
        self.description = [(c,) for c in value["columns"]]
        self.rows = value["rows"]

    def fetchmany(self, limit: int) -> list[list[Any]]:
        return self.rows[:limit]

    def fetchone(self) -> list[Any] | None:
        return self.rows[0] if self.rows else None

    def close(self, *, uncertain: bool = False) -> None:
        if self.worker is None:
            return
        self.uncertain |= uncertain
        try:
            if not self.uncertain and self.started:
                self._call(rollback_transaction=self.transaction)
                self.started = False
        finally:
            _pool.release(
                self.worker, reusable=not self.uncertain,
            )
            self.worker = None
