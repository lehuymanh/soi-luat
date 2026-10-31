"""Nạp file vào SQLite: pages, units, labels, gợi ý links."""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from soiluat.extract import extract_file, sha256_file
from soiluat.fold import fold_search, normalize_display, search_accent
from soiluat.labels import extract_fines, is_thi_hanh, labels_for_unit
from soiluat.parse import ParsedUnit, parse_pages, split_documents
from soiluat.sohieu import (
    find_ngay_ban_hanh,
    find_ngay_hieu_luc,
    infer_co_quan,
    infer_loai_text,
    so_hieu_search_key,
)

THAY_THE_RE = re.compile(
    r"thay thế\s+Nghị định số\s+([0-9/A-ZĐ\-]+)",
    re.IGNORECASE,
)
BAI_BO_RE = re.compile(r"bãi bỏ", re.IGNORECASE)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def relative_path(path: Path, root: Path) -> str:
    path = path.resolve()
    root = root.resolve()
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        # H5: ngoài thư mục data → đường dẫn tuyệt đối, tránh trùng tên ghi đè nhau
        return path.as_posix()


def start_job(conn: sqlite3.Connection, file_path: str, sha: str) -> int:
    cur = conn.execute(
        "INSERT INTO import_jobs(status, phase, file_path, sha256, started_at) "
        "VALUES ('running', 'extract', ?, ?, ?)",
        (file_path, sha, _now()),
    )
    conn.commit()
    return int(cur.lastrowid)


def finish_job(
    conn: sqlite3.Connection,
    job_id: int,
    ok: bool,
    error: str | None = None,
    status: str | None = None,
) -> None:
    st = status or ("done" if ok else "failed")
    conn.execute(
        "UPDATE import_jobs SET status = ?, error = ?, finished_at = ?, phase = ? WHERE id = ?",
        (st, error, _now(), st, job_id),
    )
    conn.commit()


def skip_duplicate_job(
    conn: sqlite3.Connection, file_path: str, sha: str, existing: str
) -> None:
    conn.execute(
        "INSERT INTO import_jobs(status, phase, file_path, sha256, "
        "existing_file_path, started_at, finished_at) "
        "VALUES ('skipped_duplicate', 'done', ?, ?, ?, ?, ?)",
        (file_path, sha, existing, _now(), _now()),
    )
    conn.commit()


def _unit_maps(units: list[ParsedUnit]) -> dict[str, ParsedUnit]:
    return {u.addr_part: u for u in units}


def _dieu_of(u: ParsedUnit, by_path: dict[str, ParsedUnit]) -> ParsedUnit | None:
    cur: ParsedUnit | None = u
    seen: set[str] = set()
    while cur is not None and cur.addr_part not in seen:
        seen.add(cur.addr_part)
        if cur.level == "dieu":
            return cur
        cur = by_path.get(cur.parent_addr or "") if cur.parent_addr else None
    return None


