"""Đo offline (không cần mô hình) câu trích bằng chứng còn bao nhiêu trong đoạn mà answer.build_context đưa vào mô hình.

python bench/llm/bang_chung.py <realdocs> [--modes normal,advance] [--split train|test|all] [--cache cache.json]

<realdocs>: thư mục có data/soiluat.db và queries.json (bench/van-ban-that). Mẫu câu giống run.py: 15 câu đầu của mẫu
theo seed là phần chấm (test), phần còn lại là phần chỉnh (train). Kết quả tìm được lưu vào --cache cho lần sau
(Advance mất ~8 s mỗi câu). Advance cần SOILUAT_MODEL_DIR và SOILUAT_RERANK_DIR.
In ra, theo chế độ tìm: tỉ lệ câu còn >= 50% bộ 3-từ của câu trích (ngữ cảnh tự nhiên, và khi chèn Điều đúng như
phép dan), tỉ lệ còn < 10%, và độ dài ngữ cảnh. Dùng để chọn cách dựng ngữ cảnh trước khi tốn giờ chạy mô hình.
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
import run  # noqa: E402
from soiluat import answer, semantic  # noqa: E402
from soiluat.db import connect  # noqa: E402
from soiluat.search import cascade_search  # noqa: E402

TEST_N = 15  # bằng --n của lệnh chấm văn bản thật trong KET-QUA.md


def build_cache(conn, real: Path, modes: list[str]) -> list[dict]:
    qs, label = run.load_queries(real / "queries.json", "test")
    by_key = defaultdict(list)
    for rid, k in run.root_keys(conn, label).items():
        by_key[k].append(rid)
    qs = [q for q in qs if any(k in by_key for k in q["gold"])]
    held = {q["id"] for q in run.pick_sample(qs, TEST_N)}
    out = []
    for q in qs:
        rec = {"id": q["id"], "q": q["q"], "evidence": q["evidence"], "split": "test" if q["id"] in held else "train",
               "gold": [r for k in q["gold"] for r in by_key.get(k, [])]}
        for mode in modes:
            semantic.set_mode(conn, mode)
            rec[mode] = answer.roots_in_order(conn, cascade_search(conn, q["q"]).ids)[:30]
        out.append(rec)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("real", type=Path)
    ap.add_argument("--modes", default="normal")
    ap.add_argument("--split", default="train", choices=["train", "test", "all"])
    ap.add_argument("--cache", type=Path)
    args = ap.parse_args()
    modes = args.modes.split(",")
    conn = connect(args.real / "data" / "soiluat.db")
    if args.cache and args.cache.exists():
        cache = json.load(open(args.cache, encoding="utf-8"))
    else:
        cache = build_cache(conn, args.real, modes)
        if args.cache:
            json.dump(cache, open(args.cache, "w", encoding="utf-8"), ensure_ascii=False)
    cache = [c for c in cache if c["evidence"] and (args.split == "all" or c["split"] == args.split)]
    for mode in modes:
        nat, forced, chars = [], [], []
        for c in cache:
            same = run.Same(conn, c["gold"])
            top = answer.unique_roots(conn, c[mode], answer.MAX_PASSAGES)
            fill = top if any(same(r) for r in top) else top[:-1] + [c["gold"][0]]
            ev = run.tri(c["evidence"])
            for roots, acc in ((top, nat), (fill, forced)):
                ps = answer.build_context(conn, roots, c["q"])
                acc.append(max((len(ev & run.tri(p.render())) / len(ev) for p in ps if same(p.root_id)), default=0))
                if acc is forced:
                    chars.append(sum(len(p.render()) for p in ps))
        n = len(cache)
        print(f"{mode}: {n} câu ({args.split}) | còn >= 50%: tự nhiên {sum(x >= .5 for x in nat) / n:.1%}, "
              f"chèn Điều đúng {sum(x >= .5 for x in forced) / n:.1%} | còn < 10% (chèn): "
              f"{sum(x < .1 for x in forced) / n:.1%} | ngữ cảnh {sum(chars) / n:.0f} ký tự")


if __name__ == "__main__":
    main()
