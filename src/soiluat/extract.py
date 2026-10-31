"""Đọc DOCX/DOC/RTF/PDF/XLSX/ảnh/TXT thành trang. Không import Tesseract/PIL ở mức module — OCR gọi từ importer."""

from __future__ import annotations

import hashlib
import re
import unicodedata
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

IMAGE_SUFFIXES = frozenset({".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"})
SUPPORTED_SUFFIXES = frozenset(
    {".docx", ".doc", ".rtf", ".pdf", ".txt", ".md", ".xlsx"} | IMAGE_SUFFIXES
)
# Luồng nạp chỉ có một, không huỷ được: file docx/xlsx vài chục KB mà XML giải nén hàng trăm MB (hay triệu đoạn rỗng,
# ~0,5 ms mỗi đoạn) làm treo cả hàng đợi hàng chục phút. Văn bản luật thật: document.xml vài MB, dưới chục nghìn đoạn.
MAX_XML_BYTES = 64 << 20
MAX_PARAGRAPHS = 300_000


@dataclass
class Note:
    kind: str  # footnote | endnote | comment | textbox | header | footer
    text: str
    ref: str | None = None


@dataclass
class ExtractedPage:
    """Một trang. `notes`: ghi chú (H1). `ocr_conf`: độ tin cậy OCR trung bình thang 0–100
    (trung bình `conf` của Tesseract trên các từ), None nếu trang không OCR."""

    page_no: int
    text: str
    kind: str
    extraction_method: str
    bbox_json: str | None = None
    ocr_status: str = "khong_can"
    notes: list[Note] = field(default_factory=list)
    ocr_conf: float | None = None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


# --- Nhận diện lớp chữ rác (L6) ---

_VN_BASE = "aăâeêioôơuưy"
_VN_LETTERS = set("abcdefghijklmnopqrstuvwxyzđ")
for _b in _VN_BASE:
    for _m in ("", "\u0300", "\u0301", "\u0303", "\u0309", "\u0323"):
        _VN_LETTERS.add(unicodedata.normalize("NFC", _b + _m))
_VN_LETTERS |= {c.upper() for c in _VN_LETTERS}
_PUNCT = set(".,;:!?()[]{}\"'“”‘’-–—/\\%&*+=<>«»…§°|_#@$€•·")


def is_junk_text(text: str) -> bool:
    """Lớp chữ PDF hỏng: ký tự lạ > 30%, nhiều \\ufffd/(cid:), hoặc dấu hiệu font VNI/TCVN3."""
    t = unicodedata.normalize("NFC", text or "")
    chars = [c for c in t if not c.isspace()]
    if len(chars) < 20:
        return False
    if t.count("\ufffd") >= 3 or t.count("(cid:") >= 3:
        return True
    bad = sum(1 for c in chars if not (c in _VN_LETTERS or c.isdigit() or c in _PUNCT))
    if bad / len(chars) > 0.3:
        return True
    letters = [c for c in chars if c.isalpha()]
    # VNI/TCVN3 hiện thành ñ ø ï Þ ® ¸ µ... — chữ Latin không có trong tiếng Việt
    legacy = sum(1 for c in letters if c not in _VN_LETTERS)
    return bool(letters) and legacy / len(letters) > 0.05


def classify_pdf_page(
    text: str, n_images: int, has_table: bool, image_cover: float = 0.0
) -> tuple[str, str, str]:
    """kind, extraction_method, ocr_status — từng trang, kế hoạch 2.5."""
    chars = len((text or "").strip())
    kind = "text_ok"
    ocr = "khong_can"
    if chars < 40 and n_images:
        kind, ocr = "image", "cho_ocr"
    elif chars < 40:
        kind, ocr = "text_suspect", "can_duyet"
    elif is_junk_text(text):
        kind, ocr = "text_suspect", "cho_ocr"
    elif n_images:
        kind = "mixed"
        if image_cover > 0.5 and chars < 200:
            ocr = "cho_ocr"
    if has_table:
        kind = "table" if kind == "text_ok" else kind
    return kind, "pdf_text", ocr


# --- Đánh số danh sách Word ---


_ROMAN = (("M", 1000), ("CM", 900), ("D", 500), ("CD", 400), ("C", 100), ("XC", 90), ("L", 50),
          ("XL", 40), ("X", 10), ("IX", 9), ("V", 5), ("IV", 4), ("I", 1))


def _roman(n: int) -> str:
    out = ""
    for sym, val in _ROMAN:
        while n >= val:
            out, n = out + sym, n - val
    return out


