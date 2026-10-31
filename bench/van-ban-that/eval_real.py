"""Chấm tìm kiếm trên kho văn bản thật: 84 câu đã kiểm chứng (realdocs/queries.json).

python eval_real.py REALDOCS normal|advance
REALDOCS chứa data/soiluat.db và queries.json; cũng dùng cho câu hỏi văn phòng tự gom (bench/gold/README.md):
mỗi câu cần file, q, dieu_doc; kind, dieu_quoted, page, also_ok là tuỳ chọn.
Trúng (rộng): thẻ cùng file và (Điều ∈ {dieu_doc, dieu_quoted, also_ok} hoặc trang thẻ phủ trang bằng chứng).
Trúng (chặt): chỉ tính Điều. Hạng = vị trí thẻ, không gộp. "muc_*": hạng theo mục hiển thị (P1 K1 compact);
"muc_dai_dien_*" chỉ xét bản đại diện (cách tính của cổng P1 cho văn bản thật), "muc_*" xét cả "Cũng có ở".
"""
import json
import os
import re
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
P, MODE = Path(sys.argv[1]), sys.argv[2]
os.environ["SOILUAT_DATA"] = str(P / "data")
from soiluat import semantic  # noqa: E402
from soiluat.cards import assemble_cards, compact  # noqa: E402
from soiluat.db import connect  # noqa: E402
from soiluat.search import DIEU_CAP, cascade_search  # noqa: E402

DIEU = re.compile(r"^D(\d+)", re.I)
conn = connect(P / "data" / "soiluat.db")
semantic.set_mode(conn, MODE)
qs = json.load(open(P / "queries.json", encoding="utf-8"))


def cards_for(q):
    r = cascade_search(conn, q)
    ids = r.ids[:DIEU_CAP] if r.note == "dieu" else r.ids
    idset = set(ids)
    return assemble_cards(conn, ids, synonym_note=r.note, fold_ids={i for i in r.fold_ids if i in idset},
                          f2_ids={i for i in r.f2_ids if i in idset}, tiers=r.tiers, intent=r.intent)


def dieu_of(c):
    row = conn.execute("SELECT path FROM units WHERE id = ?", (c.unit_ids[0],)).fetchone() if c.unit_ids else None
    m = DIEU.match(row[0]) if row else None
    return m.group(1) if m else None


if MODE == "advance":  # nạp mô hình trước, không tính vào độ trễ câu đầu
    cards_for("khởi động")
out, lat = [], []
for q in qs:
    ok_dieu = {str(x) for x in [q["dieu_doc"], q.get("dieu_quoted"), *q.get("also_ok", [])] if x}
    t = time.perf_counter()
    cs = cards_for(q["q"])
    lat.append((time.perf_counter() - t) * 1000)
    def ranks(rows):
        """rows: [(hạng, thẻ)]; trả (hạng rộng, hạng chặt) đầu tiên."""
        loose = strict = None
        for k, c in rows:
            if Path(c.file_path).name != q["file"]:
                continue
            d = dieu_of(c)
            pf, pt = c.page_from, c.page_to or c.page_from
            if strict is None and d in ok_dieu:
                strict = k
            if loose is None and (d in ok_dieu or (pf is not None and q.get("page") and pf <= q["page"] <= pt)):
                loose = k
        return loose, strict

    loose, strict = ranks(enumerate(cs, 1))
    items = compact(conn, list(cs), q["q"], limit=0)
    m_loose, m_strict = ranks((k, c) for k, it in enumerate(items, 1) for c in [it, *it.also_in])
    d_loose, d_strict = ranks(enumerate(items, 1))
    file_rank = next((k for k, c in enumerate(cs, 1) if Path(c.file_path).name == q["file"]), None)
    out.append({**{k: q.get(k) for k in ("file", "q", "dieu_doc", "page")}, "kind": q.get("kind", "cau_hoi"), "rong": loose, "chat": strict,
                "muc_rong": m_loose, "muc_chat": m_strict, "muc_dai_dien_rong": d_loose, "muc_dai_dien_chat": d_strict,
                "file_dau": file_rank, "so_the": len(cs), "so_muc": len(items), "hien_san": min(5, len(items)),
                "ms": round(lat[-1])})


def hit(key, sub=None):
    v = [o[key] for o in out if sub is None or o["kind"] == sub]
    return {k: round(sum(1 for r in v if r and r <= k) / len(v) * 100, 1) for k in (1, 3, 5, 10)}


lat.sort()
rep = {"mode": MODE, "so_cau": len(out), "rong": hit("rong"), "chat": hit("chat"),
       "rong_tu_khoa": hit("rong", "tu_khoa"), "rong_cau_hoi": hit("rong", "cau_hoi"), "dung_file_top1": hit("file_dau")[1],
       "p50_ms": round(lat[len(lat) // 2]), "p95_ms": round(lat[int(len(lat) * .95)]),
       "the_tb": round(sum(o["so_the"] for o in out) / len(out), 1),
       "muc_rong": hit("muc_rong"), "muc_chat": hit("muc_chat"),
       "muc_dai_dien_rong": hit("muc_dai_dien_rong"), "muc_dai_dien_chat": hit("muc_dai_dien_chat"),
       "muc_tb": round(sum(o["so_muc"] for o in out) / len(out), 1),
       "hien_san_tb": round(sum(o["hien_san"] for o in out) / len(out), 1)}
print(json.dumps(rep, ensure_ascii=False))
json.dump({"tong": rep, "tung_cau": out}, open(P / f"eval_{MODE}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
