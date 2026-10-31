from pathlib import Path

from soiluat.parse import parse_structure
from soiluat.sohieu import find_so_hieu

FIXTURE = Path(__file__).parent / "fixtures" / "nd15.txt"


def test_parse_dieu_khoan():
    text = FIXTURE.read_text(encoding="utf-8")
    r = parse_structure(text)
    assert r.so_hieu and "15/2020" in r.so_hieu
    dieu = [u for u in r.units if u.level == "dieu"]
    assert len(dieu) >= 3
    addrs = {u.addr_part for u in r.units}
    assert any(a == "D5.K1" or a.startswith("D5.K1") for a in addrs)
    assert r.c_khoan == 1.0
    assert r.c_phu > 0.5
    assert r.c_lien_tuc == 1.0
    assert r.s >= 0.6
    assert r.tier in (1, 2)


def test_c_lien_tuc_consecutive():
    text = (
        "Nghị định số 1/2020/NĐ-CP\n"
        "Điều 1. Một\n1. Khoản một.\n"
        "Điều 2. Hai\n1. Khoản hai.\n"
        "Điều 3. Ba\n1. Khoản ba.\n"
    )
    r = parse_structure(text)
    assert r.c_lien_tuc == 1.0
    assert r.s >= 0.6


def test_s_below_threshold_uses_tier3():
    text = (
        "Nghị định số 1/2020/NĐ-CP\n"
        "Điều 1. Một\n5. Khoản năm.\n"
        "Điều 9. Chín\n8. Khoản tám.\n"
        "Điều 20. Hai mươi\n3. Khoản ba.\n"
    )
    r = parse_structure(text)
    assert r.tier == 3
    assert all(u.level == "doan" for u in r.units)


def test_force_doan():
    text = "Nghị định số 1/2020/NĐ-CP\nĐiều 1. Một\n1. Khoản một.\nĐiều 2. Hai\n1. Khoản hai.\n"
    r = parse_structure(text, force_doan=True)
    assert r.tier == 3
    assert r.so_hieu and "1/2020" in r.so_hieu


def test_parse_fallback_without_dieu():
    r = parse_structure("Đây là đoạn văn không có cấu trúc điều khoản gì cả. " * 5)
    assert r.tier == 3
    assert r.units
    assert all(u.level == "doan" for u in r.units)


def test_find_so_hieu():
    assert find_so_hieu("xem 15/2020/NĐ-CP ngay") is not None


def test_diem_nhieu_dong():
    """N1a: dòng nối của một điểm thuộc về điểm đó, không bị dồn vào khoản cha."""
    text = (
        "Nghị định số 1/2020/NĐ-CP\n"
        "Điều 1. Xử phạt người điều khiển xe\n"
        "1. Phạt tiền từ 100.000 đồng đến 200.000 đồng đối với một trong các hành vi sau đây:\n"
        "a) Người điều khiển xe mô tô, xe gắn máy không có hoặc\n"
        "không mang theo Giấy chứng nhận bảo hiểm còn hiệu lực;\n"
        "b) Người điều khiển xe mô tô không mang theo\n"
        "Giấy đăng ký xe.\n"
        "2. Phạt tiền từ 400.000 đồng đến 600.000 đồng đối với người điều khiển xe ô tô\n"
        "không mang theo Giấy phép lái xe.\n"
        "Điều 2. Hiệu lực\n"
        "Nghị định này có hiệu lực từ ngày 01 tháng 01 năm 2021.\n"
    )
    u = {x.addr_part: x for x in parse_structure(text).units}
    assert u["D1.K1"].text.strip() == "Phạt tiền từ 100.000 đồng đến 200.000 đồng đối với một trong các hành vi sau đây:"
    assert "không mang theo Giấy chứng nhận bảo hiểm" in u["D1.K1.Đa"].text
    assert "Giấy đăng ký xe" in u["D1.K1.Đb"].text and "bảo hiểm" not in u["D1.K1.Đb"].text
    assert "không mang theo Giấy phép lái xe" in u["D1.K2"].text  # khoản không có điểm: không đổi


def test_c1_dong_so_hong_khong_lay_so_hieu_van_ban_duoc_dan():
    """C1: dòng "Số:" của chính văn bản bị OCR hỏng thì để trống, không lấy số của văn bản căn cứ."""
    from soiluat.parse import parse_so_hieu_from_text

    can_cu = "Căn cứ Luật số 84/2015/QH13 ngày 25 tháng 6 năm 2015;"
    for so in ("Số: | /2026/TT-BNV", "Số: |9 /2026/TT-BTC", "Số: — /2026/TT-BGDĐT"):
        text = f"BỘ NỘI VỤ\n{so}\nTHÔNG TƯ\n{can_cu}\nĐiều 1. Phạm vi"
        assert parse_so_hieu_from_text(text) is None, so
    # dòng Số đủ số (kể cả dạng bảng) vẫn đọc đúng
    for ln in ("Số: 26/2026/TT-BNV", "| Số: 26/2026/TT-BNV | Hà Nội, ngày 19 tháng 10 năm 2026 |"):
        assert parse_so_hieu_from_text(f"BỘ NỘI VỤ\n{ln}\n{can_cu}") == "26/2026/TT-BNV", ln
    # không có dòng Số nào: vẫn lấy số hiệu đầu tiên trong văn bản như cũ
    assert parse_so_hieu_from_text(f"THÔNG TƯ\n{can_cu}") == "84/2015/QH13"


def test_f3_tieu_muc_va_ten_chuong_khong_dinh_vao_diem_cuoi():
    text = (
        "Nghị định số 1/2020/NĐ-CP\n"
        "Chương I\nQUY ĐỊNH CHUNG\n"
        "Điều 1. Một\n1. Khoản một:\na) Tiếp nhận tố cáo;\nb) Xử lý tố cáo.\n"
        "Tiểu mục 2. TIẾP NHẬN VÀ XỬ LÝ TỐ CÁO\n"
        "Mục 3\nHÀNH VI VI PHẠM\n"
        "Chương II\nTHI HÀNH\n"
        "Điều 2. Hai\n1. Khoản hai.\n"
    )
    r = parse_structure(text)
    assert {u.addr_part: u.text for u in r.units}["D1.K1.Đb"] == "Xử lý tố cáo."
    assert not any("Tiểu mục" in u.text or "THI HÀNH" in u.text for u in r.units)


def test_f3_ten_dieu_bi_ngat_dong_noi_lai_thanh_mot_ten():
    r = parse_structure("Nghị định số 1/2020/NĐ-CP\nĐiều 1. Quy định về tổ chức\nvà hoạt động\n1. Khoản một.\n")
    d1 = next(u for u in r.units if u.addr_part == "D1")
    assert d1.title == "Quy định về tổ chức và hoạt động"
