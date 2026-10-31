"""FTS5 nhiều tầng + tra số hiệu. Advance thêm vector toàn kho (semantic) và reranker top-5 (crossrank)."""

from __future__ import annotations

import json
import re
import sqlite3
import threading
from dataclasses import dataclass, field

from soiluat.fold import (
    fold_search,
    iy_norm_text,
    iy_norm_token,
    iy_token_alts,
    query_has_accent,
    search_accent,
)
from soiluat import crossrank, semantic
from soiluat.query import split_intent
from soiluat.sohieu import (
    citation_remainder,
    find_dieu_so,
    find_so_hieu,
    find_so_hieu_prefix,
    so_hieu_search_key,
)

_LEVEL_SQL = (
    "CASE level WHEN 'khoan' THEN 0 WHEN 'diem' THEN 1 "
    "WHEN 'dieu' THEN 2 ELSE 3 END, id"
)

RISK_LABELS = ("NGHIA_VU", "CAM", "THOI_HAN", "DIEU_KIEN", "CHE_TAI")
_OCR_PAGE_COND = """
p.extraction_method LIKE '%ocr%'
AND IFNULL(p.verification_status, '') != 'da_doi_chieu'
AND p.ocr_status NOT IN ('khong_can', 'da_doi_chieu')
"""


@dataclass
class CascadeResult:
    ids: list[int]
    tier: int
    note: str
    fold_ids: set[int] = field(default_factory=set)
    f2_ids: set[int] = field(default_factory=set)
    tiers: dict[int, int] = field(default_factory=dict)  # id -> tầng khớp (0 = tra số hiệu)
    intent: str = ""
    sure: bool | None = None  # Advance: kết quả đầu "độ tin cậy cao"; None = không chấm (Normal, tra số hiệu, thiếu mô hình)

    def __iter__(self):
        yield self.ids
        yield self.tier
        yield self.note


def fts_quote(tok: str) -> str:
    t = (tok or "").replace('"', '""').strip()
    return f'"{t}"' if t else ""


PhraseIndex = dict[str, list[tuple[tuple[str, ...], str]]]


def phrase_index(phrases) -> PhraseIndex:
    """Từ đầu (chuẩn i/y) -> [(các từ, cụm gốc)], dài trước."""
    idx: PhraseIndex = {}
    for p in set(phrases):
        key = tuple(iy_norm_text(p).split())
        if key:
            idx.setdefault(key[0], []).append((key, p))
    for v in idx.values():
        v.sort(key=lambda x: (-len(x[0]), -len(x[1])))
    return idx


def tokenize(normalized: str, phrases=(), indexes=()) -> list[str]:
    """Tách từ theo cụm dài nhất trong từ vựng; tra theo từ đầu, không quét mọi cụm."""
    idxs = [phrase_index(phrases), *indexes] if phrases else list(indexes)
    words = (normalized or "").split()
    keys = [iy_norm_token(w) for w in words]
    out: list[str] = []
    i = 0
    while i < len(words):
        best: tuple[tuple[str, ...], str] | None = None
        for idx in idxs:
            for key, p in idx.get(keys[i], ()):
                n = len(key)
                if best is not None and n <= len(best[0]):
                    break
                if tuple(keys[i : i + n]) == key:
                    best = (key, p)
                    break
        if best:
            out.append(best[1])
            i += len(best[0])
        else:
            out.append(words[i])
            i += 1
    return [t for t in out if t]


# Cache tên Điều theo (file DB, nhánh); khoá phiên bản = (max id, count) của units,
# nạp thêm / xoá / nạp lại là tự làm mới. App mở connection mới mỗi request nên cache ở mức module.
_TITLE_CACHE: dict[tuple[str, bool], tuple[tuple, PhraseIndex]] = {}


def _db_file(conn: sqlite3.Connection) -> str:
    for r in conn.execute("PRAGMA database_list"):
        if r[1] == "main" and r[2]:
            return r[2]
    return f":memory:{id(conn)}"


_TITLE_LOCK = threading.Lock()  # tìm đồng thời dùng chung một lần dựng, không mỗi luồng một bản