def format_list_token(num_fmt: str, n: int) -> str:
    if n < 1:
        n = 1
    if num_fmt == "lowerLetter":
        return chr(ord("a") + (n - 1) % 26)
    if num_fmt == "upperLetter":
        return chr(ord("A") + (n - 1) % 26)
    if num_fmt == "upperRoman":
        return _roman(n)
    if num_fmt == "lowerRoman":
        return _roman(n).lower()
    if num_fmt == "decimalZero":
        return f"{n:02d}"
    return str(n)


def next_list_label(
    counts: dict[tuple[int, int], int],
    num_id: int,
    ilvl: int,
    num_fmt: str,
    lvl_text: str,
) -> str:
    counts[(num_id, ilvl)] = counts.get((num_id, ilvl), 0) + 1
    for n, l in list(counts):
        if n == num_id and l > ilvl:
            counts[(n, l)] = 0
    token = format_list_token(num_fmt, counts[(num_id, ilvl)])
    if lvl_text and "%1" in lvl_text:
        return lvl_text.replace("%1", token)
    if num_fmt == "lowerLetter":
        return f"{token})"
    return f"{token}."


class _Lvl:
    """Một cấp của abstractNum: w:numFmt, w:lvlText, w:start, w:isLgl, w:lvlRestart=0."""

    __slots__ = ("fmt", "text", "start", "lgl", "no_restart")

    def __init__(self, fmt="decimal", text="%1.", start=1, lgl=False, no_restart=False):
        self.fmt, self.text, self.start, self.lgl, self.no_restart = fmt, text, start, lgl, no_restart


def render_label(levels: dict[int, _Lvl], counts: dict[tuple[int, int], int], num_id: int, ilvl: int) -> str:
    """Nhãn số của đoạn thuộc (num_id, ilvl): tăng bộ đếm, đặt lại các cấp thấp hơn, thay mọi %k trong lvlText."""
    lv = levels.get(ilvl) or _Lvl()
    counts[(num_id, ilvl)] = counts.get((num_id, ilvl), lv.start - 1) + 1
    for (n, l) in list(counts):
        if n == num_id and l > ilvl and not (levels.get(l) and levels[l].no_restart):
            del counts[(n, l)]
    if lv.fmt == "bullet":
        return "-"
    if lv.fmt == "none":
        return ""

    def sub(m: re.Match) -> str:
        k = int(m.group(1)) - 1
        kl = levels.get(k) or _Lvl()
        val = counts.get((num_id, k), kl.start)
        return format_list_token("decimal" if lv.lgl else kl.fmt, val)

    text = re.sub(r"%(\d)", sub, lv.text or "")
    if text == (lv.text or "") and "%" not in text:  # lvlText không có %k (hiếm): dùng số của cấp hiện tại
        return f"{format_list_token(lv.fmt, counts[(num_id, ilvl)])}."
    return text


