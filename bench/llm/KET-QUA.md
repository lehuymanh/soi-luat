# Kết quả đo câu trả lời bằng LLM (P0, trên máy ảo)

30/10/2026. Bộ đo: [README.md](README.md). Mô hình chính: Qwen3-VL-4B-Instruct, GGUF Q4_K_M chính hãng (lý do chọn: [CHON-MO-HINH.md](CHON-MO-HINH.md)). Vòng 1: mã `9d4b7c7`; vòng 2 (sau bảy việc sửa): mã `b17461f`. Lời nhắc, khuôn JSON, bộ kiểm nằm trong `src/soiluat/answer.py`.

**Đây chưa phải số đo trên máy 16 GB.** Máy đo là máy ảo Linux 4 nhân (Xeon có AVX-512), 15 GB RAM, chạy llama-cpp-python 0.3.36 (bản mới nhất lúc đo; kiến trúc `qwen3vl` chỉ có trong llama.cpp từ 30/10/2025, xem CHON-MO-HINH.md), 4 luồng, nhiệt độ 0,1, seed 2026, cùng prompt và khuôn mà app sẽ dùng. Các tỉ lệ chất lượng không phụ thuộc máy nên dùng được cho quyết định; **thời gian thì không**: cổng 45 giây phải đo trên máy 16 GB theo README.

## Vòng 2: sau bảy việc sửa (30/10/2026)

Mã đo: commit `b17461f`. Mọi lựa chọn làm trên phần train (Zalo train; văn bản thật: các câu ngoài 15 câu test) hoặc offline, rồi chấm tập test **một lần**, cùng ba bộ và cùng mẫu câu như vòng 1. Cùng máy ảo, cùng llama-cpp-python 0.3.36, 4 luồng, nhiệt độ 0,1, seed 2026. **Ngoại lệ: câu bẫy.** Câu bẫy sinh từ kho, không chia train/test, nên 6 câu bẫy dùng ở A/B (và ở các lần chỉnh của vòng 1) nằm trong 20 câu bẫy của tập test. Số bẫy trên test vì thế không hoàn toàn chưa thấy. Việc chọn biến thể không dựa vào bẫy: bẫy 5/6 ở cả ba biến thể.

### Bảy việc đã làm và số đo trước khi chấm test

| Việc | Đã làm | Số đo (train hoặc offline, không phải chất lượng báo cáo) |
|---|---|---|
| 1. Ngữ cảnh cho Điều dài | Dòng dài hơn 300 ký tự (bản OCR dính nhiều khoản/điểm thành một dòng 1.500–10.000 ký tự) tách theo câu; câu đầu dòng là câu dẫn, đi theo mọi câu được giữ; nhãn giữa dòng ("b) Đối với tổ chức:") gộp với câu sau. Chấm dòng theo độ hiếm trong Điều (IDF, mỗi dòng là một tài liệu). Câu khớp nhất dài hơn phần ngân sách còn lại thì lấy khúc quanh chỗ khớp. Ngân sách 2.600 → 2.400 ký tự để độ dài ngữ cảnh giữ như cũ. Thêm chỉ số `dan_bang_chung_con`. | Offline, 66 câu train văn bản thật có câu trích bằng chứng: câu trích còn ≥ 50% trong đoạn **53% → 80%** (Advance), **53% → 82%** (Normal) với ngữ cảnh tự nhiên (không chèn Điều đúng); khi chèn Điều đúng như phép `dan`: 55% → 82% / 83%, câu còn dưới 10% từ 29% xuống 6%. Độ dài ngữ cảnh 2.658 ký tự (vòng 1: 2.657). Chỉ đổi cách chấm (IDF trong Điều, IDF toàn kho, BM25) mà không tách câu thì gần như không đổi (+1 câu); đưa 3 đoạn thay 5 không thêm gì khi đã tách câu, nên giữ 5. |
| 2. Hết cắt JSON | Câu bị cắt ở trần 200 token giữ các ý đã viết xong (ý đang dở bỏ cả), không còn thay bằng trích nguyên văn; trần độ dài tiền đề sai 200 → 150, câu trả lời 320 → 240 ký tự (p95 đo trên train 101 và 191). Chuỗi chạm trần bị grammar cắt giữa chữ: bộ kiểm bỏ chữ cuối đang dở. | 7/7 câu bị cắt trong các lần chạy train vòng 1 cứu được, cả 7 còn ít nhất một ý. Train vòng 2 (126 lần gọi, ba biến thể): bị cắt 2–4/30 ở Zalo, 0/12 ở văn bản thật; đọc được sau khi cứu **100%**. |
| 3. Kiểm phạm vi | Trường `pham_vi` (đúng / hẹp hơn / khác) sinh trước `du_can_cu`. Đoạn chỉ nói trường hợp hẹp hơn điều được hỏi thì vẫn trả lời, nói rõ phạm vi; giao diện phải hiện cảnh báo. Ví dụ trong lời nhắc là ví dụ chung, không lấy từ các câu test đã soát ở vòng 1. | A/B dưới đây. |
| 4. Chặn chữ CJK khi sinh | Mọi chuỗi trong khuôn JSON có `pattern` loại chữ Trung/Nhật/Hàn và lối viết `\uXXXX`; trần độ dài ghi trong pattern (llama.cpp bỏ qua `maxLength` khi có `pattern`). | Câu hỏi cố tình đòi trả lời tiếng Trung: không còn chữ CJK (mô hình chuyển sang tiếng Anh/Việt). Tốc độ không đổi (23,6 s so với 24,3 s cùng câu). 126 lần gọi train: 0% CJK. |
| 5. Bộ kiểm tham chiếu | "khoản a" là điểm a; số hiệu bị cắt cụt khớp theo phần đầu; phía nguồn đọc số viết bằng chữ ("dưới mười lăm tuổi" cho phép 15; "mười năm" là 10, không phải 15). | Chẩn đoán, giữ nguyên câu trả lời vòng 1 trên tập test, chỉ thay bộ kiểm và phần cứu JSON: dẫn đúng sau kiểm 20 → 23/30 (Zalo), 12 → 16/20 (gold), 7 → 8/15 (văn bản thật); ý bị bỏ vì "số lạ" ở gold 6 → 1. |
| 6. Gemma 4 E4B | GGUF QAT Q4_0 chính hãng (5,15 GB). Mẫu hội thoại của GGUF dựng được trong llama-cpp-python (có vai system). Cùng lời nhắc, khuôn, bộ kiểm với Qwen; không chỉnh riêng. | Chạy thử 5 lần gọi train: 5/5 đúng, JSON đọc được 5/5 (1 câu bị cắt đã cứu), ~67 s/lần gọi trên máy ảo (Qwen ~55 s). |
| 7. Máy 16 GB, ≥ 100 câu | Chưa đo được ở đây: cần máy của văn phòng. README có lệnh cho cả hai mô hình, cỡ mẫu 100 câu. | — |

