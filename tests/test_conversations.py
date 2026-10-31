"""P1 H1: bảng lịch sử trò chuyện (conversations, messages), nâng cấp kho 0.8 an toàn."""

import html
import json
import re
import sqlite3
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import soiluat.app as appmod
from soiluat import conversations
from soiluat.db import connect, init_schema
from soiluat.ingest import ingest_path, relative_path, sha256_file
from soiluat.rebuild import rebuild_document, rebuild_document_from_file


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
    # D1.K1, D2.K1 cùng path nhưng chữ khác; D3, D3.K1 không còn; D1 chữ y hệt nhưng là Điều của văn bản khác (D1 soát):
    # `h` gắn cả số hiệu, nên hỏng cả năm. Chỉ băm chữ thì D1 "Phạm vi điều chỉnh" của văn bản mới được nhận nhầm
    assert (ids, bad) == ([], 5)


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


def test_resolve_ref_muc_van_ban_kiem_doc_id_va_so_hieu(db, tmp_path):
    d1 = _nap(db, tmp_path, "15/2020")
    h = conversations._h("15/2020/nd-cp")
    assert db.execute("SELECT so_hieu_search FROM documents WHERE id = ?", (d1,)).fetchone()[0] == "15/2020/nd-cp"
    assert conversations.resolve(db, [[d1, None, h, 0, 0, 0], [d1 + 99, None, h, 0, 0, 0]]) == ([d1], 1)
    assert conversations.resolve(db, [[d1, None, conversations._h("99/2026/nd-cp"), 0, 0, 0]]) == ([], 1)  # id còn nhưng là văn bản khác


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
    assert res["kind"] == "full" and res["note"] == "so_hieu" and res["refs"] == [[d1, None, conversations._h("20/2020/nd-cp"), 0, 0, 0]]
    assert len(raw) < 400  # không phải 13 ref đơn vị, càng không phải ~1.500 ref của luật 300 Điều
    assert conversations.resolve(db, res["refs"]) == ([d1], 0)


def test_ask_ref_toi_da_150_khi_so_hieu_kem_y_dinh(db, tmp_path, monkeypatch):
    """Số hiệu + ý định ("mức phạt") không phải 'Mở toàn văn' mà trả mọi đơn vị của văn bản: refs không được phình theo."""
    _nap(db, tmp_path, "20/2020", n_dieu=200)
    c = _client(tmp_path, monkeypatch)
    r = _ask(c, "20/2020/NĐ-CP mức phạt")
    res = _bot(db, int(r.headers["X-Conversation-Id"]))
    assert res["intent"] == "muc_phat" and res["n_ids"] > conversations.REFS_MAX >= len(res["refs"]) > 0


# ---- P1 H3: mở lại cuộc trò chuyện (GET /c/{id}, GET /c/{id}/m/{mid}) ----

def _hoi(c, *qs, **filters):
    """Hỏi lần lượt bằng POST /ask thật vào cùng một cuộc; trả (id cuộc, các mảnh HTML trả về)."""
    cid, out = None, []
    for q in qs:
        r = _ask(c, q, cid, **filters)
        cid = int(r.headers["X-Conversation-Id"])
        out.append(r.text)
    return cid, out


def _sub(html):
    return re.search(r'<p class="sub">(.*?)</p>', html)[1]


def _hrefs(html):
    return re.findall(r'class="addr" href="([^"]+)"', html)


def _hai_van_ban(db, tmp_path):
    """Hai văn bản có từ riêng: "kiểm toán nội bộ" chỉ ở A, "lưu trữ hồ sơ" chỉ ở B."""
    a = _nap(db, tmp_path, "15/2020", noi="Đơn vị phải kiểm toán nội bộ")
    b = _nap(db, tmp_path, "16/2020", noi="Cơ sở phải lưu trữ hồ sơ")
    return a, b


def _lam_hong(db, ref):
    db.execute("UPDATE units SET raw_text = raw_text || ' chữ mới' WHERE doc_id = ? AND path = ?", (ref[0], ref[1]))
    db.commit()


def test_mo_lai_khong_tim_lai_du_muc(db, tmp_path, monkeypatch):
    _hai_van_ban(db, tmp_path)
    c = _client(tmp_path, monkeypatch)
    cid, htmls = _hoi(c, "kiểm toán nội bộ", "lưu trữ hồ sơ")
    monkeypatch.setattr(appmod, "cascade_search", lambda *a, **k: pytest.fail("mở lại không được tìm lại"))
    r = c.get(f"/c/{cid}", follow_redirects=False)
    assert r.status_code == 200 and "<h1>kiểm toán nội bộ</h1>" in r.text  # tên cuộc là câu đầu
    assert r.text.count('class="msg bot"') == 2 and r.text.count('<form class="res"') == 2
    assert r.text.count('<div class="bubble">') == 2 and "không còn đúng nguồn" not in r.text
    assert _hrefs(r.text) == _hrefs(htmls[0]) + _hrefs(htmls[1]) and len(_hrefs(htmls[0])) > 1  # cùng mục, cùng thứ tự
    assert re.fullmatch(r"\d\d/\d\d/\d{4}, \d\d:\d\d · 2 câu hỏi", _sub(r.text))  # Normal: không ghi "tìm theo nghĩa", không ghi "Advance"
    assert f'data-cid="{cid}"' in r.text  # JS ghi tiếp vào đúng cuộc này


