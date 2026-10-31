#!/usr/bin/env python
"""Đo từng phần của parser trên 21 văn bản thật, không qua DB (kế hoạch P1, N3): Điều tách được so với số
Điều thật, khối nơi nhận và chữ ký lọt vào đơn vị, Phụ lục bị bỏ hoặc bị nuốt, số trang lọt vào đơn vị,
Chương/Mục, mở đầu, bảng, đơn vị phình to, thứ tự khoản/điểm, câu bằng chứng còn nằm trong một đơn vị.

Đọc pages.reviewed_text/raw_text từ bản sao kho (chỉ đọc), gọi parse_pages như rebuild_document. Dùng làm cổng
hồi quy cho mọi lần sửa parser: chạy trước và sau, so bảng TỔNG.

python -I bench/van-ban-that/cau_truc_chi_tiet.py --db <realdocs>/data/soiluat.db [--out audit.json]
Số Điều thật: dieu_that_chi_tiet.json (đối chiếu tay trên chữ OCR và PDF).
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sqlite3
import sys
import time
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ap = argparse.ArgumentParser()
ap.add_argument("--db", required=True)
ap.add_argument("--src", default=str(REPO / "src"))
ap.add_argument("--truth", default=str(HERE / "dieu_that_chi_tiet.json"))
ap.add_argument("--queries", default=str(HERE / "queries.json"))
ap.add_argument("--manifest", default=str(HERE / "manifest.json"))
ap.add_argument("--out", default="cau_truc_chi_tiet.json")
ap.add_argument("--examples", type=int, default=6)
args = ap.parse_args()
sys.path.insert(0, args.src)

from soiluat.fold import fold_search, normalize_display  # noqa: E402
from soiluat.parse import CHUONG_MUC, TABLE_ROW, parse_pages  # noqa: E402
from soiluat.rebuild import page_text  # noqa: E402

TRUTH = json.loads(Path(args.truth).read_text()) if Path(args.truth).exists() else {}
QUERIES = json.loads(Path(args.queries).read_text())
MANIFEST = {m["file"]: m for m in json.loads(Path(args.manifest).read_text())}

# ---- mẫu nhận dạng -------------------------------------------------------------------------------
TERM = ".;:"                                   # dấu kết thúc đơn vị hợp lệ
CLOSERS = "”\"')]’ "                           # ngoặc đóng/khoảng trắng bỏ qua khi xét dấu cuối
PAGE_NO = re.compile(r"^(?:[-–—~]\s*)?\d{1,3}(?:\s*[-–—~])?$")   # dòng chỉ có số trang: "3", "- 3 -"
NOI_NHAN = re.compile(r"^\W{0,3}n[oơ]i\s*nh[aậ]n\b", re.I)
SIGN_LINE = re.compile(
    r"^(?:(?:KT|TM|TUQ|Q)\.\s*\S.*|CHỦ TỊCH QUỐC HỘI|CHỦ TỊCH NƯỚC|BỘ TRƯỞNG|THỦ TƯỚNG|PHÓ THỦ TƯỚNG|THỨ TRƯỞNG"
    r"|CHỦ TỊCH|TỔNG GIÁM ĐỐC|GIÁM ĐỐC)\s*$|^\W{0,3}Lưu\s*:|^\W{0,3}[-~–]\s*(?:Ban Bí thư|Thủ tướng|Văn phòng|Tòa án|Viện kiểm sát|Công báo|Cổng)",
    re.I,
)
SIGN_LINE_UPPER = re.compile(r"^(?:KT\.|TM\.|TUQ\.|Q\.)|^(?:CHỦ TỊCH|BỘ TRƯỞNG|THỦ TƯỚNG|PHÓ THỦ TƯỚNG|THỨ TRƯỞNG)\b")
# tiêu đề phụ lục: chỉ "Phụ lục" + số La Mã/số/chữ (có thể kèm ngoặc), hoặc "Mẫu số n"; không nhận câu "Phụ lục IV của Luật…"
PHU_LUC = re.compile(r"^\W{0,3}(?:PHỤ\s+LỤC|Phụ\s+lục)(?:\s+[IVXLC\d]+[A-Z]?)?\s*(?:\(.*\))?\W*$|^\W{0,3}(?:Mẫu số|MẪU SỐ)\s*\d+[A-Za-z]?\b")
# dòng đầu Chương/Mục/Phần kể cả OCR hỏng: "Chương", "Chương HH", "` Chương II", "CHƯƠNG 3"; chỉ nhận dòng ngắn
CHUONG_LOOSE = re.compile(r"^\W{0,3}(?:Ch[uư][oơ]ng|CH[UƯ][OƠ]NG|Mục|MỤC|Phần|PHẦN)\s*[IVXLCDMHhlI\d]{0,6}\W{0,2}$")
RECIPIENT = re.compile(r"^\W{0,3}[-~–—]\s*(?:Ban Bí thư|Thủ tướng|Các [Bb]ộ|Văn phòng|Hội đồng|HĐND|Tòa án|Viện kiểm sát|Kiểm toán|Ủy ban|Công báo|Cổng|Lưu)")
ADOPT_START = re.compile(r"^\W{0,3}\S{2,8}\s+này\s+(?:đã\s+)?được\s+Quốc\s+hội", re.I)
DIEU_HEAD = re.compile(r"^\W{0,3}Điều\s+\d", re.I)
ADOPT = re.compile(r"được\s+Quốc\s+hội\s+nước\s+Cộng\s+hòa|[Kk][ỳỹy]\)?\s+họp.*thông\s+qua|thông\s+qua\s+ngày", re.I)
SIGNER_NAME = re.compile(r"^\W{0,3}(?:Trần Thanh Mẫn|Phạm Thị Thanh Trà|Phạm Ngọc Thưởng)\b|QU\S{1,2}C\s*H\S{1,2}I\W*$")
QUOTED_DIEU = re.compile(r"^[“\"]\s*Điều\s+\d+[a-z]?\s*[.:]")
INLINE_MARK = re.compile(r"(?<=[;:.])\s+(?:[a-zđ]\)|\d{1,2}[.)])\s+(?=[A-ZĐa-zà-ỹ])")
INLINE_DIEU = re.compile(r"(?<=[.;:])\s+Điều\s+\d+[a-z]?\.\s+[A-ZĐ]")
ALPHA_TOKEN = re.compile(r"[A-Za-zÀ-ỹĐđ]+")
GLUE_CAMEL = re.compile(r"[a-zà-ỹ]{2}[A-ZĐ][a-zà-ỹ]{2}")
DIEM_ORDER = "abcdđeghiklmnopqrstuvxy"        # thứ tự chữ điểm trong văn bản pháp luật Việt Nam
NGAY = re.compile(r"ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})", re.I)
HIEU_LUC = re.compile(r"có hiệu lực(?: thi hành)?\s*(?:kể\s+)?từ\s+ngày\s+(\d{1,2})[/ ](?:tháng\s+)?(\d{1,2})[/ ](?:năm\s+)?(\d{4})", re.I)


def ex(lst: list, item, k=args.examples):
    if len(lst) < k:
        lst.append(item)


def clip(s: str, n=70) -> str:
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1] + "…"


def tail(s: str, n=45) -> str:
    s = " ".join(s.split())
    return s if len(s) <= n else "…" + s[-n:]


def covered_lines(L: list[str], units) -> set[int]:
    """Chỉ số dòng gốc đã vào một đơn vị: lần theo thứ tự dòng của text đơn vị (dòng đầu = line_from)."""
    cov: set[int] = set()
    for u in units:
        tl = u.text.split("\n")
        j = u.line_from
        cov.add(j)
        if u.level == "dieu":  # tên Điều ngắt dòng: parser nối các dòng sau vào title (một dòng trong text)
            k = j + 1
            while k < min(len(L), j + 6):
                t_ = L[k].strip()
                if len(t_) >= 6 and (" " + t_) in tl[0]:
                    cov.add(k)
                    j = k
                elif t_:
                    break
                k += 1
        for t in tl[1:]:
            j += 1
            while j < len(L) and L[j].strip() != t.strip():
                j += 1
            if j >= len(L):
                break
            cov.add(j)
    return cov


def unit_lines_index(L, units):
    """unit -> danh sách chỉ số dòng gốc (cùng cách lần như covered_lines)."""
    out = {}
    for u in units:
        idx = [u.line_from]
        j = u.line_from
        if u.level == "dieu":
            k = j + 1
            while k < min(len(L), j + 6):
                t_ = L[k].strip()
                if len(t_) >= 6 and (" " + t_) in u.text.split("\n")[0]:
                    idx.append(k)
                    j = k
                elif t_:
                    break
                k += 1
        for t in u.text.split("\n")[1:]:
            j += 1
            while j < len(L) and L[j].strip() != t.strip():
                j += 1
            if j >= len(L):
                break
            idx.append(j)
        out[id(u)] = idx
    return out


def ends_open(text: str) -> bool:
    """Đơn vị không kết thúc bằng . ; : (bỏ ngoặc đóng ở cuối)."""
    t = text.rstrip().rstrip(CLOSERS)
    return bool(t) and t[-1] not in TERM


# ---- đo từng văn bản -----------------------------------------------------------------------------
db = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
db.row_factory = sqlite3.Row
by_file = {Path(d["file_path"]).name: d["id"] for d in db.execute("SELECT id, file_path FROM documents")}

R: dict[int, dict] = {}
EXAMPLES: dict[str, list] = collections.defaultdict(list)
TOT = collections.Counter()

for d in db.execute("SELECT * FROM documents ORDER BY id"):
    did = d["id"]
    pages = db.execute("SELECT * FROM pages WHERE doc_id=? ORDER BY page_no", (did,)).fetchall()
    views = [SimpleNamespace(page_no=p["page_no"], text=page_text(p)) for p in pages]
    t0 = time.perf_counter()
    res = parse_pages(views, so_hieu=d["so_hieu"])
    parse_ms = (time.perf_counter() - t0) * 1000
    L = normalize_display("\n\n".join(v.text for v in views)).replace("\r\n", "\n").split("\n")
    body = [u for u in res.units if u.level != "ghi_chu"]
    cov = covered_lines(L, body)
    ulines = unit_lines_index(L, body)
    ne = [i for i, l in enumerate(L) if l.strip()]
    dropped = [i for i in ne if i not in cov]
    dieu = [u for u in body if u.level == "dieu"]
    first_dieu = min((u.line_from for u in dieu), default=len(L))
    last_dieu = max((u.line_from for u in dieu), default=0)
    m = collections.defaultdict(int)
    tag = f"{did}:{d['so_hieu']}"
    m["parse_ms"] = round(parse_ms, 1)
    m["pages"], m["lines"], m["chars"] = len(pages), len(ne), sum(len(L[i]) for i in ne)
    m["units"] = len(body)
    for lv in ("dieu", "khoan", "diem", "doan"):
        m[f"n_{lv}"] = sum(1 for u in body if u.level == lv)

    # 1. số Điều tách được so với số Điều thật ------------------------------------------------------
    nums = [(int(re.match(r"D(\d+)", u.addr_part).group(1)), u) for u in dieu]
    parsed_nums = [n for n, _ in nums]
    tr = TRUTH.get(str(did), {})
    last_true = tr.get("last", max(parsed_nums, default=0))
    extra_lines = set(tr.get("extra_line_from", []))
    true_set = set(range(1, last_true + 1)) | set(tr.get("also_true", []))
    got_true = {n for n, u in nums if u.line_from not in extra_lines and n in true_set}
    missing = sorted(true_set - got_true)
    extra = [u for n, u in nums if u.line_from in extra_lines or n not in true_set]
    dup = [u for _, u in nums if "~" in u.addr_part]
    m["dieu_true"], m["dieu_parsed"] = len(true_set), len(dieu)
    m["dieu_tp"], m["dieu_missing"], m["dieu_extra"] = len(got_true), len(missing), len(extra)
    m["dieu_dup_suffix"] = len(dup)
    m["dieu_lowconf"] = sum(1 for u in dieu if u.confidence < 0.9)
    m["dieu_missing_list"] = missing
    owner_first_missing = 10**9
    if missing:
        ex(EXAMPLES["dieu_missing"], f"{tag}: thiếu Điều {missing} ({tr.get('note', '')})")

    # 2. đơn vị kết thúc giữa câu ------------------------------------------------------------------
    flat = [u for u in body if u.level in ("khoan", "diem", "doan") or (u.level == "dieu" and "\n" in u.text)]
    mid_strict = mid_loose = 0
    for k, u in enumerate(body[:-1]):
        if u.level not in ("khoan", "diem", "doan") and not (u.level == "dieu" and "\n" in u.text):
            continue
        nxt = body[k + 1]
        if not ends_open(u.text):
            continue
        mid_loose += 1
        last_ln = u.text.split("\n")[-1].strip()
        oc = "so_trang" if PAGE_NO.match(last_ln) else ("tieu_de_hoa" if last_ln.isupper() and len(last_ln) >= 8 else "khac")
        m[f"open_{oc}"] += 1
        if oc == "khac":
            ex(EXAMPLES["open_other"], f"{tag} {u.addr_part}: «{tail(u.text, 50)}» → {nxt.addr_part}", 25)
        if nxt.text[:1].islower():
            mid_strict += 1
            cause = "so_trang" if PAGE_NO.match(u.text.split("\n")[-1].strip()) else "khac"
            m[f"mid_cause_{cause}"] += 1
            ex(EXAMPLES["mid_sentence"], f"{tag} {u.addr_part}: «{tail(u.text)}» ⏎ {nxt.addr_part}: «{clip(nxt.text, 40)}»")
    m["unit_flat"], m["mid_strict"], m["mid_open_any"] = len(flat), mid_strict, mid_loose

    # 3. dòng sau điểm cuối cùng bị nuốt vào điểm --------------------------------------------------
    kids = collections.defaultdict(list)
    for u in body:
        if u.parent_addr:
            kids[u.parent_addr].append(u)
    swallow = swallow_q = 0
    pl_first_ = next((i for i in ne if i > last_dieu and PHU_LUC.match(L[i].strip())), None)
    for kh in (u for u in body if u.level == "khoan"):
        dm = [c for c in kids.get(kh.addr_part, []) if c.level == "diem"]
        if not dm:
            continue
        last = dm[-1]
        idx = ulines[id(last)]
        for a in range(1, len(idx)):
            prev_t, cur_t = L[idx[a - 1]].strip(), L[idx[a]].strip()
            if re.search(r"\.\W{0,4}[A-Za-z]?\W{0,3}$", prev_t) and cur_t[:1].isupper() and not PAGE_NO.match(cur_t) \
                    and not (ADOPT.search(cur_t) or SIGNER_NAME.search(cur_t) or NOI_NHAN.match(cur_t) or DIEU_HEAD.match(cur_t)) \
                    and idx[a] < (pl_first_ if pl_first_ is not None else len(L)):
                before = "\n".join(L[x] for x in idx[:a])
                if before.count("“") > before.count("”"):  # đang ở trong đoạn trích “…” của luật sửa đổi: không phải câu kết khoản
                    swallow_q += 1
                    ex(EXAMPLES["tail_swallow_in_quote"], f"{tag} {last.addr_part}: «{clip(cur_t, 60)}»", 40)
                else:
                    swallow += 1
                    ex(EXAMPLES["tail_swallow"], f"{tag} {last.addr_part}: «{tail(prev_t, 35)}» ⏎ «{clip(cur_t, 60)}»", 40)
                break
    m["khoan_with_diem"] = sum(1 for kh in body if kh.level == "khoan" and any(c.level == "diem" for c in kids.get(kh.addr_part, [])))
    m["tail_swallow"], m["tail_swallow_in_quote"] = swallow, swallow_q

    # 4. bảng ---------------------------------------------------------------------------------------
    trows = [i for i in ne if TABLE_ROW.match(L[i].strip())]
    pipe_raw = [i for i in ne if "|" in L[i] and not TABLE_ROW.match(L[i].strip())]
    m["table_rows"] = len(trows)
    m["table_rows_dropped"] = sum(1 for i in trows if i not in cov)
    m["table_rows_in_units"] = m["table_rows"] - m["table_rows_dropped"]
    m["pipe_rows_ocr_raw"] = len(pipe_raw)
    m["pipe_rows_ocr_raw_dropped"] = sum(1 for i in pipe_raw if i not in cov)
    m["units_from_table"] = sum(1 for u in body if u.from_table)
    # bảng = dãy dòng bảng liên tiếp (cho phép dòng trống/số trang xen giữa); đếm bảng bị chia cho > 1 đơn vị
    owner = {}
    for u in body:
        for i in ulines[id(u)]:
            owner[i] = u.addr_part
    owner_of = owner.get
    tables, cur = [], []
    for i in trows:
        if cur and all((not L[x].strip()) or PAGE_NO.match(L[x].strip()) for x in range(cur[-1] + 1, i)):
            cur.append(i)
        else:
            if cur:
                tables.append(cur)
            cur = [i]
    if cur:
        tables.append(cur)
    def region_of(i):
        if i < first_dieu:
            return "dau"
        if pl_start_t is not None and i >= pl_start_t:
            return "phu_luc"
        if sign_start_t is not None and i >= sign_start_t:
            return "chu_ky"
        return "than"
    pl_start_t = next((i for i in ne if i > last_dieu and PHU_LUC.match(L[i].strip())), None)
    sign_start_t = next((i for i in ne if i > last_dieu and NOI_NHAN.match(L[i].strip())), None)
    for i in trows:
        rg = region_of(i)
        m[f"table_rows_{rg}"] += 1
        if i not in cov:
            m[f"table_rows_{rg}_dropped"] += 1
    m["tables"] = len(tables)
    m["tables_split"] = sum(1 for t in tables if len({owner.get(i) for i in t if i in owner}) > 1)
    m["tables_dropped_all"] = sum(1 for t in tables if all(i not in cov for i in t))
    for t in tables:
        if all(i not in cov for i in t):
            ex(EXAMPLES["table_dropped"], f"{tag}: bảng {len(t)} dòng bị bỏ, đầu: «{clip(L[t[0]], 60)}»")

    # 5. dòng OCR dính --------------------------------------------------------------------------------
    # (a) hai mốc cấu trúc trên một dòng; (b) tên Điều dính đuôi câu; (c) từ dính/rác trong thân văn bản;
    # (d) hai cột bị gộp một dòng ("Nơi nhận: KT. BỘ TRƯỞNG") làm hỏng điều kiện vào khối chữ ký
    glue_inline = glue_dieu = glue_word = glue_camel = glue_word_pl = 0
    pl_first = next((i for i in ne if i > last_dieu and PHU_LUC.match(L[i].strip())), len(L))
    for i in ne:
        s_ = L[i].strip()
        mk = INLINE_MARK.search(s_)
        if mk and mk.start() > 12:
            glue_inline += 1
            ex(EXAMPLES["glue_inline_marker"], f"{tag} L{i}: «{clip(s_[max(0, mk.start() - 25): mk.end() + 25], 80)}»")
        mk = INLINE_DIEU.search(s_)
        if mk:
            glue_dieu += 1
            ex(EXAMPLES["glue_dieu_head"], f"{tag} L{i}: «{clip(s_[max(0, mk.start() - 25): mk.end() + 25], 80)}»")
        for t in ALPHA_TOKEN.findall(s_):
            if (len(t) >= 14 and not t.isupper()) or GLUE_CAMEL.search(t):
                if i >= pl_first:
                    glue_word_pl += 1
                else:
                    glue_word += 1
                    ex(EXAMPLES["glue_token_body"], f"{tag} L{i}: «{t}»")
    m["glue_inline_marker"], m["glue_dieu_head"] = glue_inline, glue_dieu
    m["glue_token_body"], m["glue_token_phu_luc"] = glue_word, glue_word_pl
    for i in ne:
        s_ = L[i].strip()
        if NOI_NHAN.match(s_) and len(s_) >= 20:
            ex(EXAMPLES["glue_columns"], f"{tag} L{i}: «{clip(s_, 70)}»", 20)

    # 7a. phụ lục (tìm trước để cắt vùng chữ ký) ------------------------------------------------------
    pl_idx = [i for i in ne if i > last_dieu and PHU_LUC.match(L[i].strip())]
    pl_start = pl_idx[0] if pl_idx else None

    # 6. khối nơi nhận / chữ ký / câu "Luật này được Quốc hội … thông qua" lọt vào đơn vị -------------
    cand = [i for i in ne if i > last_dieu and (NOI_NHAN.match(L[i].strip()) or ADOPT_START.match(L[i].strip()))]
    # "Nơi nhận" mất chữ do OCR: lấy dãy ≥3 dòng gạch đầu dòng kiểu "- Ban Bí thư…", lùi một dòng nếu là "TM./KT. …"
    bul = [i for i in ne if i > last_dieu and RECIPIENT.match(L[i].strip())]
    for k0 in range(len(bul) - 2):
        if bul[k0 + 2] - bul[k0] <= 6:
            j0 = bul[k0]
            prev_ne = [x for x in ne if x < j0][-1:]
            cand.append(prev_ne[0] if prev_ne and re.search(r"TM\.|KT\.|CH[IÍ]NH PH", L[prev_ne[0]]) else j0)
            break
    sign_start = min(cand) if cand else None
    luu = next((i for i in ne if sign_start is not None and i >= sign_start and re.match(r"^\W{0,3}L[uư]u\s*:", L[i].strip())), None)
    sign_end = (luu + 1) if luu is not None else (pl_start if pl_start is not None else len(L))
    sign_region = [i for i in ne if sign_start is not None and sign_start <= i < sign_end]
    m["sign_block_lines"] = len(sign_region)
    m["sign_leak_lines"] = sum(1 for i in sign_region if i in cov)           # đã vào đơn vị (rò vào Điều/khoản/điểm cuối)
    m["sign_cut_lines"] = len(sign_region) - m["sign_leak_lines"]           # bị cắt đúng (in_sign)
    m["sign_leak_units"] = len({owner_of(i) for i in sign_region if i in cov} - {None}) if sign_region else 0
    m["sign_block_kind"] = (
        "khong_co" if sign_start is None else (
            "noi_nhan" if NOI_NHAN.match(L[sign_start].strip())
            else ("cau_thong_qua" if ADOPT_START.match(L[sign_start].strip()) else "mat_chu_noi_nhan"))
    )
    if m["sign_leak_lines"]:
        ex(EXAMPLES["sign_leak"], f"{tag}: {m['sign_leak_lines']}/{len(sign_region)} dòng chữ ký lọt vào {owner_of(sign_start)}, đầu «{clip(L[sign_start], 60)}»", 30)
    nn_lines = [i for i in ne if NOI_NHAN.match(L[i].strip())]
    m["noi_nhan_lines"] = len(nn_lines)
    m["noi_nhan_not_triggered"] = sum(1 for i in nn_lines if len(L[i].strip()) >= 20)  # parser chỉ vào in_sign khi dòng < 20 ký tự

    # 7. phần mở đầu / phụ lục -----------------------------------------------------------------------
    pre_dropped = [i for i in dropped if i < first_dieu]
    orphans = [u for u in body if u.level == "doan"]
    pre_total = [i for i in ne if i < first_dieu]
    cc = [i for i in pre_total if fold_search(L[i]).startswith("can cu")]
    m["preamble_lines"], m["preamble_dropped"] = len(pre_total), len(pre_dropped)
    m["preamble_can_cu_lines"] = len(cc)
    m["preamble_can_cu_dropped"] = sum(1 for i in cc if i not in cov)
    m["preamble_orphan_doan_units"] = len(orphans)
    m["preamble_orphan_chars"] = sum(len(u.text) for u in orphans)
    for u in orphans:
        ex(EXAMPLES["preamble_orphan"], f"{tag} {u.addr_part}: {len(u.text)} ký tự, đầu «{clip(u.text, 70)}»")
    m["has_phu_luc"] = int(pl_start is not None)
    if pl_start is not None:
        reg = [i for i in ne if i >= pl_start]
        m["phu_luc_lines"] = len(reg)
        m["phu_luc_chars"] = sum(len(L[i]) for i in reg)
        m["phu_luc_dropped_lines"] = sum(1 for i in reg if i not in cov)
        m["phu_luc_dropped_chars"] = sum(len(L[i]) for i in reg if i not in cov)
        # dòng Phụ lục nằm trong đơn vị Phụ lục riêng (PLk.paraN, N3 B2) là đúng; "nuốt" chỉ tính khi nằm trong Điều/khoản/điểm
        own_pl = [i for i in reg if i in cov and str(owner_of(i) or "").startswith("PL")]
        m["phu_luc_own_lines"] = len(own_pl)
        m["phu_luc_absorbed_lines"] = m["phu_luc_lines"] - m["phu_luc_dropped_lines"] - len(own_pl)
        m["phu_luc_absorbed_chars"] = m["phu_luc_chars"] - m["phu_luc_dropped_chars"] - sum(len(L[i]) for i in own_pl)
        ex(EXAMPLES["phu_luc"], f"{tag}: Phụ lục từ L{pl_start} «{clip(L[pl_start], 50)}»: {len(reg)} dòng/{m['phu_luc_chars']} ký tự, bỏ {m['phu_luc_dropped_lines']} dòng, nuốt vào {owner_of(reg[-1])} {m['phu_luc_absorbed_lines']} dòng", 30)
    after = [i for i in dropped if i >= first_dieu and (sign_start is None or i < sign_start) and (pl_start is None or i < pl_start)]
    m["dropped_in_body"] = len(after)       # dòng thân văn bản bị bỏ (không phải mở đầu/chữ ký/phụ lục): nội dung mất thật
    for i in after:
        ex(EXAMPLES["dropped_in_body"], f"{tag} L{i}: «{clip(L[i], 70)}»", 30)

    # 8. Chương / Mục / Phần ----------------------------------------------------------------------------
    rec = [i for i in ne if CHUONG_MUC.match(L[i].strip()) and len(L[i].strip()) <= 80]
    fp = [i for i in ne if CHUONG_MUC.match(L[i].strip()) and len(L[i].strip()) > 80]
    garb = [i for i in ne if CHUONG_LOOSE.match(L[i].strip()) and i not in rec]
    m["chuong_recognized"], m["chuong_garbled"], m["chuong_false_pos"] = len(rec), len(garb), len(fp)
    t_drop = t_abs = h_abs = 0
    for h in rec + garb:
        if h in cov:
            h_abs += 1
        j = h + 1
        while j < len(L) and (not L[j].strip() or (L[j].strip().isupper() and not DIEU_HEAD.match(L[j].strip()) and j - h <= 4)):
            if L[j].strip():
                if j in cov:
                    t_abs += 1
                    ex(EXAMPLES["chuong_title_absorbed"], f"{tag} L{h}: «{clip(L[h], 20)}» ⏎ «{clip(L[j], 50)}» vào {owner.get(j)}", 20)
                else:
                    t_drop += 1
            j += 1
    fdrop = 0
    for h in rec:
        pv = [x for x in ne if x < h][-1:]
        if pv and h not in cov:
            ptxt = L[pv[0]].strip()
            if ptxt.rstrip(CLOSERS)[-1:] not in TERM and not PAGE_NO.match(ptxt) and not ptxt.isupper() and not CHUONG_MUC.match(ptxt):
                fdrop += 1
                ex(EXAMPLES["chuong_false_drop"], f"{tag} L{h}: «{tail(ptxt, 30)}» ⏎ «{clip(L[h], 60)}» (dòng nội dung bị coi là đầu Chương/Mục và bỏ)")
    m["chuong_false_drop"] = fdrop
    m["chuong_head_absorbed"], m["chuong_title_lines_absorbed"], m["chuong_title_lines_dropped"] = h_abs, t_abs, t_drop
    for h in garb:
        ex(EXAMPLES["chuong_garbled"], f"{tag} L{h}: «{clip(L[h], 50)}»", 20)
    # 9. kích thước đơn vị ------------------------------------------------------------------------------
    sizes = sorted(len(u.text) for u in body if u.level in ("khoan", "diem", "dieu"))
    m["unit_max_chars"] = max((len(u.text) for u in body), default=0)
    m["units_gt_2000"] = sum(1 for u in body if len(u.text) > 2000)
    m["units_gt_4000"] = sum(1 for u in body if len(u.text) > 4000)
    big = sorted(body, key=lambda u: -len(u.text))[:2]
    for u in big:
        if len(u.text) > 2000:
            ex(EXAMPLES["unit_big"], f"{tag} {u.addr_part}: {len(u.text)} ký tự, đầu «{clip(u.text, 50)}»")
    for u in body:
        if len(u.text) > 2000:
            idxs = ulines[id(u)]
            if pl_start_t is not None and any(i >= pl_start_t for i in idxs):
                cause = "phu_luc_hoac_chu_ky_nuot"
            elif sign_start_t is not None and any(i >= sign_start_t for i in idxs):
                cause = "phu_luc_hoac_chu_ky_nuot"
            elif re.search(r"[“\"]\s*Điều\s+\d", u.text):
                cause = "trich_dan_luat_sua_doi"
            elif m["dieu_missing"] and u.line_from >= min(owner_first_missing, 10**9):
                cause = "nuot_Dieu_do_ngoac"
            else:
                cause = "khac"
            m[f"big_{cause}"] += 1
            if cause == "khac":
                ex(EXAMPLES["unit_big_khac"], f"{tag} {u.addr_part}: {len(u.text)} ký tự, đầu «{clip(u.text, 60)}»", 20)
    qd = 0
    for u in body:
        if u.level in ("khoan", "diem", "dieu"):
            for t in u.text.split("\n")[1:]:
                if QUOTED_DIEU.match(t.strip()):
                    qd += 1
                    ex(EXAMPLES["quoted_dieu_flattened"], f"{tag} {u.addr_part}: «{clip(t, 60)}»")
    m["quoted_dieu_flattened"] = qd

    # 10. thứ tự khoản / điểm -------------------------------------------------------------------------
    k_gap = k_dup = d_gap = d_dup = d_order = 0
    for dd in dieu:
        ks = [c for c in kids.get(dd.addr_part, []) if c.level == "khoan"]
        prev = 0
        for c in ks:
            mm = re.search(r"\.K(\d+)(~\d+)?$", c.addr_part)
            n = int(mm.group(1))
            if mm.group(2):
                k_dup += 1
            elif n > prev + 1:
                k_gap += 1
                ex(EXAMPLES["khoan_gap"], f"{tag} {c.addr_part}: nhảy từ {prev} lên {n}")
            prev = n if n > prev or n == 1 else prev
        for kh in ks:
            ds = [c for c in kids.get(kh.addr_part, []) if c.level == "diem"]
            pos_prev = -1
            for c in ds:
                mm = re.search(r"\.Đ(.+?)(~\d+)?$", c.addr_part)
                letter = mm.group(1)
                pos = DIEM_ORDER.find(letter)
                if mm.group(2):
                    d_dup += 1
                    ex(EXAMPLES["diem_dup"], f"{tag} {c.addr_part}")
                elif pos > pos_prev + 1:
                    d_gap += 1
                    ex(EXAMPLES["diem_gap"], f"{tag} {c.addr_part}: nhảy {DIEM_ORDER[pos_prev] if pos_prev >= 0 else '∅'}→{letter}")
                elif 0 <= pos < pos_prev:
                    d_order += 1
                pos_prev = max(pos_prev, pos)
    comma = 0
    for u in body:
        for i in ulines[id(u)][1:]:
            if re.match(r"^\d{1,2},\s+\S", L[i].strip()):
                comma += 1
                ex(EXAMPLES["khoan_comma"], f"{tag} trong {u.addr_part}: «{clip(L[i], 60)}»")
    m["khoan_comma_absorbed"] = comma
    m["khoan_gap"], m["khoan_dup"], m["diem_gap"], m["diem_dup"], m["diem_back"] = k_gap, k_dup, d_gap, d_dup, d_order

    # 11. số trang lọt vào đơn vị: dòng chỉ có số ở đầu/cuối mỗi trang -----------------------------------
    starts, cur = [], 0
    for v in views:
        starts.append(cur)
        cur += len(normalize_display(v.text or "").replace("\r\n", "\n").split("\n")) + 1
    pn_all = pn_in = 0
    for k, v in enumerate(views):
        a_, b_ = starts[k], (starts[k + 1] - 1 if k + 1 < len(starts) else len(L))
        idx = [i for i in range(a_, min(b_, len(L))) if L[i].strip()]
        for i in {idx[0], idx[-1]} if idx else ():
            if PAGE_NO.match(L[i].strip()):
                pn_all += 1
                if i in cov:
                    pn_in += 1
                    ex(EXAMPLES["page_no_in_unit"], f"{tag} trang {v.page_no} {owner_of(i)}: dòng «{L[i].strip()}»")
    m["page_no_lines"], m["page_no_in_unit"] = pn_all, pn_in

    # 12. số hiệu & điểm quan trọng đọc được bằng quy tắc (nhóm A/C) --------------------------------
    man = MANIFEST.get(Path(d["file_path"]).name, {})
    m["so_hieu_db"], m["so_hieu_manifest"] = d["so_hieu"], man.get("so_hieu")
    m["so_hieu_ok"] = int(d["so_hieu"] == man.get("so_hieu"))
    head = "\n".join(L[:30])
    m["ngay_ky_in_head"] = int(bool(NGAY.search(head)))
    hl_units = [u for u in dieu if re.search(r"hieu luc|thi hanh", fold_search(u.title))]
    m["dieu_hieu_luc_found"] = int(bool(hl_units))
    hl_iso = None
    for hu in hl_units[::-1]:
        txt = " ".join((hu.text + "\n" + "\n".join(c.text for c in kids.get(hu.addr_part, []))).split())
        mh = HIEU_LUC.search(txt)
        if mh:
            hl_iso = f"{mh.group(3)}-{int(mh.group(2)):02d}-{int(mh.group(1)):02d}"
            break
    m["hieu_luc_date_regex"] = hl_iso
    m["hieu_luc_db"] = d["ngay_hieu_luc"]
    m["hieu_luc_status"] = "khop" if hl_iso and hl_iso == d["ngay_hieu_luc"] else ("khac" if hl_iso and d["ngay_hieu_luc"] else ("db_co_regex_khong" if d["ngay_hieu_luc"] else ("regex_co_db_khong" if hl_iso else "khong_co")))
    m["ngay_ban_hanh_db"], m["hieu_luc_flag_db"] = d["ngay_ban_hanh"], d["hieu_luc"]
    m["has_can_cu"] = int(bool(cc))
    # 13. so với kho dựng bằng parser CŨ (trước N1a): đơn vị đổi path/nội dung
    old_rows = {r["path"]: " ".join((r["raw_text"] or "").split()) for r in db.execute(
        "SELECT path, raw_text FROM units WHERE doc_id=? AND level!='ghi_chu'", (did,))}
    new_rows = {u.addr_part: " ".join(u.text.split()) for u in body}
    m["n1a_paths_same"] = len(set(old_rows) & set(new_rows))
    m["n1a_paths_only_old"] = len(set(old_rows) - set(new_rows))
    m["n1a_paths_only_new"] = len(set(new_rows) - set(old_rows))
    m["n1a_text_changed"] = sum(1 for k in set(old_rows) & set(new_rows) if old_rows[k] != new_rows[k])
    R[did] = dict(m)
    R[did]["_tag"] = tag
    for k, v in m.items():
        if isinstance(v, int):
            TOT[k] += v

# ---- bằng chứng (84 câu) còn nằm trong đơn vị không: phủ 4-gram từ (chịu được lỗi OCR lẻ và dấu …) -------
def grams(txt: str, n=4) -> set:
    w = fold_search(txt).replace("…", " ").replace("...", " ").split()
    return {" ".join(w[k: k + n]) for k in range(max(0, len(w) - n + 1))}


ev = collections.Counter()
ev_ex = {"khong_trong_don_vi": [], "ranh_gioi": [], "phan_bi_bo": []}
cache: dict[int, tuple] = {}
for q in QUERIES:
    did = by_file.get(q["file"])
    if did is None:
        continue
    if did not in cache:
        pages = db.execute("SELECT * FROM pages WHERE doc_id=? ORDER BY page_no", (did,)).fetchall()
        views = [SimpleNamespace(page_no=p["page_no"], text=page_text(p)) for p in pages]
        res = parse_pages(views, so_hieu=db.execute("SELECT so_hieu FROM documents WHERE id=?", (did,)).fetchone()[0])
        units = [u for u in res.units if u.level != "ghi_chu"]
        L_ = normalize_display("\n\n".join(v.text for v in views)).replace("\r\n", "\n").split("\n")
        cv = covered_lines(L_, units)
        drop_txt = " ".join(L_[i] for i, l in enumerate(L_) if l.strip() and i not in cv)
        cache[did] = ([grams(u.text) for u in units], grams(" ".join(L_)), grams(drop_txt))
    ug, dg, pg = cache[did]
    g = grams(q["evidence"])
    ev["total"] += 1
    if not g:
        continue
    best = max(len(g & x) / len(g) for x in ug)
    allc = len(g & dg) / len(g)
    dropc = len(g & pg) / len(g)
    if best >= 0.8:
        ev["in_one_unit"] += 1
    elif dropc >= 0.8:
        ev["in_dropped_lines"] += 1
        ev_ex["phan_bi_bo"].append(f"{q['file']} · {clip(q['evidence'], 60)}")
    elif allc >= 0.8:
        ev["split_across_units"] += 1
        ev_ex["ranh_gioi"].append(f"{q['file']} · best={best:.2f} · {clip(q['evidence'], 60)}")
    else:
        ev["ocr_differs"] += 1
        ev_ex["khong_trong_don_vi"].append(f"{q['file']} · doc={allc:.2f} unit={best:.2f} · {clip(q['evidence'], 60)}")

out = dict(per_doc=R, totals=dict(TOT), examples=EXAMPLES, evidence=dict(ev), evidence_examples=ev_ex)
Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1, default=list))

# ---- in bảng tóm tắt -----------------------------------------------------------------------------------
cols = [
    ("dieu_true", "Điều thật"), ("dieu_parsed", "tách"), ("dieu_missing", "thiếu"), ("dieu_extra", "thừa"),
    ("mid_strict", "giữa câu"), ("tail_swallow", "câu kết"), ("table_rows", "dòng bảng"), ("table_rows_dropped", "bảng bỏ"),
    ("glue_inline_marker", "dính mốc"), ("sign_leak_lines", "ký lọt"), ("preamble_dropped", "mở đầu bỏ"),
    ("phu_luc_dropped_lines", "PL bỏ"), ("phu_luc_absorbed_lines", "PL nuốt"), ("phu_luc_own_lines", "PL riêng"), ("chuong_recognized", "Chương"),
    ("units_gt_2000", ">2000"), ("page_no_in_unit", "số trang"),
]
print("doc  so_hieu".ljust(26) + " ".join(h.rjust(9) for _, h in cols))
for did, m in R.items():
    print(m["_tag"][:25].ljust(26) + " ".join(str(m.get(k, 0)).rjust(9) for k, _ in cols))
print("TỔNG".ljust(26) + " ".join(str(TOT.get(k, 0)).rjust(9) for k, _ in cols))
print("bằng chứng:", dict(ev))
print("ghi", args.out)
