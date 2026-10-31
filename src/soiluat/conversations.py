"""P1 H2: lưu câu hỏi vào cuộc trò chuyện. Tin trả lời chỉ giữ tham chiếu (doc_id, path, h) tới đơn vị, không giữ thẻ
dựng sẵn: mở lại dựng từ dữ liệu hiện tại (hiệu lực, ghi chú luôn mới). `h` bắt trường hợp id văn bản bị dùng lại hoặc
path đổi sau khi nạp lại; chỉ (doc_id, path) thì có thể hiện nhầm đoạn mà không báo. `h` băm cả số hiệu của văn bản: `raw_text`
của một Điều có Khoản con chỉ là tiêu đề ("Phạm vi điều chỉnh"), y hệt ở nhiều văn bản."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import unicodedata
from datetime import datetime

from soiluat.fold import fold_search

REFS_MAX = 150  # Advance trả tới ~150 id; số hiệu kèm ý định trả mọi đơn vị của văn bản (hàng nghìn): cắt để tin không phình
DOC_MAX = 5  # "Mở toàn văn" hiện tối đa 5 văn bản (_results.html)
TITLE_MAX = 60
HIST_MAX = 200  # cuộc hiện trên thanh bên: 5.000 cuộc là ~2,7 MB HTML mỗi lần tải trang và mỗi lần gõ vào ô tìm
RENAME_MAX = 80  # tên người dùng tự đặt dài hơn tên tự cắt từ câu hỏi (60); như ô nhập trong mẫu


def _h(so_hieu_search: str | None, raw_text: str | None = None) -> str:
    """Dấu nhận ra đúng đối tượng cũ: số hiệu (văn bản không số hiệu thì rỗng) và chữ đơn vị; ref mức văn bản chỉ có số hiệu."""
    return hashlib.sha1(f"{so_hieu_search or ''}|{raw_text or ''}".encode("utf-8")).hexdigest()[:10]


def refs_of(conn: sqlite3.Connection, ids: list[int], tiers: dict[int, int] | None = None,
            fold_ids: set[int] = frozenset(), f2_ids: set[int] = frozenset()) -> list[list]:
    """[doc_id, path, h, tier, fold, f2] cho mỗi id (đúng cái người dùng thấy: sau lọc và cắt), giữ thứ tự `ids`;
    id không còn thì bỏ. Thiếu tầng thì 6 như `assemble_cards`."""
    tiers = tiers or {}
    rows = {r[0]: r for r in conn.execute(
        "SELECT u.id, u.doc_id, u.path, d.so_hieu_search, u.raw_text FROM units u JOIN documents d ON d.id = u.doc_id "
        "WHERE u.id IN (SELECT value FROM json_each(?))", (json.dumps(ids),))}
    return [[rows[i][1], rows[i][2], _h(rows[i][3], rows[i][4]), tiers.get(i, 6), int(i in fold_ids), int(i in f2_ids)]
            for i in ids if i in rows]


def match(conn: sqlite3.Connection, refs: list[list]):
    """Gắn lại từng ref với đơn vị hiện có theo (doc_id, path), chỉ nhận khi số hiệu và chữ khớp `h`: sinh (ref, id) theo
    thứ tự cũ, id là None khi ref hỏng. Ref mức văn bản (path None, tin `kind = full`) kiểm văn bản còn và đúng số hiệu,
    rồi trả chính doc_id."""
    for ref in refs:
        doc_id, path, h = ref[:3]
        row = conn.execute("SELECT d.so_hieu_search, u.id, u.raw_text FROM documents d LEFT JOIN units u "
                           "ON u.doc_id = d.id AND u.path = ? WHERE d.id = ?", (path, doc_id)).fetchone()  # path NULL: không đơn vị nào khớp
        if row is None:
            yield ref, None
        elif path is None:
            yield ref, doc_id if _h(row[0]) == h else None
        else:
            yield ref, row[1] if row[1] is not None and _h(row[0], row[2]) == h else None


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
    refs = ([[x.doc_id, None, _h(x.so_hieu_search), 0, 0, 0] for x in items[:DOC_MAX]] if full
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


def nhom(ts: str, now, tz=None) -> str:
    """Nhóm trên thanh bên theo ngày địa phương, không theo UTC (`ts` lưu UTC: tin 00:30 giờ Việt Nam sẽ nằm nhầm nhóm
    tới 07:00). `now` là chuỗi ISO hay datetime có múi giờ; `tz` None = giờ máy."""
    now = datetime.fromisoformat(now) if isinstance(now, str) else now
    tuoi = (now.astimezone(tz).date() - datetime.fromisoformat(ts).astimezone(tz).date()).days
    return "Hôm nay" if tuoi <= 0 else "7 ngày qua" if tuoi <= 7 else "Cũ hơn"  # tuổi âm (đồng hồ lùi): vẫn trong nhóm


def history(conn: sqlite3.Connection, q: str, now, tz=None) -> tuple[list[tuple[str, list[sqlite3.Row]]], int]:
    """(các cuộc theo nhóm [(tên nhóm, [hàng id, title])], số cuộc chưa hiện): mới cập nhật trước, nhóm rỗng bỏ, tối đa HIST_MAX
    cuộc. `q` không rỗng thì chỉ giữ cuộc có đủ mọi từ (không dấu, không phân biệt hoa thường) trong tên hoặc trong câu hỏi
    của người dùng.
    shortcut: lọc bằng Python trên mọi cuộc; quá ~10 nghìn tin thì chuyển sang FTS."""
    words = fold_search(q).split()
    rows = conn.execute(
        "SELECT c.id, c.title, c.updated_at, (SELECT COALESCE(group_concat(m.text, ' '), '') FROM messages m "
        "WHERE m.conversation_id = c.id AND m.role = 'user') AS hoi FROM conversations c ORDER BY c.updated_at DESC, c.id DESC"
        if words else "SELECT id, title, updated_at FROM conversations ORDER BY updated_at DESC, id DESC").fetchall()
    hits = []
    for r in rows:
        hay = fold_search(f"{r['title']} {r['hoi']}") if words else ""
        if all(w in hay for w in words):
            hits.append(r)
    out: dict[str, list] = {}
    for r in hits[:HIST_MAX]:
        out.setdefault(nhom(r["updated_at"], now, tz), []).append(r)
    return list(out.items()), max(0, len(hits) - HIST_MAX)