class _Numbering:
    def __init__(self, doc) -> None:
        self._counts: dict[tuple[int, int], int] = {}
        self._levels: dict[int, dict[int, _Lvl]] = {}  # num_id → {ilvl: _Lvl}
        self._load(doc)

    def _load(self, doc) -> None:
        try:
            from docx.oxml.ns import qn

            part = doc.part.numbering_part
            root = part._element
        except Exception:
            return

        def val(el, tag, default=None):
            x = el.find(qn(tag))
            return x.get(qn("w:val")) if x is not None else default

        abs_lvls: dict[int, dict[int, _Lvl]] = {}
        for absn in root.iter(qn("w:abstractNum")):
            try:
                abs_id = int(absn.get(qn("w:abstractNumId")))
            except (TypeError, ValueError):
                continue
            lvls: dict[int, _Lvl] = {}
            for lvl in absn.iter(qn("w:lvl")):
                try:
                    ilvl = int(lvl.get(qn("w:ilvl")))
                except (TypeError, ValueError):
                    continue
                try:
                    start = int(val(lvl, "w:start", "1"))
                except ValueError:
                    start = 1
                lvls[ilvl] = _Lvl(
                    val(lvl, "w:numFmt", "decimal") or "decimal",
                    val(lvl, "w:lvlText", "%1.") or "%1.",
                    start,
                    lvl.find(qn("w:isLgl")) is not None,
                    val(lvl, "w:lvlRestart") == "0",
                )
            abs_lvls[abs_id] = lvls
        for num in root.iter(qn("w:num")):
            try:
                num_id = int(num.get(qn("w:numId")))
                abs_id = int(val(num, "w:abstractNumId"))
            except (TypeError, ValueError):
                continue
            lvls = {k: _Lvl(v.fmt, v.text, v.start, v.lgl, v.no_restart) for k, v in abs_lvls.get(abs_id, {}).items()}
            for ov in num.findall(qn("w:lvlOverride")):  # đánh số lại từ giá trị khác
                try:
                    k = int(ov.get(qn("w:ilvl")))
                    st = val(ov, "w:startOverride")
                    if st is not None and k in lvls:
                        lvls[k].start = int(st)
                except (TypeError, ValueError):
                    pass
            self._levels[num_id] = lvls

    def paragraph_text(self, p, text: str | None = None) -> str:
        """Gắn nhãn số tự động vào đầu đoạn. `text` có thể chứa \\f (ngắt trang)."""
        if text is None:
            text = p.text or ""
        text = text.strip(" \t\r\n")  # giữ \f
        label = self._label(p)
        if not label:
            return text
        lead = len(text) - len(text.lstrip("\f"))
        body = text[lead:].lstrip()
        head = label.lower().rstrip(".)")
        if body.lower().startswith(head):
            return text
        return text[:lead] + f"{label} {body}".strip()

    def _num_pr_from_style(self, p) -> tuple[int, int] | None:
        try:
            from docx.oxml.ns import qn

            style = p.style
        except Exception:
            return None
        seen = 0
        while style is not None and seen < 8:
            seen += 1
            try:
                num_pr = style.element.find(qn("w:pPr"))
                if num_pr is not None:
                    np = num_pr.find(qn("w:numPr"))
                    if np is not None:
                        num_id_el = np.find(qn("w:numId"))
                        ilvl_el = np.find(qn("w:ilvl"))
                        if num_id_el is not None:
                            num_id = int(num_id_el.get(qn("w:val")))
                            ilvl = int(ilvl_el.get(qn("w:val"))) if ilvl_el is not None else 0
                            return num_id, ilvl
            except Exception:
                return None
            style = getattr(style, "base_style", None)
        return None

    def _label(self, p) -> str:
        num_id = None
        ilvl = 0
        try:
            num_pr = p._p.pPr.numPr
            if num_pr is not None:
                ilvl = int(num_pr.ilvl.val) if num_pr.ilvl is not None else 0
                num_id = int(num_pr.numId.val)
        except Exception:
            num_id = None
        if num_id is None:
            got = self._num_pr_from_style(p)
            if got is None:
                return ""
            num_id, ilvl = got
        if num_id == 0:
            return ""
        return render_label(self._levels.get(num_id, {}), self._counts, num_id, ilvl)


# --- DOCX: duyệt thân văn bản theo thứ tự ---

_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"


def _w(tag: str) -> str:
    return f"{{{_W}}}{tag}"


W_P, W_TBL, W_TR, W_TC, W_SDT, W_SDTC = map(_w, ("p", "tbl", "tr", "tc", "sdt", "sdtContent"))
W_T, W_TAB, W_BR, W_CR = map(_w, ("t", "tab", "br", "cr"))
W_LRPB, W_FNREF, W_ENREF = map(_w, ("lastRenderedPageBreak", "footnoteReference", "endnoteReference"))
W_TXBX, W_ID, W_TYPE, W_VAL = map(_w, ("txbxContent", "id", "type", "val"))
W_PPR, W_PBB, W_TCPR, W_SPAN, W_VMERGE = map(
    _w, ("pPr", "pageBreakBefore", "tcPr", "gridSpan", "vMerge")
)
W_NBH, W_CUSTOM = _w("noBreakHyphen"), _w("customXml")
_SKIP = set(map(_w, ("del", "delText", "instrText", "rPr", "pPr", "footnoteRef", "endnoteRef", "moveFrom")))
MC_ALT, MC_CHOICE, MC_FALLBACK = (f"{{{_MC}}}{t}" for t in ("AlternateContent", "Choice", "Fallback"))


def _check_zip_size(z: zipfile.ZipFile) -> None:
    """Tổng cỡ khai báo của các phần XML (file_size là hạn đọc cứng của zipfile, không khai thấp để lách được)."""
    if sum(i.file_size for i in z.infolist() if i.filename.endswith((".xml", ".rels"))) > MAX_XML_BYTES:
        raise ValueError("Tệp .docx/.xlsx quá lớn khi giải nén")


def _parse_part(z: zipfile.ZipFile, name: str):
    from lxml import etree

    try:
        return etree.fromstring(z.read(name))
    except KeyError:
        return None


def _notes_part(z: zipfile.ZipFile, name: str, tag: str) -> dict[str, str]:
    """footnotes.xml / endnotes.xml / comments.xml → {id: text}."""
    root = _parse_part(z, name)
    out: dict[str, str] = {}
    if root is None:
        return out
    for el in root.iter(_w(tag)):
        if el.get(W_TYPE) in ("separator", "continuationSeparator", "continuationNotice"):
            continue
        out[el.get(W_ID)] = " ".join(_plain_lines(el))
    return out


