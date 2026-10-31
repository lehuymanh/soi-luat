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


# ---- N1b: nâng cấp dữ liệu một lần (PARSE_REV) ----

import time

from soiluat import db as dbmod
from soiluat.db import backup_db
from soiluat.jobs import Jobs
from soiluat.parse import PARSE_REV
from soiluat.rebuild import rebuild_if_changed


def _lech(db, doc_id):
    """Giả lập kho dựng bằng parser cũ: sửa chữ một Điều cho lệch với kết quả parse hiện tại."""
    uid, goc = db.execute(
        "SELECT id, raw_text FROM units WHERE doc_id = ? AND level = 'dieu' ORDER BY id LIMIT 1", (doc_id,)
    ).fetchone()
    db.execute("UPDATE units SET raw_text = 'chữ của parser cũ' WHERE id = ?", (uid,))
    db.commit()
    return uid, goc


def _raw(db, uid):
    return db.execute("SELECT raw_text FROM units WHERE id = ?", (uid,)).fetchone()[0]


def _rev(db):
    r = db.execute("SELECT value FROM app_meta WHERE key = 'parse_rev'").fetchone()
    return r[0] if r else None


def _chay(j, db, toi_da=200):
    """Gọi _migrate_chunk tới khi trả False; trả số lần True."""
    n = 0
    while j._migrate_chunk(db):
        n += 1
        assert n < toi_da
    return n


def test_rebuild_if_changed_sua_lech_thi_dung_lai(db, nd9):
    uid, goc = _lech(db, nd9)
    assert rebuild_if_changed(db, nd9) is True
    assert db.execute("SELECT raw_text FROM units WHERE doc_id = ? AND path = 'D1'", (nd9,)).fetchone()[0] == goc


def test_rebuild_if_changed_khong_doi_giu_nguyen_id(db, nd9):
    ids = db.execute("SELECT id FROM units WHERE doc_id = ? ORDER BY id", (nd9,)).fetchall()
    assert rebuild_if_changed(db, nd9) is False
    assert db.execute("SELECT id FROM units WHERE doc_id = ? ORDER BY id", (nd9,)).fetchall() == ids


def test_rebuild_if_changed_bo_qua_fallback_doan(db, nd9):
    uid, _ = _lech(db, nd9)
    db.execute("UPDATE documents SET fallback_doan = 1 WHERE id = ?", (nd9,))
    db.commit()
    assert rebuild_if_changed(db, nd9) is False
    assert _raw(db, uid) == "chữ của parser cũ"


def test_backup_db_loi_khong_de_tep_ten_dich(tmp_path):
    src = tmp_path / "hong.db"
    src.write_bytes(b"day khong phai sqlite" * 100)
    dest = tmp_path / "backup" / "soiluat.db"
    with pytest.raises(sqlite3.DatabaseError):
        backup_db(src, dest)
    assert not dest.exists()
    assert list(dest.parent.iterdir()) == []  # không sót .tmp, .tmp-journal


def test_backup_db_het_dia_giua_chung_giu_ban_cu(tmp_path):
    resource = pytest.importorskip("resource")  # giả lập đĩa đầy bằng trần cỡ tệp (Linux)
    import signal

    src = tmp_path / "soiluat.db"
    c = sqlite3.connect(src)
    c.execute("CREATE TABLE t(x BLOB)")
    c.executemany("INSERT INTO t VALUES (?)", [(b"x" * 100_000,)] * 30)  # ~3 MB
    c.commit()
    c.close()
    dest = tmp_path / "backup" / "soiluat.db"
    dest.parent.mkdir()
    c = sqlite3.connect(dest)  # bản sao lưu cũ hợp lệ
    c.execute("CREATE TABLE cu(x)")
    c.commit()
    c.close()
    cu = dest.read_bytes()
    soft, hard = resource.getrlimit(resource.RLIMIT_FSIZE)
    old_sig = signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
    resource.setrlimit(resource.RLIMIT_FSIZE, (1 << 20, hard))
    try:
        with pytest.raises(sqlite3.Error):
            backup_db(src, dest)
    finally:
        resource.setrlimit(resource.RLIMIT_FSIZE, (soft, hard))
        signal.signal(signal.SIGXFSZ, old_sig)
    assert dest.read_bytes() == cu
    assert [p.name for p in dest.parent.iterdir()] == ["soiluat.db"]


