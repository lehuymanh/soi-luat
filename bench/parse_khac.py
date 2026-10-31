"""So parser của mã hiện tại với bảng units đã lưu trong một kho, không ghi gì (cổng hồi quy khi sửa parser).

python -I bench/parse_khac.py <thư mục data> [--limit N] [--vi-du K]

Mỗi văn bản (bỏ văn bản fallback_doan = 1, như nâng cấp dữ liệu N1b) được parse lại từ pages như rebuild_document;
"đổi" = danh sách (path, chữ) của đơn vị khác với units trong kho (không tính ghi chú, vì dựng lại giữ ghi chú cũ).
Kho dựng bằng parser cũ + parser mới không đổi văn bản nào = kết quả tìm trên kho đó không đổi sau nâng cấp.
"""
import json
import sqlite3
import sys
import time
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from soiluat.parse import parse_pages  # noqa: E402
from soiluat.rebuild import page_text  # noqa: E402

DATA = Path(sys.argv[1])
LIMIT = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
VD = int(sys.argv[sys.argv.index("--vi-du") + 1]) if "--vi-du" in sys.argv else 5
conn = sqlite3.connect(f"file:{DATA / 'soiluat.db'}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
docs = conn.execute("SELECT id, so_hieu, file_path FROM documents WHERE fallback_doan = 0 ORDER BY id").fetchall()[:LIMIT]
n_fb = conn.execute("SELECT COUNT(*) FROM documents WHERE fallback_doan = 1").fetchone()[0]
t0 = time.perf_counter()
changed, vi_du, them, bot = [], [], 0, 0
for d in docs:
    pages = conn.execute("SELECT * FROM pages WHERE doc_id = ? ORDER BY page_no", (d["id"],)).fetchall()
    parsed = parse_pages([SimpleNamespace(page_no=p["page_no"], text=page_text(p)) for p in pages], so_hieu=d["so_hieu"])
    new = [(u.addr_part, u.text) for u in parsed.units if u.level != "ghi_chu"]
    old = [(r[0], r[1]) for r in conn.execute(
        "SELECT path, raw_text FROM units WHERE doc_id = ? AND level != 'ghi_chu' ORDER BY id", (d["id"],))]
    if new != old:
        changed.append(d["id"])
        np_, op_ = {p for p, _ in new}, {p for p, _ in old}
        them += len(np_ - op_)
        bot += len(op_ - np_)
        if len(vi_du) < VD:
            vi_du.append({"doc_id": d["id"], "so_hieu": d["so_hieu"], "don_vi_cu": len(old), "don_vi_moi": len(new),
                          "path_moi": sorted(np_ - op_)[:5], "path_mat": sorted(op_ - np_)[:5]})
rep = {"so_van_ban": len(docs), "bo_qua_fallback_doan": n_fb, "van_ban_doi": len(changed), "path_them": them,
       "path_mat": bot, "giay": round(time.perf_counter() - t0, 1), "vi_du": vi_du}
print(json.dumps(rep, ensure_ascii=False, indent=1))