def _plain_lines(el) -> list[str]:
    """Các dòng chữ (mỗi đoạn một dòng) của footnote/comment/header; bỏ nhánh Fallback."""
    parts: list[str] = []

    def rec(e) -> None:
        for c in e:
            if c.tag == W_T:
                parts.append(c.text or "")
            elif c.tag in (W_TAB, W_BR, W_CR):
                parts.append(" ")
            elif c.tag in _SKIP or c.tag == MC_FALLBACK:
                continue
            else:
                rec(c)
                if c.tag in (W_P, W_TC):
                    parts.append("\n" if c.tag == W_P else " ")

    rec(el)
    lines = (" ".join(ln.split()) for ln in "".join(parts).split("\n"))
    return [ln for ln in lines if ln]


def _blocks(el, tags: tuple[str, ...]):
    """Con trực tiếp có tag trong `tags`, đi xuyên qua w:sdt/w:customXml."""
    for c in el:
        if c.tag in tags:
            yield c
        elif c.tag in (W_SDT, W_SDTC, W_CUSTOM):
            yield from _blocks(c, tags)


def _comment_ranges(body) -> dict[str, str]:
    """id comment → đoạn chữ được comment (≤ 80 ký tự)."""
    open_ids: dict[str, list[str]] = {}
    done: dict[str, str] = {}
    start, end = _w("commentRangeStart"), _w("commentRangeEnd")
    for el in body.iter(start, end, W_T):
        if el.tag == start:
            open_ids[el.get(W_ID)] = []
        elif el.tag == end:
            buf = open_ids.pop(el.get(W_ID), None)
            if buf is not None:
                done[el.get(W_ID)] = " ".join("".join(buf).split())[:80]
        else:
            for buf in open_ids.values():
                buf.append(el.text or "")
    return done


class _DocxReader:
    def __init__(self, doc, z: zipfile.ZipFile) -> None:
        from docx.text.paragraph import Paragraph

        self._Paragraph = Paragraph
        self.doc = doc
        self.numbering = _Numbering(doc)
        self.footnotes = _notes_part(z, "word/footnotes.xml", "footnote")
        self.endnotes = _notes_part(z, "word/endnotes.xml", "endnote")
        self.n_ref = 0
        self.n_para = 0
        self.pages: list[ExtractedPage] = []
        self.lines: list[str] = []
        self.page_notes: list[Note] = []
        self.first_notes: list[Note] = []  # comment/textbox/header/footer → trang 1

    # trang
    def flush(self, force: bool = False) -> None:
        text = "\n".join(self.lines).strip()
        if not text and not self.page_notes and not force:
            return  # ngắt trang cứng + lastRenderedPageBreak liền nhau: không đẻ trang rỗng
        self.pages.append(
            ExtractedPage(
                page_no=len(self.pages) + 1,
                text=text,
                kind="text_ok",
                extraction_method="docx",
                notes=self.page_notes,
            )
        )
        self.lines, self.page_notes = [], []

    def add_text(self, text: str) -> None:
        """Thêm chữ; mỗi \\f là một ranh giới trang."""
        for i, seg in enumerate(text.split("\f")):
            if i:
                self.flush()
            seg = seg.strip()
            if seg:
                self.lines.append(seg)

    # đoạn văn
    def run_text(self, el) -> str:
        parts: list[str] = []

        def rec(e) -> None:
            for c in e:
                tag = c.tag
                if tag == W_T:
                    parts.append(c.text or "")
                elif tag == W_TAB:
                    parts.append("\t")
                elif tag == W_BR:
                    parts.append("\f" if c.get(W_TYPE) == "page" else "\n")
                elif tag == W_CR:
                    parts.append("\n")
                elif tag == W_LRPB:
                    parts.append("\f")
                elif tag == W_NBH:
                    parts.append("-")
                elif tag in (W_FNREF, W_ENREF):
                    parts.append(self.note_ref(tag, c.get(W_ID)))
                elif tag == W_TXBX:
                    self.textbox(c)
                elif tag == MC_ALT:
                    # Choice và Fallback là hai bản của cùng nội dung: chỉ đọc một
                    branch = c.find(MC_CHOICE)
                    if branch is None:
                        branch = c.find(MC_FALLBACK)
                    if branch is not None:
                        rec(branch)
                elif tag in _SKIP:
                    continue
                else:
                    rec(c)

        rec(el)
        return "".join(parts)

    def note_ref(self, tag: str, nid: str | None) -> str:
        kind, src = ("footnote", self.footnotes) if tag == W_FNREF else ("endnote", self.endnotes)
        text = src.get(nid or "", "")
        if not text:
            return ""
        self.n_ref += 1
        self.page_notes.append(Note(kind=kind, text=text, ref=str(self.n_ref)))
        return f"[^{self.n_ref}]"

    def textbox(self, el) -> None:
        text = "\n".join(_plain_lines(el))
        if text:
            self.first_notes.append(Note(kind="textbox", text=text))

    def para_text(self, p_el) -> str:
        self.n_para += 1  # thân và ô bảng đều qua đây
        if self.n_para > MAX_PARAGRAPHS:
            raise ValueError("Tệp .docx có quá nhiều đoạn")
        text = self.run_text(p_el)
        ppr = p_el.find(W_PPR)
        if ppr is not None and ppr.find(W_PBB) is not None:
            text = "\f" + text
        p = self._Paragraph(p_el, self.doc._body)
        return self.numbering.paragraph_text(p, text)

    # bảng
    def cell_text(self, tc) -> str:
        out: list[str] = []
        for b in _blocks(tc, (W_P, W_TBL)):
            if b.tag == W_P:
                out.append(self.para_text(b))
            else:  # bảng lồng: dồn chữ vào ô cha
                out.extend(self.cell_text(c) for tr in _blocks(b, (W_TR,)) for c in _blocks(tr, (W_TC,)))
        return " ".join(out)

    def table_rows(self, tbl) -> list[str]:
        rows: list[str] = []
        for tr in _blocks(tbl, (W_TR,)):
            cells: list[str] = []
            brk = False
            for tc in _blocks(tr, (W_TC,)):
                tcpr = tc.find(W_TCPR)
                span, cont = 1, False
                if tcpr is not None:
                    gs = tcpr.find(W_SPAN)
                    if gs is not None and (gs.get(W_VAL) or "").isdigit():
                        span = int(gs.get(W_VAL))
                    vm = tcpr.find(W_VMERGE)
                    cont = vm is not None and vm.get(W_VAL) in (None, "continue")
                text = self.cell_text(tc)
                brk = brk or "\f" in text
                text = "" if cont else " ".join(text.replace("\f", " ").split()).replace("|", "/")
                cells.append(text)
                cells.extend([""] * (span - 1))  # ô gộp ngang: giữ chỗ cột
            if any(cells):
                rows.append(("\f" if brk else "") + "| " + " | ".join(cells) + " |")
        return rows

    # thân văn bản
    def walk(self, parent) -> None:
        for el in _blocks(parent, (W_P, W_TBL)):
            if el.tag == W_P:
                self.add_text(self.para_text(el))
            else:
                for row in self.table_rows(el):
                    self.add_text(row)


