# Đo tìm kiếm trên câu hỏi thật — Zalo AI 2021 Legal Text Retrieval (22/10/2026)

**Dữ liệu:** `GreenNode/zalo-ai-legal-text-retrieval-vn` (MIT). 61.425 điều thuộc 3.271 văn bản; **788 câu hỏi thật** (tập test) có đáp án do người gán (thường 1 Điều).
**Kho:** nạp qua đúng đường nạp thật (`parse_pages` → `_store_doc` → nhãn, liên kết): 427.351 đơn vị, DB 1,35 GB, 510 s. Parser tách được 444/447 Điều đáp án.
**Đo:** đúng khi Điều đáp án nằm trong 10 kết quả đầu (gom theo Điều). Chạy lại:

```text
python bench/zalo/build_db.py <thư mục zalo> <thư mục data>
python bench/zalo/eval.py <thư mục zalo> <thư mục data> test
python bench/zalo/why_miss.py <thư mục zalo> <thư mục data> --limit 120
```

## Kết quả (788 câu)

| Cách | Hit@10 | Hit@1 | MRR@10 | 0 kết quả | p50 | p95 |
|---|---|---|---|---|---|---|
| **Hiện tại** (rút câu hỏi + 6 tầng AND + xếp thẻ) | **54,7%** | 26,1% | 0,348 | 7,5% | 190 ms | 404 ms |
| BM25 OR, cột có dấu | 84,9% | — | 0,603 | 0% | 398 ms | 677 ms |
| BM25 OR, bỏ từ có ở > 20% đơn vị | 83,9% | — | 0,589 | 0% | 183 ms | 320 ms |
| BM25 OR, bỏ từ > 35% | 84,6% | — | 0,601 | 0% | 317 ms | 550 ms |
| **BM25 OR, có dấu + ngữ cảnh khoản cha** | **86,9%** | 53,4% | **0,657** | 0% | 477 ms | 786 ms |
| **Sau khi chuyển app sang BM25 OR** (bản cuối, đường `cascade_search` + dựng thẻ của app) | **88,5%** | 52,9% | **0,661** | 0% | 962 ms | 1622 ms |
| BM25 OR, không dấu | 77,7% | — | 0,558 | 0% | 464 ms | 747 ms |

BM25 OR: đưa nguyên câu hỏi (không bỏ từ nào bằng danh sách tay), `MATCH {cột} : (w1 OR w2 …)`, xếp bằng `bm25()` có sẵn trong FTS5. Không thêm thư viện.

**Chồng lấn** (hiện tại vs BM25 có ngữ cảnh): cả hai trúng 419; chỉ BM25 trúng 266; chỉ cách hiện tại trúng 12; cả hai trượt 91.

## Vì sao cách hiện tại trượt (mẫu 120 câu, trượt 54)

| Khâu | Số câu | Giải thích |
|---|---|---|
| Thang tầng dừng ở tầng đầu có kết quả | 38 | Tầng đó (AND một phần từ / 2 từ hiếm nhất, trần 50 đơn vị) không chứa Điều đúng; không có so sánh mức liên quan giữa các tầng |
| Khoá xếp thẻ đẩy Điều đúng xuống | 9 | Điều đúng có trong kết quả nhưng xếp theo hạng liên kết / nhãn / Q5, không theo độ liên quan → hạng 13–31 |
| 0 kết quả | 7 | Viết tắt ("KCB"), câu dài: mọi tầng AND đều rỗng |

## Đọc kết quả

- Gốc G2 được xác nhận bằng số: **chuyển sang BM25 OR tăng 54,7% → 86,9%**, số câu ra đúng ở hạng 1 tăng gấp đôi (26% → 53%), không còn câu nào 0 kết quả.
- Danh sách từ tay (bỏ "như thế nào", "được quy định"…) không cần: BM25 tự hạ trọng số từ phổ biến. Cắt từ phổ biến chỉ giúp tốc độ (p50 398 → 183 ms ở ngưỡng 20%) và làm mất ~1 điểm.
- 12 câu chỉ cách cũ trúng phần lớn là câu "X là gì": cách cũ có tầng khớp cụm nguyên văn. → thêm điểm cộng khi khớp cụm/NEAR vào BM25.
- 91 câu cả hai trượt là **khác chữ** ("quán karaoke" ↔ "kinh doanh dịch vụ karaoke", "nướng bắp trên cầu"): đây là giới hạn của tìm theo chữ — chỉ từ điển đồng nghĩa hoặc tìm theo nghĩa mới gỡ được.
- Độ trễ đo trên kho 427 nghìn đơn vị (lớn hơn nhiều kho một cơ quan); kho nhỏ sẽ nhanh hơn — chưa đo.