def test_mo_lai_van_dung_sau_rebuild_document(db, tmp_path, monkeypatch):
    d1 = _nap(db, tmp_path, "15/2020", noi="Đơn vị phải kiểm toán nội bộ")
    _nap(db, tmp_path, "16/2020", noi="Cơ sở phải lưu trữ hồ sơ")  # nạp muộn hơn: không có nó thì id đơn vị của d1 không đổi
    c = _client(tmp_path, monkeypatch)
    cid, (truoc,) = _hoi(c, "kiểm toán nội bộ")
    cu = _unit_ids(db, d1)
    rebuild_document(db, d1)
    moi = _unit_ids(db, d1)
    assert set(cu).isdisjoint(moi)  # id đơn vị đã đổi hết: ref chỉ còn tìm lại được bằng (doc_id, path)
    r = c.get(f"/c/{cid}")
    assert "không còn đúng nguồn" not in r.text and _hrefs(r.text) == _hrefs(truoc)
    uids = {int(u) for u in re.findall(r'name="uid" value="(\d+)"', r.text)}
    assert uids and uids <= set(moi)  # ô "Chọn xuất" mang id mới, không phải id đã chết


def test_mo_lai_hieu_luc_lay_tu_du_lieu_hien_tai(db, tmp_path, monkeypatch):
    d1 = _nap(db, tmp_path, "15/2020")
    c = _client(tmp_path, monkeypatch)
    cid, (truoc,) = _hoi(c, "báo cáo định kỳ")
    assert "Hết hiệu lực" not in truoc
    db.execute("UPDATE documents SET hieu_luc = 'het' WHERE id = ?", (d1,))
    db.commit()
    assert "Hết hiệu lực" in c.get(f"/c/{cid}").text  # không lưu thẻ dựng sẵn


def test_mo_lai_ref_hong_co_dai_canh_bao_theo_tung_tin(db, tmp_path, monkeypatch):
    _hai_van_ban(db, tmp_path)
    c = _client(tmp_path, monkeypatch)
    cid, _ = _hoi(c, "kiểm toán nội bộ", "lưu trữ hồ sơ", loai="nghi_dinh")
    rows = db.execute("SELECT result_json FROM messages WHERE conversation_id = ? AND role = 'bot' ORDER BY id", (cid,)).fetchall()
    res = json.loads(rows[1][0])
    n = len(res["refs"])
    for ref in res["refs"][:2]:
        _lam_hong(db, ref)
    r = c.get(f"/c/{cid}")
    assert r.text.count("không còn đúng nguồn") == 1  # chỉ tin thứ hai
    assert f"<b>2/{n} kết quả không còn đúng nguồn</b> vì văn bản đã nạp lại hoặc xoá. Hãy hỏi lại để có kết quả mới." in r.text
    assert 'data-ask="lưu trữ hồ sơ"' in r.text and ">Hỏi lại</button>" in r.text
    assert json.loads(re.search(r"data-filters='([^']*)'", r.text)[1]) == res["filters"]  # hỏi lại giữ bộ lọc của tin đó
    assert "Đang lọc" in r.text and 'class="card' in r.text  # ref còn lại vẫn hiện
    assert r.text.index("không còn đúng nguồn") > r.text.rindex('<div class="bubble">')  # dải nằm ở đầu câu trả lời của tin hỏng


def test_mo_lai_het_ref_chi_con_dai_canh_bao(db, tmp_path, monkeypatch):
    _nap(db, tmp_path, "15/2020")
    c = _client(tmp_path, monkeypatch)
    cid, _ = _hoi(c, "báo cáo định kỳ")
    refs = _bot(db, cid)["refs"]
    db.execute("UPDATE units SET raw_text = raw_text || ' đổi'")  # nạp lại mà chữ đổi hết
    db.commit()
    r = c.get(f"/c/{cid}")
    assert f"<b>{len(refs)}/{len(refs)} kết quả không còn đúng nguồn</b>" in r.text
    assert 'class="card' not in r.text and "Không tìm thấy đoạn nào" not in r.text  # không nói "không tìm thấy" bên cạnh dải này


def test_mo_lai_cau_khong_ra_ket_qua_van_hien_nhu_luc_hoi(db, tmp_path, monkeypatch):
    _nap(db, tmp_path, "15/2020")
    c = _client(tmp_path, monkeypatch)
    cid, _ = _hoi(c, "xyzzy quux")
    r = c.get(f"/c/{cid}")
    assert "Không tìm thấy đoạn nào khớp «xyzzy quux»" in r.text and "không còn đúng nguồn" not in r.text


def test_mo_lai_tin_toan_van(db, tmp_path, monkeypatch):
    d1 = _nap(db, tmp_path, "20/2020", n_dieu=12)
    c = _client(tmp_path, monkeypatch)
    cid, _ = _hoi(c, "20/2020/NĐ-CP")
    monkeypatch.setattr(appmod, "assemble_cards", lambda *a, **k: pytest.fail("kind = full không qua assemble_cards"))
    r = c.get(f"/c/{cid}")
    assert f'<a class="btn" href="/doc/{d1}" data-doc>Mở toàn văn</a>' in r.text and 'class="card' not in r.text
    db.execute("DELETE FROM documents WHERE id = ?", (d1,))
    db.commit()
    r = c.get(f"/c/{cid}")
    assert "<b>1/1 kết quả không còn đúng nguồn</b>" in r.text and "Mở toàn văn" not in r.text


