"""Hàng đợi nạp + nhúng nền trong app (soiluat.jobs)."""

from __future__ import annotations

import sqlite3
import time

import pytest

from soiluat import semantic
from soiluat.ingest import ingest_path
from soiluat.jobs import Jobs

np = pytest.importorskip("numpy")

DOC = "Nghị định số 9/2024/NĐ-CP\nĐiều 1. Giá dịch vụ\n1. Cơ sở phải niêm yết giá.\nĐiều 2. Thuế\n1. Nộp thuế đúng hạn.\n"


class FakeEncoder:
    np = np

    def encode(self, texts, batch=8):
        v = np.array([[float("giá" in t.lower()), float("thuế" in t.lower()), 1e-3] for t in texts], np.float32)
        return v / np.linalg.norm(v, axis=1, keepdims=True)


@pytest.fixture
def advance(db, tmp_path, monkeypatch):
    """Kho tmp_path/soiluat.db ở chế độ Advance với bộ mã hoá giả (không cần mô hình thật)."""
    monkeypatch.setenv("SOILUAT_DATA", str(tmp_path))
    monkeypatch.delenv("SOILUAT_SEMANTIC", raising=False)
    monkeypatch.setattr(semantic, "_ENC", FakeEncoder())
    monkeypatch.setattr(semantic, "_ENC_TRIED", True)
    monkeypatch.setattr(semantic, "model_installed", lambda: True)
    semantic.set_mode(db, "advance")
    j = Jobs()
    yield j
    j.stop()


def _until(cond, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return
        time.sleep(0.05)
    raise AssertionError("hết giờ chờ")


def _vectors(db):
    return db.execute("SELECT COUNT(*) FROM unit_vectors").fetchone()[0]


def test_import_then_embed_in_advance(advance, db, tmp_path):
    f = tmp_path / "nd9.txt"
    f.write_text(DOC, encoding="utf-8")
    advance.submit([f], ocr=False, doan=False)
    _until(lambda: db.execute("SELECT COUNT(*) FROM units").fetchone()[0] and not semantic.missing_roots(db))
    assert _vectors(db) == 3  # 2 Điều + đoạn mở đầu
    snap = advance.snapshot()
    assert snap["items"][0]["state"] == "du" and snap["embed"]["total"] == 3


def test_normal_mode_never_embeds(advance, db, tmp_path):
    semantic.set_mode(db, "normal")
    f = tmp_path / "nd9.txt"
    f.write_text(DOC, encoding="utf-8")
    advance.submit([f], ocr=False, doan=False)
    _until(lambda: not advance.snapshot()["active"] and advance.snapshot()["total"])
    time.sleep(0.3)
    assert _vectors(db) == 0


def test_wake_embeds_when_mode_flips_to_advance(advance, db, tmp_path):
    semantic.set_mode(db, "normal")
    f = tmp_path / "nd9.txt"
    f.write_text(DOC, encoding="utf-8")
    ingest_path(db, f, tmp_path)
    advance.wake()
    time.sleep(0.3)
    assert _vectors(db) == 0
    semantic.set_mode(db, "advance")
    advance.wake()
    _until(lambda: not semantic.missing_roots(db))
    assert _vectors(db) == 3


def test_folder_expands_and_unsupported_single_file_listed(advance, db, tmp_path):
    d = tmp_path / "thu_muc" / "con"
    d.mkdir(parents=True)
    (d / "a.txt").write_text(DOC, encoding="utf-8")
    (d / "~$a.docx").write_bytes(b"")  # file tạm Office
    (d / "anh.gif").write_bytes(b"GIF")
    odd = tmp_path / "x.exe"
    odd.write_bytes(b"MZ")
    r = advance.submit([tmp_path / "thu_muc", odd], ocr=False, doan=False)
    assert r == {"queued": 1, "skipped": 1}  # gif trong thư mục đếm bỏ qua; ~$ không tính
    _until(lambda: not advance.snapshot()["active"])
    got = {i["name"]: i["state"] for i in advance.snapshot()["items"]}
    assert got == {"a.txt": "du", "x.exe": "bo_qua"}


def test_one_bad_file_does_not_stop_queue(advance, db, tmp_path, monkeypatch):
    import soiluat.importer as imp

    real = imp.import_one

    def flaky(conn, f, root, **kw):
        if f.name == "hong.txt":
            raise RuntimeError("hỏng")
        return real(conn, f, root, **kw)

    monkeypatch.setattr(imp, "import_one", flaky)
    bad, good = tmp_path / "hong.txt", tmp_path / "tot.txt"
    bad.write_text(DOC, encoding="utf-8")
    good.write_text(DOC + "3. Thêm.\n", encoding="utf-8")
    advance.submit([bad, good], ocr=False, doan=False)
    _until(lambda: not advance.snapshot()["active"] and advance.snapshot()["total"] == 2)
    items = {i["name"]: (i["state"], i["note"]) for i in advance.snapshot()["items"]}
    assert items["hong.txt"][0] == "loi" and "hỏng" in items["hong.txt"][1]
    assert items["tot.txt"][0] == "du"


def test_keeps_at_most_keep_rows_dropping_finished_first(advance, tmp_path, monkeypatch):
    import soiluat.jobs as jm

    monkeypatch.setattr(jm, "KEEP", 3)
    files = []
    for k in range(5):
        f = tmp_path / f"f{k}.txt"
        f.write_text(DOC + f"{k + 3}. Mục {k}.\n", encoding="utf-8")
        files.append(f)
    advance.submit(files[:3], ocr=False, doan=False)
    _until(lambda: not advance.snapshot()["active"])
    advance.submit(files[3:], ocr=False, doan=False)
    _until(lambda: not advance.snapshot()["active"])
    names = [i["name"] for i in advance.snapshot()["items"]]
    assert len(names) <= 3 and names[-1] == "f4.txt"


def test_s2_nhung_loi_khong_giet_luong_nen_va_lan_sau_nhung_lai(advance, db, tmp_path, monkeypatch):
    """S2: embed_roots lỗi (khoá ghi giữ quá 5 s, đĩa đầy, onnx lỗi) không được làm chết luồng im lặng: chip "Nhúng" tắt
    thay vì quay mãi, và lần wake() sau nhúng lại được."""
    f = tmp_path / "nd9.txt"
    f.write_text(DOC, encoding="utf-8")
    ingest_path(db, f, tmp_path)
    real, calls = semantic.embed_roots, []

    def hong_mot_lan(conn, enc, ids):
        calls.append(1)
        if len(calls) == 1:
            raise sqlite3.OperationalError("database is locked")
        return real(conn, enc, ids)

    monkeypatch.setattr(semantic, "embed_roots", hong_mot_lan)
    advance.wake()
    _until(lambda: calls and not advance.snapshot()["active"])
    snap = advance.snapshot()
    assert advance._thread.is_alive() and snap["embed"]["running"] is False
    assert "database is locked" in snap["embed"]["error"] and _vectors(db) == 0
    advance.wake()  # khoá đã nhả: lần đếm lại nhúng được
    _until(lambda: not semantic.missing_roots(db))
    assert _vectors(db) == 3
