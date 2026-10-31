"""SoiLuat.exe — một app: tra cứu + nạp file + cài đặt. FastAPI, chỉ 127.0.0.1.

Phần nạp (trích chữ, OCR) chỉ nạp khi dùng lần đầu (soiluat.jobs), nên Normal không tốn RAM cho nó."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import re
import secrets
import shutil
import socket
import sqlite3
import sys
import threading
import uuid
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlencode

from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import (
    FileResponse, HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse, Response,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn

from soiluat import crossrank, pageimg, reader, semantic
from soiluat.cards import OCR_LABEL, _ocr_unverified, assemble_cards, compact, doc_groups, summarize
from soiluat.config import HOST, PORT, data_dir, db_path
from soiluat.db import backup_db, connect, init_schema
from soiluat.export_word import card_pages, export_cards, page_label
from soiluat.fold import display_addr
from soiluat.jobs import JOBS, SUFFIXES
from soiluat.search import DIEU_CAP, _so_hieu_docs, apply_doc_filters, cascade_search, filter_docs
from soiluat.sohieu import find_dieu_so


def _ngay(s):
    """'2020-02-01' thành '01/02/2020' như mẫu; giá trị không đúng dạng ISO giữ nguyên."""
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s or "")
    return f"{m[3]}/{m[2]}/{m[1]}" if m else s


TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
TEMPLATES.env.filters["ngay"] = _ngay
TEMPLATES.env.globals.update(
    page_label=page_label, card_pages=card_pages, addr=reader.addr, cite=reader.cite, doc_groups=doc_groups,
    highlight=lambda text, q: reader.highlight(text, reader.query_words(q)),  # đã thoát HTML, gạch dưới từ khớp
    fname=lambda p: re.split(r"[\\/]", (p or "").split("#vb", 1)[0])[-1], LOAI=reader.LOAI, OCR_LABEL=OCR_LABEL,
)
CSRF_TOKEN = secrets.token_urlsafe(32)
SHOW_CAP = 25  # mục hiện tối đa trên trang (5 đầu, "Xem thêm" từng 10); nhiều hơn thì dòng "còn nữa"
_ocr_cache: dict | None = None

app = FastAPI(title="Soi Luật")
# Windows lấy MIME từ registry; máy có registry lỗi trả text/plain và trình duyệt bỏ qua JS/CSS
for _ext, _type in ((".js", "text/javascript"), (".css", "text/css"), (".woff2", "font/woff2")):
    mimetypes.add_type(_type, _ext)


class _NoCacheStatic(StaticFiles):
    async def get_response(self, path, scope):
        r = await super().get_response(path, scope)
        r.headers["Cache-Control"] = "no-cache"  # sau khi nâng cấp app, trình duyệt phải hỏi lại app.js mới
        return r


app.mount("/static", _NoCacheStatic(directory=str(Path(__file__).parent / "static")), name="static")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _test_bypass() -> bool:
    return os.environ.get("SOILUAT_ALLOW_TEST_HOST") == "1"


def _host_ok(host_header: str) -> bool:
    name = (host_header or "").split(":")[0].lower()
    allowed = {"127.0.0.1", "localhost"}
    if _test_bypass():
        allowed.add("testserver")
    return name in allowed


class HostGuard(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if not _host_ok(request.headers.get("host") or ""):
            return PlainTextResponse("Bad Host", status_code=400)
        response = await call_next(request)
        if not _test_bypass():
            response.set_cookie(
                "soiluat_csrf",
                CSRF_TOKEN,
                samesite="strict",
                httponly=False,
            )
        return response


app.add_middleware(HostGuard)


@app.exception_handler(OverflowError)
async def _id_qua_lon(request, exc):
    """Id gõ tay lớn hơn số nguyên SQLite (2**63-1): không có bản ghi nào, không phải lỗi máy chủ."""
    return HTMLResponse("Không tìm thấy.", status_code=404)


def _check_csrf(request: Request, token: str = "") -> None:
    if _test_bypass():
        return
    cookie = request.cookies.get("soiluat_csrf")
    header = request.headers.get("x-csrf-token") or token
    if cookie != CSRF_TOKEN or header != CSRF_TOKEN:
        raise HTTPException(status_code=403, detail="CSRF")


def get_conn():
    conn = connect(db_path())
    init_schema(conn)
    return conn


def _tpl(request: Request, name: str, ctx: dict):
    ctx = {**ctx, "csrf_token": CSRF_TOKEN}
    return TEMPLATES.TemplateResponse(request, name, ctx)


def _card_dates(conn, cards) -> dict[int, dict]:
    """Ngày ban hành/hiệu lực, loại và cơ quan theo unit đầu của thẻ (Card không mang các trường này)."""
    ids = [c.unit_ids[0] for c in cards if c.unit_ids]
    if not ids:
        return {}
    q = ",".join("?" * len(ids))
    rows = conn.execute(
        "SELECT u.id, d.ngay_ban_hanh, d.ngay_hieu_luc, d.loai, d.co_quan FROM units u "
        f"JOIN documents d ON d.id = u.doc_id WHERE u.id IN ({q})",
        ids,
    ).fetchall()
    return {r["id"]: dict(r) for r in rows}


def _search(conn: sqlite3.Connection, q: str, loai: str, co_quan: str, hieu_luc: str) -> dict:
    """Tìm và lọc: `ids` đã lọc và cắt, `n_found` trước lọc, `n_ids` sau lọc trước cắt (P1 K1; H2, H3 dùng lại)."""
    # BM25 OR tự hạ trọng số từ phổ biến ("như thế nào", "được quy định"): không bỏ khung hỏi bằng danh sách
    result = cascade_search(conn, q)
    ids = apply_doc_filters(conn, result.ids, loai=loai, co_quan=co_quan, hieu_luc=hieu_luc)
    n_ids = len(ids)
    if result.note == "dieu" and n_ids > DIEU_CAP:
        ids = ids[:DIEU_CAP]
    # nhãn tin cậy nói về kết quả đầu: bộ lọc/giới hạn đổi kết quả đầu thì bỏ nhãn
    sure = result.sure if ids and result.ids and ids[0] == result.ids[0] else None
    return {"result": result, "ids": ids, "n_found": len(result.ids), "n_ids": n_ids, "sure": sure}


def _full_docs(conn: sqlite3.Connection, q: str, s: dict, loai: str = "", co_quan: str = "", hieu_luc: str = "") -> list[SimpleNamespace] | None:
    """Truy vấn chỉ có số hiệu (kể cả số hiệu một phần): mỗi văn bản khớp một mục "Mở toàn văn", không liệt kê
    mọi đơn vị. "Số hiệu + Điều n" mà văn bản không có Điều n cũng ra "Mở toàn văn", kèm câu không có Điều n.
    Văn bản lấy từ số hiệu (không từ đơn vị: bản quét chưa OCR hay văn bản chỉ có đoạn không có đơn vị Điều/Khoản) rồi lọc."""
    r = s["result"]
    dieu = find_dieu_so(q)
    if r.note != "so_hieu" or r.intent or (dieu and r.ids):
        return None
    doc_ids = filter_docs(conn, _so_hieu_docs(conn, q), loai=loai, co_quan=co_quan, hieu_luc=hieu_luc)
    out = []
    for did in doc_ids:
        d = conn.execute(
            "SELECT d.*, (SELECT COUNT(*) FROM units u WHERE u.doc_id = d.id AND u.level = 'dieu') AS n_dieu, "
            "(SELECT COUNT(*) FROM pages p WHERE p.doc_id = d.id) AS n_pages FROM documents d WHERE d.id = ?", (did,)
        ).fetchone()
        out.append(SimpleNamespace(full=True, doc_id=did, missing_dieu=dieu or "", **{k: d[k] for k in (
            "so_hieu", "loai", "co_quan", "file_path", "hieu_luc", "ngay_ban_hanh", "ngay_hieu_luc", "n_dieu", "n_pages")}))
    return out


def _ctx(conn: sqlite3.Connection, q: str, s: dict, loai: str = "", co_quan: str = "", hieu_luc: str = "") -> dict:
    """Thẻ và mục gọn từ kết quả tìm (P1 K1)."""
    r, ids = s["result"], s["ids"]
    full = _full_docs(conn, q, s, loai, co_quan, hieu_luc)
    idset = set(ids)
    cards = [] if full is not None else assemble_cards(
        conn, ids, synonym_note=r.note,
        fold_ids={i for i in r.fold_ids if i in idset}, f2_ids={i for i in r.f2_ids if i in idset},
        tiers=r.tiers, intent=r.intent,
    )
    items = full if full is not None else compact(conn, cards, q, limit=SHOW_CAP, cap=DIEU_CAP)
    cut_note = ""
    if r.note == "dieu" and s["n_ids"] > DIEU_CAP:
        cut_note = (f"Có {s['n_ids']} văn bản có Điều này, chỉ hiển thị {min(DIEU_CAP, SHOW_CAP, len(items))}. "
                    "Thêm số hiệu văn bản để thu hẹp.")
    return {"cards": cards, "items": items, "n_items": len(items), "cut_note": cut_note,
            "n": summarize(cards), "dates": _card_dates(conn, cards)}


def _log_query(conn: sqlite3.Connection, q: str, n: int) -> None:
    try:
        conn.execute("INSERT INTO query_log(query_raw, result_count, created_at) VALUES (?,?,?)", (q, n, _now()))
        conn.commit()
    except sqlite3.OperationalError:  # đang nạp file giữ khoá ghi: bỏ một dòng nhật ký, không làm hỏng kết quả
        conn.rollback()


def _search_ctx(q: str, loai: str, co_quan: str, hieu_luc: str) -> dict:
    conn = get_conn()
    ctx = {"cards": [], "items": [], "n_items": 0, "n_found": 0, "cut_note": "", "dates": {}, "n": {"n1": 0, "n2": 0, "n3": 0, "n4": 0}}
    hints: list[str] = []
    q2_note = ""
    sure = None
    n_docs = int(conn.execute("SELECT COUNT(*) AS n FROM documents").fetchone()["n"] or 0)
    empty_kho = n_docs == 0
    n_che = conn.execute("SELECT COUNT(*) AS n FROM unit_labels WHERE label = 'CHE_TAI'").fetchone()["n"]
    if not empty_kho and int(n_che or 0) == 0:
        q2_note = "Kho chưa có văn bản xử phạt — phần lớn thẻ là rủi ro chưa rõ chế tài (loại 3)."
    if q.strip():
        s = _search(conn, q, loai, co_quan, hieu_luc)
        sure = s["sure"]
        ctx = {**_ctx(conn, q, s, loai, co_quan, hieu_luc), "n_found": s["n_found"]}  # n_found: đoạn tìm được trước bộ lọc ("Không còn kết quả sau khi lọc")
        if ctx["cut_note"]:
            q2_note = (q2_note + " " if q2_note else "") + ctx["cut_note"]
        # "Mở toàn văn": số văn bản, để gõ số hiệu không lọt vào trang "Truy vấn bỏ sót" (lọc result_count = 0)
        _log_query(conn, q, len(ctx["items"]) if not ctx["cards"] else len(ctx["cards"]))
        if not ctx["items"]:
            hints = [r["term"] for r in conn.execute("SELECT term FROM synonyms WHERE approved = 1 LIMIT 8")]
    # số trên thanh bên "Liên kết chờ duyệt": cùng hàng chờ với trang /review
    n_queue = conn.execute("SELECT COUNT(*) FROM links WHERE confirmed = 0").fetchone()[0]
    conn.close()
    return {
        **ctx, "q": q, "loai": loai, "co_quan": co_quan, "hieu_luc": hieu_luc, "hints": hints,
        "q2_note": q2_note, "sure": sure, "empty_kho": empty_kho, "n_docs": n_docs, "n_queue": n_queue,
    }


@app.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    q: str = Query(""),
    loai: str = Query(""),
    co_quan: str = Query(""),
    hieu_luc: str = Query(""),
):
    ctx = _search_ctx(q, loai, co_quan, hieu_luc)
    if request.headers.get("HX-Request"):
        return _tpl(request, "_results.html", ctx)
    conn = get_conn()
    co_quans = [r[0] for r in conn.execute(
        "SELECT DISTINCT co_quan FROM documents WHERE co_quan IS NOT NULL AND co_quan != '' ORDER BY co_quan")]
    conn.close()
    return _tpl(request, "index.html", {**ctx, "mode": _mode_status(), "suffixes": ",".join(sorted(SUFFIXES)), "co_quans": co_quans})


def _mode_status(count_pending: bool = True) -> dict:
    """Chế độ tìm + tình trạng mô hình; đếm Điều chưa nhúng chỉ khi advance (đỡ tốn ở normal)."""
    conn = get_conn()
    mode = semantic.get_mode(conn)
    installed = semantic.model_installed()
    pending = semantic.pending(conn) if count_pending and mode == "advance" and installed else 0
    conn.close()
    return {"mode": mode, "installed": installed, "pending": pending}


@app.post("/settings/mode")
def set_search_mode(request: Request, mode: str = Form(...), q: str = Form(""), csrf_token: str = Form("")):
    _check_csrf(request, csrf_token)
    if mode not in semantic.MODES:
        raise HTTPException(status_code=400, detail="mode")
    conn = get_conn()
    semantic.set_mode(conn, mode)
    conn.close()
    JOBS.wake()  # chuyển sang Advance: bắt đầu nhúng nền các Điều chưa có vector
    return RedirectResponse("/?" + urlencode({"q": q}) if q else "/", status_code=303)


@app.get("/review", response_class=HTMLResponse)
def review(request: Request):
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT l.id, su.path AS spath, du.path AS dpath,
               su.raw_text AS stext, du.raw_text AS dtext,
               ds.so_hieu AS s_so, dd.so_hieu AS d_so
        FROM links l
        JOIN units su ON su.id = l.sanction_unit
        JOIN units du ON du.id = l.duty_unit
        JOIN documents ds ON ds.id = su.doc_id
        JOIN documents dd ON dd.id = du.doc_id
        WHERE l.confirmed = 0
        """
    ).fetchall()
    conn.close()
    items = []
    for r in rows:
        d = dict(r)
        d["saddr"] = display_addr(d.get("s_so"), d["spath"])
        d["daddr"] = display_addr(d.get("d_so"), d["dpath"])
        items.append(d)
    return _tpl(request, "review.html", {"rows": items})


