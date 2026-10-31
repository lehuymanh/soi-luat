"""Parser 3 tầng Điều/Khoản/Điểm; tầng 3 chia đoạn."""

from __future__ import annotations

import bisect
import re
from dataclasses import dataclass, field, replace

from soiluat.fold import fold_search, normalize_display

# "Điều 1. Tên", "Điều 4.Hiệu lực"
DIEU_STD = re.compile(
    r"^Điều\s+(\d+[a-z]?)\.\s*(.*)$",
    re.IGNORECASE,
)
# nới: "ĐIỀU 1:", "Điều 3 .", "Điều1.", OCR "Đieu 1." — vẫn cần dấu . hoặc : sau số
DIEU_LOOSE = re.compile(
    r"^[ĐDđd]i[eêềéèẽẻ]\s*u\s*(\d+[a-z]?)\s*[.:]\s*(.*)$",
    re.IGNORECASE,
)
# OCR đọc hỏng chữ "Điều" ("Đ1eu 12.", "Đlgu 20.", "Dieu 3:"): cần có số và dấu . hoặc : theo sau
DIEU_OCR = re.compile(
    r"^[ĐDđd][1iIl!íìỉĩị]?[eêềéèẽẻếểệgqo]{1,2}\s*[uưgờ]\s*(\d+[a-z]?)\s*[.:]\s*(\S.*)$",
)
# số Điều bị OCR đọc thành chữ cái: "Điều M Thẩm quyền…" (suy từ số Điều trước)
DIEU_NUM_LETTER = re.compile(r"^Điều\s+[A-Z]{1,2}\s*[.:]?\s+([A-ZĐ][^\n]{3,})$")
# "Điều thứ hai." / "Điều thứ 2:"
DIEU_THU = re.compile(
    r"^[ĐDđd]i[eêềéèẽẻ]u\s+thứ\s+([^.:]{1,30}?)\s*[.:]\s*(.*)$",
    re.IGNORECASE,
)
# không dấu câu sau số (OCR mất dấu): chỉ nhận khi tên Điều viết hoa
DIEU_BARE = re.compile(r"^Điều\s*(\d+[a-z]?)\s+(\S.*)$", re.IGNORECASE)
# "1.", "1)", "1/" — tối đa 2 chữ số để không nhận năm "2023."
KHOAN = re.compile(r"^(\d{1,2})[.)/](?!\d)\s*(.*)$")
DIEM_PAREN = re.compile(r"^([a-zđ])\)\s*(.*)$", re.IGNORECASE)
DIEM_DOT = re.compile(r"^([a-zđ])\.\s+(.*)$")
CHUONG_MUC = re.compile(r"^(Chương|Mục|Phần)\s+([IVXLCDM]+|\d+)\b", re.IGNORECASE)
# "Số: 15/2020/NĐ-CP", "Luật số: 17/2026/QH16", "Số: 388 /2026/NĐ-CP" (số điền tay, cách trước "/");
# phân biệt hoa thường: dòng căn cứ bị ngắt "số 40/2019/QH14." không phải dòng số hiệu
SO_LINE = re.compile(r"^(?:(?:Luật|Bộ luật|Pháp lệnh|Nghị quyết|Lệnh)\s+số\s*:|Số\s*[:.]?|SỐ\s*[:.]?)\s*\d+\s*/")
SO_HIEU_SPACED = re.compile(r"(\d+)\s*/\s*(\d{4})\s*/\s*([A-ZĐ0-9][A-ZĐ0-9-]*)", re.IGNORECASE)
TABLE_ROW = re.compile(r"^\|.*\|$")
# tên văn bản ở trích dẫn: "Điều 6 Nghị định này"
DOC_WORDS = ("nghi dinh", "thong tu", "luat", "bo luat", "quyet dinh", "nghi quyet", "phap lenh")

