"""Chạy demo + đo hiệu năng Soi Luật trên máy hiện tại.

python bench/run_bench.py DEMO_DIR          (sau gen_corpus.py + word_tools.py)

Ra DEMO_DIR/results/*.json. Không đụng ./data của repo: mọi DB nằm trong DEMO_DIR.
"""

from __future__ import annotations

import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

import psutil

REPO = Path(__file__).resolve().parents[1]
TESS_DIR = r"C:\Program Files\Tesseract-OCR"
TESSDATA = str(Path(os.environ.get("LOCALAPPDATA", "")) / "SoiLuatDemo" / "tessdata")
PORT = 8765  # app hardcode 8000; máy đo có wslrelay chiếm 8000 nên chạy uvicorn trực tiếp


def _env(data: Path, ocr_path: bool) -> dict:
    env = dict(os.environ, SOILUAT_DATA=str(data), PYTHONIOENCODING="utf-8", PYTHONPATH=str(REPO / "src"))
    if ocr_path:
        env["PATH"] = TESS_DIR + os.pathsep + env["PATH"]
        env["TESSDATA_PREFIX"] = TESSDATA
    else:
        env["PATH"] = os.pathsep.join(p for p in env["PATH"].split(os.pathsep) if "Tesseract" not in p)
    return env