@app.post("/links/{link_id}/confirm")
def confirm_link(
    request: Request, link_id: int, csrf_token: str = Form("")
):
    _check_csrf(request, csrf_token)
    conn = get_conn()
    conn.execute(
        "UPDATE links SET confirmed = 1, reviewed_at = ? WHERE id = ?",
        (_now(), link_id),
    )
    conn.commit()
    conn.close()
    return RedirectResponse("/review", status_code=303)


@app.post("/links/{link_id}/reject")
def reject_link(
    request: Request, link_id: int, csrf_token: str = Form("")
):
    _check_csrf(request, csrf_token)
    conn = get_conn()
    conn.execute("DELETE FROM links WHERE id = ?", (link_id,))
    conn.commit()
    conn.close()
    return RedirectResponse("/review", status_code=303)


@app.get("/review/pages", response_class=HTMLResponse)
def review_pages(request: Request):
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT p.id, p.page_no, p.kind, p.ocr_status, p.verification_status,
               p.raw_text, d.file_path, d.so_hieu
        FROM pages p
        JOIN documents d ON d.id = p.doc_id
        WHERE p.extraction_method LIKE '%ocr%'
           OR p.ocr_status IN ('cho_ocr','ocr_xong','can_duyet')
        ORDER BY p.id
        """
    ).fetchall()
    conn.close()
    return _tpl(request, "review_pages.html", {"rows": [dict(r) for r in rows]})


@app.get("/review/hints", response_class=HTMLResponse)
def review_hints(request: Request):
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT h.id, h.kind, h.target_so_hieu, h.snippet, h.confirmed,
               d.file_path, d.so_hieu
        FROM effect_hints h
        JOIN documents d ON d.id = h.source_doc_id
        WHERE h.confirmed = 0
        ORDER BY h.id
        """
    ).fetchall()
    conn.close()
    return _tpl(request, "review_hints.html", {"rows": [dict(r) for r in rows]})