HEADER_HINTS = (
    "cong hoa xa hoi",
    "doc lap - tu do",
    "can cu luat",
    "can cu nghi dinh",
)
SIGN_HINTS = ("kt. bo truong", "noi nhan", "tm. chinh phu", "thu tuong")
SIGN_WORDS = ("kt.", "tm.", "q.", "truong", "thu tuong", "chu tich", "noi nhan")
LOAI_LINES = (
    "nghi dinh", "thong tu", "thong tu lien tich", "quyet dinh", "luat", "bo luat",
    "nghi quyet", "chi thi", "phap lenh", "cong van",
)

_SO = {
    "mot": 1, "nhat": 1, "hai": 2, "ba": 3, "bon": 4, "tu": 4, "nam": 5, "lam": 5,
    "sau": 6, "bay": 7, "tam": 8, "chin": 9,
}

NOTE_TITLES = {
    "footnote": "Chú thích",
    "endnote": "Chú thích cuối",
    "comment": "Nhận xét",
    "textbox": "Hộp văn bản",
    "header": "Đầu trang",
    "footer": "Chân trang",
}


@dataclass
class ParsedUnit:
    level: str
    addr_part: str
    title: str
    text: str
    parent_addr: str | None
    confidence: float
    from_table: bool = False
    line_from: int = -1
    line_to: int = -1
    page_from: int | None = None
    page_to: int | None = None


@dataclass
class ParseResult:
    units: list[ParsedUnit] = field(default_factory=list)
    so_hieu: str | None = None
    c_phu: float = 0.0
    c_lien_tuc: float = 0.0
    c_khoan: float = 0.0
    s: float = 0.0
    tier: int = 3
    n_low_conf: int = 0


def _is_header_or_sign(line: str) -> bool:
    low = fold_search(line)
    if any(h in low for h in HEADER_HINTS):
        return True
    if any(h in low for h in SIGN_HINTS):
        return True
    return False


def so_tu_chu(words: str) -> int | None:
    """'hai' → 2, 'mười lăm' → 15, 'hai mươi' → 20, '7' → 7."""
    w = fold_search(words).split()
    if len(w) == 1 and w[0].isdigit():
        return int(w[0])
    if not w or any(x not in _SO and x != "muoi" for x in w):
        return None
    if "muoi" not in w:
        return _SO[w[0]] if len(w) == 1 else None
    i = w.index("muoi")
    if i > 1 or len(w) - i > 2:
        return None
    tens = _SO[w[0]] if i == 1 else 1
    ones = _SO[w[i + 1]] if len(w) > i + 1 else 0
    return tens * 10 + ones


# chữ Latin/Việt: A-Z, 0-9, À-Ơ (đến U+01B0), Ạ-ỹ (U+1EA0..U+1EF9); ˆ (U+02C6), ‹, | … là rác
_JUNK_HEAD = re.compile(r"^(?:[^A-Za-z0-9À-ưẠ-ỹ“\"]+|[A-ZĂÂ]{1,2}(?=Đ[iíìỉ]))")  # ký tự rác từ vết mực/mộc: "ˆ Điều 21.", "ĂĐỉều 50."


def _dieu_match(line: str) -> tuple[str, str, float] | None:
    s = line.strip()
    if not s:
        return None
    m = DIEU_STD.match(s)
    if m:
        return m.group(1), (m.group(2) or "").strip(), 1.0
    clean = _JUNK_HEAD.sub("", s)
    if clean != s:
        m = DIEU_STD.match(clean) or DIEU_LOOSE.match(clean)
        if m:
            return m.group(1), (m.group(2) or "").strip(" |"), 0.65
        s = clean
    m = DIEU_THU.match(s)
    if m:
        n = so_tu_chu(m.group(1))
        return (str(n), (m.group(2) or "").strip(), 0.65) if n else None
    m = DIEU_LOOSE.match(s)
    if m:
        return m.group(1), (m.group(2) or "").strip(), 0.65
    m = DIEU_OCR.match(s)
    if m:
        return m.group(1), (m.group(2) or "").strip(), 0.6
    m = DIEU_BARE.match(s)
    if m:
        title = m.group(2).strip()
        if title[0].isupper() and not fold_search(title).startswith(DOC_WORDS):
            return m.group(1), title, 0.6
    return None