def persist_parsed(
    conn: sqlite3.Connection,
    doc_id: int,
    parsed,
    method: str,
    n_pages: int,
) -> dict[str, int]:
    by_path = _unit_maps(parsed.units)
    path_to_id: dict[str, int] = {}
    pending_fines: list[tuple[str, str]] = []
    for u in parsed.units:
        parent_id = path_to_id.get(u.parent_addr) if u.parent_addr else None
        parent = by_path.get(u.parent_addr) if u.parent_addr else None
        dieu = _dieu_of(u, by_path)
        ctx_raw = ""
        if parent is not None:
            ctx_raw = f"{parent.title} {parent.text}".strip()
        from_table = 1 if u.from_table else 0
        note = u.level == "ghi_chu"
        fines = (None, None) if note else extract_fines(u.text, bool(from_table))
        if u.level == "diem" and parent is not None and fines[0] is None:
            pf = extract_fines(parent.text, False)
            if pf[0] is not None:
                pending_fines.append((u.addr_part, parent.addr_part))
                fines = pf
        cur = conn.execute(
            """
            INSERT INTO units(
              doc_id, parent_id, path, level, title, title_search,
              raw_text, normalized_text, search_accent, search_text,
              context_search, context_accent,
              page_from, page_to, boundary_confidence, extraction_method,
              verification_status, from_table, fine_min, fine_max
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'chua', ?, ?, ?)
            """,
            (
                doc_id,
                parent_id,
                u.addr_part,
                u.level,
                u.title,
                fold_search(u.title),
                u.text,
                normalize_display(u.text),
                search_accent(u.text),
                fold_search(u.text),
                fold_search(ctx_raw),
                search_accent(ctx_raw),
                u.page_from or 1,
                u.page_to or u.page_from or n_pages,
                u.confidence,
                method,
                from_table,
                fines[0],
                fines[1],
            ),
        )
        uid = int(cur.lastrowid)
        path_to_id[u.addr_part] = uid
        if note:
            continue  # ghi chú không gắn nhãn (H4)
        for lab in labels_for_unit(
            u, from_table=bool(from_table), parent=parent, dieu=dieu
        ):
            conn.execute(
                "INSERT OR IGNORE INTO unit_labels(unit_id, label) VALUES (?, ?)",
                (uid, lab),
            )
    for child_path, parent_path in pending_fines:
        cid = path_to_id.get(child_path)
        pid = path_to_id.get(parent_path)
        if cid and pid:
            conn.execute(
                "UPDATE units SET fine_source_unit = ? WHERE id = ?",
                (pid, cid),
            )
    return path_to_id


def suggest_effect_hints(conn: sqlite3.Connection, doc_id: int) -> None:
    rows = conn.execute(
        "SELECT id, title, raw_text FROM units WHERE doc_id = ?",
        (doc_id,),
    ).fetchall()
    # gợi ý đã duyệt còn sau khi dựng lại: không thêm bản chưa duyệt trùng (bai_bo không có đích nên không lọc)
    kept = {r[0] for r in conn.execute(
        "SELECT target_so_hieu FROM effect_hints WHERE source_doc_id = ? AND kind = 'thay_the' AND confirmed = 1",
        (doc_id,),
    )}
    for row in rows:
        blob = f"{row['title'] or ''} {row['raw_text'] or ''}"
        if not is_thi_hanh(row["title"] or "", row["raw_text"] or "") and not BAI_BO_RE.search(
            blob
        ):
            if not THAY_THE_RE.search(blob):
                continue
        m = THAY_THE_RE.search(blob)
        if m and m.group(1) in kept:
            continue
        if m:
            conn.execute(
                "INSERT INTO effect_hints(source_doc_id, source_unit_id, target_so_hieu, "
                "kind, snippet, confirmed) VALUES (?, ?, ?, 'thay_the', ?, 0)",
                (doc_id, row["id"], m.group(1), blob[:400]),
            )
        elif BAI_BO_RE.search(blob) and is_thi_hanh(row["title"] or "", row["raw_text"] or ""):
            conn.execute(
                "INSERT INTO effect_hints(source_doc_id, source_unit_id, target_so_hieu, "
                "kind, snippet, confirmed) VALUES (?, ?, ?, 'bai_bo', ?, 0)",
                (doc_id, row["id"], None, blob[:400]),
            )


def _insert_pages(conn: sqlite3.Connection, doc_id: int, pages, job_id: int | None) -> None:
    for p in pages:
        raw = p.text or ""
        conn.execute(
            """
            INSERT INTO pages(
              doc_id, page_no, kind, extraction_method, ocr_status, ocr_conf,
              raw_text, normalized_text, search_accent, search_text,
              verification_status, bbox_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'chua', ?)
            """,
            (
                doc_id,
                p.page_no,
                p.kind,
                p.extraction_method,
                p.ocr_status,
                getattr(p, "ocr_conf", None),
                raw,
                normalize_display(raw),
                search_accent(raw),
                fold_search(raw),
                p.bbox_json,
            ),
        )
        if job_id is not None:
            conn.execute(
                "UPDATE import_jobs SET pages_done = ? WHERE id = ?",
                (p.page_no, job_id),
            )