@app.post("/hints/{hint_id}/confirm")
def confirm_hint(request: Request, hint_id: int, csrf_token: str = Form("")):
    _check_csrf(request, csrf_token)
    conn = get_conn()
    conn.execute(
        "UPDATE effect_hints SET confirmed = 1, reviewed_at = ? WHERE id = ?",
        (_now(), hint_id),
    )
    conn.commit()
    conn.close()
    return RedirectResponse("/review/hints", status_code=303)


@app.post("/hints/{hint_id}/reject")
def reject_hint(request: Request, hint_id: int, csrf_token: str = Form("")):
    _check_csrf(request, csrf_token)
    conn = get_conn()
    conn.execute("DELETE FROM effect_hints WHERE id = ?", (hint_id,))
    conn.commit()
    conn.close()
    return RedirectResponse("/review/hints", status_code=303)


@app.get("/review/subjects", response_class=HTMLResponse)
def review_subjects(request: Request):
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, phrase, kind, approved FROM subject_rules ORDER BY kind, id"
    ).fetchall()
    conn.close()
    return _tpl(request, "review_subjects.html", {"rows": [dict(r) for r in rows]})


@app.post("/subjects")
def add_subject(
    request: Request,
    phrase: str = Form(...),
    kind: str = Form(...),
    csrf_token: str = Form(""),
):
    _check_csrf(request, csrf_token)
    if kind not in ("uu_tien", "ha_uu_tien"):
        kind = "uu_tien"
    phrase = phrase.strip()
    if phrase:
        from soiluat.fold import fold_search

        conn = get_conn()
        try:
            conn.execute(
                "INSERT INTO subject_rules(phrase, phrase_fold, kind, approved) "
                "VALUES (?, ?, ?, 1)",
                (phrase, fold_search(phrase), kind),
            )
            conn.commit()
        except Exception:
            conn.rollback()
        conn.close()
    return RedirectResponse("/review/subjects", status_code=303)