def sys_ram() -> dict:
    vm = psutil.virtual_memory()
    return {"total_mb": vm.total // 2**20, "avail_mb": vm.available // 2**20, "used_pct": vm.percent}


# ---------- worker: nạp file, chạy trong process riêng để đo RAM đỉnh ----------

def worker_import(files_json: str, out_json: str, ocr: str) -> None:
    from soiluat.config import data_dir, db_path
    from soiluat.db import connect, init_schema
    from soiluat.ingest import ingest_path

    files = json.loads(Path(files_json).read_text(encoding="utf-8"))
    root = data_dir()
    root.mkdir(parents=True, exist_ok=True)
    conn = connect(db_path())
    init_schema(conn)
    me = psutil.Process()
    rows = []
    t_all = time.perf_counter()
    for f in files:
        t0 = time.perf_counter()
        rec = {"file": f}
        try:
            doc_id = ingest_path(conn, Path(f), root, run_ocr=ocr == "1")
            d = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
            rec.update(
                ok=True, doc_id=doc_id, so_hieu=d["so_hieu"], file_path=d["file_path"],
                struct_score=d["struct_score"], fallback_doan=d["fallback_doan"],
                extraction=d["extraction_method"],
                n_units=conn.execute("SELECT COUNT(*) FROM units WHERE doc_id=?", (doc_id,)).fetchone()[0],
                n_dieu=conn.execute("SELECT COUNT(*) FROM units WHERE doc_id=? AND level='dieu'", (doc_id,)).fetchone()[0],
                n_pages=conn.execute("SELECT COUNT(*) FROM pages WHERE doc_id=?", (doc_id,)).fetchone()[0],
                ocr_pages=conn.execute("SELECT COUNT(*) FROM pages WHERE doc_id=? AND extraction_method='ocr'", (doc_id,)).fetchone()[0],
                empty_pages=conn.execute("SELECT COUNT(*) FROM pages WHERE doc_id=? AND length(trim(coalesce(raw_text,'')))<40", (doc_id,)).fetchone()[0],
                chars=conn.execute("SELECT COALESCE(SUM(length(raw_text)),0) FROM units WHERE doc_id=?", (doc_id,)).fetchone()[0],
            )
        except Exception as e:  # ghi lỗi, nạp tiếp file sau (CLI thật thì dừng — xem cli_dirty)
            rec.update(ok=False, error=f"{type(e).__name__}: {e}"[:300])
        rec["sec"] = round(time.perf_counter() - t0, 3)
        rec["rss_mb"] = round(me.memory_info().rss / 2**20, 1)
        rows.append(rec)
    mi = me.memory_info()
    out = {
        "files": rows,
        "total_sec": round(time.perf_counter() - t_all, 2),
        "peak_mb": round(getattr(mi, "peak_wset", mi.rss) / 2**20, 1),
        "cpu_sec": round(sum(me.cpu_times()[:2]), 2),
        "db_mb": round(db_path().stat().st_size / 2**20, 2),
    }
    conn.close()
    Path(out_json).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


def run_import(name: str, files: list[Path], data: Path, res: Path, ocr: bool, ocr_path: bool = True) -> dict:
    lst = res / f"{name}.files.json"
    lst.write_text(json.dumps([str(f) for f in files], ensure_ascii=False), encoding="utf-8")
    out = res / f"import_{name}.json"
    before = sys_ram()
    t0 = time.perf_counter()
    subprocess.run([sys.executable, __file__, "_import", str(lst), str(out), "1" if ocr else "0"],
                   env=_env(data, ocr_path), check=True)
    r = json.loads(out.read_text(encoding="utf-8"))
    r["wall_sec_incl_startup"] = round(time.perf_counter() - t0, 2)
    r["sys_ram_before"] = before
    out.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    ok = sum(1 for x in r["files"] if x["ok"])
    print(f"[import {name}] {ok}/{len(files)} ok, {r['total_sec']}s, peak {r['peak_mb']} MB, db {r['db_mb']} MB")
    return r


# ---------- truy vấn + đáp án ----------

ABBR = {
    "thuế giá trị gia tăng": "thuế GTGT", "bảo hiểm xã hội bắt buộc": "BHXH bắt buộc",
    "phương tiện phòng cháy và chữa cháy": "phương tiện PCCC", "phương án chữa cháy": "phương án PCCC",
    "báo cáo đánh giá tác động môi trường": "báo cáo ĐTM", "hóa đơn điện tử": "HĐĐT",
    "hệ thống báo cháy tự động": "hệ thống báo cháy", "hợp đồng lao động bằng văn bản": "HĐLĐ",
}
PARA = {
    ("nộp", "hồ sơ khai thuế"): "gửi tờ khai thuế", ("đóng", "bảo hiểm xã hội bắt buộc"): "nộp tiền bảo hiểm xã hội",
    ("giao kết", "hợp đồng lao động bằng văn bản"): "ký hợp đồng lao động",
    ("thu gom", "chất thải nguy hại"): "xử lý rác thải nguy hại", ("lập", "hóa đơn điện tử"): "xuất hóa đơn điện tử",
    ("trả", "lương làm thêm giờ"): "thanh toán tiền làm thêm giờ", ("ghi", "nhãn hàng hóa"): "dán nhãn sản phẩm",
    ("xóa", "dữ liệu cá nhân khi hết mục đích"): "hủy dữ liệu cá nhân",
    ("đề nghị cấp", "giấy phép xây dựng"): "xin giấy phép xây dựng",
    ("trang bị", "phương tiện phòng cháy và chữa cháy"): "mua bình chữa cháy",
}


def build_queries(demo: Path) -> list[dict]:
    from soiluat.fold import fold_search

    sys.path.insert(0, str(Path(__file__).parent))
    from gen_corpus import TOPICS

    man = json.loads((demo / "manifest.json").read_text(encoding="utf-8"))
    qs: list[dict] = []
    for t in TOPICS:
        for a, o in t["acts"]:
            ph = f"{a} {o}"
            want = sorted({f"{m['so_hieu']}#{d['dieu']}" for m in man for d in m["dieus"]
                           if d["kind"] == "nghia_vu" and ph in d["phrases"]})
            if not want:
                continue
            qs.append({"group": "tu_khoa", "q": ph, "want": want})
            qs.append({"group": "khong_dau", "q": fold_search(ph), "want": want})
            qs.append({"group": "cau_hoi", "q": f"{t['subj']} có phải {ph} không?", "want": want})
            qs.append({"group": "cau_hoi", "q": f"quy định về việc {ph} như thế nào?", "want": want})
            if o in ABBR:
                qs.append({"group": "viet_tat", "q": f"{a} {ABBR[o]}", "want": want})
            if (a, o) in PARA:
                qs.append({"group": "dien_dat_khac", "q": PARA[(a, o)], "want": want})
            sanc = sorted({f"{m['so_hieu']}#{d['dieu']}" for m in man for d in m["dieus"]
                           if d["kind"] == "che_tai" and f"không {ph}" in d["phrases"]})
            if sanc:
                qs.append({"group": "muc_phat", "q": f"mức phạt không {ph}", "want": sanc})
        for b in t["bans"]:
            want = sorted({f"{m['so_hieu']}#{d['dieu']}" for m in man for d in m["dieus"]
                           if d["kind"] == "cam" and b in d["phrases"]})
            if want:
                qs.append({"group": "tu_khoa", "q": b, "want": want})
    for m in man[::20]:
        d5 = next((d for d in m["dieus"] if d["dieu"] == 5), None)
        qs.append({"group": "so_hieu", "q": m["so_hieu"], "want": [f"{m['so_hieu']}#{d['dieu']}" for d in m["dieus"]]})
        qs.append({"group": "so_hieu", "q": fold_search(m["so_hieu"]), "want": [f"{m['so_hieu']}#{d['dieu']}" for d in m["dieus"]]})
        if d5:
            qs.append({"group": "dieu_so_hieu", "q": f"Điều 5 {m['so_hieu']}", "want": [f"{m['so_hieu']}#5"]})
    for e in json.loads((demo / "dirty_expect.json").read_text(encoding="utf-8")):
        qs.append({"group": "dirty", "q": e["query"], "file": e["file"], "expect": e["want"], "note": e["note"]})
    return qs


def worker_quality(q_json: str, out_json: str) -> None:
    import re

    from soiluat.app import _search_ctx
    from soiluat.fold import fold_search

    qs = json.loads(Path(q_json).read_text(encoding="utf-8"))
    out = []
    for q in qs:
        t0 = time.perf_counter()
        ctx = _search_ctx(q["q"], "", "", "")
        ms = (time.perf_counter() - t0) * 1000
        cards = ctx["cards"]
        top = cards[:10]
        rec = {**q, "ms": round(ms, 1), "n_cards": len(cards)}
        if q["group"] == "dirty":
            fq = fold_search(q["q"])
            # văn bản tách từ một file có file_path "<path>#vb<k>"
            hits = [c for c in top if fold_search(c.file_path.split("#vb")[0]).endswith(fold_search(Path(q["file"]).name))
                    and (fq in fold_search(c.duty_text + " " + c.sanction_text) or q["expect"].startswith("so_hieu"))]
            rec.update(found=bool(hits), addr=(hits[0].duty_addr or hits[0].sanction_addr) if hits else "",
                       kind=hits[0].kind if hits else "", page=hits[0].page_from if hits else None,
                       warnings=hits[0].warnings if hits else [],
                       top_files=[c.file_path for c in top[:3]])
        else:
            want = set(q["want"])

            def key(c):
                m = re.search(r"Điều (\d+)", c.duty_addr or c.sanction_addr or "")
                return f"{c.so_hieu}#{m.group(1)}" if m else ""

            # thẻ mức phạt: Điều chế tài có thể nằm ở sanction_addr
            def keys(c):
                ks = {key(c)}
                m = re.search(r"Điều (\d+)", c.sanction_addr or "")
                if m:
                    ks.add(f"{c.so_hieu}#{m.group(1)}")
                return ks

            rel = [bool(keys(c) & want) for c in top]
            rec.update(hit10=any(rel), p10=round(sum(rel) / len(top), 3) if top else 0.0,
                       first_rel=(rel.index(True) + 1) if any(rel) else None,
                       ranks=[c.rank for c in top], n_want=len(want))
        rec.pop("want", None)
        out.append(rec)
    Path(out_json).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


# ---------- Search App qua HTTP ----------

def bench_server(data: Path, res: Path, qs: list[dict], tag: str, cores: list[int] | None) -> dict:
    import httpx

    env = _env(data, ocr_path=False)
    t0 = time.perf_counter()
    proc = subprocess.Popen([sys.executable, "-c",
                             f"import uvicorn; uvicorn.run('soiluat.app:app', host='127.0.0.1', port={PORT})"],
                            env=env, cwd=str(REPO),
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    p = psutil.Process(proc.pid)
    if cores:
        p.cpu_affinity(cores)
    base = f"http://127.0.0.1:{PORT}"
    try:
        with httpx.Client(base_url=base, timeout=60) as cli:
            while True:
                try:
                    if cli.get("/").status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                if time.perf_counter() - t0 > 60:
                    raise RuntimeError("Search App không lên sau 60 giây")
                time.sleep(0.05)
            startup = time.perf_counter() - t0
            rss_idle0 = p.memory_info().rss
            p.cpu_percent(None)
            time.sleep(10)
            cpu_idle = p.cpu_percent(None)
            lat: dict[str, list[float]] = {}
            first: list[float] = []
            for rep in range(3):
                for q in qs:
                    t1 = time.perf_counter()
                    r = cli.get("/", params={"q": q["q"]}, headers={"HX-Request": "true"})
                    dt = (time.perf_counter() - t1) * 1000
                    if r.status_code != 200:
                        lat.setdefault("_errors", []).append(r.status_code)
                    if rep == 0:
                        first.append(dt)
                    else:
                        lat.setdefault(q["group"], []).append(dt)
            t2 = time.perf_counter()
            r = cli.get("/doc/1?u=1")
            open_unit_ms = (time.perf_counter() - t2) * 1000
            mi = p.memory_info()
            rss_after = mi.rss
            peak = getattr(mi, "peak_wset", mi.rss)
    finally:
        proc.terminate()
        proc.wait(10)

    def stats(v: list[float]) -> dict:
        v = sorted(v)
        return {"n": len(v), "p50": round(statistics.median(v), 1),
                "p95": round(v[max(0, int(len(v) * 0.95) - 1)], 1), "max": round(v[-1], 1)}

    allv = [x for k, v in lat.items() if k != "_errors" for x in v]
    out = {
        "tag": tag, "cores": cores or "all", "startup_sec": round(startup, 2),
        "rss_idle_mb": round(rss_idle0 / 2**20, 1), "cpu_idle_pct": cpu_idle,
        "rss_after_mb": round(rss_after / 2**20, 1), "peak_mb": round(peak / 2**20, 1),
        "all": stats(allv), "first_pass": stats(first), "open_unit_ms": round(open_unit_ms, 1),
        "by_group": {k: stats(v) for k, v in lat.items() if k != "_errors"},
        "errors": lat.get("_errors", []), "sys_ram": sys_ram(),
    }
    (res / f"server_{tag}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[server {tag}] start {out['startup_sec']}s, idle {out['rss_idle_mb']} MB, "
          f"p50 {out['all']['p50']} ms, p95 {out['all']['p95']} ms, max {out['all']['max']} ms, peak {out['peak_mb']} MB")
    return out


def worker_extras(out_json: str) -> None:
    """Xuất Word 10 thẻ + sao lưu SQLite, đo thời gian."""
    from soiluat.app import _search_ctx
    from soiluat.config import data_dir, db_path
    from soiluat.db import backup_db
    from soiluat.export_word import export_cards

    cards = _search_ctx("phải báo cáo", "", "", "")["cards"][:10]
    t0 = time.perf_counter()
    export_cards(cards, data_dir() / "export.docx")
    t_exp = time.perf_counter() - t0
    t0 = time.perf_counter()
    backup_db(db_path(), data_dir() / "backup" / "soiluat.db")
    t_bak = time.perf_counter() - t0
    Path(out_json).write_text(json.dumps({"export_10_cards_sec": round(t_exp, 3), "backup_sec": round(t_bak, 3),
                                          "db_mb": round(db_path().stat().st_size / 2**20, 2)}), encoding="utf-8")


def main(demo: Path) -> None:
    res = demo / "results"
    res.mkdir(exist_ok=True)
    data = demo / "data"
    if data.exists():
        import shutil

        shutil.rmtree(data)
    m = {"machine": {"cpu": psutil.cpu_count(False), "threads": psutil.cpu_count(), **sys_ram()}}

    # 1) OCR khi máy thiếu Tesseract trên PATH (hành vi lỗi im lặng)
    run_import("ocr_no_path", [demo / "dirty" / "d05_pdf_scan_sach.pdf"], demo / "data_nopath", res, ocr=True, ocr_path=False)

    # 2) CLI thật trên thư mục bẩn: có dừng giữa chừng không?
    cli = subprocess.run([sys.executable, "-m", "soiluat.importer", str(demo / "dirty"), "--ocr"],
                         env=_env(demo / "data_cli", True), cwd=str(REPO), capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    cli_cp = subprocess.run([sys.executable, "-m", "soiluat.importer", str(demo / "dirty" / "d09_dinh_dang_le.docx")],
                            env={**_env(demo / "data_cli_cp1252", False), "PYTHONIOENCODING": "cp1252"},
                            cwd=str(REPO), capture_output=True, text=True, encoding="utf-8", errors="replace")
    (res / "cli_dirty.json").write_text(json.dumps({
        "rc": cli.returncode, "stderr_tail": cli.stderr[-1500:],
        "cp1252_rc": cli_cp.returncode, "cp1252_stderr_tail": cli_cp.stderr[-600:]}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"[cli dirty] rc={cli.returncode}  [cli cp1252 pipe] rc={cli_cp.returncode}")

    # 3) Kho tải
    sc = demo / "scale"
    run_import("docx", sorted((sc / "docx").glob("*.docx")), data, res, ocr=False)
    run_import("pdf_text", sorted((sc / "pdf_text").glob("*.pdf")), data, res, ocr=False)
    run_import("pdf_scan_ocr", sorted((sc / "pdf_scan").glob("*.pdf")), data, res, ocr=True)
    dirty = sorted(p for p in (demo / "dirty").rglob("*") if p.is_file())
    run_import("dirty", dirty, data, res, ocr=True)

    # 4) Chất lượng + độ trễ
    qs = build_queries(demo)
    qj = res / "queries.json"
    qj.write_text(json.dumps(qs, ensure_ascii=False, indent=1), encoding="utf-8")
    subprocess.run([sys.executable, __file__, "_quality", str(qj), str(res / "quality.json")],
                   env=_env(data, False), check=True)
    subprocess.run([sys.executable, __file__, "_extras", str(res / "extras.json")], env=_env(data, False), check=True)
    lat_qs = [q for q in qs if q["group"] != "dirty"]
    bench_server(data, res, lat_qs, "all_cores", None)
    bench_server(data, res, lat_qs, "2_threads", [0, 1])
    m["sys_ram_end"] = sys_ram()
    (res / "machine.json").write_text(json.dumps(m, indent=1), encoding="utf-8")
    print("xong ->", res)


if __name__ == "__main__":
    if sys.argv[1] == "_import":
        worker_import(*sys.argv[2:5])
    elif sys.argv[1] == "_quality":
        worker_quality(*sys.argv[2:4])
    elif sys.argv[1] == "_extras":
        worker_extras(sys.argv[2])
    elif sys.argv[1] == "_server":  # chạy lại riêng phần đo Search App
        demo = Path(sys.argv[2])
        res = demo / "results"
        lat = [q for q in json.loads((res / "queries.json").read_text(encoding="utf-8")) if q["group"] != "dirty"]
        bench_server(demo / "data", res, lat, "all_cores", None)
        bench_server(demo / "data", res, lat, "2_threads", [0, 1])
        m = {"machine": {"cpu": psutil.cpu_count(False), "threads": psutil.cpu_count(), **sys_ram()}}
        (res / "machine.json").write_text(json.dumps(m, indent=1), encoding="utf-8")
    else:
        main(Path(sys.argv[1]))