def extract_docx(path: Path) -> list[ExtractedPage]:
    from docx import Document

    with zipfile.ZipFile(path) as z:
        _check_zip_size(z)  # trước Document(): python-docx dựng cả cây XML trong bộ nhớ
        doc = Document(str(path))
        r = _DocxReader(doc, z)
        body = doc.element.body
        r.walk(body)
        r.flush(force=not r.pages)
        comments = _notes_part(z, "word/comments.xml", "comment")
        ranges = _comment_ranges(body)
        for cid, text in comments.items():
            if text:
                r.first_notes.append(Note(kind="comment", text=text, ref=ranges.get(cid) or None))
        seen: set[tuple[str, str]] = set()
        for name in sorted(z.namelist()):
            m = re.fullmatch(r"word/(header|footer)\d*\.xml", name)
            if not m:
                continue
            text = "\n".join(_plain_lines(_parse_part(z, name)))
            if text and (m.group(1), text) not in seen:
                seen.add((m.group(1), text))
                r.first_notes.append(Note(kind=m.group(1), text=text))
    r.pages[0].notes[:0] = r.first_notes
    return r.pages


# --- PDF ---


def _image_cover(page) -> float:
    """Tỷ lệ diện tích trang bị ảnh phủ (cộng dồn, chặn 1.0)."""
    area = float(page.width * page.height) or 1.0
    s = 0.0
    for im in page.images or []:
        w = min(im["x1"], page.width) - max(im["x0"], 0)
        h = min(im["bottom"], page.height) - max(im["top"], 0)
        if w > 0 and h > 0:
            s += w * h
    return min(1.0, s / area)


def _table_row_line(row: list[str | None]) -> str:
    cells = [" ".join((c or "").split()).replace("|", "/") for c in row]
    return "| " + " | ".join(cells) + " |" if any(cells) else ""


COL_GAP = 15.0  # pt: khoảng trống giữa hai ô; dãn chữ căn đều hiếm khi quá ~8 pt
COL_TOL = 4.0