@app.post("/subjects/{rule_id}/delete")
def delete_subject(request: Request, rule_id: int, csrf_token: str = Form("")):
    _check_csrf(request, csrf_token)
    conn = get_conn()
    conn.execute("DELETE FROM subject_rules WHERE id = ?", (rule_id,))
    conn.commit()
    conn.close()
    return RedirectResponse("/review/subjects", status_code=303)


@app.get("/review/synonyms", response_class=HTMLResponse)
def review_synonyms(request: Request):
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, term, alt, kind, approved, reviewed_at FROM synonyms "
        "ORDER BY approved, term, alt"
    ).fetchall()
    kinds = [r["kind"] for r in conn.execute("SELECT DISTINCT kind FROM synonyms")]
    conn.close()
    return _tpl(
        request,
        "review_synonyms.html",
        {"rows": [dict(r) for r in rows], "kinds": kinds},
    )


@app.post("/synonyms")
def add_synonym(
    request: Request,
    term: str = Form(...),
    alt: str = Form(...),
    kind: str = Form(""),
    csrf_token: str = Form(""),
):
    _check_csrf(request, csrf_token)
    term, alt = term.strip(), alt.strip()
    if term and alt and term != alt:
        conn = get_conn()
        # người duyệt tự thêm → coi như đã duyệt
        conn.execute(
            "INSERT OR IGNORE INTO synonyms(term, alt, kind, approved, reviewed_at) "
            "VALUES (?, ?, ?, 1, ?)",
            (term, alt, kind.strip() or "dong_nghia", _now()),
        )
        conn.commit()
        conn.close()
    return RedirectResponse("/review/synonyms", status_code=303)