**A/B việc 3** (train: Zalo 12 câu + 6 bẫy; văn bản thật 6 câu; cùng mẫu; mã `7aec13f`; "khẳng định sai" = câu `tu_choi` trả lời đủ căn cứ với `pham_vi` "đúng", tức khẳng định như có căn cứ khi Điều đúng đã bị bỏ):

| Biến thể | Dẫn đúng | Từ chối hẳn (`du_can_cu = false`) | Khẳng định sai | Bẫy | Bị cắt |
|---|---|---|---|---|---|
| Không có `pham_vi` | 10/12 · 4/6 | 4/12 · 5/6 | 8/12 · 1/6 | 5/6 | 2/30 · 0/12 |
| "hẹp hơn" buộc từ chối | 10/12 · 4/6 | 5/12 · 5/6 | 7/12 · 1/6 | 5/6 | 3/30 · 0/12 |
| **"hẹp hơn" vẫn trả lời, nói rõ phạm vi (chọn)** | 10/12 · 4/6 | 2/12 · 3/6 | **5/12 · 1/6** | 5/6 | 4/30 · 0/12 |

(số "a · b": Zalo · văn bản thật)

Chọn biến thể cuối vì ít câu khẳng định sai nhất trên train, và đây là thiết kế đã ghi ở việc 3 của vòng 1. Khi "hẹp hơn" buộc từ chối, mô hình né nhãn đó (3/12 câu so với 6/12) và trả lời "đúng" nhiều hơn. Đọc lại 8 câu được gắn "hẹp hơn" khi Điều đúng đã bị bỏ: 5/8 câu nói rõ đoạn không quy định hoặc không áp dụng cho điều được hỏi ("Đoạn văn không quy định về mức phạt đối với trung tâm sát hạch lái xe khi có trên 50% số xe không bảo đảm điều kiện. Chỉ quy định trách nhiệm về cơ sở vật chất…"); 3/8 vẫn trả lời kèm giới hạn phạm vi (mức thưởng tối đa "chỉ áp dụng với quyết định của Bộ trưởng Bộ Công an"). Cái giá: từ chối hẳn giảm, nên chỉ số `tu_choi_dung` của cổng P0 thấp đi; phải tính `tu_choi_hoac_neu_hep` mới phản ánh đúng hành vi. Cách tính cổng là việc người dùng chốt (lộ trình mục 9).

**Soát độc lập** (4 góc nhìn: cứu JSON, bộ kiểm số, dựng ngữ cảnh, grammar và bộ đo; mỗi phát hiện được một tác tử khác kiểm chứng ngược): 6/15 phát hiện là thật, đã sửa, mỗi lỗi có test hỏng trên mã cũ (commit `131ca78`). Hai lỗi nặng: "mười năm" đọc thành 15, và câu khớp nhất quá dài bị bỏ khiến đoạn gần như rỗng. Bản đầu của phần sửa bỏ hẳn tách ở dấu hai chấm làm câu còn bằng chứng tụt 80% → 71% trên train; bản cuối giữ tách câu dẫn đầu dòng, chỉ gộp nhãn giữa dòng, và lấy lại 80%.

### Kết quả trên tập test

**Qwen3-VL-4B, vòng 1 → vòng 2** (cùng mẫu câu; Zalo 30 câu + 20 bẫy, gold 20, văn bản thật 15; mỗi câu hai lần gọi `dan` và `tu_choi`):

