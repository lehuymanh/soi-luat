# Number-check cases (expected results)

| Input | Expected |
|---|---|
| `Phạt từ 500.000 đến 1 triệu đồng` | {500000, 1000000} |
| `1.5 triệu đồng` | {1500000} |
| `0.5%` | {0.5} |
| `ngày 01.08.2030` | {'1/8/2030'} |
| `khoản 1, 2 và điểm a Điều 5` | {khoan:1, khoan:2, diem:a, dieu:5} |
| `Đoạn [1] và đoạn 2 nêu điều kiện` | {} (no numbers) |
| Source `[1] 36/2024/QH15 — Điều 8. Mức phạt` plus claim `Nộp phạt trong 15 ngày.` | claim dropped (15 comes from QH15) |
| Source `… 1. Phạt tiền từ 500.000 đồng …` plus claim `Thời hạn 1 ngày.` | claim dropped (1 comes from the khoản marker or [1]) |

The check goes through `numbers()` in `src/soiluat/answer.py`; run the answer tests after every change.
