"""P1 H1: bảng lịch sử trò chuyện (conversations, messages), nâng cấp kho 0.8 an toàn."""

import json
import sqlite3
import unicodedata
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import soiluat.app as appmod
from soiluat import conversations
from soiluat.db import connect, init_schema
from soiluat.ingest import ingest_path
from soiluat.rebuild import rebuild_document


def _kho_08(path):
    conn = sqlite3.connect(path)
    conn.executescript((Path(__file__).parent / "fixtures" / "schema_08.sql").read_text(encoding="utf-8"))
    conn.execute("INSERT INTO documents(id, file_path, sha256, source_status, extraction_method) VALUES (1, 'a.txt', 'x', 'ok', 'txt')")
    conn.execute("INSERT INTO units(id, doc_id, path, level, raw_text, normalized_text, search_text, extraction_method,"
                 " verification_status) VALUES (1, 1, 'D1', 'dieu', 'Điều 1', 'dieu 1', 'dieu 1', 'txt', 'auto')")
    conn.execute("INSERT INTO query_log(query_raw, result_count, created_at) VALUES ('phạt', 3, '2026-01-01')")
    conn.commit()
    conn.close()


def _dump(conn):
    return [tuple(r) for t in ("documents", "units", "query_log") for r in conn.execute(f"SELECT * FROM {t} ORDER BY 1")]


def test_nang_cap_tu_0_8(tmp_path):
    _kho_08(tmp_path / "kho.db")
    conn = connect(tmp_path / "kho.db")
    before = _dump(conn)
    init_schema(conn)
    init_schema(conn)  # chạy lại mỗi request vẫn an toàn
    assert _dump(conn) == before
    cid = conn.execute("INSERT INTO conversations(title, created_at, updated_at) VALUES ('Mức phạt', 'a', 'a')").lastrowid
    m1 = conn.execute("INSERT INTO messages(conversation_id, role, text, created_at) VALUES (?, 'user', 'hỏi', 'a')", (cid,)).lastrowid
    conn.execute("DELETE FROM messages WHERE id = ?", (m1,))
    m2 = conn.execute("INSERT INTO messages(conversation_id, role, text, created_at) VALUES (?, 'bot', 'đáp', 'a')", (cid,)).lastrowid
    assert m2 > m1  # id tin đã xoá không tái dùng: tab cũ không nhận nhầm tin mới
    conn.execute("DELETE FROM conversations WHERE id = ?", (cid,))
    assert conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 0  # xoá cuộc xoá luôn tin
    plan = " ".join(r[3] for r in conn.execute("EXPLAIN QUERY PLAN SELECT * FROM messages WHERE conversation_id = 1 ORDER BY id"))
    assert "INDEX" in plan and "SCAN" not in plan, plan


# ---- P1 H2: lưu câu hỏi (conversations.py, POST /ask) ----

T0, T1 = "2026-01-01T00:00:00+00:00", "2026-01-02T00:00:00+00:00"


def _nd(so, n_dieu=4, noi="Đơn vị phải báo cáo định kỳ"):
    return f"Nghị định số {so}/NĐ-CP ngày 01 tháng 01 năm 2020\n\n" + "".join(
        f"Điều {d}. Báo cáo lần {d}\n1. {noi} lần {d}.\n\n" for d in range(1, n_dieu + 1))


def _nap(db, tmp_path, so, **kw):
    p = tmp_path / (so.replace("/", "-") + ".txt")
    p.write_text(_nd(so, **kw), encoding="utf-8")
    return ingest_path(db, p, tmp_path)


def _unit_ids(db, doc_id):
    return [r["id"] for r in db.execute("SELECT id FROM units WHERE doc_id = ? ORDER BY id", (doc_id,))]


def _client(tmp_path, monkeypatch):
    monkeypatch.setenv("SOILUAT_DATA", str(tmp_path))
    return TestClient(appmod.app)


def _ask(c, q, cid=None, **filters):
    return c.post("/ask", data={"q": q, **({"conversation_id": str(cid)} if cid else {}), **filters})


def _bot(db, cid):
    return json.loads(db.execute("SELECT result_json FROM messages WHERE conversation_id = ? AND role = 'bot' "
                                 "ORDER BY id DESC LIMIT 1", (cid,)).fetchone()[0])


