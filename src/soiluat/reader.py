"""Trình đọc văn bản (kế hoạch P1, R1): thân văn bản theo thứ tự, đơn vị được chọn, tô từ khớp, chuỗi trích dẫn."""

from __future__ import annotations

import re
import sqlite3

from markupsafe import Markup, escape

from soiluat.answer import STOP
from soiluat.fold import _PATH_RE, fold_search, pretty_path, search_accent
from soiluat.query import _eq, _w, classify_query
from soiluat.sohieu import citation_remainder

LOAI = {
    "luat": "Luật", "phap_lenh": "Pháp lệnh", "nghi_quyet": "Nghị quyết", "nghi_dinh": "Nghị định",
    "thong_tu": "Thông tư", "quyet_dinh": "Quyết định", "chi_thi": "Chỉ thị", "cong_van": "Công văn",
}
# Tô từ: bỏ cụm "bao nhiêu" trước, rồi bỏ từ dừng trừ "bao"/"nhieu", để "bảo hiểm" được gạch đủ hai chữ.
_HL_STOP = STOP - {"bao", "nhieu"}
_BAO_NHIEU = re.compile(r"\bbao\s+nhi[eêế]u\b", re.I)


def _lan(n: str | None) -> str:
    return f" (lần {n})" if n else ""


def addr(path: str) -> str:
    """'D5.K1.Đa' → 'Điểm a khoản 1 Điều 5' (thứ tự trích dẫn); đường dẫn khác dùng pretty_path."""
    m = _PATH_RE.match((path or "").strip())
    if not m:
        s = pretty_path(path)
        return s[:1].upper() + s[1:]
    d, dn, k, kn, diem, diemn = m.groups()
    parts = []
    if diem:
        parts.append(f"điểm {diem}{_lan(diemn)}")
    if k:
        parts.append(f"khoản {k}{_lan(kn)}")
    parts.append(f"Điều {d}{_lan(dn)}")
    s = " ".join(parts)
    return s[:1].upper() + s[1:]


def cite(so_hieu: str | None, loai: str | None, path: str) -> str:
    """'Điểm a khoản 1 Điều 5 Nghị định 15/2020/NĐ-CP'; phần nào thiếu thì bỏ."""
    return " ".join(x for x in (addr(path), LOAI.get(loai or "", ""), (so_hieu or "").strip()) if x)


def resolve_sel(conn: sqlite3.Connection, doc_id: int, u: int | None, path: str) -> int | None:
    """Tìm theo path trước (id đơn vị đổi khi nạp lại và bị tái dùng sau xoá); id chỉ nhận khi thuộc văn bản này."""
    if path:
        r = conn.execute("SELECT id FROM units WHERE doc_id = ? AND path = ?", (doc_id, path)).fetchone()
        if r:
            return r[0]
    if u:
        r = conn.execute("SELECT id FROM units WHERE id = ? AND doc_id = ?", (u, doc_id)).fetchone()
        if r:
            return r[0]
    return None


def query_words(q: str) -> list:
    if q and classify_query(q) == "so_hieu":
        q = citation_remainder(q)  # "Điều 5", số hiệu không phải từ khoá; câu còn chữ khác (mức phạt … theo Điều 5) vẫn tô
    if not q:
        return []
    q = _BAO_NHIEU.sub(" ", q)
    return [w for w in (_w(t) for t in re.findall(r"\w+", q)) if w[3] not in _HL_STOP]


def highlight(text: str, words: list) -> Markup:
    """Thoát mọi chữ (chữ OCR không đáng tin) rồi gạch dưới từ khớp câu hỏi."""
    if not words:
        return escape(text)
    out, pos = [], 0
    for m in re.finditer(r"\w+", text):
        tok = m.group(0)
        norm = (search_accent(tok), fold_search(tok))  # một lần cho mỗi chữ, không lặp theo số từ câu hỏi
        if any(_eq(w, norm) for w in words):
            out += [escape(text[pos:m.start()]), Markup('<mark class="m">'), escape(tok), Markup("</mark>")]
            pos = m.end()
    out.append(escape(text[pos:]))
    return Markup("").join(out)


def _label(path: str, level: str) -> str:
    seg = re.sub(r"~\d+$", "", path.rsplit(".", 1)[-1])
    if level == "khoan" and seg.startswith("K"):
        return seg[1:] + "."
    if level == "diem" and seg.startswith("Đ"):
        return seg[1:] + ")"
    return ""


def build_view(conn: sqlite3.Connection, doc_id: int, sel_id: int | None, q: str) -> dict:
    """Mọi dòng của văn bản theo thứ tự id, kèm lớp sel/sel-in, ghi chú dưới đơn vị cha và mục lục."""
    doc = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    rows = conn.execute(
        "SELECT id, parent_id, path, level, title, raw_text, reviewed_text, page_from, from_table "
        "FROM units WHERE doc_id = ? ORDER BY id", (doc_id,)
    ).fetchall()
    by_id = {r["id"]: r for r in rows}
    sel, inside = set(), set()
    if sel_id in by_id:
        sel.add(sel_id)
        s = by_id[sel_id]
        if s["level"] == "diem" and s["parent_id"] in by_id:
            sel.add(s["parent_id"])  # câu dẫn của khoản đi cùng điểm được chọn
        kids: dict[int, list[int]] = {}
        for r in rows:
            if r["parent_id"] is not None:
                kids.setdefault(r["parent_id"], []).append(r["id"])
        stack = list(kids.get(sel_id, []))
        while stack:
            i = stack.pop()
            inside.add(i)
            stack += kids.get(i, [])
    words = query_words(q)
    notes: dict[int, list[dict]] = {}
    lines, orphan, toc = [], [], []

    def item(r) -> dict:
        text = r["reviewed_text"] or r["raw_text"] or ""
        title = (r["title"] or "").strip()
        if r["level"] == "dieu" and title and text.startswith(title):
            text = text[len(title):].strip()  # thân Điều không lặp tên
        cls = ["u"] + (["l2"] if r["level"] == "diem" else []) + (["sel"] if r["id"] in sel else []) \
            + (["sel-in"] if r["id"] in inside else []) + (["table"] if r["from_table"] else [])
        hot = r["id"] in sel or r["id"] in inside
        return {"id": r["id"], "path": r["path"], "level": r["level"], "label": _label(r["path"], r["level"]),
                "title": title, "html": highlight(text, words if hot else []), "cls": " ".join(cls),
                "page": r["page_from"], "notes": []}

    for r in rows:
        if r["level"] == "ghi_chu":
            (notes.setdefault(r["parent_id"], []) if r["parent_id"] in by_id else orphan).append(item(r))
            continue
        lines.append(item(r))
        if r["level"] == "dieu":
            toc.append({"id": r["id"], "label": addr(r["path"]), "path": r["path"], "title": lines[-1]["title"]})
    for ln in lines:
        ln["notes"] = notes.get(ln["id"], [])
    if doc is not None and doc["fallback_doan"]:
        seen = set()
        toc = []
        for ln in lines:
            if ln["page"] and ln["page"] not in seen:
                seen.add(ln["page"])
                toc.append({"id": ln["id"], "label": f"Trang {ln['page']}", "path": ln["path"]})
    return {"doc": doc, "lines": lines, "toc": toc, "orphan_notes": orphan,
            "orphan_open": any(n["id"] in sel for n in orphan), "sel": sel_id if sel_id in by_id else None}
