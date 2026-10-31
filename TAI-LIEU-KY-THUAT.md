# Soi Luật — Tài liệu kỹ thuật

Phiên bản app 0.8 · cập nhật 29/10/2026 · Đối tượng đọc: người bảo trì, người build/đóng gói, người đánh giá chất lượng tìm kiếm.
Hướng dẫn cho người dùng cuối: [HUONG-DAN-DON-GIAN.md](HUONG-DAN-DON-GIAN.md) (ngắn) và [HUONG-DAN.md](HUONG-DAN.md) (đầy đủ).

---

## 1. Tổng quan

Soi Luật là app **tra cứu văn bản pháp luật offline** trên máy Windows văn phòng. Người dùng nạp văn bản (Word, PDF, ảnh scan, Excel, TXT) vào một kho SQLite cục bộ, rồi hỏi bằng từ khoá hoặc câu tự nhiên. Kết quả là **nguyên văn** Điều/khoản/điểm kèm văn bản nguồn và số trang. App **không sinh văn bản**, không gọi dịch vụ ngoài.

| Mục | Giá trị |
|---|---|
| Máy mục tiêu | Windows 10/11 x64, 8 GB RAM trở lên, Office có thể đang mở; thiết kế và đo trên Ryzen 5 5600GT (6 nhân/12 luồng, AVX2), 16 GB, không card rời |
| Mạng | Không cần. App chỉ nghe `127.0.0.1`; hai mô hình AI chạy tại chỗ. Đã kiểm: 0 kết nối ra ngoài khi chạy bản đóng gói |
| Ngôn ngữ / khung | Python 3.11, FastAPI + uvicorn, Jinja2, giao diện HTML một trang (htmx), không cần cài Python trên máy chạy (PyInstaller onedir) |
| Lưu trữ | SQLite (WAL) + FTS5, một file `soiluat.db`; kho 61.425 Điều ≈ 1,5 GB |
| Hai chế độ tìm | **Normal** (BM25 + quy tắc, ~1 giây, ~75 MB RAM) và **Advance** (thêm vector + reranker, ~9 giây, ~2,2 GB RAM đỉnh) |
| Dung lượng | Bộ cài 840 MB; sau cài 1,4 GB (app 140 MB, Tesseract 134 MB, hai mô hình 1.119 MB) |

---

## 2. Kiến trúc

```
                       ┌────────────── SoiLuat.exe (một tiến trình) ──────────────┐
 Trình duyệt ─HTTP──▶  │ app.py (FastAPI)                                          │
 127.0.0.1:8000        │   ├─ search.py ─ cascade BM25 ─▶ semantic.py ─▶ crossrank │
                       │   │              (Advance: vector toàn kho)  (reranker)   │
                       │   ├─ cards.py     dựng thẻ kết quả, nhãn, chế tài         │
                       │   ├─ jobs.py      luồng nền: nạp file, OCR, nhúng vector  │
                       │   └─ export_word.py, pageimg.py                           │
                       │ ingest/extract/parse/ocr  ◀── nạp file                    │
                       └──────────────┬────────────────────────────────────────────┘
                                      │
              data\soiluat.db (SQLite WAL + FTS5)     models\aiteamvn-embedding\
              data\files\ (bản sao file nguồn)        models\aiteamvn-reranker\
                                                      tesseract\ (OCR tiếng Việt)
```

Một tiến trình duy nhất: tìm kiếm chạy trong luồng request, nạp file/OCR/nhúng chạy trong **một luồng nền** (`jobs.py`, lần lượt từng file). `SoiLuat.exe import …` là dòng lệnh dùng cùng mã nạp.

### 2.1 Các module (`src/soiluat/`)