| Chỉ số | Zalo: v1 | Zalo: v2 | Gold `vle`: v1 | Gold `vle`: v2 | Văn bản thật: v1 | Văn bản thật: v2 |
|---|---|---|---|---|---|---|
| JSON đọc được (chưa cứu) | 87,5% (87,5%) | 100,0% (78,8%) | 92,5% (92,5%) | 100,0% (95,0%) | 96,7% (96,7%) | 100,0% (96,7%) |
| Bị cắt ở trần 200 token | 13,8% | 21,3% | 7,5% | 5,0% | 3,3% | 3,3% |
| Dẫn đúng Điều | 66,7% | 83,3% | 70,0% | 75,0% | 46,7% | 86,7% |
| Dẫn đúng sau bộ kiểm | 66,7% | 80,0% | 60,0% | 75,0% | 46,7% | 86,7% |
| Từ chối hẳn (`du_can_cu = false`) | 26,7% | 16,7% | 35,0% | 20,0% | 66,7% | 60,0% |
| Từ chối hoặc nêu phạm vi hẹp hơn | 26,7% | 73,3% | 35,0% | 60,0% | 66,7% | 86,7% |
| Khẳng định như đủ căn cứ khi đã bỏ Điều đúng | 66,7% | 26,7% | 65,0% | 40,0% | 33,3% | 13,3% |
| Có Điều đúng mà bị gắn "hẹp hơn"/"khác" | — | 26,7% | — | 10,0% | — | 40,0% |
| Chỉ ra tiền đề sai (bẫy) | 75,0% | 85,0% | — | — | — | — |
| Số liệu khớp nguồn | 95,7% | 98,8% | 83,8% | 100,0% | 96,6% | 100,0% |
| Có chữ Trung/Nhật/Hàn | 3,8% | 0,0% | 10,0% | 0,0% | 0,0% | 0,0% |
| Phải thay bằng trích nguyên văn | 12,5% | 0,0% | 12,5% | 0,0% | 3,3% | 0,0% |
| Token sinh ra, trung bình | 137 | 155 | 127 | 137 | 93 | 118 |
| Mô hình p50 / p95 trên máy ảo (s) | 72 / 93 | 57 / 72 | 63 / 81 | 53 / 71 | 57 / 85 | 49 / 68 |

(cột "JSON đọc được": tính cả câu bị cắt đã cứu; trong ngoặc là JSON đọc được ngay, không cần cứu. p50/p95 tính như `run.py`: phần tử thứ ⌊n·p⌋ của dãy đã xếp; với 30–80 lần gọi, p95 là giá trị lớn thứ 2–4 nên rất nhiễu. Thời gian không so được giữa hai vòng: máy ảo dùng chung, tải khác nhau.)

**Ba mô hình, cùng mã vòng 2, cùng mẫu câu.** Gemma 4 E4B là bản QAT Q4_0 chính hãng (dự phòng từ đầu). Nemotron-3.5-Bolt-E4B (bartowski Q4_K_M 5,16 GB) là ứng viên mới tìm thêm theo yêu cầu của người dùng (`CHON-MO-HINH.md` mục 7). Cả ba dùng cùng lời nhắc, khuôn, bộ kiểm, nhiệt độ 0,1; không chỉnh riêng cho mô hình nào.

Gộp ba bộ (65 câu `dan`, 65 câu `tu_choi`, 20 câu bẫy, 150 lần gọi):

| | Qwen3-VL-4B | Gemma 4 E4B | Nemotron-3.5-Bolt-E4B |
|---|---|---|---|
| Dẫn đúng Điều | **53/65 (81,5%)** | 48/65 (73,8%) | 44/65 (67,7%) |
| Khẳng định như đủ căn cứ khi đã bỏ Điều đúng | **18/65 (27,7%)** | 19/65 (29,2%) | 24/65 (36,9%) |
| Từ chối hoặc nêu phạm vi hẹp hơn | **47/65 (72,3%)** | 46/65 (70,8%) | 41/65 (63,1%) |
| Từ chối hẳn (`du_can_cu = false`) | 18/65 | **36/65** | 34/65 |
| Chỉ ra tiền đề sai (bẫy) | 17/20 | **19/20** | 17/20 |
| Bị cắt ở trần 200 token | **20/150** | 39/150 | 31/150 |
| Mô hình p50 trên máy ảo (Zalo / gold / văn bản thật) | **57 / 53 / 49 s** | 73 / 69 / 67 s | 74 / 65 / 67 s |

Từng bộ:

