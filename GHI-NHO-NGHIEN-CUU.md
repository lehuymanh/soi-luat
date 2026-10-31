# Ghi nhớ nghiên cứu P0 (bàn giao cho lượt làm sau)

Viết 31/10/2026, cuối P0 của lộ trình 1.0. Người đọc chính: agent (hoặc người) làm tiếp P1 hay "việc trước P3", hoặc phải đo lại phần trả lời AI. Tài liệu này giữ **kết luận, phương pháp và những điều không tự tra được**. Số liệu đầy đủ nằm ở tài liệu nguồn; ở đây chỉ chép số cần để định hướng, kèm chỗ tra.

Đọc theo thứ tự này:

1. Tệp này: mục 1–2 để biết đang ở đâu, mục 3 trước khi đo bất cứ gì, mục 5 trước khi chạy job dài.
2. `soi-luat-lo-trinh-1.0.md`: mục 6 (P0 trạng thái, P1, P3 có "Việc trước P3"), mục 9 (quyết định còn mở).
3. `soi-luat-ke-hoach-p1.md`: kế hoạch triển khai P1 từng việc, từng file.
4. `bench/llm/KET-QUA.md` (vòng 2 ở đầu, vòng 1 ở dưới), `bench/llm/CHON-MO-HINH.md` (mục 7: lần tìm thêm mô hình), `bench/van-ban-that/KET-QUA.md` (mốc tìm kiếm P0).

---

## 1. Trạng thái bàn giao

- Nhánh `claude/funny-feynman-xvg6dm`, PR nháp lehuymanh/soi-luat#2 (base là nhánh của PR lộ trình lehuymanh/soi-luat#1). `pytest`: 258 passed, 7 skipped (bỏ qua vì thiếu Word COM, Tesseract hoặc mô hình thật, giống `main`).
- P0, phần máy làm được: **xong**. Còn chờ chủ dự án (lộ trình mục 9): duyệt mẫu `mau/giao-dien-1.0.html` (cổng để bắt đầu P1), chốt cách tính cổng câu trả lời AI (điều 10), đo trên máy 16 GB, ≥ 100 câu hỏi thật, chế độ tìm mặc định (điều 8).
- Mã trả lời AI (`src/soiluat/answer.py`) **chưa gắn vào app**; chỉ `bench/llm/run.py` gọi nó. P3 sẽ gắn.
- Số test của vòng 2 đo trên mã `b17461f`. Sau đó bản soát sửa thêm 6 lỗi (`bc9f9af`). Lần đo LLM kế tiếp phải chạy trên mã mới, và chạy lại sau khi P1 sửa parser (chữ đưa vào mô hình đổi).

## 2. Kết luận nghiên cứu

### 2.1 Tìm kiếm (mốc cho P1)

- Trên 21 văn bản thật 2026 (84 câu đã kiểm chứng), **Normal hơn Advance ở hạng 1**: Hit@1 rộng 83,3% so với 72,6%. Bước làm tụt là hợp điểm vector với BM25 (BM25 + vector, chưa reranker: 67,9%). Ở @10 hai bên gần bằng. Nguồn: `bench/van-ban-that/KET-QUA.md`, mục "Mốc P0".
- Hệ quả đã ghi vào lộ trình: giữ Normal làm mặc định tới khi nhánh độ chính xác (mục 6, điều 0) sửa bước hợp; P3 chạy được với Normal.

### 2.2 Trả lời bằng LLM

