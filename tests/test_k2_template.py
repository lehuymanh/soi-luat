"""P1 K2: _results.html theo mẫu giao diện 1.0 (đầu kết quả, nhóm theo văn bản, mục gọn, chân, trạng thái rỗng, ô lọc)."""

import re
from types import SimpleNamespace as NS

from fastapi.testclient import TestClient

import soiluat.app as appmod
from soiluat.cards import OCR_LABEL, Card
from soiluat.ingest import ingest_path

N0 = {"n1": 0, "n2": 0, "n3": 0, "n4": 0}


def _c(**kw) -> Card:
    base = dict(kind="Quy định liên quan", title="Điều 5. Báo cáo", sample="", duty_text="Phải báo cáo định kỳ.",
                duty_addr="", sanction_text="", sanction_addr="", hieu_luc="chua_ro", link_status="",
                ocr_unverified=False, unit_ids=[1], so_hieu="15/2020/NĐ-CP", file_path="nd15.pdf", warnings=[],
                doc_id=1, path="D5.K1", head="Báo cáo", snippet="Phải báo cáo định kỳ.")
    base.update(kw)
    return Card(**base)


def _render(items, **ctx):
    ctx = {"items": items, "cards": items, "n": {**N0, "n4": len(items)}, "dates": {}, "csrf_token": "t", "q": "báo cáo", **ctx}
    return appmod.TEMPLATES.env.get_template("_results.html").render(**ctx)


def _hx(client, q, **p):
    return client.get("/", params={"q": q, **p}, headers={"HX-Request": "true"}).text


def _kho(tmp_path, monkeypatch, db, docs):
    monkeypatch.setenv("SOILUAT_DATA", str(tmp_path))
    for name, text in docs.items():
        p = tmp_path / name
        p.write_text(text, encoding="utf-8")
        ingest_path(db, p, tmp_path)
    return TestClient(appmod.app)


def _nd(so, n_dieu):
    return f"Nghị định số {so}/NĐ-CP\n" + "".join(
        f"Điều {d}. Báo cáo lần {d}\n1. Đơn vị phải báo cáo định kỳ lần {d}.\n" for d in range(1, n_dieu + 1))


# --- đầu kết quả ---


def test_dau_ket_qua_dem_muc_van_ban_va_y_dinh_mot_lan():
    items = [_c(intent="muc_phat"), _c(unit_ids=[2], path="D6.K1", intent="muc_phat"), _c(unit_ids=[3], doc_id=2, intent="muc_phat")]
    html = _render(items)
    assert "3 kết quả trong 2 văn bản" in html
    assert html.count("Ý định: mức phạt") == 1


def test_nhan_chac_chan_chi_khi_co_sure_va_dong_finding():
    two = [_c(), _c(unit_ids=[2], path="D6.K1")]
    ban = _render(two, sure=None)
    assert "Khớp rõ" not in ban and "Chưa chắc chắn" not in ban and "Đoạn đầu:" in ban
    assert "Đoạn đầu khớp hơn hẳn" not in ban
    chac = _render(two, sure=True)
    assert "Khớp rõ" in chac and "Đoạn đầu khớp hơn hẳn các đoạn sau" in chac
    chua = _render(two, sure=False)
    assert "Chưa chắc chắn" in chua and "Nhiều đoạn khớp gần ngang nhau. Đọc vài đoạn đầu, bắt đầu từ" in chua
    assert "Chỉ có một đoạn khớp: " in _render([_c()])
    # trích dẫn đủ dạng: địa chỉ, loại và số hiệu văn bản
    html = _render(two, dates={1: {"loai": "nghi_dinh"}})
    assert "<b>Khoản 1 Điều 5 Nghị định 15/2020/NĐ-CP</b>" in html


def test_dong_loai_doan_dem_tren_ca_danh_sach_va_chu_giai_bang_nut():
    html = _render([_c(), _c(unit_ids=[2])], n={"n1": 1, "n2": 0, "n3": 0, "n4": 4})
    assert "1 mức phạt đã duyệt · 4 quy định liên quan" in html and "mức phạt máy gợi ý" in html  # hạng 2 chỉ ở chú giải
    assert re.search(r'<button type="button" class="link" data-legend aria-expanded="false">Các loại đoạn là gì\?</button>', html)
    leg = re.search(r'<dl class="legend" hidden>(.*?)</dl>', html, re.S).group(1)
    for t in ("mức phạt đã duyệt", "mức phạt máy gợi ý", "nghĩa vụ chưa rõ mức phạt", "quy định liên quan"):
        assert t in leg