@pytest.fixture
def kho(db, tmp_path, monkeypatch):
    monkeypatch.setenv("SOILUAT_DATA", str(tmp_path))  # db_path() trỏ đúng kho của fixture `db`
    return tmp_path / "backup" / f"soiluat-truoc-parse{PARSE_REV}.db"


def test_nang_cap_sao_luu_roi_dung_lai_ghi_parse_rev_sau_cung(db, nd9, kho, monkeypatch):
    uid, goc = _lech(db, nd9)
    gap = []
    import soiluat.rebuild as rb

    real = rb.rebuild_if_changed
    monkeypatch.setattr(rb, "rebuild_if_changed", lambda c, d: gap.append((_rev(c), kho.exists())) or real(c, d))
    j = Jobs()
    assert j._migrate_chunk(db) is True  # lần đầu: sao lưu, chốt danh sách, chưa duyệt văn bản nào
    snap = j.snapshot()
    assert snap["migrate"]["running"] and snap["migrate"]["total"] == 1 and snap["active"]
    _chay(j, db)
    assert gap == [(None, True)]  # lúc dựng lại: đã có sao lưu, chưa có parse_rev
    assert _raw(db, uid) == goc and _rev(db) == PARSE_REV
    bak = dbmod.connect(kho)
    assert bak.execute("SELECT raw_text FROM units WHERE id = ?", (uid,)).fetchone()[0] == "chữ của parser cũ"
    bak.close()
    assert not j.snapshot()["migrate"]["running"] and not j.snapshot()["active"]
    # mở app lần sau: không làm gì
    gap.clear()
    kho_mtime = kho.stat().st_mtime_ns
    assert _chay(Jobs(), db) == 0 and gap == [] and kho.stat().st_mtime_ns == kho_mtime


def test_nang_cap_kho_trong_ghi_co_khong_sao_luu(db, kho):
    j = Jobs()
    assert j._migrate_chunk(db) is False
    assert _rev(db) == PARSE_REV and not kho.parent.exists()


def test_nang_cap_van_ban_bi_khoa_khong_ghi_parse_rev_va_khong_duyet_lai(db, nd9, kho, monkeypatch):
    uid, _ = _lech(db, nd9)
    n = []

    def khoa(*a, **k):
        n.append(1)
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(ingest, "persist_parsed", khoa)
    j = Jobs()
    _chay(j, db)
    assert len(n) == 2 and _rev(db) is None and not db.in_transaction  # lần đầu và một lượt thử lại cuối lượt (S4)
    assert "database is locked" in j.migrate["error"] and not j.migrate["running"]
    assert _raw(db, uid) == "chữ của parser cũ"  # văn bản lỗi còn nguyên đơn vị
    assert j._migrate_chunk(db) is False and len(n) == 2  # một lượt mỗi lần mở app
    j.wake(); j.stop()  # wake, submit không đặt lại cờ
    assert j._migrate_chunk(db) is False and len(n) == 2


def test_nang_cap_sao_luu_loi_thi_khong_dung_lai_va_khong_thu_lai(db, nd9, kho, monkeypatch):
    uid, _ = _lech(db, nd9)
    n = []

    def hong(src, dest):
        n.append(1)
        raise OSError("disk full")

    monkeypatch.setattr(dbmod, "backup_db", hong)
    j = Jobs()
    _chay(j, db)
    assert len(n) == 1 and _rev(db) is None and _raw(db, uid) == "chữ của parser cũ"
    assert "disk full" in j.migrate["error"] and j.migrate["failed"] == 1
    assert j._migrate_chunk(db) is False and len(n) == 1


