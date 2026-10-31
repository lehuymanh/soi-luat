"""Bảng so sánh cho KET-QUA.md, dựng thẳng từ JSON kết quả thô của run.py (không chép tay số).

python bench/llm/bang.py TEN=tep_zalo.json,tep_vle.json,tep_real.json [TEN2=...] [--gop]

Mỗi đối số là một cột: tên rồi ba tệp kết quả (Zalo, gold, văn bản thật; thiếu bộ nào thì bỏ trống ô đó).
--gop: thêm bảng gộp ba bộ (đếm câu, không lấy trung bình tỉ lệ).
Định nghĩa các chỉ số: README.md, mục "Đọc kết quả"; "khẳng định sai" = câu tu_choi có du_can_cu true và pham_vi
"đúng" (hoặc không có trường này).
"""

import json
import re
import sys
from pathlib import Path

CJK = re.compile("[⺀-鿿가-힯豈-﫿]")
BO = ["Zalo", "Gold `vle`", "Văn bản thật"]


def pc(xs) -> str:
    xs = list(xs)
    return f"{100 * sum(map(bool, xs)) / len(xs):.1f}%".replace(".", ",") if xs else "—"


def dem(d: dict) -> dict:
    R = d["tung_cau"]
    k = {t: [r for r in R if r["kind"] == t] for t in ("dan", "tu_choi", "bay")}
    sai = [r["raw"].get("du_can_cu") is True and r["raw"].get("pham_vi", "đúng") == "đúng" for r in k["tu_choi"]]
    return {
        "JSON đọc được (chưa cứu)": f"{pc(r['json_ok'] for r in R)} ({pc(r['json_ok'] and not r.get('cut') for r in R)})",
        "Bị cắt ở trần 200 token": pc((r.get("completion_tokens") or 0) >= 200 for r in R),
        "Dẫn đúng Điều": pc(r["ok"] for r in k["dan"]),
        "Dẫn đúng sau bộ kiểm": pc({n for y in r["checked"].get("cac_y", []) for n in y["nguon"]} & set(r["gold_n"])
                                   for r in k["dan"]),
        "Từ chối hẳn (`du_can_cu = false`)": pc(r["ok"] for r in k["tu_choi"]),
        "Từ chối hoặc nêu phạm vi hẹp hơn": pc(r["ok"] or r["raw"].get("pham_vi") in ("hẹp hơn", "khác")
                                              for r in k["tu_choi"]),
        "Khẳng định như đủ căn cứ khi đã bỏ Điều đúng": pc(sai),
        "Chỉ ra tiền đề sai (bẫy)": pc(r["ok"] for r in k["bay"]),
        "Số liệu khớp nguồn": pc(not any(x.endswith(":so") for x in r["dropped"]) for r in R if r["json_ok"]),
        "Có chữ Trung/Nhật/Hàn": pc(CJK.search(r["content"] or "") for r in R),
        "Token sinh ra, trung bình": str(round(sum(r.get("completion_tokens") or 0 for r in R) / len(R))),
        "Mô hình p50 / p95 trên máy chạy đo (s)": f"{d['tong']['llm_p50_s']:.0f} / {d['tong']['llm_p95_s']:.0f}",
    }


def gop(ds: list[dict]) -> dict:
    R = [r for d in ds for r in d["tung_cau"]]
    k = {t: [r for r in R if r["kind"] == t] for t in ("dan", "tu_choi", "bay")}
    def n(xs) -> str:
        xs = list(xs)
        return f"{sum(map(bool, xs))}/{len(xs)}"

    return {
        "Dẫn đúng Điều": n(r["ok"] for r in k["dan"]),
        "Khẳng định như đủ căn cứ khi đã bỏ Điều đúng": n(
            r["raw"].get("du_can_cu") is True and r["raw"].get("pham_vi", "đúng") == "đúng" for r in k["tu_choi"]),
        "Từ chối hoặc nêu phạm vi hẹp hơn": n(r["ok"] or r["raw"].get("pham_vi") in ("hẹp hơn", "khác")
                                             for r in k["tu_choi"]),
        "Từ chối hẳn": n(r["ok"] for r in k["tu_choi"]),
        "Chỉ ra tiền đề sai (bẫy)": n(r["ok"] for r in k["bay"]),
        "Bị cắt ở trần 200 token": n((r.get("completion_tokens") or 0) >= 200 for r in R),
    }


def main() -> None:
    cols = []
    for a in sys.argv[1:]:
        if a.startswith("--"):
            continue
        ten, tep = a.split("=", 1)
        files = [Path(f) if f else None for f in tep.split(",")]
        cols.append((ten, [json.load(open(f, encoding="utf-8")) if f and f.exists() else None for f in files]))
    cells = [(bo, ten, dem(d)) for i, bo in enumerate(BO) for ten, ds in cols
             if i < len(ds) and (d := ds[i]) is not None]
    print("| Chỉ số | " + " | ".join(f"{bo}: {ten}" for bo, ten, _ in cells) + " |")
    print("|---|" + "---|" * len(cells))
    for key in cells[0][2]:
        print(f"| {key} | " + " | ".join(m[key] for _, _, m in cells) + " |")
    if "--gop" in sys.argv:
        g = [(ten, gop([d for d in ds if d])) for ten, ds in cols]
        print("\n| Gộp ba bộ | " + " | ".join(t for t, _ in g) + " |")
        print("|---|" + "---|" * len(g))
        for key in g[0][1]:
            print(f"| {key} | " + " | ".join(m[key] for _, m in g) + " |")


if __name__ == "__main__":
    main()
