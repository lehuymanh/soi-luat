"""Lắp thẻ lúc search — kế hoạch 4.3.1."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import PurePath

from soiluat import answer, semantic
from soiluat.fold import display_addr, dieu_path
from soiluat.labels import is_thi_hanh
from soiluat.search import DIEU_CAP

KIND_RANK1 = "Rủi ro (liên kết đã duyệt)"
KIND_RANK2 = "Rủi ro có chế tài (chưa có liên kết đã duyệt)"
KIND_RANK3 = "Rủi ro: nghĩa vụ / điều cấm / thời hạn / điều kiện, chưa rõ chế tài"
KIND_RANK4 = "Quy định liên quan"

RISK_NO_SANCTION = {"NGHIA_VU", "CAM", "THOI_HAN", "DIEU_KIEN"}
Q6_LABEL = "khớp khi bỏ dấu, có thể khác nghĩa"
Q5_LABEL = "nghĩa vụ của cơ quan khác"
OCR_LABEL = "Trích dẫn OCR chưa xác minh"
WORD_RE = re.compile(r"[0-9A-Za-zÀ-ỹĂăÂâÊêÔôƠơƯưĐđ]+", re.UNICODE)


@dataclass
class Card:
    kind: str
    title: str
    sample: str
    duty_text: str
    duty_addr: str
    sanction_text: str
    sanction_addr: str
    hieu_luc: str
    link_status: str
    ocr_unverified: bool
    unit_ids: list[int] = field(default_factory=list)
    synonym_note: str = ""
    page_from: int | None = None
    so_hieu: str = ""
    file_path: str = ""
    warnings: list[str] = field(default_factory=list)
    q5_other: bool = False
    q5_priority: bool = False
    q6_fold: bool = False
    grey: bool = False
    rank: int = 4
    page_to: int | None = None
    notes: list[str] = field(default_factory=list)  # ghi chú (ghi_chu) thuộc Điều, ≤ 3
    match_tier: int = 0  # 1–6 tầng khớp tốt nhất của nhóm; 7 = chỉ theo nghĩa (vector); 0 = tra số hiệu / không rõ
    intent: str = ""  # "" hoặc "muc_phat"
    relevance: int = 0  # thứ tự độ liên quan (BM25 + khớp cụm) của nhóm trong kết quả tìm, 0 = tốt nhất
    # P1 K1 (compact): một mục kết quả gọn
    doc_id: int | None = None
    path: str = ""  # đơn vị khớp nhất trong phần trích: địa chỉ của mục và chỗ "Mở tại đoạn này"
    head: str = ""  # tên Điều, không kèm số (số lấy từ path)
    snippet: str = ""
    also_in: list = field(default_factory=list)  # thẻ cùng nội dung ở văn bản khác ("Cũng có ở")
    more: list[str] = field(default_factory=list)  # path các đơn vị khác cùng Điều cũng khớp, tối đa 3


def _labels(conn: sqlite3.Connection, unit_id: int) -> set[str]:
    rows = conn.execute(
        "SELECT label FROM unit_labels WHERE unit_id = ?",
        (unit_id,),
    ).fetchall()
    return {r["label"] for r in rows}


def _labels_many(conn: sqlite3.Connection, ids: list[int]) -> set[str]:
    if not ids:
        return set()
    q = ",".join("?" * len(ids))
    rows = conn.execute(
        f"SELECT label FROM unit_labels WHERE unit_id IN ({q})",
        ids,
    ).fetchall()
    return {r["label"] for r in rows}


def _ocr_unverified(
    conn: sqlite3.Connection, page_from: int | None, page_to: int | None, doc_id: int
) -> bool:
    if page_from is None:
        return False
    pf, pt = page_from, page_to or page_from
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM pages WHERE doc_id = ? AND page_no BETWEEN ? AND ? "
        "AND ocr_status NOT IN ('khong_can','da_doi_chieu') "
        "AND extraction_method LIKE '%ocr%'",
        (doc_id, pf, pt),
    ).fetchone()
    return int(row["n"] or 0) > 0


def _unit(conn: sqlite3.Connection, uid: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM units WHERE id = ?", (uid,)).fetchone()


def _doc(conn: sqlite3.Connection, did: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM documents WHERE id = ?", (did,)).fetchone()


def _display_text(row: sqlite3.Row) -> str:
    return row["reviewed_text"] or row["raw_text"] or ""


def _addr(row: sqlite3.Row, so_hieu: str) -> str:
    return display_addr(so_hieu, row["path"])


def _ancestors(conn: sqlite3.Connection, u: sqlite3.Row) -> list[int]:
    out: list[int] = []
    pid = u["parent_id"]
    seen: set[int] = set()
    while pid and pid not in seen:
        seen.add(pid)
        out.append(pid)
        row = _unit(conn, pid)
        if row is None:
            break
        pid = row["parent_id"]
    return out


def _dieu_row(conn: sqlite3.Connection, u: sqlite3.Row) -> sqlite3.Row | None:
    cur = u
    while cur is not None:
        if cur["level"] == "dieu":
            return cur
        if not cur["parent_id"]:
            return None
        cur = _unit(conn, cur["parent_id"])
    return None


def _links_touching(conn: sqlite3.Connection, ids: list[int]) -> list[sqlite3.Row]:
    if not ids:
        return []
    q = ",".join("?" * len(ids))
    return conn.execute(
        f"SELECT * FROM links WHERE duty_unit IN ({q}) OR sanction_unit IN ({q})",
        list(ids) + list(ids),
    ).fetchall()


def _classify_group(
    conn: sqlite3.Connection,
    uids: list[int],
    labs: set[str],
    extra_ids: list[int],
) -> tuple[int, str, sqlite3.Row | None, sqlite3.Row | None]:
    look = list(dict.fromkeys(uids + extra_ids))
    links = _links_touching(conn, look)
    confirmed = [r for r in links if r["confirmed"] == 1]
    duty = _unit(conn, uids[0])
    sanc = None
    use = confirmed or links
    if use:
        row = use[0]
        if row["duty_unit"] in look:
            duty = _unit(conn, row["duty_unit"]) or duty
            sanc = _unit(conn, row["sanction_unit"])
        else:
            sanc = _unit(conn, row["sanction_unit"])
            duty = _unit(conn, row["duty_unit"]) or duty
    if confirmed:
        return 1, "da_xac_nhan", duty, sanc
    if "CHE_TAI" in labs or links:
        st = "may_goi_y" if links else "chua_noi"
        if "CHE_TAI" in labs and sanc is None:
            for uid in uids:
                if "CHE_TAI" in _labels(conn, uid):
                    sanc = _unit(conn, uid)
                    break
        if duty and "CHE_TAI" in _labels(conn, duty["id"]) and "NGHIA_VU" not in labs and "CAM" not in labs:
            if not any(x in labs for x in RISK_NO_SANCTION):
                duty = None
        return 2, st, duty, sanc
    if labs & RISK_NO_SANCTION:
        return 3, "", duty, None
    return 4, "", duty, None


def _sample(
    duty: sqlite3.Row | None,
    sanc: sqlite3.Row | None,
    rank: int,
    so_hieu: str,
    link_st: str,
) -> str:
    if rank == 4:
        return ""
    parts: list[str] = []
    if duty is not None and rank in (1, 2, 3):
        parts.append(
            "Không thực hiện / thực hiện hành vi bị cấm / không đáp ứng "
            f"điều kiện / không đúng thời hạn tại {_addr(duty, so_hieu)}"
        )
    if sanc is not None and rank in (1, 2):
        parts.append(f"có thể bị xử phạt theo {_addr(sanc, so_hieu)}")
        parts.append("[kiểm tra quy định về mức phạt của nghị định này]")
    sample = " ".join(parts)
    if sample and not sample.endswith("."):
        sample += "."
    if link_st == "may_goi_y":
        sample += " (máy gợi ý, chưa duyệt)"
    return sample.strip()


def _words(text: str) -> list[str]:
    return WORD_RE.findall(text or "")


def _phrase_hits(haystack: str, phrase: str, case_sensitive: bool) -> bool:
    hw = _words(haystack)
    pw = _words(phrase)
    if not pw:
        return False
    if not case_sensitive:
        hw_c = [w.lower() for w in hw]
        pw_c = [w.lower() for w in pw]
    else:
        hw_c, pw_c = hw, pw
    n = len(pw_c)
    for i in range(len(hw_c) - n + 1):
        if hw_c[i : i + n] == pw_c:
            return True
    return False


def _best_rule(
    rules: list[sqlite3.Row], haystack: str, kind: str
) -> sqlite3.Row | None:
    hits: list[sqlite3.Row] = []
    for r in rules:
        if r["kind"] != kind:
            continue
        phrase = r["phrase"]
        sensitive = len(_words(phrase)) < 2
        if _phrase_hits(haystack, phrase, sensitive):
            hits.append(r)
    if not hits:
        return None
    hits.sort(key=lambda r: (-len(_words(r["phrase"])), -len(r["phrase"])))
    return hits[0]


def _ha_uu_window(text: str, phrase: str, case_sensitive: bool) -> bool:
    words = _words(text)
    cmp_w = words if case_sensitive else [w.lower() for w in words]
    pw = _words(phrase)
    pw_c = pw if case_sensitive else [w.lower() for w in pw]
    n = len(pw_c)
    if n == 0:
        return False
    anchors: list[int] = []
    low = [w.lower() for w in words]
    for i, w in enumerate(low):
        if w == "phải":
            anchors.append(i)
        if i + 2 <= len(low) and low[i] == "có" and low[i + 1] == "trách" and low[i + 2] == "nhiệm":
            anchors.append(i)
    for a in anchors:
        start = max(0, a - 8)
        window = cmp_w[start:a]
        for i in range(len(window) - n + 1):
            if window[i : i + n] == pw_c:
                return True
    return False


def apply_q5(
    conn: sqlite3.Connection,
    primary: sqlite3.Row,
    dieu: sqlite3.Row | None,
) -> tuple[bool, bool]:
    rules = conn.execute(
        "SELECT phrase, kind FROM subject_rules WHERE approved = 1"
    ).fetchall()
    if not rules:
        return False, False
    unit_text = " ".join(
        x
        for x in (
            primary["title"] or "",
            primary["normalized_text"] or primary["raw_text"] or "",
            primary["context_accent"] or "",
        )
        if x
    )
    dieu_title = (dieu["title"] if dieu else "") or ""
    hay_parts = [unit_text, dieu_title]
    if dieu:
        dp = dieu["path"] or ""
        rows = conn.execute(
            "SELECT title, normalized_text, raw_text, context_accent "
            "FROM units WHERE doc_id = ? AND (path = ? OR path LIKE ?)",
            (int(primary["doc_id"]), dp, dp + ".%"),
        ).fetchall()
        for r in rows:
            hay_parts.extend(
                [
                    r["title"] or "",
                    r["normalized_text"] or r["raw_text"] or "",
                    r["context_accent"] or "",
                ]
            )
    hay = " ".join(x for x in hay_parts if x)
    uu = _best_rule(rules, hay, "uu_tien") is not None
    ha = False
    for r in rules:
        if r["kind"] != "ha_uu_tien":
            continue
        phrase = r["phrase"]
        sensitive = len(_words(phrase)) < 2
        blob = f"{primary['normalized_text'] or primary['raw_text'] or ''} {primary['context_accent'] or ''}"
        if _ha_uu_window(blob, phrase, sensitive):
            ha = True
            break
        prefix = "Trách nhiệm của "
        if dieu_title and _phrase_hits(
            dieu_title, prefix + phrase, case_sensitive=False
        ):
            ha = True
            break
    return uu, ha


def _order_group_uids(
    conn: sqlite3.Connection,
    uids: list[int],
    meta: dict[int, sqlite3.Row],
) -> list[int]:
    def sort_key(i: int) -> tuple:
        u = meta[i]
        lv = {"khoan": 0, "diem": 1, "dieu": 2}.get(u["level"], 3)
        text = (u["raw_text"] or "").strip()
        title = (u["title"] or "").strip()
        thin = 1 if (not text or text == title) else 0
        return (thin, lv, i)

    ordered = sorted(uids, key=sort_key)
    first = meta[ordered[0]]
    if first["level"] == "dieu":
        child = conn.execute(
            "SELECT * FROM units WHERE doc_id = ? AND path LIKE ? "
            "AND level IN ('khoan','diem') ORDER BY id LIMIT 1",
            (first["doc_id"], (first["path"] or "") + ".%"),
        ).fetchone()
        if child is not None:
            cid = int(child["id"])
            meta[cid] = child
            if cid not in ordered:
                ordered = [cid] + ordered
    return ordered


def _group_key(conn: sqlite3.Connection, u: sqlite3.Row) -> tuple[int, str]:
    # Ghi chú (H4, level ghi_chu) gom vào thẻ của đơn vị cha nếu có.
    if u["level"] == "ghi_chu" and u["parent_id"]:
        p = _unit(conn, u["parent_id"])
        if p is not None:
            return (int(u["doc_id"]), dieu_path(p["path"], p["level"]))
    return (int(u["doc_id"]), dieu_path(u["path"], u["level"]))


def _notes(
    conn: sqlite3.Connection, primary: sqlite3.Row, dieu: sqlite3.Row | None
) -> list[str]:
    """Text ghi chú (footnote, comment…) con của Điều trong thẻ, tối đa 3."""
    if dieu is not None:
        dp = dieu["path"] or ""
        # đi theo idx_units_path rồi idx_units_parent, không quét cả bảng
        rows = conn.execute(
            "SELECT g.reviewed_text, g.raw_text FROM units d "
            "JOIN units g ON g.parent_id = d.id "
            "WHERE d.doc_id = ? AND (d.path = ? OR d.path LIKE ?) AND g.level = 'ghi_chu' "
            "ORDER BY g.id LIMIT 3",
            (int(dieu["doc_id"]), dp, dp + ".%"),
        ).fetchall()
    else:
        anchor = primary["parent_id"] if primary["level"] == "ghi_chu" else primary["id"]
        rows = conn.execute(
            "SELECT reviewed_text, raw_text FROM units "
            "WHERE parent_id = ? AND level = 'ghi_chu' ORDER BY id LIMIT 3",
            (anchor,),
        ).fetchall()
    return [t for t in (_display_text(r) for r in rows) if t]


def assemble_cards(
    conn: sqlite3.Connection,
    hit_ids: list[int],
    synonym_note: str = "",
    fold_ids: set[int] | None = None,
    f2_ids: set[int] | None = None,
    tiers: dict[int, int] | None = None,
    intent: str = "",
) -> list[Card]:
    fold_ids = fold_ids or set()
    f2_ids = f2_ids or set()
    groups: dict[tuple[int, str], list[int]] = {}
    meta: dict[int, sqlite3.Row] = {}
    for uid in hit_ids:
        u = _unit(conn, uid)
        if u is None:
            continue
        meta[uid] = u
        groups.setdefault(_group_key(conn, u), []).append(uid)

    cards: list[Card] = []
    for pos, (_, hits) in enumerate(groups.items()):  # groups theo thứ tự hit_ids = thứ tự liên quan
        # Tầng của thẻ = tầng tốt nhất trong nhóm (4.3.1); không có tiers -> 0.
        tier = min(tiers.get(i, 6) for i in hits) if tiers is not None else 0
        uids = _order_group_uids(conn, hits, meta)
        primary = meta[uids[0]]
        extra = _ancestors(conn, primary)
        labs = _labels_many(conn, uids + extra)
        rank, link_st, duty, sanc = _classify_group(conn, uids, labs, extra)
        dieu = _dieu_row(conn, primary)
        title_src = dieu or primary
        if rank == 3 and is_thi_hanh(title_src["title"] or "", _display_text(primary)):
            rank = 4
        if all(meta[i]["level"] == "ghi_chu" for i in hits):
            rank, link_st, duty, sanc = 4, "", None, None
        doc = _doc(conn, primary["doc_id"])
        hieu = (doc["hieu_luc"] if doc else None) or "chua_ro"
        so = (doc["so_hieu"] if doc else None) or ""
        pages = [meta[i]["page_from"] for i in uids if meta[i]["page_from"] is not None]
        page_from = min(pages) if pages else primary["page_from"]
        page_to = primary["page_to"]
        ocr = _ocr_unverified(conn, page_from, page_to, primary["doc_id"])
        kind_label = {1: KIND_RANK1, 2: KIND_RANK2, 3: KIND_RANK3, 4: KIND_RANK4}[rank]
        warns: list[str] = []
        if hieu == "chua_ro":
            warns.append("Hiệu lực chưa rõ")
        if hieu == "het":
            warns.append("Văn bản hết hiệu lực")
        if ocr:
            warns.append(OCR_LABEL)
        if primary["level"] == "doan":
            warns.append("Không có cấu trúc Điều/Khoản")
        if primary["from_table"]:
            warns.append("Trang bảng — không lấy mức phạt tự động")
        q6 = any(i in fold_ids or i in f2_ids for i in uids)
        if q6:
            warns.append(Q6_LABEL)
        if any(i in f2_ids for i in uids) and OCR_LABEL not in warns:
            warns.append(OCR_LABEL)
            ocr = True
        uu, ha = apply_q5(conn, primary, dieu)
        if ha:
            warns.append(Q5_LABEL)
        title = (
            (dieu["title"] if dieu else None)
            or primary["title"]
            or (duty["title"] if duty else "")
            or pretty_fallback(primary, so)
        )
        if primary["level"] == "doan" and not so and doc and doc["file_path"]:
            # văn bản không số hiệu (ghi chú, tài liệu nội bộ): "trang 1 đoạn 1" không cho biết file nào
            title = f"{PurePath(doc['file_path'].split('#vb', 1)[0]).stem} · {title}"
        cards.append(
            Card(
                kind=kind_label,
                title=title or kind_label,
                sample=_sample(duty, sanc, rank, so, link_st),
                duty_text=_display_text(duty)
                if duty and rank in (1, 2, 3)
                else (_display_text(primary) if rank == 4 else ""),
                duty_addr=_addr(duty, so)
                if duty and rank in (1, 2, 3)
                else (_addr(primary, so) if rank == 4 else ""),
                sanction_text=_display_text(sanc) if sanc and rank in (1, 2) else "",
                sanction_addr=_addr(sanc, so) if sanc and rank in (1, 2) else "",
                hieu_luc=hieu,
                link_status=link_st,
                ocr_unverified=ocr,
                unit_ids=uids,
                synonym_note=synonym_note,
                page_from=primary["page_from"],
                so_hieu=so,
                file_path=(doc["file_path"] if doc else None) or "",
                warnings=warns,
                q5_other=ha,
                q5_priority=uu,
                q6_fold=q6,
                grey=(hieu == "het"),
                rank=rank,
                page_to=primary["page_to"],
                notes=_notes(conn, primary, dieu),
                match_tier=tier,
                intent=intent,
                relevance=pos,
                doc_id=int(primary["doc_id"]),
            )
        )
    # Tìm theo chữ (tiers có tầng > 0): độ liên quan trước; hạng liên kết / Q5 chỉ để phân thứ khi
    # hai thẻ liền kề cùng tầng khớp thì giữ thứ tự BM25. Tra số hiệu / Điều (tầng 0): tầng -> hạng -> Q5.
    # Hết hiệu lực luôn cuối (B13). Hỏi mức phạt (L17): thẻ có chế tài (hạng 1–2) lên trước.
    by_relevance = bool(tiers) and any(t > 0 for t in tiers.values())
    cards.sort(
        key=lambda c: (
            c.hieu_luc == "het",
            # chế tài chỉ được ưu tiên khi khớp đủ từ (tầng ≤ 3); khớp một phần thì chỉ theo độ liên quan
            intent == "muc_phat" and not (c.rank in (1, 2) and (c.match_tier <= 3 or not by_relevance)),
            c.relevance if by_relevance else c.match_tier,
            c.rank,
            0 if c.q5_priority else (2 if c.q5_other else 1),
            {"con": 0, "chua_ro": 1}.get(c.hieu_luc, 1),
        )
    )
    return cards


def pretty_fallback(row: sqlite3.Row, so_hieu: str) -> str:
    return display_addr(so_hieu, row["path"])


def summarize(cards: list[Card]) -> dict[str, int]:
    n = {"n1": 0, "n2": 0, "n3": 0, "n4": 0}
    for c in cards:
        if c.rank == 1:
            n["n1"] += 1
        elif c.rank == 2:
            n["n2"] += 1
        elif c.rank == 3:
            n["n3"] += 1
        else:
            n["n4"] += 1
    return n


_EMPTY_SIG = hashlib.sha1(b"").hexdigest()


def _in(conn: sqlite3.Connection, sql: str, ids: list) -> list[sqlite3.Row]:
    return conn.execute(sql.format("SELECT value FROM json_each(?)"), (json.dumps(ids),)).fetchall()


def compact(conn: sqlite3.Connection, items: list[Card], query: str, limit: int = 25, cap: int = DIEU_CAP) -> list[Card]:
    """Kết quả gọn (P1 K1): mỗi mục là một (văn bản, Điều); Điều cùng nội dung ở văn bản khác gộp vào mục đầu
    ("Cũng có ở"), đại diện là bản còn hiệu lực rồi bản ban hành mới hơn; `limit` mục đầu có phần trích và địa chỉ."""
    items = items[:cap]
    roots = semantic.root_ids(conn, [c.unit_ids[0] for c in items if c.unit_ids])
    groups: list[list[Card]] = []
    at: dict[tuple, int] = {}
    root_of: dict[int, int | None] = {}
    for c in items:
        u0 = c.unit_ids[0] if c.unit_ids else None
        rid = roots.get(u0)  # ghi chú có cha không có gốc: không băm, không trích
        root_of[id(c)] = rid
        if rid is None:
            key = ("u", u0, id(c))
        else:
            sig = answer.content_sig(conn, rid)
            key = ("r", rid) if sig == _EMPTY_SIG else ("s", sig)  # thân rỗng: mọi Điều rỗng cùng một khoá
        g = at.get(key)
        if g is not None and all(x.doc_id != c.doc_id for x in groups[g]):  # chỉ gộp giữa các văn bản
            groups[g].append(c)
            continue
        at.setdefault(key, len(groups))
        groups.append([c])
    dates = {r[0]: r[1] or "" for r in _in(conn, "SELECT id, ngay_ban_hanh FROM documents WHERE id IN ({})",
                                            list({c.doc_id for c in items}))}
    out = []
    for g in groups:
        newest = sorted(g, key=lambda c: dates.get(c.doc_id, ""), reverse=True)  # sắp ổn định: cùng ngày giữ thứ tự
        rep = min(newest, key=lambda c: c.hieu_luc != "con")
        rep.also_in = [c for c in g if c is not rep]
        out.append(rep)
    shown = out[:limit]
    units = {r[0]: r for r in _in(conn, "SELECT id, path, level FROM units WHERE id IN ({})",
                                  [i for c in shown for i in c.unit_ids])}
    for c in shown:
        rid = root_of[id(c)]
        if rid is None:
            c.snippet = c.duty_text
        else:
            head, c.snippet, c.path = answer.snippet(conn, rid, query)
            c.head = re.sub(r"^Điều \w+\.\s*", "", head)
        if not c.path and c.unit_ids and c.unit_ids[0] in units:
            c.path = units[c.unit_ids[0]]["path"]
        c.more = [units[i]["path"] for i in c.unit_ids
                  if i in units and units[i]["level"] != "dieu" and units[i]["path"] != c.path][:3]
    return out


def doc_groups(items: list) -> list[list]:
    """Mục theo văn bản, giữ thứ tự xuất hiện đầu (không dùng groupby của Jinja: nó sắp theo khoá, phá thứ hạng)."""
    out: list[list] = []
    at: dict = {}
    for c in items:
        k = getattr(c, "doc_id", None)
        k = id(c) if k is None else k
        if k not in at:
            at[k] = len(out)
            out.append([])
        out[at[k]].append(c)
    return out