def _preamble_line(line: str) -> bool:
    """Phần mở đầu chuẩn: quốc hiệu, cơ quan, Số:, nơi + ngày, tên loại, Căn cứ…"""
    f = fold_search(line)
    return (
        line.isupper()
        or _is_header_or_sign(line)
        or bool(SO_LINE.match(line))
        or f.startswith(("can cu", "theo de nghi"))
        or bool(re.search(r",\s*ngày\s+\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4}", line, re.I))
    )


def _quote_state(line: str, open_: bool) -> bool:
    """Còn trong khối trích dẫn sau dòng này không (“ ” của Word và " thẳng).

    Khối chỉ mở bằng ngoặc ở đầu dòng hoặc ngay sau dấu ":" ("… như sau: “Điều 5."). Ngoặc giữa câu là
    trích ngắn trên một dòng, hoặc ký tự OCR chèn nhầm ('bồ "sung'), không được giữ trạng thái sang dòng sau.
    """
    s = line.strip()
    depth = 1 if open_ else 0
    block = open_
    for k, ch in enumerate(s):
        if ch not in '“”"':
            continue
        if 0 < k < len(s) - 1 and s[k - 1].isalpha() and s[k + 1].isalpha():
            continue  # ngoặc kẹp giữa chữ: OCR chèn nhầm ('m“ểp')
        if ch == '"':  # ngoặc thẳng: mở nếu sát chữ/số phía sau, còn lại là đóng
            ch = "“" if k + 1 < len(s) and s[k + 1].isalnum() and (k == 0 or not s[k - 1].isalnum()) else "”"
        if ch == "“":
            if depth == 0:
                block = k == 0 or s[:k].rstrip().endswith(":")
            depth += 1
        elif depth:
            depth -= 1
    return depth > 0 and block


def _quoted_dieu_no(line: str) -> int | None:
    """Số của "Điều n." đứng đầu dòng, có hay không có ngoặc mở."""
    m = re.match(r'^[“"]?\s*Điều\s+(\d+)(?!\d)', line.strip())
    return int(m.group(1)) if m else None


def _next_own_dieu(line: str, current_dieu: ParsedUnit | None) -> bool:
    """Dòng là "Điều n. Tên" với n = số Điều hiện tại + 1 (hoặc 1 khi chưa có Điều)."""
    m = DIEU_STD.match(line.strip())
    if not m or not m.group(1).isdigit() or not m.group(2)[:1].isupper():
        return False
    cur = _dieu_num_key(current_dieu.addr_part)[0] if current_dieu else 0
    return int(m.group(1)) == cur + 1


def _mid_sentence(prev: str) -> bool:
    """Dòng trước bị ngắt giữa câu (không kết thúc bằng . ; : …)."""
    p = prev.rstrip()
    return bool(p) and p[-1] not in ".;:!?)\"”'"


def parse_so_hieu_from_text(text: str) -> str | None:
    from soiluat.sohieu import find_so_hieu

    # ưu tiên dòng "Số: …" ở phần đầu
    for ln in (text or "").split("\n", 40)[:40]:
        if SO_LINE.match(ln.strip()):
            m = SO_HIEU_SPACED.search(ln)
            if m:
                return "/".join(m.groups())
    return find_so_hieu(text or "")


def parse_structure(
    text: str,
    so_hieu: str | None = None,
    *,
    force_doan: bool = False,
) -> ParseResult:
    text = normalize_display(text or "")
    so_hieu = so_hieu or parse_so_hieu_from_text(text)
    prefix = so_hieu or "doc"
    lines = text.replace("\r\n", "\n").split("\n")
    nonempty = [(i, ln) for i, ln in enumerate(lines) if ln.strip()]
    if not force_doan:
        # quốc hiệu / chữ ký không tính vào độ phủ C_phu
        body = "\n".join(ln for _, ln in nonempty if not _is_header_or_sign(ln))
        try:
            result = _parse_lines(lines, body)
        except Exception:  # noqa: BLE001 — lỗi parse thì chia đoạn, không mất file
            result = None
        if result is not None:
            result.so_hieu = so_hieu
            return result
    fb = _fallback_paragraphs(nonempty, prefix)
    fb.so_hieu = so_hieu
    return fb


