import asyncio
import threading
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from mcp.server.fastmcp.exceptions import ToolError
from pydantic import ValidationError

from redshift_mcp_server import analytics as a
from redshift_mcp_server import server
from redshift_mcp_server.database import RedshiftError


def plan(**changes):
    return a.AnalysisPlan.model_validate(
        {
            "version": "1",
            "dataset": "production",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "measures": [{"field": "oil_bbl", "aggregation": "sum"}],
            **changes,
        }
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"sql": "SELECT secret"},
        {"schema": "public"},
        {"version": "2"},
        {"dataset": "daily_production"},
        {"limit": True},
        {"limit": 501},
        {"limit": "2"},
        {"group_by": ["well_id; DROP TABLE wells"]},
        {"group_by": ["state", "state"]},
        {"time_bucket": "week"},
        {"start_date": "2025-1-1"},
        {"end_date": "2024-12-31"},
        {"start_date": "2000-01-01"},
        {"start_date": None},
        {"measures": [{"field": "oil_bbl", "aggregation": "sum", "expression": "1=1"}]},
        {"measures": [{"field": "profit", "aggregation": "sum"}]},
        {"measures": [{"field": "oil_bbl", "aggregation": "avg"}]},
        {"filters": [{"field": "state", "operator": "like", "values": ["%"]}]},
        {"filters": [{"field": "state", "operator": "eq", "values": ["TX", "OK"]}]},
        {"filters": [{"field": "state", "operator": "eq", "values": ["\x00"]}]},
        {"filters": [{"field": "well_id", "operator": "in", "values": []}]},
        {"order_by": {"measure_index": 1}},
        {"order_by": {"measure_index": True}},
        {"order_by": {"measure_index": 0, "direction": "DESC; SELECT 1"}},
    ],
)
def test_closed_strict_plan(changes):
    with pytest.raises(ValidationError):
        plan(**changes)


@pytest.mark.parametrize("empty_production,empty_prices", [
    (False, False), (True, False), (False, True), (True, True),
])
def test_context_one_live_coverage_query_preserves_envelope(
    connector, empty_production, empty_prices,
):
    cursor = connector.return_value.cursor.return_value
    cursor.description = [(column,) for column in [
        "first_date", "last_date", "production_records", "first_month",
        "last_month", "price_records",
    ]]
    production = (
        (None, None, 0) if empty_production else (date(2025, 1, 1), date(2025, 12, 31), 365)
    )
    prices = (None, None, 0) if empty_prices else (date(2025, 1, 1), date(2025, 12, 1), 12)
    cursor.fetchmany.return_value = [(*production, *prices)]
    value = a.get_data_context()
    cursor.execute.assert_called_once()
    sql, parameters = cursor.execute.call_args.args
    assert parameters == ()
    assert "CROSS JOIN" in sql
    assert "MIN(production_date)" in sql and "MAX(production_date)" in sql
    assert "MIN(price_month)" in sql and "MAX(price_month)" in sql
    assert sql.count("COUNT(*)") == 2
    assert "oge_synthetic.daily_production" in sql
    assert "oge_synthetic.monthly_prices" in sql
    assert value["production_coverage"] == {
        "first_date": None if empty_production else "2025-01-01",
        "last_date": None if empty_production else "2025-12-31",
        "records": 0 if empty_production else 365,
    }
    assert value["price_coverage"] == {
        "first_month": None if empty_prices else "2025-01-01",
        "last_month": None if empty_prices else "2025-12-01",
        "records": 0 if empty_prices else 12,
    }
    assert set(value) == {
        "version", "schema", "production_coverage", "price_coverage",
        "datasets", "limits", "notes",
    }
    assert value["limits"]["statement_timeout_ms"] == 10000
    cursor.close.assert_called_once_with(uncertain=False)
    # Calling again must execute again, not return cached mutable coverage.
    a.get_data_context()
    assert cursor.execute.call_count == 2