def test_luu_hai_tin_cap_nhat_updated_at(db):
    res = {"kind": "list", "q": "báo cáo", "refs": []}
    cid = conversations.save(db, None, "báo cáo định kỳ", res, T0)
    rows = db.execute("SELECT role, text, result_json FROM messages WHERE conversation_id = ? ORDER BY id", (cid,)).fetchall()
    assert [r["role"] for r in rows] == ["user", "bot"]
    assert rows[0]["text"] == "báo cáo định kỳ" and rows[0]["result_json"] is None
    assert json.loads(rows[1]["result_json"]) == res
    c = db.execute("SELECT title, created_at, updated_at FROM conversations").fetchone()
    assert (c["title"], c["created_at"], c["updated_at"]) == ("báo cáo định kỳ", T0, T0)
    assert conversations.save(db, cid, "câu thứ hai", res, T1) == cid  # cuộc còn: ghi tiếp, không tạo cuộc mới
    c = db.execute("SELECT title, created_at, updated_at FROM conversations").fetchone()
    assert (c["title"], c["created_at"], c["updated_at"]) == ("báo cáo định kỳ", T0, T1)  # tiêu đề là câu đầu
    assert db.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 4


def test_tieu_de_nfc_cat_60_ky_tu(db):
    dai = unicodedata.normalize("NFD", "Mức phạt đối với hành vi không đội mũ bảo hiểm khi đi xe máy trên đường")
    cid = conversations.save(db, None, dai, {}, T0)
    title = db.execute("SELECT title FROM conversations WHERE id = ?", (cid,)).fetchone()[0]
    nfc = unicodedata.normalize("NFC", dai)
    assert title == nfc[:60] + "…" and len(title) == 61  # cắt sau khi chuẩn hoá: NFD sẽ cắt giữa chữ cái và dấu
    assert unicodedata.is_normalized("NFC", title)
    vua = "a" * 60
    cid = conversations.save(db, None, vua, {}, T0)
    assert db.execute("SELECT title FROM conversations WHERE id = ?", (cid,)).fetchone()[0] == vua  # đủ 60: không thêm "…"
    cid = conversations.save(db, None, "dòng một\n\n  dòng hai", {}, T0)  # Shift+Enter: tên cuộc một dòng
    assert db.execute("SELECT title FROM conversations WHERE id = ?", (cid,)).fetchone()[0] == "dòng một dòng hai"


def test_luu_loi_khong_de_lai_cuoc_rong(db):
    """Không tạo dòng conversations trước khi lưu được tin đầu: tin trả lời lỗi thì cả giao dịch lui."""
    db.execute("CREATE TRIGGER chan BEFORE INSERT ON messages WHEN new.role = 'bot' BEGIN SELECT RAISE(ABORT, 'x'); END")
    with pytest.raises(sqlite3.Error):
        conversations.save(db, None, "báo cáo", {}, T0)
    assert db.execute("SELECT COUNT(*) FROM conversations").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 0
    assert not db.in_transaction


def test_refs_of_resolve_khu_hoi(db, tmp_path):
    d1 = _nap(db, tmp_path, "15/2020")
    ids = _unit_ids(db, d1)[:5][::-1]  # thứ tự xếp hạng, không phải thứ tự id
    refs = conversations.refs_of(db, ids, tiers={ids[0]: 1, ids[1]: 3}, fold_ids={ids[1]}, f2_ids={ids[2]})
    assert [r[0] for r in refs] == [d1] * 5 and all(len(r[2]) == 10 for r in refs)
    assert [r[3:] for r in refs[:4]] == [[1, 0, 0], [3, 1, 0], [6, 0, 1], [6, 0, 0]]  # (tier, fold, f2); thiếu tier = 6 như assemble_cards
    assert json.loads(json.dumps(refs)) == refs
    assert conversations.resolve(db, refs) == (ids, 0)  # giữ thứ tự xếp hạng


def test_resolve_bao_hong_khi_mat_path_hoac_chu_doi(db, tmp_path):
    d1 = _nap(db, tmp_path, "15/2020")
    a, b, c = _unit_ids(db, d1)[:3]
    refs = conversations.refs_of(db, [a, b, c])
    db.execute("UPDATE units SET path = path || '~9' WHERE id = ?", (a,))
    db.execute("UPDATE units SET raw_text = raw_text || ' thêm chữ' WHERE id = ?", (b,))
    assert conversations.resolve(db, refs) == ([c], 2)


def test_resolve_bao_hong_khi_doc_id_bi_van_ban_khac_dung(db, tmp_path):
    d1 = _nap(db, tmp_path, "15/2020", n_dieu=4)
    by_path = {r["path"]: r["id"] for r in db.execute("SELECT id, path FROM units WHERE doc_id = ?", (d1,))}
    refs = conversations.refs_of(db, [by_path[p] for p in ("D1", "D1.K1", "D2.K1", "D3", "D3.K1")])
    db.execute("DELETE FROM documents WHERE id = ?", (d1,))
    db.commit()
    d2 = _nap(db, tmp_path, "16/2020", n_dieu=2, noi="Nội dung khác hẳn")
    assert d2 == d1  # documents.id tái dùng: nếu SQLite đổi cách cấp id thì test này không còn kiểm gì
    ids, bad = conversations.resolve(db, refs)
    # D1.K1, D2.K1 cùng path nhưng chữ khác; D3, D3.K1 không còn: chỉ (doc_id, path) sẽ hiện nhầm. D1 (chữ y hệt) vẫn nhận
    assert bad == 4 and len(ids) == 1