def _text_lines(words: list[dict]) -> list[list[dict]]:
    lines: list[list[dict]] = []
    for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if lines and abs(lines[-1][0]["top"] - w["top"]) <= 3:
            lines[-1].append(w)
        else:
            lines.append([w])
    return [sorted(ln, key=lambda w: w["x0"]) for ln in lines]


def _segments(line: list[dict]) -> list[list[dict]]:
    segs = [[line[0]]]
    for w in line[1:]:
        if w["x0"] - segs[-1][-1]["x1"] > COL_GAP:
            segs.append([w])
        else:
            segs[-1].append(w)
    return segs


def _real_table(rows: list[list[str | None]]) -> bool:
    """find_tables còn bắt khung tô nền quanh đoạn văn (mỗi hàng một ô) và lưới mỗi chữ một ô của chữ căn đều:
    coi là chữ thường, không thì dòng "| Điều 15. … |" làm parser mất Điều."""
    filled = [[c for c in r if c and c.strip()] for r in rows]
    if not filled or sum(len(r) <= 1 for r in filled) >= 0.7 * len(filled):
        return False
    cells = [c for r in filled for c in r]
    return not (len(rows[0]) > 12 and sum(len(c) for c in cells) < 6 * len(cells))


def _borderless_tables(page) -> list[tuple[tuple[float, float, float, float], list[list[str]]]]:
    """Bảng không kẻ khung (Word bỏ viền): các dòng liên tiếp có ≥ 2 cụm chữ thẳng cột.

    Dòng chỉ có một cụm mà thẳng với cột thứ 2 trở đi là phần xuống dòng của ô.
    """
    lines = [(ln, _segments(ln)) for ln in _text_lines(page.extract_words())]
    blocks: list[list[tuple[list[dict], list[list[dict]]]]] = []
    cols: list[float] = []
    for ln, segs in lines:
        starts = [s[0]["x0"] for s in segs]
        if len(segs) >= 2:
            if blocks and blocks[-1] and ln[0]["top"] - blocks[-1][-1][0][0]["bottom"] < 20:
                blocks[-1].append((ln, segs))
            else:
                blocks.append([(ln, segs)])
                cols = []
            cols = sorted(set(cols) | {round(x) for x in starts})
        elif (
            blocks
            and blocks[-1]
            and ln[0]["top"] - blocks[-1][-1][0][0]["bottom"] < 20
            and any(abs(starts[0] - c) <= COL_TOL for c in cols[1:])
        ):
            blocks[-1].append((ln, segs))
        else:
            blocks.append([])
    out = []
    for blk in blocks:
        multi = [segs for _, segs in blk if len(segs) >= 2]
        if not (len(multi) >= 2 or any(len(s) >= 3 for s in multi)):
            continue
        starts = sorted({round(s[0]["x0"]) for _, segs in blk for s in segs})
        colx: list[float] = []
        for x in starts:  # gộp các mép trái gần nhau thành một cột
            if not colx or x - colx[-1] > COL_TOL:
                colx.append(x)
        rows: list[list[str]] = []
        for ln, _ in blk:
            cells = [""] * len(colx)
            # xếp theo từng chữ: ô dài sát cột bên có thể không đủ khoảng trống để tách cụm
            for w in ln:
                j = max((i for i, c in enumerate(colx) if c <= w["x0"] + COL_TOL), default=0)
                cells[j] = (cells[j] + " " + w["text"]).strip()
            if rows and not cells[0]:  # không có cột đầu: dòng tiếp của hàng trước
                rows[-1] = [(a + " " + b).strip() for a, b in zip(rows[-1], cells)]
            else:
                rows.append(cells)
        words = [w for ln, _ in blk for w in ln]
        bbox = (
            min(w["x0"] for w in words) - 1,
            min(w["top"] for w in words) - 1,
            max(w["x1"] for w in words) + 1,
            max(w["bottom"] for w in words) + 1,
        )
        out.append((bbox, rows))
    return out


_FN_START = re.compile(r"^(\d{1,3})[.)]?\s+\S")


