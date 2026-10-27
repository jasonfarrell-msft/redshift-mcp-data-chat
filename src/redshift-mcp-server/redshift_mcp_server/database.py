"""Bounded metadata operations; no user-provided SQL or identifier interpolation."""

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import Any

from redshift_mcp_server.official import OfficialCursor, QuarantinedError, RedshiftError


def validate_name(value: str, argument: str) -> str:
    """Accept quoted/unusual SQL names safely as values, while rejecting invalid input."""
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise ValueError(f"{argument} must be a nonempty name without NUL characters.")
    if len(value.encode("utf-8")) > 127:
        raise ValueError(f"{argument} must be at most 127 UTF-8 bytes.")
    return value


def validate_limit(limit: int) -> int:
    if type(limit) is not int or not 1 <= limit <= 500:
        raise ValueError("limit must be an integer between 1 and 500.")
    return limit


@contextmanager
def _cursor() -> Iterator[Any]:
    """Compatibility surface for semantic code, NOT a database driver connection."""
    cursor = OfficialCursor()
    uncertain = False
    try:
        cursor.open()
        yield cursor
    except QuarantinedError:
        uncertain = True
        raise
    except (RedshiftError, ValueError):
        raise
    except Exception:
        raise RedshiftError("Official MCP operation failed; provider details suppressed.") from None
    finally:
        cursor.close(uncertain=uncertain)


def _query(sql: str, parameters: Sequence[Any], limit: int) -> dict[str, Any]:
    with _cursor() as cursor:
        cursor.execute(sql, tuple(parameters))
        rows = cursor.fetchmany(limit + 1)
        columns = [column[0] for column in cursor.description]
        return {
            "items": [dict(zip(columns, row, strict=True)) for row in rows[:limit]],
            "truncated": len(rows) > limit,
        }


def test_connection() -> dict[str, bool]:
    with _cursor() as cursor:
        cursor.execute("SELECT 1")
        row = cursor.fetchone()
        if row is None or tuple(row) != (1,):
            raise RedshiftError("Redshift connection probe returned an unexpected result.")
    return {"connected": True}


def list_schemas(limit: int = 100) -> dict[str, Any]:
    limit = validate_limit(limit)
    return _query(
        "SELECT schema_name FROM svv_all_schemas "
        "WHERE database_name = current_database() "
        "AND schema_name NOT IN ('pg_catalog', 'information_schema') "
        "ORDER BY schema_name LIMIT %s",
        (limit + 1,),
        limit,
    )


def list_tables(schema: str, limit: int = 100) -> dict[str, Any]:
    schema = validate_name(schema, "schema")
    limit = validate_limit(limit)
    return _query(
        "SELECT schema_name AS table_schema, table_name, "
        "CASE WHEN table_type = 'TABLE' THEN 'BASE TABLE' ELSE table_type END AS table_type "
        "FROM svv_all_tables WHERE database_name = current_database() "
        "AND schema_name = %s ORDER BY table_name LIMIT %s",
        (schema, limit + 1),
        limit,
    )


def describe_table(schema: str, table: str, limit: int = 100) -> dict[str, Any]:
    schema = validate_name(schema, "schema")
    table = validate_name(table, "table")
    limit = validate_limit(limit)
    return _query(
        "SELECT schema_name AS table_schema, table_name, column_name, ordinal_position, data_type, "
        "is_nullable, column_default FROM svv_all_columns "
        "WHERE database_name = current_database() AND schema_name = %s AND table_name = %s "
        "ORDER BY ordinal_position LIMIT %s",
        (schema, table, limit + 1),
        limit,
    )