## Phát hiện phụ

`units_vocab` được tạo là `fts5vocab(units_fts, 'row')` (không có cột `col`), nên `search._token_df` luôn lỗi `no such column: col` và rơi vào nhánh đếm bằng `MATCH` — đúng nhưng chậm.

## Giới hạn

- Chỉ đo **tìm kiếm** trên văn bản pháp quy đã sạch; không đo đọc file, OCR, cấu trúc.
- Thẻ hạng 1–4 (liên kết nghĩa vụ–chế tài đã duyệt) là tính năng duyệt, không phải độ liên quan; bộ này không đo giá trị đó.
- Mỗi câu thường chỉ 1 Điều đáp án; Điều khác cũng đúng nhưng không được gán sẽ bị tính là trượt (cả hai cách chịu như nhau).

## Sau khi chuyển app sang BM25 OR (22/10/2026)

Một truy vấn BM25 OR lấy 300 ứng viên (cột có dấu + ngữ cảnh, trọng số 1/1/1/0,3/0,3); mức khớp (cụm, gần nhau, đủ từ, đồng nghĩa, một phần) tính bằng Python trên ứng viên và nhân vào điểm; trả 100 đơn vị đầu; thẻ xếp theo độ liên quan trước. Không còn `strip_question` trong app.

- Hit@10 54,7% → **88,5%**, MRR 0,348 → **0,661**, Hit@1 26,1% → 52,9%, 0 kết quả 7,5% → 0%. Cao hơn bản thử (86,9%) nhờ thêm điểm khớp cụm.
- **Chậm hơn:** p50 190 → 962 ms, p95 404 → 1622 ms (kho 427 nghìn đơn vị; kho một cơ quan nhỏ hơn nhiều, chưa đo).
- Bỏ `strip_question` tăng độ chính xác trên train (0,800 → 0,842). Chỉnh trọng số cột / hệ số cộng cụm: chênh trong ngưỡng nhiễu.
- Câu hỏi mức phạt: ưu tiên thẻ chế tài hạng 1–2 chỉ khi khớp ≥ "đủ từ"; nếu không, thẻ lỏng nổi lên làm trượt ca "Không niêm yết giá bị phạt bao nhiêu?".
- pytest: 187 passed; stress10: 20/20.

## Thêm cộng điểm cặp âm tiết (22/10/2026)

Điểm mỗi ứng viên nhân thêm `(1 + 2,0 × tỉ lệ cặp âm tiết liền nhau của câu hỏi có trong đơn vị hoặc ngữ cảnh)`; trọng số cột ngữ cảnh 0,3 → 0,5. Hệ số chọn trên 300 câu train (Hit@10 0,867 → 0,910), rồi đo một lần trên 788 câu test:

| 788 câu test | Trước | Sau |
|---|---|---|
| Hit@1 | 52,9% | **58,9%** |
| Hit@3 | 78,2% | 82,0% |
| Hit@5 | 83,4% | **86,2%** |
| Hit@10 | 88,5% | **90,2%** |
| MRR@10 | 0,661 | 0,709 |
| p50 / p95 | 962 / 1622 ms | 975 / 1614 ms |

Không đạt mục tiêu "top 5 = 90%". pytest 187 passed; stress10 20/20.

## Thử nghiệm EmbeddingGemma (22/10/2026, chưa đưa vào app)

`onnx-community/embeddinggemma-300m-ONNX`, bản int8 (295 MB), onnxruntime CPU, cắt 256 token, vector 256 chiều. Không nhúng cả kho (quá lâu): chỉ nhúng 15.710 Điều nằm trong 30 kết quả đầu của BM25 cho 988 câu, rồi xếp hạng lại bằng RRF (hạng BM25 + hạng theo nghĩa). Tham số chọn trên 200 câu train (top 20, w=1, k=5), đo một lần trên 788 câu test:

| 788 câu test | BM25 (app) | BM25 + EmbeddingGemma | Chỉ theo nghĩa (xếp lại top 30) |
|---|---|---|---|
| Hit@1 | 58,9% | **62,3%** | 47,1% |
| Hit@3 | 82,0% | 83,9% | 71,4% |
| Hit@5 | 86,2% | **89,2%** | 79,8% |
| Hit@10 | 90,2% | **92,3%** | 90,1% |

