"""N0 (kế hoạch P1): bốn cột khoá ngoại trỏ vào units phải có chỉ mục, kể cả kho 0.8 cũ."""

import sqlite3
from pathlib import Path

import pytest

from soiluat.db import init_schema

FK_COLS = [
    ("units", "fine_source_unit"),
    ("page_regions", "unit_id"),
    ("query_log", "selected_unit"),
    ("effect_hints", "source_unit_id"),
]


def _plan(conn, table, col):
    return " ".join(r[3] for r in conn.execute(f"EXPLAIN QUERY PLAN SELECT 1 FROM {table} WHERE {col} = 1"))


@pytest.mark.parametrize("table,col", FK_COLS)
def test_kho_08_co_chi_muc_sau_init_schema(tmp_path, table, col):
    conn = sqlite3.connect(tmp_path / "kho08.db")
    conn.executescript((Path(__file__).parent / "fixtures" / "schema_08.sql").read_text(encoding="utf-8"))
    assert "SCAN" in _plan(conn, table, col)  # kho 0.8 thiếu chỉ mục: xoá văn bản phải quét cả bảng
    init_schema(conn)
    plan = _plan(conn, table, col)
    assert "INDEX" in plan and "SCAN" not in plan, plan