def test_resolve_sau_rebuild_document_van_tim_lai_bang_path(db, tmp_path):
    d1 = _nap(db, tmp_path, "15/2020")
    _nap(db, tmp_path, "16/2020")  # nạp muộn hơn: không có nó thì rebuild_document giữ nguyên id đơn vị và test không kiểm gì
    before = {r["path"]: r["id"] for r in db.execute("SELECT id, path FROM units WHERE doc_id = ?", (d1,))}
    paths = sorted(before)[:4]
    refs = conversations.refs_of(db, [before[p] for p in paths])
    rebuild_document(db, d1)
    after = {r["path"]: r["id"] for r in db.execute("SELECT id, path FROM units WHERE doc_id = ?", (d1,))}
    assert all(after[p] != before[p] for p in paths)  # id đơn vị đã đổi
    assert conversations.resolve(db, refs) == ([after[p] for p in paths], 0)


def test_resolve_ref_muc_van_ban_chi_kiem_doc_id(db, tmp_path):
    d1 = _nap(db, tmp_path, "15/2020")
    assert conversations.resolve(db, [[d1, None, None, 0, 0, 0], [d1 + 99, None, None, 0, 0, 0]]) == ([d1], 1)


def test_ask_luu_cuoc_va_hai_tin_roi_ghi_tiep(db, tmp_path, monkeypatch):
    _nap(db, tmp_path, "15/2020")
    c = _client(tmp_path, monkeypatch)
    r = _ask(c, "báo cáo định kỳ", loai="nghi_dinh")
    assert r.status_code == 200 and 'class="card' in r.text
    cid = int(r.headers["X-Conversation-Id"])
    res = _bot(db, cid)
    assert set(res) == {"kind", "q", "filters", "note", "intent", "sure", "n_found", "n_ids", "refs"}  # không q2_note, không gap
    assert res["kind"] == "list" and res["q"] == "báo cáo định kỳ" and res["filters"]["loai"] == "nghi_dinh"
    assert res["refs"] and all(len(x) == 6 for x in res["refs"]) and res["n_ids"] >= len(res["refs"])
    assert conversations.resolve(db, res["refs"])[1] == 0
    r2 = _ask(c, "lưu trữ hồ sơ", cid)
    assert r2.headers["X-Conversation-Id"] == str(cid)
    assert db.execute("SELECT COUNT(*) FROM conversations").fetchone()[0] == 1
    assert [x[0] for x in db.execute("SELECT role FROM messages ORDER BY id")] == ["user", "bot"] * 2
    assert db.execute("SELECT COUNT(*) FROM query_log").fetchone()[0] == 2  # nhật ký truy vấn vẫn ghi


