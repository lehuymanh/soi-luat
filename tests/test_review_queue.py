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


def test_review_ocr_page_rebuilds(tmp_path, monkeypatch):
    client, _, _, page_id = _client(tmp_path, monkeypatch)
    from soiluat.config import db_path
    from soiluat.db import connect
    from soiluat.rebuild import set_page_reviewed

    conn = connect(db_path())
    new = "Điều 99. Văn bản đã sửa unique_review_token\n1. Phải đối chiếu."
    set_page_reviewed(conn, page_id, new)
    conn.close()
    found = client.get("/", params={"q": "unique_review_token"})
    assert found.status_code == 200
    assert "unique_review_token" in found.text or "Điều 99" in found.text


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
