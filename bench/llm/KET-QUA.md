# Kết quả đo câu trả lời bằng LLM (P0, trên máy ảo)

30/10/2026. Bộ đo: [README.md](README.md). Mô hình chính: Qwen3-VL-4B-Instruct, GGUF Q4_K_M chính hãng (lý do chọn: [CHON-MO-HINH.md](CHON-MO-HINH.md)). Vòng 1: mã `9d4b7c7`; vòng 2 (sau bảy việc sửa): mã `b17461f`. Lời nhắc, khuôn JSON, bộ kiểm nằm trong `src/soiluat/answer.py`.

**Đây chưa phải số đo trên máy 16 GB.** Máy đo là máy ảo Linux 4 nhân (Xeon có AVX-512), 15 GB RAM, chạy llama-cpp-python 0.3.36 (bản mới nhất lúc đo; kiến trúc `qwen3vl` chỉ có trong llama.cpp từ 30/10/2025, xem CHON-MO-HINH.md), 4 luồng, nhiệt độ 0,1, seed 2026, cùng prompt và khuôn mà app sẽ dùng. Các tỉ lệ chất lượng không phụ thuộc máy nên dùng được cho quyết định; **thời gian thì không**: cổng 45 giây phải đo trên máy 16 GB theo README.

## Vòng 2: sau bảy việc sửa (30/10/2026)

Mã đo: commit `b17461f`. Mọi lựa chọn làm trên phần train (Zalo train; văn bản thật: các câu ngoài 15 câu test) hoặc offline, rồi chấm tập test **một lần**, cùng ba bộ và cùng mẫu câu như vòng 1. Cùng máy ảo, cùng llama-cpp-python 0.3.36, 4 luồng, nhiệt độ 0,1, seed 2026.

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

Chọn biến thể cuối vì ít câu khẳng định sai nhất, và đây là thiết kế đã ghi ở việc 3 của vòng 1. Khi "hẹp hơn" buộc từ chối, mô hình né nhãn đó (3/12 câu so với 6/12) và trả lời "đúng" nhiều hơn. Đọc lại 8 câu được gắn "hẹp hơn" khi Điều đúng đã bị bỏ: cả 8 câu, chữ trả lời tự nói đoạn không quy định đúng điều được hỏi ("Đoạn văn không quy định mức phạt đối với trung tâm sát hạch… chỉ quy định trách nhiệm về cơ sở vật chất"). Cái giá: từ chối hẳn giảm, nên chỉ số `tu_choi_dung` của cổng P0 thấp đi; phải tính `tu_choi_hoac_neu_hep` mới phản ánh đúng hành vi. Cách tính cổng là việc người dùng chốt (lộ trình mục 9).

**Soát độc lập** (4 góc nhìn: cứu JSON, bộ kiểm số, dựng ngữ cảnh, grammar và bộ đo; mỗi phát hiện được một tác tử khác kiểm chứng ngược): 6/15 phát hiện là thật, đã sửa, mỗi lỗi có test hỏng trên mã cũ (commit `131ca78`). Hai lỗi nặng: "mười năm" đọc thành 15, và câu khớp nhất quá dài bị bỏ khiến đoạn gần như rỗng. Bản đầu của phần sửa bỏ hẳn tách ở dấu hai chấm làm câu còn bằng chứng tụt 80% → 71% trên train; bản cuối giữ tách câu dẫn đầu dòng, chỉ gộp nhãn giữa dòng, và lấy lại 80%.

### Kết quả trên tập test

**Qwen3-VL-4B, vòng 1 → vòng 2** (cùng mẫu câu; Zalo 30 câu + 20 bẫy, gold 20, văn bản thật 15; mỗi câu hai lần gọi `dan` và `tu_choi`):

| Chỉ số | Zalo: v1 | Zalo: v2 | Gold `vle`: v1 | Gold `vle`: v2 | Văn bản thật: v1 | Văn bản thật: v2 |
|---|---|---|---|---|---|---|
| JSON đọc được (chưa cứu) | 87,5% (87,5%) | 100,0% (78,8%) | 92,5% (92,5%) | 100,0% (95,0%) | 96,7% (96,7%) | 100,0% (96,7%) |
| Bị cắt ở trần 200 token | 13,8% | 21,2% | 7,5% | 5,0% | 3,3% | 3,3% |
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