- Mô hình chính **Qwen3-VL-4B-Instruct Q4_K_M** (lý do chọn: `CHON-MO-HINH.md`). Vòng 1 → vòng 2 trên tập test (Zalo / gold / văn bản thật): dẫn đúng Điều 66,7 / 70 / 46,7% → **83,3 / 75 / 86,7%**; khẳng định như đủ căn cứ khi đã bỏ Điều đúng 66,7 / 65 / 33,3% → **26,7 / 40 / 13,3%**; JSON dùng được 87,5 / 92,5 / 96,7% → 100%; chữ Trung 3,8 / 10 / 0% → 0%. Mức tăng chắc chắn (vượt nhiễu): dẫn đúng ở Zalo và văn bản thật, khẳng định sai ở Zalo. Gold chỉ +1 câu.
- **Cổng P0 chưa đạt trọn**: dẫn đúng ≥ 80% đạt 2/3 bộ; JSON và từ chối đạt hay không tùy cách tính (lộ trình mục 9, điều 10).
- **Ba mô hình, cùng mã, cùng mẫu** (gộp 65 câu): dẫn đúng Qwen 53, Gemma 4 E4B 48, Nemotron-3.5-Bolt-E4B 44; khẳng định sai 18 / 19 / 24. **Chưa vượt nhiễu** (McNemar ghép cặp: Qwen–Gemma p = 0,30, Qwen–Bolt p = 0,06). Giữ Qwen vì nhanh hơn ~20–27% và tệp 2,5 GB so với ~5,2 GB.
- **Đổi mô hình cùng cỡ không sửa được lỗi phạm vi** (khái quát quy định của trường hợp hẹp cho câu hỏi chung, ví dụ mức phạt chỉ áp dụng tại đường ngang dùng cho mọi chỗ vượt đèn đỏ). Cả ba mô hình khẳng định sai ở 28–37% khi gộp. Hướng tiếp theo ở luồng xử lý (lộ trình, "Việc trước P3").

### 2.3 Cái gì có tác dụng, cái gì không

| Thay đổi | Kết quả | Nguồn đo |
|---|---|---|
| Tách câu cho dòng dài > 300 ký tự (OCR dính nhiều khoản/điểm), câu đầu dòng làm câu dẫn | **Có tác dụng lớn nhất.** Câu trích bằng chứng còn ≥ 50% trong đoạn: 53% → 80% câu (train văn bản thật) | offline, `bang_chung.py` |
| Chấm dòng theo IDF trong Điều thay vì đếm từ trùng | Nhỏ (+1–2 câu); chỉ có ích khi đã tách câu | offline |
| IDF toàn kho, BM25 theo dòng | Không hơn IDF trong Điều | offline |
| Đưa 3 đoạn thay 5 | Không thêm gì khi đã tách câu; mất Điều đúng khỏi top nhiều hơn | offline |
| Cứu JSON bị cắt (giữ ý đã viết xong) | JSON dùng được 100%; nhưng câu bẫy bị cắt thường mất hết ý có nguồn | test |
| `pattern` loại chữ CJK trong khuôn JSON | Chữ Trung 0%, tốc độ không đổi | test, smoke |
| Trường `pham_vi` trước `du_can_cu`, "hẹp hơn" vẫn trả lời kèm phạm vi (B1) | Ít khẳng định sai nhất trên train (5/12 so với 7/12 khi "hẹp hơn" buộc từ chối, 8/12 khi không có trường); từ chối hẳn giảm; gắn cờ thừa 10–40% câu có Điều đúng | A/B train, test |
| Bộ kiểm: "khoản a" = điểm a, số viết bằng chữ, số hiệu cụt, chuỗi chạm trần | Dẫn đúng sau kiểm trên câu trả lời vòng 1: 20 → 23/30, 12 → 16/20, 7 → 8/15 | chẩn đoán |
| Gemma 4 E4B, Nemotron-3.5-Bolt-E4B | Không hơn Qwen; viết dài hơn, chậm hơn | test |

### 2.4 Vấn đề còn mở (đã đưa vào lộ trình)

1. Lỗi phạm vi 28% khi gộp (mục 2.2).
2. Câu bẫy chạm trần 200 token: 17/20 bị cắt, 15 mất hết ý có nguồn (tiền đề sai và câu trả lời nhắc lại cùng mức phạt).
3. Cờ "hẹp hơn" gắn nhầm cho 10–40% câu có Điều đúng: giao diện sẽ hiện cảnh báo thừa.
4. Chưa có số trên máy 16 GB: thời gian đo trên máy ảo không dùng được cho cổng 45 giây.
5. Câu bẫy dùng chung giữa phần chỉnh và phần chấm (mục 3.1).

## 3. Phương pháp

### 3.1 Bộ đo `bench/llm/run.py`

Chấm hoàn toàn bằng máy; đáp án là Điều đúng có sẵn trong các bộ đo tìm kiếm. Mỗi câu hỏi chạy hai phép trên cùng câu, khác ngữ cảnh; thêm câu bẫy:

