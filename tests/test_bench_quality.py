"""bench/run_bench.py (worker_quality) và bench/doc_open.py: nhóm số hiệu chấm theo mục "Mở toàn văn"."""

import importlib.util
import json
import sys
import types
from pathlib import Path


def _load(monkeypatch, name):
    monkeypatch.setitem(sys.modules, "psutil", types.ModuleType("psutil"))  # máy kiểm thử không cài psutil, worker không dùng
    spec = importlib.util.spec_from_file_location("bench_" + name, Path(__file__).parents[1] / "bench" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_worker_quality_so_hieu_cham_theo_muc_mo_toan_van(db, sample_doc, tmp_path, monkeypatch):
    """Truy vấn chỉ có số hiệu không dựng thẻ (ctx["cards"] rỗng), chỉ có mục full: nhóm so_hieu không được tụt về 0."""
    monkeypatch.setenv("SOILUAT_DATA", str(tmp_path))
    so = "15/2020/NĐ-CP"
    want = [f"{so}#{k}" for k in range(1, 4)]
    qs = [{"group": "so_hieu", "q": so, "want": want}, {"group": "so_hieu", "q": "15/2020/nd-cp", "want": want},
          {"group": "so_hieu", "q": "99/2020/NĐ-CP", "want": want},  # số hiệu không có trong kho: không được tính trúng
          {"group": "dirty", "q": so, "file": "nd15.txt", "expect": f"so_hieu {so}", "note": ""}]
    (tmp_path / "q.json").write_text(json.dumps(qs, ensure_ascii=False), encoding="utf-8")
    _load(monkeypatch, "run_bench").worker_quality(str(tmp_path / "q.json"), str(tmp_path / "o.json"))
    out = json.loads((tmp_path / "o.json").read_text(encoding="utf-8"))
    assert [(r["hit10"], r["first_rel"]) for r in out[:3]] == [(True, 1), (True, 1), (False, None)]
    assert out[3]["found"] is True


def test_doc_open_khong_gui_u_rong_khi_van_ban_khong_co_don_vi(db, sample_doc, tmp_path):
    """GET /doc/{id}?u= trả 422; văn bản không đơn vị (bản quét chưa OCR) phải mở bằng /doc/{id} không tham số u."""
    import subprocess

    from soiluat.ingest import ingest_path

    p = tmp_path / "quet.txt"
    p.write_text("Nghị định số 7/2021/NĐ-CP\nĐiều 1. Phạm vi\n1. Phạt tiền theo quy định.\n", encoding="utf-8")
    quet = ingest_path(db, p, tmp_path)
    db.execute("DELETE FROM units WHERE doc_id = ?", (quet,))
    db.commit()
    data = tmp_path / "data"
    data.mkdir()
    db.execute("VACUUM INTO ?", (str(data / "soiluat.db"),))
    r = subprocess.run([sys.executable, "-I", str(Path(__file__).parents[1] / "bench" / "doc_open.py"), str(data), "--n", "5"],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr[-600:]
    assert json.loads(r.stdout)["so_van_ban"] == 2
