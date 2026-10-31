# Bộ đo câu trả lời bằng LLM (lộ trình 1.0, P0)

Đo mô hình sinh câu trả lời **trước khi** gắn vào app (P3). Chấm hoàn toàn bằng máy: đáp án là Điều đúng đã có sẵn
trong các bộ đo tìm kiếm, nên không cần người chấm pháp lý. Mã dùng chung với app: `src/soiluat/answer.py`
(dựng ngữ cảnh, lời nhắc, JSON schema, kiểm nguồn và số liệu). Đổi lời nhắc, khuôn hay cách dựng ngữ cảnh thì chạy lại
bộ này (lộ trình mục 5, điều 7).

Chọn mô hình: [chon-mo-hinh.md](../../docs/nghien-cuu/chon-mo-hinh.md). Kết quả đo: [KET-QUA.md](KET-QUA.md).

## Ba phép đo

| Phép | Ngữ cảnh đưa vào mô hình | Đúng khi |
|---|---|---|
| `dan` (dẫn đúng Điều) | 5 Điều đầu do tìm kiếm của app xếp; Điều đúng giữ chỗ tìm kiếm xếp, nằm ngoài top 5 thì thay đoạn cuối | `du_can_cu = true` và có ý dẫn đúng đoạn chứa Điều đó |
| `tu_choi` (từ chối đúng) | Cùng câu hỏi, bỏ Điều đúng và mọi Điều cùng nội dung ở văn bản khác | `du_can_cu = false` (`tu_choi_dung`); tính cả câu trả lời có `pham_vi` là "hẹp hơn"/"khác", tức không khẳng định như đủ căn cứ: `tu_choi_hoac_neu_hep` |
| `bay` (tiền đề sai) | Câu sinh từ một điểm có mức phạt (`units.fine_min/fine_max`), hỏi với mức tiền gấp 3; Điều chứa điểm đó luôn có trong ngữ cảnh | `tien_de_sai` khác rỗng và câu trả lời nêu đúng một mức trong nguồn (so số) |

Mọi lần gọi còn được đo: JSON hợp lệ, bị cắt ở trần token (`bi_cat`) và cứu được hay không, số liệu khớp đoạn được
dẫn (`so_khop`), có chữ Trung/Nhật/Hàn, câu trả lời quá 3 câu, phải thay bằng trích nguyên văn, thời gian tìm + thời
gian mô hình, số token. Bộ có câu trích bằng chứng (`queries.json` của văn bản thật, trường `evidence`) đo thêm câu
trích đó còn bao nhiêu trong đoạn sau khi cắt (`dan_bang_chung_con`), để tách lỗi dựng ngữ cảnh khỏi lỗi mô hình.

Cổng P0 (lộ trình mục 6): trên máy 16 GB đang mở Office, **p95 tổng ≤ 45 giây** (`tong_p95_s`, tính cả phần tìm ở
Advance), **JSON hợp lệ ≥ 99%**, **dẫn đúng ≥ 80%**, **từ chối đúng ≥ 80%**. Ngưỡng chất lượng là đề xuất, chốt khi có số.

## Chạy trên máy 16 GB (Windows)

1. **llama.cpp:** tải bản Windows CPU x64 mới nhất ở trang Releases của `ggml-org/llama.cpp` (tệp
   `llama-b<số>-bin-win-cpu-x64.zip`), giải nén. Cần `llama-server.exe` và `llama-bench.exe`.
2. **Mô hình:** `Qwen3VL-4B-Instruct-Q4_K_M.gguf` (2,33 GiB) từ Hugging Face `Qwen/Qwen3-VL-4B-Instruct-GGUF`.
   Không cần tệp `mmproj` (chạy như mô hình chữ). Dự phòng: Gemma 4 E4B, bản GGUF QAT Q4_0 của Google.
3. **Tốc độ thô** (Office và trình duyệt đang mở, như `docs/nghien-cuu/chon-mo-hinh.md` mục 5):

   ```text
   llama-bench -m Qwen3VL-4B-Instruct-Q4_K_M.gguf -t 6 -p 1000,1500 -n 200 -r 5
   ```