def _after_units(
    conn: sqlite3.Connection, doc_id: int, so_hieu: str | None, *, commit_before_fts: bool = False
) -> None:
    from soiluat.links import suggest_citation_links, suggest_fts_links

    suggest_citation_links(conn, doc_id, so_hieu)
    if commit_before_fts:  # chỉ dựng lại (rebuild_document): nhả khoá ghi trước các truy vấn FTS; nạp file giữ giao dịch cả nhóm
        conn.commit()
    suggest_fts_links(conn, doc_id)
    suggest_effect_hints(conn, doc_id)


def _extract(path: Path, run_ocr: bool):
    pages = extract_file(path)
    if run_ocr:
        # A: maybe_ocr_pages nhận cả PDF lẫn ảnh; thiếu Tesseract → OcrUnavailable
        from soiluat.ocr import maybe_ocr_pages

        pages = maybe_ocr_pages(path, pages)
    return pages


def _method(pages) -> str:
    method = pages[0].extraction_method if pages else "fallback"
    if any(p.extraction_method == "ocr" for p in pages):
        method = "mixed" if method != "ocr" else "ocr"
    return method


def group_ids(conn: sqlite3.Connection, rel: str) -> list[int]:
    """Các văn bản tách từ cùng một file: rel, rel#vb2, rel#vb3… (H4), theo thứ tự."""
    pre = rel + "#vb"
    rows = conn.execute(
        "SELECT id, file_path FROM documents WHERE file_path = ? "
        "OR substr(file_path, 1, ?) = ?",
        (rel, len(pre), pre),
    ).fetchall()

    def k(r) -> int:
        tail = r["file_path"][len(pre):]
        return int(tail) if r["file_path"] != rel and tail.isdigit() else 1

    return [int(r["id"]) for r in sorted(rows, key=k)]


def _store_doc(
    conn: sqlite3.Connection,
    doc_id: int | None,
    file_path: str,
    sha: str,
    pages,
    force_doan: bool,
    job_id: int | None,
):
    """Ghi một văn bản (mới hoặc thay nội dung doc_id cũ). Trả (doc_id, so_hieu)."""
    full_text = "\n\n".join(p.text or "" for p in pages)
    parsed = parse_pages(pages, force_doan=force_doan)
    so_hieu = parsed.so_hieu
    method = _method(pages)
    restart = any(u.level == "dieu" and "~" in u.addr_part for u in parsed.units)
    vals = (
        file_path,
        sha,
        so_hieu,
        so_hieu_search_key(so_hieu),
        infer_loai_text(full_text, so_hieu),
        infer_co_quan(full_text),
        find_ngay_ban_hanh(full_text),
        find_ngay_hieu_luc(full_text),
        method,
        parsed.s,
        1 if restart else 0,
        1 if parsed.tier == 3 else 0,
    )
    if doc_id is None:
        cur = conn.execute(
            """
            INSERT INTO documents(
              file_path, sha256, so_hieu, so_hieu_search, loai, co_quan,
              ngay_ban_hanh, ngay_hieu_luc, extraction_method, struct_score,
              multi_document_suspected, fallback_doan, hieu_luc, source_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'chua_ro', 'SOURCE_HASHED')
            """,
            vals,
        )
        doc_id = int(cur.lastrowid)
    else:
        conn.execute("DELETE FROM pages WHERE doc_id = ?", (doc_id,))
        conn.execute("DELETE FROM units WHERE doc_id = ?", (doc_id,))
        conn.execute("DELETE FROM effect_hints WHERE source_doc_id = ?", (doc_id,))
        # không đụng hieu_luc; ngày đã có giữ lại nếu lần này không trích được
        conn.execute(
            """
            UPDATE documents SET
              file_path = ?, sha256 = ?, so_hieu = ?, so_hieu_search = ?, loai = ?,
              co_quan = ?, ngay_ban_hanh = COALESCE(?, ngay_ban_hanh),
              ngay_hieu_luc = COALESCE(?, ngay_hieu_luc), extraction_method = ?,
              struct_score = ?, multi_document_suspected = ?, fallback_doan = ?
            WHERE id = ?
            """,
            (*vals, doc_id),
        )
    _insert_pages(conn, doc_id, pages, job_id)
    persist_parsed(conn, doc_id, parsed, method, max([p.page_no for p in pages] or [1]))
    return doc_id, so_hieu