| Module | Vai trò |
|---|---|
| `app.py` | FastAPI: trang tìm, nạp file, cài đặt, duyệt liên kết/từ điển, xem nguồn, xuất Word; `HostGuard` và CSRF |
| `extract.py` | Đọc DOCX/DOC/RTF/PDF/XLSX/ảnh/TXT thành trang (giữ bảng, footnote, comment, text box) |
| `convert.py` | `.doc/.rtf` → `.docx` tạm qua Word COM, dự phòng LibreOffice |
| `ocr.py` | OCR bằng Tesseract (chỉ importer gọi; không import ở mức module) |
| `parse.py` | Parser 3 tầng Điều / khoản / điểm; tầng 3 chia theo đoạn khi không có cấu trúc |
| `ingest.py` | Ghi pages, units, nhãn, gợi ý liên kết, gợi ý hiệu lực vào SQLite |
| `rebuild.py` | Dựng lại units/FTS sau khi nạp lại cùng đường dẫn |
| `fold.py`, `sohieu.py`, `query.py` | Chuẩn hoá tiếng Việt (có dấu / không dấu), nhận số hiệu và "Điều n", tách ý định ("mức phạt…") |
| `search.py` | Tra số hiệu/Điều; cascade BM25 nhiều tầng; gọi Advance |
| `semantic.py` | Embedding AITeamVN, hợp RRF toàn kho |
| `crossrank.py` | Reranker AITeamVN top-5 và độ tin cậy |
| `cards.py` | Gom đơn vị thành thẻ, gắn chế tài, nhãn rủi ro, ghi chú |
| `answer.py` | Trợ lý trả lời 1.0 (chưa gắn vào giao diện): dựng ngữ cảnh 3–5 Điều, lời nhắc, JSON schema, gọi `llama-server`, kiểm nguồn và số liệu; đo bằng `bench/llm/run.py` |
| `labels.py`, `links.py` | Nhãn (NGHIA_VU, CAM, THOI_HAN, DIEU_KIEN, QUYEN, CHE_TAI, DINH_NGHIA) và liên kết nghĩa vụ–chế tài (chờ người duyệt) |
| `jobs.py` | Hàng đợi nạp file và nhúng vector nền |
| `importer.py`, `health.py` | Dòng lệnh nạp/nhúng; khám sức khoẻ kho (CSV) |
| `db.py`, `schema.sql`, `config.py` | Kết nối, lược đồ, đường dẫn dữ liệu |

### 2.2 Lược đồ dữ liệu (`schema.sql`)

| Bảng | Nội dung chính |
|---|---|
| `documents` | Một dòng/văn bản: `so_hieu`, `loai`, `co_quan`, ngày ban hành/hiệu lực, `hieu_luc` ∈ {con, het, chua_ro}, `sha256` (chống nạp trùng), cờ `fallback_doan` |
| `pages` | Trang gốc: văn bản thô, văn bản chuẩn hoá, trạng thái OCR (`ocr_status`, độ tin cậy), `reviewed_text` |
| `units` | Đơn vị tìm kiếm: `level` ∈ {dieu, khoan, diem, doan}, `path` dạng `D3.K1.Đa`, `parent_id`, các cột chuẩn hoá cho FTS (`search_text` không dấu, `search_accent` có dấu, `context_*` ngữ cảnh cha), `fine_min/fine_max` (chế tài tiền) |
| `units_fts` | FTS5 external-content trên `units`, tokenizer `unicode61 remove_diacritics 0`, đồng bộ bằng trigger |
| `unit_labels`, `links` | Nhãn từng đơn vị; liên kết chế tài ↔ nghĩa vụ (`confirmed` do người duyệt) |
| `synonyms`, `subject_rules` | Từ điển đồng nghĩa/viết tắt và quy tắc ưu tiên chủ thể; chỉ mục `approved = 1` mới dùng khi tìm |
| `effect_hints` | Gợi ý "thay thế/bãi bỏ" tìm thấy trong văn bản (chờ xác nhận) |
| `unit_vectors` | Vector 1024 chiều **float16** của Điều gốc, khoá `(unit_id, model)` — đổi `model` thì vector cũ bị bỏ qua |
| `app_meta` | Khoá/giá trị: chế độ tìm (`search_mode`), phiên bản seed từ điển |
| `import_jobs`, `query_log` | Hàng đợi nạp file; nhật ký câu hỏi (kể cả câu không ra kết quả) |

