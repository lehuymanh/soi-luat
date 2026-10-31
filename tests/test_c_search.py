"""Agent C: L16–L20, H4 (fold), H6 (Card)."""

from soiluat.cards import assemble_cards
from soiluat.db import connect, init_schema, seed_synonyms
from soiluat.fold import dieu_path, fold_search, pretty_path, search_accent
from soiluat.ingest import ingest_path
from soiluat.query import classify_query, split_intent, strip_question
from soiluat.search import _so_hieu_docs, _title_index, cascade_search, tokenize
from soiluat.sohieu import find_dieu_so


def _ingest(db, tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return ingest_path(db, p, tmp_path)


def _paths(db, ids):
    return [db.execute("SELECT path FROM units WHERE id = ?", (i,)).fetchone()["path"] for i in ids]


# ---------- L20: cache từ vựng ----------

def test_title_cache_refreshes_after_ingest(db, tmp_path):
    _ingest(db, tmp_path, "a.txt", "Nghị định số 1/2021/NĐ-CP\nĐiều 1. Lưu trữ hồ sơ\n1. Nội dung.\n")
    idx = _title_index(db, False)
    assert ("luu", "tru", "ho", "so") in [k for k, _ in idx["luu"]]
    assert _title_index(db, False) is idx  # cùng phiên bản: không đọc lại
    _ingest(db, tmp_path, "b.txt", "Nghị định số 2/2021/NĐ-CP\nĐiều 1. Niêm yết giá dịch vụ\n1. Nội dung.\n")
    # connection mới (như app mỗi request) vẫn thấy tên Điều vừa nạp
    conn2 = connect(tmp_path / "soiluat.db")
    try:
        idx2 = _title_index(conn2, False)
        assert idx2 is not idx
        assert tokenize("niem yet gia dich vu", indexes=[idx2]) == ["niem yet gia dich vu"]
    finally:
        conn2.close()


def test_tokenize_longest_phrase_and_iy():
    toks = tokenize("bao cao dinh ki quy", ["bao cao", "bao cao dinh ky"])
    assert toks == ["bao cao dinh ky", "quy"]


# ---------- L16: tầng khớp trước hạng ----------

def test_exact_phrase_card_before_loose_risk_card(db, tmp_path):
    _ingest(
        db, tmp_path, "rank.txt",
        "Nghị định số 3/2021/NĐ-CP\n"
        "Điều 1. Xử phạt\n"
        "1. Phạt tiền từ 1.000.000 đồng đến 2.000.000 đồng đối với hành vi không lập sổ, "
        "không theo dõi tài sản zzqx.\n"
        "Điều 2. Mẫu biểu\n"
        "1. Mẫu lập sổ theo dõi tài sản zzqx được ban hành kèm theo.\n",
    )
    r = cascade_search(db, "lập sổ theo dõi tài sản zzqx")
    cards = assemble_cards(db, r.ids, tiers=r.tiers, intent=r.intent)
    assert cards[0].match_tier == 1
    assert "Mẫu lập sổ" in cards[0].duty_text
    assert any(c.rank == 2 and c.match_tier > 1 for c in cards[1:])
    # không truyền tiers: giữ thứ tự cũ theo hạng (xuất Word)
    assert assemble_cards(db, r.ids)[0].rank == 2


def test_so_hieu_lookup_is_tier0(db, sample_doc):
    r = cascade_search(db, "15/2020/NĐ-CP")
    assert set(r.tiers.values()) == {0}
    cards = assemble_cards(db, r.ids, tiers=r.tiers)
    assert all(c.match_tier == 0 for c in cards)


# ---------- L17: mức phạt ----------

def test_split_intent():
    assert split_intent("mức phạt không đóng bảo hiểm xã hội") == ("muc_phat", "không đóng bảo hiểm xã hội")
    assert split_intent("muc phat khong dong bhxh") == ("muc_phat", "khong dong bhxh")
    assert split_intent("không nộp báo cáo bị phạt bao nhiêu?") == ("muc_phat", "không nộp báo cáo")
    assert split_intent("phat tien") == ("muc_phat", "phat tien")  # bỏ hết thì giữ nguyên
    assert split_intent("báo cáo định kỳ") == ("", "báo cáo định kỳ")


def test_muc_phat_puts_sanction_first(db, tmp_path):
    _ingest(
        db, tmp_path, "bhxh.txt",
        "Nghị định số 4/2021/NĐ-CP\n"
        "Điều 3. Trách nhiệm đóng\n"
        "1. Người sử dụng lao động phải đóng bảo hiểm xã hội bắt buộc qwv.\n"
        "Điều 4. Hồ sơ\n"
        "1. Hồ sơ đóng bảo hiểm xã hội bắt buộc qwv gồm tờ khai.\n"
        "Điều 9. Vi phạm về đóng bảo hiểm\n"
        "1. Phạt tiền từ 10.000.000 đồng đến 20.000.000 đồng đối với một trong các hành vi sau đây:\n"
        "a) Không đóng bảo hiểm xã hội bắt buộc qwv cho người lao động.\n",
    )
    r = cascade_search(db, "mức phạt không đóng bảo hiểm xã hội bắt buộc qwv")
    assert r.intent == "muc_phat"
    cards = assemble_cards(db, r.ids, tiers=r.tiers, intent=r.intent)
    top = cards[0]
    assert top.intent == "muc_phat"
    assert top.rank == 2
    assert "Điều 9" in (top.sanction_addr or top.duty_addr)
    assert top.sanction_text


# ---------- L18: từ điển seed + tầng 4 ----------

def test_seed_loaded_and_safe_rerun(db):
    n = db.execute("SELECT COUNT(*) FROM synonyms WHERE approved = 1 AND kind = 'viet_tat'").fetchone()[0]
    m = db.execute("SELECT COUNT(*) FROM synonyms WHERE approved = 0").fetchone()[0]
    assert n >= 40 and m >= 30
    db.execute("UPDATE synonyms SET approved = 1 WHERE term = 'xin cấp'")
    db.execute("DELETE FROM synonyms WHERE term = 'KKT'")
    db.commit()
    init_schema(db)
    seed_synonyms(db)
    assert db.execute("SELECT approved FROM synonyms WHERE term = 'xin cấp'").fetchone()[0] == 1
    assert db.execute("SELECT COUNT(*) FROM synonyms WHERE term = 'KKT'").fetchone()[0] == 0


def test_abbreviation_union_tier4(db, tmp_path):
    _ingest(
        db, tmp_path, "bh.txt",
        "Nghị định số 5/2021/NĐ-CP\nĐiều 2. Đóng bảo hiểm\n"
        "1. Doanh nghiệp phải đóng bảo hiểm xã hội bắt buộc hằng tháng.\n",
    )
    for q in ("đóng BHXH bắt buộc", "đóng bhxh", "dong BHXH", "Dong Bhxh bat buoc"):
        r = cascade_search(db, q)
        assert "D2.K1" in _paths(db, r.ids), q
        assert r.tiers[r.ids[0]] == 4, q
        assert r.note == "dong_nghia"


def test_abbreviation_reverse_multiword(db, tmp_path):
    _ingest(
        db, tmp_path, "pccc.txt",
        "Nghị định số 6/2021/NĐ-CP\nĐiều 7. Trang bị\n1. Cơ sở phải trang bị phương tiện PCCC đầy đủ.\n",
    )
    r = cascade_search(db, "trang bị phương tiện phòng cháy và chữa cháy")
    assert "D7.K1" in _paths(db, r.ids)


# ---------- L19: câu hỏi ----------

def test_strip_question_frames_and_subject():
    assert classify_query("tổ chức tín dụng có phải báo cáo định kỳ không?") == "question"
    assert strip_question("tổ chức tín dụng có phải báo cáo định kỳ không?") == "báo cáo định kỳ"
    assert strip_question("quy định về việc kê khai thuế như thế nào?") == "kê khai thuế"
    assert strip_question("to chuc tin dung co phai bao cao khong") == "bao cao"
    assert strip_question("thời hạn nộp hồ sơ là bao lâu") == "thời hạn nộp hồ sơ"
    # "không" giữa câu là phủ định, giữ lại
    assert strip_question("doanh nghiệp không nộp báo cáo thì sao?") .startswith("doanh nghiệp không nộp")
    # bỏ chủ ngữ mà không còn gì thì giữ chủ ngữ
    assert strip_question("ngân hàng có phải không?") == "ngân hàng"


# ---------- H4: đường dẫn ----------

def test_pretty_and_dieu_path_with_suffix():
    assert pretty_path("D5~2.K1") == "Điều 5 (lần 2) khoản 1"
    assert pretty_path("D1.K1~2") == "Điều 1 khoản 1 (lần 2)"
    assert pretty_path("D1.K1~2.Đa~2") == "Điều 1 khoản 1 (lần 2) điểm a (lần 2)"
    assert pretty_path("D12.K1.Đa") == "Điều 12 khoản 1 điểm a"
    assert pretty_path("GC3") == "ghi chú 3"
    assert pretty_path("p2.para3") == "trang 2 đoạn 3"
    assert dieu_path("D5~2.K1") == "D5~2"
    assert dieu_path("D1.K1~2.Đa~2") == "D1"
    assert dieu_path("D5.K1") == "D5"
    assert dieu_path("GC3", "ghi_chu") == "GC3"


def test_dieu_lookup_includes_duplicate_number(db, sample_doc):
    dieu = db.execute("SELECT id FROM units WHERE doc_id = ? AND path = 'D5'", (sample_doc,)).fetchone()["id"]
    db.execute(
        "INSERT INTO units(doc_id, parent_id, path, level, title, title_search, raw_text, normalized_text, "
        "search_accent, search_text, extraction_method, verification_status) "
        "VALUES (?, NULL, 'D5~2', 'dieu', 'Báo cáo bổ sung', ?, 'x', 'x', 'x', 'x', 'txt', 'chua')",
        (sample_doc, fold_search("Báo cáo bổ sung")),
    )
    db.commit()
    r = cascade_search(db, "Điều 5 15/2020/NĐ-CP")
    paths = set(_paths(db, r.ids))
    assert "D5~2" in paths and any(p.startswith("D5.") or p == "D5" for p in paths)
    assert dieu


# ---------- H6: ghi chú, trang ----------

def _add_note(db, doc_id, parent_id, path, text):
    db.execute(
        "INSERT INTO units(doc_id, parent_id, path, level, title, title_search, raw_text, normalized_text, "
        "search_accent, search_text, page_from, page_to, extraction_method, verification_status) "
        "VALUES (?, ?, ?, 'ghi_chu', '', '', ?, ?, ?, ?, 2, 2, 'txt', 'chua')",
        (doc_id, parent_id, path, text, text, search_accent(text), fold_search(text)),
    )
    db.commit()


def test_ghi_chu_hit_grouped_with_parent_and_notes(db, sample_doc):
    k1 = db.execute("SELECT id FROM units WHERE doc_id = ? AND path = 'D5.K1'", (sample_doc,)).fetchone()["id"]
    _add_note(db, sample_doc, k1, "GC1", "Chú thích: áp dụng cả chi nhánh ngân hàng nước ngoài ghichuxyz.")
    r = cascade_search(db, "ghichuxyz")
    cards = assemble_cards(db, r.ids, tiers=r.tiers)
    assert len(cards) == 1
    c = cards[0]
    assert c.rank == 4
    assert c.title == "Báo cáo định kỳ"  # gom theo Điều cha
    assert any("ghichuxyz" in n for n in c.notes)
    assert c.page_from == 2 and c.page_to == 2
    # thẻ Điều 5 tìm bằng từ khác vẫn mang ghi chú
    r2 = cascade_search(db, "báo cáo định kỳ")
    d5 = [c for c in assemble_cards(db, r2.ids, tiers=r2.tiers) if c.title == "Báo cáo định kỳ"]
    assert d5 and d5[0].notes


def test_ghi_chu_without_parent_is_own_card(db, sample_doc):
    _add_note(db, sample_doc, None, "GC2", "Ghi chú đầu trang mocoparent.")
    r = cascade_search(db, "mocoparent")
    cards = assemble_cards(db, r.ids, tiers=r.tiers)
    assert len(cards) == 1 and cards[0].rank == 4
    assert "ghi chú 2" in cards[0].duty_addr


# ---------- Tra số hiệu và "Điều n" (đợt dọn mã 0.9.0: C5, C6/F5, C10) ----------

def _nd5_khoan(db, tmp_path):
    _ingest(
        db, tmp_path, "nd384.txt",
        "Nghị định số 384/2026/NĐ-CP\n"
        "Điều 5. Mức thu\n"
        "1. Mức một.\n"
        "2. Mức hai khoản nhắc khoản 2 và Điều 5 trong lời.\n"
        "a) Điểm a của khoản hai.\n"
        "3. Mức ba.\n"
        "Điều 6. Nộp\n"
        "1. Nộp tiền.\n",
    )


def test_c5_ngay_thang_khong_bi_doc_la_dau_so_hieu(db, tmp_path):
    from soiluat.sohieu import find_so_hieu_prefix
    _ingest(db, tmp_path, "tt02.txt", "Thông tư số 02/2021/TT-BTC\nĐiều 1. Lưu trữ\n1. Hồ sơ lưu trữ.\n")
    for q in ("hạn nộp hồ sơ trước ngày 05/02/2021", "hạn nộp trong tháng 10/2020", "ngày 5/2/2021"):
        assert find_so_hieu_prefix(q) is None, q
    assert find_so_hieu_prefix("15/2020") == "15/2020"
    assert find_so_hieu_prefix("Thông tư 15/2020 Điều 5") == "15/2020"
    assert _so_hieu_docs(db, "hạn nộp hồ sơ trước ngày 05/02/2021") == []  # không giới hạn kho vào Thông tư 02/2021


def test_c6_khoan_diem_trong_cau_trich_khong_thanh_tu_khoa(db, tmp_path):
    _nd5_khoan(db, tmp_path)
    goc = cascade_search(db, "Điều 5 384/2026/NĐ-CP")
    assert set(_paths(db, goc.ids)) >= {"D5", "D5.K1", "D5.K2", "D5.K2.Đa", "D5.K3"}
    for q in ("Khoản 2 Điều 5 Nghị định 384/2026/NĐ-CP", "384/2026/NĐ-CP Điều 5 khoản 2",
              "Điểm a khoản 2 Điều 5 384/2026/NĐ-CP", "điểm a, khoản 2, Điều 5 Nghị định số 384/2026/NĐ-CP"):
        r = cascade_search(db, q)
        assert r.note == "so_hieu" and sorted(r.ids) == sorted(goc.ids), q  # cả Điều 5, không khoản chỉ "nhắc" khoản 2
    # từ khoá thật đi kèm vẫn được tìm trong Điều
    assert cascade_search(db, "khoản 2 Điều 5 384/2026/NĐ-CP mức ba").ids


def test_c10_so_hieu_thieu_so_0_va_chu_cai_dieu_hoa_thuong(db, tmp_path):
    _ingest(db, tmp_path, "tt02.txt", "Thông tư số 02/2021/TT-BTC\nĐiều 1. Lưu trữ\n1. Hồ sơ.\n")
    assert cascade_search(db, "Thông tư 2/2021/TT-BTC").ids == cascade_search(db, "02/2021/TT-BTC").ids != []
    assert cascade_search(db, "2/2021").note == "so_hieu"
    _ingest(db, tmp_path, "luat30.txt", "Luật số 30/2022/QH15\nĐiều 1A. Bổ sung\n1. Nội dung bổ sung.\nĐiều 2. Hai\n1. Hai.\n")
    for q in ("Điều 1A", "Điều 1a"):
        r = cascade_search(db, q)
        assert "D1A" in _paths(db, r.ids), q
        r = cascade_search(db, f"30/2022/QH15 {q}")
        assert set(_paths(db, r.ids)) == {"D1A", "D1A.K1"}, q


def test_c10_cau_hoi_nfd_giong_nfc(db, tmp_path):
    import unicodedata
    _nd5_khoan(db, tmp_path)
    q = "Điều 5 Nghị định số 384/2026/NĐ-CP"
    nfd = unicodedata.normalize("NFD", q)
    assert nfd != q
    r = cascade_search(db, nfd)
    assert r.note == "so_hieu" and r.ids == cascade_search(db, q).ids != []
    assert find_dieu_so(nfd) == "5"


def test_f4_ocr_unit_ids_chi_duyet_van_ban_co_trang_ocr(db):
    from soiluat.search import _ocr_unit_ids

    def add_doc(did, ocr, status, n=200):
        db.execute("INSERT INTO documents(id, file_path, sha256, source_status, extraction_method) VALUES (?,?,?,?,?)",
                   (did, f"f{did}", f"s{did}", "x", "ocr" if ocr else "txt"))
        db.executemany(
            "INSERT INTO pages(doc_id, page_no, kind, extraction_method, ocr_status, verification_status) VALUES (?,?,?,?,?,?)",
            [(did, p, "scan", "ocr" if ocr else "pdf_text", status, "auto") for p in range(1, n + 1)])
        db.executemany(
            "INSERT INTO units(doc_id, path, level, raw_text, normalized_text, search_text, extraction_method, "
            "verification_status, page_from, page_to) VALUES (?,?,?,?,?,?,?,?,?,?)",
            [(did, f"D{u}", "dieu", "x", "x", "x", "txt", "auto", u, u) for u in range(1, n + 1)])

    add_doc(1, True, "chua_doi_chieu")
    add_doc(2, True, "da_doi_chieu", n=5)
    add_doc(3, False, "khong_can", n=5)
    db.commit()
    steps = [0]
    db.set_progress_handler(lambda: steps.__setitem__(0, steps[0] + 1) or 0, 1)
    ids = _ocr_unit_ids(db)
    db.set_progress_handler(None, 0)
    assert sorted(ids) == [r[0] for r in db.execute("SELECT id FROM units WHERE doc_id = 1 ORDER BY id")]
    assert steps[0] < 60_000  # theo số trang x số đơn vị của văn bản thì ~350.000 bước; duyệt từ đơn vị thì ~11.000