@app.post("/synonyms/{syn_id}/approve")
def approve_synonym(
    request: Request,
    syn_id: int,
    approved: int = Form(1),
    csrf_token: str = Form(""),
):
    _check_csrf(request, csrf_token)
    conn = get_conn()
    conn.execute(
        "UPDATE synonyms SET approved = ?, reviewed_at = ? WHERE id = ?",
        (1 if approved else 0, _now(), syn_id),
    )
    conn.commit()
    conn.close()
    return RedirectResponse("/review/synonyms", status_code=303)


@app.post("/synonyms/{syn_id}/delete")
def delete_synonym(request: Request, syn_id: int, csrf_token: str = Form("")):
    _check_csrf(request, csrf_token)
    conn = get_conn()
    conn.execute("DELETE FROM synonyms WHERE id = ?", (syn_id,))
    conn.commit()
    conn.close()
    return RedirectResponse("/review/synonyms", status_code=303)


@app.get("/review/docs", response_class=HTMLResponse)
def review_docs(request: Request, doc_id: int | None = Query(None, alias="id")):
    """?id=N chỉ một văn bản (liên kết "Sửa số hiệu" từ trình đọc); không có thì cả kho, không phân trang."""
    conn = get_conn()
    docs = conn.execute(
        """
        SELECT id, file_path, so_hieu, loai, co_quan, hieu_luc, struct_score,
               extraction_method, ngay_ban_hanh, ngay_hieu_luc
        FROM documents
        WHERE ? IS NULL OR id = ?
        ORDER BY IFNULL(struct_score, 1) ASC
        """,
        (doc_id, doc_id),
    ).fetchall()
    items = []
    for d in docs:
        units = conn.execute(
            "SELECT id, path, level, title, boundary_confidence, raw_text "
            "FROM units WHERE doc_id = ? ORDER BY id LIMIT 40",
            (d["id"],),
        ).fetchall()
        items.append({"doc": dict(d), "units": [dict(u) for u in units]})
    conn.close()
    return _tpl(request, "review_docs.html", {"items": items, "only": doc_id is not None})


