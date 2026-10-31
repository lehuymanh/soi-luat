"""Agent D: cổng, nạp file trong app, trạng thái, từ điển, hiển thị trang, xuất Word."""

from __future__ import annotations

import socket
import time

import pytest
from docx import Document
from fastapi.testclient import TestClient

import soiluat.app as appmod
from soiluat.cards import Card

H = {"Host": "127.0.0.1:8007"}  # cổng khác 8000: Host guard vẫn nhận


def _card(**extra) -> Card:
    c = Card(
        kind="Quy định liên quan",
        title="Điều 5. Báo cáo",
        sample="",
        duty_text="Doanh nghiệp phải báo cáo định kỳ.",
        duty_addr="15/2020/NĐ-CP · Điều 5 khoản 1",
        sanction_text="",
        sanction_addr="",
        hieu_luc="chua_ro",
        link_status="",
        ocr_unverified=True,
        unit_ids=[1],
        page_from=3,
        so_hieu="15/2020/NĐ-CP",
        file_path="nd15.docx",
        warnings=["Hiệu lực chưa rõ"],
    )
    for k, v in extra.items():  # page_to/notes/intent: trường C thêm, có thể chưa có
        setattr(c, k, v)
    return c


@pytest.fixture
def no_ocr_check(monkeypatch):
    monkeypatch.setattr(appmod, "_ocr_cache", {"ok": True, "langs": ["vie"], "message": ""})


# --- cổng ---


def test_pick_port_skips_busy_port():
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    busy = srv.getsockname()[1]
    try:
        assert appmod._port_busy(busy)
        got = appmod.pick_port(busy, tries=20)
        assert busy < got <= busy + 20
    finally:
        srv.close()


def test_main_reads_env_port(monkeypatch, tmp_path):
    seen = {}
    monkeypatch.setenv("SOILUAT_DATA", str(tmp_path))
    monkeypatch.setattr(appmod.JOBS, "wake", lambda: None)  # không khởi luồng nền thật
    monkeypatch.setenv("SOILUAT_PORT", "8123")
    monkeypatch.setenv("SOILUAT_NO_BROWSER", "1")
    monkeypatch.setattr(appmod, "pick_port", lambda p: seen.setdefault("want", p))
    monkeypatch.setattr(appmod.uvicorn, "run", lambda *a, **k: seen.setdefault("port", k["port"]))
    monkeypatch.setattr(appmod.webbrowser, "open", lambda *a: pytest.fail("không được mở trình duyệt"))
    appmod.main([])
    assert seen == {"want": 8123, "port": 8123}
    seen.clear()
    appmod.main(["--port", "9001"])
    assert seen["port"] == 9001


def test_main_danh_thuc_luong_nen_de_nang_cap_du_lieu(monkeypatch, tmp_path):
    seen = []
    monkeypatch.setenv("SOILUAT_DATA", str(tmp_path))
    monkeypatch.setenv("SOILUAT_NO_BROWSER", "1")
    monkeypatch.setattr(appmod, "pick_port", lambda p: p)
    monkeypatch.setattr(appmod.uvicorn, "run", lambda *a, **k: seen.append("run"))
    monkeypatch.setattr(appmod.JOBS, "wake", lambda: seen.append("wake"))
    appmod.main([])
    assert seen == ["wake", "run"]  # luồng chạy ngay lúc mở app, không đợi file đầu tiên


# --- nạp file ngay trong app (một process) ---

DOC = "Nghị định số 9/2024/NĐ-CP\nĐiều 1. Giá dịch vụ\n1. Cơ sở phải niêm yết giá.\n"


@pytest.fixture
def jobs(tmp_path, monkeypatch):
    from soiluat.jobs import Jobs

    monkeypatch.setenv("SOILUAT_DATA", str(tmp_path))
    j = Jobs()
    monkeypatch.setattr(appmod, "JOBS", j)
    yield j
    j.stop()


