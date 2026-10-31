from __future__ import annotations

import re
import sqlite3

CITE_RE = re.compile(
    r"quy định tại\s+khoản\s+(\d+)\s+Điều\s+(\d+[a-z]?)",
    re.IGNORECASE,
)
CITE_DIEU_RE = re.compile(
    r"quy định tại\s+Điều\s+(\d+[a-z]?)",
    re.IGNORECASE,
)
# phần đứng sau "Điều n": "Nghị định số 15/2020/NĐ-CP", "Thông tư này", "Luật Doanh nghiệp"
CITE_DOC_RE = re.compile(
    r"\s*(?:của\s+)?(Bộ luật|Luật|Nghị định|Thông tư(?: liên tịch)?|Quyết định|Nghị quyết|Pháp lệnh)"
    r"(?:\s+(này)|\s+(?:số\s+)?(\d+/\d{4}/[A-ZĐ0-9-]+))?",
    re.IGNORECASE,
)


CITE_THIS_DIEM = re.compile(
    r"điểm\s+([a-zđ])\s+khoản\s+(\d+)\s+Điều\s+này",
    re.IGNORECASE,
)
CITE_THIS_KHOAN = re.compile(
    r"khoản\s+(\d+)\s+Điều\s+này",
    re.IGNORECASE,
)


def _dieu_num(path: str) -> str | None:
    # "D5~2.K1" → "5~2" (Điều trùng số, H4)
    m = re.match(r"D(\d+[a-z]?(?:~\d+)?)", path or "", re.I)
    return m.group(1) if m else None


def _insert_link(
    conn: sqlite3.Connection,
    sanction_id: int,
    duty_id: int,
    method: str,
) -> bool:
    try:
        conn.execute(
            "INSERT INTO links(sanction_unit, duty_unit, method, confirmed) "
            "VALUES (?, ?, ?, 0)",
            (sanction_id, duty_id, method),
        )
        return True
    except sqlite3.IntegrityError:
        return False


def _target_doc(conn: sqlite3.Connection, doc_id: int, text: str, end: int) -> int | None:
    """Văn bản được dẫn chiếu sau "Điều n": None nếu là văn bản khác không có trong kho."""
    m = CITE_DOC_RE.match(text, end)
    if not m or m.group(2):
        return doc_id  # không nêu văn bản, hoặc "… này"
    if not m.group(3):
        return None  # "Luật Doanh nghiệp" không số hiệu → không đoán
    from soiluat.sohieu import so_hieu_search_key

    row = conn.execute(
        "SELECT id FROM documents WHERE so_hieu_search = ? ORDER BY id LIMIT 1",
        (so_hieu_search_key(m.group(3).rstrip(".,;:-")),),
    ).fetchone()
    return int(row["id"]) if row else None


def suggest_citation_links(
    conn: sqlite3.Connection,
    doc_id: int,
    so_hieu: str | None,
) -> int:
    rows = conn.execute(
        "SELECT u.id, u.path, u.raw_text FROM units u "
        "JOIN unit_labels l ON l.unit_id = u.id "
        "WHERE u.doc_id = ? AND l.label = 'CHE_TAI'",
        (doc_id,),
    ).fetchall()
    n = 0
    for row in rows:
        text = row["raw_text"] or ""
        duty_path = None
        target = doc_id
        method = "dan_chieu"
        m_this = CITE_THIS_DIEM.search(text)
        dieu_n = _dieu_num(row["path"])
        if m_this and dieu_n:
            duty_path = f"D{dieu_n}.K{m_this.group(2)}.Đ{m_this.group(1).lower()}"
            method = "noi_bo"
        elif dieu_n:
            m_k = CITE_THIS_KHOAN.search(text)
            if m_k:
                duty_path = f"D{dieu_n}.K{m_k.group(1)}"
                method = "noi_bo"
        if duty_path is None:
            m = CITE_RE.search(text)
            if m:
                duty_path = f"D{m.group(2)}.K{m.group(1)}"
            else:
                m = CITE_DIEU_RE.search(text)
                if m:
                    duty_path = f"D{m.group(1)}"
            if m:
                target = _target_doc(conn, doc_id, text, m.end())
        if not duty_path or target is None:
            continue
        duty = conn.execute(
            "SELECT id FROM units WHERE doc_id = ? AND path = ?",
            (target, duty_path),
        ).fetchone()
        if duty is None and ".K" in duty_path:
            dieu = duty_path.split(".K")[0]
            duty = conn.execute(
                "SELECT id FROM units WHERE doc_id = ? AND path = ?",
                (target, dieu),
            ).fetchone()
        if duty is None:
            continue
        if _insert_link(conn, row["id"], duty["id"], method):
            n += 1
    return n


def suggest_fts_links(conn: sqlite3.Connection, doc_id: int, limit: int = 3) -> int:
    from soiluat.labels import extract_hanh_vi
    from soiluat.search import match_units

    rows = conn.execute(
        "SELECT u.id, u.raw_text FROM units u "
        "JOIN unit_labels l ON l.unit_id = u.id "
        "WHERE u.doc_id = ? AND l.label = 'CHE_TAI'",
        (doc_id,),
    ).fetchall()
    todo: list[tuple[int, int]] = []
    for row in rows:
        existing = conn.execute(
            "SELECT 1 FROM links WHERE sanction_unit = ?",
            (row["id"],),
        ).fetchone()
        if existing:
            continue
        hv = extract_hanh_vi(row["raw_text"] or "")
        if not hv:
            continue
        hits = match_units(
            conn,
            hv,
            doc_id=None,
            labels=("NGHIA_VU", "CAM", "THOI_HAN", "DIEU_KIEN"),
            limit=limit,
            branch="fold",
        )
        todo.extend((row["id"], hid) for hid in hits if hid != row["id"])
    n = 0
    for sid, hid in todo:  # ghi sau khi đọc xong: các truy vấn FTS ở trên không nằm trong giao dịch ghi (rebuild_document)
        try:
            conn.execute(
                "INSERT INTO links(sanction_unit, duty_unit, method, confirmed) "
                "VALUES (?, ?, 'goi_y', 0)",
                (sid, hid),
            )
            n += 1
        except sqlite3.IntegrityError:
            pass
    return n