| Chỉ số | Zalo: Qwen | Zalo: Gemma | Zalo: Bolt | Gold `vle`: Qwen | Gold `vle`: Gemma | Gold `vle`: Bolt | Văn bản thật: Qwen | Văn bản thật: Gemma | Văn bản thật: Bolt |
|---|---|---|---|---|---|---|---|---|---|
| JSON đọc được (chưa cứu) | 100,0% (78,8%) | 100,0% (63,8%) | 98,8% (65,0%) | 100,0% (95,0%) | 100,0% (82,5%) | 100,0% (95,0%) | 100,0% (96,7%) | 100,0% (96,7%) | 100,0% (100,0%) |
| Bị cắt ở trần 200 token | 21,3% | 38,8% | 36,3% | 5,0% | 17,5% | 5,0% | 3,3% | 3,3% | 0,0% |
| Dẫn đúng Điều | 83,3% | 63,3% | 56,7% | 75,0% | 85,0% | 75,0% | 86,7% | 80,0% | 80,0% |
| Dẫn đúng sau bộ kiểm | 80,0% | 63,3% | 56,7% | 75,0% | 85,0% | 75,0% | 86,7% | 80,0% | 80,0% |
| Từ chối hẳn (`du_can_cu = false`) | 16,7% | 46,7% | 40,0% | 20,0% | 55,0% | 55,0% | 60,0% | 73,3% | 73,3% |
| Từ chối hoặc nêu phạm vi hẹp hơn | 73,3% | 66,7% | 56,7% | 60,0% | 60,0% | 65,0% | 86,7% | 93,3% | 73,3% |
| Khẳng định như đủ căn cứ khi đã bỏ Điều đúng | 26,7% | 33,3% | 43,3% | 40,0% | 40,0% | 35,0% | 13,3% | 6,7% | 26,7% |
| Có Điều đúng mà bị gắn "hẹp hơn"/"khác" | 26,7% | 26,7% | 30,0% | 10,0% | 10,0% | 10,0% | 40,0% | 20,0% | 20,0% |
| Chỉ ra tiền đề sai (bẫy) | 85,0% | 95,0% | 85,0% | — | — | — | — | — | — |
| Số liệu khớp nguồn | 98,8% | 100,0% | 97,5% | 100,0% | 100,0% | 100,0% | 100,0% | 100,0% | 96,7% |
| Có chữ Trung/Nhật/Hàn | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% |
| Phải thay bằng trích nguyên văn | 0,0% | 0,0% | 2,5% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% |
| Token sinh ra, trung bình | 155 | 170 | 166 | 137 | 164 | 146 | 118 | 138 | 136 |
| Mô hình p50 / p95 trên máy ảo (s) | 57 / 72 | 73 / 89 | 74 / 94 | 53 / 71 | 69 / 83 | 65 / 81 | 49 / 68 | 67 / 80 | 67 / 82 |

- **Giữ Qwen3-VL-4B làm mô hình chính.** Qwen dẫn đúng nhiều nhất khi gộp, khẳng định sai ngang Gemma (18 so với 19/65) và ít hơn Bolt (24/65), viết ngắn nhất, tốn ít thời gian hơn ~20–27% (p50 từng bộ), và tệp nhỏ bằng nửa (2,5 GB so với ~5,2 GB). **Chênh lệch chất lượng giữa ba mô hình chưa vượt nhiễu** (kiểm McNemar ghép cặp trên 65 câu `dan`: Qwen–Gemma p = 0,30, Qwen–Bolt p = 0,06), nên lý do chọn dựa nhiều vào tốc độ và RAM. Thời gian chỉ so tương đối: ba mô hình chạy ở các giờ khác nhau trên máy ảo dùng chung, và Qwen sinh ít token hơn.
- **Gemma 4 E4B** hơn ở gold (dẫn đúng 17 so với 15/20) và ở câu bẫy (19 so với 17/20), đều trong nhiễu, và từ chối hẳn nhiều gấp đôi (36 so với 18/65). Nhưng Gemma kém ở Zalo (19 so với 25/30) và khẳng định sai ngang Qwen: không sửa được lỗi phạm vi. Ở Zalo, Gemma dẫn sai 11 câu: 5 câu từ chối dù có Điều đúng (4 câu gắn "khác"); 3 câu bị cắt, mỗi câu còn 1 ý nhưng dẫn đoạn khác; 3 câu dẫn nhầm đoạn.
- **Nemotron-3.5-Bolt-E4B kém nhất khi gộp** (dẫn đúng 44/65, khẳng định sai 24/65), nhưng không đều theo bộ: ở gold Bolt dẫn đúng bằng Qwen và khẳng định sai thấp nhất (35%); ở văn bản thật dẫn đúng bằng Gemma. Bolt là Gemma 4 E4B được NVIDIA huấn luyện thêm, nhưng trên bộ này không hơn Gemma 4 E4B gốc (bản gốc là QAT Q4_0, Bolt là Q4_K_M, nên không cùng cách lượng tử hóa). Mức tăng bám ngữ cảnh NVIDIA công bố bằng tiếng Anh không thấy ở đây, khớp với phép thử RAG tiếng Hàn độc lập ghi ở `CHON-MO-HINH.md` mục 7. Không đề xuất đo tiếp trên máy 16 GB.
- Gộp ba bộ, cả ba mô hình đều khẳng định sai ở 28–37% số câu khi đã bỏ Điều đúng. Đổi mô hình cùng cỡ không giải quyết lỗi này; hướng tiếp theo nằm ở mã và luồng (bước kiểm phạm vi riêng, tín hiệu điểm tìm kiếm thấp; xem việc tiếp theo bên dưới).

