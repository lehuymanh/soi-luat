"""Kế hoạch P1, N1c: dựng lại văn bản giữ gợi ý hiệu lực đã duyệt và không để giao dịch dở khi lỗi."""

import sqlite3

import pytest

from soiluat import ingest
from soiluat.ingest import ingest_path
from soiluat.rebuild import rebuild_document

ND9 = (
    "Nghị định số 9/2021/NĐ-CP\n"
    "Điều 1. Phạm vi điều chỉnh\n"
    "Nghị định này quy định về xử phạt.\n"
    "Điều 2. Hiệu lực thi hành\n"
    "1. Nghị định này có hiệu lực thi hành từ ngày 01 tháng 01 năm 2021 và thay thế Nghị định số 46/2016/NĐ-CP.\n"
    "2. Kể từ ngày Nghị định này có hiệu lực thi hành, bãi bỏ Điều 3 Nghị định số 10/2015/NĐ-CP.\n"
    "3. Kể từ ngày Nghị định này có hiệu lực thi hành, bãi bỏ khoản 2 Điều 4 Thông tư số 11/2016/TT-BTC.\n"
)


@pytest.fixture
def nd9(db, tmp_path):
    p = tmp_path / "nd9.txt"
    p.write_text(ND9, encoding="utf-8")
    return ingest_path(db, p, tmp_path)


def _hints(db, doc_id):
    return db.execute(
        "SELECT id, kind, target_so_hieu, confirmed FROM effect_hints WHERE source_doc_id = ? ORDER BY id", (doc_id,)
    ).fetchall()


def test_goi_y_da_duyet_con_sau_dung_lai(db, nd9):
    hints = _hints(db, nd9)
    tt = [h for h in hints if h["kind"] == "thay_the"]
    assert len(tt) == 1 and sum(h["kind"] == "bai_bo" for h in hints) == 2
    db.execute("UPDATE effect_hints SET confirmed = 1 WHERE id = ?", (tt[0]["id"],))
    db.commit()
    rebuild_document(db, nd9)
    after = _hints(db, nd9)
    assert [h["id"] for h in after if h["confirmed"]] == [tt[0]["id"]]
    assert sum(h["kind"] == "thay_the" for h in after) == 1  # không nhân đôi gợi ý đã duyệt
    assert sum(h["kind"] == "bai_bo" for h in after) == 2  # hai điều khoản bãi bỏ vẫn ra hai gợi ý


def test_loi_giua_chung_khong_mat_don_vi(db, nd9, monkeypatch):
    n = db.execute("SELECT count(*) FROM units WHERE doc_id = ?", (nd9,)).fetchone()[0]

    def boom(*a, **k):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(ingest, "persist_parsed", boom)
    with pytest.raises(sqlite3.OperationalError):
        rebuild_document(db, nd9)
    assert not db.in_transaction
    assert db.execute("SELECT count(*) FROM units WHERE doc_id = ?", (nd9,)).fetchone()[0] == n
