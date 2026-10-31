"""Nạp 10 file vào một kho (kèm kho nền để có nhiễu) rồi chạy truy vấn, đo có ra đúng thẻ trong top 10 không.

python bench/stress10/run.py DATA_DIR [KHO_NEN_soiluat.db]
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent.parent


def main(data: Path, base_db: Path | None) -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    shutil.rmtree(data, ignore_errors=True)
    data.mkdir(parents=True)
    if base_db:
        shutil.copy(base_db, data / "soiluat.db")
    os.environ["SOILUAT_DATA"] = str(data)
    os.environ["SOILUAT_ALLOW_TEST_HOST"] = "1"
    sys.path.insert(0, str(ROOT / "src"))
    r = subprocess.run([sys.executable, "-m", "soiluat.importer", str(HERE / "files"), "--ocr"],
                       capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONPATH=str(ROOT / "src")))
    print(r.stdout[-1500:], r.stderr[-500:])

    import sqlite3

    from soiluat import app as appmod

    c = sqlite3.connect(data / "soiluat.db")
    c.row_factory = sqlite3.Row
    print("\n== Cấu trúc đọc được ==")
    for d in c.execute("select id, file_path, loai, struct_score, fallback_doan from documents where file_path like '%stress10%' order by file_path"):
        n = c.execute("select level, count(*) n from units where doc_id=? group by level", (d["id"],)).fetchall()
        print(Path(d["file_path"]).name, "| loai:", d["loai"], "| điểm cấu trúc:", d["struct_score"], "| chia đoạn:", d["fallback_doan"], "|",
              {x["level"]: x["n"] for x in n})
    exp = json.loads((HERE / "expected.json").read_text(encoding="utf-8"))
    ok = 0
    print("\n== Truy vấn ==")
    for e in exp:
        # mục gọn (K2): trang chỉ hiện phần trích, nên xét cả chữ đầy đủ còn trong Card (duty_text, sanction_text, sample)
        cards = appmod._search_ctx(e["q"], "", "", "")["items"]
        pos = None
        for i, it in enumerate(cards[:10], start=1):
            txt = " ".join(getattr(it, k, "") for k in ("snippet", "duty_text", "sanction_text", "sample")).lower()
            if e["marker"].lower() in txt:
                pos = i
                break
        ok += pos is not None
        print(("ĐÚNG  vị trí %-2s" % pos if pos else "TRƯỢT        "), "|", e["file"], "|", e["q"], f"({len(cards)} thẻ)")
    print(f"\n{ok}/{len(exp)} truy vấn có thẻ đúng trong top 10")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) > 2 else None)