def test_dang_loc():
    html = _render([_c()], loai="nghi_dinh", co_quan="Bộ Tài chính", hieu_luc="con")
    assert "Đang lọc: Nghị định, Bộ Tài chính, còn hiệu lực." in html
    assert "Đang lọc" not in _render([_c()], loai="", co_quan="", hieu_luc="")


# --- nhóm theo văn bản ---


def test_dau_nhom_ten_pill_dong_mt():
    dt = {"loai": "nghi_dinh", "co_quan": "Bộ Tài chính", "ngay_ban_hanh": "2020-02-01", "ngay_hieu_luc": "2026-03-01"}
    html = _render([_c(), _c(unit_ids=[2], path="D6.K1")], dates={1: dt, 2: dt})
    head = re.search(r'<header class="grp-h">(.*?)</header>', html, re.S).group(1)
    assert "Nghị định 15/2020/NĐ-CP" in head and "· 2 Điều" in head
    assert '<span class="pill neu">Hiệu lực chưa rõ</span>' in head
    assert "Bộ Tài chính · ban hành 01/02/2020 · hiệu lực từ 01/03/2026 · nd15.pdf" in head
    assert html.count('<section class="grp') == 1


def test_dau_nhom_van_ban_quet_khong_so_hieu_ghi_ten_tep_va_het_hieu_luc_mo():
    html = _render([_c(so_hieu="", file_path="D:\\kho\\quet_01.pdf#vb2", hieu_luc="het")])
    head = re.search(r'<header class="grp-h">(.*?)</header>', html, re.S).group(1)
    assert "<h3>quet_01.pdf" in head and "Hết hiệu lực" in head
    assert '<section class="grp faded">' in html
    assert "Chưa có" not in head  # thiếu cơ quan, ngày thì bỏ phần đó, không in chữ trống


def test_canh_bao_ocr_len_dau_nhom_mot_lan_nhom_lan_giu_o_tung_muc():
    ocr = dict(ocr_unverified=True, warnings=["Hiệu lực chưa rõ", OCR_LABEL])
    html = _render([_c(**ocr), _c(unit_ids=[2], path="D6.K1", **ocr)])
    assert html.count(OCR_LABEL) == 1
    assert OCR_LABEL in re.search(r'<header class="grp-h">(.*?)</header>', html, re.S).group(1)
    lan = _render([_c(**ocr), _c(unit_ids=[2], path="D6.K1")])
    assert lan.count(OCR_LABEL) == 1 and OCR_LABEL not in re.search(r'<header class="grp-h">(.*?)</header>', lan, re.S).group(1)
    assert "Hiệu lực chưa rõ" not in lan.split('<ul class="items">')[1]  # pill đã nói, không lặp trong mục


# --- một mục ---


def test_muc_dia_chi_lien_ket_mo_trinh_doc_nut_va_o_chon():
    html = _render([_c()], q="báo cáo", dates={1: {"loai": "nghi_dinh"}})
    assert html.count('<article class="card ') == 1
    assert 'href="/doc/1?path=D5.K1&amp;q=b%C3%A1o%20c%C3%A1o" data-doc>Khoản 1 Điều 5</a>' in html
    assert '<span class="dieu-t">Báo cáo</span>' in html
    assert re.search(r'<a class="go" href="/doc/1\?path=D5\.K1[^"]*" data-doc>Mở tại đoạn này</a>', html)
    cite = "Khoản 1 Điều 5 Nghị định 15/2020/NĐ-CP"
    # nhãn trình đọc màn hình theo Điều: 25 nút "Sao chép trích dẫn" và 25 ô "Chọn để xuất" không được trùng tên
    assert f'<button type="button" class="quiet" data-copy="{cite}" aria-label="Sao chép trích dẫn: {cite}">Sao chép trích dẫn</button>' in html
    assert re.search(rf'<input type="checkbox" name="uid" value="1" aria-label="Chọn để xuất {cite}">\s*Chọn để xuất', html)
    assert '<mark class="m">báo</mark>' in html


def test_muc_thieu_truong_moi_van_ra_va_tro_ve_unit():
    c = NS(kind="Quy định liên quan", title="Điều 5. Báo cáo", duty_text="Nội dung", unit_ids=[7], hieu_luc="con",
           so_hieu="", file_path="a.txt", warnings=[], rank=4, grey=False, ocr_unverified=False)
    html = _render([c], cards=[c])
    assert 'href="/unit/7?q=b%C3%A1o%20c%C3%A1o"' in html and "Nội dung" in html and "Điều 5. Báo cáo" in html


