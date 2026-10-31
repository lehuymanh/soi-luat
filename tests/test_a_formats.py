"""L2/L3/L6: xlsx, ảnh, .doc/.rtf, bảng PDF, trang cần OCR."""

import zipfile
from pathlib import Path

import pytest

from soiluat import convert
from soiluat.extract import (
    SUPPORTED_SUFFIXES,
    _borderless_tables,
    classify_pdf_page,
    extract_file,
    is_junk_text,
)

X = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
R = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'


def test_supported_suffixes_contract():
    need = ".docx .doc .rtf .pdf .txt .md .jpg .jpeg .png .tif .tiff .bmp .xlsx".split()
    assert set(need) <= SUPPORTED_SUFFIXES


def test_unsupported_suffix(tmp_path):
    p = tmp_path / "a.pptx"
    p.write_bytes(b"x")
    with pytest.raises(ValueError, match="Không hỗ trợ"):
        extract_file(p)


def _xlsx(path: Path) -> None:
    rels = (
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Target="worksheets/sheet1.xml" Type="ws"/>'
        '<Relationship Id="rId2" Target="/xl/worksheets/sheet2.xml" Type="ws"/></Relationships>'
    )
    wb = f'<workbook {X} {R}><sheets><sheet name="A" sheetId="1" r:id="rId1"/><sheet name="B" sheetId="2" r:id="rId2"/></sheets></workbook>'
    sst = f'<sst {X}><si><t>Nội dung</t></si><si><r><t>Phí </t></r><r><t>thẩm định</t></r></si></sst>'
    s1 = (
        f'<worksheet {X}><sheetData>'
        '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="C1" t="inlineStr"><is><t>Mức thu</t></is></c></row>'
        '<row r="2"><c r="A2" t="s"><v>1</v></c><c r="B2"><v>5000000</v></c><c r="C2"><v>1.5</v></c></row>'
        '<row r="3"/></sheetData></worksheet>'
    )
    s2 = f'<worksheet {X}><sheetData><row r="1"><c r="B1" t="b"><v>1</v></c></row></sheetData></worksheet>'
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("xl/workbook.xml", wb)
        z.writestr("xl/_rels/workbook.xml.rels", rels)
        z.writestr("xl/sharedStrings.xml", sst)
        z.writestr("xl/worksheets/sheet1.xml", s1)
        z.writestr("xl/worksheets/sheet2.xml", s2)


def test_xlsx_sheets_rows(tmp_path):
    p = tmp_path / "pl.xlsx"
    _xlsx(p)
    pages = extract_file(p)
    assert [pg.page_no for pg in pages] == [1, 2]
    assert pages[0].text.splitlines() == [
        "| Nội dung |  | Mức thu |",
        "| Phí thẩm định | 5000000 | 1.5 |",
    ]
    assert pages[1].text == "|  | TRUE |"
    assert pages[0].kind == "table" and pages[0].extraction_method == "xlsx"


def test_image_frames_are_pages(tmp_path):
    from PIL import Image

    p = tmp_path / "scan.tif"
    a, b = Image.new("L", (40, 40), 255), Image.new("L", (40, 40), 0)
    a.save(p, save_all=True, append_images=[b])
    pages = extract_file(p)
    assert [(x.page_no, x.kind, x.ocr_status, x.text) for x in pages] == [
        (1, "image", "cho_ocr", ""),
        (2, "image", "cho_ocr", ""),
    ]
    q = tmp_path / "a.jpg"
    a.save(q)
    assert len(extract_file(q)) == 1


def test_convert_fallback_error_and_cleanup(tmp_path, monkeypatch):
    seen: list[Path] = []

    def fail(name):
        def f(src, dst):
            seen.append(dst)
            raise RuntimeError(f"{name} hỏng")

        return f

    monkeypatch.setattr(convert, "word_to_docx", fail("word"))
    monkeypatch.setattr(convert, "soffice_to_docx", fail("lo"))
    src = tmp_path / "cu.doc"
    src.write_bytes(b"x")
    with pytest.raises(ValueError, match="LibreOffice") as e:
        extract_file(src)
    assert "word hỏng" in str(e.value) and "lo hỏng" in str(e.value)
    assert len(seen) == 2 and not seen[0].parent.exists()  # thư mục tạm đã dọn


