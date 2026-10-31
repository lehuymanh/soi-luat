import re
from pathlib import Path

from fastapi.testclient import TestClient


def _client(tmp_path, monkeypatch):
    monkeypatch.setenv("SOILUAT_DATA", str(tmp_path))
    from soiluat.app import app
    from soiluat.config import db_path
    from soiluat.db import connect, init_schema
    from soiluat.ingest import ingest_path

    conn = connect(db_path())
    init_schema(conn)
    src = Path(__file__).parent / "fixtures" / "nd15.txt"
    dest = tmp_path / "nd15.txt"
    dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    doc_id = ingest_path(conn, dest, tmp_path)
    uid = conn.execute(
        "SELECT id FROM units WHERE doc_id = ? LIMIT 1", (doc_id,)
    ).fetchone()["id"]
    page_id = conn.execute(
        "SELECT id FROM pages WHERE doc_id = ?", (doc_id,)
    ).fetchone()["id"]
    conn.close()
    return TestClient(app), doc_id, uid, page_id


def test_review_docs_hieu_luc(tmp_path, monkeypatch):
    client, doc_id, uid, _ = _client(tmp_path, monkeypatch)
    r = client.get("/review/docs")
    assert r.status_code == 200
    assert "nd15" in r.text
    assert "đã duyệt cấu trúc" not in r.text
    r3 = client.post(
        f"/docs/{doc_id}/hieu-luc",
        data={"hieu_luc": "con"},
        follow_redirects=True,
    )
    assert r3.status_code == 200
    src = client.get(f"/unit/{uid}")
    assert src.status_code == 200
    assert "nd15" in src.text
    assert "15/2020" in src.text
    r4 = client.post(
        f"/docs/{doc_id}/so-hieu",
        data={"so_hieu": "15/2020/NĐ-CP"},
        follow_redirects=True,
    )
    assert r4.status_code == 200
    assert "15/2020" in r4.text


def test_missed_queries_and_htmx_fragment(tmp_path, monkeypatch):
    client, _, _, _ = _client(tmp_path, monkeypatch)
    client.get("/", params={"q": "xyzkhongco123"})
    missed = client.get("/missed")
    assert missed.status_code == 200
    assert "xyzkhongco123" in missed.text
    frag = client.get(
        "/", params={"q": "bao cao"}, headers={"HX-Request": "true"}
    )
    assert frag.status_code == 200
    assert "<!doctype" not in frag.text.lower()
    assert "báo cáo" in frag.text.lower() or "Điều" in frag.text


def test_filter_hieu_luc_http(tmp_path, monkeypatch):
    client, doc_id, _, _ = _client(tmp_path, monkeypatch)
    client.post(f"/docs/{doc_id}/hieu-luc", data={"hieu_luc": "con"})
    empty = client.get("/", params={"q": "bao cao", "hieu_luc": "het"})
    assert "Không còn kết quả sau khi lọc" in empty.text
    hit = client.get("/", params={"q": "bao cao", "hieu_luc": "con"})
    assert "Không tìm thấy" not in hit.text


def test_empty_kho_message(tmp_path, monkeypatch):
    monkeypatch.setenv("SOILUAT_DATA", str(tmp_path))
    from soiluat.app import app

    client = TestClient(app)
    r = client.get("/", params={"q": "báo cáo định kì"})
    assert r.status_code == 200
    assert "Kho chưa có văn bản" in r.text
    assert "Không tìm thấy quy định" not in r.text

def test_backup_http(tmp_path, monkeypatch):
    client, _, _, _ = _client(tmp_path, monkeypatch)
    r = client.post("/backup")
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert (tmp_path / "backup" / "soiluat.db").exists()