**Đọc kết quả (Qwen):**

- **Dẫn đúng Điều tăng rõ ở Zalo (20 → 25/30) và văn bản thật (7 → 13/15)**, qua ngưỡng 80% ở cả hai; gold chỉ tăng 1 câu (14 → 15/20), trong nhiễu. Trên văn bản thật, câu trích bằng chứng còn ≥ 50% trong đoạn ở 9/15 câu (vòng 1, dựng lại đúng ngữ cảnh cũ: 7/15). Trong 6 câu văn bản thật đổi từ sai sang đúng: 1 câu nhờ cứu JSON, 3 câu từ từ chối chuyển sang trả lời đúng, 2 câu từ dẫn nhầm Điều sang dẫn đúng. Không tách được phần của từng việc sửa (ngữ cảnh mới, trường phạm vi, lời nhắc) vì test không chạy bỏ từng phần; bộ kiểm không ảnh hưởng chỉ số này (chấm trước bộ kiểm).
- **Khẳng định sai khi đã bỏ Điều đúng giảm ở cả ba bộ, rõ nhất ở Zalo:** 20 → 8/30 (Zalo), 13 → 8/20 (gold), 5 → 2/15 (văn bản thật; trong nhiễu). Đổi lại, từ chối hẳn giảm vì "hẹp hơn" được trả lời kèm phạm vi; tính cả câu nêu phạm vi hẹp hơn thì 73,3 / 60 / 86,7%. Cái giá thứ hai: câu có Điều đúng cũng bị gắn "hẹp hơn"/"khác" ở 26,7 / 10 / 40% số câu, tức giao diện sẽ hiện cảnh báo thừa ở những câu đó.
- **JSON dùng được 100% ở cả ba bộ** (vòng 1: 87,5 / 92,5 / 96,7%). Nhưng bị cắt lại nhiều hơn ở Zalo (21,3%): **cả 17 lần bị cắt đều là câu bẫy** (17/20 câu bẫy), 15 trong số đó mất hết ý có nguồn. Câu bẫy vẫn đúng 15/17 vì chấm theo tiền đề sai, nhưng câu trả lời không còn chip dẫn nguồn. Câu thường không bị cắt lần nào ở Zalo.
- Chữ Trung/Nhật/Hàn 0% (vòng 1: 3,8 / 10 / 0%); không câu nào phải thay bằng trích nguyên văn (vòng 1: 12,5 / 12,5 / 3,3%); số liệu khớp nguồn 98,8–100%.
- Cỡ mẫu nhỏ (15–30 câu mỗi bộ; khoảng tin cậy 95% xấu nhất ±18–25 điểm): chênh 1–2 câu không có nghĩa; mức tăng dẫn đúng ở Zalo và văn bản thật, mức giảm khẳng định sai ở Zalo thì vượt nhiễu.

**So với cổng P0 đề xuất:** dẫn đúng ≥ 80% đạt ở 2/3 bộ; JSON ≥ 99% đạt nếu tính câu đã cứu, không đạt nếu tính đọc ngay (78,8% ở Zalo do câu bẫy); từ chối ≥ 80% không đạt theo cách tính cũ (`du_can_cu = false`), đạt ở văn bản thật nếu tính cả câu nêu phạm vi hẹp hơn. Hai cách tính này là quyết định của người dùng (lộ trình mục 9).

**Việc tiếp theo** (chỉnh trên train, chấm lại test một lần):

1. **Câu bẫy chạm trần token:** tiền đề sai và câu trả lời nhắc lại cùng mức phạt. Hạ trần `tra_loi` khi đã có `tien_de_sai`, hoặc đưa `cac_y` lên trước `tra_loi`, để ý có nguồn không bị cắt.
2. **Lỗi phạm vi còn 13–40% tùy bộ** (gộp 28–37% ở cả ba mô hình) và đổi mô hình cùng cỡ không sửa được. Hai hướng đo được trên train: (a) dùng điểm tìm kiếm/reranker thấp làm tín hiệu "có thể không đúng trường hợp" để hiện cảnh báo, không cần gọi thêm mô hình; (b) bước kiểm phạm vi thứ hai bằng mô hình rất nhỏ (ứng viên: LFM3-1.7B, `CHON-MO-HINH.md` mục 7; giấy phép có trần doanh thu), chỉ khi còn ngân sách 45 giây.
3. **Cảnh báo thừa:** 10–40% câu có Điều đúng bị gắn "hẹp hơn"/"khác". Cần xem trên giao diện P3 cảnh báo có gây khó chịu không, hoặc chỉ hiện khi kèm tín hiệu (a).
4. **Tách câu bẫy train/test** (`traps` sinh từ cả kho): bỏ khỏi phần chỉnh các điểm dùng làm bẫy ở test.
5. **Máy 16 GB** (README): tốc độ, RAM, p95 45 giây; cỡ mẫu ≥ 100 câu khi có câu hỏi thật của văn phòng.

## Vòng 1 (commit `9d4b7c7`)

### Cách chọn cấu hình trước khi đo (tập train, không báo cáo làm chất lượng)