def test_luong_nen_tu_nang_cap_khi_wake(db, nd9, kho):
    uid, goc = _lech(db, nd9)
    j = Jobs()
    j.wake()
    try:
        end = time.time() + 30
        while _rev(db) != PARSE_REV and time.time() < end:
            time.sleep(0.05)
    finally:
        j.stop()
    assert _rev(db) == PARSE_REV and _raw(db, uid) == goc and kho.exists()


# ---- N1b: soát lần hai (S1..S7, T2, R1) ----

import os

import soiluat.jobs as jobsmod
import soiluat.rebuild as rb

XU_PHAT = (
    "Nghị định số 20/2024/NĐ-CP\n"
    "Điều 1. Nghĩa vụ niêm yết giá\n"
    "1. Cơ sở kinh doanh phải niêm yết giá bán công khai tại cửa hàng.\n"
    "Điều 2. Xử phạt\n"
    "1. Phạt tiền từ 1.000.000 đồng đến 2.000.000 đồng đối với hành vi không niêm yết giá bán công khai.\n"
    "Điều 3. Xử phạt khác\n"
    "1. Phạt tiền từ 3.000.000 đồng đến 5.000.000 đồng đối với hành vi vi phạm quy định tại khoản 1 Điều 1 Nghị định này.\n"
)


def _nhieu_van_ban(db, tmp_path, n):
    ids = []
    for k in range(n):
        p = tmp_path / f"vb{k}.txt"
        p.write_text(ND9.replace("số 9/2021", f"số {k + 20}/2021", 1), encoding="utf-8")
        ids.append(ingest_path(db, p, tmp_path))
    return ids


def _khoa_ghi(tmp_path):
    """Kết nối khác giữ khoá ghi của kho (như bản chạy cổng 8001 đang nạp file lớn)."""
    other = dbmod.connect(tmp_path / "soiluat.db")
    other.execute("BEGIN IMMEDIATE")
    return other


def test_s1_t3_khoa_ghi_o_buoc_ghi_co_thi_luong_khong_chet_im(db, kho, tmp_path):
    other = _khoa_ghi(tmp_path)
    db.execute("PRAGMA busy_timeout=50")
    try:
        j = Jobs()
        assert j._migrate_chunk(db) is False  # kho trống: bước ghi cờ gặp khoá, không được ném OperationalError
    finally:
        other.rollback()
        other.close()
    assert not j.migrate["running"] and "locked" in j.migrate["error"]
    assert j._migrate_tried and _rev(db) is None and not db.in_transaction


def test_s4_khoa_thoang_qua_duoc_thu_lai_cuoi_luot(db, nd9, kho, monkeypatch):
    uid, goc = _lech(db, nd9)
    real = rb.rebuild_if_changed
    calls = []

    def khoa_mot_lan(c, d):
        calls.append(d)
        if len(calls) == 1:
            raise sqlite3.OperationalError("database is locked")
        return real(c, d)

    monkeypatch.setattr(rb, "rebuild_if_changed", khoa_mot_lan)
    j = Jobs()
    _chay(j, db)
    assert calls == [nd9, nd9]  # khoá hết ngay sau đó: thử lại một lần ở cuối lượt
    assert _raw(db, uid) == goc and _rev(db) == PARSE_REV and j.migrate["error"] == ""
    assert j.migrate["done"] == j.migrate["total"] == 1  # lượt thử lại không tính thêm
    assert j.migrate["failed"] == 0