@app.post("/docs/{doc_id}/hieu-luc")
def set_hieu_luc(
    request: Request,
    doc_id: int,
    hieu_luc: str = Form(...),
    csrf_token: str = Form(""),
):
    _check_csrf(request, csrf_token)
    if hieu_luc not in ("con", "het", "chua_ro"):
        hieu_luc = "chua_ro"
    conn = get_conn()
    conn.execute(
        "UPDATE documents SET hieu_luc = ? WHERE id = ?",
        (hieu_luc, doc_id),
    )
    conn.commit()
    conn.close()
    return RedirectResponse("/review/docs", status_code=303)


@app.post("/docs/{doc_id}/so-hieu")
def set_so_hieu(
    request: Request,
    doc_id: int,
    so_hieu: str = Form(""),
    csrf_token: str = Form(""),
):
    _check_csrf(request, csrf_token)
    from soiluat.sohieu import so_hieu_search_key

    so = so_hieu.strip()
    conn = get_conn()
    conn.execute(
        "UPDATE documents SET so_hieu = ?, so_hieu_search = ? WHERE id = ?",
        (so or None, so_hieu_search_key(so) if so else "", doc_id),
    )
    conn.commit()
    conn.close()
    return RedirectResponse("/review/docs", status_code=303)


@app.get("/unit/{unit_id}")
def unit_view(unit_id: int, q: str = ""):
    """Liên kết cũ (0.8, thẻ Word đã xuất) và "Xem nguồn" mở trình đọc tại đúng đơn vị."""
    conn = get_conn()
    u = conn.execute("SELECT doc_id, path FROM units WHERE id = ?", (unit_id,)).fetchone()
    conn.close()
    if u is None:
        return HTMLResponse("Không tìm thấy đơn vị.", status_code=404)
    qs = urlencode({"path": u["path"], "u": unit_id, **({"q": q} if q else {})})
    return RedirectResponse(f"/doc/{u['doc_id']}?{qs}#u{unit_id}", status_code=303)


HL_PILL = {"con": ("Còn hiệu lực", "pos"), "het": ("Hết hiệu lực", "neg")}


@app.get("/doc/{doc_id}", response_class=HTMLResponse)
def doc_view(request: Request, doc_id: int, u: int | None = None, path: str = "", q: str = "",
             page: int | None = None):
    """Trình đọc: toàn văn, đơn vị chọn được tô và cuộn tới. Không ghi DB."""
    conn = get_conn()
    try:
        if conn.execute("SELECT 1 FROM documents WHERE id = ?", (doc_id,)).fetchone() is None:
            return HTMLResponse("Không tìm thấy văn bản.", status_code=404)
        sel = reader.resolve_sel(conn, doc_id, u, path)
        view = reader.build_view(conn, doc_id, sel, q)
        d = view["doc"]
        su = conn.execute("SELECT * FROM units WHERE id = ?", (sel,)).fetchone() if sel else None
        pf, pt = (su["page_from"], su["page_to"]) if su else (1, 2**31)
        pages = conn.execute(
            "SELECT page_no, kind, ocr_status, verification_status, raw_text, reviewed_text FROM pages "
            "WHERE doc_id = ? ORDER BY page_no", (doc_id,)
        ).fetchall()
        ocr_warn = _ocr_unverified(conn, pf, pt, doc_id)
    finally:
        conn.close()
    fname = Path(d["file_path"].split("#vb", 1)[0]).name
    name = " ".join(x for x in (reader.LOAI.get(d["loai"] or "", ""), d["so_hieu"] or "") if x) or fname
    if su is None:
        where, cite = "Toàn văn", name
    else:
        where = reader.addr(su["path"])
        cite = reader.cite(d["so_hieu"], d["loai"], su["path"]) if d["so_hieu"] else f"{where} {fname}"
    can_view = pageimg.can_view(d["file_path"])
    has_img = can_view and pageimg.source_file(d["file_path"]) is not None
    in_sel = [p for p in pages if su and (su["page_from"] or 0) <= p["page_no"] <= (su["page_to"] or su["page_from"] or 0)]
    ctx = {
        "view": view, "d": d, "su": su, "name": name, "fname": fname, "where": where, "cite": cite,
        "pill": HL_PILL.get(d["hieu_luc"], ("Hiệu lực chưa rõ", "neu")), "ocr_warn": ocr_warn,
        "pages": in_sel, "raw_pages": [] if has_img else pages, "q": q,
        "can_view": can_view, "has_img": has_img, "page_nos": [p["page_no"] for p in pages],
        "orig_path": str(pageimg.stored_path(d["file_path"])),
        "page": page or (su["page_from"] if su else None) or (pages[0]["page_no"] if pages else 1),  # văn bản tách từ tệp lớn bắt đầu ở trang > 1
        "full": not request.headers.get("HX-Request"),
    }
    return _tpl(request, "doc.html" if ctx["full"] else "_reader.html", ctx)