Chi phí đo trên máy thử (12 nhân logic; máy văn phòng có thể chậm hơn):
- Nhúng: 2,7 Điều/s (2 luồng), 3,2 Điều/s (12 luồng) → 61 nghìn Điều ≈ 6 giờ, 10 nghìn ≈ 1 giờ (một lần khi nạp).
- Mỗi câu hỏi: +213 ms (nhúng câu hỏi, 2 luồng).
- RAM: ~430 MB khi đã nạp (tắt memory arena; bật thì 1,3 GB), đỉnh 1,2 GB lúc nhúng lần đầu.
- Giấy phép Gemma (không phải MIT/Apache).

## EmbeddingGemma trong app (22/10/2026) — đo đầu-cuối

Code app (`soiluat/semantic.py`): vector theo Điều (tên + toàn bộ khoản/điểm, cắt 256 token, 256 chiều, float16 trong bảng `unit_vectors`); khi tìm nhúng câu hỏi rồi xếp lại 20 Điều đầu của BM25 bằng RRF (k=5, w=1). Nhúng bằng `bench/zalo/embed_needed.py` (gọi `semantic.embed_roots`, 2 luồng) đúng 9.047 Điều mà bước xếp lại chạm tới cho 788 câu test — kết quả trùng với nhúng cả kho. Đo qua `eval.py` (đường `cascade_search` + dựng thẻ của app) và `app_ram.py` (Search App thật qua HTTP, 60 câu).

| 788 câu test | Tắt (BM25) | Bật (BM25 + EmbeddingGemma) |
|---|---|---|
| Hit@1 | 58,9% | 60,5% |
| Hit@3 | 82,0% | 83,0% |
| Hit@5 | 86,2% | **89,1%** |
| Hit@10 | 90,2% | **91,8%** |
| MRR@10 | 0,709 | 0,725 |
| Độ trễ trong process p50 / p95 | 959 / 1603 ms | 1256 / 1967 ms |

Từng câu: 128 câu lên hạng, **110 câu xuống hạng**; 33 câu vào top 5, 10 câu rơi khỏi top 5.

| Search App (HTTP, 60 câu) | Tắt | Bật |
|---|---|---|
| RAM lúc rảnh | 59 MB | 58 MB (mô hình chưa nạp) |
| RAM sau câu đầu / cuối lượt | 69 / 73 MB | **479 / 488 MB** |
| RAM đỉnh (peak working set) | 78 MB | **1300 MB** |
| Câu đầu tiên | 3,2 s | **6,5 s** (nạp mô hình) |
| p50 / p95 | 1118 / 1695 ms | 1471 / 2145 ms |

Nhúng: **2,29 Điều/s** ở 2 luồng (9.047 Điều trong 3.942 s) → 10 nghìn Điều ≈ 73 phút, 61 nghìn ≈ 7,4 giờ.

## Thử mô hình tĩnh potion-multilingual-128M (22/10/2026, chưa đưa vào app)

`minishlab/potion-multilingual-128M` (MIT, model2vec): tra bảng từ rồi lấy trung bình, không chạy mạng nơ-ron. Cùng cách xếp lại như EmbeddingGemma (RRF với 20 Điều đầu của BM25), tham số chọn trên 200 câu train, đo trên 788 câu test (nhúng văn bản gốc của bộ Zalo, 1 Điều = tên + nội dung):

| 788 câu test | BM25 | BM25 + EmbeddingGemma | BM25 + potion |
|---|---|---|---|
| Hit@1 | 58,9% | 62,3% | **46,6%** |
| Hit@3 | 82,0% | 83,9% | 73,0% |
| Hit@5 | 86,2% | 89,2% | **84,1%** |
| Hit@10 | 90,2% | 92,3% | 90,1% |

Tốc độ nhanh hơn nhiều (3.053 Điều/s, một câu hỏi 0,7 ms) nhưng **xếp lại làm kết quả tệ đi**, không tốt lên; và nạp mô hình mất 11,5 s, RAM +1,1 GB (bảng từ 500.353 × 256 float32). Không dùng.

## EmbeddingGemma cắt 128 token (22/10/2026)

Cùng cách đo đầu-cuối như trên (9.047 Điều, 788 câu test), chỉ đổi `semantic.MAXLEN` 256 → 128 (vector lưu tên riêng, mặc định app chưa đổi):

| 788 câu test | 256 token | 128 token |
|---|---|---|
| Hit@1 | 60,5% | 60,2% |
| Hit@3 | 83,0% | 83,5% |
| Hit@5 | 89,1% | 89,1% |
| Hit@10 | 91,8% | 91,9% |
| Tốc độ nhúng (2 luồng) | 2,29 Điều/s | **4,51 Điều/s** |

Độ chính xác như nhau (chênh trong nhiễu), nhúng nhanh gấp ~2 lần.

