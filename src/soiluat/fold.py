"""Chuẩn hoá: NFC hiển thị; search_accent giữ dấu; fold bỏ dấu đ→d."""

from __future__ import annotations

import re
import unicodedata

_WS = re.compile(r"\s+")

_D_VARIANTS = {
    "\u0110": "d",
    "\u0111": "d",
    "\u00d0": "d",
    "\u00f0": "d",
}

# i/y cùng âm (kỳ/kì, tỷ/tỉ). Không đổi diphthong ay/ây/oy (hay ≠ hai).
_Y2I = str.maketrans("yỳỷỹýỵ", "iìỉĩíị")
_I2Y = str.maketrans("iìỉĩíị", "yỳỷỹýỵ")
_AEO = set("aăâeêoôơàáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệòóỏõọồốổỗộờớởỡợ")
_Y_FINAL = set("yỳỷỹýỵ")
_I_FINAL = set("iìỉĩíị")


def iy_norm_token(tok: str) -> str:
    """Chuẩn i/y cuối tiếng: kỳ → kì. Giữ hay/tây."""
    if len(tok) < 2:
        return tok
    last = tok[-1]
    if last not in _Y_FINAL:
        return tok
    if tok[-2] in _AEO:
        return tok
    return tok[:-1] + last.translate(_Y2I)


def iy_norm_text(text: str) -> str:
    return " ".join(iy_norm_token(w) for w in (text or "").split())


def iy_token_alts(tok: str) -> tuple[str, ...]:
    """Token gốc + biến thể i↔y (kì/kỳ). Một phần tử nếu không đổi."""
    if len(tok) < 2:
        return (tok,)
    last = tok[-1]
    if tok[-2] in _AEO:
        return (tok,)
    if last in _Y_FINAL:
        alt = tok[:-1] + last.translate(_Y2I)
    elif last in _I_FINAL:
        alt = tok[:-1] + last.translate(_I2Y)
    else:
        return (tok,)
    if alt == tok:
        return (tok,)
    return (tok, alt)


def normalize_display(text: str | None) -> str:
    if not text:
        return ""
    return unicodedata.normalize("NFC", text)


def search_accent(text: str | None) -> str:
    """NFC, chữ thường, Ð→Đ, giữ dấu nguyên âm, không đ→d."""
    if not text:
        return ""
    s = unicodedata.normalize("NFC", text)
    s = s.lower()
    s = s.replace("\u00d0", "\u0110").replace("\u00f0", "\u0111")
    s = _WS.sub(" ", s).strip()
    return s


def fold_search(text: str | None) -> str:
    if not text:
        return ""
    s = unicodedata.normalize("NFC", text)
    s = s.lower()
    s = "".join(_D_VARIANTS.get(ch, ch) for ch in s)
    nfd = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn")
    s = unicodedata.normalize("NFC", s)
    s = _WS.sub(" ", s).strip()
    return s


def query_has_accent(raw: str) -> bool:
    return search_accent(raw) != fold_search(raw)


# H4: Điều/khoản/điểm trùng số mang hậu tố ~n (lần thứ n), ví dụ D5~2.K1.
_PATH_RE = re.compile(
    r"^D(\d+[a-z]?)(?:~(\d+))?(?:\.K(\d+)(?:~(\d+))?)?(?:\.Đ([^~]+)(?:~(\d+))?)?$", re.I
)


def _lan(n: str | None) -> str:
    return f" (lần {n})" if n else ""


def pretty_path(path: str) -> str:
    p = (path or "").strip()
    m = _PATH_RE.match(p)
    if m:
        d, dn, k, kn, diem, diemn = m.groups()
        parts = [f"Điều {d}{_lan(dn)}"]
        if k:
            parts.append(f"khoản {k}{_lan(kn)}")
        if diem:
            parts.append(f"điểm {diem}{_lan(diemn)}")
        return " ".join(parts)
    m = re.match(r"^GC(\d+)$", p, re.I)
    if m:
        return f"ghi chú {m.group(1)}"
    m = re.match(r"^p(\d+)\.para(\d+)$", p, re.I)
    if m:
        return f"trang {m.group(1)} đoạn {m.group(2)}"
    m = re.match(r"^PL(\d+)\.para(\d+)$", p, re.I)
    if m:
        return f"phụ lục {m.group(1)} đoạn {m.group(2)}"
    return p


def display_addr(so_hieu: str | None, path: str) -> str:
    so = (so_hieu or "").strip()
    readable = pretty_path(path)
    if so and readable:
        return f"{so} · {readable}"
    return so or readable


def dieu_path(path: str, level: str = "") -> str:
    p = (path or "").strip()
    if level in ("doan", "cua_so", "ghi_chu"):
        return p
    m = re.match(r"(D\d+[a-z]?(?:~\d+)?)", p, re.I)
    return m.group(1) if m else p


_PAGE_NO_LINE = re.compile(r"(?m)^[ \t]*[-–]?[ \t]*\d{1,3}[ \t]*[-–]?[ \t]*(?:\n|$)")


def strip_page_numbers(text: str) -> str:
    """Bỏ dòng chỉ có số trang ("12", "- 13 -") lọt vào chữ đơn vị khi hiển thị; chỉ mục giữ nguyên chữ gốc."""
    return _PAGE_NO_LINE.sub("", text or "").rstrip("\n")