@app.get("/page/{doc_id}/{page_no}")
def page_image(doc_id: int, page_no: int):
    """Ảnh trang gốc để đối chiếu thẻ (đặc biệt chữ OCR). Chỉ phục vụ file đã nạp, theo doc_id."""
    conn = get_conn()
    row = conn.execute("SELECT file_path FROM documents WHERE id = ?", (doc_id,)).fetchone()
    conn.close()
    src = pageimg.source_file(row["file_path"]) if row else None
    kind = pageimg.VIEWABLE.get(src.suffix.lower()) if src else None
    if kind is None:
        return HTMLResponse("Không có ảnh trang gốc (file gốc không còn hoặc không phải PDF/ảnh).", status_code=404)
    hdr = {"Cache-Control": "private, max-age=3600"}
    if kind == "pdf":
        png = pageimg.render_pdf_page(src, page_no)
        if png is None:
            return HTMLResponse("Không có trang này.", status_code=404)
        return Response(png, media_type="image/png", headers=hdr)
    if page_no != 1:  # ảnh đơn chỉ có một trang
        return HTMLResponse("Không có trang này.", status_code=404)
    return FileResponse(src, media_type="image/png" if kind == "png" else "image/jpeg", headers=hdr)


@app.get("/missed", response_class=HTMLResponse)
def missed(request: Request):
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, query_raw, result_count, created_at FROM query_log "
        "WHERE result_count = 0 ORDER BY id DESC LIMIT 100"
    ).fetchall()
    conn.close()
    return _tpl(request, "missed.html", {"rows": [dict(r) for r in rows]})


def ocr_status(refresh: bool = False) -> dict:
    """Trạng thái OCR (Tesseract + gói vie), nhớ kết quả; module OCR chỉ nạp ở lần gọi đầu."""
    global _ocr_cache
    if _ocr_cache is None or refresh:
        from soiluat.importer import check_ocr

        _ocr_cache = check_ocr()
    return _ocr_cache


def _safe_name(name: str) -> str:
    base = Path((name or "").replace("\\", "/")).name
    base = re.sub(r'[<>:"/\|?*\x00-\x1f]', "_", base).strip(" .")
    return base or "tai-lieu"


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _store_upload(up: UploadFile, folder: Path) -> Path:
    """Lưu file tải lên vào data/files. Trùng tên + trùng nội dung: dùng lại file cũ;
    trùng tên khác nội dung: 'tên (2).đuôi'. Giữ bản gốc để còn xem trang gốc đối chiếu."""
    folder.mkdir(parents=True, exist_ok=True)
    tmp = folder / f".{uuid.uuid4().hex}.part"
    with open(tmp, "wb") as out:
        shutil.copyfileobj(up.file, out)
    name = _safe_name(up.filename or "")
    stem, suf = Path(name).stem, Path(name).suffix
    dest, n, sha = folder / name, 1, ""
    while dest.exists():
        sha = sha or _sha(tmp)
        if _sha(dest) == sha:
            tmp.unlink()
            return dest
        n += 1
        dest = folder / f"{stem} ({n}){suf}"
    tmp.replace(dest)
    return dest


@app.get("/api/status")
def api_status(ocr: str = Query("")):
    """Tình trạng cho giao diện: số văn bản, hàng đợi nạp, nhúng vector, chế độ tìm; ?ocr=1 kèm OCR (lai = kiểm lại)."""
    conn = get_conn()
    docs = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    snap = JOBS.snapshot(conn)
    conn.close()
    emb = snap["embed"]
    mode = _mode_status(count_pending=not emb["running"])
    if emb["running"]:
        mode["pending"] = max(0, emb["total"] - emb["done"])
    out = {"docs": docs, "jobs": snap, "mode": mode}
    if ocr:
        out["ocr"] = ocr_status(refresh=(ocr == "lai"))
    return out


