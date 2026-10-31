"""Kế hoạch P1, R1: dựng thân văn bản cho trình đọc, chọn đúng đơn vị, tô từ khớp, chuỗi trích dẫn."""

import time

from markupsafe import Markup

from soiluat import reader
from soiluat.ingest import ingest_path

ND = (
    "Nghị định số 7/2021/NĐ-CP\n"
    "Điều 1. Phạm vi điều chỉnh\n"
    "Nghị định này quy định mức phạt.\n"
    "Điều 2. Xử phạt người điều khiển xe\n"
    "1. Phạt tiền từ 100.000 đồng đến 200.000 đồng đối với một trong các hành vi sau đây:\n"
    "a) Người điều khiển xe mô tô không có hoặc\n"
    "không mang theo Giấy chứng nhận bảo hiểm còn hiệu lực;\n"
    "b) Người điều khiển xe mô tô không mang theo Giấy đăng ký xe <script>.\n"
    "2. Phạt tiền từ 400.000 đồng đến 600.000 đồng đối với người điều khiển xe ô tô.\n"
)


def _doc(db, tmp_path, text=ND, name="nd7.txt"):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return ingest_path(db, p, tmp_path)


def _uid(db, doc, path):
    return db.execute("SELECT id FROM units WHERE doc_id = ? AND path = ?", (doc, path)).fetchone()[0]


def _add_unit(db, doc, path, level, text, parent=None):
    db.execute(
        "INSERT INTO units(doc_id, parent_id, path, level, title, raw_text, normalized_text, search_text, "
        "extraction_method, verification_status) VALUES (?,?,?,?,?,?,?,?,'text','ok')",
        (doc, parent, path, level, "", text, text, text),
    )
    return db.execute("SELECT last_insert_rowid()").fetchone()[0]


def test_thu_tu_neo_va_diem_nhieu_dong(db, tmp_path):
    doc = _doc(db, tmp_path)
    v = reader.build_view(db, doc, None, "")
    ids = [ln["id"] for ln in v["lines"]]
    assert ids == sorted(ids)
    a = next(ln for ln in v["lines"] if ln["path"] == "D2.K1.Đa")
    assert "không mang theo Giấy chứng nhận bảo hiểm" in str(a["html"])  # dòng nối thuộc điểm (N1a)
    assert a["label"] == "a)" and a["cls"].startswith("u l2")
    assert [t["label"] for t in v["toc"]] == ["Điều 1", "Điều 2"]


def test_chon_diem_thi_khoan_cha_cung_sel_va_to_tu(db, tmp_path):
    doc = _doc(db, tmp_path)
    sel = _uid(db, doc, "D2.K1.Đa")
    v = reader.build_view(db, doc, sel, "muc phat bảo hiểm bao nhiêu")
    by = {ln["path"]: ln for ln in v["lines"]}
    assert "sel" in by["D2.K1.Đa"]["cls"].split() and "sel" in by["D2.K1"]["cls"].split()
    assert "sel" not in by["D2.K1.Đb"]["cls"].split()
    html = str(by["D2.K1.Đa"]["html"])
    assert '<mark class="m">bảo</mark> <mark class="m">hiểm</mark>' in html  # "bảo hiểm" gạch đủ, "bao nhiêu" bị bỏ
    assert "mark" not in str(by["D2.K1.Đb"]["html"])  # chỉ tô trong đơn vị được chọn
    assert '<mark class="m">Phạt</mark>' in str(by["D2.K1"]["html"])  # "phat" không dấu khớp "Phạt"


def test_go_co_dau_khong_to_chu_khong_dau(db, tmp_path):
    words = reader.query_words("phạt")
    assert "<mark" not in str(reader.highlight("phat tien", words))
    assert '<mark class="m">phạt</mark>' in str(reader.highlight("phạt tiền", words))


def test_thoat_html_va_truy_van_so_hieu_khong_to(db, tmp_path):
    doc = _doc(db, tmp_path)
    sel = _uid(db, doc, "D2.K1.Đb")
    v = reader.build_view(db, doc, sel, "7/2021/NĐ-CP")
    b = str(next(ln for ln in v["lines"] if ln["path"] == "D2.K1.Đb")["html"])
    assert "&lt;script&gt;" in b and "<script>" not in b and "mark" not in b
    assert isinstance(reader.highlight("x", []), Markup)


def test_resolve_sel_path_thang_id_cu(db, tmp_path):
    doc = _doc(db, tmp_path)
    other = _doc(db, tmp_path, ND.replace("7/2021", "8/2021"), "nd8.txt")
    k1 = _uid(db, doc, "D2.K1")
    assert reader.resolve_sel(db, doc, _uid(db, doc, "D1"), "D2.K1") == k1
    assert reader.resolve_sel(db, doc, _uid(db, other, "D2.K1"), "") is None  # id của văn bản khác bị bỏ
    assert reader.resolve_sel(db, doc, k1, "") == k1