def test_ask_cau_rong_khong_tao_cuoc(db, tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    r = _ask(c, "   ")
    assert r.status_code == 200 and "X-Conversation-Id" not in r.headers
    assert db.execute("SELECT COUNT(*) FROM conversations").fetchone()[0] == 0


def test_ask_conversation_id_rac_hoac_da_xoa_tao_cuoc_moi(db, tmp_path, monkeypatch):
    _nap(db, tmp_path, "15/2020")
    c = _client(tmp_path, monkeypatch)
    cid = int(_ask(c, "báo cáo định kỳ").headers["X-Conversation-Id"])
    db.execute("DELETE FROM conversations WHERE id = ?", (cid,))  # xoá ở tab khác
    db.commit()
    r = _ask(c, "lưu trữ hồ sơ", cid)
    new = int(r.headers["X-Conversation-Id"])
    assert r.status_code == 200 and 'class="card' in r.text and new != cid  # AUTOINCREMENT: id cũ không tái dùng
    assert db.execute("SELECT COUNT(*) FROM messages WHERE conversation_id = ?", (new,)).fetchone()[0] == 2
    for rac in ("abc", "99999999999999999999999", "-1", "٣"):
        r = _ask(c, "lưu trữ hồ sơ", rac)
        assert r.status_code == 200 and int(r.headers["X-Conversation-Id"]) > new


def test_ask_cau_khong_ra_ket_qua_hien_o_missed(db, tmp_path, monkeypatch):
    _nap(db, tmp_path, "15/2020")
    c = _client(tmp_path, monkeypatch)
    r = _ask(c, "xyzzy quux")
    assert r.status_code == 200 and "Không tìm thấy đoạn nào" in r.text
    assert "xyzzy quux" in c.get("/missed").text  # POST không làm /missed ngừng nhận câu mới
    assert _bot(db, int(r.headers["X-Conversation-Id"]))["refs"] == []  # vẫn là một lượt hỏi trong cuộc


def test_ask_van_ghi_query_log_khi_save_loi(db, tmp_path, monkeypatch):
    _nap(db, tmp_path, "15/2020")
    c = _client(tmp_path, monkeypatch)

    def hong(*a, **k):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(conversations, "save", hong)
    r = _ask(c, "báo cáo định kỳ")
    assert r.status_code == 200 and "Chưa lưu được vào lịch sử (đang nạp file)" in r.text and 'class="card' in r.text
    assert "X-Conversation-Id" not in r.headers
    assert db.execute("SELECT query_raw FROM query_log").fetchall()[0][0] == "báo cáo định kỳ"


def test_ask_khoa_ghi_van_tra_ket_qua_kem_canh_bao(db, tmp_path, monkeypatch):
    """Kết nối khác giữ BEGIN IMMEDIATE (đang nạp file): không 500, kết quả vẫn hiện. Chờ khoá rút còn 0,3 s cho nhanh;
    đường mã giống hệt chờ 5 s thật."""
    _nap(db, tmp_path, "15/2020")
    c = _client(tmp_path, monkeypatch)
    goc = appmod.get_conn

    def nhanh():
        conn = goc()
        conn.execute("PRAGMA busy_timeout=300")
        return conn

    monkeypatch.setattr(appmod, "get_conn", nhanh)
    giu = connect(tmp_path / "soiluat.db")
    giu.execute("BEGIN IMMEDIATE")
    try:
        r = _ask(c, "báo cáo định kỳ")
    finally:
        giu.rollback()
        giu.close()
    assert r.status_code == 200 and "Chưa lưu được vào lịch sử" in r.text and 'class="card' in r.text
    assert db.execute("SELECT COUNT(*) FROM conversations").fetchone()[0] == 0


def test_ask_so_hieu_mot_minh_luu_ref_muc_van_ban(db, tmp_path, monkeypatch):
    d1 = _nap(db, tmp_path, "20/2020", n_dieu=12)
    c = _client(tmp_path, monkeypatch)
    r = _ask(c, "20/2020/NĐ-CP")
    assert "Mở toàn văn" in r.text and 'class="card' not in r.text
    cid = int(r.headers["X-Conversation-Id"])
    raw = db.execute("SELECT result_json FROM messages WHERE conversation_id = ? AND role = 'bot'", (cid,)).fetchone()[0]
    res = json.loads(raw)
    assert res["kind"] == "full" and res["note"] == "so_hieu" and res["refs"] == [[d1, None, None, 0, 0, 0]]
    assert len(raw) < 400  # không phải 13 ref đơn vị, càng không phải ~1.500 ref của luật 300 Điều
    assert conversations.resolve(db, res["refs"]) == ([d1], 0)


def test_ask_ref_toi_da_150_khi_so_hieu_kem_y_dinh(db, tmp_path, monkeypatch):
    """Số hiệu + ý định ("mức phạt") không phải 'Mở toàn văn' mà trả mọi đơn vị của văn bản: refs không được phình theo."""
    _nap(db, tmp_path, "20/2020", n_dieu=200)
    c = _client(tmp_path, monkeypatch)
    r = _ask(c, "20/2020/NĐ-CP mức phạt")
    res = _bot(db, int(r.headers["X-Conversation-Id"]))
    assert res["intent"] == "muc_phat" and res["n_ids"] > conversations.REFS_MAX >= len(res["refs"]) > 0


def test_ask_csrf_khi_tat_bypass(db, tmp_path, monkeypatch):
    monkeypatch.setenv("SOILUAT_DATA", str(tmp_path))
    monkeypatch.delenv("SOILUAT_ALLOW_TEST_HOST")
    h = {"Host": "127.0.0.1:8000"}
    c = TestClient(appmod.app)
    token = c.get("/", headers=h).cookies.get("soiluat_csrf")
    assert c.post("/ask", headers=h, data={"q": "báo cáo"}).status_code == 403
    assert c.post("/ask", headers={"Host": "evil.example"}, data={"q": "báo cáo"}).status_code == 400
    ok = c.post("/ask", headers={**h, "X-CSRF-Token": token}, data={"q": "báo cáo"})
    assert ok.status_code == 200 and "X-Conversation-Id" in ok.headers