def _median(xs: list[float]) -> float:
    xs = sorted(xs)
    return xs[len(xs) // 2]


def _line_size(ln: dict) -> float | None:
    sizes = [c["size"] for c in ln.get("chars", ()) if c["text"].strip()]
    return _median(sizes) if sizes else None


def _pdf_footnotes(page) -> tuple[dict[float, None], dict[float, list], list[tuple[str, str]]]:
    """Footnote của trang: chữ nhỏ hơn thân ≥ 12%, nửa dưới trang, mở đầu bằng số.

    Trả (top các dòng footnote, {top dòng thân: [(vị trí, số)]}, [(số, nội dung)]).
    Chữ nhỏ ở cuối trang không mở đầu bằng số (số trang, ghi chú khác) không bị coi là footnote.
    """
    lines = page.extract_text_lines(return_chars=True)
    sizes = [c["size"] for ln in lines for c in ln["chars"] if c["text"].strip()]
    if len(sizes) < 40:
        return {}, {}, []
    body = _median(sizes)
    foot_tops: dict[float, None] = {}
    notes: list[list[str]] = []
    started = False
    for ln in lines:
        sz = _line_size(ln)
        if ln["top"] < page.height * 0.5 or sz is None or sz > body * 0.88:
            if started:
                break
            continue
        m = _FN_START.match(ln["text"])
        if m:
            started = True
            notes.append([m.group(1), ln["text"][m.end(1):].lstrip(".) ").strip()])
        elif started:
            notes[-1][1] += " " + ln["text"].strip()
        else:
            continue
        foot_tops[ln["top"]] = None
    if not notes:
        return {}, {}, []
    nums = {n for n, _ in notes}
    marks: dict[float, list[tuple[int, str]]] = {}
    for ln in lines:
        if ln["top"] in foot_tops:
            continue
        # chỉ số mũ: chuỗi chữ số nhỏ hơn thân ≥ 20%; k = số ký tự không-trắng đứng trước nó
        k, run, start = 0, "", 0
        for c in [*ln["chars"], {"text": " ", "size": body}]:
            if c["text"].isdigit() and c["size"] < body * 0.8:
                if not run:
                    start = k
                run += c["text"]
            else:
                if run in nums and start > 0:
                    marks.setdefault(ln["top"], []).append((start, run))
                run = ""
            k += len(c["text"].strip())
    return foot_tops, marks, [(n, t) for n, t in notes if t]


def _mark_line(text: str, marks: list[tuple[int, tuple[str, str]]]) -> str:
    """Thay chuỗi chữ số mũ (vị trí k theo ký tự không-trắng) bằng [^ref]."""
    for k, ref in sorted(marks, reverse=True):
        seen = 0
        for i, ch in enumerate(text):
            if ch.isspace():
                continue
            if seen == k:
                j = i + len(ref[1])
                text = text[:i].rstrip() + f"[^{ref[0]}]" + text[j:]
                break
            seen += 1
    return text


def _pdf_text_with_tables(page, tables, skip=None, marks=None) -> str:
    """Chữ ngoài bảng theo thứ tự đọc + mỗi bảng thành các dòng | … | đặt theo toạ độ y.

    `tables`: [(bbox, rows)]. `skip`: top các dòng footnote bỏ khỏi thân; `marks`: {top: [(vị trí, (ref, số))]}.
    """
    boxes = [bbox for bbox, _ in tables]

    def outside(obj) -> bool:
        if "x0" not in obj or "top" not in obj:
            return True
        cx = (obj["x0"] + obj["x1"]) / 2
        cy = (obj["top"] + obj["bottom"]) / 2
        return not any(x0 <= cx <= x1 and top <= cy <= bottom for x0, top, x1, bottom in boxes)

    items: list[tuple[float, str]] = []
    for ln in page.filter(outside).extract_text_lines(return_chars=False):
        if skip and ln["top"] in skip:
            continue
        text = _mark_line(ln["text"], marks[ln["top"]]) if marks and ln["top"] in marks else ln["text"]
        items.append((ln["top"], text))
    for bbox, rows in tables:
        lines = [r for r in (_table_row_line(row) for row in rows) if r]
        if lines:
            items.append((bbox[1], "\n".join(lines)))
    items.sort(key=lambda it: it[0])
    return "\n".join(text for _, text in items)


def extract_pdf(path: Path) -> list[ExtractedPage]:
    import pdfplumber

    pages: list[ExtractedPage] = []
    n_ref = 0
    with pdfplumber.open(str(path)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            tables = [(t.bbox, rows) for t in page.find_tables() if _real_table(rows := t.extract())]
            if not tables:
                tables = _borderless_tables(page)
            foot_tops, marks, fnotes = _pdf_footnotes(page)
            notes: list[Note] = []
            refmap: dict[str, str] = {}
            for num, ftext in fnotes:
                n_ref += 1
                refmap[num] = str(n_ref)
                notes.append(Note(kind="footnote", text=ftext, ref=str(n_ref)))
            marks = {top: [(k, (refmap[n], n)) for k, n in d if n in refmap] for top, d in marks.items()}
            if tables or fnotes:
                text = _pdf_text_with_tables(page, tables, foot_tops, marks)
            else:
                text = page.extract_text()
            text = text or ""
            images = page.images or []
            kind, method, ocr = classify_pdf_page(
                text, len(images), bool(tables), _image_cover(page)
            )
            pages.append(
                ExtractedPage(
                    page_no=i,
                    text=text,
                    kind=kind,
                    extraction_method=method,
                    ocr_status=ocr,
                    notes=notes,
                )
            )
    return pages


# --- Ảnh, XLSX, DOC/RTF ---


def extract_image(path: Path) -> list[ExtractedPage]:
    from PIL import Image

    with Image.open(path) as img:
        n = getattr(img, "n_frames", 1) or 1
    return [
        ExtractedPage(page_no=i, text="", kind="image", extraction_method="image", ocr_status="cho_ocr")
        for i in range(1, n + 1)
    ]


_X = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_PR = "http://schemas.openxmlformats.org/package/2006/relationships"


def _x(tag: str) -> str:
    return f"{{{_X}}}{tag}"


def _si_text(el) -> str:
    # bỏ rPh (phiên âm) — chỉ lấy t của chuỗi chính
    return "".join(t.text or "" for t in el.iter(_x("t")) if t.getparent().tag != _x("rPh"))


def _col_index(ref: str) -> int:
    n = 0
    for ch in ref:
        if not ch.isalpha():
            break
        n = n * 26 + ord(ch.upper()) - 64
    return n - 1


def _cell_value(c, shared: list[str]) -> str:
    t = c.get("t")
    if t == "inlineStr":
        is_ = c.find(_x("is"))
        return _si_text(is_) if is_ is not None else ""
    v = c.find(_x("v"))
    raw = v.text if v is not None and v.text else ""
    if t == "s":
        return shared[int(raw)] if raw.isdigit() and int(raw) < len(shared) else ""
    if t == "b":
        return "TRUE" if raw == "1" else "FALSE"
    if t in ("str", "e") or not raw:
        return raw
    # shortcut: ngày tháng Excel hiện ra số serial, đọc numFmt trong styles.xml khi cần
    try:
        f = float(raw)
    except ValueError:
        return raw
    return str(int(f)) if f.is_integer() else repr(f)


def extract_xlsx(path: Path) -> list[ExtractedPage]:
    from lxml import etree

    pages: list[ExtractedPage] = []
    with zipfile.ZipFile(path) as z:
        _check_zip_size(z)
        names = set(z.namelist())
        shared: list[str] = []
        if "xl/sharedStrings.xml" in names:
            sroot = etree.fromstring(z.read("xl/sharedStrings.xml"))
            shared = [_si_text(si) for si in sroot.iter(_x("si"))]
        rels = {}
        if "xl/_rels/workbook.xml.rels" in names:
            for rel in etree.fromstring(z.read("xl/_rels/workbook.xml.rels")).iter(f"{{{_PR}}}Relationship"):
                target = rel.get("Target", "").lstrip("/")
                rels[rel.get("Id")] = target if target.startswith("xl/") else "xl/" + target
        wb = etree.fromstring(z.read("xl/workbook.xml"))
        for sheet in wb.iter(_x("sheet")):
            part = rels.get(sheet.get(f"{{{_R}}}id"), "")
            if part not in names:
                continue
            rows: list[list[str]] = []
            for row in etree.fromstring(z.read(part)).iter(_x("row")):
                cells: dict[int, str] = {}
                for i, c in enumerate(row.iter(_x("c"))):
                    col = _col_index(c.get("r") or "") if c.get("r") else i
                    val = " ".join(_cell_value(c, shared).split()).replace("|", "/")
                    if val:
                        cells[col] = val
                if cells:
                    rows.append([cells.get(j, "") for j in range(max(cells) + 1)])
            width = max((len(r) for r in rows), default=0)
            text = "\n".join(
                "| " + " | ".join(r + [""] * (width - len(r))) + " |" for r in rows
            )
            pages.append(
                ExtractedPage(
                    page_no=len(pages) + 1, text=text, kind="table", extraction_method="xlsx"
                )
            )
    return pages or [ExtractedPage(page_no=1, text="", kind="table", extraction_method="xlsx")]


def extract_file(path: Path) -> list[ExtractedPage]:
    suf = path.suffix.lower()
    if suf == ".docx":
        return extract_docx(path)
    if suf in {".doc", ".rtf"}:
        from soiluat.convert import converted_docx

        with converted_docx(path) as tmp:
            return extract_docx(tmp)
    if suf == ".pdf":
        return extract_pdf(path)
    if suf in IMAGE_SUFFIXES:
        return extract_image(path)
    if suf == ".xlsx":
        return extract_xlsx(path)
    if suf in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8", errors="replace")
        return [
            ExtractedPage(
                page_no=1, text=text, kind="text_ok", extraction_method="txt"
            )
        ]
    raise ValueError(f"Không hỗ trợ: {suf}")