Điều gốc (`parent_id IS NULL`) là đơn vị được nhúng vector và chấm lại; khoản/điểm đi theo Điều của chúng.

---

## 3. Luồng nạp văn bản

1. **Nhận file** (chọn/kéo thả: chép vào `data\files`; hoặc đường dẫn có sẵn: giữ nguyên chỗ).
2. **Chống trùng** theo SHA-256 (`trùng`) và theo đường dẫn (`không đổi`).
3. **Trích chữ** (`extract.py`): DOCX/TXT/PDF có chữ nhanh (~0,1–0,5 giây/file); PDF scan và ảnh qua OCR Tesseract tiếng Việt (~1,7 giây/trang); trang chưa bật OCR đánh dấu `cần OCR`.
4. **Nhận diện văn bản** (`ingest.py`): số hiệu, loại, cơ quan, ngày; PDF gộp nhiều văn bản được tách và ghi `multi_document_suspected`.
5. **Parse** (`parse.py`): tách Điều / khoản / điểm; không tách được thì chia theo đoạn (`fallback_doan`). Có thể ép chia đoạn bằng tuỳ chọn khi nạp.
6. **Ghi** `units` + trigger FTS5; gán nhãn; gợi ý liên kết chế tài và gợi ý hiệu lực.
7. **Nhúng vector** (chỉ khi chế độ Advance và đã cài mô hình): luồng nền tính vector cho Điều chưa có, khi hàng đợi nạp file trống.

Hiệu lực mặc định là `chua_ro`; app **không** tự kết luận văn bản còn hay hết hiệu lực.

**Nâng cấp dữ liệu khi parser đổi.** Quy tắc: **đổi đầu ra parser (path hoặc chữ của đơn vị) thì tăng `PARSE_REV`** (`parse.py`). Kho có `app_meta.parse_rev` khác `PARSE_REV` được nâng cấp một lần khi mở app, trong luồng `soiluat-jobs` (`jobs._migrate_chunk`): sao lưu ra `data\backup\soiluat-truoc-parse<PARSE_REV>.db` (mỗi lần tăng `PARSE_REV` một bản riêng, không đè bản cũ; ghi qua tệp `.<pid>.tmp` nên hai bản app cùng kho không xoá tệp của nhau; lỗi mà chưa có bản nào thì không dựng lại), dựng lại từng văn bản mà parse mới khác đơn vị đang lưu (`rebuild.rebuild_if_changed`; bỏ qua `fallback_doan = 1`), duyệt hết không sót mới ghi `parse_rev`. Văn bản lỗi hoặc bị khoá ghi: thử lại một lần cuối lượt; ba văn bản lỗi liên tiếp thì bỏ cả lượt (khoá giữ lâu, không chờ 5 s cho từng văn bản). Còn sót thì báo ở thanh bên (số văn bản chưa nâng cấp, chi tiết ở title), không ghi cờ, và chỉ thử lại ở lần mở app sau; lỗi SQLite lúc ghi cờ cũng báo như vậy, luồng không chết im. Kho trống: ghi cờ ngay, không sao lưu.

Dựng lại một văn bản (`rebuild_document`) giữ khoá ghi từ lúc đọc trang tới commit đơn vị (chữ đối chiếu vừa lưu không bị đè), commit rồi mới dựng gợi ý (truy vấn FTS không giữ khoá ghi cả kho). Giữ: liên kết (kể cả người và ngày duyệt), gợi ý hiệu lực đã duyệt, vector của Điều không đổi chữ. Không giữ: liên kết và gợi ý hiệu lực đã bác (bác là `DELETE`, không có dấu vết) nên hiện lại một lần ở văn bản được dựng lại, và liên kết đã duyệt có đường dẫn không còn trong parse mới; giữ cặp đã bác cần thêm bảng (P2). Trong lúc nâng cấp, tìm kiếm dùng chỉ mục tên Điều và ma trận vector bản cũ (dựng lại cho từng văn bản làm mỗi lần tìm chậm thêm 1–6 s); cả hai làm mới đúng một lần khi nâng cấp xong.