def test_parameterization_and_registered_only_join():
    injection = "TX'); DROP TABLE wells; --"
    p = plan(
        filters=[{"field": "state", "operator": "eq", "values": [injection]}],
        group_by=["operator"],
        order_by={"measure_index": 0, "direction": "desc"},
        limit=5,
    )
    sql, params, units = a.compile_query(p, "daily_production", "day", "production_date")
    assert injection not in sql
    assert params == [date(2025, 1, 1), date(2025, 12, 31), injection, 6]
    assert "JOIN oge_synthetic.wells w ON p.well_id = w.well_id" in sql
    assert "w.state IN (%s)" in sql
    assert "ORDER BY oil_bbl_sum DESC NULLS LAST, 1 ASC NULLS LAST" in sql
    assert units == {"oil_bbl_sum": "bbl"}
    with pytest.raises(ValueError, match="Unregistered"):
        a.compile_query(p, "secret", "day", "production_date")


@pytest.mark.parametrize(
    ("changes", "source", "grain", "column", "checked"),
    [
        ({}, "daily_production", "day", "production_date", False),
        ({"time_bucket": "day"}, "daily_production", "day", "production_date", False),
        ({"time_bucket": "month"}, "monthly_production", "month", "production_month", True),
        ({"time_bucket": "year"}, "annual_production", "year", "production_year", True),
        (
            {"time_bucket": "year", "start_date": "2025-02-01"},
            "monthly_production",
            "month",
            "production_month",
            True,
        ),
        (
            {"time_bucket": "month", "start_date": "2025-01-02"},
            "daily_production",
            "day",
            "production_date",
            False,
        ),
    ],
)
def test_source_requires_full_period_and_reconciles_every_well_period(
    monkeypatch, changes, source, grain, column, checked
):
    check = MagicMock(return_value=True)
    monkeypatch.setattr(a, "_integrity", check)
    assert a._source(MagicMock(), plan(**changes)) == (source, grain, column)
    assert check.call_count == (2 if checked else 1)
    if checked:
        sql = check.call_args.args[1]
        assert "FULL OUTER JOIN" in sql and "r.copies = 1" in sql
        assert "oil_bbl_nulls = 0" in sql and "gas_mcf_nulls = 0" in sql
        check.side_effect = [True, False]
        assert a._source(MagicMock(), plan(**changes))[0] == "daily_production"


def test_prices_and_wells_have_distinct_semantics(monkeypatch):
    p = plan(dataset="prices", measures=[{"field": "oil_usd_per_bbl", "aggregation": "avg"}])
    check = MagicMock(return_value=True)
    monkeypatch.setattr(a, "_integrity", check)
    assert a._source(MagicMock(), p) == ("monthly_prices", "month", "price_month")
    assert "COUNT(DISTINCT price_month)" in check.call_args.args[1]
    sql, _, units = a.compile_query(p, "monthly_prices", "month", "price_month")
    assert "AVG(CAST(p.oil_usd_per_bbl AS DECIMAL(38, 8)))" in sql and "JOIN" not in sql
    assert units == {"oil_usd_per_bbl_avg": "USD/bbl"}
    for changes in (
        {"start_date": "2025-01-02"},
        {"group_by": ["state"]},
        {"time_bucket": "day"},
        {"end_date": "2025-12-30"},
    ):
        with pytest.raises(ValidationError):
            plan(
                dataset="prices",
                measures=[{"field": "oil_usd_per_bbl", "aggregation": "avg"}],
                **changes,
            )
    w = plan(
        dataset="wells",
        start_date=None,
        end_date=None,
        measures=[{"field": "wells", "aggregation": "count"}],
        group_by=["basin"],
    )
    assert a._source(MagicMock(), w) == ("wells", "well", "start_month")
    assert "COUNT(DISTINCT well_id)" in check.call_args.args[1]
    sql, params, _ = a.compile_query(w, "wells", "well", "start_month")
    assert "WHERE" not in sql and params == [101]
    check.return_value = False
    with pytest.raises(RedshiftError, match="unique"):
        a._source(MagicMock(), w)


def result_cursor(connector, rows):
    cursor = connector.return_value.cursor.return_value
    cursor.description = [
        ("oil_bbl_sum",),
        ("oil_bbl_sum_null_records",),
        ("source_records",),
        ("first_observation",),
        ("last_observation",),
    ]
    cursor.fetchmany.return_value = rows
    return cursor