**Từ 22/10/2026 mặc định app là 128 token** (`semantic.MAXLEN = 128`, `MODEL_NAME` đổi thành `embeddinggemma-300m-q8-256-len128`: kho đã nhúng ở 256 token sẽ được báo là chưa nhúng và cần chạy lại `--nhung`).

## Chốt (22/10/2026, đo lại cả hai chế độ trên app hiện tại)

| 788 câu test | Normal (BM25) | Advance (BM25 + EmbeddingGemma 128 token) |
|---|---|---|
| Hit@1 / @3 / @5 / @10 | 58,9 / 82,0 / 86,2 / 90,2% | 60,2 / 83,5 / 89,1 / 91,9% |
| MRR@10 | 0,709 | 0,722 |
| Độ trễ trong process p50 / p95 | 1087 / 1902 ms | 1314 / 2149 ms |

Search App qua HTTP (60 câu): Normal RAM 59 → 73 MB, đỉnh 77 MB, p50 / p95 1163 / 1931 ms; Advance RAM 479 → 381 MB, đỉnh 1298 MB, p50 / p95 1639 / 2663 ms.
Câu đầu tiên sau khi bật app dao động mạnh theo cache ổ đĩa của file kho 1,4 GB: đo 4 lần Normal 3,2 / 5,9 / 17,1 / 17,9 s, Advance 6,5 / 7,5 / 10,7 / 36,1 s (chậm nhất là ngay sau khi vừa nạp/nhúng file khác làm trôi cache). Không phải do code: các câu sau ổn định.
Thử trên văn bản thật: `bench/van-ban-that/KET-QUA.md`.

## Thêm 20 Điều từ vector toàn kho ở Advance (23/10/2026)

`semantic.DENSE_K = 20`: ngoài xếp lại 20 Điều đầu BM25, thêm 20 Điều gần nghĩa nhất toàn kho, chỉ chen sau, không đổi thứ tự các Điều BM25 tìm ra (lý do và thử trên ghi chú viết tự do: `bench/van-ban-that/KET-QUA.md`). Cần nhúng **cả kho**: đã nhúng nốt 52 314 Điều (12 096 s ≈ 3 giờ 22 phút, 4,3 Điều/s, 2 luồng), nay 61 361 / 61 361.

| 788 câu test, Advance | Chỉ xếp lại (K = 0) | + 20 Điều từ vector (K = 20) |
|---|---|---|
| Hit@1 / @3 / @5 / @10 | 60,2 / 83,5 / 89,1 / 91,9% | 60,2 / 83,5 / 89,1 / **92,5%** |
| MRR@10 | 0,722 | 0,723 |
| Độ trễ trong process p50 / p95 | 1477 / 2333 ms | 1280 / 1934 ms |

K = 0 trên kho nhúng đủ cho kết quả như lần chốt (787 / 788 câu cùng hạng; Hit@k, MRR y hệt): xếp lại chỉ đụng 20 Điều đầu, vốn đã có vector. K = 20: 6 câu tốt hơn, 6 câu kém hơn. Tốt hơn đều là câu trước không vào top 10 nay vào hạng 5–7 ("Phạt bao nhiêu nếu ô tô vượt đèn đỏ?", "Xây nhà cao tầng ở gần sân bay được không?", "hợp đồng hợp tác là gì?"…). Kém hơn: 5 câu tụt 1 hạng ở vị trí 5–9, 1 câu từ hạng 9 ra ngoài top 10 ("dừng đỗ xe trên cầu để hóng mát"). Hạng 1–3 không câu nào đổi. Chênh độ trễ giữa hai lượt là do cache ổ đĩa (lượt sau chạy khi file kho đã nóng), không phải K = 20 nhanh hơn.

Ma trận vector (61 361 × 256, float32) nạp ở câu Advance đầu tiên, giữ trong process:

| Process mới, đo 3 lần | Lần 1 (ổ đĩa chưa cache) | Lần 2 | Lần 3 |
|---|---|---|---|
| Nạp ma trận | 6,10 s | 0,41 s | 0,39 s |
| RAM sau nạp / đỉnh lúc nạp | +66 / +138 MB | +65 / +138 MB | +65 / +138 MB |

Mỗi câu sau đó: kiểm khoá cache (đếm vector) ~7 ms, nhân câu hỏi × ma trận + lấy 20 đầu ~5 ms.

Search App thật qua HTTP (uvicorn, cùng 60 câu như lần chốt, Advance):