Mọi lựa chọn dưới đây làm trên câu hỏi **train** của Zalo, rồi mới chấm một lần trên tập **test**:

| Thay đổi | Lý do (đo trên train) |
|---|---|
| Giữ câu dẫn của khoản khi giữ một điểm | Lần chạy thử đầu: 2/3 câu bẫy sai, cả hai vì cắt mất dòng "Phạt tiền từ … đối với các hành vi sau": điểm còn mà mức phạt mất |
| Gộp Điều trùng nội dung trong ngữ cảnh | Kho Zalo có văn bản chép lại y nguyên (`63/2019/NĐ-` và `63/2019/NĐ-CP`), tốn chỗ của Điều khác |
| Ngân sách ngữ cảnh 2.600 ký tự | Đo `prompt_tokens`: chữ luật kèm tiêu đề ~3,1 ký tự/token, nên 3.000 ký tự thành ~1.150 token mới, vượt trần ~1.000 token |
| JSON schema hai nhánh theo `du_can_cu` | Lần đầu mô hình trả lời đúng nhưng để trống `cac_y` (không dẫn nguồn) |
| `tien_de_sai` đứng trước `du_can_cu` | A/B cùng mẫu (8 câu + 6 bẫy): bẫy 6/6 so với 5/6; câu hỏi nêu sai mức phạt vẫn được dẫn nguồn |
| Trần độ dài (`maxLength`, tối đa 2 ý) | 6/44 câu ở A/B hỏng JSON, cả 6 do bị cắt ở 200 token |

### Kết quả trên tập test

Mỗi câu hỏi được gọi hai lần: `dan` (Điều đúng có trong ngữ cảnh) và `tu_choi` (đã bỏ Điều đúng và các bản gần như cùng chữ). Câu bẫy tiền đề sai (`bay`) chỉ sinh được trên kho Zalo (các điểm có mức phạt). Mỗi bộ chấm một lần trên mã cuối.

| Chỉ số | Zalo test | Gold `vle` | Văn bản thật | Cổng P0 (đề xuất) |
|---|---|---|---|---|
| Số câu (lần gọi) | 30 + 20 bẫy (80) | 20 (40) | 15 (30) | |
| Tìm kiếm cho ngữ cảnh | Normal | Normal | Advance | |
| JSON hợp lệ | 87,5% | 92,5% | 96,7% | ≥ 99% |
| Dẫn đúng Điều (`dan`) | 66,7% | 70,0% | 46,7% | ≥ 80% |
| Dẫn đúng, chỉ tính câu JSON hợp lệ | 77% (20/26) | 82% (14/17) | 50% (7/14) | |
| Dẫn đúng sau bộ kiểm | 66,7% | 60,0% | 46,7% | |
| Từ chối đúng (`tu_choi`) | 26,7% | 35,0% | 66,7% | ≥ 80% |
| Chỉ ra tiền đề sai (`bay`) | 75,0% (15/20) | — | — | |
| Gắn tiền đề sai cho câu bình thường | 6,7% | 0% | 0% | |
| Số liệu khớp nguồn (`so_khop`) | 95,7% | 83,8% | 96,6% | |
| Có chữ Trung/Nhật/Hàn | 3,8% (3/80) | 10,0% (4/40) | 0% | |
| Phải thay bằng trích nguyên văn | 12,5% | 12,5% | 3,3% | |
| Câu trả lời quá 3 câu | 0% | 0% | 0% | |
| Điều đúng do tìm kiếm đưa vào top 5 | 76,7% | 85,0% | 93,3% | |
| Token mới mỗi câu, trung vị (p95); lời nhắc cố định 383 token đã cache | ~935 (1.110) | ~850 (930) | ~955 (1.027) | ~1.000 |
| Token sinh ra (trung bình; trần 200) | 137 | 127 | 93 | |
| Thời gian mô hình p50 / p95, máy ảo (phần tử thứ ⌊n·p⌋ của dãy đã xếp, như `run.py`) | 71,8 / 93,2 s | 63,4 / 81,5 s | 57,1 / 85,0 s (thêm tìm Advance p50 9,9 s) | |

Tốc độ máy ảo (llama-cpp-python, 4 luồng), từ log máy chủ của 72 lần gọi ở gold và văn bản thật (log của lần chạy Zalo đã bị ghi đè): đọc prompt ~27 token/giây, sinh ~5,2 token/giây (trung vị). RSS của tiến trình máy chủ đo bằng `ps` lúc chạy ~6,5 GB; log ghi ~4,9 GiB bộ đệm (mô hình 2,4 GiB nạp bằng mmap, bản sắp xếp lại trọng số cho CPU 1,7 GiB, KV 0,6 GiB, tính toán 0,3 GiB). Không đại diện cho `llama-server` trên máy 16 GB.

### Đọc kết quả