def test_mo_lai_giu_nhan_khop_ro_chi_khi_the_dau_con_la_ref_dau(db, tmp_path, monkeypatch):
    _nap(db, tmp_path, "15/2020")
    c = _client(tmp_path, monkeypatch)
    cid, _ = _hoi(c, "báo cáo định kỳ")
    mid, raw = db.execute("SELECT id, result_json FROM messages WHERE conversation_id = ? AND role = 'bot'", (cid,)).fetchone()
    res = json.loads(raw)

    def dat(**kw):
        db.execute("UPDATE messages SET result_json = ? WHERE id = ?", (json.dumps({**res, **kw}, ensure_ascii=False), mid))
        db.commit()

    assert "Khớp rõ" not in c.get(f"/c/{cid}").text and "tìm theo nghĩa" not in _sub(c.get(f"/c/{cid}").text)  # Normal không chấm
    dat(refs=[[*res["refs"][0][:3], 7, 0, 0], *res["refs"][1:]])  # đoạn chỉ do vector tìm ra (tầng 7): cũng là Advance dù không có nhãn
    r = c.get(f"/c/{cid}")
    assert _sub(r.text).endswith("tìm theo nghĩa") and "Khớp rõ" not in r.text
    dat(sure=True)
    r = c.get(f"/c/{cid}")
    assert "Khớp rõ" in r.text and _sub(r.text).endswith("1 câu hỏi · tìm theo nghĩa")  # cuộc này đã tìm bằng Advance; không ghi tên chế độ
    dat(sure=False)
    assert "Chưa chắc chắn" in c.get(f"/c/{cid}").text
    _lam_hong(db, res["refs"][0])  # thẻ đầu không còn là ref đầu đã lưu: nhãn nói về cái khác
    r = c.get(f"/c/{cid}")
    assert "Chưa chắc chắn" not in r.text and "Khớp rõ" not in r.text and "không còn đúng nguồn" in r.text


def test_mo_lai_chi_dung_san_3_tin_gan_nhat_va_xem_lai_tung_tin(db, tmp_path, monkeypatch):
    _hai_van_ban(db, tmp_path)
    c = _client(tmp_path, monkeypatch)
    qs = ["kiểm toán nội bộ", "lưu trữ hồ sơ", "kiểm toán nội bộ lần 2", "lưu trữ hồ sơ lần 2", "kiểm toán nội bộ lần 3"]
    cid, htmls = _hoi(c, *qs)
    mids = [r[0] for r in db.execute("SELECT id FROM messages WHERE conversation_id = ? AND role = 'bot' ORDER BY id", (cid,))]
    goc, dem = appmod.assemble_cards, []
    monkeypatch.setattr(appmod, "assemble_cards", lambda *a, **k: (dem.append(1), goc(*a, **k))[1])
    r = c.get(f"/c/{cid}")
    assert len(dem) == 3 and r.text.count('<form class="res"') == 3  # chỉ 3 tin cuối được dựng
    assert re.findall(r'data-mid="(\d+)"', r.text) == [str(m) for m in mids[:2]] and r.text.count(">Xem lại</button>") == 2
    assert r.text.count('<div class="bubble">') == 5  # câu hỏi của tin cũ vẫn hiện
    dem.clear()
    f = c.get(f"/c/{cid}/m/{mids[0]}")
    assert f.status_code == 200 and len(dem) == 1 and _hrefs(f.text) == _hrefs(htmls[0]) and "<h1" not in f.text
    # tin hỏng thì mảnh "Xem lại" cũng mang dải cảnh báo
    _lam_hong(db, _bot(db, cid)["refs"][0])
    assert "không còn đúng nguồn" in c.get(f"/c/{cid}/m/{mids[4]}").text
    # cuộc có đúng 3 tin: dựng hết, không có nút
    cid3, _ = _hoi(c, *qs[:3])
    assert "data-mid" not in c.get(f"/c/{cid3}").text


