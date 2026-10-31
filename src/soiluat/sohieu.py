"""Nhận diện số hiệu và 'Điều n' trên chuỗi gõ gốc."""

from __future__ import annotations

import re
import unicodedata

from soiluat.fold import fold_search

# C2 — giống 3.1 / 4.3.3
SO_HIEU_RE = re.compile(r"(?i)(\d+/\d{4}/[A-ZĐ0-9-]+)")
# F4: thiếu đuôi; (?<!\d) để 15/2020 không khớp trong 115/2020; (?<![\d/]) và "tháng " để ngày 05/02/2021 và
# "tháng 10/2020" không bị đọc là số hiệu 02/2021, 10/2020
SO_HIEU_PREFIX_RE = re.compile(r"(?i)(?<![\d/])(?<!tháng\s)(\d+/\d{4})(?!/[A-ZĐ0-9-])")
DIEU_RE = re.compile(r"Điều\s+(\d+[a-z]?)", re.IGNORECASE)
# "khoản 2", "điểm a" trong trích dẫn "điểm a khoản 2 Điều 5": địa chỉ chứ không phải từ khoá
KHOAN_DIEM_RE = re.compile(r"(?i)\b(?:khoản\s+\d+[a-z]?|điểm\s+[a-zđ])\b")


def find_so_hieu(raw: str) -> str | None:
    m = SO_HIEU_RE.search(raw or "")
    return m.group(1) if m else None


def find_so_hieu_prefix(raw: str) -> str | None:
    if find_so_hieu(raw):
        return None
    m = SO_HIEU_PREFIX_RE.search(raw or "")
    return m.group(1) if m else None


def find_dieu_so(raw: str) -> str | None:
    m = DIEU_RE.search(unicodedata.normalize("NFC", raw or ""))  # chữ dán từ nguồn NFD vẫn khớp "Điều"
    return m.group(1) if m else None


_CITE_BOILER_RE = re.compile(
    r"(?i)\b(nghị định|thông tư liên tịch|thông tư|luật|quyết định)\b|\bsố\b"
)


def citation_remainder(raw: str) -> str:
    """Phần còn lại sau khi bỏ số hiệu / Điều n / từ loại văn bản."""
    s = unicodedata.normalize("NFC", raw or "")
    s = SO_HIEU_RE.sub(" ", s)
    s = SO_HIEU_PREFIX_RE.sub(" ", s)
    # shortcut: "khoản 2 Điều 5 <số hiệu>" ra cả Điều 5 (không tìm chữ "khoản", "2"), chưa thu hẹp tới khoản 2;
    # nâng khi compact và phần trích chọn được đúng khoản (C6/F5, xếp ở P2)
    if DIEU_RE.search(s):
        s = KHOAN_DIEM_RE.sub(" ", s)
    s = DIEU_RE.sub(" ", s)
    s = _CITE_BOILER_RE.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip(" ,.;:-")


def so_hieu_search_key(so_hieu: str | None) -> str:
    return fold_search(so_hieu or "")


def infer_loai(so_hieu: str | None) -> str | None:
    key = fold_search(so_hieu or "")
    if not key:
        return None
    if "nd-cp" in key or "/nd" in key:
        return "nghi_dinh"
    if "/tt" in key:
        return "thong_tu"
    if "/qd" in key:
        return "quyet_dinh"
    return None


LOAI_TEN = {
    "nghi dinh": "nghi_dinh",
    "thong tu": "thong_tu",
    "thong tu lien tich": "thong_tu",
    "quyet dinh": "quyet_dinh",
    "luat": "luat",
    "bo luat": "luat",
    "nghi quyet": "nghi_quyet",
    "chi thi": "chi_thi",
    "phap lenh": "phap_lenh",
    "cong van": "cong_van",
}
_NGAY = r"ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})"
BAN_HANH_RE = re.compile(r",\s*" + _NGAY, re.IGNORECASE)
_TU_NGAY = (
    r"(?:\s+[^\s\d]{1,6}){0,3}?\s+từ\s+ngày\s+(?:"  # "thi hành", "kể", và chữ OCR hỏng ("thị hành", "kê")
    r"(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})|(\d{1,2})/(\d{1,2})/(\d{4}))"
)
HIEU_LUC_RE = re.compile(r"có hiệu lực" + _TU_NGAY, re.IGNORECASE)
# câu chính: "Luật này có hiệu lực …" (Điều hiệu lực), khác câu chuyển tiếp hay đoạn trích của luật khác
HIEU_LUC_NAY_RE = re.compile(
    r"(?:Luật|Bộ luật|Pháp lệnh|Nghị định|Nghị quyết|Thông tư|Quyết định|Chỉ thị)\s+này\s+có hiệu lực" + _TU_NGAY,
    re.IGNORECASE,
)
# câu kết của luật/nghị quyết Quốc hội: "… khóa XVI, Kỳ họp … thông qua ngày 24 tháng 8 năm 2026."
THONG_QUA_RE = re.compile(r"thông\s+qua\s+ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})", re.IGNORECASE)


