"""Đo phần trả lời bằng LLM (lộ trình 1.0, P0): chấm hoàn toàn bằng máy, đáp án là Điều đúng có sẵn trong bộ đo.

python bench/llm/run.py DB QUERIES [--split test] [--url http://127.0.0.1:8080] [--n 50] [--skip 0] [--bay 30]
                        [--mode normal|advance] [--passages 5] [--out ket_qua.json]

DB: soiluat.db của kho chứa văn bản nguồn (kho Zalo cho Zalo và gold vle; realdocs/data/soiluat.db cho văn bản thật).
QUERIES: thư mục dạng GreenNode (queries.jsonl + qrels_<split>.jsonl hoặc qrels/<split>.jsonl; split 'gold' cho vle),
hoặc file queries.json dạng bench/van-ban-that (file, q, dieu_doc, also_ok).

Mỗi câu hỏi chạy hai phép, cùng câu, khác ngữ cảnh:
- dan: Điều đúng nằm trong ngữ cảnh (giữ chỗ tìm kiếm xếp; ngoài top thì thay đoạn cuối). Đúng khi du_can_cu = true
  và có ý dẫn đoạn đó, hoặc dẫn một Điều gần như cùng chữ (bản trước/sau sửa đổi, bản chép ở văn bản khác).
- tu_choi: bỏ Điều đúng và các Điều gần như cùng chữ đó. Đúng khi du_can_cu = false.
Thêm --bay câu bẫy sinh từ điểm có mức phạt (units.fine_min/fine_max), hỏi với mức tiền gấp 3. Đúng khi tien_de_sai
khác rỗng và câu trả lời nêu đúng một mức trong nguồn.
Máy chủ: llama-server (llama.cpp), hoặc server cùng API OpenAI có response_format.json_object.schema.
Thời gian: tìm (cascade_search như app) + gọi mô hình, đo bằng đồng hồ; số token lấy từ server nếu có.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
import urllib.request
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from soiluat import answer, crossrank, semantic  # noqa: E402
from soiluat.db import connect  # noqa: E402
from soiluat.fold import fold_search  # noqa: E402
from soiluat.search import cascade_search  # noqa: E402

DIEU = re.compile(r"^D(\d+[a-z]?)", re.I)
SEED = 2026


def load_queries(path: Path, split: str) -> tuple[list[dict], str]:
    """[{id, q, gold: {'<văn bản>+<Điều>'}}] và cách gọi tên văn bản ('path': file_path như Zalo; 'name': tên file)."""
    if path.is_file():
        out = []
        for i, q in enumerate(json.load(open(path, encoding="utf-8"))):
            ok = {str(x) for x in [q["dieu_doc"], q.get("dieu_quoted"), *q.get("also_ok", [])] if x}
            out.append({"id": str(i), "q": q["q"], "gold": {f"{q['file']}+{d}".lower() for d in ok},
                        "evidence": q.get("evidence") or ""})
        return out, "name"
    qs = {d["_id"]: d["text"] for d in map(json.loads, open(path / "queries.jsonl", encoding="utf-8"))}
    rel = path / f"qrels_{split}.jsonl"
    if not rel.exists():
        rel = path / "qrels" / f"{split}.jsonl"
    gold: dict[str, set[str]] = defaultdict(set)
    for d in map(json.loads, open(rel, encoding="utf-8")):
        gold[d["query-id"]].add(d["corpus-id"].lower())
    return [{"id": k, "q": qs[k], "gold": g} for k, g in sorted(gold.items())], "path"


def pick_sample(qs: list[dict], n: int, skip: int = 0) -> list[dict]:
    """n câu theo seed. skip > 0: bỏ đúng `skip` câu mà `--n skip` sẽ chấm, lấy n câu từ phần còn lại. Không cắt tiền tố
    của sample(qs, skip + n): random.sample đổi thuật toán theo cỡ mẫu nên tiền tố có thể khác sample(qs, skip)."""
    held = {q["id"] for q in random.Random(SEED).sample(qs, min(skip, len(qs)))}
    rest = [q for q in qs if q["id"] not in held]
    return random.Random(SEED).sample(rest, min(n, len(rest)))


def root_keys(conn, label: str) -> dict[int, str]:
    out = {}
    for rid, fp, path in conn.execute(
        "SELECT u.id, d.file_path, u.path FROM units u JOIN documents d ON d.id = u.doc_id WHERE u.parent_id IS NULL"
    ):
        m = DIEU.match(path or "")
        if m:
            name = fp.replace("\\", "/").rsplit("/", 1)[-1] if label == "name" else fp
            out[rid] = f"{name}+{m.group(1)}".lower()
    return out


NEAR = 0.7  # ≥ 70% bộ 3-từ của Điều dài hơn trùng với Điều kia: cùng nội dung (bản chép, bản cũ/mới); 0,5 theo Điều
# ngắn hơn thì gộp nhầm các Điều khác nhau của cùng một nghị định (Điều 5, 6, 7 NĐ 100/2019)


def tri(text: str) -> set:
    w = fold_search(text).split()
    return {tuple(w[i:i + 3]) for i in range(max(len(w) - 2, 1))}


def shingles(conn, rid: int) -> set:
    head, lines = semantic.root_lines(conn, rid)
    return tri(" ".join(t for _, t in lines) or head)


class Same:
    """Điều nào gần như cùng chữ với Điều đúng: dùng để chấm 'dan' và để loại khỏi ngữ cảnh 'tu_choi'."""

    def __init__(self, conn, gold: list[int]):
        self.conn, self.gold = conn, set(gold)
        self.sh = [shingles(conn, g) for g in gold]

    def __call__(self, rid: int) -> bool:
        if rid in self.gold:
            return True
        s = shingles(self.conn, rid)
        return any(s and g and len(s & g) / max(len(s), len(g)) >= NEAR for g in self.sh)


def vnd(v: int) -> str:
    return f"{v:,}".replace(",", ".")


def traps(conn, k: int) -> list[dict]:
    """Câu hỏi tiền đề sai: hành vi ở một điểm dưới khoản 'phạt tiền từ … đối với … hành vi', mức tiền gấp 3."""
    rows = conn.execute(
        """SELECT u.id, u.normalized_text, u.fine_min, u.fine_max FROM units u
           JOIN units s ON s.id = u.fine_source_unit
           WHERE u.level = 'diem' AND u.fine_min > 0 AND u.fine_max > u.fine_min
             AND length(u.normalized_text) BETWEEN 20 AND 220 AND s.normalized_text LIKE '%hành vi%'
           ORDER BY u.id"""
    ).fetchall()
    out = []
    for uid, text, mn, mx in random.Random(SEED).sample(rows, min(k, len(rows))):
        hv = text.strip().rstrip(";.,:").strip()
        q = f"{hv[0].upper()}{hv[1:]} thì bị phạt tiền từ {vnd(3 * mn)} đồng đến {vnd(3 * mx)} đồng, đúng không?"
        out.append({"id": f"bay{uid}", "q": q, "unit": uid, "fine": {mn, mx}})
    return out


def cited(a: dict) -> set:
    return {n for y in a.get("cac_y") or [] if isinstance(y, dict) for n in y.get("nguon") or []}


def sentences(t: str) -> int:
    return len([s for s in re.split(r"(?<=[.!?…])\s+", (t or "").strip()) if s])


def model_id(url: str) -> str:
    try:
        req = urllib.request.Request(url.rstrip("/") + "/v1/models")
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=10) as r:
            return json.load(r)["data"][0]["id"]
    except Exception:  # noqa: BLE001 — chỉ để ghi vào báo cáo
        return "?"


def ask(conn, args, roots: list[int], q: str) -> dict:
    ps = answer.build_context(conn, roots, q, max_passages=args.passages)
    t = time.perf_counter()
    res, content, err = {}, None, ""
    try:
        res = answer.chat(args.url, answer.messages(ps, q), answer.schema(len(ps)), api_key=args.api_key,
                          temperature=args.temp)
        content = res["choices"][0]["message"]["content"]
    except Exception as e:  # noqa: BLE001 — máy chủ lỗi/hết giờ: ghi lại, câu đó tính là sai
        err = repr(e)
    llm_s = time.perf_counter() - t
    chk = answer.check(content, ps, q)
    usage, tim = res.get("usage") or {}, res.get("timings") or {}
    return {
        "passages": [p.root_id for p in ps],
        "ctx": [p.render() for p in ps],
        "ctx_chars": sum(len(p.render()) for p in ps),
        "content": content,
        "raw": chk.raw,
        "checked": chk.answer,
        "dropped": chk.dropped,
        "json_ok": chk.json_ok,
        "cut": chk.cut,
        "llm_s": round(llm_s, 2),
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "prompt_n": tim.get("prompt_n"),  # llama-server: token prompt phải đọc mới (sau cache)
        "prompt_per_second": tim.get("prompt_per_second"),
        "predicted_per_second": tim.get("predicted_per_second"),
        "err": err,
    }


def pct(xs) -> float | None:
    xs = list(xs)
    return round(100 * sum(map(bool, xs)) / len(xs), 1) if xs else None


def pctl(xs, p: float) -> float | None:
    xs = sorted(x for x in xs if x is not None)
    return round(xs[min(int(len(xs) * p), len(xs) - 1)], 2) if xs else None


def summary(recs: list[dict], meta: dict) -> dict:
    by = defaultdict(list)
    for r in recs:
        by[r["kind"]].append(r)
    ok_json = [r for r in recs if r["json_ok"]]
    return {
        **meta,
        "so_lan_goi": len(recs),
        "json_hop_le": pct(r["json_ok"] and not r["cut"] for r in recs),
        "json_dung_duoc": pct(r["json_ok"] for r in recs),
        "bi_cat": pct((r["completion_tokens"] or 0) >= answer.N_PREDICT for r in recs),
        "dan_dung": pct(r["ok"] for r in by["dan"]),
        "dan_dung_sau_kiem": pct(bool(cited(r["checked"]) & set(r["gold_n"])) for r in by["dan"]),
        "dan_tien_de_sai_thua": pct((r["raw"].get("tien_de_sai") or "").strip() for r in by["dan"]),
        "dan_dieu_dung_do_tim_ra": pct(r["natural"] for r in by["dan"]),
        "dan_bang_chung_con": pct(r["bang_chung"] >= 0.5 for r in by["dan"] if r.get("bang_chung") is not None),
        "tu_choi_dung": pct(r["ok"] for r in by["tu_choi"]),
        "tu_choi_hoac_neu_hep": pct(r["ok"] or r["raw"].get("pham_vi") in ("hẹp hơn", "khác") for r in by["tu_choi"]),
        "dan_pham_vi_khong_dung": pct(r["raw"].get("pham_vi") not in (None, "đúng") for r in by["dan"]),
        "bay_dung": pct(r["ok"] for r in by["bay"]),
        "bay_co_tien_de_sai": pct((r["raw"].get("tien_de_sai") or "").strip() for r in by["bay"]),
        "so_khop": pct(not any(d.endswith(":so") for d in r["dropped"]) for r in ok_json),
        "co_chu_cjk": pct(answer.CJK.search(r["content"] or "") for r in recs),
        "qua_3_cau": pct(sentences(r["raw"].get("tra_loi")) > 3 for r in ok_json),
        "thay_bang_trich": pct(r["checked"].get("trich_nguyen_van") for r in recs),
        "loi_may_chu": sum(1 for r in recs if r["err"]),
        "tim_p50_s": pctl([r["search_s"] for r in recs], 0.5),
        "llm_p50_s": pctl([r["llm_s"] for r in recs], 0.5),
        "llm_p95_s": pctl([r["llm_s"] for r in recs], 0.95),
        "tong_p50_s": pctl([r["search_s"] + r["llm_s"] for r in recs], 0.5),
        "tong_p95_s": pctl([r["search_s"] + r["llm_s"] for r in recs], 0.95),
        "prompt_tokens_tb": round(sum(r["prompt_tokens"] or 0 for r in recs) / max(len(recs), 1)),
        "prompt_tokens_p95": pctl([r["prompt_tokens"] for r in recs], 0.95),
        "completion_tokens_tb": round(sum(r["completion_tokens"] or 0 for r in recs) / max(len(recs), 1)),
        "ctx_chars_tb": round(sum(r["ctx_chars"] for r in recs) / max(len(recs), 1)),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("db", type=Path)
    ap.add_argument("queries", type=Path)
    ap.add_argument("--split", default="test")
    ap.add_argument("--url", default=os.environ.get("SOILUAT_LLM_URL", "http://127.0.0.1:8080"))
    ap.add_argument("--api-key", default=os.environ.get("SOILUAT_LLM_KEY", ""))
    ap.add_argument("--n", type=int, default=50, help="số câu hỏi (mỗi câu hai lần gọi: dan, tu_choi)")
    ap.add_argument("--skip", type=int, default=0, help="bỏ K câu đầu của mẫu (bộ không có tập train: chỉnh trên "
                    "phần còn lại, chấm trên K câu đầu)")
    ap.add_argument("--bay", type=int, default=30, help="số câu bẫy tiền đề sai")
    ap.add_argument("--mode", choices=semantic.MODES, default="advance")
    ap.add_argument("--passages", type=int, default=answer.MAX_PASSAGES)
    ap.add_argument("--temp", type=float, default=answer.TEMPERATURE)
    ap.add_argument("--out", type=Path, default=Path("ket_qua_llm.json"))
    args = ap.parse_args()

    conn = connect(args.db)
    semantic.set_mode(conn, args.mode)
    if args.mode == "advance" and not (
        conn.execute("SELECT 1 FROM unit_vectors WHERE model = ? LIMIT 1", (semantic.MODEL_NAME,)).fetchone()
        and semantic.encoder() and crossrank.ranker()
    ):  # thiếu thì app lặng lẽ tìm như Normal: số đo sẽ ghi nhầm là Advance
        sys.exit("Kho chưa có vector hoặc chưa cài mô hình AITeamVN: dùng --mode normal, hoặc nhúng vector trước.")
    qs, label = load_queries(args.queries, args.split)
    keys = root_keys(conn, label)
    by_key: dict[str, list[int]] = defaultdict(list)
    for rid, k in keys.items():
        by_key[k].append(rid)
    qs = [q for q in qs if any(k in by_key for k in q["gold"])]
    sample = pick_sample(qs, args.n, args.skip)
    if not sample:
        sys.exit("Không còn câu hỏi nào sau khi lọc theo kho và --skip.")
    jobs = [("dan", q) for q in sample] + [("tu_choi", q) for q in sample] + [("bay", t) for t in traps(conn, args.bay)]
    random.Random(SEED).shuffle(jobs)  # xen kẽ ba phép: máy nóng/nguội không lệch về một phép
    meta = {"model": model_id(args.url), "db": str(args.db), "queries": str(args.queries), "mode": args.mode,
            "passages": args.passages, "temp": args.temp, "ctx_chars": answer.CTX_CHARS, "n": len(sample),
            "skip": args.skip,
            "cpu": os.cpu_count()}
    n_ctx = args.passages

    ask(conn, args, answer.roots_in_order(conn, cascade_search(conn, sample[0]["q"]).ids)[:n_ctx], sample[0]["q"])  # câu mồi: system prompt vào cache
    recs: list[dict] = []
    for i, (kind, q) in enumerate(jobs, 1):
        t = time.perf_counter()
        ranked = answer.roots_in_order(conn, cascade_search(conn, q["q"]).ids)
        search_s = time.perf_counter() - t
        natural = None
        if kind == "bay":
            gold = list(semantic.root_ids(conn, [q["unit"]]).values())
            if not gold:
                continue
        else:
            gold = [r for k in q["gold"] for r in by_key.get(k, [])]
        same = Same(conn, gold)
        uniq = answer.unique_roots(conn, ranked, 3 * n_ctx)
        if kind == "tu_choi":
            ctx = [r for r in uniq if not same(r)][:n_ctx]
        else:
            top = uniq[:n_ctx]
            natural = any(same(r) for r in top)
            ctx = top if natural else top[: n_ctx - 1] + [gold[0]]
        r = ask(conn, args, ctx, q["q"])
        gold_n = [k for k, rid in enumerate(r["passages"], 1) if same(rid)]
        if q.get("evidence") and kind == "dan":  # câu trích đáp án còn bao nhiêu trong đoạn: tách lỗi cắt khỏi lỗi mô hình
            ev = tri(q["evidence"])
            r["bang_chung"] = round(max((len(ev & tri(r["ctx"][k - 1])) / len(ev) for k in gold_n), default=0.0), 2)
        a = r["raw"]
        if kind == "dan":
            ok = a.get("du_can_cu") is True and bool(cited(a) & set(gold_n))
        elif kind == "tu_choi":
            ok = a.get("du_can_cu") is False
        else:
            said = " ".join([a.get("tien_de_sai") or "", a.get("tra_loi") or ""] + [y.get("y", "") for y in a.get("cac_y") or [] if isinstance(y, dict)])
            right = {Decimal(v) for v in q["fine"]} - {Decimal(3 * v) for v in q["fine"]}  # nhắc lại số của câu hỏi không tính
            ok = bool((a.get("tien_de_sai") or "").strip()) and bool(right & answer.numbers(said))
        recs.append({"kind": kind, "id": q["id"], "q": q["q"], "gold_n": gold_n, "natural": natural, "ok": ok,
                     "search_s": round(search_s, 2), **r})
        print(f"{i}/{len(jobs)} {kind:7} {'đúng' if ok else 'sai '} tìm {search_s:.1f}s + LLM {r['llm_s']:.1f}s"
              f"{' ' + r['err'][:80] if r['err'] else ''}", file=sys.stderr, flush=True)
        json.dump({"tong": summary(recs, meta), "tung_cau": recs}, open(args.out, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    print(json.dumps(summary(recs, meta), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
