import sqlite3
from contextlib import nullcontext
from unittest.mock import MagicMock

import pytest

from redshift_mcp_server import database


def test_no_connect_without_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(database.RedshiftError, match="not configured"):
        database.test_connection()


def test_tls_timeout_readonly_and_cleanup(connector: MagicMock) -> None:
    assert database.test_connection() == {"connected": True}
    cursor = connector.return_value.cursor.return_value
    cursor.open.assert_called_once()
    cursor.execute.assert_called_once_with("SELECT 1")
    cursor.close.assert_called_once_with(uncertain=False)
    connector.return_value.commit.assert_not_called()


def test_transaction_setup_order(connector: MagicMock) -> None:
    cursor = connector.return_value.cursor.return_value
    database.test_connection()
    assert [call[0] for call in cursor.mock_calls] == ["open", "execute", "fetchone", "close"]


def test_iam_default_provider_chain(connector: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REDSHIFT_PASSWORD", "ignored-old-password")
    database.test_connection()
    connector.assert_not_called()


@pytest.mark.parametrize("operation", ["list_schemas", "list_tables", "describe_table"])
def test_metadata_parameters_and_truncation(connector: MagicMock, operation: str) -> None:
    cursor = connector.return_value.cursor.return_value
    cursor.fetchmany.return_value = [("one",), ("two",), ("three",)]
    name = "x'; DROP TABLE demo; --"
    arguments = {
        "list_schemas": (),
        "list_tables": (name,),
        "describe_table": (name, 'A "quoted" table\'; DROP TABLE demo; --'),
    }[operation]
    result = getattr(database, operation)(*arguments, limit=2)
    sql, params = cursor.execute.call_args.args
    assert params == (*arguments, 3)
    assert all(argument not in sql for argument in arguments)
    catalog = {
        "list_schemas": "svv_all_schemas",
        "list_tables": "svv_all_tables",
        "describe_table": "svv_all_columns",
    }[operation]
    assert f"FROM {catalog}" in sql
    assert "database_name = current_database()" in sql
    assert "information_schema." not in sql
    if arguments:
        assert "schema_name = %s" in sql
        assert "schema_name AS table_schema" in sql
    if operation == "describe_table":
        assert "table_name = %s" in sql
        assert "ORDER BY ordinal_position LIMIT %s" in sql
    elif operation == "list_tables":
        assert "WHEN table_type = 'TABLE' THEN 'BASE TABLE' ELSE table_type" in sql
        assert "ORDER BY table_name LIMIT %s" in sql
    else:
        assert "schema_name NOT IN ('pg_catalog', 'information_schema')" in sql
        assert "ORDER BY schema_name LIMIT %s" in sql
    assert sql.count("%s") == len(params)
    cursor.fetchmany.assert_called_once_with(3)
    assert result == {
        "items": [{"schema_name": "one"}, {"schema_name": "two"}],
        "truncated": True,
    }


@pytest.mark.parametrize("value", [0, 501, True, 1.2, "2"])
def test_bad_limit_rejected_before_connection(connector: MagicMock, value: object) -> None:
    with pytest.raises(ValueError, match="limit"):
        database.list_schemas(value)
    connector.assert_not_called()


@pytest.mark.parametrize("value", ["", "  ", "a\x00b", "a" * 128, "é" * 64])
def test_bad_names_rejected_before_connection(connector: MagicMock, value: str) -> None:
    with pytest.raises(ValueError, match="schema"):
        database.list_tables(value)
    connector.assert_not_called()


def test_empty_results(connector: MagicMock) -> None:
    connector.return_value.cursor.return_value.fetchmany.return_value = []
    assert database.list_tables("public") == {"items": [], "truncated": False}


@pytest.mark.parametrize("stage", ["open", "execute", "fetchmany"])
def test_failures_are_sanitized_and_cleanup_attempted(connector: MagicMock, stage: str) -> None:
    connection = connector.return_value
    cursor = connection.cursor.return_value
    target = getattr(cursor, stage)
    target.side_effect = RuntimeError("synthetic-sensitive-connector-details")
    with pytest.raises(database.RedshiftError) as error:
        database.list_schemas()
    assert "synthetic-sensitive" not in str(error.value)
    cursor.close.assert_called_once()


@pytest.mark.parametrize("method", ["cursor_close"])
def test_cleanup_failure_is_reported(connector: MagicMock, method: str) -> None:
    connection = connector.return_value
    cursor = connection.cursor.return_value
    cursor.close.side_effect = database.QuarantinedError("cleanup failed")
    with pytest.raises(database.QuarantinedError, match="cleanup failed"):
        database.test_connection()
    cursor.close.assert_called_once()


def test_operation_failure_takes_precedence(connector: MagicMock) -> None:
    connection = connector.return_value
    connection.cursor.return_value.execute.side_effect = RuntimeError("private")
    with pytest.raises(database.RedshiftError, match="operation failed"):
        database.list_schemas()
    connection.cursor.return_value.close.assert_called_once()


def test_unexpected_probe_result(connector: MagicMock) -> None:
    connector.return_value.cursor.return_value.fetchone.return_value = None
    with pytest.raises(database.RedshiftError, match="unexpected result"):
        database.test_connection()


@pytest.mark.parametrize(
    ("operation", "arguments", "columns", "row"),
    [
        (
            "list_tables",
            ("public",),
            ("table_schema", "table_name", "table_type"),
            ("public", "sample", "BASE TABLE"),
        ),
        (
            "describe_table",
            ("public", "sample"),
            (
                "table_schema",
                "table_name",
                "column_name",
                "ordinal_position",
                "data_type",
                "is_nullable",
                "column_default",
            ),
            ("public", "sample", "id", 1, "integer", "NO", None),
        ),
    ],
)
def test_metadata_column_mapping(
    connector: MagicMock,
    operation: str,
    arguments: tuple[str, ...],
    columns: tuple[str, ...],
    row: tuple[object, ...],
) -> None:
    cursor = connector.return_value.cursor.return_value
    cursor.description = [(name,) for name in columns]
    cursor.fetchmany.return_value = [row]
    result = getattr(database, operation)(*arguments)
    assert result == {"items": [dict(zip(columns, row, strict=True))], "truncated": False}


@pytest.mark.parametrize("operation", ["list_schemas", "list_tables", "describe_table"])
def test_native_catalog_queries_preserve_scoping_and_contract(
    monkeypatch: pytest.MonkeyPatch, operation: str,
) -> None:
    """Execute the generated SELECTs against native-shaped, credential-free catalogs."""
    schema = "Exact'; DROP TABLE svv_all_tables; --"
    table = 'Exact "Table"\'; DROP TABLE svv_all_columns; --'
    with sqlite3.connect(":memory:") as connection:
        connection.create_function("current_database", 0, lambda: "current")
        connection.executescript(
            "CREATE TABLE svv_all_schemas (database_name, schema_name);"
            "CREATE TABLE svv_all_tables (database_name, schema_name, table_name, table_type);"
            "CREATE TABLE svv_all_columns (database_name, schema_name, table_name, "
            "column_name, ordinal_position, data_type, is_nullable, column_default);"
        )
        connection.executemany("INSERT INTO svv_all_schemas VALUES (?, ?)", [
            ("other", "foreign"), ("current", "pg_catalog"),
            ("current", "information_schema"), ("current", "external"),
            ("current", "local"), ("current", "public"),
        ])
        connection.executemany("INSERT INTO svv_all_tables VALUES (?, ?, ?, ?)", [
            ("other", schema, "foreign", "TABLE"),
            ("current", "different", "wrong_schema", "TABLE"),
            ("current", schema, "a", "TABLE"),
            ("current", schema, "b", "VIEW"),
            ("current", schema, "c", "EXTERNAL TABLE"),
        ])
        connection.executemany("INSERT INTO svv_all_columns VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
            ("other", schema, table, "foreign", 1, "integer", "NO", None),
            ("current", "different", table, "wrong_schema", 1, "integer", "NO", None),
            ("current", schema, "different", "wrong_table", 1, "integer", "NO", None),
            ("current", schema, table, "last", 3, "integer", "YES", None),
            ("current", schema, table, "first", 1, "integer", "NO", "0"),
            ("current", schema, table, "second", 2, "varchar", "YES", None),
        ])
        cursor = connection.cursor()
        # DB-API description is populated by execute, not before it.
        class CatalogCursor:
            def execute(self, sql, params):
                return cursor.execute(sql.replace("%s", "?"), params)

            @property
            def description(self):
                return cursor.description

            def fetchmany(self, size):
                return cursor.fetchmany(size)

        monkeypatch.setattr(database, "_cursor", lambda: nullcontext(CatalogCursor()))
        arguments = {
            "list_schemas": (), "list_tables": (schema,), "describe_table": (schema, table),
        }[operation]
        result = getattr(database, operation)(*arguments, limit=2)
        assert result["truncated"] is True
        assert len(result["items"]) == 2
        complete = getattr(database, operation)(*arguments, limit=3)
        assert complete["truncated"] is False
        if operation == "list_schemas":
            assert complete["items"] == [
                {"schema_name": name} for name in ("external", "local", "public")
            ]
        elif operation == "list_tables":
            assert complete["items"] == [
                {"table_schema": schema, "table_name": name, "table_type": kind}
                for name, kind in (("a", "BASE TABLE"), ("b", "VIEW"), ("c", "EXTERNAL TABLE"))
            ]
        else:
            assert complete["items"] == [
                {"table_schema": schema, "table_name": table, "column_name": name,
                 "ordinal_position": position, "data_type": kind,
                 "is_nullable": nullable, "column_default": default}
                for name, position, kind, nullable, default in (
                    ("first", 1, "integer", "NO", "0"),
                    ("second", 2, "varchar", "YES", None),
                    ("last", 3, "integer", "YES", None),
                )
            ]
