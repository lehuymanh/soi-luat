from __future__ import annotations

import csv
import hashlib
import io
import os
import sqlite3
from pathlib import Path

SCHEMA_FILE = Path(__file__).with_name("schema.sql")
SEED_FILE = Path(__file__).with_name("synonyms_seed.csv")


class FtsUnavailable(RuntimeError):
    """SQLite thiếu FTS5 hoặc fts5vocab."""


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def probe_fts(conn: sqlite3.Connection) -> None:
    try:
        conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS _probe_fts "
            "USING fts5(x, tokenize='unicode61 remove_diacritics 0')"
        )
        conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS _probe_vocab "
            "USING fts5vocab(_probe_fts, 'row')"
        )
    except sqlite3.OperationalError as e:
        raise FtsUnavailable(
            f"SQLite thiếu FTS5/fts5vocab (tokenize unicode61): {e}"
        ) from e
    finally:
        conn.execute("DROP TABLE IF EXISTS _probe_vocab")
        conn.execute("DROP TABLE IF EXISTS _probe_fts")


_FTS_OK = False  # SQLite không đổi trong một process: dò một lần (app gọi init_schema mỗi request)


def init_schema(conn: sqlite3.Connection) -> None:
    global _FTS_OK
    if not _FTS_OK:
        probe_fts(conn)
        _FTS_OK = True
    sql = SCHEMA_FILE.read_text(encoding="utf-8")
    conn.executescript(sql)
    try:
        conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS units_vocab "
            "USING fts5vocab(units_fts, 'row')"
        )
    except sqlite3.OperationalError:
        pass
    seed_synonyms(conn)
    conn.commit()


def seed_synonyms(conn: sqlite3.Connection) -> None:
    """Nạp synonyms_seed.csv một lần cho mỗi phiên bản file (INSERT OR IGNORE).

    Không ghi đè cột approved người dùng đã duyệt; cặp người dùng xoá không bị nạp lại
    cho tới khi file seed đổi nội dung.
    """
    if not SEED_FILE.exists():
        return
    data = SEED_FILE.read_bytes()
    ver = hashlib.sha1(data).hexdigest()
    row = conn.execute(
        "SELECT value FROM app_meta WHERE key = 'synonyms_seed'"
    ).fetchone()
    if row is not None and row[0] == ver:
        return
    rows = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    conn.executemany(
        "INSERT OR IGNORE INTO synonyms(term, alt, kind, approved) VALUES (?, ?, ?, ?)",
        [
            (r["term"].strip(), r["alt"].strip(), r["kind"].strip(), int(r["approved"] or 0))
            for r in rows
            if r.get("term") and r.get("alt")
        ],
    )
    conn.execute(
        "INSERT OR REPLACE INTO app_meta(key, value) VALUES ('synonyms_seed', ?)", (ver,)
    )


def backup_db(src: Path, dest: Path) -> None:
    """Sao lưu ra tệp .tmp rồi mới đổi tên: lỗi giữa chừng (đĩa đầy) không để tệp cụt mang tên đích, không đè bản cũ."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    # tên tạm theo tiến trình: hai bản app cùng kho không ghi chung hay xoá tệp tạm của nhau
    # shortcut: tệp tạm của tiến trình bị kill -9 không tự dọn, tối đa một tệp mỗi lần chết; dọn tay hoặc khi có báo cáo đĩa đầy
    tmp = dest.with_name(f"{dest.name}.{os.getpid()}.tmp")
    src_conn = sqlite3.connect(str(src))
    try:
        dest_conn = sqlite3.connect(str(tmp))
        try:
            src_conn.backup(dest_conn)
        finally:
            dest_conn.close()
        os.replace(tmp, dest)
    except BaseException:
        for p in (tmp, tmp.with_name(tmp.name + "-journal")):
            p.unlink(missing_ok=True)
        raise
    finally:
        src_conn.close()