---

## 4. Luồng tìm kiếm

### 4.1 Normal

`cascade_search(conn, câu hỏi)` trong `search.py`:

1. `query.split_intent` tách cụm ý định (vd. "mức phạt") khỏi câu hỏi để BM25 không bị nhiễu; câu đầy đủ vẫn được giữ cho embedding/reranker (`full_query`).
2. **Tra thẳng** nếu câu hỏi là số hiệu và/hoặc "Điều n" (tầng 0): trả đúng văn bản/Điều, không chấm điểm.
3. Ngược lại: **BM25 OR nhiều tầng** trên `units_fts`.
   - Tách từ có nhận cụm theo tiêu đề và từ vựng của kho; mở rộng bằng từ điển đồng nghĩa đã duyệt.
   - Lấy tối đa `CANDIDATES = 300` ứng viên, chấm lại theo mức khớp: tầng 1 cụm liền, 2 gần nhau, 3 đủ từ, 4 đồng nghĩa, 6 một phần (hệ số `BOOST = {1: 2.0, 2: 1.5, 3: 1.3, 4: 1.3, 6: 1.0}`), cộng thêm điểm theo tỉ lệ cặp từ liền nhau trùng với câu hỏi (`BIGRAM_ALPHA = 2.0`).
   - Câu gõ có dấu thì tìm nhánh có dấu; nếu không đơn vị nào khớp đủ từ thì thêm nhánh không dấu. Trang OCR chưa đối chiếu luôn được thử thêm nhánh không dấu (OCR hay sai dấu).
4. Trả tối đa `RETURN_TOP = 100` đơn vị; `cards.assemble_cards` dựng thẻ (gom theo Điều, gắn chế tài, nhãn rủi ro). "Điều n" không kèm số hiệu giới hạn `DIEU_CAP = 100` thẻ.
5. Bộ lọc loại văn bản / cơ quan / hiệu lực áp sau cùng (`apply_doc_filters`).

### 4.2 Advance (thêm hai bước sau bước 3)

**(a) Hợp BM25 với vector toàn kho — `semantic.rerank`**

- Embedding: AITeamVN/Vietnamese_Embedding (nền BGE-M3), ONNX int8, vector 1024 chiều (lấy CLS, chuẩn hoá L2), cắt 128 token, 2 luồng.
- Văn bản mỗi Điều được dựng lại đúng dạng văn bản luật mà mô hình đã được đo: `Điều N. Tên Điều` rồi từng khoản/điểm kèm số/chữ (`1.`, `a)`), mỗi dòng một đơn vị (`semantic.root_parts`; app tách số điều/số khoản khỏi chữ nên phải dựng lại, nếu không Hit@1 giảm ~2,7 điểm).
- Lấy `TOP = 20` Điều đầu của BM25 và `DENSE_K = 50` Điều gần nghĩa nhất **toàn kho** (ma trận 61 nghìn × 1024 float32 giữ trong RAM, 252 MB), trong phạm vi văn bản nếu câu hỏi nêu số hiệu.
- Điểm hợp RRF: `1/(5 + hạng_BM25) + 2/(5 + hạng_vector)` (`RRF_K = 5`, `W = 2.0`). Điều chỉ có từ vector chỉ được nhận khi cosine ≥ `DENSE_MIN = 0.40` (đã chỉnh: chặn 29/30 câu vô nghĩa, không mất Hit@10 trên tập chỉnh); thẻ này mang nhãn "tìm theo nghĩa, không chung từ khoá" (tầng 7).
- Điều chưa có vector không bị phạt: giữ điểm BM25 như cũ.

**(b) Reranker top-5 và độ tin cậy — `crossrank.rerank_top`**

