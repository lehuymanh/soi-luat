"""P1 H1: bảng lịch sử trò chuyện (conversations, messages), nâng cấp kho 0.8 an toàn."""

import sqlite3
from pathlib import Path

from soiluat.db import connect, init_schema


def _kho_08(path):
    conn = sqlite3.connect(path)
    conn.executescript((Path(__file__).parent / "fixtures" / "schema_08.sql").read_text(encoding="utf-8"))
    conn.execute("INSERT INTO documents(id, file_path, sha256, source_status, extraction_method) VALUES (1, 'a.txt', 'x', 'ok', 'txt')")
    conn.execute("INSERT INTO units(id, doc_id, path, level, raw_text, normalized_text, search_text, extraction_method,"
                 " verification_status) VALUES (1, 1, 'D1', 'dieu', 'Điều 1', 'dieu 1', 'dieu 1', 'txt', 'auto')")
    conn.execute("INSERT INTO query_log(query_raw, result_count, created_at) VALUES ('phạt', 3, '2026-01-01')")
    conn.commit()
    conn.close()


def _dump(conn):
    return [tuple(r) for t in ("documents", "units", "query_log") for r in conn.execute(f"SELECT * FROM {t} ORDER BY 1")]


def test_nang_cap_tu_0_8(tmp_path):
    _kho_08(tmp_path / "kho.db")
    conn = connect(tmp_path / "kho.db")
    before = _dump(conn)
    init_schema(conn)
    init_schema(conn)  # chạy lại mỗi request vẫn an toàn
    assert _dump(conn) == before
    cid = conn.execute("INSERT INTO conversations(title, created_at, updated_at) VALUES ('Mức phạt', 'a', 'a')").lastrowid
    m1 = conn.execute("INSERT INTO messages(conversation_id, role, text, created_at) VALUES (?, 'user', 'hỏi', 'a')", (cid,)).lastrowid
    conn.execute("DELETE FROM messages WHERE id = ?", (m1,))
    m2 = conn.execute("INSERT INTO messages(conversation_id, role, text, created_at) VALUES (?, 'bot', 'đáp', 'a')", (cid,)).lastrowid
    assert m2 > m1  # id tin đã xoá không tái dùng: tab cũ không nhận nhầm tin mới
    conn.execute("DELETE FROM conversations WHERE id = ?", (cid,))
    assert conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 0  # xoá cuộc xoá luôn tin
    plan = " ".join(r[3] for r in conn.execute("EXPLAIN QUERY PLAN SELECT * FROM messages WHERE conversation_id = 1 ORDER BY id"))
    assert "INDEX" in plan and "SCAN" not in plan, plan