| Phép | Ngữ cảnh | Đúng khi |
|---|---|---|
| `dan` | 5 Điều đầu của tìm kiếm; Điều đúng ngoài top thì thay đoạn cuối | `du_can_cu = true` và có ý dẫn đoạn chứa Điều đúng (hoặc bản gần như cùng chữ) |
| `tu_choi` | Bỏ Điều đúng và mọi Điều gần như cùng chữ (`Same`, ≥ 70% bộ 3-từ của Điều dài hơn trùng) | `du_can_cu = false` |
| `bay` | Câu sinh từ một điểm có mức phạt, hỏi với mức tiền gấp 3 | `tien_de_sai` khác rỗng và câu trả lời nêu một mức đúng của nguồn |

Định nghĩa chỉ số dùng trong báo cáo (giữ đúng khi đo lại, để so được):

- **Khẳng định sai** = câu `tu_choi` có `du_can_cu = true` và `pham_vi` là "đúng" hoặc không có. Đây là chỉ số an toàn chính; không đổi khi đổi cách tính cổng.
- **Từ chối hẳn** = `du_can_cu = false`. **Từ chối hoặc nêu phạm vi hẹp hơn** = từ chối hẳn hoặc `pham_vi` là "hẹp hơn"/"khác".
- **JSON đọc ngay** = đọc được không cần cứu; **dùng được** = tính cả câu cứu được (`cut`). **Bị cắt** = `completion_tokens ≥ 200`.
- **Câu trích bằng chứng còn trong đoạn** (`bang_chung`, chỉ bộ văn bản thật có trường `evidence`) = phần bộ 3-từ của câu trích đáp án có trong đoạn chứa Điều đúng. Dùng để tách lỗi dựng ngữ cảnh khỏi lỗi mô hình.
- p50/p95 = phần tử thứ ⌊n·p⌋ của dãy đã xếp; với 30–80 lần gọi, p95 là giá trị lớn thứ 2–4, rất nhiễu.

Mẫu và phần tách (seed 2026, `pick_sample`):

- **Zalo**: chỉnh trên `--split train`, chấm `--split test --n 30 --bay 20`.
- **Gold `vle`**: chỉ có một tập, 20 câu, chỉ để chấm. Không chỉnh trên bộ này.
- **Văn bản thật**: 84 câu; `--n 15` là phần chấm; chỉnh bằng `--skip 15 --n k` (lấy từ các câu ngoài đúng 15 câu đó).
- **Rò rỉ đã biết**: câu bẫy sinh từ cả kho, không theo split; 6/20 câu bẫy test đã dùng khi chỉnh. Sửa ở "Việc trước P3".
- **Chấm test một lần** trên mã cuối, sau mọi lựa chọn. Ví dụ trong lời nhắc phải là ví dụ chung, không lấy từ các câu test đã soát (vòng 2 đã thay ví dụ đường ngang/công chức vì lý do này).

Độ tin cậy: 15–30 câu mỗi bộ cho khoảng tin cậy 95% xấu nhất ±18–25 điểm. So hai mô hình trên cùng câu thì dùng McNemar ghép cặp, không so hai tỉ lệ rời.

### 3.2 Đo offline trước khi tốn giờ chạy mô hình

Một lần gọi mô hình trên máy ảo mất ~50–80 giây; một vòng chấm ba bộ là ~2,5–3,5 giờ mỗi mô hình. Vì vậy mọi thay đổi ở phần **dựng ngữ cảnh** được chọn offline trước:

1. Lưu kết quả tìm của mọi câu một lần (Advance mất ~8 s mỗi câu).
2. Dựng ngữ cảnh bằng mã đang thử, đo câu trích bằng chứng còn trong đoạn, cả ngữ cảnh tự nhiên lẫn khi chèn Điều đúng.
3. Chọn biến thể trên phần train; chỉ biến thể thắng mới chạy mô hình.