(cột "JSON đọc được": tính cả câu bị cắt đã cứu; trong ngoặc là đọc được ngay. Thời gian không so được giữa hai vòng: máy ảo dùng chung, tải khác nhau.)

**Qwen3-VL-4B so với Gemma 4 E4B (QAT Q4_0), cùng mã vòng 2, cùng mẫu câu:**

| Chỉ số | Zalo: Qwen | Zalo: Gemma | Zalo: Bolt | Gold `vle`: Qwen | Gold `vle`: Gemma | Văn bản thật: Qwen | Văn bản thật: Gemma |
|---|---|---|---|---|---|---|---|
| JSON đọc được (chưa cứu) | 100,0% (78,8%) | 100,0% (63,8%) | 100,0% (100,0%) | 100,0% (95,0%) | 100,0% (82,5%) | 100,0% (96,7%) | 100,0% (96,7%) |
| Bị cắt ở trần 200 token | 21,2% | 38,8% | 0,0% | 5,0% | 17,5% | 3,3% | 3,3% |
| Dẫn đúng Điều | 83,3% | 63,3% | 100,0% | 75,0% | 85,0% | 86,7% | 80,0% |
| Dẫn đúng sau bộ kiểm | 80,0% | 63,3% | 100,0% | 75,0% | 85,0% | 86,7% | 80,0% |
| Từ chối hẳn (`du_can_cu = false`) | 16,7% | 46,7% | — | 20,0% | 55,0% | 60,0% | 73,3% |
| Từ chối hoặc nêu phạm vi hẹp hơn | 73,3% | 66,7% | — | 60,0% | 60,0% | 86,7% | 93,3% |
| Khẳng định như đủ căn cứ khi đã bỏ Điều đúng | 26,7% | 33,3% | — | 40,0% | 40,0% | 13,3% | 6,7% |
| Có Điều đúng mà bị gắn "hẹp hơn"/"khác" | 26,7% | 26,7% | 0,0% | 10,0% | 10,0% | 40,0% | 20,0% |
| Chỉ ra tiền đề sai (bẫy) | 85,0% | 95,0% | — | — | — | — | — |
| Số liệu khớp nguồn | 98,8% | 100,0% | 100,0% | 100,0% | 100,0% | 100,0% | 100,0% |
| Có chữ Trung/Nhật/Hàn | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% |
| Phải thay bằng trích nguyên văn | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% |
| Token sinh ra, trung bình | 155 | 170 | 141 | 137 | 164 | 118 | 138 |
| Mô hình p50 / p95 trên máy ảo (s) | 57 / 72 | 73 / 89 | 64 / 64 | 53 / 71 | 69 / 83 | 49 / 68 | 67 / 80 |

- **Không mô hình nào thắng hẳn.** Dẫn đúng gộp ba bộ: Qwen 53/65, Gemma 48/65. Gemma hơn ở gold (85% so với 75%), kém ở Zalo (63,3% so với 83,3%). Ở Zalo, 5/11 câu Gemma dẫn sai là từ chối dù có Điều đúng (4 câu gắn "khác"), 3 câu bị cắt mất ý.
- **Gemma từ chối hẳn nhiều hơn** (gộp 36/65 so với 18/65), gần cách tính cổng cũ hơn. Nhưng số câu khẳng định như đủ căn cứ khi đã bỏ Điều đúng gần như bằng nhau (19/65 và 18/65): Gemma cũng không sửa được lỗi phạm vi.
- **Gemma viết dài hơn** (164–170 token ở Zalo và gold) nên bị cắt nhiều hơn (38,8% ở Zalo, có cả câu thường), và chậm hơn ~25–30% trên máy ảo. Bẫy tiền đề sai: Gemma 95%, Qwen 85%.
- Giữ Qwen3-VL-4B làm mô hình chính: nhanh hơn, ngắn hơn, dẫn đúng nhiều hơn khi gộp, bằng Gemma ở lỗi phạm vi.

**Nemotron-3.5-Bolt-E4B** (ứng viên mới, `CHON-MO-HINH.md` mục 7): đang chạy trên cùng ba bộ, sẽ điền vào đây.

**Đọc kết quả (Qwen):**