@app.post("/import/files")
def import_files(
    request: Request,
    files: list[UploadFile] = File(...),
    ocr: str = Form(""),
    doan: str = Form(""),
    csrf_token: str = Form(""),
):
    """Nhận nhiều file (hoặc cả thư mục) từ trình duyệt, lưu vào data/files rồi xếp hàng nạp."""
    _check_csrf(request, csrf_token)
    ok = [f for f in files if Path(_safe_name(f.filename or "")).suffix.lower() in SUFFIXES]
    paths = [_store_upload(f, data_dir() / "files") for f in ok]
    res = JOBS.submit(paths, ocr=bool(ocr), doan=bool(doan)) if paths else {"queued": 0, "skipped": 0}
    res["skipped"] += len(files) - len(ok)
    return JSONResponse({"ok": True, **res})


@app.post("/import/path")
def import_path(
    request: Request,
    path: str = Form(...),
    ocr: str = Form(""),
    doan: str = Form(""),
    csrf_token: str = Form(""),
):
    """Nạp file/thư mục đã có trên máy, giữ nguyên chỗ cũ (không sao chép)."""
    _check_csrf(request, csrf_token)
    src = Path(path.strip().strip('"'))
    if not path.strip() or not src.exists():
        return JSONResponse({"ok": False, "error": f"Không thấy file/thư mục: {path}"}, status_code=400)
    return JSONResponse({"ok": True, **JOBS.submit([src], ocr=bool(ocr), doan=bool(doan))})


@app.post("/import/clear")
def import_clear(request: Request, csrf_token: str = Form("")):
    _check_csrf(request, csrf_token)
    JOBS.clear()
    return {"ok": True}


@app.get("/jobs")
def jobs_moved():
    return RedirectResponse("/#import", status_code=307)


@app.post("/export")
def export(
    request: Request,
    uid: list[int] = Form(default=[]),
    csrf_token: str = Form(""),
):
    _check_csrf(request, csrf_token)
    conn = get_conn()
    dest = data_dir() / "export.docx"
    cards = assemble_cards(conn, uid)
    export_cards(cards, dest)
    conn.close()
    return FileResponse(
        dest,
        filename="soiluat-baocao.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@app.post("/backup")
def backup(request: Request, csrf_token: str = Form("")):
    _check_csrf(request, csrf_token)
    dest = data_dir() / "backup" / "soiluat.db"
    backup_db(db_path(), dest)
    return {"ok": True, "path": str(dest)}


def _port_busy(port: int) -> bool:
    # thử kết nối trước: app khác nghe [::]:port vẫn trả lời 127.0.0.1 dù bind được
    try:
        with socket.create_connection((HOST, port), timeout=0.3):
            return True
    except OSError:
        pass
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((HOST, port))
        return False
    except OSError:
        return True
    finally:
        s.close()


def pick_port(start: int, tries: int = 20) -> int:
    for port in range(start, start + tries + 1):
        if not _port_busy(port):
            return port
    raise SystemExit(f"Cổng {start}–{start + tries} đều bận. Đặt SOILUAT_PORT hoặc --port khác.")


def _warm_models() -> None:
    conn = get_conn()
    try:
        semantic.warm(conn)
        crossrank.ranker()
    except Exception:  # noqa: BLE001 — nạp trước chỉ để nhanh hơn; lỗi thì để lần tìm đầu tự nạp
        pass
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["import"]:  # SoiLuat.exe import <đường dẫn> [--ocr] [--nhung]: nạp hàng loạt từ dòng lệnh
        from soiluat.importer import main as import_main

        raise SystemExit(import_main(argv[1:]))
    ap = argparse.ArgumentParser(prog="soiluat", description="Soi Luật — tra cứu, chỉ 127.0.0.1")
    ap.add_argument(
        "--port",
        type=int,
        default=os.environ.get("SOILUAT_PORT") or str(PORT),
        help="cổng mong muốn (mặc định 8000 hoặc env SOILUAT_PORT); bận thì thử 20 cổng kế tiếp",
    )
    args = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # chuyển hướng ra file: cp1252 không in được tiếng Việt
        except Exception:  # noqa: BLE001
            pass
    data_dir().mkdir(parents=True, exist_ok=True)
    conn = get_conn()
    conn.close()
    threading.Thread(target=_warm_models, name="soiluat-warm", daemon=True).start()
    port = pick_port(args.port)
    url = f"http://{HOST}:{port}/"
    print(f"Soi Luật đang chạy: {url}", flush=True)
    if os.environ.get("SOILUAT_NO_BROWSER") != "1":
        threading.Timer(1.5, webbrowser.open, (url,)).start()
    uvicorn.run("soiluat.app:app", host=HOST, port=port, reload=False)


if __name__ == "__main__":
    main()