def _nhieu(tmp_path, monkeypatch, n=300):
    """Kho có n+1 văn bản và n liên kết chờ duyệt (đơn vị chèn thẳng, đủ cột bắt buộc)."""
    client, doc_id, _, _ = _client(tmp_path, monkeypatch)
    from soiluat.config import db_path
    from soiluat.db import connect

    conn = connect(db_path())
    conn.executemany(
        "INSERT INTO documents(file_path, sha256, source_status, extraction_method) VALUES (?, ?, 'ok', 'docx')",
        [(f"v{i}.docx", f"h{i}") for i in range(n)],
    )
    conn.executemany(
        "INSERT INTO units(doc_id, path, level, raw_text, normalized_text, search_text, extraction_method, verification_status) "
        "VALUES (?, ?, 'khoan', 'x', 'x', 'x', 'docx', 'chua')",
        [(doc_id, f"X{i}") for i in range(n + 1)],
    )
    ids = [r[0] for r in conn.execute("SELECT id FROM units WHERE path LIKE 'X%' ORDER BY id")]
    conn.executemany("INSERT INTO links(sanction_unit, duty_unit, method) VALUES (?, ?, 'goi_y')", list(zip(ids, ids[1:])))
    conn.commit()
    conn.close()
    return client, doc_id


def test_f2_duyet_lien_ket_chi_hien_mot_trang_va_noi_con_bao_nhieu(tmp_path, monkeypatch):
    """F2: hàng chờ hơn 300 liên kết thì /review chỉ dựng 50 dòng, kèm số còn lại; không dựng cả hàng chờ."""
    client, _ = _nhieu(tmp_path, monkeypatch)
    from soiluat.config import db_path
    from soiluat.db import connect

    conn = connect(db_path())
    total = conn.execute("SELECT COUNT(*) FROM links WHERE confirmed = 0").fetchone()[0]
    conn.close()
    assert total > 300
    html = client.get("/review").text
    assert html.count('class="row"') == 50
    assert f"Còn {total - 50} liên kết nữa" in html


def test_f2_van_ban_trong_kho_phan_trang_va_cat_danh_sach_dieu(tmp_path, monkeypatch):
    """F2: 301 văn bản thì /review/docs dựng 50 văn bản mỗi trang (?trang=), mỗi văn bản tối đa 5 đơn vị."""
    client, doc_id = _nhieu(tmp_path, monkeypatch)
    first = client.get("/review/docs").text
    assert first.count('class="doc"') == 50
    assert first.count('class="unit"') <= 5 * 50
    seen = set(re.findall(r'class="doc" id="d(\d+)"', first))
    second = client.get("/review/docs", params={"trang": 2}).text
    assert second.count('class="doc"') == 50 and not seen & set(re.findall(r'class="doc" id="d(\d+)"', second))
    assert client.get("/review/docs", params={"trang": 7}).text.count('class="doc"') == 1
    assert client.get("/review/docs", params={"trang": 999}).text.count('class="doc"') == 1  # quá cuối thì về trang cuối
    assert f'id="d{doc_id}"' in client.get("/review/docs", params={"id": doc_id}).text


def test_f2_luu_hieu_luc_va_so_hieu_quay_ve_dung_van_ban(tmp_path, monkeypatch):
    """F2: lưu xong thì về /review/docs?id=N (một văn bản), không tải lại cả kho."""
    client, doc_id, _, _ = _client(tmp_path, monkeypatch)
    for path, data in ((f"/docs/{doc_id}/hieu-luc", {"hieu_luc": "con"}), (f"/docs/{doc_id}/so-hieu", {"so_hieu": "15/2020/NĐ-CP"})):
        r = client.post(path, data=data, follow_redirects=False)
        assert r.status_code == 303 and r.headers["location"] == f"/review/docs?id={doc_id}"


def _rows(sql, *args):
    from soiluat.config import db_path
    from soiluat.db import connect

    conn = connect(db_path())
    try:
        return [tuple(r) for r in conn.execute(sql, args)]
    finally:
        conn.close()


def test_f7_moi_route_post_deu_goi_check_csrf():
    """F7: route ghi mới thiếu `_check_csrf` thì test này đỏ (các test CSRF khác chỉ kể tên từng route). Kiểm theo mã nguồn:
    gửi form rỗng không phân biệt được 403 với 422 vì có route kiểm tham số trước token."""
    import inspect

    from soiluat.app import app

    posts = [r for r in app.routes if "POST" in getattr(r, "methods", ())]
    assert len(posts) >= 20
    thieu = [r.path for r in posts if "_check_csrf(" not in inspect.getsource(r.endpoint)]
    assert thieu == []