def _parse_lines(lines: list[str], body: str) -> ParseResult | None:
    units: list[ParsedUnit] = []
    used: set[str] = set()
    current_dieu: ParsedUnit | None = None
    current_khoan: ParsedUnit | None = None
    current_diem: ParsedUnit | None = None  # dòng nối của điểm thuộc về điểm, không dồn vào khoản
    in_quotes = False
    q_dieu: int | None = None  # số Điều đang được trích trong khối ngoặc
    in_sign = False
    skip_upper = False
    prev = ""
    orphan: ParsedUnit | None = None
    n_orphan = 0
    seen_pre = False

    def uniq(addr: str) -> str:
        # trùng số → hậu tố ~n (H4), không bao giờ trùng path
        out, n = addr, 1
        while out in used:
            n += 1
            out = f"{addr}~{n}"
        used.add(out)
        return out

    def add_line(line: str, i: int) -> None:
        u = current_diem or current_khoan or current_dieu
        if u is None:
            return
        u.text += "\n" + line
        u.line_to = i
        if TABLE_ROW.match(line):
            u.from_table = True

    def new_unit(level: str, addr: str, title: str, text: str, parent: str | None,
                 conf: float, i: int) -> ParsedUnit:
        u = ParsedUnit(level, uniq(addr), title, text, parent, conf, line_from=i, line_to=i)
        if TABLE_ROW.match(text):
            u.from_table = True
        units.append(u)
        return u

    for i, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line:
            continue
        last, prev = prev, line
        was_quoted = in_quotes
        in_quotes = _quote_state(line, in_quotes)
        qn = _quoted_dieu_no(line)
        if was_quoted and _next_own_dieu(line, current_dieu) and not (q_dieu is not None and qn == q_dieu + 1):
            # shortcut: OCR làm mất ngoặc đóng thì khối trích dẫn không bao giờ đóng, nên "Điều n+1." đúng thứ tự
            # của văn bản coi là Điều của chính nó, trừ khi nó nối tiếp Điều đang được trích ("Điều 1, Điều 2" của luật
            # gốc). Hở: Điều trích có số = số Điều của văn bản + 1 mà ngoặc đóng bị mất thì vẫn bị nuốt.
            was_quoted = in_quotes = False
        if was_quoted or in_quotes:
            q_dieu = qn if qn is not None else q_dieu
        else:
            q_dieu = None
        # dòng đóng ngoặc (… ”) vẫn thuộc phần trích dẫn
        if (in_quotes or was_quoted) and current_dieu is not None:
            add_line(line, i)
            continue
        mid = _mid_sentence(last) and not last.isupper()
        cont = line[0].islower() and mid

        dm = None if cont else _dieu_match(line)
        if dm is None and not cont and not mid and not in_quotes:
            lm = DIEU_NUM_LETTER.match(_JUNK_HEAD.sub("", line))
            if lm and not fold_search(lm.group(1)).startswith(DOC_WORDS):
                nxt = (_dieu_num_key(current_dieu.addr_part)[0] if current_dieu else 0) + 1
                dm = (str(nxt), lm.group(1).strip(), 0.5)
        if dm and mid and (not dm[1] or dm[1][0].islower() or dm[2] < 0.65):
            dm = None  # "…theo quy định tại\nĐiều 5." là trích dẫn, không phải Điều mới
        if dm and not in_quotes:
            num, title, conf = dm
            in_sign = skip_upper = False
            current_dieu = new_unit("dieu", f"D{num}", title, title, None, conf, i)
            current_khoan = current_diem = None
            continue
        if current_dieu is None:
            # trước Điều đầu tiên: bỏ phần mở đầu chuẩn, giữ khoản/điểm mồ côi (vd. ảnh trang 2)
            orphan_k = not cont and (KHOAN.match(line) or DIEM_PAREN.match(line))
            if orphan is None and (_preamble_line(line) or CHUONG_MUC.match(line)):
                seen_pre = True
                continue
            if orphan is None and seen_pre and not orphan_k:
                continue  # trích yếu, "Chính phủ ban hành…"
            if CHUONG_MUC.match(line) or (skip_upper and line.isupper()):
                skip_upper = True
                continue
            skip_upper = False
            if orphan is None or KHOAN.match(line) and not cont:
                n_orphan += 1
                orphan = new_unit("doan", f"p1.para{n_orphan}", "", line, None, 0.5, i)
            else:
                orphan.text += "\n" + line
                orphan.line_to = i
                orphan.from_table = orphan.from_table or bool(TABLE_ROW.match(line))
            continue
        if in_sign:
            continue
        if cont and current_khoan is None and current_dieu is not None \
                and current_dieu.text == current_dieu.title:
            # tên Điều bị ngắt dòng
            current_dieu.title = current_dieu.text = f"{current_dieu.title} {line}".strip()
            current_dieu.line_to = i
            continue
        if len(line) < 20 and fold_search(line).startswith("noi nhan"):
            in_sign = True  # khối nơi nhận/chữ ký: bỏ tới Điều kế tiếp
            continue
        if CHUONG_MUC.match(line):
            skip_upper = True  # tên Chương/Mục ở dòng sau, viết hoa
            continue
        if skip_upper and line.isupper():
            continue
        skip_upper = False

        km = None if cont else KHOAN.match(line)
        if km and current_dieu is not None:
            num, rest = km.group(1), km.group(2)
            current_diem = None
            current_khoan = new_unit(
                "khoan", f"{current_dieu.addr_part}.K{num}", "", rest,
                current_dieu.addr_part, 0.9, i,
            )
            continue

        pm = DIEM_PAREN.match(line)
        if not pm and not cont and not _mid_sentence(last):
            pm = DIEM_DOT.match(line)
        if pm and current_khoan is not None:
            letter, rest = pm.group(1).lower(), pm.group(2)
            current_diem = new_unit(
                "diem", f"{current_khoan.addr_part}.Đ{letter}", "", rest,
                current_khoan.addr_part, 0.85, i,
            )
            continue

        add_line(line, i)

    for u in units:
        u.text = u.text.strip()

    dieu_units = [u for u in units if u.level == "dieu"]
    if not dieu_units:
        return None
    result = ParseResult(units=units, tier=1)
    _score(result, body)
    if any(u.confidence < 0.9 for u in dieu_units):
        result.tier = 2
    result.n_low_conf = sum(1 for u in units if u.confidence < 0.75)
    if result.s < 0.60:
        return None
    return result