def _wait(j, timeout=30):
    """Chờ hàng đợi xong (submit đã xếp item trước khi trả lời nên active=True ngay)."""
    end = time.time() + timeout
    while time.time() < end:
        s = j.snapshot()
        if s["total"] and not s["active"]:
            return s
        time.sleep(0.05)
    raise AssertionError(j.snapshot())


def _states(snap):
    return [(i["name"], i["state"]) for i in snap["items"]]


def _upload(client, *files, **form):
    return client.post("/import/files", files=[("files", (n, c, "application/octet-stream")) for n, c in files], data=form)


def test_import_path_runs_in_process(tmp_path, jobs):
    from soiluat.config import db_path
    from soiluat.db import connect

    src = tmp_path / "kho"
    src.mkdir()
    (src / "a.txt").write_text(DOC, encoding="utf-8")
    (src / "b.xyz").write_text("x", encoding="utf-8")
    client = TestClient(appmod.app)
    r = client.post("/import/path", data={"path": str(src)})
    assert r.status_code == 200 and r.json() == {"ok": True, "queued": 1, "skipped": 1}
    assert _states(_wait(jobs)) == [("a.txt", "du")]
    conn = connect(db_path())
    assert conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0] == 1
    conn.close()
    r = client.post("/import/path", data={"path": str(tmp_path / "khong_co")})
    assert r.status_code == 400 and "Không thấy" in r.json()["error"]


def test_upload_many_files_dedup_and_rename(tmp_path, jobs):
    from soiluat.config import db_path
    from soiluat.db import connect

    client = TestClient(appmod.app)
    r = _upload(client, ("a.txt", DOC.encode()), ("b.txt", (DOC + "2. Thêm.\n").encode()), ("virus.exe", b"MZ"))
    assert r.json() == {"ok": True, "queued": 2, "skipped": 1}
    assert sorted(p.name for p in (tmp_path / "files").iterdir()) == ["a.txt", "b.txt"]  # .exe không được lưu
    assert sorted(_states(_wait(jobs))) == [("a.txt", "du"), ("b.txt", "du")]
    conn = connect(db_path())
    paths = {r[0] for r in conn.execute("SELECT file_path FROM documents")}
    conn.close()
    assert paths == {"files/a.txt", "files/b.txt"}  # lưu tương đối thư mục data: xem trang gốc được
    # cùng tên + cùng nội dung: dùng lại file cũ, không nạp lại
    _upload(client, ("a.txt", DOC.encode()))
    assert _states(_wait(jobs))[-1] == ("a.txt", "khong_doi")
    assert sorted(p.name for p in (tmp_path / "files").iterdir()) == ["a.txt", "b.txt"]
    # cùng tên khác nội dung: thêm "(2)"
    _upload(client, ("a.txt", (DOC + "2. Khác hẳn.\n").encode()))
    _wait(jobs)
    assert (tmp_path / "files" / "a (2).txt").is_file()


def test_upload_name_is_sanitised(tmp_path, jobs):
    client = TestClient(appmod.app)
    _upload(client, ("..\\..\\x:y.txt", DOC.encode()))
    _wait(jobs)
    assert [p.name for p in (tmp_path / "files").iterdir()] == ["x_y.txt"]
    assert appmod._safe_name("") == "tai-lieu"


def test_import_clear_keeps_only_busy(tmp_path, jobs):
    client = TestClient(appmod.app)
    _upload(client, ("a.txt", DOC.encode()))
    _wait(jobs)
    assert client.post("/import/clear").json() == {"ok": True}
    assert jobs.snapshot()["items"] == []


def test_import_requires_csrf(tmp_path, monkeypatch, jobs):
    monkeypatch.delenv("SOILUAT_ALLOW_TEST_HOST", raising=False)
    client = TestClient(appmod.app)
    page = client.get("/", headers=H)
    token = page.cookies.get("soiluat_csrf_8007")
    assert client.post("/import/path", headers=H, data={"path": str(tmp_path)}).status_code == 403
    assert client.post("/import/files", headers=H, files=[("files", ("a.txt", b"x"))]).status_code == 403
    assert client.post("/import/clear", headers=H).status_code == 403
    ok = client.post("/import/files", headers={**H, "X-CSRF-Token": token}, files=[("files", ("a.txt", DOC.encode()))])
    assert ok.status_code == 200 and ok.json()["queued"] == 1


