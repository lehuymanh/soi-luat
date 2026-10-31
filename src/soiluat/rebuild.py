"""Rebuild unit/FTS sau sửa nguồn hoặc nạp lại cùng path — 4.3.4."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from types import SimpleNamespace

from soiluat.fold import fold_search, search_accent
from soiluat.parse import ParsedUnit, parse_pages


def page_text(row: sqlite3.Row) -> str:
    return row["reviewed_text"] or row["raw_text"] or ""


def snapshot_links(conn: sqlite3.Connection, doc_id: int) -> list[tuple]:
    rows = conn.execute(
        """
        SELECT su.doc_id AS sdoc, su.path AS spath,
               du.doc_id AS ddoc, du.path AS dpath,
               l.method, l.confirmed
        FROM links l
        JOIN units su ON su.id = l.sanction_unit
        JOIN units du ON du.id = l.duty_unit
        WHERE su.doc_id = ? OR du.doc_id = ?
        """,
        (doc_id, doc_id),
    ).fetchall()
    return [
        (r["sdoc"], r["spath"], r["ddoc"], r["dpath"], r["method"], r["confirmed"])
        for r in rows
    ]


def restore_links(conn: sqlite3.Connection, snap: list[tuple]) -> None:
    for sdoc, spath, ddoc, dpath, method_l, confirmed in snap:
        sid = conn.execute(
            "SELECT id FROM units WHERE doc_id = ? AND path = ?",
            (sdoc, spath),
        ).fetchone()
        did = conn.execute(
            "SELECT id FROM units WHERE doc_id = ? AND path = ?",
            (ddoc, dpath),
        ).fetchone()
        if not sid or not did:
            continue
        try:
            conn.execute(
                "INSERT OR IGNORE INTO links(sanction_unit, duty_unit, method, confirmed) "
                "VALUES (?, ?, ?, ?)",
                (sid["id"], did["id"], method_l, confirmed),
            )
        except sqlite3.IntegrityError:
            pass


def _old_notes(conn: sqlite3.Connection, doc_id: int) -> list[ParsedUnit]:
    """Ghi chú không nằm trong pages → giữ lại qua rebuild, gắn lại theo path cha."""
    rows = conn.execute(
        "SELECT u.path, u.title, u.raw_text, u.page_from, u.page_to, pu.path AS ppath "
        "FROM units u LEFT JOIN units pu ON pu.id = u.parent_id "
        "WHERE u.doc_id = ? AND u.level = 'ghi_chu' ORDER BY u.id",
        (doc_id,),
    ).fetchall()
    return [
        ParsedUnit(
            level="ghi_chu", addr_part=r["path"], title=r["title"] or "",
            text=r["raw_text"] or "", parent_addr=r["ppath"], confidence=1.0,
            page_from=r["page_from"], page_to=r["page_to"],
        )
        for r in rows
    ]


def rebuild_document(conn: sqlite3.Connection, doc_id: int) -> None:
    from soiluat.ingest import persist_parsed, _after_units

    snap = snapshot_links(conn, doc_id)
    doc = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    if doc is None:
        return
    pages = conn.execute(
        "SELECT * FROM pages WHERE doc_id = ? ORDER BY page_no",
        (doc_id,),
    ).fetchall()
    views = [SimpleNamespace(page_no=p["page_no"], text=page_text(p)) for p in pages]
    parsed = parse_pages(views, so_hieu=doc["so_hieu"])
    paths = {u.addr_part for u in parsed.units}
    for n in _old_notes(conn, doc_id):
        if n.parent_addr not in paths:
            n.parent_addr = None
        parsed.units.append(n)
    n_pages = max([p["page_no"] for p in pages] or [1])
    try:
        conn.execute("DELETE FROM units WHERE doc_id = ?", (doc_id,))
        # gợi ý đã duyệt giữ lại (source_unit_id thành NULL vì đơn vị được tạo lại; /review/hints không đọc cột này)
        conn.execute("DELETE FROM effect_hints WHERE source_doc_id = ? AND confirmed = 0", (doc_id,))
        method = doc["extraction_method"] or "fallback"
        persist_parsed(conn, doc_id, parsed, method, n_pages)
        restore_links(conn, snap)
        conn.execute(
            "UPDATE documents SET struct_score = ?, fallback_doan = ? WHERE id = ?",
            (parsed.s, 1 if parsed.tier == 3 else 0, doc_id),
        )
        _after_units(conn, doc_id, doc["so_hieu"])
        conn.commit()
    except BaseException:
        conn.rollback()  # lỗi giữa chừng không được để văn bản mất đơn vị khi lần commit sau chốt giao dịch dở
        raise


def rebuild_document_from_file(
    conn: sqlite3.Connection,
    doc_id: int,
    path: Path,
    rel: str,
    sha: str,
    *,
    run_ocr: bool = False,
    force_doan: bool = False,
) -> int:
    """Nạp lại file vào doc_id (và các văn bản cùng file #vb2…), giữ links đã duyệt."""
    from soiluat.ingest import group_ids, ingest_group

    old = conn.execute("SELECT file_path FROM documents WHERE id = ?", (doc_id,)).fetchone()
    ids = group_ids(conn, old["file_path"]) if old else []
    if doc_id not in ids:
        ids = [doc_id]
    first, _ = ingest_group(
        conn, path, rel, sha, ids, run_ocr=run_ocr, force_doan=force_doan
    )
    return first


def set_page_reviewed(conn: sqlite3.Connection, page_id: int, text: str) -> int:
    row = conn.execute("SELECT doc_id FROM pages WHERE id = ?", (page_id,)).fetchone()
    if row is None:
        return 0
    conn.execute(
        """
        UPDATE pages SET reviewed_text = ?, search_accent = ?, search_text = ?,
          ocr_status = 'da_doi_chieu', verification_status = 'da_doi_chieu'
        WHERE id = ?
        """,
        (text, search_accent(text), fold_search(text), page_id),
    )
    rebuild_document(conn, int(row["doc_id"]))
    return int(row["doc_id"])