- Reranker: AITeamVN/Vietnamese_Reranker (cross-encoder, nền BGE-reranker-v2-m3), ONNX int8, chấm cặp (câu hỏi, `Tên Điều\nnội dung`), cắt 384 token (cắt phần Điều), `TOPN = 5`, 2 luồng; khoản/điểm đi theo Điều.
- `gap = điểm hạng 1 − điểm hạng 2`. `gap ≥ SURE_GAP = 3.0` thì giao diện hiện **"Độ tin cậy cao"**, ngược lại **"Chưa chắc chắn: nên xem 3 kết quả đầu"**. Ngưỡng được kiểm chéo giữa hai bộ đo; đổi mô hình, độ dài hay `TOPN` thì phải đo lại.
- Thiếu mô hình/thư viện, hoặc `SOILUAT_SEMANTIC=0`: bỏ qua bước tương ứng, tìm như Normal, không có nhãn.

### 4.3 Khởi động và bộ nhớ

Khi app mở, luồng `soiluat-warm` nạp trước encoder, reranker và ma trận vector (`semantic.warm`) để câu đầu không phải gánh thời gian nạp (đo trong script nghiệm thu không có bước này: câu đầu ~31 giây). Mô hình nạp lười, một lần mỗi tiến trình.

---

## 5. Hiệu năng và chất lượng đã đo

### 5.1 Độ chính xác

Hai bộ đo, kho 61.425 Điều (chỉ chứa đúng văn bản nguồn của hai bộ câu hỏi cộng nhiễu):

| Cấu hình | Zalo 788 câu: Hit@1 / @5 / @10 | Tư vấn thật 500 câu: Hit@1 / @5 / @10 |
|---|---|---|
| Normal (BM25) | 58,9 / 86,2 / 90,2 | 51,0 / 76,6 / 83,4 |
| Chỉ vector AITeamVN | 60,2 / 84,1 / 87,8 | 72,4 / 87,4 / 92,8 |
| Hợp BM25 + vector | 68,3 / 90,4 / 95,6 | 68,4 / 89,8 / 95,4 |
| **Advance (hợp + reranker top-5)** | **74,1 / 90,4 / 95,6** | **79,2 / 89,8 / 95,4** |

**Nghiệm thu qua chính app** (29/10/2026; 300 câu ngẫu nhiên nửa Zalo nửa gold; app tự nhúng lại cả 61.361 Điều; 2 luồng):

| Chỉ số | Kết quả |
|---|---|
| Hit@1 / @3 / @5 / @10 | 79,3 / 90,0 / 92,3 / 97,3 % (thí nghiệm cùng mẫu: Hit@1 79,0 %) |
| Nhãn "độ tin cậy cao" | 61 % số câu, Hit@1 94,0 %; nhóm còn lại Hit@1 56,0 % |
| Độ trễ mỗi câu | p50 8,6 s, p95 9,6 s (câu đầu khi chưa nạp sẵn: ~31 s) |
| RAM đỉnh tiến trình | ~2,2 GB |

Trần lý thuyết: khoảng 12,7 % câu sai thật; nếu tính cả các Điều tương đương (cùng nội dung ở văn bản khác) thì Hit@1 tối đa khoảng 86–87 %. Mục tiêu 90 % Hit@1 ban đầu **không đạt**, và không có cấu hình nào đo được đạt mức đó trên phần cứng này.

### 5.2 Thời gian

| Việc | Thời gian (Ryzen 5 5600GT, 2 luồng) |
|---|---|
| Tìm ở Normal | ~1 giây |
| Tìm ở Advance | ~9 giây (reranker ~5 giây của số đó) |
| Nhúng vector | ~3–4 Điều/giây (10 nghìn Điều ≈ 1 giờ; 61 nghìn ≈ 5–7 giờ, tiếp tục được sau khi dừng) |
| Nạp file | DOCX ~0,1 s, PDF chữ ~0,5 s, PDF scan ~1,7 s/trang |
| Cài đặt bộ cài | ~77 giây; đóng gói bộ cài ~11 phút |

### 5.3 Phương án đã đo và loại