def test_execution_precision_nulls_and_no_commit(connector, monkeypatch):
    monkeypatch.setattr(a, "_integrity", MagicMock(return_value=True))
    cursor = result_cursor(
        connector,
        [
            (Decimal("222089936.27000001"), 1, 2, date(2025, 1, 1), date(2025, 1, 2)),
        ],
    )
    value = a.analyze_data(plan())
    assert value["items"][0]["oil_bbl_sum"] == "222089936.27000001"
    assert value["items"][0]["oil_bbl_sum_null_records"] == 1
    assert value["plan"]["end_date"] == "2025-12-31"
    assert value["items"][0]["first_observation"] == "2025-01-01"
    assert value["source"] == "oge_synthetic.daily_production"
    assert value["executed"] is True and value["status"] == "ok"
    cursor.open.assert_called_once()
    connector.return_value.commit.assert_not_called()
    cursor.close.assert_called_once_with(uncertain=False)


@pytest.mark.parametrize(
    ("rows", "status", "items"),
    [
        ([], "empty", []),
        ([(None, 0, 0, None, None)], "empty", []),
        ([(None, 3, 3, date(2025, 1, 1), date(2025, 1, 3))], "ok", [None]),
    ],
)
def test_empty_is_not_null_or_zero(connector, monkeypatch, rows, status, items):
    monkeypatch.setattr(a, "_integrity", MagicMock(return_value=True))
    result_cursor(connector, rows)
    value = a.analyze_data(plan())
    assert value["status"] == status
    assert [row["oil_bbl_sum"] for row in value["items"]] == items


def test_truncation_by_rows_and_utf8_bytes(connector, monkeypatch):
    monkeypatch.setattr(a, "_integrity", MagicMock(return_value=True))
    result_cursor(connector, [(Decimal("1.2"), 0, 1, None, None)] * 3)
    value = a.analyze_data(plan(limit=2))
    assert len(value["items"]) == 2 and value["status"] == "truncated"
    monkeypatch.setattr(a, "MAX_BYTES", a._response_bytes(value) - 1)
    value = a.analyze_data(plan(limit=2))
    assert len(value["items"]) == 1 and value["truncated"] is True
    assert a._response_bytes(value) <= a.MAX_BYTES


def test_fanout_or_orphans_fail_closed(connector, monkeypatch):
    monkeypatch.setattr(a, "_integrity", MagicMock(side_effect=[True, True, False]))
    with pytest.raises(RedshiftError, match="unmatched"):
        a.analyze_data(plan(group_by=["state"]))
    monkeypatch.setattr(a, "_integrity", MagicMock(side_effect=[True, False]))
    with pytest.raises(RedshiftError, match="unique"):
        a.analyze_data(plan(group_by=["operator"]))


def test_daily_duplicate_or_null_grain_fails_before_compilation(connector, monkeypatch):
    check = MagicMock(return_value=False)
    monkeypatch.setattr(a, "_integrity", check)
    with pytest.raises(RedshiftError, match="Daily production grain"):
        a.analyze_data(plan())
    sql = check.call_args.args[1]
    assert "GROUP BY well_id, production_date" in sql
    assert "HAVING COUNT(*) > 1 OR well_id IS NULL" in sql
    assert "BETWEEN %s AND %s" in sql


async def test_cancelled_call_retains_worker_permit_and_saturation_is_rejected():
    entered = [threading.Event(), threading.Event()]
    finish = threading.Event()

    def work(index):
        entered[index].set()
        assert finish.wait(5)
        return index

    tasks = [asyncio.create_task(server._run(work, i)) for i in range(2)]
    try:
        for event in entered:
            assert await asyncio.to_thread(event.wait, 2)
        tasks[0].cancel()
        with pytest.raises(asyncio.CancelledError):
            await tasks[0]
        with pytest.raises(ToolError, match="busy"):
            await server._run(lambda: None)
    finally:
        finish.set()
        await tasks[1]
    # Both worker completions, not the cancelled coroutine, release the permits.
    assert await server._run(lambda: "ready") == "ready"


async def test_direct_analytics_rate_limit_rejects_before_database(monkeypatch):
    operation = MagicMock(return_value={})
    monkeypatch.setattr(a, "get_data_context", operation)
    for _ in range(12):
        await server._run(operation)
    with pytest.raises(ToolError, match="rate exceeded"):
        await server._run(operation)
    assert operation.call_count == 12


async def test_direct_global_rate_limit_cannot_be_bypassed_by_metadata():
    import time

    server._admissions.extend([time.monotonic()] * 120)
    with pytest.raises(ToolError, match="rate exceeded"):
        await server._run(lambda: None)