def test_f7_duyet_lien_ket_dung_thi_roi_hang_cho_sai_thi_xoa(tmp_path, monkeypatch):
    client, _ = _nhieu(tmp_path, monkeypatch, n=2)
    dung, sai = [r[0] for r in _rows(
        "SELECT l.id FROM links l JOIN units u ON u.id = l.sanction_unit WHERE u.path LIKE 'X%' ORDER BY l.id")]
    assert f"/links/{dung}/confirm" in client.get("/review").text
    r = client.post(f"/links/{dung}/confirm", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/review"
    (confirmed, at), = _rows("SELECT confirmed, reviewed_at FROM links WHERE id = ?", dung)
    assert confirmed == 1 and at
    r = client.post(f"/links/{sai}/reject", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/review"
    assert _rows("SELECT id FROM links WHERE id IN (?, ?)", dung, sai) == [(dung,)]
    page = client.get("/review").text
    assert f"/links/{dung}/" not in page and f"/links/{sai}/" not in page  # đã duyệt hoặc đã xoá thì rời hàng chờ


def test_f7_duyet_goi_y_hieu_luc_dung_thi_roi_hang_cho_sai_thi_xoa(tmp_path, monkeypatch):
    client, doc_id, _, _ = _client(tmp_path, monkeypatch)
    from soiluat.config import db_path
    from soiluat.db import connect

    conn = connect(db_path())
    conn.execute("DELETE FROM effect_hints")
    conn.executemany(
        "INSERT INTO effect_hints(source_doc_id, target_so_hieu, kind, snippet) VALUES (?, ?, 'thay_the', ?)",
        [(doc_id, "1/2000/NĐ-CP", "gợi ý đúng"), (doc_id, "2/2000/NĐ-CP", "gợi ý sai")],
    )
    conn.commit()
    conn.close()
    dung, sai = [r[0] for r in _rows("SELECT id FROM effect_hints ORDER BY id")]
    assert "gợi ý đúng" in client.get("/review/hints").text
    r = client.post(f"/hints/{dung}/confirm", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/review/hints"
    (confirmed, at), = _rows("SELECT confirmed, reviewed_at FROM effect_hints WHERE id = ?", dung)
    assert confirmed == 1 and at
    r = client.post(f"/hints/{sai}/reject", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/review/hints"
    assert _rows("SELECT id FROM effect_hints") == [(dung,)]
    page = client.get("/review/hints").text
    assert "gợi ý đúng" not in page and "gợi ý sai" not in page  # trang chỉ liệt kê gợi ý chưa duyệt


def test_f7_luat_chu_the_them_roi_xoa(tmp_path, monkeypatch):
    client, _, _, _ = _client(tmp_path, monkeypatch)
    r = client.post("/subjects", data={"phrase": " doanh nghiệp nhỏ ", "kind": "ha_uu_tien"}, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/review/subjects"
    client.post("/subjects", data={"phrase": "kiểu lạ", "kind": "khong-co"})  # kind lạ về uu_tien
    client.post("/subjects", data={"phrase": "   ", "kind": "uu_tien"})  # rỗng: bỏ qua
    assert _rows("SELECT phrase, kind, approved FROM subject_rules ORDER BY id") == [
        ("doanh nghiệp nhỏ", "ha_uu_tien", 1), ("kiểu lạ", "uu_tien", 1)]
    assert "doanh nghiệp nhỏ" in client.get("/review/subjects").text
    rid = _rows("SELECT id FROM subject_rules WHERE phrase = 'doanh nghiệp nhỏ'")[0][0]
    r = client.post(f"/subjects/{rid}/delete", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/review/subjects"
    assert _rows("SELECT phrase FROM subject_rules") == [("kiểu lạ",)]
