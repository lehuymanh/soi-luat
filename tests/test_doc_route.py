"""P1 R2a: route /doc thay /unit (trình đọc toàn văn, mở tại đúng đoạn)."""

from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from fastapi.testclient import TestClient


def _setup(tmp_path, monkeypatch):
    monkeypatch.setenv("SOILUAT_DATA", str(tmp_path))
    from soiluat.app import app
    from soiluat.config import db_path
    from soiluat.db import connect, init_schema
    from soiluat.ingest import ingest_path

    conn = connect(db_path())
    init_schema(conn)
    dest = tmp_path / "nd15.txt"
    dest.write_text((Path(__file__).parent / "fixtures" / "nd15.txt").read_text(encoding="utf-8"), encoding="utf-8")
    doc_id = ingest_path(conn, dest, tmp_path)
    k = conn.execute("SELECT id, path FROM units WHERE doc_id = ? AND path = 'D5.K1'", (doc_id,)).fetchone()
    conn.close()
    return TestClient(app), doc_id, k["id"], k["path"]


def _db():
    from soiluat.config import db_path
    from soiluat.db import connect

    return connect(db_path())


def test_unit_chuyen_sang_doc(tmp_path, monkeypatch):
    c, doc_id, uid, path = _setup(tmp_path, monkeypatch)
    r = c.get(f"/unit/{uid}", follow_redirects=False)
    assert r.status_code == 303
    loc = urlsplit(r.headers["location"])
    assert loc.path == f"/doc/{doc_id}" and loc.fragment == f"u{uid}"
    assert parse_qs(loc.query) == {"path": [path], "u": [str(uid)]}
    assert c.get("/unit/999999", follow_redirects=False).status_code == 404


def test_doc_khong_co_404(tmp_path, monkeypatch):
    c, *_ = _setup(tmp_path, monkeypatch)
    r = c.get("/doc/999999")
    assert r.status_code == 404 and "Không tìm thấy văn bản" in r.text


def test_doc_trang_day_du(tmp_path, monkeypatch):
    c, doc_id, uid, path = _setup(tmp_path, monkeypatch)
    r = c.get(f"/doc/{doc_id}", params={"path": path, "q": "báo cáo định kỳ"})
    assert r.status_code == 200
    t = r.text
    assert t.count("<h1") == 1
    assert f'id="u{uid}"' in t and 'class="u sel"' in t
    assert "Khoản 1 Điều 5 Nghị định 15/2020/NĐ-CP" in t  # trích dẫn
    assert '<mark class="m">báo</mark>' in t
    assert "Nguyên văn trang 1" in t  # .txt không có ảnh trang
    assert f"/review/docs#d{doc_id}" in t
    assert "/static/reader.js" in t


def test_doc_manh_cho_htmx(tmp_path, monkeypatch):
    c, doc_id, uid, _ = _setup(tmp_path, monkeypatch)
    r = c.get(f"/doc/{doc_id}", params={"u": uid}, headers={"HX-Request": "true"})
    assert r.status_code == 200
    assert "<html" not in r.text and f'id="u{uid}"' in r.text
    assert "<h1" not in r.text  # trang hỏi đáp đã có h1


def test_doc_khong_ghi_query_log(tmp_path, monkeypatch):
    c, doc_id, uid, path = _setup(tmp_path, monkeypatch)
    c.get("/", params={"q": "bao cao"})
    conn = _db()
    before = [tuple(r) for r in conn.execute("SELECT * FROM query_log ORDER BY id")]
    conn.close()
    assert c.get(f"/unit/{uid}").status_code == 200  # theo chuyển hướng sang /doc
    conn = _db()
    after = [tuple(r) for r in conn.execute("SELECT * FROM query_log ORDER BY id")]
    conn.close()
    assert before and after == before


def test_doc_co_anh_trang_thi_khong_chep_nguyen_van(tmp_path, monkeypatch):
    from soiluat.pageimg import _png

    c, doc_id, uid, _ = _setup(tmp_path, monkeypatch)
    (tmp_path / "anh.png").write_bytes(_png(b"\xff\xff\xff", 1, 1, 3))
    conn = _db()
    conn.execute("UPDATE documents SET file_path = 'anh.png' WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()
    r = c.get(f"/doc/{doc_id}", params={"u": uid})
    assert r.status_code == 200 and "Nguyên văn trang" not in r.text