def test_nhan_hau_to_lan_dieu_ten_rong_ghi_chu(db, tmp_path):
    doc = _doc(db, tmp_path)
    d9 = _add_unit(db, doc, "D9", "dieu", "Không có tên nhưng có chữ.")
    _add_unit(db, doc, "D9.K2~4", "khoan", "Khoản trùng số.", d9)
    _add_unit(db, doc, "D2~2", "dieu", "Điều 2. Lần hai")
    k1 = _uid(db, doc, "D2.K1")
    _add_unit(db, doc, "GC1", "ghi_chu", "Chú thích của khoản 1.", k1)
    orphan = _add_unit(db, doc, "GC2", "ghi_chu", "Chân trang chung.")
    db.commit()
    v = reader.build_view(db, doc, orphan, "")
    by = {ln["path"]: ln for ln in v["lines"]}
    assert by["D9.K2~4"]["label"] == "2."
    assert "Không có tên nhưng có chữ." in str(by["D9"]["html"])
    assert any(t["label"] == "Điều 2 (lần 2)" for t in v["toc"])
    assert [g["path"] for g in by["D2.K1"]["notes"]] == ["GC1"]
    assert [n["path"] for n in v["orphan_notes"]] == ["GC2"] and v["orphan_open"]
    assert "sel" in v["orphan_notes"][0]["cls"].split()


def test_khong_cau_truc_muc_luc_theo_trang(db, tmp_path):
    doc = _doc(db, tmp_path, "Văn bản không có Điều nào.\nDòng thứ hai.\n", "doan.txt")
    db.execute("UPDATE documents SET fallback_doan = 1 WHERE id = ?", (doc,))
    db.execute("UPDATE units SET page_from = 1 WHERE doc_id = ?", (doc,))
    v = reader.build_view(db, doc, None, "")
    assert v["toc"] and v["toc"][0]["label"] == "Trang 1"
    assert all(ln["cls"] == "u" or ln["level"] == "dieu" for ln in v["lines"])  # đoạn không thụt


def test_cite():
    assert reader.cite("15/2020/NĐ-CP", "nghi_dinh", "D5.K1.Đa") == "Điểm a khoản 1 Điều 5 Nghị định 15/2020/NĐ-CP"
    assert reader.cite("17/2026/QH16", "luat", "D3") == "Điều 3 Luật 17/2026/QH16"
    assert reader.cite("17/2026/QH16", None, "D3.K2~2") == "Khoản 2 (lần 2) Điều 3 17/2026/QH16"
    assert reader.cite(None, None, "p1.para2") == "Trang 1 đoạn 2"
    assert "None" not in reader.cite(None, "", "D1") and reader.addr("D5.K1") == "Khoản 1 Điều 5"


def test_3000_don_vi_duoi_1_giay(db, tmp_path):
    lines = ["Nghị định số 9/2022/NĐ-CP"]
    for d in range(1, 301):
        lines.append(f"Điều {d}. Điều thứ {d}")
        for k in range(1, 10):
            lines.append(f"{k}. Khoản {k} của Điều {d} quy định mức phạt tiền.")
    doc = _doc(db, tmp_path, "\n".join(lines) + "\n", "lon.txt")
    n = db.execute("SELECT count(*) FROM units WHERE doc_id = ?", (doc,)).fetchone()[0]
    assert n >= 3000
    t = time.perf_counter()
    reader.build_view(db, doc, _uid(db, doc, "D150.K3"), "mức phạt tiền")
    assert time.perf_counter() - t < 1.0


def test_cau_hoi_lan_dieu_van_to_phan_con_lai():
    """classify_query gọi mọi câu có "Điều n" là so_hieu; "Điều 5" và số hiệu không phải từ khoá, phần còn lại vẫn được tô."""
    w = reader.query_words("mức phạt không đội mũ bảo hiểm theo Điều 5")
    assert w and '<mark class="m">bảo</mark>' in str(reader.highlight("mũ bảo hiểm", w))
    w = reader.query_words("100/2019/NĐ-CP Điều 5 dừng xe")
    assert '<mark class="m">dừng</mark>' in str(reader.highlight("dừng xe", w)) and "<mark" not in str(reader.highlight("Điều 5", w))
    for q in ("Điều 12", "385/2026/NĐ-CP", "Điều 5 Nghị định 15/2020/NĐ-CP"):  # chỉ có địa chỉ: không tô gì
        assert reader.query_words(q) == []


def test_to_tu_chuan_hoa_moi_chu_mot_lan_khong_nhan_voi_so_tu_cau_hoi():
    """Câu hỏi dán dài (nghìn từ) không được làm trang kết quả mất vài giây: chuẩn hóa mỗi chữ của đoạn đúng một lần."""
    words = reader.query_words(" ".join(f"tu{i}" for i in range(300)))
    text = " ".join(f"chữ{i}" for i in range(50))
    calls = []
    real = reader.fold_search
    reader.fold_search = lambda s: (calls.append(s), real(s))[1]
    try:
        out = reader.highlight(text, words)
    finally:
        reader.fold_search = real
    assert "<mark" not in str(out) and len(calls) <= 50