def test_s4_khoa_giu_lau_dung_lai_sau_3_van_ban_lien_tiep(db, tmp_path, kho, monkeypatch):
    _nhieu_van_ban(db, tmp_path, 5)
    calls = []

    def khoa(c, d):
        calls.append(d)
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(rb, "rebuild_if_changed", khoa)
    j = Jobs()
    _chay(j, db)
    assert len(calls) == 3  # không chờ 5 s cho từng văn bản còn lại, cũng không thử lại
    assert _rev(db) is None and "database is locked" in j.migrate["error"] and not j.migrate["running"]
    assert j.migrate["failed"] == 5  # 3 văn bản lỗi và 2 văn bản bỏ lượt: giao diện nói đủ số chưa nâng cấp


def test_s3_lan_nang_cap_thu_hai_co_sao_luu_rieng(db, nd9, kho, monkeypatch):
    _lech(db, nd9)
    _chay(Jobs(), db)
    thu_muc = kho.parent
    truoc = {p.name: p.read_bytes() for p in thu_muc.glob("soiluat-truoc-*.db")}
    assert len(truoc) == 1
    uid, _ = _lech(db, nd9)  # việc người dùng làm sau lần nâng cấp đầu
    monkeypatch.setattr(jobsmod, "PARSE_REV", "99")
    _chay(Jobs(), db)
    sau = {p.name: p.read_bytes() for p in thu_muc.glob("soiluat-truoc-*.db")}
    assert _rev(db) == "99" and len(sau) == 2
    assert all(sau[k] == v for k, v in truoc.items())  # bản của lần đầu còn nguyên
    moi = next(p for p in thu_muc.glob("soiluat-truoc-*.db") if p.name not in truoc)
    bak = dbmod.connect(moi)
    assert bak.execute("SELECT raw_text FROM units WHERE id = ?", (uid,)).fetchone()[0] == "chữ của parser cũ"
    bak.close()


def test_s6_sao_luu_loi_nhung_ban_kia_da_xong_thi_van_nang_cap(db, nd9, kho, monkeypatch):
    uid, goc = _lech(db, nd9)

    def ban_kia_xong_truoc(src, dest):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"ban sao luu cua ban chay kia")
        raise sqlite3.OperationalError("attempt to write a readonly database")

    monkeypatch.setattr(dbmod, "backup_db", ban_kia_xong_truoc)
    j = Jobs()
    _chay(j, db)
    assert _raw(db, uid) == goc and _rev(db) == PARSE_REV and j.migrate["error"] == ""


def test_s6_hai_ban_sao_luu_cung_luc_khong_xoa_tep_tam_cua_nhau(tmp_path, monkeypatch):
    src = tmp_path / "soiluat.db"
    c = sqlite3.connect(src)
    c.execute("CREATE TABLE t(x)")
    c.execute("INSERT INTO t VALUES (1)")
    c.commit()
    c.close()
    hong = tmp_path / "hong.db"
    hong.write_bytes(b"day khong phai sqlite" * 100)
    dest = tmp_path / "backup" / "soiluat.db"
    real = os.replace

    def thua_luc_ban_nay_sap_doi_ten(a, b):
        monkeypatch.setattr(os, "replace", real)
        with monkeypatch.context() as m:
            m.setattr(os, "getpid", lambda: 424242)  # tiến trình thứ hai cùng kho
            with pytest.raises(sqlite3.DatabaseError):
                backup_db(hong, dest)  # bản kia lỗi đúng lúc tệp tạm của bản này đã đủ
        real(a, b)

    monkeypatch.setattr(os, "replace", thua_luc_ban_nay_sap_doi_ten)
    backup_db(src, dest)
    r = sqlite3.connect(dest)
    assert r.execute("SELECT x FROM t").fetchone()[0] == 1
    r.close()
    assert [p.name for p in dest.parent.iterdir()] == ["soiluat.db"]


def test_s7_dung_lai_giu_nguoi_va_ngay_duyet_lien_ket(db, sample_doc):
    db.execute("UPDATE links SET confirmed = 1, reviewed_by = 'tester', reviewed_at = '2026-10-01T10:00:00'")
    db.commit()
    before = [tuple(r) for r in db.execute("SELECT confirmed, reviewed_by, reviewed_at FROM links")]
    assert before == [(1, "tester", "2026-10-01T10:00:00")]
    rebuild_document(db, sample_doc)
    assert [tuple(r) for r in db.execute("SELECT confirmed, reviewed_by, reviewed_at FROM links")] == before