Công cụ: `python bench/llm/bang_chung.py <realdocs> --modes normal,advance --split train --cache <tệp>`. Mốc hiện tại (train, mã `bc9f9af`): Normal còn ≥ 50% ở 81,8% câu tự nhiên, 83,3% khi chèn; còn < 10%: 4,5%; ngữ cảnh ~2.700 ký tự. Lần sửa ngữ cảnh nào làm các số này tụt thì phải có lý do.

Cách lần ra nguyên nhân dòng đáp án bị mất (dùng lại được): với các câu còn < 10%, in độ dài dòng chứa câu trích, hạng của nó theo điểm, độ dài cả Điều. Vòng 2 thấy dòng đáp án đứng hạng 0–1 nhưng dài 1.500–10.000 ký tự (OCR dính khoản), nên không vừa ngân sách: lời giải là tách câu, không phải chấm điểm khác.

### 3.3 A/B trên train

- Cùng mẫu câu, cùng tham số, mỗi biến thể đổi đúng một thứ. Mỗi biến thể chạy từ một git worktree riêng (`run.py` nạp `src/` của chính worktree đó), không đổi mã đang chạy giữa chừng.
- Chọn chỉ số quyết định **trước khi** xem kết quả, và ghi lại. Vòng 2 đặt luật "từ chối hẳn cao nhất" rồi đổi sang "khẳng định sai thấp nhất" sau khi xem số. Lý do đổi được ghi: B1 là thiết kế đã ghi từ vòng 1, và khẳng định sai mới là chỉ số an toàn. Lần sau hãy chọn đúng chỉ số an toàn ngay từ đầu.
- Đọc tay các câu đổi kết quả trước khi tin một chỉ số mới (vòng 2: 8 câu "hẹp hơn" khi đã bỏ Điều đúng, 5/8 nói rõ đoạn không quy định, 3/8 trả lời kèm giới hạn).

### 3.4 Chẩn đoán

- **Thử bộ kiểm mới trên câu trả lời cũ**: dựng lại đúng ngữ cảnh cũ bằng mã ở commit cũ (worktree), rồi chạy `answer.check` mới. Cách này đo được phần tăng do bộ kiểm mà không gọi lại mô hình.
- **JSON hỏng**: xem `completion_tokens` trước. Nếu mọi câu hỏng đều chạm trần thì lỗi do bị cắt, không phải do định dạng.
- **Đổi mã ngữ cảnh**: so từng câu (trước/sau) những câu có độ phủ đổi > 0,2. Vòng soát cuối dùng cách này mới thấy "câu khớp nhất" đôi khi là khối rác OCR (chữ ký dính phụ lục); vì vậy không ưu tiên nó trước mọi dòng khác.

### 3.5 Soát và kiểm số

- Mỗi đợt mã lớn: một workflow soát nhiều góc nhìn (lỗi; test, an toàn, tốc độ; mã thừa), rồi mỗi phát hiện được một tác tử khác cố bác bỏ. Chỉ sửa phát hiện còn đứng. Mỗi lỗi có một test hỏng trên mã cũ, rồi mới sửa. Đợt vòng 2: 6/15 rồi 14/23 phát hiện là thật.
- Số trong báo cáo dựng bằng script từ JSON thô: `python bench/llm/bang.py Qwen=zalo.json,vle.json,real.json Gemma=... --gop`. Sau khi viết báo cáo, cho hai tác tử độc lập tính lại mọi số và mọi câu diễn giải từ JSON thô. Vòng 2 bắt được: "8/8" thật ra là 5/8, rò rỉ câu bẫy, câu "tăng ở cả ba bộ" trong khi gold chỉ +1 câu.

### 3.6 Tìm mô hình

Tiêu chí (từ `CHON-MO-HINH.md` mục 1): mở trọng số, giấy phép cho dùng thương mại ngoại tuyến, GGUF chạy llama.cpp trên CPU, RAM mô hình ~4 GB (trần 6 GB), tắt chế độ suy nghĩ, kịp 45 giây p95 kể cả phần tìm. Cách làm lần 30/10/2026: bốn hướng tìm song song (mô hình nhỏ mới của các hãng; bản tinh chỉnh tiếng Việt/Đông Nam Á; bảng xếp hạng bám ngữ cảnh, tiếng Việt, làm theo chỉ dẫn; hỗ trợ llama.cpp), một bước xếp hạng theo đúng lỗi đang gặp, hai tác tử kiểm chứng ngược tại nguồn (thẻ mô hình, giấy phép, tệp GGUF, llama.cpp). Rồi đo ứng viên trên đúng bộ đo, cùng mã, không chỉnh riêng. Bài học: số bám ngữ cảnh do hãng công bố bằng tiếng Anh (Bolt: GaRAGe +9,8 điểm) không chuyển sang tiếng Việt.