- **Mọi JSON hỏng đều do bị cắt ở 200 token** (10/80 lần gọi ở Zalo, 3/40 ở gold, 1/30 ở văn bản thật; cả 14 đều sinh đúng 200 token). 13/14 câu bị cắt khi đang viết một ý (9 câu ở ý thứ hai), chỉ 1 câu tới được lưu ý. Tổng các trần `maxLength` là 1.000 ký tự, tức ~330–400 token (chữ trong JSON đo được 2,5–3 ký tự/token), nên trần chưa ngăn được cắt. Chỉ tính câu JSON hợp lệ thì dẫn đúng là 77% (Zalo), 82% (gold), 50% (văn bản thật) và chỉ ra tiền đề sai là 15/16; đây là tỉ lệ trên phần còn lại, chưa phải số đo sau khi hết cắt.
- **Từ chối là chỗ yếu chính.** Khi đã bỏ Điều đúng, mô hình vẫn nói "đủ căn cứ" ở 20/28 câu JSON hợp lệ ở Zalo và 13/20 ở gold. Mục soát dưới đây (giám khảo là mô hình) cho thấy nhóm lớn nhất là khái quát quá phạm vi đoạn, không phải bịa từ đầu.
- **Bộ kiểm số liệu chặn đúng thứ cần chặn nhưng còn quá chặt ở tham chiếu.** Trên gold, 6 lần bị bỏ ý vì "số lạ", không lần nào là số tiền bịa: mô hình viết "khoản a" thay cho "điểm a"; nhắc lại "dưới 15 tuổi" của câu hỏi trong một ý (văn bản viết "mười lăm" bằng chữ, bộ kiểm chưa đọc số viết bằng chữ); số hiệu bị trần 160 ký tự của một ý cắt cụt ("155/2020/NĐ-"); dẫn "Điều 14" không có trong các đoạn được dẫn. Vì vậy "dẫn đúng sau bộ kiểm" ở gold thấp hơn 10 điểm.
- **Chữ Trung lẫn vào 0–10% câu trả lời** (3,8% Zalo, 10% gold, 0% văn bản thật) ("mũ坚硬", "thẩm权", "quy规划"), đúng rủi ro đã ghi ở CHON-MO-HINH.md. Bộ kiểm đã chặn: ý bị bỏ, câu trả lời bị thay bằng trích nguyên văn.
- **Trên văn bản thật, dẫn đúng chỉ 46,7%, và một phần lớn không do mô hình.** Bộ câu hỏi này có sẵn câu trích bằng chứng của đáp án (`queries.json`, trường `evidence`). Ở 5/7 câu dẫn sai (JSON hợp lệ), đoạn sau khi cắt chỉ còn ≤ 31% bộ 3-từ của câu trích đó (3 câu dưới 10%); 2 câu còn lại có đủ câu trích (lỗi mô hình). Ở 5/7 câu đúng, câu trích còn ≥ 50%. Nguyên nhân: Điều của văn bản 2026 dài (bản scan, OCR), mỗi đoạn chỉ được ~520 ký tự, và dòng được giữ chọn theo số từ trùng câu hỏi chứ không theo độ hiếm. Ví dụ "thời gian thí điểm cơ chế chính sách": 7/22 dòng của Điều 8 có cụm "thí điểm cơ chế", còn dòng có đáp án ("Thời gian thí điểm không quá 05 năm…") bị cắt. Từ chối đúng ở bộ này là 66,7% (10/15); kho, chế độ tìm và cỡ mẫu khác hẳn nên không so trực tiếp với Zalo và gold.
- Gắn nhầm tiền đề sai cho câu hỏi bình thường hiếm (0–6,7%); câu trả lời không bao giờ quá 3 câu.

### Soát các câu từ chối sai (giám khảo là mô hình Claude, không phải người, không phải chấm máy)

Mỗi câu `tu_choi` bị chấm sai được hai giám khảo độc lập (mô hình Claude, cùng một tiêu chí) đọc đúng ngữ cảnh mô hình đã thấy và câu trả lời, rồi xếp: **hỗ trợ** (mọi ý đều có trong các đoạn còn lại, từ văn bản hay phiên bản khác: nhiễu của bộ đo, không phải ảo giác), **một phần** (đúng chủ đề nhưng có ý không có trong đoạn, hoặc đoạn chỉ nói về trường hợp hẹp hơn câu hỏi), **không hỗ trợ** (ý chính không có trong đoạn: bịa câu trả lời, bịa số hiệu/Điều, hoặc trả lời câu khác). Đây là đánh giá bổ sung bằng mô hình, không thay cho số chấm máy ở trên.

| Bộ | Câu từ chối sai | Hỗ trợ | Một phần | Không hỗ trợ | Hai giám khảo đồng ý |
|---|---|---|---|---|---|
| Zalo test | 22 | 4 / 5 | 12 / 13 | 6 / 4 | 17/22 |
| Gold `vle` | 13 | 3 / 3 | 6 / 6 | 4 / 4 | 13/13 |
| Văn bản thật | 5 | 0 / 0 | 4 / 4 | 1 / 1 | 5/5 |

(số "a / b": giám khảo 1 / giám khảo 2)