| | K = 0 | K = 20 |
|---|---|---|
| RAM rảnh → sau câu đầu → cuối | 58 → 480 → 492 MB | 59 → 545 → 558 MB |
| RAM đỉnh | 1304 MB | 1370 MB |
| Câu đầu / p50 / p95 | 14,6 s / 1635 / 2350 ms | 19,1 s / 1546 / 2224 ms |

K = 20 tốn thêm ~65 MB thường trực, đỉnh +66 MB. Câu đầu dao động theo cache ổ đĩa như các lần đo trước (lượt K = 0 đầu tiên, trước khi sửa nhánh K = 0 thôi nạp ma trận, đo được 25,4 s), không tách được phần 0,4–6 s của ma trận ra khỏi nhiễu đó.

**Ngưỡng `DENSE_MIN = 0,50`.** Không có ngưỡng thì câu BM25 không ra gì ("?", "qwzx plokm vbnrt", "smartphone warranty refund") vẫn nhận đủ 20 thẻ không liên quan thay vì "Không tìm thấy". Đo cosine cao nhất toàn kho Zalo: 15 câu vô nghĩa 0,27–0,47; Điều đáp án của 784 câu thật p5 / p10 / p50 = 0,51 / 0,54 / 0,65 (≥ 0,50: 752 / 784). Chỉ Điều **thêm từ vector** phải đạt ngưỡng; Điều BM25 tìm ra không bị lọc. 788 câu với ngưỡng: Hit@1 / @3 / @5 / @10 = 60,2 / 83,5 / 89,1 / 92,5%, MRR 0,723 — giống hệt K = 20 không ngưỡng (cùng 6 câu lên, 6 câu xuống; `ket_qua_test_full_k20_min50.json`). Câu vô nghĩa nay về trang "Không tìm thấy" (đã xem trên Search App).

Giao diện: thẻ chỉ có nhờ vector (không chung chữ với câu hỏi) mang tầng khớp 7 và nhãn "tìm theo nghĩa, không chung từ khoá"; thẻ đoạn của file không số hiệu có tên file trước tiêu đề ("kn-vang · trang 1 đoạn 1" thay vì "trang 1 đoạn 1"). Câu "cửa hàng kim hoàn từ chối giao chứng từ lúc sắm trang sức" trên kho 21 văn bản + 6 ghi chú: 72 thẻ, 14 thẻ mang nhãn này (vị trí 8, 10, 17, 24, 27–36), ghi chú ở vị trí 8. Kịch bản đo: `realtools/matrix_load.py`, `realtools/zalo_k.py` trong scratchpad phiên đo; kết quả từng câu: `ket_qua_test_full_k0.json`, `ket_qua_test_full_k20.json`.


## P1 K3: đo theo mục hiển thị (31/10/2026)

Quy ước (kế hoạch P1, mục 2b, chủ dự án duyệt 31/10/2026): "theo mục" là mục hiển thị sau `cards.compact` (một mục mỗi (văn bản, Điều), Điều cùng nội dung ở văn bản khác gộp vào "Cũng có ở"). Zalo và gold tính trúng khi khoá đáp án nằm ở bản đại diện hoặc một bản trùng (kho Zalo gần như không có ngày ban hành để chọn đại diện); văn bản thật tính theo bản đại diện. Mọi bộ báo cả hai cách.

Zalo test 788 câu, Normal (`SOILUAT_SEMANTIC=0`), bản dựng sau sửa parser điểm nhiều dòng (N1a), mã `c803116`; `python -I bench/zalo/eval.py <zalo> <data> test --tag muc --only hien_tai,hien_tai_muc,hien_tai_muc_dai_dien` (`ket_qua_test_muc.json`):

| Cách tính | Hit@1 | Hit@5 | Hit@10 | MRR@10 |
|---|---|---|---|---|
| theo thẻ (`hien_tai`, mốc 0.8) | 58,6 | 86,3 | 90,5 | 0,710 |
| theo mục, kèm "Cũng có ở" (`hien_tai_muc`, cổng P1) | 61,0 | 86,4 | 90,5 | 0,723 |
| theo mục, chỉ bản đại diện (`hien_tai_muc_dai_dien`) | 58,6 | 83,6 | 87,7 | 0,697 |

Cổng P1 (Hit@1, @5 theo mục không thấp hơn mốc theo thẻ trên cùng bản dựng): đạt (@1 +2,4 điểm, @5 +0,1). Chỉ tính bản đại diện thì @5 thấp hơn 2,7 điểm: đáp án Zalo hay nằm ở bản trùng mà bản đại diện được chọn theo hiệu lực và ngày ban hành, kho Zalo thiếu cả hai. Tính theo mục chỉ thêm ~74 ms mỗi câu (p50).