## 4. Môi trường và chạy lại

Container của phiên này bị thu hồi; **thư mục làm việc `/tmp/claude-0/work` (kho đo, mô hình, JSON kết quả thô) không còn ở phiên sau**. `KET-QUA.md` là bản ghi chính thức. JSON thô không commit: câu hỏi gold `vle` chưa có giấy phép (`bench/gold/README.md`).

Dựng lại để đo (Linux, CPU):

1. **Python**: venv riêng; `pip install -e ".[nghia]"` cho Advance; `pip install llama-cpp-python==0.3.36` (bản PyPI; dựng llama.cpp từ git bị chặn trong môi trường này). Bản 0.3.36 có kiến trúc `qwen3vl` và `gemma4`.
2. **Kho đo**: Zalo dựng bằng `bench/zalo/build_db.py` từ `GreenNode/zalo-ai-legal-text-retrieval-vn` (`bench/zalo/KET-QUA.md`); gold `vle` bằng `bench/gold/build_vle.py` (chỉ giữ trên máy); văn bản thật bằng `bench/van-ban-that/import_real.py` (OCR, cần Tesseract có `vie`; đặt `SOILUAT_TESSDATA` nếu thiếu), rồi `python -m soiluat.importer --nhung` để có vector cho Advance.
3. **Mô hình Advance** (AITeamVN): `pack/export_models.py`; trỏ `SOILUAT_MODEL_DIR` và `SOILUAT_RERANK_DIR` tới thư mục xuất.
4. **Mô hình sinh** (Hugging Face, tải bằng `huggingface_hub`): `Qwen/Qwen3-VL-4B-Instruct-GGUF` tệp `Qwen3VL-4B-Instruct-Q4_K_M.gguf`; `google/gemma-4-E4B-it-qat-q4_0-gguf` tệp `gemma-4-E4B_q4_0-it.gguf`; `bartowski/NVIDIA-Nemotron-3.5-Bolt-E4B-GGUF` tệp `NVIDIA-Nemotron-3.5-Bolt-E4B-Q4_K_M.gguf`.
5. **Máy chủ**: `python -m llama_cpp.server --model <gguf> --n_ctx 4096 --n_threads 4 --host 127.0.0.1 --port 8080`; đợi `/v1/models` trả lời (`curl --noproxy '*'`). Khởi động bằng `setsid nohup … &` để sống qua giới hạn 2 giờ của lệnh nền.
6. **Chấm**: ba lệnh ở `bench/llm/KET-QUA.md`, mục "Chạy lại". Trên máy 16 GB (Windows, `llama-server`): `bench/llm/README.md`.

Thời lượng trên máy ảo 4 nhân: Qwen ~50–60 s mỗi lần gọi, Gemma và Bolt ~65–80 s; ba bộ test = 150 lần gọi.

## 5. Bẫy đã gặp