- Tính câu "hỗ trợ" là trả lời được thì từ chối đúng ước ~40–43% ở Zalo, ~50% ở gold, giữ 66,7% ở văn bản thật (không câu nào "hỗ trợ"): vẫn xa ngưỡng 80%. Danh sách 22 câu của Zalo có 2 câu JSON bị cắt (phần đã sinh vẫn nói đủ căn cứ).
- **Nhóm lớn nhất là khái quát quá phạm vi đoạn** ("một phần": 22–23/40 câu khi gộp ba bộ; đa số ở Zalo và văn bản thật, nhóm lớn nhất ở gold). Ví dụ cả hai giám khảo cùng xếp "một phần": hỏi phạt ô tô vượt đèn đỏ, mô hình lấy mức chỉ áp dụng tại đường ngang, cầu chung; hỏi ô tô quá tốc độ, lấy mức chỉ áp dụng trong vùng đất cảng; lấy quy định cho công chức trả lời về viên chức; lấy quy định về Kỷ niệm chương để nói chung cho mọi hình thức khen thưởng. Bộ kiểm số không bắt được loại này vì con số đúng là có trong đoạn.
- Nhóm "không hỗ trợ" gồm dẫn một Điều không liên quan làm căn cứ (Điều 2 Thông tư 107/2016/TT-BQP, về quân nhân phục viên, cho câu hỏi BHYT con bệnh binh), nhầm "chi phí" thành "vốn hoạt động", và trả lời câu khác (hỏi tín chấp, trả lời thế chấp).

### Việc cho P3 (rút ra từ vòng này)

Cả bảy việc đã làm ở vòng 2 (mục trên); việc 7 (máy 16 GB) còn chờ máy của văn phòng.

Theo cổng P0, Qwen3-VL-4B **chưa đạt** ở vòng này: JSON, dẫn đúng và từ chối đều dưới ngưỡng đề xuất ở cả ba bộ. Một phần lỗi nằm ở mã của ta (cắt JSON, cắt mất dòng đáp án), sửa được trước khi kết luận về mô hình. Lộ trình quy định thử mô hình dự phòng trước khi kết luận. Việc tiếp theo, chỉnh trên tập train rồi chấm lại tập test một lần:

1. **Dựng ngữ cảnh cho Điều dài:** chấm dòng theo độ hiếm của từ (độ phổ biến lấy từ `units_vocab`) thay vì đếm từ trùng; khi các Điều dài thì đưa 3 đoạn với ngân sách lớn hơn (`--passages 3`). Thêm vào bộ đo chỉ số "câu trích bằng chứng còn trong đoạn" cho các bộ có trường `evidence`, để tách lỗi cắt ngữ cảnh khỏi lỗi mô hình.
2. **Hết cắt JSON:** hạ các trần đủ để tổng tệ nhất vừa 200 token theo số ký tự/token đo được (2,5–3), rồi đo lại; hoặc nâng `n_predict` lên 256–300 và đo p95 trên máy 16 GB; hoặc giữ lại các ý đã đủ khi bị cắt.
3. **Từ chối và phạm vi:** dạy lời nhắc kiểm "đoạn có nói đúng đối tượng/trường hợp được hỏi không" trước khi đặt `du_can_cu`; khi đoạn chỉ nói trường hợp hẹp hơn thì trả lời kèm phạm vi đó trong `luu_y` (giao diện: "Chỉ tìm thấy quy định cho …") thay vì khẳng định chung.
4. **Chặn chữ Trung ngay khi sinh** (loại ký tự CJK khỏi chuỗi trong grammar), không chỉ lọc sau.
5. **Bộ kiểm tham chiếu:** chữ cái luôn là điểm ("khoản a" = "điểm a"); số hiệu bị cắt cụt khớp theo phần đầu; đọc số viết bằng chữ (shortcut đã ghi trong `answer.numbers`).
6. **Mô hình dự phòng Gemma 4 E4B** (QAT Q4_0) trên đúng bộ đo này: CHON-MO-HINH.md ghi nó bám ngữ cảnh tốt hơn (faithfulness 0,796), đúng điểm Qwen yếu ở đây.
7. **Đo trên máy 16 GB** (README): tốc độ, p95 đầu-cuối có phần tìm, RAM của `llama-server`; cỡ mẫu ≥ 100 câu để khoảng tin cậy hẹp lại (vòng này 15–30 câu mỗi bộ: khoảng tin cậy 95% xấu nhất ±18–25 điểm).

## Chạy lại

```text
python bench/llm/run.py <kho Zalo>/soiluat.db <thư mục zalo> --split test --mode normal --n 30 --bay 20 --out test_zalo.json
python bench/llm/run.py <kho Zalo>/soiluat.db <gold vle> --split gold --mode normal --n 20 --bay 0 --out test_vle.json
python bench/llm/run.py <realdocs>/data/soiluat.db <realdocs>/queries.json --mode advance --n 15 --bay 0 --out test_real.json
```

Vòng 2 chạy đúng ba lệnh này trên mã `b17461f`, lần lượt với máy chủ của từng mô hình (cùng tham số: `--n_ctx 4096 --n_threads 4`).

Kho Zalo dựng bằng `bench/zalo/build_db.py`, chưa nhúng vector nên chạy `--mode normal`; văn bản thật dựng như `bench/van-ban-that/KET-QUA.md` (mục Mốc P0), có vector nên chạy `--mode advance`.