def _title_index(conn: sqlite3.Connection, accent: bool) -> PhraseIndex:
    from soiluat.jobs import JOBS  # nạp chậm: jobs không import search ở mức module

    ver = tuple(conn.execute("SELECT IFNULL(MAX(id), 0), COUNT(*) FROM units").fetchone())
    key = (_db_file(conn), accent)
    hit = _TITLE_CACHE.get(key)
    # đang nâng cấp dữ liệu: mỗi văn bản dựng lại đổi khoá mà tên Điều gần như không đổi, nên dùng bản cũ (dựng lại 1–2 s mỗi lần tìm);
    # xong nâng cấp khoá lệch bản đã giữ nên lần tìm sau dựng lại đúng một lần
    if hit and (hit[0] == ver or JOBS.migrate["running"]):
        return hit[1]
    with _TITLE_LOCK:
        hit = _TITLE_CACHE.get(key)
        if hit and hit[0] == ver:
            return hit[1]
        if accent:
            rows = conn.execute(
                "SELECT DISTINCT title FROM units WHERE level = 'dieu' AND title != ''"
            )
            titles = (search_accent(r[0]) for r in rows)
        else:
            rows = conn.execute(
                "SELECT DISTINCT title_search FROM units WHERE level = 'dieu' AND title_search != ''"
            )
            titles = (r[0] for r in rows)
        idx = phrase_index(t for t in titles if t and 1 < len(t.split()) <= 6)
        _TITLE_CACHE[key] = (ver, idx)
        return idx


def vocab_indexes(conn: sqlite3.Connection, *, accent: bool) -> list[PhraseIndex]:
    """Từ vựng tách từ: từ điển đã duyệt (đọc mới mỗi lần, bảng nhỏ) + tên Điều (cache)."""
    syn = [p for pair in load_synonyms(conn, accent=accent) for p in pair]
    return [phrase_index(syn), _title_index(conn, accent)]


def folded_tokens(q: str) -> list[str]:
    return tokenize(fold_search(q))


def _fts_term(tok: str) -> str:
    alts = [fts_quote(a) for a in iy_token_alts(tok) if fts_quote(a)]
    if not alts:
        return ""
    if len(alts) == 1:
        return alts[0]
    return "(" + " OR ".join(alts) + ")"


def fts_and(tokens: list[str]) -> str:
    parts = [_fts_term(t) for t in tokens if _fts_term(t)]
    return " AND ".join(parts)


def load_synonyms(conn: sqlite3.Connection, *, accent: bool) -> list[tuple[str, str]]:
    rows = conn.execute(
        "SELECT term, alt FROM synonyms WHERE approved = 1"
    ).fetchall()
    conv = search_accent if accent else fold_search
    return [(conv(r["term"]), conv(r["alt"])) for r in rows]


def _replace_term(tokens: list[str], term: str, alt: str) -> list[str] | None:
    """Thay đoạn token liên tiếp ghép lại bằng `term` (token có thể là cụm nhiều tiếng)."""
    want = iy_norm_text(term)
    if not want or not alt.strip():
        return None
    for i in range(len(tokens)):
        joined = ""
        for j in range(i, len(tokens)):
            joined = f"{joined} {iy_norm_text(tokens[j])}".strip()
            if joined == want:
                return tokens[:i] + [alt] + tokens[j + 1 :]
            if not want.startswith(joined + " "):
                break
    return None


def _zero_pad(key: str) -> str:
    """'2/2021/tt-btc' → '02/2021/tt-btc': văn bản ghi số hiệu một chữ số có số 0 đứng đầu, người gõ hay bỏ."""
    return re.sub(r"^(\d)/", r"0\1/", key)


def _so_hieu_docs(conn: sqlite3.Connection, raw_query: str) -> list[int]:
    full = find_so_hieu(raw_query)
    prefix = None if full else find_so_hieu_prefix(raw_query)
    if full:
        key = so_hieu_search_key(full)
        rows = conn.execute(
            "SELECT id FROM documents WHERE so_hieu_search IN (?, ?)",
            (key, _zero_pad(key)),
        ).fetchall()
    elif prefix:
        key = fold_search(prefix)
        rows = conn.execute(
            "SELECT id FROM documents WHERE so_hieu_search LIKE ? OR so_hieu_search LIKE ?",
            (key + "/%", _zero_pad(key) + "/%"),
        ).fetchall()
    else:
        return []
    return [int(r["id"]) for r in rows]


def _dieu_where(dieu: str) -> tuple[str, list[str]]:
    """Điều n gồm cả bản trùng số D{n}~k (H4)."""
    needle = f"D{dieu}"
    return (
        "(path = ? COLLATE NOCASE OR path LIKE ? OR path LIKE ?)",  # văn bản viết "Điều 1A" hay "1a", người gõ bất kỳ
        [needle, needle + ".%", needle + "~%"],
    )