def test_convert_uses_second_converter(tmp_path, monkeypatch):
    from docx import Document

    def word_fail(src, dst):
        raise RuntimeError("không có Word")

    def lo_ok(src, dst):
        d = Document()
        d.add_paragraph("Điều 1. Từ LibreOffice")
        d.save(str(dst))

    monkeypatch.setattr(convert, "word_to_docx", word_fail)
    monkeypatch.setattr(convert, "soffice_to_docx", lo_ok)
    src = tmp_path / "cu.rtf"
    src.write_bytes(b"x")
    assert extract_file(src)[0].text == "Điều 1. Từ LibreOffice"


def test_sec1_word_tat_macro_truoc_khi_mo_file(tmp_path, monkeypatch):
    """SEC-1: Word mở file qua COM mặc định bật mọi macro (AutomationSecurity = Low); phải ép tắt TRƯỚC Documents.Open."""
    import sys
    import types

    seen: dict = {}

    class Doc:
        def SaveAs2(self, *a, **k):
            seen["saved"] = True

        def Close(self, *a):
            pass

    class Docs:
        def Open(self, *a, **k):
            seen["security_at_open"] = getattr(word, "AutomationSecurity", None)
            return Doc()

    class Word:
        Documents = Docs()

        def Quit(self):
            seen["quit"] = True

    word = Word()
    client = types.ModuleType("win32com.client")
    client.DispatchEx = lambda name: word
    pkg = types.ModuleType("win32com")
    pkg.client = client
    pycom = types.ModuleType("pythoncom")
    pycom.CoInitialize = pycom.CoUninitialize = lambda: None
    for name, mod in (("win32com", pkg), ("win32com.client", client), ("pythoncom", pycom)):
        monkeypatch.setitem(sys.modules, name, mod)
    src = tmp_path / "x.doc"
    src.write_bytes(b"x")
    convert.word_to_docx(src, tmp_path / "x.docx")
    assert seen["security_at_open"] == 3  # msoAutomationSecurityForceDisable
    assert seen["saved"] and seen["quit"]


def test_rtf_via_word(tmp_path):
    pytest.importorskip("win32com.client")
    src = tmp_path / "a.rtf"
    src.write_text(r"{\rtf1\ansi Dieu 1. Pham vi dieu chinh\par Dieu 2. Doi tuong\par}", encoding="ascii")
    try:
        pages = extract_file(src)
    except ValueError as e:
        pytest.skip(f"máy không có Word/LibreOffice: {e}")
    assert "Dieu 2. Doi tuong" in pages[0].text


# --- PDF ---


def _pdf(path: Path, ops: str) -> None:
    """PDF tối thiểu một trang (Helvetica), `ops` là content stream."""
    stream = ops.encode("latin-1")
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 800] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = b"%PDF-1.4\n"
    offs = []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offs)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    path.write_bytes(out)


def _txt(x, y, s):
    return f"BT /F1 11 Tf {x} {y} Td ({s}) Tj ET\n"


def test_pdf_ruled_table_inline_by_y(tmp_path):
    ops = _txt(60, 740, "Dieu 1. Pham vi ap dung cho moi to chuc ca nhan")
    # bảng 2x2 có kẻ khung, y từ 600 đến 680
    ops += "0.5 w 60 600 m 400 600 l S 60 640 m 400 640 l S 60 680 m 400 680 l S "
    ops += "60 600 m 60 680 l S 200 600 m 200 680 l S 400 600 m 400 680 l S\n"
    ops += _txt(65, 660, "Khong niem yet") + _txt(205, 660, "Phat tien 3 trieu")
    ops += _txt(65, 620, "Khong lap so") + _txt(205, 620, "Phat tien 5 trieu")
    ops += _txt(60, 560, "Dieu 2. Hieu luc thi hanh tu ngay ky ban hanh van ban")
    p = tmp_path / "t.pdf"
    _pdf(p, ops)
    page = extract_file(p)[0]
    assert page.kind == "table"
    assert page.text.splitlines() == [
        "Dieu 1. Pham vi ap dung cho moi to chuc ca nhan",
        "| Khong niem yet | Phat tien 3 trieu |",
        "| Khong lap so | Phat tien 5 trieu |",
        "Dieu 2. Hieu luc thi hanh tu ngay ky ban hanh van ban",
    ]