def test_status_endpoint_shape_and_ocr_cache(tmp_path, monkeypatch, jobs):
    import soiluat.importer as imp

    calls = []
    monkeypatch.setattr(imp, "check_ocr", lambda: calls.append(1) or {"ok": True, "langs": ["vie"], "message": ""})
    monkeypatch.setattr(appmod, "_ocr_cache", None)
    client = TestClient(appmod.app)
    st = client.get("/api/status").json()
    assert set(st) == {"docs", "jobs", "mode"} and not calls  # không kèm OCR thì không nạp module OCR
    assert set(st["jobs"]) == {"items", "total", "done", "active", "embed", "migrate"}
    assert set(st["mode"]) == {"mode", "installed", "pending"}
    assert client.get("/api/status", params={"ocr": "1"}).json()["ocr"]["langs"] == ["vie"]
    client.get("/api/status", params={"ocr": "1"})
    assert len(calls) == 1  # nhớ kết quả
    client.get("/api/status", params={"ocr": "lai"})
    assert len(calls) == 2


def test_jobs_page_moved_and_home_has_buttons(tmp_path, monkeypatch):
    monkeypatch.setenv("SOILUAT_DATA", str(tmp_path))
    client = TestClient(appmod.app)
    r = client.get("/jobs", follow_redirects=False)
    assert r.status_code == 307 and r.headers["location"] == "/#import"
    page = client.get("/").text
    assert 'id="btn-import"' in page and 'id="btn-settings"' in page and 'id="composer"' in page
    assert 'id="migrate-line"' in page
    assert "0 văn bản" in page and "Kho chưa có văn bản" in page


def test_main_import_subcommand(monkeypatch):
    import soiluat.importer as imp

    seen = []
    monkeypatch.setattr(imp, "main", lambda argv: seen.append(argv) or 0)
    with pytest.raises(SystemExit) as e:
        appmod.main(["import", "thu_muc", "--ocr"])
    assert e.value.code == 0 and seen == [["thu_muc", "--ocr"]]


def test_mot_tap_duoi_file_chung_cho_app_jobs_va_importer():
    """F10: thêm đuôi file chỉ sửa extract.SUPPORTED_SUFFIXES; ba nơi dùng cùng đúng tập đó, không bản sao."""
    from soiluat import extract, importer, jobs as jobsmod

    assert appmod.SUPPORTED_SUFFIXES is jobsmod.SUPPORTED_SUFFIXES is importer.SUPPORTED_SUFFIXES is extract.SUPPORTED_SUFFIXES


# --- /review/synonyms ---


def test_synonyms_crud_with_csrf(tmp_path, monkeypatch):
    monkeypatch.setenv("SOILUAT_DATA", str(tmp_path))
    monkeypatch.delenv("SOILUAT_ALLOW_TEST_HOST", raising=False)
    from soiluat.config import db_path
    from soiluat.db import connect

    client = TestClient(appmod.app)
    page = client.get("/review/synonyms", headers=H)
    assert page.status_code == 200 and "Từ điển" in page.text
    token = page.cookies.get("soiluat_csrf_8007")
    form = {"term": "XYZT", "alt": "cụm thử nghiệm riêng", "kind": "viet_tat"}
    assert client.post("/synonyms", headers=H, data=form, follow_redirects=False).status_code == 403
    r = client.post("/synonyms", headers=H, data={**form, "csrf_token": token}, follow_redirects=False)
    assert r.status_code == 303

    def row():
        conn = connect(db_path())
        x = conn.execute("SELECT id, approved, kind FROM synonyms WHERE term = 'XYZT'").fetchone()
        conn.close()
        return x

    sid = row()["id"]
    assert row()["approved"] == 1 and row()["kind"] == "viet_tat"
    assert "cụm thử nghiệm riêng" in client.get("/review/synonyms", headers=H).text
    assert client.post(f"/synonyms/{sid}/approve", headers=H, data={"approved": "0"}, follow_redirects=False).status_code == 403
    client.post(f"/synonyms/{sid}/approve", headers=H, data={"approved": "0", "csrf_token": token}, follow_redirects=False)
    assert row()["approved"] == 0
    client.post(f"/synonyms/{sid}/approve", headers=H, data={"approved": "1", "csrf_token": token}, follow_redirects=False)
    assert row()["approved"] == 1
    assert client.post(f"/synonyms/{sid}/delete", headers=H, follow_redirects=False).status_code == 403
    client.post(f"/synonyms/{sid}/delete", headers=H, data={"csrf_token": token}, follow_redirects=False)
    assert row() is None


