"""N3: ba sửa nhỏ của parser trên bản scan thật (dấu “ thừa, chữ ký + phụ lục, đầu Điều bị OCR hỏng)."""
from soiluat.fold import pretty_path
from soiluat.parse import parse_structure


def _paths(r):
    return [u.addr_part for u in r.units]


def _dieu_nums(r):
    return [u.addr_part for u in r.units if u.level == "dieu"]


BODY = (
    "Nghị định số 1/2026/NĐ-CP\n"
    "Điều 1. Phạm vi\n1. Nghị định này quy định một.\n"
    "Điều 2. Hai\n1. Khoản hai.\n"
)


def test_c1_dau_ngoac_thua_khong_nuot_dieu_sau():
    # OCR chèn “ trước "Điều 3." của chính văn bản, dòng trước không kết thúc bằng ":" → không mở khối trích dẫn
    r = parse_structure(BODY + "2. Hết khoản hai.\n“Điều 3. Ba\n1. Khoản ba.\nĐiều 4. Bốn\n1. Khoản bốn.\n")
    assert _dieu_nums(r) == ["D1", "D2", "D3", "D4"]


def test_c1_trich_dan_that_sau_hai_cham_van_la_mot_khoi():
    text = (
        "Nghị định số 1/2026/NĐ-CP\nĐiều 1. Sửa đổi Luật\n"
        "1. Sửa đổi, bổ sung Điều 2 như sau:\n“Điều 2. Hai mới\n1. Khoản mới.”\n"
        "Điều 2. Hiệu lực\n1. Có hiệu lực từ ngày ký.\n"
    )
    assert _dieu_nums(parse_structure(text)) == ["D1", "D2"]  # Điều 2 trong ngoặc không thành Điều của văn bản


def test_c2_noi_nhan_kt_mot_dong_va_phu_luc_thanh_don_vi_rieng():
    text = BODY + "Nơi nhận: KT. BỘ TRƯỞNG\n- Văn phòng Chính phủ;\n- Lưu: VT.\nTHỨ TRƯỞNG\nNguyễn Văn A\nPHỤ LỤC I\nDANH MỤC\n1. Một mục.\nPHỤ LỤC II\nDanh mục hai.\n"
    r = parse_structure(text)
    assert "Nơi nhận" not in "".join(u.text for u in r.units if u.addr_part in ("D2", "D2.K1"))
    pl = [u for u in r.units if u.addr_part.startswith("PL")]
    assert [u.addr_part for u in pl] == ["PL1.para1", "PL2.para1"]
    assert "Một mục" in pl[0].text and "Danh mục hai" in pl[1].text
    assert pretty_path("PL2.para1") == "phụ lục 2 đoạn 1"


def test_c2_phu_luc_khong_co_noi_nhan_van_nam_trong_don_vi_cuoi():
    # shortcut đã ghi trong mã: không đoán phụ lục khi không có khối nơi nhận (tránh nuốt Điều sau)
    r = parse_structure(BODY + "PHỤ LỤC I\nDanh mục.\n")
    assert not [u for u in r.units if u.addr_part.startswith("PL")]


def test_c3_dau_dieu_ocr_hong():
    for head, title in [("Điều §. Quy định chuyển tiếp", "Quy định chuyển tiếp"),
                        ("Điều 3, Mức thu phí", "Mức thu phí"),
                        ("Điều 3ã. Mức thu phí", "Mức thu phí")]:
        r = parse_structure(BODY + head + "\nNội dung điều ba.\nĐiều 4. Bốn\n1. Khoản bốn.\n")
        assert _dieu_nums(r) == ["D1", "D2", "D3", "D4"], head
        assert [u.title for u in r.units if u.addr_part == "D3"] == [title]


def test_c3_khong_nhan_nham_dong_trich_dan():
    # dòng trích dẫn bị ngắt, mẫu biểu "Điều ..." và số ≠ số Điều kế tiếp không phải đầu Điều
    for line in ("Điều 46, Điều 47 của Luật này.", "Điều ... Chánh Văn phòng Bộ", "Điều 9, Mức phạt cao"):
        r = parse_structure(BODY + "2. Hết khoản hai.\n" + line + "\nĐiều 3. Ba\n1. Khoản ba.\n")
        assert _dieu_nums(r) == ["D1", "D2", "D3"], line


def test_phu_luc_gop_mot_the_khong_canh_bao_khong_cau_truc(db, tmp_path):
    """Nhóm A của N3: đoạn Phụ lục khớp cùng câu hỏi gom thành một thẻ mỗi Phụ lục (không chen kín 5 mục đầu),
    và không mang cảnh báo "Không có cấu trúc" vì văn bản có cấu trúc."""
    from soiluat import cards
    from soiluat.ingest import ingest_path
    from soiluat.search import cascade_search

    p = tmp_path / "pl.txt"
    p.write_text(BODY + "Nơi nhận:\n- Lưu: VT.\nPHỤ LỤC I\nBỐC XẾP THỦ CÔNG\nMục một về bốc xếp thủ công vật nặng.\n"
                 + "Nội dung dài về quy trình kiểm tra hàng hoá trong kho.\n" * 40 + "MỤC HAI\nMục hai cũng nói bốc xếp thủ công trong kho.\n", encoding="utf-8")
    ingest_path(db, p, tmp_path)
    ids = [r[0] for r in db.execute("SELECT id FROM units WHERE path LIKE 'PL1.%' ORDER BY id")]
    assert len(ids) >= 2
    db.execute("UPDATE units SET page_from = 2, page_to = 3 WHERE id = ?", (ids[-1],))  # như PDF: Phụ lục sang trang sau
    db.commit()
    cs = cards.assemble_cards(db, ids)
    assert len(cs) == 1 and set(cs[0].unit_ids) == set(ids)
    assert not any("Không có cấu trúc" in w for w in cs[0].warnings)
    pages = [r for r in db.execute(f"SELECT page_from, page_to FROM units WHERE id IN ({','.join('?' * len(ids))})", ids)]
    assert (cs[0].page_from, cs[0].page_to) == (min(p[0] for p in pages), max(p[1] or p[0] for p in pages))  # cả phần Phụ lục
    assert cascade_search(db, "bốc xếp thủ công").ids  # nội dung phụ lục tìm được