def test_pdf_borderless_table_wrapped_cells(tmp_path):
    ops = _txt(60, 740, "Muc phat doi voi cac hanh vi sau day duoc quy dinh nhu sau")
    ops += _txt(65, 700, "STT") + _txt(120, 700, "Hanh vi") + _txt(300, 700, "Muc phat")
    ops += _txt(65, 680, "1") + _txt(120, 680, "Khong niem yet gia dich") + _txt(300, 680, "Phat tien tu 3.000.000")
    ops += _txt(120, 666, "vu cam do") + _txt(300, 666, "dong den 5.000.000 dong")
    ops += _txt(65, 646, "2") + _txt(120, 646, "Khong lap so") + _txt(300, 646, "Phat tien 10.000.000 dong")
    ops += _txt(60, 600, "Dieu 3. Hieu luc thi hanh tu ngay ky ban hanh van ban nay")
    p = tmp_path / "b.pdf"
    _pdf(p, ops)
    assert extract_file(p)[0].text.splitlines() == [
        "Muc phat doi voi cac hanh vi sau day duoc quy dinh nhu sau",
        "| STT | Hanh vi | Muc phat |",
        "| 1 | Khong niem yet gia dich vu cam do | Phat tien tu 3.000.000 dong den 5.000.000 dong |",
        "| 2 | Khong lap so | Phat tien 10.000.000 dong |",
        "Dieu 3. Hieu luc thi hanh tu ngay ky ban hanh van ban nay",
    ]


def test_borderless_ignores_plain_paragraphs():
    class Page:
        def extract_words(self):
            words, top = [], 100.0
            for line in ["Dieu 1. Pham vi dieu chinh", "Van ban nay quy dinh ve viec", "a) Doanh nghiep phai bao cao"]:
                x = 60.0
                for w in line.split():
                    words.append({"text": w, "x0": x, "x1": x + 6 * len(w), "top": top, "bottom": top + 11})
                    x += 6 * len(w) + 4
                top += 14
            return words

    assert _borderless_tables(Page()) == []


def test_classify_mixed_image_heavy_needs_ocr():
    assert classify_pdf_page("x" * 150, 1, False, image_cover=0.8) == ("mixed", "pdf_text", "cho_ocr")
    assert classify_pdf_page("x" * 150, 1, False, image_cover=0.3)[2] == "khong_can"
    assert classify_pdf_page("x" * 300, 1, False, image_cover=0.9)[2] == "khong_can"


def test_junk_text_detection():
    good = "Điều 5. Doanh nghiệp phải nộp báo cáo giám sát an toàn thực phẩm hằng quý (mẫu 01)."
    assert not is_junk_text(good)
    assert is_junk_text("NghÞ ®Þnh nµy quy ®Þnh vÒ xö ph¹t vi ph¹m hµnh chÝnh trong lÜnh vùc")  # TCVN3
    assert is_junk_text("Nghò ñònh naøy quy ñònh veà xöû phaït vi phaïm haønh chính")  # VNI
    assert is_junk_text("Điều ��� quy định �� về việc nộp thuế")
    assert is_junk_text("(cid:12)(cid:45)(cid:77)(cid:3)(cid:90) ab")
    kind, _, ocr = classify_pdf_page("NghÞ ®Þnh nµy quy ®Þnh vÒ xö ph¹t vi ph¹m hµnh chÝnh", 0, False)
    assert (kind, ocr) == ("text_suspect", "cho_ocr")