def _head(text: str, n: int = 40) -> list[str]:
    return (text or "").split("\n", n)[:n]


def infer_loai_text(text: str, so_hieu: str | None = None) -> str | None:
    """Tên loại ở đầu văn bản (dòng viết hoa) → số hiệu → 'V/v' của công văn → None."""
    head = _head(text)
    for ln in head:
        s = ln.strip()
        if s and s.isupper() and fold_search(s) in LOAI_TEN:
            return LOAI_TEN[fold_search(s)]
    loai = infer_loai(so_hieu)
    if loai:
        return loai
    if any(re.match(r"(?i)\s*V/v\b", ln) for ln in head):
        return "cong_van"
    return None


def _iso(d: str, m: str, y: str) -> str | None:
    from datetime import date

    try:
        return date(int(y), int(m), int(d)).isoformat()
    except ValueError:
        return None


def find_ngay_ban_hanh(text: str) -> str | None:
    """'Hà Nội, ngày 15 tháng 9 năm 2023' ở phần đầu → '2023-09-15'."""
    m = BAN_HANH_RE.search("\n".join(_head(text)))
    if m:
        return _iso(*m.groups())
    # Luật, Nghị quyết của Quốc hội không có dòng "Hà Nội, ngày…": ngày thông qua ở câu kết "… khóa XVI, Kỳ họp … thông qua
    # ngày …" (sau đó còn có thể có phụ lục dài). Cần "Kỳ họp" ngay trước: "Căn cứ … Quốc hội thông qua ngày …" không tính.
    t = text or ""
    last = None
    for m in THONG_QUA_RE.finditer(t):
        if "ky hop" in _fold1(t[max(0, m.start() - 200): m.start()]):
            last = m
    return _iso(*last.groups()) if last else None


def find_ngay_hieu_luc(text: str) -> str | None:
    m = HIEU_LUC_NAY_RE.search(text or "") or HIEU_LUC_RE.search(text or "")
    if not m:
        return None
    g = m.groups()
    return _iso(*g[:3]) if g[0] else _iso(*g[3:])


def _fold1(text: str) -> str:
    """Bỏ dấu từng ký tự (giữ đúng độ dài để cắt trên chuỗi gốc), chữ thường."""
    out = []
    for ch in text:
        b = unicodedata.normalize("NFD", ch)[0]
        out.append("d" if ch in "Đđ" else b.lower())
    return "".join(out)


_CO_QUAN_RE = re.compile(
    r"(uy ban thuong vu quoc hoi|qu[a-z]{1,3}c hoi|chu tich nuoc|thu tuong chinh phu|chinh phu|"
    r"ngan hang nha nuoc[^\n]{0,40}|bo [^\n]{3,60})"
)


def infer_co_quan(text: str) -> str | None:
    """Cơ quan ban hành từ khối đầu văn bản (dòng viết hoa): bỏ cột "CỘNG HÒA XÃ HỘI…" dính cùng dòng và chữ ở thân bài."""
    for ln in _head(text, 14):
        s = " ".join(ln.replace("|", " ").split())  # hàng bảng: "| CHÍNH | PHỦ | CỘNG HÒA |"
        f = _fold1(s)
        cut = f.find("cong hoa")
        if cut > 0:
            s, f = s[:cut], f[:cut]
        m = _CO_QUAN_RE.match(f)
        if not m:
            continue
        out = " ".join(s[: m.end()].split()).rstrip(" .,;:-_")
        if m.group(1).startswith("qu"):
            out = "QUỐC HỘI"  # OCR hay đọc QUÓỐC/QUÔC: chuẩn hóa để bộ lọc cơ quan không bị chia đôi
        letters = [c for c in out if c.isalpha()]
        if letters and sum(c.isupper() for c in letters) >= 0.8 * len(letters):
            return out[:80]
    return None