- **Dẫn đúng Điều tăng rõ ở cả ba bộ** và qua ngưỡng 80% ở Zalo (83,3%) và văn bản thật (86,7%); gold 75%. Trên văn bản thật, câu trích bằng chứng còn ≥ 50% trong đoạn ở 9/15 câu (vòng 1, dựng lại đúng ngữ cảnh cũ: 7/15). Mức tăng dẫn đúng (7 → 13/15) lớn hơn mức tăng độ phủ bằng chứng, nên phần còn lại đến từ việc cứu JSON, bộ kiểm và trường phạm vi.
- **Khẳng định sai khi đã bỏ Điều đúng giảm mạnh:** 66,7 → 26,7% (Zalo), 65 → 40% (gold), 33,3 → 13,3% (văn bản thật). Đổi lại, từ chối hẳn giảm vì "hẹp hơn" được trả lời kèm phạm vi; tính cả câu nêu phạm vi hẹp hơn thì 73,3 / 60 / 86,7%. Cái giá thứ hai: câu có Điều đúng cũng bị gắn "hẹp hơn"/"khác" ở 26,7 / 10 / 40% số câu, tức giao diện sẽ hiện cảnh báo thừa ở những câu đó.
- **JSON dùng được 100% ở cả ba bộ** (vòng 1: 87,5 / 92,5 / 96,7%). Nhưng bị cắt lại nhiều hơn ở Zalo (21,2%): **cả 17 lần bị cắt đều là câu bẫy** (17/20 câu bẫy), 15 trong số đó mất hết ý có nguồn. Câu bẫy vẫn đúng 15/17 vì chấm theo tiền đề sai, nhưng câu trả lời không còn chip dẫn nguồn. Câu thường không bị cắt lần nào ở Zalo.
- Chữ Trung/Nhật/Hàn 0% (vòng 1: 3,8 / 10 / 0%); không câu nào phải thay bằng trích nguyên văn (vòng 1: 12,5 / 12,5 / 3,3%); số liệu khớp nguồn 98,8–100%.
- Cỡ mẫu nhỏ (15–30 câu mỗi bộ, khoảng tin cậy 95% ±16–25 điểm): chênh 1–2 câu không có nghĩa; các mức tăng lớn ở dẫn đúng và khẳng định sai thì vượt nhiễu.

**So với cổng P0 đề xuất:** dẫn đúng ≥ 80% đạt ở 2/3 bộ; JSON ≥ 99% đạt nếu tính câu đã cứu, không đạt nếu tính đọc ngay (78,8% ở Zalo do câu bẫy); từ chối ≥ 80% không đạt theo cách tính cũ (`du_can_cu = false`), đạt ở văn bản thật nếu tính cả câu nêu phạm vi hẹp hơn. Hai cách tính này là quyết định của người dùng (lộ trình mục 9). Việc tiếp theo cho Qwen: câu bẫy viết quá dài (tiền đề sai + câu trả lời nhắc lại cùng mức phạt) nên chạm trần; hạ trần câu trả lời khi đã có tiền đề sai, hoặc đưa `cac_y` lên trước `tra_loi`, rồi đo lại trên train.

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
7. **Đo trên máy 16 GB** (README): tốc độ, p95 đầu-cuối có phần tìm, RAM của `llama-server`; cỡ mẫu ≥ 100 câu để khoảng tin cậy hẹp lại (vòng này 15–30 câu mỗi bộ: khoảng tin cậy 95% ±16–25 điểm).

## Chạy lại

```text
python bench/llm/run.py <kho Zalo>/soiluat.db <thư mục zalo> --split test --mode normal --n 30 --bay 20 --out test_zalo.json
python bench/llm/run.py <kho Zalo>/soiluat.db <gold vle> --split gold --mode normal --n 20 --bay 0 --out test_vle.json
python bench/llm/run.py <realdocs>/data/soiluat.db <realdocs>/queries.json --mode advance --n 15 --bay 0 --out test_real.json
```

Vòng 2 chạy đúng ba lệnh này trên mã `b17461f`, lần lượt với máy chủ của từng mô hình (cùng tham số: `--n_ctx 4096 --n_threads 4`).

Kho Zalo dựng bằng `bench/zalo/build_db.py`, chưa nhúng vector nên chạy `--mode normal`; văn bản thật dựng như `bench/van-ban-that/KET-QUA.md` (mục Mốc P0), có vector nên chạy `--mode advance`.