def _fallback_paragraphs(body: list[tuple[int, str]], prefix: str) -> ParseResult:
    # (từ, số dòng) để biết đoạn nằm ở trang nào
    words = [(w, i) for i, ln in body for w in ln.split()]
    spans: list[tuple[int, int]] = []
    if len(words) <= 400:
        if words:
            spans.append((0, len(words)))
    else:
        start = 0
        while start < len(words):
            end = min(len(words), start + 350)
            spans.append((start, end))
            if end == len(words):
                break
            start = max(start + 1, end - 50)
    units = [
        ParsedUnit(
            level="doan",
            addr_part=f"p1.para{k}",
            title="",
            text=" ".join(w for w, _ in words[a:b]) if len(spans) > 1 else
            "\n".join(ln.strip() for _, ln in body).strip(),
            parent_addr=None,
            confidence=0.3,
            line_from=words[a][1],
            line_to=words[b - 1][1],
        )
        for k, (a, b) in enumerate(spans, start=1)
    ]
    return ParseResult(units=units, tier=3, s=0.0, n_low_conf=len(units))


def assign_pages(units: list[ParsedUnit], page_nos: list[int], texts: list[str]) -> None:
    """page_from/page_to thật từ ranh giới trang; texts nối bằng '\\n\\n' khi parse."""
    if not page_nos:
        return
    starts: list[int] = []
    cur = 0
    for t in texts:
        starts.append(cur)
        cur += (t or "").replace("\r\n", "\n").count("\n") + 2
    by_addr = {u.addr_part: u for u in units}
    for u in reversed(units):  # Điều phủ cả khoản/điểm con
        par = by_addr.get(u.parent_addr or "")
        if par is not None and u.line_to > par.line_to:
            par.line_to = u.line_to
    for u in units:
        if u.line_from < 0 or u.page_from is not None:
            continue
        i = max(0, bisect.bisect_right(starts, u.line_from) - 1)
        j = max(i, bisect.bisect_right(starts, u.line_to) - 1)
        u.page_from, u.page_to = page_nos[i], page_nos[j]


