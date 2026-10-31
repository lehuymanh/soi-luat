"""Cổng P1 "bấm trích dẫn mở trình đọc ≤ 1 giây": thời gian GET /doc/{id} trên kho lớn (bản sao Zalo).

python -I bench/doc_open.py <thư mục data> [--n 100]

Văn bản nhiều đơn vị nhất cộng n văn bản ngẫu nhiên (seed cố định); mở ở đơn vị cuối, có câu hỏi để tô từ.
p95 theo cùng quy ước bench/zalo/eval.py (lat.sort(); lat[int(n * 0.95)]). Ghi <data>/../doc_open.json.
Chạy trên bản sao: init_schema mỗi request tạo bảng mới nếu kho cũ chưa có.
"""
import json
import os
import random
import sys
import time
from pathlib import Path

DATA = Path(sys.argv[1])
N = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 100
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ["SOILUAT_DATA"] = str(DATA)
os.environ["SOILUAT_ALLOW_TEST_HOST"] = "1"  # TestClient gửi Host "testserver"
from fastapi.testclient import TestClient  # noqa: E402

from soiluat.app import app  # noqa: E402
from soiluat.db import connect  # noqa: E402

conn = connect(DATA / "soiluat.db")
big, n_big = conn.execute("SELECT doc_id, COUNT(*) FROM units GROUP BY doc_id ORDER BY COUNT(*) DESC LIMIT 1").fetchone()
ids = [r[0] for r in conn.execute("SELECT id FROM documents WHERE id != ?", (big,))]
docs = [big] + random.Random(1).sample(ids, min(N, len(ids)))
client = TestClient(app)
client.get(f"/doc/{big}")  # khởi động (nạp template), không tính
lat, rows = [], []
for d in docs:
    u = conn.execute("SELECT id FROM units WHERE doc_id = ? ORDER BY id DESC LIMIT 1", (d,)).fetchone()
    t = time.perf_counter()
    r = client.get(f"/doc/{d}", params={"u": u[0] if u else "", "q": "phạt tiền"})
    ms = (time.perf_counter() - t) * 1000
    assert r.status_code == 200 and (u is None or f'id="u{u[0]}"' in r.text), (d, r.status_code)
    lat.append(ms)
    rows.append({"doc_id": d, "ms": round(ms), "kb": round(len(r.content) / 1024)})
lat.sort()
rep = {"so_van_ban": len(docs), "lon_nhat": {"doc_id": big, "so_don_vi": n_big, "ms": rows[0]["ms"], "kb": rows[0]["kb"]},
       "p50_ms": round(lat[len(lat) // 2]), "p95_ms": round(lat[int(len(lat) * 0.95)]), "max_ms": round(lat[-1])}
print(json.dumps(rep, ensure_ascii=False))
(DATA.parent / "doc_open.json").write_text(json.dumps({"tong": rep, "tung_van_ban": rows}, ensure_ascii=False, indent=1),
                                           encoding="utf-8")