def test_r1_s5_dung_lai_giu_khoa_ghi_tu_luc_doc_trang(db, nd9, tmp_path, monkeypatch):
    other = dbmod.connect(tmp_path / "soiluat.db")
    other.execute("PRAGMA busy_timeout=0")
    seen = []
    real = rb._parse_stored

    def parse(conn, doc):
        out = real(conn, doc)
        try:  # người dùng lưu chữ đối chiếu của trang đúng lúc luồng nâng cấp vừa đọc và parse xong
            other.execute("UPDATE pages SET reviewed_text = 'sửa tay' WHERE doc_id = ?", (doc["id"],))
            other.commit()
            seen.append("ghi được")
        except sqlite3.OperationalError:
            seen.append("bị chặn")
        return out

    monkeypatch.setattr(rb, "_parse_stored", parse)
    try:
        rebuild_document(db, nd9)
    finally:
        other.close()
    assert seen == ["bị chặn"]  # ghi chen vào đây sẽ bị dựng lại đè bằng chữ cũ
    assert not db.in_transaction


def test_t2_dung_lai_khong_giu_khoa_ghi_trong_luc_tim_fts_cho_goi_y(db, tmp_path, monkeypatch):
    import soiluat.search as sr

    p = tmp_path / "xu_phat.txt"
    p.write_text(XU_PHAT, encoding="utf-8")
    doc_id = ingest_path(db, p, tmp_path)
    real = sr.match_units
    seen = []

    def spy(conn, *a, **k):
        seen.append(conn.in_transaction)
        return real(conn, *a, **k)

    monkeypatch.setattr(sr, "match_units", spy)
    rebuild_document(db, doc_id)
    # Điều 3 có liên kết dẫn chiếu (INSERT mở giao dịch trước bước FTS), Điều 2 phải tìm bằng FTS
    assert db.execute("SELECT COUNT(*) FROM links WHERE method IN ('dan_chieu', 'noi_bo')").fetchone()[0] == 1
    assert seen and not any(seen)  # truy vấn FTS (cỡ 0,17 s mỗi câu ở Zalo) chạy ngoài giao dịch ghi


def test_s1_nap_file_khong_giu_khoa_ghi_trong_luc_tim_fts_cho_goi_y(db, tmp_path, monkeypatch):
    """S1: nạp file (ingest_group) cũng phải nhả khoá ghi trước truy vấn FTS của gợi ý liên kết, như rebuild_document;
    giữ khoá suốt phần này làm hỏi đáp và mọi thao tác ghi khác chờ 5 s rồi lỗi trong lúc nạp văn bản xử phạt lớn."""
    import soiluat.search as sr

    p = tmp_path / "xu_phat.txt"
    p.write_text(XU_PHAT, encoding="utf-8")
    real = sr.match_units
    seen = []

    def spy(conn, *a, **k):
        seen.append(conn.in_transaction)
        return real(conn, *a, **k)

    monkeypatch.setattr(sr, "match_units", spy)
    doc_id = ingest_path(db, p, tmp_path)
    assert db.execute("SELECT COUNT(*) FROM links WHERE method IN ('dan_chieu', 'noi_bo')").fetchone()[0] == 1
    assert doc_id and seen and not any(seen)