_LABEL = re.compile(r"^(?:Điều\s+\d+[a-zA-Z]?\.|\d+\.|[a-zđ][)\.])\s+")


def _unit_with_text(body: list[ParsedUnit], ref: str) -> ParsedUnit | None:
    """Đơn vị chứa đoạn được nhận xét; ref có thể kèm nhãn "Điều 6." / "1." mà text đơn vị không có."""
    ref = " ".join(ref.split())
    for cand in (ref, _LABEL.sub("", ref)):
        if len(cand) <= 3:
            continue
        hit = next((u for u in body if cand in " ".join(u.text.split())), None)
        if hit is not None:
            return hit
    return None


def add_notes(result: ParseResult, pages) -> None:
    """Ghi chú của trang → đơn vị ghi_chu GC1… (H4)."""
    body = [u for u in result.units if u.level != "ghi_chu"]
    k = sum(1 for u in result.units if u.level == "ghi_chu")
    for p in pages:
        for n in getattr(p, "notes", None) or []:
            text = (getattr(n, "text", "") or "").strip()
            if not text:
                continue
            k += 1
            ref = getattr(n, "ref", None)
            parent = None
            if ref:
                mark = f"[^{ref}]"
                hit = next((u for u in body if mark in u.text), None)
                if hit is None:  # comment: ref là đoạn chữ được nhận xét
                    hit = _unit_with_text(body, ref)
                parent = hit.addr_part if hit else None
            result.units.append(
                ParsedUnit(
                    level="ghi_chu",
                    addr_part=f"GC{k}",
                    title=NOTE_TITLES.get(getattr(n, "kind", ""), "Ghi chú"),
                    text=text,
                    parent_addr=parent,
                    confidence=1.0,
                    page_from=p.page_no,
                    page_to=p.page_no,
                )
            )


def parse_pages(pages, so_hieu: str | None = None, *, force_doan: bool = False) -> ParseResult:
    """Parse danh sách trang (có .page_no, .text, tuỳ chọn .notes): gắn số trang + ghi chú."""
    texts = [p.text or "" for p in pages]
    r = parse_structure("\n\n".join(texts), so_hieu, force_doan=force_doan)
    assign_pages(r.units, [p.page_no for p in pages], texts)
    add_notes(r, pages)
    return r


def _is_loai_line(line: str) -> bool:
    s = line.strip()
    return bool(s) and s.isupper() and fold_search(s) in LOAI_LINES


def _header_line(line: str) -> bool:
    f = fold_search(line)
    if any(h in f for h in HEADER_HINTS[:2]):
        return True
    s = line.strip()
    return bool(s) and s.isupper() and len(s) < 60 and not any(w in f for w in SIGN_WORDS)


def _first_dieu_num(lines: list[str]) -> str | None:
    for ln in lines:
        dm = _dieu_match(ln)
        if dm:
            return dm[0]
    return None


def doc_cuts(lines: list[str]) -> list[int]:
    """Chỉ số dòng bắt đầu văn bản thứ 2, 3…: có khối đầu (Số: …, tên loại) và Điều về lại 1."""
    cuts: list[int] = []
    last = 0
    for i, ln in enumerate(lines):
        if not SO_LINE.match(ln.strip()):
            continue
        if _first_dieu_num(lines[last:i]) is None:
            continue
        if not any(_is_loai_line(x) for x in lines[max(0, i - 4): i + 6]):
            continue
        if _first_dieu_num(lines[i + 1:]) != "1":
            continue
        start = i
        while start - 1 > last and i - start < 6 and _header_line(lines[start - 1]):
            start -= 1
        cuts.append(start)
        last = start
    return cuts


