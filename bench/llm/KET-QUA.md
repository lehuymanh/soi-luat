# Kết quả đo câu trả lời bằng LLM (P0, vòng 1 trên máy ảo)

30/10/2026. Bộ đo: [README.md](README.md). Mô hình: Qwen3-VL-4B-Instruct, GGUF Q4_K_M chính hãng (lý do chọn: [CHON-MO-HINH.md](CHON-MO-HINH.md)). Mã đo: commit `9d4b7c7` (lời nhắc, khuôn JSON, bộ kiểm cố định trong `src/soiluat/answer.py`).

**Đây chưa phải số đo trên máy 16 GB.** Máy đo là máy ảo Linux 4 nhân (Xeon có AVX-512), 15 GB RAM, chạy llama-cpp-python 0.3.36 (bản mới nhất lúc đo; kiến trúc `qwen3vl` chỉ có trong llama.cpp từ 30/10/2025, xem CHON-MO-HINH.md), 4 luồng, nhiệt độ 0,1, seed 2026, cùng prompt và khuôn mà app sẽ dùng. Các tỉ lệ chất lượng không phụ thuộc máy nên dùng được cho quyết định; **thời gian thì không**: cổng 45 giây phải đo trên máy 16 GB theo README.

## Cách chọn cấu hình trước khi đo (tập train, không báo cáo làm chất lượng)

Mọi lựa chọn dưới đây làm trên câu hỏi **train** của Zalo, rồi mới chấm một lần trên tập **test**:

| Thay đổi | Lý do (đo trên train) |
|---|---|
| Giữ câu dẫn của khoản khi giữ một điểm | Lần chạy thử đầu: 2/3 câu bẫy sai, cả hai vì cắt mất dòng "Phạt tiền từ … đối với các hành vi sau": điểm còn mà mức phạt mất |
| Gộp Điều trùng nội dung trong ngữ cảnh | Kho Zalo có văn bản chép lại y nguyên (`63/2019/NĐ-` và `63/2019/NĐ-CP`), tốn chỗ của Điều khác |
| Ngân sách ngữ cảnh 2.600 ký tự | Đo `prompt_tokens`: chữ luật kèm tiêu đề ~3,1 ký tự/token, nên 3.000 ký tự thành ~1.150 token mới, vượt trần ~1.000 token |
| JSON schema hai nhánh theo `du_can_cu` | Lần đầu mô hình trả lời đúng nhưng để trống `cac_y` (không dẫn nguồn) |
| `tien_de_sai` đứng trước `du_can_cu` | A/B cùng mẫu (8 câu + 6 bẫy): bẫy 6/6 so với 5/6; câu hỏi nêu sai mức phạt vẫn được dẫn nguồn |
| Trần độ dài (`maxLength`, tối đa 2 ý) | 6/44 câu ở A/B hỏng JSON, cả 6 do bị cắt ở 200 token |

## Kết quả trên tập test

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

## Đọc kết quả

- **Mọi JSON hỏng đều do bị cắt ở 200 token** (10/80 lần gọi ở Zalo, 3/40 ở gold, 1/30 ở văn bản thật; cả 14 đều sinh đúng 200 token). 13/14 câu bị cắt khi đang viết một ý (9 câu ở ý thứ hai), chỉ 1 câu tới được lưu ý. Tổng các trần `maxLength` là 1.000 ký tự, tức ~330–400 token (chữ trong JSON đo được 2,5–3 ký tự/token), nên trần chưa ngăn được cắt. Chỉ tính câu JSON hợp lệ thì dẫn đúng là 77% (Zalo), 82% (gold), 50% (văn bản thật) và chỉ ra tiền đề sai là 15/16; đây là tỉ lệ trên phần còn lại, chưa phải số đo sau khi hết cắt.
- **Từ chối là chỗ yếu chính.** Khi đã bỏ Điều đúng, mô hình vẫn nói "đủ căn cứ" ở 20/28 câu JSON hợp lệ ở Zalo và 13/20 ở gold. Mục soát dưới đây (giám khảo là mô hình) cho thấy nhóm lớn nhất là khái quát quá phạm vi đoạn, không phải bịa từ đầu.
- **Bộ kiểm số liệu chặn đúng thứ cần chặn nhưng còn quá chặt ở tham chiếu.** Trên gold, 6 lần bị bỏ ý vì "số lạ", không lần nào là số tiền bịa: mô hình viết "khoản a" thay cho "điểm a"; nhắc lại "dưới 15 tuổi" của câu hỏi trong một ý (văn bản viết "mười lăm" bằng chữ, bộ kiểm chưa đọc số viết bằng chữ); số hiệu bị trần 160 ký tự của một ý cắt cụt ("155/2020/NĐ-"); dẫn "Điều 14" không có trong các đoạn được dẫn. Vì vậy "dẫn đúng sau bộ kiểm" ở gold thấp hơn 10 điểm.
- **Chữ Trung lẫn vào 0–10% câu trả lời** (3,8% Zalo, 10% gold, 0% văn bản thật) ("mũ坚硬", "thẩm权", "quy规划"), đúng rủi ro đã ghi ở CHON-MO-HINH.md. Bộ kiểm đã chặn: ý bị bỏ, câu trả lời bị thay bằng trích nguyên văn.
- **Trên văn bản thật, dẫn đúng chỉ 46,7%, và một phần lớn không do mô hình.** Bộ câu hỏi này có sẵn câu trích bằng chứng của đáp án (`queries.json`, trường `evidence`). Ở 5/7 câu dẫn sai (JSON hợp lệ), đoạn sau khi cắt chỉ còn ≤ 31% bộ 3-từ của câu trích đó (3 câu dưới 10%); 2 câu còn lại có đủ câu trích (lỗi mô hình). Ở 5/7 câu đúng, câu trích còn ≥ 50%. Nguyên nhân: Điều của văn bản 2026 dài (bản scan, OCR), mỗi đoạn chỉ được ~520 ký tự, và dòng được giữ chọn theo số từ trùng câu hỏi chứ không theo độ hiếm. Ví dụ "thời gian thí điểm cơ chế chính sách": 7/22 dòng của Điều 8 có cụm "thí điểm cơ chế", còn dòng có đáp án ("Thời gian thí điểm không quá 05 năm…") bị cắt. Từ chối đúng ở bộ này là 66,7% (10/15); kho, chế độ tìm và cỡ mẫu khác hẳn nên không so trực tiếp với Zalo và gold.
- Gắn nhầm tiền đề sai cho câu hỏi bình thường hiếm (0–6,7%); câu trả lời không bao giờ quá 3 câu.

## Soát các câu từ chối sai (giám khảo là mô hình Claude, không phải người, không phải chấm máy)

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

## Việc cho P3 (rút ra từ vòng này)

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

Kho Zalo dựng bằng `bench/zalo/build_db.py`, chưa nhúng vector nên chạy `--mode normal`; văn bản thật dựng như `bench/van-ban-that/KET-QUA.md` (mục Mốc P0), có vector nên chạy `--mode advance`.