def test_mo_lai_id_la(db, tmp_path, monkeypatch):
    _nap(db, tmp_path, "15/2020")
    c = _client(tmp_path, monkeypatch)
    cid, _ = _hoi(c, "báo cáo định kỳ")
    cid2, _ = _hoi(c, "lưu trữ hồ sơ")
    r = c.get("/c/9999", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/"
    assert c.get("/c/99999999999999999999").status_code == 404  # quá cỡ số nguyên SQLite: như các route khác, không 500
    ids = [(r[0], r[1]) for r in db.execute("SELECT id, role FROM messages WHERE conversation_id = ? ORDER BY id", (cid,))]
    user_mid, bot_mid = ids[0][0], ids[1][0]
    assert c.get(f"/c/{cid}/m/{bot_mid}").status_code == 200
    assert c.get(f"/c/{cid}/m/{user_mid}").status_code == 404  # tin người dùng không có kết quả
    assert c.get(f"/c/{cid2}/m/{bot_mid}").status_code == 404  # tin của cuộc khác
    assert c.get(f"/c/{cid}/m/9999").status_code == 404


def test_mo_lai_mang_csrf_token_that_khi_tat_bypass(db, tmp_path, monkeypatch):
    _nap(db, tmp_path, "15/2020")
    c = _client(tmp_path, monkeypatch)
    cid, _ = _hoi(c, "báo cáo định kỳ")
    monkeypatch.delenv("SOILUAT_ALLOW_TEST_HOST")
    h = {"Host": "127.0.0.1:8000"}
    r = c.get(f"/c/{cid}", headers=h)
    assert f'name="csrf_token" value="{appmod.CSRF_TOKEN}"' in r.text  # không rỗng: "Xuất Word" trong cuộc cũ không ra 403
    uid = re.search(r'name="uid" value="(\d+)"', r.text)[1]
    assert c.post("/export", headers=h, data={"uid": uid, "csrf_token": appmod.CSRF_TOKEN}).status_code == 200
    f = c.get(f"/c/{cid}/m/{db.execute('SELECT MIN(id) FROM messages WHERE role = ?', ('bot',)).fetchone()[0]}", headers=h)
    assert f'name="csrf_token" value="{appmod.CSRF_TOKEN}"' in f.text


def test_mo_lai_thoat_html_cau_hoi_va_ten_cuoc(db, tmp_path, monkeypatch):
    _nap(db, tmp_path, "15/2020")
    c = _client(tmp_path, monkeypatch)
    q = "báo cáo <img src=x onerror=alert(1)> \"định\" 'kỳ'"
    cid, _ = _hoi(c, q, "báo cáo", "định kỳ", "lưu trữ")  # câu đầu thành tên cuộc và tin cũ ("Xem lại")
    first, raw = db.execute("SELECT id, result_json FROM messages WHERE conversation_id = ? AND role = 'bot' ORDER BY id", (cid,)).fetchone()
    refs = json.loads(raw)["refs"]
    assert refs
    for ref in refs[:1]:
        _lam_hong(db, ref)
    for page in (c.get(f"/c/{cid}").text, c.get(f"/c/{cid}/m/{first}").text):
        assert "<img src=x" not in page
    assert "<h1>báo cáo &lt;img src=x onerror=alert(1)&gt;" in c.get(f"/c/{cid}").text
    f = c.get(f"/c/{cid}/m/{first}")
    assert "không còn đúng nguồn" in f.text
    assert html.unescape(re.search(r'data-ask="([^"]*)"', f.text)[1]) == q  # nút "Hỏi lại" gửi đúng chữ đã hỏi


def test_mo_lai_ghi_de_tep_bang_van_ban_khac_cung_id_bao_hong_het(db, tmp_path, monkeypatch):
    """D1 soát: ghi đè đúng tệp bằng văn bản khác rồi nạp lại giữ nguyên documents.id; Điều chỉ có tiêu đề ("Báo cáo lần 1")
    y hệt nhau giữa hai văn bản, nên chỉ băm chữ thì ref Điều vẫn "hợp lệ" và hiện Điều của văn bản mới như kết quả cũ."""
    d1 = _nap(db, tmp_path, "15/2020")
    c = _client(tmp_path, monkeypatch)
    cid, _ = _hoi(c, "báo cáo lần 1")
    n = len(_bot(db, cid)["refs"])
    assert n > 1
    p = tmp_path / "15-2020.txt"
    p.write_text(_nd("99/2026", noi="Nội dung khác hẳn"), encoding="utf-8")
    assert ingest_path(db, p, tmp_path) == d1  # id văn bản (và id đơn vị cũ) được dùng lại
    r = c.get(f"/c/{cid}")
    assert f"<b>{n}/{n} kết quả không còn đúng nguồn</b>" in r.text and 'class="card' not in r.text


def _viet_lai(db, tmp_path, doc_id, so, **kw):
    p = tmp_path / (so.replace("/", "-") + ".txt")
    p.write_text(_nd(so, **kw), encoding="utf-8")
    rebuild_document_from_file(db, doc_id, p, relative_path(p, tmp_path), sha256_file(p))


def test_mo_lai_toan_van_dieu_vang_nay_da_co_thi_bao_hoi_lai(db, tmp_path, monkeypatch):
    """D2 soát: tin "Số hiệu + Điều 7" dựng ra "không có Điều 7"; nạp lại bản đủ hơn (nay có Điều 7) thì mở lại không được
    khẳng định câu cũ, mà hiện dải "Hỏi lại". Trước khi nạp lại thì giữ nguyên câu cũ."""
    d1 = _nap(db, tmp_path, "20/2020", n_dieu=4)
    c = _client(tmp_path, monkeypatch)
    cid, (truoc,) = _hoi(c, "20/2020/NĐ-CP Điều 7")
    assert _bot(db, cid)["kind"] == "full" and "không có Điều 7" in truoc
    r = c.get(f"/c/{cid}")
    assert "không có Điều 7" in r.text and "không còn đúng nguồn" not in r.text
    _viet_lai(db, tmp_path, d1, "20/2020", n_dieu=8)
    r = c.get(f"/c/{cid}")
    assert "<b>1/1 kết quả không còn đúng nguồn</b>" in r.text and 'data-ask="20/2020/NĐ-CP Điều 7"' in r.text
    assert "không có Điều 7" not in r.text and "Mở toàn văn" not in r.text


def test_mo_lai_toan_van_van_ban_khac_chiem_id_thi_bao_hong(db, tmp_path, monkeypatch):
    """D3 soát: id văn bản bị văn bản khác dùng lại; ref mức văn bản chỉ kiểm id còn thì không có dải cảnh báo, còn phần
    kết quả (dựng từ chữ câu hỏi) rỗng và nói "không tìm thấy" như chưa từng có."""
    d1 = _nap(db, tmp_path, "20/2020")
    c = _client(tmp_path, monkeypatch)
    cid, _ = _hoi(c, "20/2020/NĐ-CP")
    db.execute("DELETE FROM documents WHERE id = ?", (d1,))
    db.commit()
    assert _nap(db, tmp_path, "77/2026") == d1
    r = c.get(f"/c/{cid}")
    assert "<b>1/1 kết quả không còn đúng nguồn</b>" in r.text and "Không tìm thấy đoạn nào" not in r.text


def test_mo_lai_toan_van_nap_lai_id_moi_chi_con_dai_canh_bao(db, tmp_path, monkeypatch):
    """D3 soát: xoá rồi nạp lại cùng văn bản với id mới: ref hỏng (dải 1/1), nên thẻ của văn bản mới không được hiện bên
    dưới (tự mâu thuẫn); "Hỏi lại" mới ra văn bản mới."""
    d1 = _nap(db, tmp_path, "20/2020")
    _nap(db, tmp_path, "16/2020")  # chiếm id kế tiếp: văn bản nạp lại không nhận lại id cũ
    c = _client(tmp_path, monkeypatch)
    cid, _ = _hoi(c, "20/2020/NĐ-CP")
    db.execute("DELETE FROM documents WHERE id = ?", (d1,))
    db.commit()
    d3 = _nap(db, tmp_path, "20/2020")
    assert d3 != d1
    r = c.get(f"/c/{cid}")
    assert "<b>1/1 kết quả không còn đúng nguồn</b>" in r.text and "Mở toàn văn" not in r.text and f"/doc/{d3}" not in r.text
    assert f"/doc/{d3}" in _ask(c, "20/2020/NĐ-CP", cid).text  # hỏi lại ra văn bản mới


def test_ten_trang_theo_ten_cuoc(db, tmp_path, monkeypatch):
    """UX-6 soát: tên trang (lịch sử trình duyệt, thanh tác vụ, trình đọc màn hình) là tên cuộc đang mở."""
    _nap(db, tmp_path, "15/2020")
    c = _client(tmp_path, monkeypatch)
    cid, _ = _hoi(c, "báo cáo <b>định</b> kỳ")
    assert "<title>báo cáo &lt;b&gt;định&lt;/b&gt; kỳ · Soi Luật</title>" in c.get(f"/c/{cid}").text
    assert "<title>Soi Luật</title>" in c.get("/").text


# ---- P1 H4: thanh bên (lịch sử theo nhóm, tìm, đổi tên, xoá) ----

UTC7 = timezone(timedelta(hours=7))


def _cuoc(db, title, updated, hoi=()):
    """Chèn thẳng một cuộc (updated_at tuỳ ý) kèm các câu hỏi của người dùng."""
    cid = db.execute("INSERT INTO conversations(title, created_at, updated_at) VALUES (?, ?, ?)", (title, updated, updated)).lastrowid
    db.executemany("INSERT INTO messages(conversation_id, role, text, created_at) VALUES (?, 'user', ?, ?)", [(cid, q, updated) for q in hoi])
    db.commit()
    return cid


def _nav(page):
    return re.search(r'<nav class="hist".*?</nav>', page, re.S)[0]


def _ids_ls(client, **params):
    return re.findall(r'<a href="/c/(\d+)"', client.get("/history", params=params).text)


def test_nhom_theo_ngay_dia_phuong_khong_theo_utc():
    nhom = conversations.nhom
    now = "2026-10-31T10:00:00+00:00"  # 17:00 ngày 31/10 giờ Việt Nam
    assert nhom("2026-10-30T17:30:00+00:00", now, UTC7) == "Hôm nay"  # 00:30 ngày 31/10 giờ VN, ngày UTC lại là 30/10
    assert nhom("2026-10-30T16:59:00+00:00", now, UTC7) == "7 ngày qua"  # 23:59 ngày 30/10 giờ VN
    # quanh nửa đêm: 00:10 ngày 31/10 giờ VN, tin 23:50 hôm trước (20 phút trước) đã sang nhóm "7 ngày qua"
    gan = "2026-10-30T17:10:00+00:00"
    assert nhom("2026-10-30T17:05:00+00:00", gan, UTC7) == "Hôm nay"
    assert nhom("2026-10-30T16:50:00+00:00", gan, UTC7) == "7 ngày qua"
    assert nhom("2026-10-24T05:00:00+00:00", now, UTC7) == "7 ngày qua"  # ngày 24/10 cách 7 ngày
    assert nhom("2026-10-23T05:00:00+00:00", now, UTC7) == "Cũ hơn"  # cách 8 ngày
    assert nhom("2026-11-05T00:00:00+00:00", now, UTC7) == "Hôm nay"  # đồng hồ máy lùi: không rơi khỏi các nhóm
    assert nhom("2026-10-31T09:00:00+00:00", datetime(2026, 10, 31, 10, tzinfo=timezone.utc), UTC7) == "Hôm nay"  # now cũng nhận datetime
    assert nhom(now, now) == "Hôm nay"  # mặc định giờ máy: cùng một lúc thì luôn cùng ngày


def test_lich_su_nhom_theo_ngay_moi_nhat_truoc_va_bo_nhom_rong(db, tmp_path, monkeypatch):
    now = datetime.now(timezone.utc)

    def iso(**d):
        return (now - timedelta(**d)).isoformat(timespec="seconds")

    c = _client(tmp_path, monkeypatch)
    assert "Chưa có cuộc trò chuyện nào." in _nav(c.get("/").text) and "<h2>" not in _nav(c.get("/").text)
    cu = _cuoc(db, "Cũ nhất", iso(days=30))
    assert re.findall(r"<h2>(.*?)</h2>", _nav(c.get("/").text)) == ["Cũ hơn"]  # nhóm rỗng không hiện tiêu đề
    ba = _cuoc(db, "Ba ngày trước", iso(days=3))
    mot = _cuoc(db, "Hôm nay một", iso())
    hai = _cuoc(db, "Hôm nay hai", iso())  # cùng giây với "một": id lớn hơn lên trước
    nav = _nav(c.get("/").text)
    assert re.findall(r"<h2>(.*?)</h2>", nav) == ["Hôm nay", "7 ngày qua", "Cũ hơn"]
    assert re.findall(r'<a href="/c/(\d+)"', nav) == [str(hai), str(mot), str(ba), str(cu)]


def test_lich_su_tim_khong_dau_theo_ten_va_cau_hoi(db, tmp_path, monkeypatch):
    a = _cuoc(db, "Mức phạt ma túy", T0, ["mức phạt ma túy", "tàng trữ trái phép"])
    b = _cuoc(db, "Báo cáo định kỳ", T1, ["báo cáo định kỳ", "lưu trữ hồ sơ"])
    c = _client(tmp_path, monkeypatch)
    assert _ids_ls(c, q="ma tuy") == [str(a)]  # không dấu thấy có dấu
    assert _ids_ls(c, q="  MA TÚY ") == [str(a)]
    assert _ids_ls(c, q="phat tuy") == [str(a)]  # các từ không cần liền nhau
    assert _ids_ls(c, q="luu tru ho so") == [str(b)]  # tìm cả câu hỏi bên trong cuộc, không chỉ tên
    assert _ids_ls(c, q="") == [str(b), str(a)] == _ids_ls(c)
    r = c.get("/history", params={"q": "<b>không</b>"})
    assert 'class="hrow' not in r.text and "Không có cuộc nào khớp “&lt;b&gt;không&lt;/b&gt;”." in r.text
    assert "<html" not in r.text  # mảnh cho nav, không phải cả trang


def test_lich_su_chi_hien_cuoc_moi_nhat_kem_dong_con_lai(db, tmp_path, monkeypatch):
    """D4 soát: 5.000 cuộc làm GET / và GET /history nặng ~2,7 MB mỗi lần: hiện tối đa HIST_MAX cuộc mới nhất, nói rõ còn bao
    nhiêu cuộc chưa hiện (cả khi tìm), cuộc cũ vẫn tới được bằng ô tìm."""
    n, now = conversations.HIST_MAX + 5, datetime.now(timezone.utc)
    db.executemany("INSERT INTO conversations(title, created_at, updated_at) VALUES (?, ?, ?)",
                   [(f"Cuộc số {i:03d}", t, t) for i in range(n) for t in [(now - timedelta(minutes=i)).isoformat(timespec="seconds")]])
    db.commit()
    c = _client(tmp_path, monkeypatch)
    for page in (_nav(c.get("/").text), c.get("/history").text, c.get("/history", params={"q": "cuoc so"}).text):
        assert page.count('class="hrow') == conversations.HIST_MAX
        assert "Cuộc số 000" in page and f"Cuộc số {n - 1:03d}" not in page  # giữ cuộc mới nhất
        assert "Còn 5 cuộc cũ hơn chưa hiện. Gõ vào ô tìm để thu hẹp." in page
    cu = c.get("/history", params={"q": f"cuoc so {n - 1:03d}"}).text
    assert cu.count('class="hrow') == 1 and "chưa hiện" not in cu  # cuộc cũ nhất tìm được, không dòng "còn"


def test_thanh_ben_danh_dau_cuoc_dang_mo_va_co_loi_vao_ban_phim(db, tmp_path, monkeypatch):
    _nap(db, tmp_path, "15/2020")
    c = _client(tmp_path, monkeypatch)
    cid, _ = _hoi(c, "báo cáo <b>định</b> kỳ")
    cid2, _ = _hoi(c, "lưu trữ")
    page = c.get(f"/c/{cid}").text
    nav = _nav(page)
    assert f'<div class="hrow on" data-id="{cid}">' in nav and f'<div class="hrow" data-id="{cid2}">' in nav
    assert nav.count('aria-current="page"') == 1 and f'<a href="/c/{cid}" aria-current="page">' in nav
    assert "&lt;b&gt;định&lt;/b&gt;" in nav and "<b>định" not in nav
    # nút ⋯: tên đọc ra có tên cuộc, báo có menu; ô tìm có nhãn; thông báo kết quả tìm và toast là vùng trạng thái
    assert 'aria-label="Tác vụ cho “báo cáo &lt;b&gt;định&lt;/b&gt; kỳ”" aria-haspopup="menu" aria-expanded="false"' in nav
    assert re.search(r'<label class="hsearch"><span class="sr">Tìm trong lịch sử</span>.*?<input id="hq" type="search"', page, re.S)
    assert '<p class="sr" id="hist-status" role="status"' in page and 'class="toast" id="toast" role="status" aria-live="polite"' in page
    assert "hrow on" not in c.get("/").text and "hrow on" not in c.get("/", params={"q": "báo cáo"}).text  # không cuộc nào đang mở
    assert f'<div class="hrow on" data-id="{cid2}">' in c.get("/history", params={"cid": cid2}).text


def test_doi_ten(db, tmp_path, monkeypatch):
    cid = _cuoc(db, "Tên cũ", T0)
    c = _client(tmp_path, monkeypatch)

    def tieu_de():
        return db.execute("SELECT title FROM conversations WHERE id = ?", (cid,)).fetchone()[0]

    r = c.post(f"/c/{cid}/rename", data={"title": "  Mức   phạt\nma tuý "})
    assert r.status_code == 200 and r.json()["title"] == "Mức phạt ma tuý" == tieu_de()
    assert db.execute("SELECT updated_at FROM conversations WHERE id = ?", (cid,)).fetchone()[0] == T0  # đổi tên không đẩy cuộc lên đầu
    c.post(f"/c/{cid}/rename", data={"title": unicodedata.normalize("NFD", "Điều kiện")})
    assert tieu_de() == unicodedata.normalize("NFC", "Điều kiện")  # lưu dạng NFC như tiêu đề tự đặt
    for xau in ("", "   ", "\n", "x" * 81):
        assert c.post(f"/c/{cid}/rename", data={"title": xau}).status_code == 400, repr(xau)
    assert c.post(f"/c/{cid}/rename").status_code == 400  # thiếu trường
    assert tieu_de() == "Điều kiện"  # lần bị từ chối không đổi gì
    assert c.post(f"/c/{cid}/rename", data={"title": "x" * 80}).status_code == 200 and tieu_de() == "x" * 80


def test_xoa_cuoc_xoa_tin_giu_nhat_ky_truy_van(db, tmp_path, monkeypatch):
    _nap(db, tmp_path, "15/2020")
    c = _client(tmp_path, monkeypatch)
    cid, _ = _hoi(c, "báo cáo định kỳ", "lưu trữ hồ sơ")
    giu, _ = _hoi(c, "kiểm toán nội bộ")
    n_log = db.execute("SELECT COUNT(*) FROM query_log").fetchone()[0]
    assert n_log == 3 and db.execute("SELECT COUNT(*) FROM messages WHERE conversation_id = ?", (cid,)).fetchone()[0] == 4
    r = c.post(f"/c/{cid}/delete")
    assert r.status_code == 200 and r.json() == {"ok": True}
    assert db.execute("SELECT COUNT(*) FROM conversations WHERE id = ?", (cid,)).fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM messages WHERE conversation_id = ?", (cid,)).fetchone()[0] == 0  # cascade
    assert db.execute("SELECT COUNT(*) FROM query_log").fetchone()[0] == n_log  # câu hỏi còn trong nhật ký (trang "Truy vấn bỏ sót")
    assert db.execute("SELECT COUNT(*) FROM messages WHERE conversation_id = ?", (giu,)).fetchone()[0] == 2  # cuộc khác nguyên
    assert _ids_ls(c) == [str(giu)]
    assert c.get(f"/c/{cid}", follow_redirects=False).status_code == 303
    assert c.post(f"/c/{cid}/delete").status_code == 404  # tab khác đã xoá trước


@pytest.mark.parametrize("hanh_dong", ["rename", "delete"])
@pytest.mark.parametrize("cid", [9999, 99999999999999999999])  # số sau lớn hơn số nguyên SQLite
def test_doi_ten_va_xoa_id_la_ra_404(db, tmp_path, monkeypatch, hanh_dong, cid):
    ton_tai = _cuoc(db, "Còn", T0)
    c = _client(tmp_path, monkeypatch)
    assert c.post(f"/c/{cid}/{hanh_dong}", data={"title": "Mới"}).status_code == 404
    assert _ids_ls(c) == [str(ton_tai)]


class _Theo:
    """Kết nối bọc: đếm close() (Connection của sqlite3 không cho gán đè close trên đối tượng)."""

    def __init__(self, conn, log):
        self.c, self.log = conn, log

    def __getattr__(self, name):
        return getattr(self.c, name)

    def close(self):
        self.log.append("close")
        self.c.close()


def test_route_moi_dong_ket_noi_ca_khi_loi(db, tmp_path, monkeypatch):
    cid = _cuoc(db, "Tên", T0, ["hỏi"])
    c = _client(tmp_path, monkeypatch)
    goc, mo, dong = appmod.get_conn, [], []
    monkeypatch.setattr(appmod, "get_conn", lambda: (mo.append(1), _Theo(goc(), dong))[1])
    for method, url, data, status in (
        ("get", "/history?q=hoi", None, 200), ("get", f"/c/{cid}", None, 200),
        ("post", f"/c/{cid}/rename", {"title": "Mới"}, 200), ("post", "/c/9999/rename", {"title": "Mới"}, 404),
        ("post", "/c/99999999999999999999/delete", None, 404),  # OverflowError từ SQLite
        ("post", "/c/9999/delete", None, 404), ("post", f"/c/{cid}/delete", None, 200),
    ):
        before = len(mo)
        assert getattr(c, method)(url, **({"data": data} if data else {})).status_code == status, url
        assert len(mo) > before and len(dong) == len(mo), url  # mở bao nhiêu thì đóng bấy nhiêu


def test_doi_ten_va_xoa_khoa_ghi_ra_503_khong_500(db, tmp_path, monkeypatch):
    """Đang nạp file giữ khoá ghi: báo "thử lại sau" (503), không 500, không đổi gì; hết khoá thì làm được."""
    cid = _cuoc(db, "Tên cũ", T0)
    c = _client(tmp_path, monkeypatch)
    goc = appmod.get_conn
    dong = []

    def nhanh():  # chờ khoá 0,3 s cho nhanh; đường mã giống hệt chờ 5 s thật
        conn = goc()
        conn.execute("PRAGMA busy_timeout=300")
        return _Theo(conn, dong)

    monkeypatch.setattr(appmod, "get_conn", nhanh)
    giu = connect(tmp_path / "soiluat.db")
    giu.execute("BEGIN IMMEDIATE")
    try:
        assert c.post(f"/c/{cid}/rename", data={"title": "Tên mới"}).status_code == 503
        assert c.post(f"/c/{cid}/delete").status_code == 503
    finally:
        giu.rollback()
        giu.close()
    assert dong == ["close", "close"]
    assert db.execute("SELECT title FROM conversations WHERE id = ?", (cid,)).fetchone()[0] == "Tên cũ"
    assert c.post(f"/c/{cid}/rename", data={"title": "Tên mới"}).status_code == 200


def test_xoa_dung_hop_thoai_dung_chung_khong_confirm():
    """Kế hoạch H4: hộp thoại xác nhận và toast tự dựng (như mẫu), không `confirm()` của trình duyệt."""
    js = (Path(appmod.__file__).parent / "static" / "app.js").read_text(encoding="utf-8")
    assert not re.search(r"(?<![\w.])confirm\(", js) and "function dialog(" in js and "function toast(" in js


# ---- P1 H6: CSRF và Host cho mọi POST mới (conftest bật bypass nên mỗi test phải tắt) ----

POST_MOI = {  # tên ca: cid -> (đường dẫn, form)
    "ask": lambda cid: ("/ask", {"q": "báo cáo", "conversation_id": str(cid)}),
    "rename": lambda cid: (f"/c/{cid}/rename", {"title": "Mới"}),
    "delete": lambda cid: (f"/c/{cid}/delete", {}),
}


def _luu(db):
    return [tuple(r) for t in ("conversations", "messages", "query_log") for r in db.execute(f"SELECT * FROM {t} ORDER BY 1")]


@pytest.mark.parametrize("hanh_dong", POST_MOI)
def test_post_moi_csrf_va_host_khi_tat_bypass(db, tmp_path, monkeypatch, hanh_dong):
    _nap(db, tmp_path, "15/2020")
    cids = [_cuoc(db, "Tên cũ", T0), _cuoc(db, "Tên cũ", T0)]
    c = _client(tmp_path, monkeypatch)
    monkeypatch.delenv("SOILUAT_ALLOW_TEST_HOST")
    h = {"Host": "127.0.0.1:8000"}
    token = c.get("/", headers=h).cookies.get("soiluat_csrf")
    assert token == appmod.CSRF_TOKEN
    url, data = POST_MOI[hanh_dong](cids[0])
    truoc = _luu(db)
    for gui in (
        c.post(url, headers=h, data=data),  # có cookie, thiếu token
        c.post(url, headers={**h, "X-CSRF-Token": "sai"}, data=data),
        c.post(url, headers=h, data={**data, "csrf_token": "sai"}),
        TestClient(appmod.app).post(url, headers={**h, "X-CSRF-Token": token}, data=data),  # token đúng nhưng không có cookie
    ):
        assert gui.status_code == 403
    for host in ("evil.example", "localhost.evil.example", "127.0.0.1.evil.example:8000"):
        assert c.post(url, headers={"Host": host, "X-CSRF-Token": token}, data=data).status_code == 400
        assert c.get("/history", headers={"Host": host}).status_code == 400
    assert _luu(db) == truoc  # mọi lần bị từ chối không ghi gì
    r = c.post(url, headers={**h, "X-CSRF-Token": token}, data=data)  # token ở header như post() của JS
    assert r.status_code == 200 and (hanh_dong != "ask" or "X-Conversation-Id" in r.headers)
    sau = _luu(db)
    assert sau != truoc
    url, data = POST_MOI[hanh_dong](cids[1])
    assert c.post(url, headers=h, data={**data, "csrf_token": token}).status_code == 200  # hoặc token trong form
    assert _luu(db) != sau


@pytest.mark.parametrize("hanh_dong", POST_MOI)
def test_post_moi_khoi_dong_lai_token_cu_403_kem_cookie_moi_roi_token_moi_200(db, tmp_path, monkeypatch, hanh_dong):
    """App khởi động lại khi trang cũ còn mở (CSRF_TOKEN đổi): token cũ ra 403 và chính phản hồi đó đặt cookie mới,
    nên post() của JS gửi lại với token mới là qua, không cần GET."""
    cid = _cuoc(db, "Tên cũ", T0)
    c = _client(tmp_path, monkeypatch)
    monkeypatch.delenv("SOILUAT_ALLOW_TEST_HOST")
    h = {"Host": "127.0.0.1:8000"}
    cu = c.get("/", headers=h).cookies.get("soiluat_csrf")
    monkeypatch.setattr(appmod, "CSRF_TOKEN", "token-sau-khi-khoi-dong-lai")
    url, data = POST_MOI[hanh_dong](cid)
    truoc = _luu(db)
    r = c.post(url, headers={**h, "X-CSRF-Token": cu}, data=data)
    assert r.status_code == 403 and f"soiluat_csrf={appmod.CSRF_TOKEN}" in r.headers["set-cookie"]
    assert _luu(db) == truoc
    assert c.cookies.get("soiluat_csrf") == appmod.CSRF_TOKEN  # JS đọc đúng cookie này (cookieToken)
    assert c.post(url, headers={**h, "X-CSRF-Token": appmod.CSRF_TOKEN}, data=data).status_code == 200
    assert _luu(db) != truoc