4. **Máy chủ mô hình** (chỉ nghe 127.0.0.1):

   ```text
   llama-server -m Qwen3VL-4B-Instruct-Q4_K_M.gguf --host 127.0.0.1 --port 8080 -t 6 -c 4096 --jinja
   ```

   RAM: xem Working set của `llama-server.exe` trong Task Manager hoặc Process Explorer (mục tiêu ≤ 4 GB).
5. **Đo** (máy có Python và repo, `pip install -e ".[nghia]"`; kho Zalo dựng bằng `bench/zalo/build_db.py`, đã nhúng
   vector để chạy Advance):

   ```text
   python bench/llm/run.py <kho Zalo>\soiluat.db <thư mục zalo> --split test --n 100 --bay 50 --out zalo_llm.json
   python bench/llm/run.py <kho Zalo>\soiluat.db <thư mục gold vle> --split gold --n 100 --out vle_llm.json
   python bench/llm/run.py <realdocs>\data\soiluat.db <realdocs>\queries.json --n 84 --bay 0 --out real_llm.json
   ```

   Mô hình dự phòng Gemma 4 E4B: thay `-m` bằng `gemma-4-E4B_q4_0-it.gguf` (5,15 GB, repo Hugging Face
   `google/gemma-4-E4B-it-qat-q4_0-gguf`) rồi chạy lại ba lệnh trên, đổi tên tệp `--out`.
   Trên máy ảo (vòng 2, `KET-QUA.md`) Gemma 4 E4B và Nemotron-3.5-Bolt-E4B đều không hơn Qwen3-VL-4B, nên trên
   máy 16 GB chỉ cần đo Qwen; Gemma chỉ để so RAM và tốc độ nếu có thời gian.

   Mỗi câu hỏi gọi mô hình hai lần (`dan`, `tu_choi`); mỗi câu bẫy một lần. Với ~45 giây một lần gọi, 100 câu + 50
   câu bẫy mất khoảng 3 giờ. Kết quả ghi dần vào tệp `--out` (dừng giữa chừng vẫn còn phần đã chạy); bảng tổng in ra
   cuối cùng và nằm ở khoá `tong`.

Tuỳ chọn: `--mode normal` (tìm BM25, khi kho chưa nhúng vector), `--passages 3` (đưa 3 đoạn thay vì 5 nếu chậm),
`--skip K` (bỏ K câu đầu của mẫu: với bộ không có tập train như văn bản thật, chỉnh trên phần sau K câu, chấm trên
K câu đầu), `--temp`, `--url` / `--api-key` (hoặc biến `SOILUAT_LLM_URL`, `SOILUAT_LLM_KEY`).

Câu hỏi gold `vle` lấy từ ViLegalExperts, chưa ghi giấy phép: chỉ giữ trên máy, không commit (`bench/gold/README.md`).

## Đọc kết quả

- Các tỉ lệ chất lượng không phụ thuộc máy (cùng tệp GGUF, cùng nhiệt độ và seed thì gần như lặp lại), nên số đo trên
  máy khác dùng được để chọn lời nhắc và mô hình. **Thời gian thì phải đo trên máy 16 GB**: máy khác chỉ để so tương đối.
- `json_hop_le` là JSON đọc được ngay; `json_dung_duoc` tính cả câu bị cắt ở trần token mà bộ kiểm cứu được (giữ các
  ý đã viết xong, bỏ ý đang viết dở; khoá `cut` của từng câu). `bi_cat` là tỉ lệ câu sinh chạm trần token.
- `dan_dung_sau_kiem` là tỉ lệ còn dẫn đúng sau khi bộ kiểm bỏ các ý có số liệu không khớp nguồn.
- `dan_dieu_dung_do_tim_ra` là tỉ lệ câu mà Điều đúng do chính tìm kiếm đưa vào top 5 (phần còn lại được chèn để đo).
- Xem từng câu trong khoá `tung_cau`: `ctx` là các đoạn đã đưa vào mô hình, `content` là chữ mô hình sinh, `checked`
  là câu trả lời sau khi kiểm,
  `dropped` là phần bị bỏ và lý do (`cac_y:so` = ý có số không có trong đoạn được dẫn).