def test_s6_nap_lai_cung_duong_dan_giu_goi_y_hieu_luc_da_duyet_va_khong_nhan_doi_bai_bo(db, nd9, tmp_path):
    """S6: sửa file rồi nạp lại cùng đường dẫn không xoá gợi ý đã duyệt, và gợi ý bãi bỏ (không có đích) đã duyệt
    không sinh thêm một bản chưa duyệt y hệt."""
    db.execute("UPDATE effect_hints SET confirmed = 1")
    db.commit()
    before = [(h["kind"], h["target_so_hieu"], h["confirmed"]) for h in _hints(db, nd9)]
    assert len(before) == 3 and all(c == 1 for *_, c in before)
    (tmp_path / "nd9.txt").write_text(ND9 + "4. Điều khoản bổ sung không liên quan.\n", encoding="utf-8")
    assert ingest_path(db, tmp_path / "nd9.txt", tmp_path) == nd9
    assert [(h["kind"], h["target_so_hieu"], h["confirmed"]) for h in _hints(db, nd9)] == before


def test_s6_dung_lai_khong_nhan_doi_goi_y_bai_bo_da_duyet(db, nd9):
    """S6: mỗi lần tăng PARSE_REV, rebuild_document thêm bản chưa duyệt y hệt của gợi ý bãi bỏ đã duyệt (target NULL
    nên không gì chặn); giữ gợi ý đã duyệt và không thêm bản trùng."""
    bai_bo = [h["id"] for h in _hints(db, nd9) if h["kind"] == "bai_bo"]
    db.execute("UPDATE effect_hints SET confirmed = 1 WHERE id = ?", (bai_bo[0],))
    db.commit()
    rebuild_document(db, nd9)
    rebuild_document(db, nd9)
    after = _hints(db, nd9)
    assert [h["kind"] for h in after].count("bai_bo") == 2
    assert [h["id"] for h in after if h["confirmed"]] == [bai_bo[0]]


def test_s7_hai_lan_sao_luu_cung_luc_dung_tep_tam_rieng(tmp_path, monkeypatch):
    """S7: bấm "Sao lưu SQLite" hai lần: hai yêu cầu chạy song song trong cùng một tiến trình, tệp tạm không được trùng tên
    (lần xong sau xoá tệp tạm của lần kia thì lần kia lỗi 'disk I/O error')."""
    src = tmp_path / "soiluat.db"
    c = sqlite3.connect(src)
    c.execute("CREATE TABLE t(x)")
    c.commit()
    c.close()
    seen = []
    real = sqlite3.connect
    monkeypatch.setattr(dbmod.sqlite3, "connect", lambda p, *a, **k: seen.append(str(p)) or real(p, *a, **k))
    dest = tmp_path / "backup" / "soiluat.db"
    backup_db(src, dest)
    backup_db(src, dest)
    tmps = [p for p in seen if p.endswith(".tmp")]
    assert len(tmps) == 2 and tmps[0] != tmps[1]


def test_s1_loi_sau_khi_da_luu_thi_nap_lai_dung_not_goi_y(db, tmp_path, monkeypatch):
    """S1: commit trước FTS nên lỗi ở bước gợi ý (hay app tắt) để văn bản đã lưu; lần nạp lại file đó không được báo
    "không đổi" mà bỏ mất gợi ý hiệu lực."""
    import soiluat.links as links

    p = tmp_path / "nd9.txt"
    p.write_text(ND9, encoding="utf-8")
    real = links.suggest_fts_links

    def hong(*a, **k):
        raise sqlite3.OperationalError("disk full")

    monkeypatch.setattr(links, "suggest_fts_links", hong)
    with pytest.raises(sqlite3.OperationalError):
        ingest_path(db, p, tmp_path)
    doc_id = db.execute("SELECT id FROM documents").fetchone()[0]
    assert _hints(db, doc_id) == []
    monkeypatch.setattr(links, "suggest_fts_links", real)
    assert ingest_path(db, p, tmp_path) == doc_id  # dùng lại văn bản, không nhân đôi
    assert len(_hints(db, doc_id)) == 3
    assert ingest_path(db, p, tmp_path) == doc_id
    assert db.execute("SELECT COUNT(*) FROM import_jobs").fetchone()[0] == 2  # lần xong rồi thì "không đổi", không mở job mới
