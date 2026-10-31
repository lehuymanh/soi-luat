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


def test_doc_ngay_in_dd_mm_yyyy(tmp_path, monkeypatch):
    c, doc_id, uid, _ = _setup(tmp_path, monkeypatch)
    conn = _db()
    conn.execute("UPDATE documents SET ngay_ban_hanh = '2020-01-15', ngay_hieu_luc = NULL WHERE id = ?", (doc_id,))
    conn.commit()
    t = c.get(f"/doc/{doc_id}", params={"u": uid}).text
    assert "ban hành 15/01/2020" in t and "hiệu lực từ" not in t
    conn.execute("UPDATE documents SET ngay_hieu_luc = '2020-03-01' WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()
    assert "hiệu lực từ 01/03/2020" in c.get(f"/doc/{doc_id}", params={"u": uid}).text


# --- R3: tab Bản gốc, cuộn liên tục các trang ---
def _doi_tep(doc_id, name):
    conn = _db()
    conn.execute("UPDATE documents SET file_path = ? WHERE id = ?", (name, doc_id))
    conn.commit()
    conn.close()


def test_ban_goc_an_voi_txt(tmp_path, monkeypatch):
    c, doc_id, uid, _ = _setup(tmp_path, monkeypatch)
    t = c.get(f"/doc/{doc_id}", params={"u": uid}).text
    assert 'id="tab-orig"' not in t and "/page/" not in t


def test_ban_goc_png_va_tep_mat(tmp_path, monkeypatch):
    from soiluat.pageimg import _png

    c, doc_id, uid, _ = _setup(tmp_path, monkeypatch)
    (tmp_path / "anh.png").write_bytes(_png(b"\xff\xff\xff", 1, 1, 3))
    _doi_tep(doc_id, "anh.png")
    t = c.get(f"/doc/{doc_id}", params={"u": uid}).text
    assert 'id="tab-orig"' in t and f'src="/page/{doc_id}/1"' in t
    assert c.get(f"/page/{doc_id}/1").status_code == 200
    assert c.get(f"/page/{doc_id}/2").status_code == 404  # ảnh đơn chỉ có trang 1
    (tmp_path / "anh.png").unlink()
    t = c.get(f"/doc/{doc_id}", params={"u": uid}).text
    assert 'id="tab-orig"' in t and "/page/" not in t
    assert 'role="alert"' in t and "Không mở được ảnh trang" in t and "data-retry" in t


def test_ban_goc_pdf_cuon_lien_tuc(tmp_path, monkeypatch):
    from PIL import Image

    c, doc_id, uid, _ = _setup(tmp_path, monkeypatch)
    pages = [Image.new("RGB", (300, 420), "white") for _ in range(2)]
    pages[0].save(tmp_path / "v.pdf", save_all=True, append_images=pages[1:])
    _doi_tep(doc_id, "v.pdf")
    conn = _db()
    conn.execute(
        "INSERT INTO pages(doc_id, page_no, kind, extraction_method, ocr_status, verification_status) "
        "VALUES (?, 2, 'text', 'pdf_text', 'khong_can', 'auto')", (doc_id,))
    conn.commit()
    conn.close()
    t = c.get(f"/doc/{doc_id}", params={"u": uid, "page": 2}).text
    assert 'id="p1"' in t and 'id="p2"' in t and 'data-start="2"' in t
    r = c.get(f"/page/{doc_id}/2")
    assert r.status_code == 200 and r.content[:8] == b"\x89PNG\r\n\x1a\n"


# --- R2b: mở trình đọc ngay trong trang hỏi đáp ---
def test_unit_chuyen_tiep_q(tmp_path, monkeypatch):
    c, doc_id, uid, path = _setup(tmp_path, monkeypatch)
    loc = urlsplit(c.get(f"/unit/{uid}", params={"q": "báo cáo"}, follow_redirects=False).headers["location"])
    assert parse_qs(loc.query) == {"path": [path], "u": [str(uid)], "q": ["báo cáo"]}


def test_trang_hoi_dap_co_trinh_doc(tmp_path, monkeypatch):
    c, *_ = _setup(tmp_path, monkeypatch)
    t = c.get("/", params={"q": "báo cáo định kỳ"}).text
    assert 'id="reader"' in t and "/static/reader.js" in t
    assert "data-doc" in t and "/doc/" in t and "q=b%C3%A1o" in t