def test_home_links_synonyms(tmp_path, monkeypatch):
    monkeypatch.setenv("SOILUAT_DATA", str(tmp_path))
    assert "/review/synonyms" in TestClient(appmod.app).get("/").text


# --- hiển thị ---


def test_results_card_shows_pages_notes_intent():
    c = _card(page_to=4, notes=["gc1", "gc2", "gc3", "gc4"], intent="muc_phat")
    html = appmod.TEMPLATES.env.get_template("_results.html").render(
        cards=[c], n={"n1": 0, "n2": 0, "n3": 0, "n4": 1}, dates={1: {"ngay_ban_hanh": "2020-02-01", "ngay_hieu_luc": "2026-03-01"}},
        csrf_token="t", q="x",
    )
    assert "Trang 3–4" in html
    assert "Ý định: mức phạt" in html
    assert "gc3" in html and "gc4" not in html
    assert "ban hành 01/02/2020" in html and "hiệu lực từ 01/03/2026" in html


def test_results_card_without_new_fields():
    from types import SimpleNamespace

    # Card kiểu 0.7: không có page_to/notes/intent
    c = SimpleNamespace(**{k: v for k, v in vars(_card()).items() if k not in ("page_to", "notes", "intent")})
    html = appmod.TEMPLATES.env.get_template("_results.html").render(
        cards=[c], n={"n1": 0, "n2": 0, "n3": 0, "n4": 1}, dates={}, csrf_token="t", q="x"
    )
    assert "Trang 3" in html


def test_unit_page_lists_notes_and_dates(tmp_path, monkeypatch, db, sample_doc):
    monkeypatch.setenv("SOILUAT_DATA", str(tmp_path))
    dieu = db.execute("SELECT * FROM units WHERE level = 'dieu' ORDER BY id LIMIT 1").fetchone()
    child = db.execute("SELECT id FROM units WHERE parent_id = ? LIMIT 1", (dieu["id"],)).fetchone()
    parent = child["id"] if child else dieu["id"]
    db.execute(
        "INSERT INTO units(doc_id, parent_id, path, level, raw_text, normalized_text, search_text, "
        "extraction_method, verification_status, page_from, page_to) "
        "VALUES (?, ?, 'GC1', 'ghi_chu', 'Chú thích kiểm thử D', '', '', 'docx', 'auto', 2, 2)",
        (dieu["doc_id"], parent),
    )
    db.execute("UPDATE documents SET ngay_ban_hanh = '2020-01-15', ngay_hieu_luc = '2020-03-01'")
    db.commit()
    r = TestClient(appmod.app).get(f"/unit/{dieu['id']}")
    assert r.status_code == 200
    assert "Chú thích kiểm thử D" in r.text
    assert "15/01/2020" in r.text and "01/03/2020" in r.text
    docs = TestClient(appmod.app).get("/review/docs")
    assert docs.status_code == 200 and "2020-01-15" in docs.text


# --- xuất Word ---