def test_cung_dieu_con_khop_va_cung_co_o_nhieu_van_ban():
    khac = _c(unit_ids=[9], doc_id=2, so_hieu="99/2021/NĐ-CP", file_path="b.pdf", hieu_luc="con")
    html = _render([_c(more=["D5.K2", "D5.K1.Đb"], also_in=[khac])])
    assert re.search(r'Cùng Điều còn khớp: <a class="link" href="/doc/1\?path=D5\.K2[^"]*" data-doc>Khoản 2</a> · '
                     r'<a class="link" href="/doc/1\?path=D5\.K1\.%C4%90b[^"]*" data-doc>Điểm b khoản 1</a>', html)
    assert "Cũng có ở 1 văn bản khác" in html
    also = html.split('<details class="also">')[1]
    assert 'href="/unit/9?q=' in also and "99/2021/NĐ-CP" in also and "b.pdf" in also and "Còn hiệu lực" in also
    sach = _render([_c()])
    assert "Cùng Điều còn khớp" not in sach and "Cũng có ở" not in sach


def test_nhan_tu_dong_nghia_chi_khi_that_su_dong_nghia():
    assert "khớp theo từ đồng nghĩa" in _render([_c(synonym_note="dong_nghia")])
    assert "khớp theo từ đồng nghĩa" not in _render([_c(synonym_note="dieu")])
    assert "tìm theo nghĩa, không chung từ khoá" in _render([_c(match_tier=7)])


# --- chân ---


def test_chan_xuat_word_luon_hien_tat_cho_toi_khi_chon():
    html = _render([_c(), _c(unit_ids=[2], path="D6.K1")])
    assert re.search(r'<button type="submit" class="btn primary" data-export disabled>Xuất Word</button>', html)
    assert "Đang hiện <span data-shown>2</span> trên 2" in html
    assert "data-more" not in html and 'name="csrf_token"' in html


def test_xem_them_khoi_an_nhom_tiep_khong_ve_lai_pill_va_dong_cap(db, tmp_path, monkeypatch):
    cl = _kho(tmp_path, monkeypatch, db, {"nd9.txt": _nd("9/2021", 26)})  # 26 Điều và đoạn đầu trang cũng khớp: 27 mục
    html = _hx(cl, "báo cáo định kỳ")
    assert "27 kết quả trong 1 văn bản" in html
    assert html.count('<article class="card ') == 25
    assert len(re.findall(r'<div class="more" hidden data-n="10">', html)) == 2
    assert 'data-more>Xem thêm 10 kết quả</button>' in html and "Đang hiện <span data-shown>5</span> trên 27" in html
    assert "· 5 Điều" in html and html.count("· tiếp, thêm 10 Điều") == 2
    assert html.count("Hiệu lực chưa rõ") == 1  # pill chỉ ở đầu nhóm đầu
    assert "Còn 2 mục nữa" in html
    # 5 mục đầu nằm ngoài khối ẩn
    assert html.split('<div class="more" hidden')[0].count('<article class="card ') == 5


def test_vua_du_nam_muc_khong_co_nut_xem_them(db, tmp_path, monkeypatch):
    cl = _kho(tmp_path, monkeypatch, db, {"nd9.txt": _nd("9/2021", 4)})
    html = _hx(cl, "báo cáo định kỳ")
    assert "5 kết quả trong 1 văn bản" in html and 'Đang hiện <span data-shown>5</span> trên 5' in html
    assert "data-more" not in html and 'class="more"' not in html and 'class="cap"' not in html


# --- trạng thái rỗng ---


def test_rong_kho_trong(tmp_path, monkeypatch):
    monkeypatch.setenv("SOILUAT_DATA", str(tmp_path))
    html = _hx(TestClient(appmod.app), "báo cáo")
    assert "Kho chưa có văn bản" in html and 'data-open="import"' in html and "Nạp văn bản" in html


def test_rong_khong_khop_va_bo_loc_loai_het(db, tmp_path, monkeypatch):
    cl = _kho(tmp_path, monkeypatch, db, {"nd9.txt": _nd("9/2021", 3)})
    html = _hx(cl, "zzzxyz")
    assert "Không tìm thấy đoạn nào khớp «zzzxyz»" in html and "Đã tìm trong 1 văn bản của kho" in html
    assert "nạp văn bản" in html.lower() and "<article" not in html
    loc = _hx(cl, "báo cáo định kỳ", loai="thong_tu")
    assert "Không còn kết quả sau khi lọc" in loc and re.search(r"Tìm được \d+ đoạn, nhưng không đoạn nào thuộc bộ lọc", loc)
    assert "data-unfilter" in loc and "Bỏ lọc" in loc