def ingest_group(
    conn: sqlite3.Connection,
    path: Path,
    rel: str,
    sha: str,
    old_ids: list[int],
    *,
    run_ocr: bool = False,
    force_doan: bool = False,
    job_id: int | None = None,
) -> tuple[int, str | None]:
    """Nạp file (có thể chứa nhiều văn bản) vào chỗ các doc cũ cùng file. Trả (doc đầu, cảnh báo)."""
    from soiluat.rebuild import restore_links, snapshot_links

    pages = _extract(path, run_ocr)
    if job_id is not None:
        conn.execute(
            "UPDATE import_jobs SET pages_total = ? WHERE id = ?", (len(pages), job_id)
        )
    segs = [pages] if force_doan else split_documents(pages)
    snap = [x for i in old_ids for x in snapshot_links(conn, i)]
    done: list[tuple[int, str | None]] = []
    for k, seg in enumerate(segs, start=1):
        tail = "" if k == 1 else f"#vb{k}"
        old = old_ids[k - 1] if k <= len(old_ids) else None
        done.append(_store_doc(conn, old, rel + tail, sha + tail, seg, force_doan, job_id))
    for extra in old_ids[len(segs):]:
        conn.execute("DELETE FROM documents WHERE id = ?", (extra,))
    restore_links(conn, snap)
    for doc_id, so_hieu in done:
        _after_units(conn, doc_id, so_hieu)
    conn.commit()
    warn = None
    n_ocr = sum(1 for p in pages if p.ocr_status == "cho_ocr")
    if n_ocr and not run_ocr:
        warn = f"{n_ocr} trang cần OCR, nạp lại với --ocr"
    return done[0][0], warn


def _flags_change_result(
    conn: sqlite3.Connection, ids: list[int], run_ocr: bool, force_doan: bool
) -> bool:
    """File không đổi nhưng cờ lần này cho kết quả khác lần nạp trước (vd. nạp lại với --ocr)."""
    if not ids:
        return False
    q = ",".join("?" * len(ids))
    if run_ocr and conn.execute(
        f"SELECT 1 FROM pages WHERE doc_id IN ({q}) AND ocr_status IN ('cho_ocr', 'loi_ocr') LIMIT 1",
        ids,
    ).fetchone():
        return True
    return bool(
        force_doan
        and conn.execute(
            f"SELECT 1 FROM documents WHERE id IN ({q}) AND fallback_doan = 0 LIMIT 1", ids
        ).fetchone()
    )


def ingest_path(
    conn: sqlite3.Connection,
    path: Path,
    data_root: Path,
    *,
    run_ocr: bool = False,
    force_doan: bool = False,
) -> int:
    path = path.resolve()
    sha = sha256_file(path)
    rel = relative_path(path, data_root)

    same_hash = conn.execute(
        "SELECT id, file_path FROM documents WHERE sha256 = ?", (sha,)
    ).fetchone()
    if same_hash and same_hash["file_path"] != rel:
        skip_duplicate_job(conn, rel, sha, same_hash["file_path"])
        return int(same_hash["id"])
    if same_hash and not _flags_change_result(
        conn, group_ids(conn, rel), run_ocr, force_doan
    ):
        return int(same_hash["id"])  # cùng file, nội dung không đổi

    job_id = start_job(conn, rel, sha)
    try:
        doc_id, warn = ingest_group(
            conn, path, rel, sha, group_ids(conn, rel),
            run_ocr=run_ocr, force_doan=force_doan, job_id=job_id,
        )
        finish_job(conn, job_id, True, warn)
        return doc_id
    except Exception as e:
        conn.rollback()
        finish_job(conn, job_id, False, str(e) or type(e).__name__)
        raise