def test_export_has_page_file_notes_warnings(db, sample_doc, tmp_path):
    from soiluat.export_word import export_units

    dieu = db.execute("SELECT id, doc_id FROM units WHERE path = 'D5'").fetchone()
    db.execute("UPDATE units SET page_from = 3, page_to = 5 WHERE id = ?", (dieu["id"],))
    db.execute(
        "INSERT INTO units(doc_id, parent_id, path, level, raw_text, normalized_text, search_text, "
        "extraction_method, verification_status, page_from, page_to) "
        "VALUES (?, ?, 'GC1', 'ghi_chu', 'Ghi chú cuối trang', '', '', 'docx', 'auto', 5, 5)",
        (dieu["doc_id"], dieu["id"]),
    )
    db.execute(
        "INSERT INTO pages(doc_id, page_no, kind, extraction_method, ocr_status, verification_status) "
        "VALUES (?, 4, 'scan', 'ocr', 'chua_doi_chieu', 'auto')", (dieu["doc_id"],)
    )
    db.commit()
    dest = tmp_path / "out.docx"
    export_units(db, [dieu["id"]], dest)
    text = "\n".join(p.text for p in Document(str(dest)).paragraphs)
    assert "Trang 3–5" in text
    assert "nd15.txt" in text
    assert "Điều 5 Nghị định 15/2020/NĐ-CP" in text
    assert "Tổ chức tín dụng phải báo cáo định kỳ" in text
    assert "Ghi chú cuối trang" in text
    assert "OCR chưa xác minh" in text
    assert "Hiệu lực chưa rõ" in text and "chua_ro" not in text


def test_f1_hoi_dap_khong_cho_5_giay_nhat_ky_khi_dang_nap_giu_khoa_ghi(tmp_path, monkeypatch, sample_doc):
    """F1: nhật ký truy vấn chỉ là một dòng có thể bỏ; khoá ghi bị giữ thì bỏ ngay (không chờ busy_timeout 5 s của kết nối).
    Kết quả vẫn trả đủ."""
    from soiluat.db import connect

    monkeypatch.setenv("SOILUAT_DATA", str(tmp_path))
    holder = connect(tmp_path / "soiluat.db")
    holder.execute("BEGIN IMMEDIATE")  # luồng nạp đang giữ khoá ghi
    try:
        t0 = time.monotonic()
        ctx = appmod._search_ctx("báo cáo định kỳ", "", "", "")
        took = time.monotonic() - t0
    finally:
        holder.rollback()
        holder.close()
    assert ctx["items"] and took < 2.0, took
    conn = connect(tmp_path / "soiluat.db")
    assert conn.execute("SELECT COUNT(*) FROM query_log").fetchone()[0] == 0  # dòng nhật ký đã bị bỏ
    conn.close()


def test_sec5_ten_file_dai_khong_lam_hong_ca_dot_nap_va_khong_de_lai_tep_tam(tmp_path, jobs):
    """SEC-5: tên file quá dài làm /import/files trả 500, bỏ cả lô (file ngắn đã lưu mà không xếp hàng) và sót .part."""
    client = TestClient(appmod.app)
    r = _upload(client, ("ngan.txt", DOC.encode()), ("Quyết định " + "x" * 260 + ".txt", DOC.encode() + b"\n3. Khoan khac.\n"))
    assert r.status_code == 200 and r.json()["queued"] == 2
    files = tmp_path / "files"
    assert not list(files.glob(".*.part"))
    assert all(len(p.name) <= 120 for p in files.iterdir())


def test_sec5_loi_khi_chep_file_tai_len_xoa_tep_tam(tmp_path, monkeypatch):
    """SEC-5: lỗi giữa chừng khi chép (đĩa đầy, tên quá dài) không để lại .part."""
    import io

    from starlette.datastructures import UploadFile

    def hong(*a, **k):
        raise OSError("disk full")

    monkeypatch.setattr(appmod.shutil, "copyfileobj", hong)
    with pytest.raises(OSError):
        appmod._store_upload(UploadFile(io.BytesIO(b"x"), filename="a.txt"), tmp_path / "files")
    assert list((tmp_path / "files").iterdir()) == []
