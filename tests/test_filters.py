from soiluat.search import apply_doc_filters, cascade_search
from soiluat.sohieu import infer_co_quan, infer_loai


def test_infer_loai_and_co_quan():
    assert infer_loai("15/2020/NĐ-CP") == "nghi_dinh"
    assert infer_loai("12/2021/TT-NHNN") == "thong_tu"
    assert infer_co_quan("CỘNG HÒA\nCHÍNH PHỦ\nHà Nội") == "CHÍNH PHỦ"


def test_ingest_sets_loai_nghi_dinh(db, sample_doc):
    row = db.execute(
        "SELECT loai, so_hieu FROM documents WHERE id = ?", (sample_doc,)
    ).fetchone()
    assert row["loai"] == "nghi_dinh"
    assert "15/2020" in (row["so_hieu"] or "")


def test_filter_hieu_luc(db, sample_doc):
    ids, _, _ = cascade_search(db, "bao cao")
    assert ids
    empty = apply_doc_filters(db, ids, hieu_luc="con")
    assert empty == []
    same = apply_doc_filters(db, ids, hieu_luc="chua_ro")
    assert same == ids
    none = apply_doc_filters(db, ids, loai="thong_tu")
    assert none == []
    nd = apply_doc_filters(db, ids, loai="nghi_dinh")
    assert nd == ids


def test_loc_co_quan_khop_dung_gia_tri_khong_phai_chuoi_con(db, sample_doc, tmp_path):
    """Ô lọc là danh sách chọn gửi đúng giá trị lưu: 'CHÍNH PHỦ' không kéo theo 'THỦ TƯỚNG CHÍNH PHỦ'; % và _ không là ký tự đại diện."""
    from soiluat.ingest import ingest_path

    p = tmp_path / "ttg.txt"
    p.write_text("Quyết định số 48/2026/QĐ-TTg\nĐiều 1. Phạm vi\n1. Báo cáo định kỳ hằng năm.\n", encoding="utf-8")
    ttg = ingest_path(db, p, tmp_path)
    db.execute("UPDATE documents SET co_quan = 'CHÍNH PHỦ' WHERE id = ?", (sample_doc,))
    db.execute("UPDATE documents SET co_quan = 'THỦ TƯỚNG CHÍNH PHỦ' WHERE id = ?", (ttg,))
    db.commit()
    ids = [r[0] for r in db.execute("SELECT id FROM units ORDER BY id")]
    doc_of = {r[0]: r[1] for r in db.execute("SELECT id, doc_id FROM units")}
    kept = apply_doc_filters(db, ids, co_quan="CHÍNH PHỦ")
    assert kept and {doc_of[i] for i in kept} == {sample_doc}
    assert apply_doc_filters(db, ids, co_quan="%") == [] and apply_doc_filters(db, ids, co_quan="CHÍNH PHỦ_") == []


def _kho_loc(db, tmp_path):
    """150 Điều Nghị định khớp "báo cáo định kỳ" rất sát, và một Quyết định khớp yếu hơn (chữ loãng trong đoạn dài)."""
    from soiluat.ingest import ingest_path

    nd = "Nghị định số 15/2020/NĐ-CP ngày 01 tháng 01 năm 2020\n" + "".join(
        f"Điều {i}. Báo cáo định kỳ\n1. Báo cáo định kỳ hằng tháng.\n" for i in range(1, 151)
    )
    (tmp_path / "nd.txt").write_text(nd, encoding="utf-8")
    qd = ("Quyết định số 48/2026/QĐ-TTg\nĐiều 1. Phạm vi\n1. Việc báo cáo định kỳ " + "và các việc khác " * 30 + "thực hiện hằng năm.\n")
    (tmp_path / "qd.txt").write_text(qd, encoding="utf-8")
    return ingest_path(db, tmp_path / "nd.txt", tmp_path), ingest_path(db, tmp_path / "qd.txt", tmp_path)


def test_c3_bo_loc_ap_trong_truy_van_khong_sau_khi_cat_top(db, tmp_path):
    """C3: bộ lọc loại không được áp sau khi cắt top-100 của toàn kho: Quyết định khớp yếu vẫn phải hiện."""
    from soiluat.app import _search

    nd, qd = _kho_loc(db, tmp_path)
    s = _search(db, "báo cáo định kỳ", "quyet_dinh", "", "")
    doc_of = {r[0]: r[1] for r in db.execute("SELECT id, doc_id FROM units")}
    assert s["ids"] and {doc_of[i] for i in s["ids"]} == {qd}
    assert len(_search(db, "báo cáo định kỳ", "", "", "")["ids"]) > 50  # không lọc: vẫn là cả kho


def test_c3_bo_loc_khong_van_ban_nao_thi_rong_khong_phai_khong_loc(db, tmp_path):
    """C3: bộ lọc không còn văn bản nào cho kết quả rỗng (danh sách doc_ids rỗng không được hiểu là "không giới hạn"),
    cả khi câu hỏi có số hiệu."""
    from soiluat.app import _search

    _kho_loc(db, tmp_path)
    assert _search(db, "báo cáo định kỳ", "nghi_quyet", "", "")["ids"] == []
    assert _search(db, "15/2020/NĐ-CP báo cáo định kỳ", "quyet_dinh", "", "")["ids"] == []
    assert _search(db, "báo cáo định kỳ", "", "", "con")["ids"] == []  # cả kho hiệu lực chưa rõ
