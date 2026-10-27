import os
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    """Never load a real .env or inherited database settings in tests."""
    monkeypatch.chdir(tmp_path)
    from redshift_mcp_server import official, server

    monkeypatch.setattr(official, "_pool", official._WorkerPool())
    server._admissions.clear()
    server._analysis_admissions.clear()
    monkeypatch.setattr(os, "environ", os.environ.copy())
    for name in tuple(os.environ):
        if (
            name.startswith(("REDSHIFT_", "AWS_", "CONTAINER_APP_"))
            or name == "PYTHON_DOTENV_DISABLED"
        ):
            monkeypatch.delenv(name)
    yield
    official.shutdown_workers()


@pytest.fixture
def configured(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in {
        "REDSHIFT_HOST": "example.invalid",
        "REDSHIFT_DATABASE": "test",
        "REDSHIFT_USER": "metadata_reader",
        "REDSHIFT_PASSWORD": "synthetic-test-only",
    }.items():
        monkeypatch.setenv(name, value)


@pytest.fixture
def connector(monkeypatch: pytest.MonkeyPatch, configured: None) -> MagicMock:
    connect = MagicMock()
    cursor = connect.return_value.cursor.return_value
    cursor.fetchone.return_value = [1]  # Real connector returns a list, not a tuple.
    cursor.description = [("schema_name",)]
    cursor.fetchmany.return_value = [("public",)]
    monkeypatch.setattr("redshift_mcp_server.database.OfficialCursor", lambda: cursor)
    return connect