# --- Mở toàn văn ---


def test_so_hieu_mot_minh_ra_mo_toan_van_trong_html(db, tmp_path, monkeypatch):
    cl = _kho(tmp_path, monkeypatch, db, {"nd9.txt": _nd("9/2021", 3)})
    did = db.execute("SELECT id FROM documents").fetchone()[0]
    html = _hx(cl, "9/2021/NĐ-CP")
    assert f'<a class="btn" href="/doc/{did}" data-doc>Mở toàn văn</a>' in html
    assert "Số hiệu khớp 1 văn bản" in html and "3 Điều" in html and "<article" not in html
    assert "gõ thêm “Điều n”" in html
    miss = _hx(cl, "Điều 99 Nghị định 9/2021/NĐ-CP")
    assert "không có Điều 99" in miss and "Mở toàn văn" in miss


def test_mo_toan_van_toi_da_nam_van_ban():
    docs = [NS(full=True, doc_id=i, so_hieu=f"{i}/2021/NĐ-CP", loai="nghi_dinh", co_quan="", file_path=f"v{i}.pdf",
               hieu_luc="chua_ro", ngay_ban_hanh="", ngay_hieu_luc="", n_dieu=0, n_pages=1, missing_dieu="") for i in range(1, 8)]
    html = _render(docs, cards=[], n_items=7)
    assert "Số hiệu khớp 7 văn bản" in html and html.count('<div class="full">') == 5
    assert "Còn 2 văn bản khớp nữa. Gõ đủ số hiệu để mở đúng văn bản." in html and "chưa tách Điều" in html


# --- ô lọc, dữ liệu, đăng ký ---


def test_card_dates_tra_them_loai_va_co_quan(db, sample_doc):
    db.execute("UPDATE documents SET co_quan = 'Chính phủ'")
    db.commit()
    uid = db.execute("SELECT id FROM units LIMIT 1").fetchone()[0]
    d = appmod._card_dates(db, [_c(unit_ids=[uid])])[uid]
    assert d["co_quan"] == "Chính phủ" and d["loai"] and "ngay_ban_hanh" in d and "ngay_hieu_luc" in d


def test_o_loc_co_quan_la_select_lay_tu_kho(db, tmp_path, monkeypatch):
    cl = _kho(tmp_path, monkeypatch, db, {"a.txt": _nd("1/2021", 1), "b.txt": _nd("2/2021", 1), "c.txt": _nd("3/2021", 1)})
    db.execute("UPDATE documents SET co_quan = CASE so_hieu WHEN '1/2021/NĐ-CP' THEN 'Bộ Tài chính' WHEN '2/2021/NĐ-CP' THEN 'Bộ Tài chính' ELSE 'Chính phủ' END")
    db.commit()
    html = cl.get("/").text
    sel = re.search(r'<select name="co_quan"[^>]*>(.*?)</select>', html, re.S).group(1)
    assert re.findall(r'<option value="([^"]*)"', sel) == ["", "Bộ Tài chính", "Chính phủ"]
    cur = cl.get("/", params={"q": "báo cáo", "co_quan": "Chính phủ"}).text
    assert 'value="Chính phủ" selected' in cur
    la = cl.get("/", params={"co_quan": "Cơ quan đã xoá"}).text  # giá trị cũ không có trong kho vẫn giữ, không âm thầm bỏ lọc
    assert 'value="Cơ quan đã xoá" selected' in la


def test_dang_ky_globals_va_bo_loc():
    g = appmod.TEMPLATES.env.globals
    for k in ("highlight", "doc_groups", "cite", "addr"):
        assert callable(g[k])
    assert str(g["highlight"]("Phải <b>báo</b> cáo", "báo cáo")).count('<mark class="m">') == 2  # đã thoát và tô từ khớp
    assert "&lt;b&gt;" in str(g["highlight"]("<b>", "x"))


def test_the_tu_van_ban_that_khong_ra_the_html_roi(db, tmp_path, monkeypatch):
    cl = _kho(tmp_path, monkeypatch, db, {"nd9.txt": _nd("9/2021", 2)})
    html = _hx(cl, "báo cáo")
    assert "Xem nguồn" not in html and "Xuất Word các thẻ đã chọn" not in html and 'class="stat' not in html
    assert not re.search(r"<script", html)
