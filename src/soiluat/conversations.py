"""P1 H2: lưu câu hỏi vào cuộc trò chuyện. Tin trả lời chỉ giữ tham chiếu (doc_id, path, h) tới đơn vị, không giữ thẻ
dựng sẵn: mở lại dựng từ dữ liệu hiện tại (hiệu lực, ghi chú luôn mới). `h` bắt trường hợp id văn bản bị dùng lại hoặc
path đổi sau khi nạp lại; chỉ (doc_id, path) thì có thể hiện nhầm đoạn mà không báo."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import unicodedata

REFS_MAX = 150  # Advance trả tới ~150 id; số hiệu kèm ý định trả mọi đơn vị của văn bản (hàng nghìn): cắt để tin không phình
DOC_MAX = 5  # "Mở toàn văn" hiện tối đa 5 văn bản (_results.html)
TITLE_MAX = 60


def _h(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]


def refs_of(conn: sqlite3.Connection, ids: list[int], tiers: dict[int, int] | None = None,
            fold_ids: set[int] = frozenset(), f2_ids: set[int] = frozenset()) -> list[list]:
    """[doc_id, path, h, tier, fold, f2] cho mỗi id (đúng cái người dùng thấy: sau lọc và cắt), giữ thứ tự `ids`;
    id không còn thì bỏ. Thiếu tầng thì 6 như `assemble_cards`."""
    tiers = tiers or {}
    rows = {r[0]: r for r in conn.execute(
        "SELECT id, doc_id, path, raw_text FROM units WHERE id IN (SELECT value FROM json_each(?))", (json.dumps(ids),))}
    return [[rows[i][1], rows[i][2], _h(rows[i][3]), tiers.get(i, 6), int(i in fold_ids), int(i in f2_ids)]
            for i in ids if i in rows]


def match(conn: sqlite3.Connection, refs: list[list]):
    """Gắn lại từng ref với đơn vị hiện có theo (doc_id, path), chỉ nhận khi chữ khớp `h`: sinh (ref, id) theo thứ tự cũ,
    id là None khi ref hỏng. Ref mức văn bản (path None, tin `kind = full`) chỉ kiểm văn bản còn không và trả chính doc_id."""
    for ref in refs:
        doc_id, path, h = ref[:3]
        if path is None:
            row = conn.execute("SELECT id FROM documents WHERE id = ?", (doc_id,)).fetchone()
        else:
            row = conn.execute("SELECT id, raw_text FROM units WHERE doc_id = ? AND path = ?", (doc_id, path)).fetchone()
            row = row if row and _h(row[1]) == h else None
        yield ref, row[0] if row else None


def resolve(conn: sqlite3.Connection, refs: list[list]) -> tuple[list[int], int]:
    """(id theo thứ tự cũ, số ref hỏng); hỏng thì bỏ."""
    got = [i for _, i in match(conn, refs)]
    ids = [i for i in got if i is not None]
    return ids, len(got) - len(ids)


def result_of(conn: sqlite3.Connection, q: str, filters: dict, s: dict, ctx: dict) -> dict:
    """`result_json` của tin trả lời. Không lưu thẻ, ghi chú phụ thuộc kho (q2_note) hay `gap`; lưu số trước lọc và
    trước cắt để `_ctx` tính lại dòng "Còn N mục nữa". Truy vấn chỉ có số hiệu ("Mở toàn văn") chỉ lưu ref mức văn bản."""
    r, items = s["result"], ctx["items"]
    full = bool(items) and getattr(items[0], "full", False)
    refs = ([[x.doc_id, None, None, 0, 0, 0] for x in items[:DOC_MAX]] if full
            else refs_of(conn, s["ids"][:REFS_MAX], r.tiers, r.fold_ids, r.f2_ids))
    return {"kind": "full" if full else "list", "q": q, "filters": filters, "note": r.note, "intent": r.intent,
            "sure": s["sure"], "n_found": s["n_found"], "n_ids": s["n_ids"], "refs": refs}


def save(conn: sqlite3.Connection, cid: int | None, q: str, result: dict, now: str) -> int:
    """Ghi tin hỏi và tin trả lời trong một giao dịch ngắn, trả id cuộc. `cid` None hoặc không còn (xoá ở tab khác, hay
    lúc câu hỏi còn trong hàng đợi) thì tạo cuộc mới với câu này làm tiêu đề. Lỗi ghi ném `sqlite3.Error` cho nơi gọi
    và không để lại cuộc rỗng."""
    blob = json.dumps(result, ensure_ascii=False)
    try:
        conn.execute("BEGIN IMMEDIATE")  # khoá ghi trước khi kiểm cuộc còn không: không ai xoá cuộc giữa kiểm và ghi
        if cid is None or conn.execute("SELECT 1 FROM conversations WHERE id = ?", (cid,)).fetchone() is None:
            title = " ".join(unicodedata.normalize("NFC", q).split())  # Shift+Enter không đưa xuống dòng vào tên cuộc
            if len(title) > TITLE_MAX:
                title = title[:TITLE_MAX] + "…"
            cid = conn.execute("INSERT INTO conversations(title, created_at, updated_at) VALUES (?, ?, ?)",
                               (title, now, now)).lastrowid
        else:
            conn.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, cid))
        conn.executemany("INSERT INTO messages(conversation_id, role, text, result_json, created_at) VALUES (?, ?, ?, ?, ?)",
                         [(cid, "user", q, None, now), (cid, "bot", "", blob, now)])
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    return cid