| Phương án | Kết luận |
|---|---|
| Reranker top-10 thay vì top-5 | Hơn 0,5–1,8 điểm Hit@1 nhưng chậm gấp đôi → giữ top-5 |
| Phạt "hubness", ưu tiên văn bản mới hơn khi hoà điểm | Không ổn định giữa hai bộ đo → bỏ |
| Reranker gte, EmbeddingGemma 300M/EmbeddingGemma-2 | Kém AITeamVN trên bộ đo → bỏ |
| Fine-tune trên GPU thuê / huấn luyện từ đầu | Loại: yêu cầu chạy offline, không thuê hạ tầng, thời gian và độ chắc chắn kém |

Số đo chi tiết nằm trong `bench/*/KET-QUA.md`; các tập đo trong `bench/` (`zalo`, `gold`, `van-ban-that`, `stress10`).

---

## 6. Cấu hình

Biến môi trường (đều tuỳ chọn):

| Biến | Tác dụng |
|---|---|
| `SOILUAT_DATA` | Thư mục dữ liệu (mặc định `.\data` tính từ thư mục làm việc; lối tắt của bộ cài đặt thư mục làm việc là `%LOCALAPPDATA%\SoiLuat`) |
| `SOILUAT_PORT` | Cổng mong muốn (mặc định 8000, bận thì thử 20 cổng kế tiếp) |
| `SOILUAT_NO_BROWSER=1` | Không tự mở trình duyệt |
| `SOILUAT_MODEL_DIR`, `SOILUAT_RERANK_DIR` | Thư mục mô hình embedding / reranker (mặc định `<dữ liệu>\models\aiteamvn-*`, bản đóng gói: `models\` cạnh `SoiLuat.exe`) |
| `SOILUAT_SEMANTIC=0` | Tắt hoàn toàn phần vector và reranker (Advance chạy như Normal) |

Hằng số chỉnh chất lượng/tốc độ (đổi thì phải đo lại): `semantic.py` — `TOP`, `DENSE_K`, `RRF_K`, `W`, `DENSE_MIN`, `MAXLEN`, `THREADS`; `crossrank.py` — `TOPN`, `MAXLEN`, `THREADS`, `SURE_GAP`; `search.py` — `CANDIDATES`, `RETURN_TOP`, `BOOST`, `BIGRAM_ALPHA`.

Chế độ tìm (Normal/Advance) lưu trong `app_meta.search_mode` và đổi ở **Cài đặt**; mặc định Normal.

---

## 7. Dòng lệnh

```text
SoiLuat.exe                              mở app
SoiLuat.exe import <đường dẫn> [--ocr] [--nhung]     nạp hàng loạt (và nhúng ngay)
SoiLuat.exe import --nhung [--nen]       chỉ nhúng vector còn thiếu; --nen: 1 luồng, ưu tiên thấp
python -m soiluat.health                 khám sức khoẻ kho (CSV)
```

Nhúng vector dừng giữa chừng (tắt máy, Ctrl+C) thì chạy lại sẽ làm tiếp, vì vector được ghi từng đợt.

---

## 8. Đóng gói và phát hành

Cần máy build có Python 3.11+, `pip install -e ".[pack,word,ocr,nghia]"`, onnxruntime **1.22.1** (đã kiểm), Inno Setup 6, và thư mục mô hình.

1. **Xuất mô hình, một lần, cần mạng:** `python pack/export_models.py <thư mục>` tạo `aiteamvn-embedding\`, `aiteamvn-reranker\` (tokenizer + `onnx\model_int8.onnx` + `NOTICE.md`) và `LICENSE-Apache-2.0.txt`. Bản mô hình được ghim theo commit; `NOTICE.md` ghi nguồn, giấy phép và SHA-256 từng tệp. Phần xuất reranker (PyTorch → ONNX → int8) cần torch/transformers; embedding lấy ONNX fp32 do AITeamVN công bố rồi lượng tử hoá.
2. **Dựng gói:**

   ```text
   powershell -File pack\build.ps1 -Tesseract "C:\Program Files\Tesseract-OCR" -VieData <vie.traineddata> -Models <thư mục ở bước 1> [-Setup]
   ```

   Ra `dist\SoiLuat\` (onedir) và, nếu có `-Setup`, `dist\SoiLuat-Setup.exe`. `build.ps1` kiểm đủ tệp mô hình trước khi chép.
3. **Bộ cài** (`pack/SoiLuat.iss`): cài cho người dùng hiện tại, không cần quyền admin, vào `%LOCALAPPDATA%\Programs\SoiLuat`; kho dữ liệu ở `%LOCALAPPDATA%\SoiLuat\data` nên gỡ hoặc cài đè không mất kho.
4. Thư mục `dist` không nằm trong git; bộ cài 840 MB vượt giới hạn 100 MB mỗi file của GitHub, nên phát qua nơi khác hoặc GitHub Releases.

Giấy phép mô hình: cả hai mô hình AITeamVN theo Apache-2.0 (nền BGE-M3 giấy phép MIT, BGE-reranker-v2-m3 Apache-2.0); đã chuyển ONNX int8 nên phải giữ `NOTICE.md` và văn bản giấy phép kèm theo bản phát hành.

---

## 9. Bảo mật và riêng tư

- App chỉ nghe `127.0.0.1`; `HostGuard` từ chối `Host` khác `127.0.0.1`/`localhost`.
- Các thao tác ghi (đổi chế độ, duyệt liên kết, từ điển…) yêu cầu token CSRF khớp cookie `soiluat_csrf`.
- Không có gọi mạng: không phân tích sử dụng, không tải mô hình lúc chạy, không cập nhật tự động.
- Dữ liệu văn bản, nhật ký câu hỏi và vector chỉ nằm trong `data\`. Sao lưu: **Cài đặt → Sao lưu SQLite** (`db.backup_db`).
- Văn bản kiểm thử chứa dữ liệu thật không được đưa vào gói hay vào git.

---

## 10. Kiểm thử

- `pytest` (234 test qua, 2 bỏ qua khi thiếu mô hình thật): parser, nạp file, tìm kiếm, thẻ kết quả, bộ lọc, CSRF/Host, importer, đóng gói (`test_pack_spec.py`), `semantic` và `crossrank` (có `FakeRanker`, không cần mô hình).
- Hai test dùng mô hình thật chỉ chạy khi đặt `SOILUAT_MODEL_DIR` / `SOILUAT_RERANK_DIR`.
- Đo chất lượng: `bench/zalo`, `bench/gold` (có kiểm tra rò rỉ dữ liệu huấn luyện của mô hình), `bench/van-ban-that` (21 văn bản thật, phần lớn scan), `bench/stress10`.
- Nghiệm thu bản đóng gói: cài vào thư mục tạm, nhúng và hỏi thử, kiểm tra không có kết nối ngoài `127.0.0.1`, gỡ cài.

---

## 11. Giới hạn đã biết và việc chưa làm

- Hit@1 khoảng 79 % ở Advance: cứ khoảng 5 câu có 1 câu kết quả đầu sai; khoảng 1/40 câu Điều đúng ra ngoài 10 kết quả đầu. Nhãn "tin cậy cao" sai khoảng 1/16.
- Chưa thử trên máy 8 GB thật (RAM đỉnh đo ở máy 16 GB: ~2,2 GB).
- Nâng cấp từ bản dùng EmbeddingGemma: vector cũ bị bỏ qua (khác `model`), app nhúng lại nền; kho 61 nghìn Điều mất vài giờ.
- App không tự biết hiệu lực; không có nút xoá/sửa từng văn bản trong giao diện (nạp lại cùng đường dẫn thì cập nhật).
- Bộ cài chưa có chữ ký số, nên Windows SmartScreen cảnh báo.
- Ý tưởng chưa làm: gộp Điều trùng nội dung giữa các văn bản ("cũng có ở…"), từ điển viết tắt mở rộng, hiệu chỉnh `SURE_GAP` trên nhật ký câu hỏi thật.