def _units_for_docs(
    conn: sqlite3.Connection,
    doc_ids: list[int],
    dieu: str | None,
) -> list[int]:
    ids: list[int] = []
    for did in doc_ids:
        if dieu:
            where, params = _dieu_where(dieu)
            rows = conn.execute(
                f"SELECT id FROM units WHERE doc_id = ? AND {where} "
                f"AND level IN ('dieu','khoan','diem') ORDER BY {_LEVEL_SQL}",
                [did, *params],
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id FROM units WHERE doc_id = ? AND "
                f"level IN ('dieu','khoan','diem') ORDER BY {_LEVEL_SQL}",
                (did,),
            ).fetchall()
        ids.extend(int(r["id"]) for r in rows)
    return ids


def lookup_so_hieu(
    conn: sqlite3.Connection,
    raw_query: str,
) -> list[int]:
    docs = _so_hieu_docs(conn, raw_query)
    if not docs:
        return []
    return _units_for_docs(conn, docs, find_dieu_so(raw_query))


DIEU_CAP = 100  # "Điều n" không kèm số hiệu: mỗi văn bản một Điều, dựng quá nhiều thẻ thì chậm


def lookup_dieu_all_docs(conn: sqlite3.Connection, dieu: str) -> list[int]:
    needle = f"D{dieu}"
    rows = conn.execute(
        "SELECT id FROM units WHERE (path = ? COLLATE NOCASE OR path LIKE ?) AND level = 'dieu' ORDER BY id",
        (needle, needle + "~%"),
    ).fetchall()
    return [int(r["id"]) for r in rows]


def _ids_on_dieu(conn: sqlite3.Connection, ids: list[int], dieu: str) -> list[int]:
    needle = f"D{dieu}".lower()
    keep: list[int] = []
    meta = _fetch_units(conn, ids)
    for uid in ids:
        row = meta.get(uid)
        if row is None:
            continue
        path = (row["path"] or "").lower()
        if path == needle or path.startswith((needle + ".", needle + "~")):
            keep.append(uid)
    return keep


def match_units(
    conn: sqlite3.Connection,
    query: str,
    *,
    doc_id: int | None = None,
    doc_ids: list[int] | None = None,
    labels: tuple[str, ...] | None = None,
    limit: int = 50,
    match_sql: str | None = None,
    branch: str = "fold",
    only_ids: list[int] | None = None,
) -> list[int]:
    if match_sql is None:
        match_sql = fts_and(folded_tokens(query))
    return [
        i
        for i, _ in scored_units(
            conn, match_sql, branch=branch, doc_id=doc_id, doc_ids=doc_ids, labels=labels,
            limit=limit, only_ids=only_ids,
        )
    ]


# trọng số bm25 theo thứ tự cột units_fts: title_search, search_accent, search_text,
# context_search, context_accent — ngữ cảnh (khoản/Điều cha) 0,5 (đo trên bộ Zalo)
BM25_WEIGHTS = "1.0, 1.0, 1.0, 0.5, 0.5"


