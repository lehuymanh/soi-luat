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
    assert f"/review/docs?id={doc_id}" in t  # chỉ mở một văn bản, không tải cả trang Văn bản trong kho
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
    conn = _db()
    sha = conn.execute("SELECT sha256 FROM documents WHERE id = ?", (doc_id,)).fetchone()[0]
    conn.close()
    assert 'id="tab-orig"' in t and f'src="/page/{doc_id}/1?v={sha[:8]}"' in t  # nạp lại cùng đường dẫn, nội dung đổi: URL ảnh đổi theo
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


def _pdf_nhieu_trang(tmp_path, name, n):
    from PIL import Image

    pages = [Image.new("RGB", (300, 420), "white") for _ in range(n)]
    pages[0].save(tmp_path / name, save_all=True, append_images=pages[1:])


def test_ban_goc_van_ban_tach_tu_tep_lon_dung_so_trang_goc(tmp_path, monkeypatch):
    """Văn bản thứ hai của một PDF có page_no 4..5: chú thích 'Trang 4' không kèm '/ tổng', mở không chọn đơn vị thì cuộn tới trang 4."""
    c, doc_id, uid, _ = _setup(tmp_path, monkeypatch)
    _pdf_nhieu_trang(tmp_path, "hai.pdf", 5)
    _doi_tep(doc_id, "hai.pdf")
    conn = _db()
    conn.execute("UPDATE pages SET page_no = 4 WHERE doc_id = ?", (doc_id,))
    conn.execute("INSERT INTO pages(doc_id, page_no, kind, extraction_method, ocr_status, verification_status) "
                 "VALUES (?, 5, 'text', 'pdf_text', 'khong_can', 'auto')", (doc_id,))
    conn.commit()
    conn.close()
    t = c.get(f"/doc/{doc_id}").text
    assert "<figcaption>Trang 4</figcaption>" in t and "<figcaption>Trang 5</figcaption>" in t
    assert "Trang 5 / 2" not in t and "Trang 4 / 2" not in t
    assert 'data-start="4"' in t


def test_id_vuot_so_nguyen_sqlite_tra_404_khong_phai_500(tmp_path, monkeypatch):
    """FastAPI nhận int lớn tuỳ ý; sqlite báo OverflowError khi id > 2**63-1 (gõ tay vào URL)."""
    c, doc_id, *_ = _setup(tmp_path, monkeypatch)
    c = TestClient(c.app, raise_server_exceptions=False)
    big = 99999999999999999999
    for url in (f"/doc/{big}", f"/doc/{doc_id}?u={big}", f"/unit/{big}", f"/page/{big}/1"):
        assert c.get(url).status_code == 404, url
    assert c.get(f"/doc/{doc_id}").status_code == 200


def test_sua_so_hieu_chi_mo_mot_van_ban(tmp_path, monkeypatch):
    from soiluat.ingest import ingest_path

    c, doc_id, *_ = _setup(tmp_path, monkeypatch)
    conn = _db()
    (tmp_path / "khac.txt").write_text("Nghị định số 9/2021/NĐ-CP\nĐiều 1. Phạm vi\n1. Nội dung.\n", encoding="utf-8")
    khac = ingest_path(conn, tmp_path / "khac.txt", tmp_path)
    conn.close()
    one = c.get("/review/docs", params={"id": doc_id}).text
    assert f'id="d{doc_id}"' in one and f'id="d{khac}"' not in one and 'href="/review/docs"' in one  # kèm đường về danh sách đủ
    both = c.get("/review/docs").text
    assert f'id="d{doc_id}"' in both and f'id="d{khac}"' in both
    assert f'id="d{doc_id}"' not in c.get("/review/docs", params={"id": khac}).text


# --- soát K2: pdfium không an toàn khi nhiều luồng dùng; tab Bản gốc xin nhiều trang cùng lúc ---
PDFIUM_THREADS = r'''
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image, ImageDraw
from soiluat import ocr
from soiluat.pageimg import render_pdf_page

pdf = Path(sys.argv[1]) / "n.pdf"
pages = []
for n in range(40):
    im = Image.new("RGB", (300, 420), "white")
    ImageDraw.Draw(im).rectangle((10 + n * 5, 10, 40 + n * 5, 400), fill="black")
    pages.append(im)
pages[0].save(pdf, save_all=True, append_images=pages[1:])
nos = list(range(1, 41))
serial = {n: render_pdf_page(pdf, n) for n in nos}
serial_ocr = {n: img.tobytes() for n, img in ocr._page_images(pdf, nos)}  # OCR dựng trang trong luồng nạp, cùng lúc với /page
with ThreadPoolExecutor(6) as ex:
    job = ex.submit(lambda: {n: img.tobytes() for n, img in ocr._page_images(pdf, nos)})
    got = list(ex.map(lambda n: (n, render_pdf_page(pdf, n)), [(i % 40) + 1 for i in range(120)]))
assert all(png == serial[n] for n, png in got), "ảnh trang lệch khi chạy song song"
assert job.result() == serial_ocr, "OCR dựng trang lệch khi chạy song song"
'''


def test_render_trang_pdf_song_song_giong_tuan_tu(tmp_path):
    """6 luồng vẽ trang cùng lúc phải ra đúng ảnh như vẽ tuần tự. Chạy ở tiến trình riêng vì khi hỏng pdfium làm chết cả tiến trình
    (SIGSEGV/SIGABRT) hoặc báo PdfiumError; trên mã chưa có khoá thì tái hiện 6/6 lần."""
    import subprocess
    import sys

    src = Path(__file__).parents[1] / "src"
    r = subprocess.run([sys.executable, "-I", "-c", f"import sys; sys.path.insert(0, {str(src)!r}); sys.argv = ['x', {str(tmp_path)!r}]\n" + PDFIUM_THREADS],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, f"exit {r.returncode}: {r.stderr[-500:]}"


def test_tep_mat_chi_dung_duong_dan_cu_khong_hen_nap_lai_tu_cho_moi(tmp_path, monkeypatch):
    """Nạp lại tệp từ chỗ mới bị bỏ qua vì trùng sha256 (documents.file_path giữ nguyên), nên lời khuyên là đưa tệp về đúng đường dẫn cũ."""
    c, doc_id, uid, _ = _setup(tmp_path, monkeypatch)
    _doi_tep(doc_id, "anh.png")  # tệp không tồn tại
    t = c.get(f"/doc/{doc_id}", params={"u": uid}).text
    assert f"<code>{tmp_path / 'anh.png'}</code>" in t and "đúng đường dẫn này" in t
    js = (Path(__file__).parents[1] / "src" / "soiluat" / "static" / "reader.js").read_text(encoding="utf-8")
    assert "hãy nạp lại tệp từ chỗ mới" not in js and "đường dẫn" in js.split("Vẫn chưa thấy tệp")[1][:200]