def split_documents(pages: list) -> list[list]:
    """Tách file chứa nhiều văn bản thành nhiều nhóm trang (giữ số trang gốc)."""
    flat: list[tuple[int, str]] = []
    for pi, p in enumerate(pages):
        for ln in normalize_display(p.text or "").replace("\r\n", "\n").split("\n"):
            flat.append((pi, ln))
    cuts = doc_cuts([ln for _, ln in flat])
    if not cuts:
        return [list(pages)]
    bounds = [0, *cuts, len(flat)]
    segs: list[list] = []
    for a, b in zip(bounds, bounds[1:]):
        by_page: dict[int, list[str]] = {}
        for pi, ln in flat[a:b]:
            by_page.setdefault(pi, []).append(ln)
        segs.append([replace(pages[pi], text="\n".join(lns)) for pi, lns in by_page.items()])
    # trang bị cắt đôi: ghi chú theo mốc [^n], không có mốc thì về văn bản đầu
    copies: dict[int, list] = {}
    for seg in segs:
        for pc in seg:
            copies.setdefault(pc.page_no, []).append(pc)
    for cs in copies.values():
        notes = list(getattr(cs[0], "notes", None) or [])
        if len(cs) < 2 or not notes:
            continue
        for c in cs:
            c.notes = []
        for n in notes:
            ref = getattr(n, "ref", None)
            tgt = next((c for c in cs if ref and f"[^{ref}]" in c.text), cs[0])
            tgt.notes.append(n)
    return segs


def _dieu_num_key(addr: str) -> tuple[int, str]:
    m = re.search(r"(?:^|[.#])D(\d+)([a-z]?)", addr, re.I)
    if not m:
        m = re.match(r"D(\d+)([a-z]?)", addr, re.I)
    if not m:
        return (0, "")
    return (int(m.group(1)), (m.group(2) or "").lower())


def _pair_normal(prev: tuple[int, str], cur: tuple[int, str]) -> bool:
    n_i, s_i = prev
    n_j, s_j = cur
    if cur == (1, "") and n_i > 1:
        return True  # đánh số lại từ 1: văn bản ghép, cấu trúc vẫn tốt
    if not s_i and n_j == n_i + 1 and not s_j:
        return True
    if not s_i and n_j == n_i and s_j == "a":
        return True
    if s_i and n_j == n_i and s_j and ord(s_j[0]) == ord(s_i[0]) + 1:
        return True
    if s_i and n_j == n_i + 1 and not s_j:
        return True
    return False


def _score(result: ParseResult, body: str) -> None:
    dieu = [u for u in result.units if u.level == "dieu"]
    body_len = max(1, len(body))
    in_dieu = sum(
        len(u.text) for u in result.units if u.level in ("dieu", "khoan", "diem", "doan")
    )
    result.c_phu = min(1.0, in_dieu / body_len)

    if not dieu:
        result.c_lien_tuc = 0.0
        result.c_khoan = 0.0
        result.s = 0.0
        return

    nums = [_dieu_num_key(u.addr_part) for u in dieu]
    if len(dieu) == 1:
        result.c_lien_tuc = 1.0
    else:
        abnormal = 0
        for i in range(len(nums) - 1):
            if not _pair_normal(nums[i], nums[i + 1]):
                abnormal += 1
        result.c_lien_tuc = 1.0 - abnormal / max(1, len(dieu) - 1)

    kids: dict[str, list[int]] = {}
    for u in result.units:
        if u.level == "khoan":
            m = re.search(r"\.K(\d+)(?:~\d+)?$", u.addr_part)
            if m:
                kids.setdefault(u.parent_addr or "", []).append(int(m.group(1)))
    # khoản đánh lại từ 1 giữa chừng: tiêu đề Điều sau bị mất (mộc đè, OCR hỏng), thứ tự khoản vẫn đúng
    good_k = sum(
        1 for d in dieu
        if all(b in (a + 1, 1) for a, b in zip([0, *kids.get(d.addr_part, [])], kids.get(d.addr_part, [])))
    )
    result.c_khoan = good_k / len(dieu)
    result.s = max(0.0, min(1.0, 0.4 * result.c_phu + 0.3 * result.c_lien_tuc + 0.3 * result.c_khoan))