def scored_units(
    conn: sqlite3.Connection,
    match_sql: str,
    *,
    branch: str = "fold",
    doc_id: int | None = None,
    doc_ids: list[int] | None = None,
    labels: tuple[str, ...] | None = None,
    limit: int = 50,
    only_ids: list[int] | None = None,
) -> list[tuple[int, float]]:
    """(id, điểm bm25) — điểm âm, càng nhỏ càng liên quan."""
    if not match_sql:
        return []
    cols = (
        "{search_accent context_accent}"
        if branch == "accent"
        else "{search_text context_search}"
    )
    sql_match = f"{cols} : ({match_sql})"
    extra = ""
    params: list = [sql_match]
    join = bool(doc_ids or doc_id is not None or labels)
    if doc_ids:
        placeholders = ",".join("?" * len(doc_ids))
        extra += f" AND u.doc_id IN ({placeholders})"
        params.extend(int(i) for i in doc_ids)
    elif doc_id is not None:
        extra += " AND u.doc_id = ?"
        params.append(doc_id)
    if labels:
        placeholders = ",".join("?" * len(labels))
        extra += (
            f" AND u.id IN (SELECT unit_id FROM unit_labels WHERE label IN ({placeholders}))"
        )
        params.extend(labels)
    if only_ids is not None:
        # dấu +: không để SQLite duyệt từng id rồi chạy lại cả truy vấn FTS cho mỗi id (kho OCR: 0,7 s → 3 ms)
        extra += " AND +f.rowid IN (SELECT value FROM json_each(?))"
        params.append(json.dumps(only_ids))
    params.append(limit)
    # không JOIN units khi không cần cột của nó: JOIN hàng trăm nghìn dòng khớp làm chậm gấp ~2
    src = "units_fts f JOIN units u ON u.id = f.rowid" if join else "units_fts f"
    try:
        rows = conn.execute(
            f"""
            SELECT f.rowid, bm25(units_fts, {BM25_WEIGHTS}) AS s
            FROM {src}
            WHERE units_fts MATCH ?
            {extra}
            ORDER BY s
            LIMIT ?
            """,
            params,
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    return [(int(r[0]), float(r[1])) for r in rows]


def _ocr_unit_ids(conn: sqlite3.Connection) -> list[int]:
    """Unit thuộc trang OCR chưa đối chiếu (F2). Chỉ xét văn bản có trang OCR (kho chữ không đụng tới), rồi mỗi unit tra
    trang của nó qua chỉ mục (doc_id, page_no): không ghép trang x unit cùng văn bản (bậc hai theo số trang)."""
    rows = conn.execute(
        f"""
        SELECT u.id FROM units u
        WHERE u.doc_id IN (SELECT p.doc_id FROM pages p WHERE {_OCR_PAGE_COND})
          AND EXISTS (SELECT 1 FROM pages p WHERE p.doc_id = u.doc_id AND {_OCR_PAGE_COND}
                      AND p.page_no BETWEEN IFNULL(u.page_from, 1)
                                        AND IFNULL(u.page_to, IFNULL(u.page_from, 1)))
        """
    ).fetchall()
    return [int(r[0]) for r in rows]


def _token_df(conn: sqlite3.Connection, token: str) -> int:
    """Số đơn vị chứa từ (mọi cột). units_vocab là fts5vocab 'row'."""
    try:
        row = conn.execute("SELECT doc FROM units_vocab WHERE term = ?", (token,)).fetchone()
    except sqlite3.OperationalError:
        return 0
    return int(row[0]) if row else 0


_RISK_IN = ",".join(f"'{x}'" for x in RISK_LABELS)


def _fetch_units(
    conn: sqlite3.Connection,
    ids: list[int],
    meta: dict[int, sqlite3.Row] | None = None,
) -> dict[int, sqlite3.Row]:
    """Một truy vấn cho cả lô (kèm cờ nhãn rủi ro, đường dẫn cha); chỉ đọc id chưa có trong meta."""
    meta = {} if meta is None else meta
    need = [i for i in dict.fromkeys(ids) if i not in meta]
    if need:
        rows = conn.execute(
            f"""
            SELECT u.id, u.doc_id, u.path, u.level, p.path AS ppath, p.level AS plevel,
              EXISTS(SELECT 1 FROM unit_labels l
                     WHERE l.unit_id = u.id AND l.label IN ({_RISK_IN})) AS risk
            FROM units u LEFT JOIN units p ON p.id = u.parent_id
            WHERE u.id IN (SELECT value FROM json_each(?))
            """,
            (json.dumps(need),),
        ).fetchall()
        meta.update({int(r["id"]): r for r in rows})
    return meta


CANDIDATES = 300  # ứng viên chấm điểm
RETURN_TOP = 100  # đơn vị trả về cho dựng thẻ (xếp theo độ liên quan)
# hệ số nhân điểm bm25 theo mức khớp: cả cụm > các từ gần nhau > đủ mọi từ / đồng nghĩa > một phần
BOOST = {1: 2.0, 2: 1.5, 3: 1.3, 4: 1.3, 6: 1.0}
BIGRAM_ALPHA = 2.0  # cộng điểm theo tỉ lệ cặp âm tiết liền nhau của câu hỏi có trong đơn vị (chọn trên tập train Zalo)
COMMON_DF = 0.35  # từ có ở > 35% đơn vị không đưa vào OR (chỉ để nhanh; bỏ hết thì giữ lại)


def _or_terms(conn: sqlite3.Connection, tokens: list[str]) -> list[str]:
    """Âm tiết rời + cụm nhiều tiếng (tên Điều, từ điển) làm các vế OR."""
    words = list(dict.fromkeys(w for t in tokens for w in t.split()))
    n = conn.execute("SELECT MAX(id) FROM units").fetchone()[0] or 1  # nhanh hơn COUNT(*)
    kept = [w for w in words if _token_df(conn, w) <= COMMON_DF * n] or words
    phrases = [t for t in dict.fromkeys(tokens) if " " in t]
    return [x for x in (_fts_term(w) for w in kept) if x] + [fts_quote(p) for p in phrases]


def _words(text: str) -> list[str]:
    return [iy_norm_token(w) for w in re.findall(r"\w+", text or "")]


def _match_tier(words: list[str], pos: dict[str, list[int]], tokens: list[str],
                alts: list[list[str]]) -> int:
    """Mức khớp của một đơn vị, tính trên chữ đã lấy về (không truy vấn FTS thêm):
    1 cụm nguyên văn, 2 các từ trong cửa sổ ngắn, 3 đủ mọi từ, 4 đủ sau khi thay đồng nghĩa, 6 một phần."""
    def has(toks: list[str]) -> bool:
        return all(t.split()[0] in pos for t in toks)

    if has(tokens):
        phrase = " ".join(tokens)
        if f" {phrase} " in f" {' '.join(words)} ":
            return 1
        # cửa sổ nhỏ nhất chứa đủ mọi từ (NEAR 10)
        marks = sorted((p, k) for k, t in enumerate(tokens) for p in pos[t.split()[0]])
        need, have, lo, best = len(tokens), {}, 0, 10**9
        for hi, (p, k) in enumerate(marks):
            have[k] = have.get(k, 0) + 1
            while len(have) == need:
                best = min(best, p - marks[lo][0])
                kk = marks[lo][1]
                have[kk] -= 1
                if not have[kk]:
                    del have[kk]
                lo += 1
        return 2 if best <= len(tokens) + 10 else 3
    return 4 if any(has(a) for a in alts) else 6


def _run_cascade(
    conn: sqlite3.Connection,
    raw_query: str,
    tokens: list[str],
    *,
    branch: str,
    only_ids: list[int] | None = None,
    doc_ids: list[int] | None = None,
) -> tuple[list[int], int, str, dict[int, int], dict[int, float]]:
    """Một truy vấn BM25 OR lấy ứng viên, rồi nhân hệ số theo mức khớp (tính trên chữ ứng viên).
    Trả (ids theo độ liên quan, tầng tốt nhất, ghi chú, tầng từng id, điểm từng id).
    Tầng: 1 cụm, 2 gần nhau, 3 đủ từ, 4 đồng nghĩa, 6 một phần."""
    if not tokens:
        return [], 6, "empty", {}, {}
    accent = branch == "accent"
    terms = _or_terms(conn, tokens)
    alts: list[list[str]] = []
    for term, alt in load_synonyms(conn, accent=accent):
        for a, b in ((term, alt), (alt, term)):
            replaced = _replace_term(tokens, a, b)
            if replaced:
                alts.append(replaced)
                terms.append(fts_quote(b))
    terms = list(dict.fromkeys(terms))
    if not terms:
        return [], 6, "empty", {}, {}
    cand = scored_units(conn, " OR ".join(terms), branch=branch, only_ids=only_ids, doc_ids=doc_ids,
                        limit=CANDIDATES)
    if not cand:
        return [], 6, "", {}, {}
    col = "search_accent" if accent else "search_text"
    ctx_col = "context_accent" if accent else "context_search"
    rows = {r[0]: (r[1], r[2]) for r in conn.execute(
        f"SELECT id, {col}, {ctx_col} FROM units WHERE id IN (SELECT value FROM json_each(?))",
        (json.dumps([i for i, _ in cand]),),
    )}
    qw = _words(search_accent(raw_query) if accent else fold_search(raw_query))
    qbi = set(zip(qw, qw[1:]))
    norm_tokens = [" ".join(_words(x)) for x in tokens if _words(x)]
    norm_alts = [[" ".join(_words(x)) for x in a if _words(x)] for a in alts]
    tiers: dict[int, int] = {}
    final: dict[int, float] = {}
    for i, sc in cand:
        text, ctx = rows.get(i, ("", ""))
        words = _words(text or "")
        pos: dict[str, list[int]] = {}
        for k, w in enumerate(words):
            pos.setdefault(w, []).append(k)
        t = _match_tier(words, pos, norm_tokens, norm_alts)
        tiers[i] = t
        frac = 0.0
        if qbi:
            cw = _words(ctx or "")
            have = set(zip(words, words[1:])) | set(zip(cw, cw[1:]))
            frac = len(qbi & have) / len(qbi)
        final[i] = sc * BOOST[t] * (1 + BIGRAM_ALPHA * frac)
    ordered = sorted(final, key=lambda i: (final[i], i))
    note = "dong_nghia" if any(t == 4 for t in tiers.values()) else ""
    return ordered, min(tiers.values()), note, tiers, final


def _merge(score: dict[int, float], tiers: dict[int, int], more: dict[int, float],
           more_tiers: dict[int, int]) -> None:
    for i, sc in more.items():
        if i not in score:  # hit có dấu giữ điểm / tầng của nó
            score[i] = sc
            tiers[i] = more_tiers[i]


def _dense_only(ids: list[int], tiers: dict[int, int]) -> dict[int, int]:
    """Đơn vị chỉ có nhờ vector toàn kho (Advance, không chung chữ với câu hỏi): tầng 7."""
    tiers.update((i, 7) for i in ids if i not in tiers)
    return tiers


def _sure(gap: float | None) -> bool | None:
    return None if gap is None else gap >= crossrank.SURE_GAP


def _fts_cascade(
    conn: sqlite3.Connection,
    raw_query: str,
    *,
    doc_ids: list[int] | None = None,
    full_query: str | None = None,
) -> CascadeResult:
    if doc_ids is not None and not doc_ids:  # [] = không văn bản nào qua bộ lọc; scored_units/rerank hiểu [] là "không giới hạn"
        return CascadeResult([], 6, "")
    accented = query_has_accent(raw_query)
    dense_q = full_query or raw_query  # embedding cần nguyên câu hỏi: BM25 bỏ cụm "mức phạt", nghĩa của câu thì không
    tok_f = tokenize(fold_search(raw_query), indexes=vocab_indexes(conn, accent=False))

    if not accented:
        ids, tier, note, tiers, _ = _run_cascade(conn, raw_query, tok_f, branch="fold", doc_ids=doc_ids)
        ids = semantic.rerank(conn, dense_q, ids[:RETURN_TOP], doc_ids)
        ids, gap = crossrank.rerank_top(conn, dense_q, ids)
        return CascadeResult(ids, tier, note, tiers=_dense_only(ids, tiers), sure=_sure(gap))

    tok_a = tokenize(search_accent(raw_query), indexes=vocab_indexes(conn, accent=True))
    _, tier, note, tiers, score = _run_cascade(conn, raw_query, tok_a, branch="accent", doc_ids=doc_ids)
    fold_ids: set[int] = set()
    # Q6: gõ có dấu mà không đơn vị nào khớp đủ từ (vd. văn bản gõ không dấu) → thêm nhánh không dấu
    if not score or min(tiers.values()) > 3:
        _, ft, n2, ftiers, fscore = _run_cascade(conn, raw_query, tok_f, branch="fold", doc_ids=doc_ids)
        fold_ids = set(fscore) - set(score)
        _merge(score, tiers, fscore, ftiers)
        tier = min(tier, ft) if fscore else tier
        note = note or n2
    f2_ids: set[int] = set()
    ocr_ids = _ocr_unit_ids(conn)
    if ocr_ids:  # F2: OCR sai dấu — tìm không dấu trong trang OCR chưa đối chiếu
        _, _, _, f2_tiers, f2_score = _run_cascade(
            conn, raw_query, tok_f, branch="fold", only_ids=ocr_ids, doc_ids=doc_ids
        )
        f2_ids = set(f2_score)
        _merge(score, tiers, f2_score, f2_tiers)
    ids = semantic.rerank(conn, dense_q, sorted(score, key=lambda i: (score[i], i))[:RETURN_TOP], doc_ids)
    ids, gap = crossrank.rerank_top(conn, dense_q, ids)
    keep = set(ids)
    return CascadeResult(ids, tier, note, fold_ids=(fold_ids | f2_ids) & keep, f2_ids=f2_ids & keep,
                         tiers=_dense_only(ids, tiers), sure=_sure(gap))


def _tier0(ids: list[int], note: str) -> CascadeResult:
    return CascadeResult(ids, 0, note, tiers={i: 0 for i in ids})


def cascade_search(conn: sqlite3.Connection, raw_query: str, doc_ids: list[int] | None = None) -> CascadeResult:
    """`doc_ids`: chỉ tìm trong các văn bản này (bộ lọc áp trong truy vấn, không sau khi cắt top); None = cả kho.
    Hai nhánh tra thẳng (chỉ số hiệu, chỉ Điều) không đi qua đây: nơi gọi vẫn lọc bằng apply_doc_filters."""
    intent, q = split_intent(raw_query)
    result = _cascade(conn, q, full_query=raw_query, doc_ids=doc_ids)
    result.intent = intent
    return result


def _cascade(conn: sqlite3.Connection, raw_query: str, full_query: str | None = None,
             doc_ids: list[int] | None = None) -> CascadeResult:
    docs = _so_hieu_docs(conn, raw_query)
    dieu = find_dieu_so(raw_query)
    rest = citation_remainder(raw_query)

    if docs and not rest:
        return _tier0(lookup_so_hieu(conn, raw_query), "so_hieu")

    if docs and rest:
        scope = docs if doc_ids is None else [d for d in docs if d in set(doc_ids)]
        result = _fts_cascade(conn, rest, doc_ids=scope, full_query=full_query)
        if dieu:
            narrowed = _ids_on_dieu(conn, result.ids, dieu)
            if narrowed:
                result.ids = narrowed
            else:
                result = _tier0(_units_for_docs(conn, docs, dieu), "so_hieu")
        if not result.ids:
            return _tier0(lookup_so_hieu(conn, raw_query), "so_hieu")
        return result

    if dieu and not rest:
        return _tier0(lookup_dieu_all_docs(conn, dieu), "dieu")

    return _fts_cascade(conn, raw_query, doc_ids=doc_ids, full_query=full_query)


def _filter_sql(loai: str, co_quan: str, hieu_luc: str) -> tuple[str, list]:
    """Điều kiện lọc trên bảng documents (bí danh d), dùng chung cho lọc đơn vị và lọc văn bản. Ô cơ quan là danh sách
    chọn nên so khớp đúng giá trị lưu (LIKE làm 'CHÍNH PHỦ' kéo theo 'THỦ TƯỚNG CHÍNH PHỦ', và '%' thành ký tự đại diện)."""
    sql, params = "", []
    for col, v in (("loai", loai), ("co_quan", co_quan), ("hieu_luc", hieu_luc)):
        v = (v or "").strip()
        if v:
            sql += f" AND d.{col} = ?"
            params.append(v)
    return sql, params


def apply_doc_filters(
    conn: sqlite3.Connection,
    ids: list[int],
    *,
    loai: str = "",
    co_quan: str = "",
    hieu_luc: str = "",
) -> list[int]:
    where, params = _filter_sql(loai, co_quan, hieu_luc)
    if not ids or not where:
        return ids
    q = ",".join("?" * len(ids))
    rows = conn.execute(f"SELECT u.id FROM units u JOIN documents d ON d.id = u.doc_id WHERE u.id IN ({q}){where}", [*ids, *params])
    keep = {int(r["id"]) for r in rows}
    return [i for i in ids if i in keep]


def filtered_doc_ids(conn: sqlite3.Connection, *, loai: str = "", co_quan: str = "", hieu_luc: str = "") -> list[int] | None:
    """Mọi văn bản qua bộ lọc; None khi không đặt bộ lọc nào (khác danh sách rỗng: lọc mà không văn bản nào khớp)."""
    where, params = _filter_sql(loai, co_quan, hieu_luc)
    if not where:
        return None
    return [int(r[0]) for r in conn.execute(f"SELECT d.id FROM documents d WHERE 1{where}", params)]


def filter_docs(conn: sqlite3.Connection, doc_ids: list[int], *, loai: str = "", co_quan: str = "", hieu_luc: str = "") -> list[int]:
    """Như apply_doc_filters, cho danh sách văn bản."""
    where, params = _filter_sql(loai, co_quan, hieu_luc)
    if not doc_ids or not where:
        return doc_ids
    q = ",".join("?" * len(doc_ids))
    keep = {int(r[0]) for r in conn.execute(f"SELECT d.id FROM documents d WHERE d.id IN ({q}){where}", [*doc_ids, *params])}
    return [i for i in doc_ids if i in keep]