- **Container khởi động lại giữa chừng** (hai lần trong P0): mọi tiến trình nền chết. Commit và push sớm; viết script chạy dài có **tự bỏ qua phần đã xong** (ghi `EXIT=0` từng phần vào tệp trạng thái, như bộ chạy vòng 2).
- **Tranh CPU**: máy 4 nhân; chạy ONNX (Advance) hay một job nặng cùng lúc với máy chủ mô hình làm sinh chữ chậm ~10 lần (0,48 so với 5 token/s). Thời gian chỉ so được khi chạy một mình. Workflow chỉ chạy song song 2 tác tử trên máy này.
- **`pkill -f <mẫu>` giết luôn shell đang gõ** nếu dòng lệnh chứa mẫu đó (exit 144). Lấy PID bằng `pgrep -f "[l]lama_cpp.server"` (mẹo dấu ngoặc) rồi `kill`.
- **Heredoc không có dấu nháy** (`<<EOF`) chạy lệnh trong dấu backtick: chữ `` `dan` `` trong nội dung bị xoá. Dùng `<<'EOF'` khi viết tài liệu bằng shell.
- **`random.sample` đổi thuật toán theo cỡ mẫu**: tiền tố của `sample(qs, a+b)` không chắc bằng `sample(qs, a)`. Muốn phần chỉnh tách khỏi phần chấm thì loại đúng tập chấm rồi lấy mẫu từ phần còn lại (`pick_sample`).
- **llama.cpp bỏ qua `maxLength` khi chuỗi có `pattern`**: trần độ dài phải ghi trong pattern (`{0,n}`).
- **Gemma 4 qua `llama-server`**: issue llama.cpp #30256, khuôn JSON qua `response_format` vẫn cho kênh suy nghĩ khi tắt suy nghĩ. llama-cpp-python tự dịch schema nên không vướng; trên máy 16 GB nếu gặp thì truyền grammar GBNF.
- **Đọc tệp kết quả lúc `run.py` đang ghi** cho số sai (một lần đọc được 29 thay vì 30 câu `dan`). Đọc sau khi có dòng trạng thái kết thúc.
- **Mẫu lời nhắc ghi ví dụ "không phải 5.000.000 đồng"**: mô hình chép ví dụ vào câu thường, bộ kiểm bỏ. Ví dụ trong lời nhắc nên dùng số khó trùng.
- **Số hiệu như `QH15`, tên tệp, mã đoạn `[1]`, nhãn khoản `1.`** từng "bảo lãnh" cho số bịa. Bộ kiểm hiện tách chúng thành nhãn; thêm luật mới thì thêm test cho đúng loại này (`.claude/skills/vietnamese-legal-number-check`).

## 6. Việc tiếp theo

- **P1** theo `soi-luat-ke-hoach-p1.md`, sau khi chủ dự án duyệt mẫu. P1 không phụ thuộc kết quả đo mô hình.
- **Việc trước P3** (lộ trình mục 6, P3), chạy xen bằng máy: câu bẫy chạm trần; tín hiệu điểm tìm kiếm thấp cho lỗi phạm vi; tách câu bẫy train/test; chạy lại `bench/llm` sau khi P1 sửa parser.
- **Quyết định của chủ dự án**: lộ trình mục 9 (điều 8, 9, 10 liên quan trực tiếp tới việc trên).

## 7. Bản đồ tệp

| Tệp | Là gì |
|---|---|
| `src/soiluat/answer.py` | Lõi trả lời: dựng ngữ cảnh, lời nhắc, khuôn JSON, gọi `llama-server`, cứu JSON, bộ kiểm số liệu |
| `tests/test_answer.py`, `tests/test_bench_llm.py` | Test của lõi trả lời và cách lấy mẫu của bộ đo |
| `bench/llm/run.py` | Bộ đo câu trả lời (ba phép, chỉ số, `--skip`) |
| `bench/llm/bang.py` | Bảng báo cáo từ JSON thô |
| `bench/llm/bang_chung.py` | Đo offline câu trích bằng chứng còn trong đoạn |
| `bench/llm/KET-QUA.md` | Kết quả vòng 1, vòng 2, A/B, ba mô hình, việc tiếp theo, lệnh chạy lại |
| `bench/llm/CHON-MO-HINH.md` | Chọn mô hình theo benchmark công khai; mục 7: lần tìm thêm 30/10/2026 |
| `bench/llm/README.md` | Cách chạy, kể cả trên máy 16 GB |
| `bench/van-ban-that/KET-QUA.md` | Mốc tìm kiếm trên văn bản thật (Normal/Advance) |
| `soi-luat-lo-trinh-1.0.md` | Lộ trình 1.0; P0 trạng thái; P3 "Việc trước P3"; quyết định mở |
| `soi-luat-ke-hoach-p1.md` | Kế hoạch triển khai P1 |
| `mau/giao-dien-1.0.html` | Mẫu giao diện chờ duyệt |
| `.claude/skills/` | Kỹ năng rút ra trong P0 (đóng gói ngữ cảnh, khuôn JSON, kiểm số tiếng Việt, chạy llama.cpp) |
