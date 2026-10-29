# Kế hoạch Soi Luật (bản 0.8)

Ứng dụng tra cứu văn bản pháp luật **chỉ cho máy văn phòng** (Windows, **8 GB RAM**, Word/Excel/trình duyệt có thể đang mở). Không có bản “đầy đủ” / semantic / LLM song song với bản này.

- **Ngày:** 21/10/2026 (0.7: 28/09/2026)
- **Sản phẩm:** Soi Luật = FTS5 + từ điển + parser + quy tắc + người duyệt. Gọi tắt **Lite** vì đó là toàn bộ phạm vi, không phải bản rút gọn của hệ thống khác.
- **Trạng thái:** bản 0.8; thay thế 0.7. Giữ Q1–Q6, F1–F4. 0.8 là bản **đưa code khớp thực tế file văn phòng** sau demo đo hiệu năng (`bench/BAO-CAO-DEMO.md`): thêm Q7 (từ điển khởi tạo), Q8 (đầu vào mở rộng), Q9 (hỏi “mức phạt”), và quy ước địa chỉ đơn vị mới (mục 4.3.9). Không đổi phạm vi: vẫn không embedding/LLM.
- **Checklist:** [soi-luat-checklist.md](soi-luat-checklist.md) **bản 0.8, có hiệu lực.** Không bám checklist 0.4–0.7 để tick việc.
- **Thay thế:** bản 0.7, 0.6, 0.5, 0.4 Lite, 0.3 (Markdown) và các bản kế hoạch HTML trước đó

Bản này là kế hoạch triển khai chính thức. Parser, FTS5, từ điển, OCR (Importer), thẻ, xuất Word và người duyệt liên kết/hiệu lực nằm trong sản phẩm. Embedding, vector, ONNX, RRF, LLM, RAG, Docker **không thuộc sản phẩm** — không ghi là bước sau.

**Phạm vi máy văn phòng:** Soi Luật = FTS5 + từ điển + parser + quy tắc + người duyệt. Không embedding, không vector, không ONNX Runtime, không RRF, không LLM, không llama.cpp, không RAG.

**Quyết định (Q1–Q6 giữ nguyên; 0.7 làm rõ F1–F4; 0.8 thêm Q7–Q9):**

| Mã | Nội dung |
|---|---|
| **Q1** | Rủi ro **không** bắt buộc phải có chế tài. Mọi quy định tạo ra nghĩa vụ, điều cấm, thời hạn hoặc điều kiện phải đáp ứng đều là rủi ro tiềm năng. Chế tài, nếu có, chỉ làm tăng thứ tự ưu tiên. |
| **Q2** | Chưa biết kho có nghị định xử phạt hay không. Đây là **điều kiện đầu vào** phải đếm ở tuần 1 (mục 2.6, 10), không phải giả định. |
| **Q3** | “Tổng hợp” = gom file vào một kho để tra cứu. **Không** sinh bộ Word thống nhất. Xuất Word chỉ là báo cáo từ thẻ người dùng chọn. |
| **Q4** | Giữ 8 tuần bằng cách **không làm trên máy văn phòng:** giao diện sửa ranh giới; giao diện sửa chữ OCR; giao diện tách file nhiều văn bản. Thay bằng sửa file nguồn (hoặc đánh dấu “chia theo đoạn”) rồi nạp lại. |
| **Q5** | Đối tượng quan tâm do người dùng nhập: danh sách **ưu tiên** và **hạ ưu tiên**. Chỉ so khớp chuỗi, không trích chủ thể. Có cụm ưu tiên → xếp lên. Cụm hạ ưu tiên trong cửa sổ khoảng 8 tiếng trước “phải” / “có trách nhiệm” → xếp xuống, nhãn phụ “nghĩa vụ của cơ quan khác”. **Không đổi hạng thẻ.** |
| **Q6** | Truy vấn có dấu: chạy hết 6 tầng trên nhánh có dấu trước. Chỉ khi nhánh đó ra **0 nhóm** mới chạy nhánh bỏ dấu. Mọi thẻ từ nhánh bỏ dấu mang nhãn “khớp khi bỏ dấu, có thể khác nghĩa”. |
| **Q7** | **Từ điển khởi tạo (0.8).** Gói kèm `synonyms_seed.csv`, nạp vào `synonyms` lúc khởi tạo DB bằng `INSERT OR IGNORE` (mỗi phiên bản file một lần, ghi hash vào `app_meta`; cặp người dùng đã xoá không bị nạp lại cho tới khi file seed đổi). Hai nhóm: **viết tắt pháp lý chuẩn** (BHXH, GTGT, PCCC, ĐTM… 67 cặp) nạp sẵn `approved = 1`; **diễn đạt khác / đồng nghĩa** (44 cặp) nạp `approved = 0`, chờ người duyệt ở `/review/synonyms`. Lý do: viết tắt là chuẩn của lĩnh vực, không có sai nghĩa; diễn đạt khác có thể đổi nghĩa pháp lý nên giữ nguyên nguyên tắc “người duyệt mới có hiệu lực”. Quy tắc 4.3.2 “chỉ `approved = 1`” **không đổi**. |
| **Q8** | **Đầu vào mở rộng (0.8).** Ngoài DOCX / PDF / TXT, Importer nhận `.doc` / `.rtf` (đổi sang DOCX tạm bằng Word COM, rồi LibreOffice, không có cả hai thì báo lỗi hướng dẫn), ảnh (`.jpg .jpeg .png .tif .tiff .bmp`, đi qua OCR), `.xlsx` (mỗi sheet một trang). DOCX đọc đủ bảng, footnote/endnote, comment, text box, header/footer (mục 2.9). **Nạp không bao giờ im lặng thất bại:** thiếu Tesseract thì báo `OcrUnavailable`; trang cần OCR mà không có `--ocr` thì job ghi cảnh báo; lỗi một file không dừng cả lượt. |
| **Q9** | **Hỏi “mức phạt” (0.8).** Cụm “mức phạt / bị phạt / xử phạt / chế tài / phạt tiền…” (có và không dấu) được bỏ khỏi truy vấn trước khi chạy tầng tìm; đơn vị chế tài hoặc có liên kết chế tài được đưa lên đầu; thẻ gắn `intent = muc_phat`. Chỉ đổi cách xếp thẻ, không đổi định nghĩa bốn hạng. |

> **Ghi chú về thứ tự kết quả (đính chính).** Mục 3.6 của bản 0.7 đã ghi: tầng khớp → hạng thẻ → Q5 → hiệu lực → BM25. Code 0.7 lại xếp theo hạng thẻ **trước**, nên thẻ khớp nguyên câu bị đẩy xuống dưới thẻ chỉ khớp lỏng (demo: vị trí 13). 0.8 sửa **code** cho đúng 3.6; không đổi kế hoạch. Chi tiết: ghi chú cuối mục 3.6.

---

## 0. Mục tiêu

Ứng dụng chạy nội bộ (local) làm ba việc:

1. **Tổng hợp** (Q3): gom các file nghị định, thông tư (Word, PDF, PDF scan) vào **một kho tra cứu**. Không chuẩn hoá thành một bộ Word thống nhất; không sinh “kho văn bản sạch” bắt buộc.
2. Người dùng nhập từ khoá, số hiệu, điều khoản hoặc câu hỏi ngắn.
3. Ứng dụng trả về các **rủi ro tiềm năng** (Q1) kèm **trích dẫn nguyên văn** và địa chỉ nguồn, theo bốn loại thẻ mục 3.4.

**Định nghĩa rủi ro (Q1):** không đòi hỏi đã nối được chế tài. Nghĩa vụ, điều cấm, thời hạn, điều kiện phải đáp ứng — đã là rủi ro tiềm năng. Có chế tài (và liên kết đã duyệt) thì thẻ được xếp trước.

**Nghị định xử phạt (Q2):** không giả định kho đã có văn bản xử phạt. Tuần 1 script 2.6 phải đếm. Nếu kho **không** có văn bản xử phạt, phần lớn thẻ sẽ là loại 3 (rủi ro chưa rõ chế tài); app **vẫn phải hữu ích** — nguyên văn nghĩa vụ/cấm/thời hạn/điều kiện + địa chỉ nguồn là đầu ra đúng, không phải lỗi.

**Ràng buộc máy văn phòng:**

- Máy mục tiêu: Windows 10/11, 4–8 nhân CPU, **8 GB RAM là ràng buộc cứng**, không GPU, không Docker.
- Cùng lúc người dùng vẫn mở Word, Excel và trình duyệt.
- Một người dùng, local-only; FastAPI chỉ lắng nghe trên `127.0.0.1`. Mọi request phải khớp header `Host` (`127.0.0.1:<cổng>` hoặc `localhost:<cổng>`); request ghi dữ liệu có CSRF; không bật CORS (mục 4.3.8).
- **Không embedding, vector index, ONNX Runtime, RRF, LLM hay RAG.** App phải trả kết quả dùng được chỉ bằng FTS5, từ điển nghiệp vụ, parser, quy tắc và khung kết quả cố định.
- DOCX, PDF có chữ, PDF scan, PDF trộn, ảnh chụp trang và `.xlsx` nằm trong sản phẩm. File `.doc` / `.rtf` cũ được đổi sang DOCX tạm lúc nạp nếu máy có Word hoặc LibreOffice; không có thì phải đổi trước khi nạp (Q8).
- **Không** giao diện sửa ranh giới, sửa chữ OCR, tách nhiều văn bản trong một file (Q4). Sửa nguồn rồi nạp lại.

**Cổng tuần 0 (trước khi viết code tìm kiếm/thẻ):** người dùng tự viết **5 từ khoá thật**, mỗi từ kèm kết quả mong đợi: loại rủi ro (1–4), Điều/Khoản của văn bản nào, có cần mức phạt trên thẻ hay không. Đồng thời cung cấp hai danh sách Q5 (ưu tiên / hạ ưu tiên), **tên đầy đủ** khi cụm một tiếng dễ nhầm (F3). Khung 3.4 / 4.3.1 phải biểu diễn được cả 5 từ khoá. Không biểu diễn được thì **sửa khung trước khi code**. Cập nhật `soi-luat-checklist.md` theo 0.8. Chi tiết mục 8 và 9.

---

## 1. Trả lời nhanh hai vấn đề

**Vấn đề 1: File có tuân theo mẫu để tách được không?**

- Văn bản quy phạm pháp luật chính thức phải theo thể thức nhà nước quy định. Cách đánh số Điều, Khoản, Điểm ổn định qua nhiều thời kỳ, nên phần lớn văn bản gốc tách được.
- Nhưng file thực tế thường lệch mẫu: OCR làm vỡ dòng, Word dùng đánh số tự động, file bị chỉnh sửa, ghép hoặc trích một phần.
- Cách xử lý:
  - Không coi cấu trúc là điều kiện bắt buộc.
  - Dùng bộ tách ba tầng có điểm tin cậy. Tách được thì trích dẫn đến Điều/Khoản/Điểm; không tách được thì vẫn trích dẫn đến "trang N, đoạn M".
  - Tuần đầu chạy một script đo toàn bộ kho để biết tỷ lệ thật, không đoán.
  - File lệch nặng: sửa file nguồn hoặc nạp với cờ “chia theo đoạn”, không có UI ranh giới (Q4).

**Vấn đề 2: Tổng hợp từ khoá đầu vào thành đầu ra hợp lý thế nào?**

“Tổng hợp” ở mục tiêu là **gom file vào kho** (Q3), không phải sinh văn bản mới. Đầu ra lúc gõ từ khoá là việc **lắp ráp thẻ** chứ không phải **sáng tác**. Quy trình:

1. Phân loại đầu vào: số hiệu, từ khoá ngắn, hay câu hỏi dài.
2. Chuẩn hoá: truy vấn có dấu chạy **hết 6 tầng** trên nhánh `{search_accent context_accent}` trước; **chỉ khi 0 nhóm** mới sang nhánh `{search_text context_search}` trên toàn kho (Q6). **Ngoại lệ F2:** unit trang OCR chưa `da_doi_chieu` luôn chạy thêm nhánh bỏ dấu **chỉ trên tập đó**, rồi gộp dù nhánh có dấu đã có nhóm. Truy vấn không dấu chỉ đi nhánh bỏ dấu. Mở rộng bằng từ điển đồng nghĩa đã duyệt (mục 4.3.2).
3. Tìm kiếm FTS5 (**cập nhật 22/10/2026:** một truy vấn BM25 OR lấy 300 ứng viên, nhân hệ số theo mức khớp cụm/gần/đủ từ/đồng nghĩa; thay cho thang 6 tầng AND có điều kiện dừng theo nhóm; đo trên Zalo: Hit@10 54,7% → 88,5%). Kết quả gom theo **nhóm (doc_id, Điều)**.
4. Lắp thẻ theo mục 4.3.1: tóm tắt → bốn loại thẻ Q1 → cảnh báo.

Câu chữ trong thẻ sinh từ mẫu câu, điền bằng dữ liệu trích từ chính văn bản. Không có mô hình sinh chữ.

Tìm theo từ **không** hiểu đồng nghĩa ngoài từ điển: gõ “rò rỉ dữ liệu” sẽ **không** ra đoạn “lộ, lọt thông tin” nếu chưa có cặp đã duyệt (mục 3.3). Đây là đánh đổi có chủ đích để máy 8 GB chạy được; đo bằng Recall@10 (mục 9, B11).

---

## 2. Vấn đề 1: Văn bản không theo mẫu

### 2.1 Căn cứ để kỳ vọng văn bản có cấu trúc

- **Luật Ban hành văn bản QPPL số 64/2025/QH15:** văn bản QPPL có thể bố cục theo phần, chương, mục, tiểu mục, điều, khoản, điểm; phần, chương, mục, tiểu mục, điều phải có tên. [1]
- **Nghị định 78/2025/NĐ-CP** quy định thể thức, kỹ thuật trình bày: [2]
  - Điều đánh số Ả Rập.
  - Khoản đánh số 1, 2, 3 kèm dấu chấm.
  - Điểm đánh chữ a, b, c kèm dấu đóng ngoặc.
  - Font Times New Roman, bảng mã Unicode TCVN 6909:2001.
- **Văn bản cũ hơn** theo Thông tư 25/2011/TT-BTP rồi Nghị định 34/2016/NĐ-CP. Quy ước Điều/Khoản/Điểm về cơ bản giữ nguyên qua các thời kỳ, nên một bộ quy tắc dùng được cho văn bản của nhiều năm. [3][4]

### 2.2 Những kiểu lệch mẫu sẽ gặp

| Kiểu lệch | Ví dụ | Hậu quả nếu không xử lý |
|---|---|---|
| Word đánh số tự động | "Điều 1.", "1.", "a)" là số của danh sách, không nằm trong chữ | Đọc thô mất số, không nhận ra ranh giới |
| OCR vỡ dòng, dính chữ | "Điều1.", "Điêu 5", "Diều 7", khoản nối liền vào dòng trước | Quy tắc chuẩn bỏ sót |
| Ký tự trông giống nhau | "Ð" (U+00D0, chữ Eth) thay cho "Đ" (U+0110), hay gặp ở file cũ; "d)" và "đ)" bị OCR nhầm | So khớp chuỗi trượt |
| Font cũ TCVN3/VNI | Hiển thị đúng nhưng mã ký tự sai | Tìm kiếm không ra gì |
| Văn bản hợp nhất, có chú thích | Chú thích "[1] Khoản này được sửa đổi bởi…" chen giữa | Chú thích bị gộp vào khoản |
| Văn bản sửa đổi | Nội dung khoản mới nằm trong ngoặc kép | Tách nhầm thành Điều của văn bản sửa đổi |
| Không có Điều | Công văn, quyết định cá biệt, hướng dẫn nghiệp vụ | Không tách được theo Điều |
| Nhiều văn bản trong một file | PDF scan cả tập | Metadata sai, Điều bị trùng số |
| Bảng, phụ lục | Bảng mức phạt, biểu mẫu | Mất cấu trúc hàng/cột; không tự ghép mức phạt từ bảng |

### 2.3 Nguyên tắc: cấu trúc là điểm cộng, không phải điều kiện

Mọi đoạn văn bản đều có **địa chỉ trích dẫn tối thiểu**: tên file, số trang, số thứ tự đoạn. Tách được cấu trúc thì địa chỉ **hiển thị** được nâng lên Văn bản (số hiệu hiện tại) > Điều > Khoản > Điểm. Khoá nội bộ là `(doc_id, path)` (mục 4.2, 4.3.3), không nhúng số hiệu vào khoá. Nhờ vậy:

- Văn bản không tách được vẫn tìm được và vẫn trích dẫn được.
- Không file nào bị bỏ khỏi kho chỉ vì sai mẫu.
- Hai file cùng số hiệu vẫn nạp được (hai `doc_id`).

### 2.4 Bộ tách ba tầng

**Tầng 1: quy tắc chuẩn**

Đầu đoạn khớp mẫu đúng thể thức:

```
ĐIỀU   ^Điều\s+(\d+[a-z]?)\.\s*(.+)
KHOẢN  ^(\d+)\.\s+
ĐIỂM   ^([a-zđ])\)\s+
```

**Tầng 2: quy tắc nới lỏng và tín hiệu định dạng**

Chuẩn hoá trước khi so khớp:

- Chuyển Unicode về NFC.
- Đổi "Ð" (U+00D0) thành "Đ" (U+0110).
- Chuyển mã TCVN3/VNI sang Unicode.

Mẫu nới lỏng:

- `(?i)^[ĐD]i[eêề]u\s*(\d+)\s*[.:]`: chấp nhận thiếu dấu cách, chữ hoa, dấu hai chấm, lỗi dấu do OCR.
- Khoản dạng `1)`, điểm dạng `a.`.

Tín hiệu định dạng:

- Với DOCX: dòng in đậm, cỡ chữ, thụt lề. **python-docx không tính sẵn số danh sách.** Phải tự mô phỏng bộ đếm từ `numbering.xml` (abstractNum, numId, ilvl, numFmt, lvlText) và từ `numPr` trên đoạn **hoặc** trên style (nhiều file chỉ gắn numbering ở style). Phương án dự phòng khi máy có Microsoft Word: đọc `Range.ListFormat.ListString` qua Word COM (`pywin32`). [cần kiểm chứng] tỷ lệ file trong kho chỉ có numbering trên style / cần COM. Ngoài fixture tạo bằng python-docx, kiểm thử bắt buộc có **ít nhất 3 file DOCX soạn bằng Microsoft Word thật**: numbering gắn trên đoạn; numbering gắn trên style; danh sách nhiều cấp (E6, mục 9).
- Với PDF: độ đậm của font, khoảng cách dòng.

Ràng buộc để loại nhận nhầm:

- "Điều 5" nằm giữa câu ("theo quy định tại Điều 5") không phải ranh giới. Ranh giới thường ở đầu đoạn; việc có tên Điều theo sau là một tín hiệu mạnh nhưng không phải điều kiện tuyệt đối với file lỗi.
- Với văn bản sửa đổi, nội dung trong ngoặc kép có thể là `replacement_content`: phải giữ nguyên cả khối và quan hệ với điều sửa đổi. Không được đơn giản bỏ các heading nằm trong khối; nếu chưa phân biệt chắc chắn thì nạp với “chia theo đoạn” hoặc sửa file nguồn (không có UI ranh giới, Q4).

**Tầng 3: dự phòng**

- Chia theo đoạn văn. Đoạn quá dài thì chia cửa sổ khoảng 300–400 chữ, chồng lấn khoảng 50 chữ.
- Giữ số trang, gắn nhãn "không có cấu trúc"; `path` dạng `p{trang}.para{n}`.
- Vẫn gắn nhãn nghĩa vụ/cấm/thời hạn/điều kiện/chế tài ở mức đoạn (mục 3.5).

Mỗi đơn vị **chỉ chứa chữ riêng của nó** (B4): Điều = tên Điều + câu dẫn của Điều (không gồm toàn bộ khoản/điểm con); Khoản = câu dẫn của khoản; Điểm = nội dung điểm. Câu dẫn của cha đưa vào `context_search` và `context_accent` để xếp hạng (C3: hai cột này phải nằm trong bộ lọc MATCH), không copy vào `raw_text` của con.

### 2.5 Điểm ưu tiên duyệt và độ tin cậy từng ranh giới

Ba thành phần, mỗi thành phần trong khoảng [0, 1]. Gọi `N` = số Điều tìm thấy, `L_nội` = số ký tự phần nội dung (đã bỏ quốc hiệu, căn cứ, phần ký), `L_trong_điều` = số ký tự thuộc các đơn vị mức Điều/Khoản/Điểm (chữ riêng, không đếm trùng cha–con).

- **C_phủ** = `L_trong_điều / max(1, L_nội)` rồi cắt vào [0, 1]. Mẫu số không bao giờ 0.
- **C_liên_tục** (B12):
  - Nếu `N = 0`: C_liên_tục = 0.
  - Nếu `N = 1`: C_liên_tục = 1 (Điều đầu khác 1 **không** tính nhảy cóc).
  - Nếu `N ≥ 2`: parse mỗi Điều thành `(n, s)` với `n` số nguyên, `s` hậu tố chữ (rỗng, `a`, `b`, …). **Không** so Điều đầu với số 1. Với mỗi cặp liên tiếp `(d_i, d_{i+1})`, cặp **bình thường** khi một trong các trường hợp:
    - `s_i` rỗng, `n_{i+1} = n_i + 1`, `s_{i+1}` rỗng;
    - `s_i` rỗng, `n_{i+1} = n_i`, `s_{i+1}` là `a`;
    - `s_i` khác rỗng, `n_{i+1} = n_i`, `s_{i+1}` là chữ Latin kế `s_i`;
    - `s_i` khác rỗng, `n_{i+1} = n_i + 1`, `s_{i+1}` rỗng.
    Cặp khác các trường hợp trên là **bất thường** (kể cả lặp số, nhảy cách).  
    `C_liên_tục = 1 − (số cặp bất thường) / max(1, N − 1)`.
- **C_khoản** = (số Điều có khoản đánh số liên tục từ 1, hoặc không có khoản nào) / `N` khi `N ≥ 1`; nếu `N = 0` thì C_khoản = 0.

Công thức gộp:

```
S = 0,4 × C_phủ + 0,3 × C_liên_tục + 0,3 × C_khoản
```

Mỗi C_i ∈ [0, 1] nên **0 ≤ S ≤ 1**. Cài đặt phải kẹp S vào [0, 1] nếu làm tròn.

Điểm S chỉ dùng để **xếp ưu tiên** (file nào nên sửa nguồn trước), không phải bằng chứng ranh giới đúng:

| S | Xử lý ban đầu |
|---|---|
| ≥ 0,90 | Dùng kết quả tầng 1/2; ưu tiên sửa nguồn thấp hơn nhưng vẫn lấy mẫu kiểm |
| 0,60 – 0,90 | Dùng kết quả; ghi vào danh sách file nên rà soát |
| < 0,60 | Dùng tầng 3 (chia đoạn), gắn nhãn "không có cấu trúc" |

Mỗi ranh giới Điều/Khoản/Điểm còn có `boundary_confidence` riêng dựa trên regex, vị trí đầu đoạn, định dạng, tính liên tục và ngữ cảnh.

Trọng số và ngưỡng trên là đề xuất ban đầu. Tuần 1 chỉnh lại theo dữ liệu thật: lấy ít nhất 20 văn bản đại diện đã kiểm tay; không dùng S để tự tuyên bố tài liệu đã được con người xác minh.

### 2.6 Đo kho văn bản ngay tuần đầu

Viết một script "khám sức khoẻ kho". Script chạy qua toàn bộ thư mục và xuất một file CSV, mỗi file văn bản một dòng:

```
file, loại (docx/pdf-chữ/pdf-scan/trộn), số trang, số trang có chữ,
số trang lớp chữ tốt / đáng ngờ / chỉ ảnh / trộn / có bảng,
số trang cần OCR, font cũ?, nghi có nhiều văn bản?, số Điều tìm thấy,
C_phủ, C_liên_tục, C_khoản, S, tầng dùng, số ranh giới confidence thấp,
số hiệu đoán được, ngày hiệu lực đoán được, RAM nạp đỉnh,
dung lượng nguồn / dữ liệu sinh thêm / dung lượng ước tính,
có_cụm_phạt_tiền_từ (0/1),   -- Điều nào đó chứa "phạt tiền từ"
```

**Q2 — đếm nghị định/văn bản xử phạt (không giả định):**

- `so_van_ban_co_phat_tien_tu` = số file có ít nhất một Điều (hoặc đoạn, nếu tầng 3) chứa chuỗi `"phạt tiền từ"` (so khớp không phân biệt hoa thường, trên chữ đã NFC).
- `ty_le_xu_phat` = `so_van_ban_co_phat_tien_tu / max(1, tong_so_file)`.
- Ghi hai số này vào dòng tổng kết CSV (không chỉ từng file).

Kết quả trả lời bằng số các câu hỏi:

- Bao nhiêu phần trăm văn bản tách tốt?
- Bao nhiêu phần trăm phải OCR?
- Bao nhiêu phần trăm cần sửa nguồn / nạp chia đoạn?
- Kho **có** văn bản xử phạt hay không, tỷ lệ bao nhiêu?

Nếu `ty_le_xu_phat = 0`, ghi rõ vào biên bản tuần 1: đầu ra chính sẽ là thẻ loại 3; không coi đó là thất bại của khung Q1.

Từ đó quyết định có cần đầu tư thêm cho OCR hay cho việc sửa file nguồn, **không** quyết định làm UI ranh giới trong 8 tuần.

### 2.7 Sửa văn bản điểm thấp (sửa nguồn, nạp lại)

Không có màn hình: thêm/bỏ ranh giới Điều; sửa chữ OCR trên trang; tách một file thành nhiều văn bản (Q4, mục 11).

Trong 8 tuần:

- Sửa Word/PDF/TXT **nguồn**, rồi nạp lại. Cùng `file_path` (UNIQUE), SHA-256 đổi → cập nhật **tại chỗ** cùng `doc_id` (mục 4.3.4), không mất `links` đã duyệt nếu `(doc_id, path)` hai đầu còn.
- File mới (đường dẫn khác), dù trùng số hiệu với file đã có, vẫn nạp thành `doc_id` khác — **trừ khi** trùng `sha256` với bản đã có: bỏ qua, job `skipped_duplicate` (E5).
- Đánh dấu **chia theo đoạn** lúc nạp (cờ Importer / file kèm), ép tầng 3 cho file đó.
- Sửa số hiệu, ngày, `hieu_luc` trên form metadata ngắn (không phải UI ranh giới). Đổi `so_hieu` **không** đổi `path`, không được làm mất liên kết đã duyệt.
- Hàng đợi **gợi ý hết hiệu lực** (B13): Importer không tự đổi `hieu_luc`; người bấm chấp nhận/từ chối.

Sửa nguồn / nạp lại xong phải rebuild unit/FTS (4.3.4). SHA-256 phát hiện file đổi; không chứng minh bản chính thức.

### 2.8 PDF: xử lý từng trang, ba lớp chữ

Không gộp cả file thành một khối “đọc chữ hoặc OCR”. Mỗi trang được phân loại riêng:

| Loại trang | Cách xử lý |
|---|---|
| Lớp chữ tốt | Dùng text PDF trực tiếp; lưu toạ độ chữ (bounding box) để tô sáng khi xem |
| Lớp chữ đáng ngờ | Lớp chữ quá ít, lệch encoding, hoặc không khớp layout → OCR lại **hoặc** ghi vào CSV tuần 1 để sửa nguồn |
| Chỉ có ảnh | Tesseract 5 + `vie` |
| Trang trộn chữ và ảnh | Giữ text layer có chất lượng, OCR riêng vùng ảnh cần thiết; không OCR đè toàn trang một cách mặc định |
| Trang có bảng/phụ lục | Giữ ảnh và text tuyến tính để đối chiếu; cảnh báo; **không** tự ghép mức phạt / thẻ chế tài từ hàng–cột chưa duyệt |

Cách nhận “lớp chữ đáng ngờ” (tuần 1 chỉnh ngưỡng trên dữ liệu thật), ví dụ:

- Tỷ lệ ký tự lấy được / diện tích trang quá thấp.
- Nhiều ký tự thay thế, font TCVN3/VNI chưa chuyển, hoặc chuỗi không phải tiếng Việt đọc được.
- Text layer không theo thứ tự đọc (cột, header/footer trộn vào thân).

**Ba lớp text**, lưu riêng, không ghi đè lên nhau:

1. **text nguồn / OCR thô** — đúng như máy đọc được; kèm phiên bản OCR nếu trang đi qua Tesseract.
2. **text để tìm** — hai cột trên unit (và tương ứng khi dựng từ trang): `search_accent` (mục 3.2) và `search_text` (fold). Không hiện `search_text` cho người dùng.
3. **text đã đối chiếu thủ công** — cột `reviewed_text` có trong lược đồ nhưng **không có UI sửa**. Muốn chữ đúng thì sửa nguồn hoặc OCR ngoài app rồi nạp lại. Cột thường NULL.

Mỗi trang có trạng thái OCR, ví dụ: `khong_can` | `cho_ocr` | `ocr_xong` | `can_duyet` | `da_doi_chieu`; đồng thời lưu engine, phiên bản, ngôn ngữ, confidence và vùng nguồn.

Trích dẫn từ trang OCR chưa `da_doi_chieu` phải mang nhãn **“Trích dẫn OCR chưa xác minh”** (mục 3.4). SHA-256 chỉ giúp phát hiện file trùng hoặc thay đổi.

### 2.9 Đọc file thực tế (0.8)

Demo trên 18 file lệch mẫu (`bench/BAO-CAO-DEMO.md`) cho thấy bản 0.7 mất nội dung hoặc không nạp được ở 9 loại file. 0.8 xử lý như sau; mọi chỗ vẫn đi qua `ExtractedPage` (chữ + `notes` + `ocr_conf`), parser không biết định dạng gốc.

| Tình huống | Cách xử lý 0.8 |
|---|---|
| Bảng Word | Đọc theo thứ tự thân văn bản (đoạn và bảng xen kẽ). Mỗi hàng một dòng `\| ô \| ô \|`; ô gộp ngang/dọc để ô rỗng giữ cột; bảng lồng dồn vào ô cha. Đơn vị chứa dòng bảng → `from_table = 1` (vẫn **không** lấy mức phạt từ bảng) |
| Footnote / endnote Word | Mốc `[^n]` ngay chỗ tham chiếu + `Note(kind = footnote/endnote)` trên trang có mốc |
| Comment, text box, header, footer Word | `Note` trên trang tương ứng (comment có `ref` = đoạn chữ được nhận xét ≤ 80 ký tự; text box chỉ đọc nhánh `mc:Choice`, không nhân đôi; header/footer bỏ bản trùng) |
| Ghi chú → đơn vị | Parser đổi `Note` thành đơn vị `level = ghi_chu`, `path = GC{n}`, cha là đơn vị chứa mốc nếu tìm được; **không gắn nhãn rủi ro** (hạng 4); thẻ hiện tối đa 3 ghi chú của Điều |
| Tách trang DOCX | Ngắt trang cứng, `w:lastRenderedPageBreak`, `pageBreakBefore` → số trang gần với Word |
| PDF có bảng | `find_tables()` cho bảng kẻ khung; thêm bộ dò bảng **không kẻ khung** (≥ 2 cụm chữ thẳng cột, dòng không có chữ ở cột đầu gộp vào hàng trước). Bảng thành dòng `\| … \|` đúng vị trí theo toạ độ y; không còn chữ hai ô trộn lẫn. Trang vẫn `kind = table` |
| `.doc` / `.rtf` | `convert.py`: Word COM (`SaveAs2` DOCX, luôn `Quit`) → LibreOffice `soffice --headless` → lỗi tiếng Việt nêu cách xử lý |
| Ảnh chụp trang | Mỗi ảnh / frame là một trang `kind = image`, `ocr_status = cho_ocr` |
| `.xlsx` | Đọc bằng `zipfile` + XML (sharedStrings, inlineStr, số, bool); mỗi sheet một trang, hàng dạng `\| … \|` |
| PDF trộn / lớp chữ rác | OCR thêm trang `mixed` mà ảnh phủ > 50% diện tích và chữ < 200 ký tự; trang có lớp chữ rác (> 30% ký tự lạ, `\ufffd`, `(cid:`, dấu hiệu font VNI/TCVN3) → `text_suspect` + `cho_ocr`. Không OCR đè trang chữ tốt |
| Tesseract | `ocr_status()` tìm theo thứ tự: env `SOILUAT_TESSERACT` → `PATH` → `C:\Program Files\Tesseract-OCR` → `%LOCALAPPDATA%\Programs\Tesseract-OCR` → thư mục `tesseract\` cạnh exe; tessdata theo `SOILUAT_TESSDATA` → `TESSDATA_PREFIX` → `%LOCALAPPDATA%\SoiLuat\tessdata` → `<tesseract>\tessdata`; phải có `vie`. Thiếu → `OcrUnavailable` (không còn bỏ qua im lặng). Lỗi một trang → `ocr_status = loi_ocr` |
| Tiền xử lý ảnh trước OCR | Render theo **dpi gốc của ảnh, kẹp 150–300** (trang không có ảnh: 300). Đo thực tế: ép 300 dpi lên bản scan 150–200 dpi làm OCR **kém đi** (d06: 95% → 58%). Chuyển xám, autocontrast, khử nghiêng ±5° (PIL, không OpenCV). OSD (tự xoay) **chỉ khi lượt đầu kém**: `ocr_conf < 75` hoặc chữ quá thưa (< 30 chữ cái / megapixel) → xoay, OCR lại, giữ bản conf cao hơn. `ocr_conf` thang 0–100 |
| Hai văn bản một file | Tách khi có dòng `Số: …/…`, tên loại viết hoa gần đó **và** Điều đánh số lại từ 1; văn bản thứ k ≥ 2 lưu `file_path = "<path>#vb{k}"`, `sha256 = "<sha>#vb{k}"`. Không đủ ba điều kiện → giữ một văn bản, đánh dấu `multi_document_suspected` |
| Định dạng Điều lệch | Nhận `ĐIỀU 1:`, `Điều thứ hai`, `Điều 3 .`, `Điều 4.Hiệu lực` (tên viết hoa), khoản `1)` `1/`, điểm `a.` `đ)`. `Chương` / `Mục` / khối “Nơi nhận” không thành đơn vị. Dòng trích dẫn (“…tại\\nĐiều 5.”) không bị nhận là Điều mới |
| Trùng số Điều/khoản/điểm | Hậu tố `~n` (mục 4.3.9); **không bao giờ** crash `UNIQUE(doc_id, path)`. Lỗi parse → chia đoạn, không mất file |
| Nội dung trước Điều đầu tiên | Bỏ phần mở đầu chuẩn (quốc hiệu, tên cơ quan, `Số:`, nơi–ngày, `Căn cứ…`); giữ khoản/điểm “mồ côi” và đoạn thân bài thành `doan` (ví dụ ảnh chụp trang 2 của văn bản) |
| Metadata | `ngay_ban_hanh` (dòng “…, ngày … tháng … năm …”) và `ngay_hieu_luc` (“có hiệu lực từ ngày …”) dạng `YYYY-MM-DD`, tìm trong 40 dòng đầu / toàn văn; `loai` suy từ dòng tên loại → số hiệu → dòng “V/v” (`cong_van`) → NULL, **không** là đuôi file. Không đụng `hieu_luc` |
| Số trang thật | `page_from` / `page_to` của mọi đơn vị tính từ ranh giới trang (Điều phủ cả khoản/điểm con); thẻ hiện “Trang x–y” |

Giới hạn đã biết (chưa xử lý): Điều nằm trong phần trích dẫn dùng ngoặc kép cong `“ ”` (parser chỉ nhận `"`); bảng không kẻ khung có thể nhận nhầm ở phần đầu văn bản hai cột trong PDF thật; tách văn bản không đủ khối đầu.

---

## 3. Vấn đề 2: Từ từ khoá đến kết quả hợp lý

### 3.1 Phân loại đầu vào

| Loại | Nhận biết | Xử lý |
|---|---|---|
| Số hiệu, điều khoản cụ thể | Khớp mẫu `(?i)\d+/\d{4}/[A-ZĐ0-9-]+`, hoặc thiếu đuôi `(?<!\d)\d+/\d{4}(?!/\S)` (F4), hoặc "Điều 5 Nghị định 15/2020" | Tra thẳng trên `so_hieu_search` và `path` (mục 4.3.3), không qua FTS nhiều tầng |
| Từ khoá ngắn (1–4 từ) | Ít tiếng, không có từ hỏi | Tách từ (4.3.2) → FTS5 nhiều tầng |
| Câu dài, câu hỏi | Có từ hỏi ("như thế nào", "có được không", "bao nhiêu", "là gì", "phải làm gì", "bao lâu", "khi nào") | 0.8: bỏ khung hỏi (“xin hỏi”, “quy định về việc”, “có phải … không”…), bỏ chủ ngữ đứng trước “có phải / có được / có cần” khi phần sau còn chữ, chỉ cắt từ đệm ở hai đầu câu (giữ cụm cho tầng 1); “không” chỉ bỏ khi đứng cuối câu → như từ khoá |
| Hỏi mức phạt (Q9) | Có “mức phạt / bị phạt / xử phạt / chế tài / phạt tiền…” (có hoặc không dấu) | Bỏ cụm này khỏi truy vấn, chạy như từ khoá, thẻ `intent = muc_phat`: đơn vị chế tài / có liên kết chế tài lên đầu (mục 3.6). Bỏ hết chữ thì giữ nguyên truy vấn |

### 3.2 Chuẩn hoá, hai cột tìm, và mở rộng

**Chuẩn hoá hiển thị:** NFC. Nguyên văn (`raw_text` / `reviewed_text`) giữ nguyên để hiện trên thẻ.

**`search_accent` (B1):** Unicode NFC; chữ thường; đổi `Ð` (U+00D0) thành `Đ` (U+0110); **giữ dấu** nguyên âm; gộp khoảng trắng. Không đổi `đ` thành `d`.

**`search_text` (fold, truy vấn không dấu):**

```
Điều kiện hoạt động
→ dieu kien hoat dong
```

Thứ tự trên `search_text`:

1. Unicode NFC.
2. Chữ thường.
3. `Đ`, `đ`, và `Ð` (U+00D0) thành `d`.
4. Bỏ dấu nguyên âm (ổ → o, ộ → o, ễ → e, …).
5. Gộp khoảng trắng.

Không phụ thuộc SQLite `remove_diacritics` để ánh xạ `đ → d`. Tokenizer FTS5: `unicode61 remove_diacritics 0` — **không** nhờ tokenizer gỡ dấu. [5]

**Vì sao không chỉ tìm trên cột bỏ dấu:** sau khi bỏ dấu, một số cặp tiếng Việt trùng nhau, ví dụ **thuế / thuê**, **phạt / phát**, **cấm / cam**, **lãi / lại**. Gõ có dấu phải ưu tiên `search_accent` để “thuế” không ra đoạn chỉ có “thuê”.

**Cách chọn nhánh lúc gõ (Q6):**

- Truy vấn **có dấu** (còn dấu thanh hoặc `đ`/`Đ` sau NFC): chạy **đủ 6 tầng** trên nhánh có dấu (`{search_accent context_accent}`, mục 4.3.2), kể cả điều kiện dừng trong nhánh đó. **Chỉ khi** sau cả nhánh số nhóm = 0 mới chạy nhánh bỏ dấu **trên toàn kho**. Mọi thẻ sinh từ nhánh bỏ dấu toàn kho gắn nhãn phụ **“khớp khi bỏ dấu, có thể khác nghĩa”**.
- **Ngoại lệ OCR (F2):** unit thuộc trang OCR chưa `da_doi_chieu` **luôn** chạy thêm nhánh bỏ dấu, **giới hạn trong tập unit OCR đó**, rồi **gộp** vào kết quả dù nhánh có dấu đã có nhóm. Thẻ có hit từ nguồn này mang **cả** nhãn OCR (**Trích dẫn OCR chưa xác minh**) và nhãn Q6. Không được loại unit OCR chỉ vì nhánh có dấu đã có kết quả.
- Truy vấn **không dấu**: chỉ nhánh `{search_text context_search}` (fold đ→d); không gắn nhãn Q6 (trừ khi thẻ đã mang nhãn OCR vì trang chưa đối chiếu).

Kết quả **cuối cùng** hiện cho người dùng khi gõ `thuế`: không chứa đoạn **chỉ** có `thuê` trên văn bản không-OCR, trừ đúng trường hợp nhánh có dấu ra 0 nhóm — khi đó thẻ phải mang nhãn Q6. Đoạn OCR sai dấu của cùng nội dung **được** nằm trong kết quả (F2), kèm hai nhãn.

**Từ điển đồng nghĩa và viết tắt:**

- Người dùng tự quản lý, dạng bảng hai cột. Ví dụ: "TCTD" ↔ "tổ chức tín dụng", "phạt" ↔ "xử phạt", "chậm" ↔ "không đúng thời hạn".
- App tự gợi ý thêm cặp mới từ kho: các cụm hay đứng gần nhau. Người dùng bấm đồng ý mới được thêm vào từ điển.
- Mở rộng có kiểm soát:
  - Cụm gốc được trọng số (tầng) cao hơn cụm mở rộng.
  - Kết quả nào chỉ khớp nhờ từ đồng nghĩa thì ghi rõ "khớp theo từ đồng nghĩa X".

### 3.3 Tìm kiếm FTS5 nhiều tầng (không embedding, không RRF)

Một nhánh FTS5 trên năm cột `title_search`, `search_accent`, `search_text`, `context_search`, `context_accent` (mục 4.2). MATCH luôn kèm cột context của cùng nhánh (C3). Thuật toán tầng, escape, tách từ, IDF, điều kiện dừng: 4.3.2.

**Giới hạn có chủ đích:** tìm theo từ đã tách + từ điển đã duyệt, không theo nghĩa. Ví dụ: gõ `rò rỉ dữ liệu` **không** ra đoạn viết `lộ, lọt thông tin` nếu `synonyms` chưa có cặp đó. Đo thiếu sót bằng Recall@10 (B11), không bằng cách cài embedding.

Ví dụ truy vấn `chậm báo cáo định kỳ`. Giả sử từ điển đã duyệt có `chậm` → `không đúng thời hạn` (không tự bịa cặp khác):

| Thứ tự | Tầng | Ví dụ (sau escape, mục 4.3.2) | Ưu tiên |
|---:|---|---|---|
| 1 | Cụm đúng (phrase) | `"chậm báo cáo định kỳ"` trên cột phù hợp | Cao nhất |
| 2 | NEAR trong cửa sổ 10 | `NEAR("chậm" "báo cáo" "định kỳ", 10)` | Cao |
| 3 | Tất cả từ (AND) | `"chậm" AND "báo cáo" AND "định kỳ"` | Cao |
| 4 | Thay từ bằng `alt` đã duyệt | Union tầng 3 với truy vấn đã thay `"chậm"` → `"không đúng thời hạn"` AND các từ còn lại. Không AND chung mọi token gốc lẫn alt | Trung bình |
| 5 | Bớt **một từ** IDF thấp nhất (mục 4.3.2, E3) | Bỏ từ generic, giữ các từ còn lại AND | Thấp hơn |
| 6 | Cụm lõi còn lại | AND các từ còn | Thấp nhất, chỉ khi chưa đạt dừng |

- Mỗi token đưa vào `MATCH` đã bọc `"..."`; `"` trong token nhân đôi. Không ghép chuỗi gõ thô. Từ `AND`, `OR`, `NOT`, `NEAR` của người dùng cũng là token đã quote, không thành toán tử.
- Tách truy vấn thành **từ** bằng so khớp dài nhất với bộ từ vựng: `synonyms.term`/`alt` đã duyệt, tên các Điều trong kho, cụm 2–3 tiếng hay gặp trong kho (thống kê lúc nạp, không dùng để bịa đồng nghĩa). Không bớt theo từng âm tiết (`bao` / `cao` từ “báo cáo” nếu “báo cáo” đã là một từ vựng).
- Không gợi ý chính tả (mục 4.3.7).
- Lọc theo bộ lọc người dùng: loại văn bản, cơ quan, còn hiệu lực.
- Trong cùng tầng: loại thẻ (3.6), Q5 đối tượng, hiệu lực, BM25. Cột context chỉ có tác dụng BM25 khi nằm trong bộ lọc MATCH (C3).
- Văn bản `hieu_luc = 'het'`: thẻ màu xám, xếp **cuối** (B13).
- Thẻ từ nhánh bỏ dấu (Q6, kể F2): nhãn phụ “khớp khi bỏ dấu, có thể khác nghĩa”.

Không dùng vector, không dùng Reciprocal Rank Fusion.

**Điều kiện dừng:** sau mỗi tầng, gom `H` thành nhóm `(doc_id, Điều)` (hay `(doc_id, path` tầng 3 `pN.para…` nếu không có Điều)). **Dừng** khi:

- ≥ 5 nhóm có ít nhất một đơn vị mang nhãn `NGHIA_VU`, `CAM`, `THOI_HAN`, `DIEU_KIEN` hoặc `CHE_TAI`; **hoặc**
- ≥ 10 nhóm bất kỳ.

Đếm **nhóm đã gom**, không đếm từng khoản/điểm (B7).

### 3.4 Lắp ráp kết quả theo khung cố định

Mọi kết quả cùng bố cục năm phần. Không phần nào do máy tự sáng tác.

**Cách gọi thẻ** — thứ tự ưu tiên Q1. Không gọi “đã xác nhận” theo nghĩa pháp lý; chỉ nói **liên kết đã duyệt** (người đã bấm Đúng trên cặp nghĩa vụ–chế tài):

| Hạng | Điều kiện | Tên thẻ |
|---:|---|---|
| 1 | Có ít nhất một `links.confirmed = 1` gắn với nhóm (nghĩa vụ/cấm/hạn/điều kiện ↔ chế tài) | **Rủi ro (liên kết đã duyệt)** |
| 2 | Có nhãn `CHE_TAI`, **hoặc** có `links` nhưng không có `confirmed = 1` (máy gợi ý `confirmed = 0`). Gồm cả đơn vị `CHE_TAI` **chưa nối** được nghĩa vụ | **Rủi ro có chế tài (chưa có liên kết đã duyệt)** |
| 3 | Có nhãn rủi ro `NGHIA_VU` / `CAM` / `THOI_HAN` / `DIEU_KIEN`, **không** có `CHE_TAI` trong nhóm, **không** có `links` | **Rủi ro: nghĩa vụ / điều cấm / thời hạn / điều kiện, chưa rõ chế tài** |
| 4 | Không thuộc 1–3 (định nghĩa, quyền, đoạn khác; **không** gồm `CHE_TAI` đứng một mình) | **Quy định liên quan** |
| (nhãn phụ) | Trang OCR chưa `da_doi_chieu` | **Trích dẫn OCR chưa xác minh** — không đổi hạng 1–4 |
| (nhãn phụ) | Q5 hạ ưu tiên | **nghĩa vụ của cơ quan khác** — không đổi hạng |
| (nhãn phụ) | Q6 nhánh bỏ dấu | **khớp khi bỏ dấu, có thể khác nghĩa** — không đổi hạng |

Nhãn rủi ro (hạng 3): `NGHIA_VU`, `CAM`, `THOI_HAN`, `DIEU_KIEN`. Nhãn `CHE_TAI` (kể cả chưa có `links`) → **hạng 2**, không rơi hạng 4. Hạng 1 chỉ khi đã có liên kết người duyệt.

```
A. TÓM TẮT
   Tìm thấy {n1} rủi ro (liên kết đã duyệt), {n2} rủi ro có chế tài (chưa có liên kết đã duyệt),
   {n3} rủi ro chưa rõ chế tài, {n4} quy định liên quan,
   trong {m} văn bản ({m_hl} còn hiệu lực).

B. THẺ (mỗi thẻ = một nhóm doc_id + Điều, hoặc một đoạn nếu không có Điều)
   Nhãn   : bốn tên thẻ ở bảng trên
   Tiêu đề: {tên Điều} hoặc {cụm hành vi trích từ khoản/điểm}
   Câu mẫu: Không thực hiện / thực hiện hành vi bị cấm / không đáp ứng
            điều kiện / không đúng thời hạn tại {địa chỉ hiển thị}
            [có thể bị {hình thức} {từ X đến Y đồng} theo {địa chỉ chế tài}].
            (Không điền ô chủ thể. Hạng 2 hiện mức phạt theo đúng quy tắc
            dưới đây; không rõ đối tượng áp dụng thì không in số tiền.
            Liên kết máy gợi ý ghi “máy gợi ý, chưa duyệt”.)
   Nghĩa vụ / cấm / hạn / điều kiện: "…nguyên văn…"  — {địa chỉ hiển thị} · trang
   Chế tài : "…nguyên văn…"  — {địa chỉ hiển thị} · trang   (hạng 1 và hạng 2, nếu có)
   Trạng thái hiệu lực: còn / hết / chưa rõ  (hết: xám, cuối danh sách)
   Liên kết: đã duyệt / máy gợi ý / chưa nối nghĩa vụ / không có
   OCR     : (nếu có) Trích dẫn OCR chưa xác minh
   Q5      : (nếu có) nghĩa vụ của cơ quan khác
   Q6      : (nếu có) khớp khi bỏ dấu, có thể khác nghĩa

C. QUY ĐỊNH LIÊN QUAN
   Các đoạn khớp không mang nhãn rủi ro (định nghĩa, quyền, thủ tục…),
   hiện nguyên văn kèm địa chỉ hiển thị.

D. CẢNH BÁO
   - Kết quả từ văn bản chưa rõ hiệu lực.
   - Kết quả từ văn bản hết hiệu lực (xám).
   - Kết quả từ trang OCR độ tin cậy thấp / chưa đối chiếu: bấm để xem ảnh trang gốc.
   - Kết quả từ văn bản "không có cấu trúc": địa chỉ chỉ đến trang/đoạn.
   - Trang có bảng: mức phạt không tự ghép từ bảng.
   - Kho ít hoặc không có văn bản xử phạt (Q2): hầu hết thẻ loại 3 là đúng thiết kế.

E. KHI KHÔNG TÌM THẤY
   "Không tìm thấy quy định khớp với '{từ khoá}' trong kho."
   Gợi ý: các term/cụm đã có trong từ điển đã duyệt (nếu có).
   Không gợi ý chính tả, không đưa ra nội dung suy đoán.
```

**Quy tắc điền câu mẫu:**

- Chỉ điền ô khi dữ liệu trích được từ văn bản. Thiếu ô nào thì bỏ cả cụm chứa ô đó.
- **Không** điền ô chủ thể.
- **Mức phạt cá nhân / tổ chức:** không tự quy đổi. Không xác định được đối tượng áp dụng thì **không** hiện số tiền trên câu mẫu; hiện nguyên văn chế tài và ghi chú `[kiểm tra quy định về mức phạt của nghị định này]`.
- Không tự lấy số tiền từ trang đánh dấu là bảng.
- `fine_min` / `fine_max` trên **điểm** hành vi kế thừa câu dẫn khoản cha; cột `fine_source_unit` trỏ đơn vị nguồn (B2).

Cách biến danh sách đơn vị FTS thành các thẻ trên: mục 4.3.1.

### 3.5 Dữ liệu để lắp thẻ: gắn nhãn và nối chế tài

Việc này làm trong lúc nạp (Importer), không làm lúc tìm. Một đơn vị có thể mang **nhiều nhãn** (bảng `unit_labels`, mục 4.3.6). Ontology **chỉ** là các nhãn này cộng bảng `links` — không có ontology đầy đủ, không phát hiện mâu thuẫn liên văn bản (mục 11, A4).

**Gắn nhãn bằng từ khoá pháp lý** (bảng từ khoá mở rộng được):

| Nhãn | Dấu hiệu (ví dụ) |
|---|---|
| NGHĨA_VỤ | "phải", "có trách nhiệm", "có nghĩa vụ" |
| CẤM | "không được", "nghiêm cấm", "cấm" |
| THỜI_HẠN | "trong thời hạn", "chậm nhất", "trước ngày", "kể từ ngày" |
| ĐIỀU_KIỆN | "phải đáp ứng", "điều kiện" |
| QUYỀN | "có quyền", "được quyền", "được phép" |
| CHẾ_TÀI | Chỉ theo quy tắc F1 dưới bảng — **không** gắn vì gặp chữ `"buộc"` / `"bắt buộc"` / `"ràng buộc"` đơn lẻ |
| ĐỊNH_NGHĨA | Khoản thuộc Điều có tên "Giải thích từ ngữ" |

**Phủ định (B8):** không gán `NGHIA_VU` (và không suy thành nghĩa vụ từ “phải”) khi cụm là `"không phải"`, `"không bắt buộc"`, `"không có nghĩa vụ"`. [cần kiểm chứng] danh sách phủ định đủ cho kho thật — đo precision/recall mục 9. `"không bắt buộc"` chỉ là phủ định nghĩa vụ; **không** phải dấu hiệu `CHE_TAI`.

**Gắn `CHE_TAI` (F1)** — Importer, lúc nạp. Chỉ gắn khi **một** trong hai:

1. Chữ riêng đơn vị có dạng `"phạt … đối với hành vi"` (kể `"đối với các hành vi sau"`, `"đối với một trong các hành vi"`).
2. Đơn vị là **điểm** nằm dưới khoản cha có câu dẫn dạng đó.

Thêm: tiếng **đầu** của chữ riêng đơn vị đúng là `"buộc"` (ranh giới từ; **không** khớp trong `"bắt buộc"` / `"ràng buộc"`) **và** khoản cha (hoặc Điều) có tên / câu dẫn `"Biện pháp khắc phục hậu quả"`. Loại `"bắt buộc"`, `"ràng buộc"` — không gắn `CHE_TAI`.

**Không** gắn `CHE_TAI` cho Điều (và đơn vị con) có tên thuộc quy định chung: `"Hình thức xử phạt"`, `"Mức phạt tiền"`, `"Thẩm quyền xử phạt"`, `"Thời hiệu"` (so khớp tên Điều, chữ có dấu, không cần đúng hoa thường vì các tên này từ hai tiếng trở lên).

Fixture mục 9: `"thông tin bắt buộc"` → không `CHE_TAI`; Điều `"Thẩm quyền xử phạt"` → không `CHE_TAI`; điểm dưới `"Phạt tiền từ … đối với các hành vi sau"` → `CHE_TAI`.

**Trích chế tài — cấu trúc nghị định xử phạt thường gặp (B2):** [cần kiểm chứng] kho tuần 1 có đúng dạng này hay không (liên quan Q2).

Cấu trúc xử lý:

- Câu dẫn **khoản**: `"Phạt tiền từ A đồng đến B đồng đối với một trong các hành vi sau đây:"`.
- Hành vi nằm ở **điểm** a), b), c)…
- Hình thức bổ sung / biện pháp khắc phục ở các **khoản sau**, dẫn chiếu `"điểm a khoản 1 Điều này"` (và biến thể cùng Điều).

Quy tắc:

1. Đơn vị chế tài để gắn `fine_*` và nối `links.sanction_unit` là **điểm** (không gán mức phạt cho cả khoản rồi thôi).
2. `fine_min` / `fine_max` trên điểm **kế thừa** từ câu dẫn khoản cha; `fine_source_unit` = `units.id` của khoản (hoặc Điều) chứa câu dẫn. Không copy số từ bảng.
3. Bắt dẫn chiếu nội bộ cùng Điều (`Điều này`, `khoản này`) để nối khoản hình thức bổ sung / khắc phục vào đúng điểm hành vi (`links.method = dan_chieu` hoặc `noi_bo`, `confirmed = 0`).
4. Parse số tiền: `"10.000.000 đồng"`, `"01 triệu đồng"`, `"triệu đồng"` sau số. Dạng `"gấp … lần"` và `"…% …"` → `fine_min`/`fine_max` = NULL (vẫn giữ nguyên văn).
5. Cá nhân / tổ chức: không quy đổi. Không chắc đối tượng → câu mẫu không in số, chỉ nguyên văn + ghi chú mục 3.4.

**Nối chế tài với nghĩa vụ / cấm / hạn / điều kiện:**

1. Có dẫn chiếu tường minh ("vi phạm quy định tại khoản 2 Điều 5 Thông tư số …"): regex, `links.method = dan_chieu`, `confirmed = 0`.
2. Không có dẫn chiếu: cụm sau "đối với hành vi", FTS tầng 1–3 trên đơn vị đã có nhãn `NGHIA_VU`/`CAM`/`THOI_HAN`/`DIEU_KIEN`; `synonyms.kind = hanh_vi` đã duyệt thì thay token như 4.3.2. Tối đa 3 ứng viên. Người bấm Đúng/Sai trên `/review` (UI này **giữ** — không thuộc Q4).
3. Trên thẻ: `confirmed = 1` → hạng 1; `CHE_TAI` hoặc `links` chỉ `confirmed = 0` → hạng 2 (kể cả chế tài chưa nối nghĩa vụ); nhãn rủi ro không `CHE_TAI` không `links` → hạng 3.

### 3.6 Gom nhóm và xếp hạng

**Gom nhóm:**

- Mọi hit cùng `doc_id` và cùng Điều (`path` có tiền tố `D{n}` giống nhau) thành **một thẻ**. Không có Điều: mỗi `path` tầng 3 một thẻ.
- **Không** gom theo văn bản thay thế/bãi bỏ tự động. B13 chỉ **gợi ý** hết hiệu lực vào hàng đợi.
- Hiện điểm/khoản BM25 cao nhất trước; nguyên văn hit khác thu gọn trong thẻ.

**Xếp hạng:**

1. Tầng tìm kiếm (mục 3.3), tầng 1 trước tầng 6. Nhánh có dấu trước nhánh bỏ dấu toàn kho (Q6). Hit F2 (OCR bỏ dấu) gộp sau, không thay tầng đã đạt của hit có dấu.
2. Trong cùng tầng: thẻ hạng 1 trước 2 trước 3 trước 4.
3. **Q5 — đối tượng quan tâm** (sau hạng thẻ, trước hiệu lực). Không đổi hạng. **Luật so khớp (F3):**
   - Chỉ trên **chữ có dấu** (`normalized_text` / `title` / câu dẫn cha accent / tên Điều). **Không** so trên `search_text`, `phrase_fold` hay bất kỳ chuỗi đã bỏ dấu.
   - Ranh giới **từ nguyên** (không khớp mảnh nằm trong từ khác).
   - Nhiều cụm chồng nhau: **cụm dài nhất thắng** (ví dụ `"Ngân hàng Nhà nước"` thắng `"ngân hàng"`).
   - Cụm **dưới 2 tiếng** phân biệt hoa thường (`"Bộ"` ≠ `"bộ"`). Cụm từ 2 tiếng trở lên không phân biệt hoa thường trên chữ có dấu. Khuyến nghị người dùng nhập **tên đầy đủ**.
   - Đơn vị hoặc Điều cha chứa cụm `subject_rules.kind = 'uu_tien'` (`approved = 1`) → xếp **lên**. Ví dụ: `"tổ chức tín dụng"`, `"ngân hàng"`, `"doanh nghiệp"`.
   - Cụm `ha_uu_tien` (ví dụ `"cơ quan nhà nước"`, `"Bộ"`, `"Ủy ban nhân dân"`, `"Thanh tra"`, `"cơ quan có thẩm quyền"`) trong cửa sổ **khoảng 8 tiếng** ngay trước `"phải"` hoặc `"có trách nhiệm"` (chữ riêng + câu dẫn cha, vẫn chữ có dấu) → xếp **xuống**, nhãn phụ **“nghĩa vụ của cơ quan khác”**.
   - **Thêm:** tên Điều khớp `"Trách nhiệm của " + {cụm hạ ưu tiên}` (cùng luật từ nguyên / dài nhất / hoa thường) → các đơn vị thuộc Điều đó xếp xuống như hạ ưu tiên, cùng nhãn phụ.
4. Còn hiệu lực trước chưa rõ; **hết hiệu lực cuối cùng** và tô xám.
5. BM25 (chữ riêng nặng hơn context; MATCH phải gồm cột context, C3).

Hai hệ số tinh chỉnh (nếu cần) chỉ khi đã cùng tầng và cùng loại thẻ. Chỉnh lại sau bộ 5 từ khoá tuần 0 và bộ 50 từ khoá mục 9.

**Khoá sắp xếp cài đặt ở 0.8** (`cards.assemble_cards`), theo thứ tự ưu tiên:

1. `hieu_luc = het` **cuối toàn danh sách** (không chỉ cuối trong cùng tầng; khớp B13 và checklist “xám + xếp cuối”).
2. Hỏi mức phạt (Q9): thẻ hạng 1–2 trước các thẻ khác.
3. `match_tier`: tầng thấp nhất (tốt nhất) trong nhóm; tra số hiệu / Điều = tầng 0. Server mang tầng theo từng id (`CascadeResult.tiers`).
4. Hạng thẻ 1 → 4.
5. Q5 (ưu tiên → trung tính → hạ ưu tiên).
6. Hiệu lực `con` trước `chua_ro`.

Không truyền `tiers` (ví dụ xuất Word từ thẻ đã chọn) thì `match_tier = 0` và thứ tự rơi về hạng → Q5 → hiệu lực như 0.7. Bản 0.7 của **code** bỏ qua bước 3 nên thẻ khớp nguyên câu bị đẩy xuống (demo: thứ 13/63); đây là sửa code cho đúng kế hoạch, không phải đổi kế hoạch.

---

## 4. Kiến trúc gọn: Search App và Importer tách process

### 4.1 Hai tiến trình

OCR và parser nặng. Tiến trình tra cứu **không** import Tesseract/OpenCV khi khởi động. Có thể dùng chung giao diện (nút “Nạp văn bản” mở Importer), nhưng **không thường trú cùng một process**.

```
Thư mục văn bản (DOCX / PDF / PDF scan)
        │
        ▼
SoiLuatImporter.exe     ← chỉ chạy khi nạp tài liệu
  đọc DOCX/PDF, phân loại từng trang, render ảnh,
  OCR Tesseract, parser 3 tầng, metadata, gắn nhãn,
  gợi ý liên kết chế tài, gợi ý hết hiệu lực (B13)
        │
        ▼
soiluat.db (SQLite WAL)  +  thư mục bản gốc  +  ảnh/trang dẫn chứng
        ▲
        │
SoiLuat.exe             ← tra cứu, luôn nhẹ
  FastAPI 127.0.0.1, Host/CSRF, HTMX, FTS5
  duyệt links + gợi ý hiệu lực (không UI ranh giới/OCR/tách file)
        │
        └──► Xuất báo cáo Word (từ thẻ đã chọn; không kho Word chuẩn hoá)
```

| Process | Việc | Thư viện nặng lúc chạy |
|---|---|---|
| `SoiLuat.exe` | Tra cứu, xem thẻ, xuất Word, xác nhận liên kết / gợi ý hiệu lực | FastAPI, SQLite; **không** Tesseract/OpenCV |
| `SoiLuatImporter.exe` | Đọc file, vẽ trang, OCR, parser | python-docx, pdfplumber, pypdfium2, Pillow (tiền xử lý ảnh; 0.8 **không** dùng OpenCV), Tesseract; tùy chọn pywin32 (Word COM, đổi `.doc` / `.rtf`) |

- Dữ liệu gồm `soiluat.db`, thư mục nguồn, ảnh/trang dẫn chứng và manifest. Đường dẫn lưu trong DB phải là đường dẫn tương đối tính từ thư mục dữ liệu. **Không** bắt buộc sinh kho Word chuẩn hoá (Q3, mục 4.3.7).
- Hai process cùng một file DB: WAL + `busy_timeout` (mục 4.3.5). Không sao chép file DB trong lúc đang ghi. Sao lưu bằng SQLite Backup API/snapshot nhất quán hoặc dừng cả Search App và Importer, rồi chép **toàn bộ** gói dữ liệu.
- Có thể OCR trên máy mạnh hơn, nhưng phải xuất một gói nhập có manifest/hash rồi nhập vào kho chính; không ghi đè DB đang sử dụng.

### 4.2 Lược đồ SQLite

Không có bảng vector. Đây là lược đồ định hướng; migration triển khai phải bổ sung `NOT NULL`, `CHECK`, khóa ngoại, chỉ mục và audit phù hợp.

```sql
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;
PRAGMA foreign_keys = ON;

CREATE TABLE documents(
  id INTEGER PRIMARY KEY,
  file_path TEXT NOT NULL UNIQUE,        -- đường dẫn tương đối; UNIQUE (E5)
  sha256 TEXT NOT NULL UNIQUE,           -- nhận diện trùng/thay đổi, không chứng minh chính thức
  so_hieu TEXT,                          -- hiển thị; KHÔNG UNIQUE (hai file cùng số hiệu)
  so_hieu_search TEXT,                   -- fold mục 3.2; tra thẳng; không phải khoá unit
  loai TEXT, co_quan TEXT,
  ngay_ban_hanh TEXT, ngay_hieu_luc TEXT,
  hieu_luc TEXT CHECK(hieu_luc IN ('con','het','chua_ro')),
  source_status TEXT NOT NULL,
  extraction_method TEXT NOT NULL,        -- docx/pdf_text/ocr/mixed/fallback
  struct_score REAL,
  multi_document_suspected INTEGER NOT NULL DEFAULT 0,
  fallback_doan INTEGER NOT NULL DEFAULT 0,
  reviewed_by TEXT, reviewed_at TEXT
);

CREATE TABLE pages(
  id INTEGER PRIMARY KEY,
  doc_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  page_no INTEGER NOT NULL,
  kind TEXT NOT NULL,                     -- text_ok/text_suspect/image/mixed/table
  extraction_method TEXT NOT NULL,
  ocr_status TEXT NOT NULL,               -- khong_can/cho_ocr/ocr_xong/loi_ocr/can_duyet/da_doi_chieu
  ocr_engine TEXT, ocr_version TEXT,
  ocr_conf REAL,
  raw_text TEXT,
  normalized_text TEXT,                   -- NFC, giữ dấu
  search_accent TEXT,                     -- mục 3.2 search_accent
  search_text TEXT,                       -- fold
  reviewed_text TEXT,                     -- không UI sửa; thường NULL
  verification_status TEXT NOT NULL,
  reviewed_by TEXT, reviewed_at TEXT,
  bbox_json TEXT,
  UNIQUE(doc_id, page_no)
);

CREATE TABLE units(
  id INTEGER PRIMARY KEY,
  doc_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  parent_id INTEGER REFERENCES units(id) ON DELETE CASCADE,
  path TEXT NOT NULL,                     -- D5.K2.Đa hoặc p7.para3; KHÔNG chứa số hiệu
  level TEXT NOT NULL,                    -- chuong/muc/dieu/khoan/diem/doan/cua_so/ghi_chu (0.8)
  title TEXT,
  title_search TEXT NOT NULL DEFAULT '',  -- fold của title
  raw_text TEXT NOT NULL,                 -- chỉ chữ riêng đơn vị (B4)
  normalized_text TEXT NOT NULL,
  search_accent TEXT NOT NULL DEFAULT '',
  search_text TEXT NOT NULL,
  context_search TEXT NOT NULL DEFAULT '', -- câu dẫn cha, fold; BM25 thấp
  context_accent TEXT NOT NULL DEFAULT '', -- câu dẫn cha, search_accent
  reviewed_text TEXT,
  page_from INTEGER, page_to INTEGER,
  boundary_confidence REAL,
  extraction_method TEXT NOT NULL,
  verification_status TEXT NOT NULL,
  from_table INTEGER NOT NULL DEFAULT 0,
  fine_min INTEGER,
  fine_max INTEGER,
  fine_source_unit INTEGER REFERENCES units(id) ON DELETE SET NULL,
  reviewed_by TEXT, reviewed_at TEXT,
  UNIQUE(doc_id, path)
);

CREATE TABLE unit_labels(
  unit_id INTEGER NOT NULL REFERENCES units(id) ON DELETE CASCADE,
  label TEXT NOT NULL CHECK(label IN (
    'NGHIA_VU','CAM','THOI_HAN','DIEU_KIEN',
    'QUYEN','CHE_TAI','DINH_NGHIA'
  )),
  PRIMARY KEY (unit_id, label)
);

CREATE TABLE page_regions(
  id INTEGER PRIMARY KEY,
  page_id INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
  unit_id INTEGER REFERENCES units(id) ON DELETE SET NULL,
  x0 REAL, y0 REAL, x1 REAL, y1 REAL,
  image_path TEXT
);

CREATE VIRTUAL TABLE units_fts USING fts5(
  title_search,
  search_accent,
  search_text,
  context_search,
  context_accent,
  content='units',
  content_rowid='id',
  tokenize='unicode61 remove_diacritics 0'
);

-- Trigger INSERT/UPDATE/DELETE đồng bộ đủ 5 cột trên (mục 4.3.5).
-- Trọng số bm25() đi theo thứ tự cột trong CREATE VIRTUAL TABLE (E4):
--   bm25(units_fts, w_title, w_accent, w_fold, w_context_search, w_context_accent)
-- với w_context_search < w_fold và w_context_accent < w_accent
-- (w_context < w_chữ_riêng của cùng nhánh).
-- Tên bảng fts5vocab do mình đặt, ví dụ:
--   CREATE VIRTUAL TABLE units_vocab USING fts5vocab(units_fts, 'row');
-- Cả hai exe lúc khởi động thử tạo FTS5 + fts5vocab tạm; lỗi thì dừng và báo rõ (E4, 4.3.5).

CREATE TABLE links(
  id INTEGER PRIMARY KEY,
  sanction_unit INTEGER NOT NULL REFERENCES units(id) ON DELETE CASCADE,
  duty_unit INTEGER NOT NULL REFERENCES units(id) ON DELETE CASCADE,
  method TEXT NOT NULL,                   -- dan_chieu/goi_y/noi_bo
  confirmed INTEGER NOT NULL DEFAULT 0,
  reviewed_by TEXT, reviewed_at TEXT,
  UNIQUE(sanction_unit, duty_unit)
);

CREATE TABLE synonyms(
  id INTEGER PRIMARY KEY,
  term TEXT NOT NULL, alt TEXT NOT NULL,
  kind TEXT NOT NULL,                     -- viet_tat/dong_nghia/hanh_vi
  approved INTEGER NOT NULL DEFAULT 0,
  reviewed_by TEXT, reviewed_at TEXT,
  UNIQUE(term, alt)
);

CREATE TABLE import_jobs(
  id INTEGER PRIMARY KEY,
  status TEXT NOT NULL CHECK(status IN (
    'queued','running','done','failed','skipped_duplicate'
  )),
  phase TEXT,
  file_path TEXT,
  sha256 TEXT,
  existing_file_path TEXT,              -- bản đã có khi skipped_duplicate (E5)
  pages_done INTEGER NOT NULL DEFAULT 0,
  pages_total INTEGER,
  error TEXT,
  started_at TEXT,
  finished_at TEXT
);

CREATE TABLE query_log(
  id INTEGER PRIMARY KEY,
  query_raw TEXT NOT NULL,
  result_count INTEGER NOT NULL,
  selected_unit INTEGER REFERENCES units(id) ON DELETE SET NULL,
  selected_doc_id INTEGER REFERENCES documents(id) ON DELETE SET NULL,
  selected_path TEXT,
  created_at TEXT NOT NULL
);

-- Q5: danh sách ưu tiên / hạ ưu tiên do người dùng nhập.
-- so khớp lúc xếp hạng: phrase (chữ có dấu, ranh giới từ, F3). KHÔNG dùng phrase_fold.
CREATE TABLE subject_rules(
  id INTEGER PRIMARY KEY,
  phrase TEXT NOT NULL,
  phrase_fold TEXT NOT NULL,             -- lưu khi nhập; không dùng để so khớp Q5
  kind TEXT NOT NULL CHECK(kind IN ('uu_tien','ha_uu_tien')),
  approved INTEGER NOT NULL DEFAULT 0,
  UNIQUE(phrase, kind)
);

-- B13: gợi ý hết hiệu lực, không tự UPDATE documents.hieu_luc
CREATE TABLE effect_hints(
  id INTEGER PRIMARY KEY,
  source_doc_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  source_unit_id INTEGER REFERENCES units(id) ON DELETE SET NULL,
  target_so_hieu TEXT,
  kind TEXT NOT NULL CHECK(kind IN ('thay_the','bai_bo')),
  snippet TEXT NOT NULL,
  confirmed INTEGER NOT NULL DEFAULT 0,   -- 0 chờ; 1 đã áp dụng het; -1 từ chối
  reviewed_by TEXT, reviewed_at TEXT
);
```

Không cột `units.addr` làm UNIQUE. Địa chỉ **hiển thị** lúc render: `{documents.so_hieu hiện tại} · {path đọc được}` (ví dụ `15/2020/NĐ-CP · Điều 5 khoản 1 điểm a`), hoặc `{file_path} · trang N đoạn M` nếu không có số hiệu / không có Điều.

Trạng thái nguồn tối thiểu: `SOURCE_HASHED`, `TEXT_EXTRACTED`, `OCR_UNVERIFIED`, `TEXT_HUMAN_VERIFIED`, `MATCHED_OFFICIAL_COPY`, `SOURCE_CONFLICT`, `SOURCE_UNREADABLE`. (Bỏ dựa vào `STRUCTURE_REVIEWED` từ UI ranh giới — không có UI đó, Q4.)

### 4.3 Hợp đồng implement

Code bám đúng quy tắc dưới đây; không suy diễn thêm tầng, không tự ghép cụm đồng nghĩa, không nhúng số hiệu vào `path`.

#### 4.3.1 Lắp thẻ lúc search

Đầu vào: tập đơn vị `H` do tra thẳng (4.3.3) hoặc FTS một tầng (4.3.2) trả về, đã lọc bộ lọc người dùng.

Gom `H` thành nhóm `G` theo `(doc_id, dieu_path)` với `dieu_path` = tiền tố `D{n}` của `path`, hoặc toàn bộ `path` nếu `level` là `doan`/`cua_so`.

Với mỗi nhóm `G`:

1. Chọn đơn vị hiện chính = BM25 cao nhất trong nhóm. Đọc mọi nhãn của các unit trong nhóm (hợp). Lấy cha (`parent_id`) chỉ để hiện ngữ cảnh, không tạo thẻ thứ hai.
2. OCR: nếu ít nhất một trang trong `[min page_from, max page_to]` đã OCR và chưa `da_doi_chieu` → nhãn phụ **Trích dẫn OCR chưa xác minh**, không đổi hạng. Nếu nhóm có hit từ nhánh bỏ dấu OCR (F2) → **thêm** nhãn Q6 (cả hai nhãn).
3. Phân loại hạng 1–4 **đúng bảng mục 3.4** (cùng định nghĩa với khung A–E và fixture mục 9):
   - Có ít nhất một `links.confirmed = 1` gắn với nhóm → **hạng 1**.
   - Có nhãn `CHE_TAI` trong nhóm, **hoặc** có `links` nhưng không có `confirmed = 1` (máy gợi ý `confirmed = 0`). Gồm cả `CHE_TAI` **chưa nối** được nghĩa vụ → **hạng 2**. Không được xếp `CHE_TAI` đứng một mình xuống hạng 4.
   - Có nhãn rủi ro `NGHIA_VU` / `CAM` / `THOI_HAN` / `DIEU_KIEN`, không `CHE_TAI`, không `links` → **hạng 3**.
   - Không thuộc 1–3 → **hạng 4**.
   `links` tra theo `duty_unit` ∈ nhóm (và tổ tiên mức Điều); chiều ngược `sanction_unit` ∈ nhóm. `confirmed = 1` thắng `0`.
4. Câu mẫu: nguyên văn + địa chỉ **hiển thị** (so_hieu lúc render + path). **Hạng 2 hiện mức phạt theo đúng quy tắc 3.4** (không rõ đối tượng áp dụng thì không in số tiền). Không ô chủ thể. Liên kết máy gợi ý ghi “máy gợi ý, chưa duyệt”. `CHE_TAI` chưa nối nghĩa vụ: vẫn hiện nguyên văn chế tài, câu mẫu thiếu cụm nghĩa vụ thì bỏ cụm đó.
5. Q5 (sau hạng, trước hiệu lực, **không đổi hạng**): so khớp `subject_rules.approved = 1` theo **đúng luật F3 mục 3.6** — chữ có dấu, ranh giới từ nguyên, cụm dài nhất thắng, cụm dưới 2 tiếng phân biệt hoa thường; **không** so trên chữ bỏ dấu / `phrase_fold`. Có cụm `uu_tien` trên đơn vị hoặc Điều cha → xếp lên. Cụm `ha_uu_tien` trong cửa sổ khoảng 8 tiếng trước `"phải"` / `"có trách nhiệm"` **hoặc** tên Điều `"Trách nhiệm của " + cụm hạ ưu tiên` → xếp xuống, nhãn phụ **nghĩa vụ của cơ quan khác**.
6. Q6: nhóm có hit từ nhánh bỏ dấu toàn kho, **hoặc** từ nhánh bỏ dấu OCR (F2) → nhãn phụ **khớp khi bỏ dấu, có thể khác nghĩa**.
7. `hieu_luc = 'het'` → cờ xám, sort key cuối.

Tầng của thẻ = tầng thấp nhất (ưu tiên cao nhất) trong nhóm. Xếp mục 3.6.

#### 4.3.2 Mở rộng truy vấn, escape, từ, dừng

**Escape FTS5 (B5):** với mỗi token `t` sau khi tách từ: `'"' + t.replace('"', '""') + '"'`. Ghép AND/NEAR/phrase từ các token đã quote. Cấm `MATCH` chuỗi thô.

**Tách từ (B6):** so khớp dài nhất trên chuỗi đã chuẩn hoá (accent hoặc fold tùy nhánh) với từ vựng = `synonyms` approved ∪ tên Điều ∪ cụm 2–3 tiếng thống kê từ kho. Phần không khớp: tách theo khoảng trắng. Bỏ token rỗng.

**Cột MATCH (C3, Q6):** khi có bộ lọc cột, FTS5 **chỉ** tính các lần khớp trong cột được lọc. Không đưa cột context vào bộ lọc thì trọng số context **vô tác dụng**. Vì vậy:

- Truy vấn **có dấu:** chạy **đủ 6 tầng** trên nhánh có dấu với
  `{search_accent context_accent} : <expr>`.
  **Chỉ khi** sau cả 6 tầng số nhóm = 0 mới chạy nhánh bỏ dấu **trên toàn kho**.
- **Ngoại lệ OCR (F2):** sau (hoặc song song với) nhánh có dấu, **luôn** chạy nhánh bỏ dấu `{search_text context_search} : <expr_fold>` **chỉ trên** unit thuộc trang OCR chưa `da_doi_chieu`. Gộp hit vào `H` dù nhánh có dấu đã có nhóm. Không được lọc bỏ tập OCR vì “đã có kết quả có dấu”.
- Nhánh **bỏ dấu toàn kho:** `{search_text context_search} : <expr_fold>` — chỉ khi truy vấn có dấu ra 0 nhóm, hoặc truy vấn không dấu.
- Truy vấn **không dấu:** chỉ nhánh bỏ dấu toàn kho (không gắn nhãn Q6).
- Mọi thẻ sinh từ nhánh bỏ dấu (toàn kho hoặc F2) khi truy vấn có dấu: nhãn Q6; F2 thêm nhãn OCR.

`title_search` nằm trong bảng FTS. Nếu muốn trọng số title có tác dụng thì phải đưa `title_search` vào bộ lọc (cùng lý do C3); không bắt buộc trong expr mặc định trên.

**Tầng:** đúng bảng 3.3 (1 phrase → 2 NEAR 10 → 3 AND → 4 union alt → 5 bớt từ IDF min → 6 lõi). Điều kiện dừng (B7) áp **trong từng nhánh**; hết 6 tầng nhánh có dấu mà 0 nhóm mới sang nhánh bỏ dấu toàn kho (Q6). Không được sang bỏ dấu toàn kho chỉ vì “chưa đạt ngưỡng dừng” khi nhánh có dấu đã có nhóm. Nhánh F2 (OCR) **không** bị điều kiện “0 nhóm” chặn.

**IDF theo từ (E3):**

- `df(từ)` = số dòng `units_fts` khớp `{cột_nhánh} : "từ"` (token đã quote). Cột nhánh có dấu = `search_accent`; cột nhánh bỏ dấu = `search_text`. Đây là đếm IDF, không phải câu MATCH tìm kiếm (câu tìm luôn kèm context, C3).
- `fts5vocab` (`units_vocab`, E4) **chỉ** dùng cho từ **một tiếng**. Từ nhiều tiếng: đếm bằng MATCH `"từ"`, không lấy `fts5vocab`.
- Có thể cache `df` theo phiên bản kho (ví dụ sau mỗi lần nạp xong: số document + max `import_jobs.finished_at`).
- Bớt **cả từ**, không bớt âm tiết. Tầng 5 bỏ **một** từ có IDF thấp nhất.

Chỉ `synonyms.approved = 1`. Tầng 4 không AND gốc∪alt.

**Dừng (B7):** sau mỗi tầng, gom theo 4.3.1; dừng nếu ≥ 5 nhóm có nhãn rủi ro hoặc `CHE_TAI`, hoặc ≥ 10 nhóm. Không đạt thì tầng tiếp **cùng nhánh**. Hết tầng 6 của nhánh đang chạy: nếu là nhánh có dấu và 0 nhóm → sang nhánh bỏ dấu toàn kho; nhánh F2 OCR vẫn chạy / đã chạy trên tập OCR. Không thì phần E.

Kết quả chỉ xuất hiện từ tầng 4 trở đi: ghi đồng nghĩa `term` → `alt` trên thẻ.

#### 4.3.3 Tra số hiệu và Điều

`documents.so_hieu` nguyên văn để hiện. `so_hieu_search` = fold(so_hieu) lúc nạp và lúc sửa metadata. **Không UNIQUE.** Tra khớp được **mọi** `doc_id` cùng `so_hieu_search` (hai file cùng số hiệu: cả hai).

Nhận diện trên **chuỗi gõ gốc** bằng đúng mẫu mục 3.1: `(?i)\d+/\d{4}/[A-ZĐ0-9-]+` (đủ đuôi) hoặc thiếu đuôi `(?<!\d)\d+/\d{4}(?!/\S)` rồi bước 2 dưới. Cùng các mẫu ở 3.1 và đây. Nhờ vậy `15/2020/nd-cp` và `15/2020/NĐ-CP` ra cùng văn bản; `64/2025/QH15` bắt đủ `QH15`; dạng `TTLT-…` nằm trong `[A-ZĐ0-9-]+`.

Parse tùy chọn: `Điều\s+(\d+[a-z]?)` kèm loại (`Nghị định|NĐ|Thông tư|TT`) và số. Tra:

1. Mọi `documents` với `so_hieu_search = fold(số hiệu đầy đủ)`.
2. Thiếu đuôi (gõ đúng `số/năm`, ví dụ `15/2020`): **khớp đầu chuỗi** `so_hieu_search LIKE fold('15/2020') || '/%'` (F4). **Cấm** `%` ở **đầu** mẫu số hiệu (không `LIKE '%' || …`). Nhờ vậy `15/2020` không ra `115/2020/…`.
3. Nếu có số Điều: `units` các `doc_id` đó, `path = 'D' || số` hoặc `path LIKE 'D' || số || '.%'` (đây là `path`, không phải số hiệu).

Không dùng chuỗi `so_hieu#D…` làm khoá. Hit tập này không qua FTS nhiều tầng. Lắp thẻ 4.3.1.

#### 4.3.4 Rebuild sau nạp lại (không UI ranh giới/OCR)

`title_search` = fold(title) lúc nạp. `search_accent` / `search_text` từ **chữ riêng** đơn vị. `context_search` / `context_accent` từ câu dẫn cha; đơn vị gốc Điều: để rỗng.

Nguồn chữ hiện: `reviewed_text` nếu không NULL, không thì `raw_text`. Cột này thường NULL.

**Cùng `file_path` (UNIQUE), SHA đổi (sửa nguồn):** giữ `doc_id`. Snapshot `links` theo **cả hai đầu** `(sanction_doc_id, sanction_path, duty_doc_id, duty_path, method, confirmed)` — `(doc_id, path)`, không số hiệu (E2). Xoá unit cũ (CASCADE links; `query_log.selected_unit` SET NULL — C1). Parse lại, insert unit mới cùng quy tắc path. Gắn lại link khi **cả hai** `(doc_id, path)` còn tồn tại; `confirmed = 1` giữ. Một đầu mất → link đó mất. `ON DELETE CASCADE` chỉ dọn mồ côi, không thay snapshot.

Liên kết **giữa hai văn bản khác nhau** phải được giữ khi **chỉ một** trong hai văn bản được nạp lại: đầu kia không bị xoá nên `(doc_id, path)` còn; sau parse đầu này, gắn lại nếu path mới còn.

**Đổi `documents.so_hieu`:** không đụng `path`, không rebuild unit, **không** mất `links` đã duyệt. Test mục 9.

**`file_path` mới, trùng số hiệu, khác `sha256`:** `INSERT` document mới.

**Cùng nội dung (`sha256` trùng) nhưng khác đường dẫn (E5):** **không** `INSERT`. Ghi `import_jobs` `status = 'skipped_duplicate'`, điền `existing_file_path` = `file_path` của bản đã có. Không tạo `doc_id` thứ hai.

**`query_log` (C1):** nạp lại văn bản có unit đang được `query_log.selected_unit` tham chiếu **phải thành công**. Sau nạp: `selected_unit` có thể NULL; `selected_doc_id` và `selected_path` giữ để biết chỗ đã chọn.

Trigger FTS **năm** cột; lệch đếm thì `INSERT INTO units_fts(units_fts) VALUES('rebuild')`.

#### 4.3.5 Hai process, WAL, job, khởi động FTS

- Mở DB: `journal_mode=WAL`, `busy_timeout=5000`, `foreign_keys=ON`.
- **Khởi động cả `SoiLuat.exe` và `SoiLuatImporter.exe` (E4):** thử tạo bảng FTS5 tạm và bảng `fts5vocab` tạm, ví dụ `CREATE VIRTUAL TABLE _probe_fts USING fts5(x, tokenize='unicode61 remove_diacritics 0')` rồi `CREATE VIRTUAL TABLE _probe_vocab USING fts5vocab(_probe_fts, 'row')`; xoá sau khi xong. Lỗi → **dừng process**, báo rõ (thiếu FTS5 / fts5vocab). Đưa vào test máy sạch mục 9.
- `SoiLuat.exe`: ghi khi xác nhận/từ chối `links`, `effect_hints`, sửa metadata số hiệu/hiệu lực, sửa `subject_rules`. Không OCR, không UI ranh giới.
- `SoiLuatImporter.exe`: writer chính. Job `queued` → `running` → `done` / `failed` / `skipped_duplicate`; `file_path` + `sha256`; resume hash trùng job chưa xong. Cùng path file, hash mới → cập nhật tại chỗ (4.3.4). Hash trùng bản đã có, path khác → `skipped_duplicate` (E5).
- Nút “Nạp” spawn Importer; theo dõi `import_jobs`; không import Tesseract vào search.
- OCR: một worker trên 8 GB. Dọn tạm khi `done`/`failed`/`skipped_duplicate`.

Trigger FTS (đủ cột context_accent — C3):

```sql
CREATE TRIGGER units_ai AFTER INSERT ON units BEGIN
  INSERT INTO units_fts(rowid, title_search, search_accent, search_text, context_search, context_accent)
  VALUES (new.id, new.title_search, new.search_accent, new.search_text, new.context_search, new.context_accent);
END;
CREATE TRIGGER units_ad AFTER DELETE ON units BEGIN
  INSERT INTO units_fts(units_fts, rowid, title_search, search_accent, search_text, context_search, context_accent)
  VALUES ('delete', old.id, old.title_search, old.search_accent, old.search_text, old.context_search, old.context_accent);
END;
CREATE TRIGGER units_au AFTER UPDATE ON units BEGIN
  INSERT INTO units_fts(units_fts, rowid, title_search, search_accent, search_text, context_search, context_accent)
  VALUES ('delete', old.id, old.title_search, old.search_accent, old.search_text, old.context_search, old.context_accent);
  INSERT INTO units_fts(rowid, title_search, search_accent, search_text, context_search, context_accent)
  VALUES (new.id, new.title_search, new.search_accent, new.search_text, new.context_search, new.context_accent);
END;
```

#### 4.3.6 Nhiều nhãn

Không cột `units.label`. Importer ghi mọi nhãn khớp vào `unit_labels`. Thứ tự khi vừa nghĩa vụ vừa chế tài: 4.3.1.

Loại trừ: không gán nhãn rủi ro / `CHE_TAI` cho quốc hiệu, căn cứ, phần ký. Điều khoản thi hành / hiệu lực thi hành: vẫn index; **không** biến “phải thi hành nghị định này” thành thẻ hạng 1–3 nếu không có `links` đã duyệt — để hạng 4.

**`CHE_TAI` (F1, cùng 3.5):** chỉ dạng `"phạt … đối với hành vi"` hoặc điểm dưới khoản có câu dẫn đó; tiếng đầu đơn vị đúng `"buộc"` (ranh giới từ, không khớp `"bắt buộc"` / `"ràng buộc"`) trong khoản `"Biện pháp khắc phục hậu quả"`; **cấm** gắn vì `"bắt buộc"` / `"ràng buộc"`; Điều quy định chung (hình thức xử phạt, mức phạt tiền, thẩm quyền xử phạt, thời hiệu) không gắn `CHE_TAI`.

Phủ định: mục 3.5.

Importer quét cụm `"thay thế Nghị định số"` và `"bãi bỏ"` trong đơn vị thi hành → `effect_hints` (`thay_the` / `bai_bo`), `confirmed = 0`. Không `UPDATE hieu_luc` cho đến khi người duyệt (B13).

#### 4.3.7 Không làm trên máy văn phòng

| Cắt | Lý do | Thay bằng |
|---|---|---|
| UI sửa ranh giới | Q4, 8 tuần | Sửa nguồn hoặc cờ chia theo đoạn, nạp lại |
| UI sửa chữ OCR | Q4 | Sửa nguồn / OCR ngoài app, nạp lại |
| UI tách file nhiều văn bản | Q4 | Không có UI. 0.8 tự tách khi đủ ba điều kiện (mục 2.9); không đủ thì tách file trước khi nạp |
| Ontology đầy đủ, phát hiện mâu thuẫn liên văn bản | A4, đề bài tham khảo gốc | Chỉ `unit_labels` + `links` |
| Quan hệ thay thế / bãi bỏ tự động | Không tự đổi hiệu lực | `effect_hints` + người duyệt; lọc `hieu_luc` |
| Ô chủ thể trong câu mẫu | Không extractor | Câu mẫu không chủ thể |
| Gợi ý chính tả | Không spellfix | Tầng 6 bớt từ; phần E gợi từ điển |
| Kho Word chuẩn hoá bắt buộc | Q3 | Xuất Word = báo cáo thẻ đã chọn |
| `synonyms.kind = chu_the` | Theo ô chủ thể | Bỏ |
| Embedding, vector, ONNX, RRF, LLM, RAG, Docker | Máy văn phòng 8 GB + Office | Mục 11 (không thuộc sản phẩm) |

#### 4.3.8 Localhost, Host, CSRF

- Bind `127.0.0.1` (không `0.0.0.0`).
- Mọi request: header `Host` ∈ {`127.0.0.1:<port>`, `localhost:<port>`}; khác → 400. Không tin `X-Forwarded-Host`.
- Không bật CORS.
- Mọi POST/PUT/PATCH/DELETE (xác nhận link, effect_hints, metadata, nạp spawn, xuất, backup): CSRF. Token ngẫu nhiên **mỗi lần khởi động** process Search App, gửi cookie `SameSite=Strict` (không `Secure` bắt buộc vì HTTP local), form/header phải khớp. GET không đổi dữ liệu.

#### 4.3.9 Quy ước 0.8 (địa chỉ đơn vị, file, nạp, cổng)

**Địa chỉ đơn vị (`units.path`)** — vẫn không nhúng số hiệu:

| Trường hợp | `path` | Hiển thị (`fold.pretty_path`) |
|---|---|---|
| Điều / khoản / điểm | `D5`, `D5.K1`, `D5.K1.Đa` | Điều 5 khoản 1 điểm a |
| Số trùng trong cùng văn bản (lần 2 trở đi) | hậu tố `~n` ngay sau số: `D5~2`, `D5~2.K1`, `D1.K1~2`, `D1.K1~2.Đa~2` | Điều 5 (lần 2) khoản 1 |
| Đoạn (tầng 3, khoản mồ côi) | `p1.para{n}` | trang 1 đoạn n |
| Ghi chú (footnote, comment, text box, header/footer) | `GC{n}`, `level = ghi_chu` | ghi chú n |

`dieu_path` (khoá gom thẻ): `D5~2.K1` → `D5~2`; `GC3` → `GC3`. Regex dẫn chiếu trong `links.py` và `search.py` phải nhận `~n`. Hậu tố `~n` thay cho lỗi `UNIQUE(doc_id, path)` của 0.7 (văn bản đánh số lại Điều, PDF ghép).

**File và văn bản:**

- File ngoài thư mục dữ liệu lưu **đường dẫn tuyệt đối** (dấu `/`), không chỉ tên file (0.7: hai file trùng tên ở hai thư mục ghi đè nhau). File trong thư mục dữ liệu vẫn tương đối. Các dòng cũ không bị đổi.
- Văn bản thứ k ≥ 2 tách từ một file: `file_path = "<path>#vb{k}"`, `sha256 = "<sha>#vb{k}"`. Nạp lại cùng file dùng lại `doc_id` cũ theo thứ tự, thêm hoặc xoá `#vbk` cho khớp, giữ `links` đã duyệt.
- Dẫn chiếu “Điều n Nghị định/Thông tư số X” nối sang văn bản có số hiệu X nếu X có trong kho; không có thì **không** nối về Điều n của chính văn bản đang đọc (0.7 nối nhầm).
- `documents.loai` mới: `nghi_dinh | thong_tu | quyet_dinh | luat | cong_van | nghi_quyet | chi_thi | phap_lenh | NULL`. **Còn tồn:** ô lọc `loai` trên `index.html` mới liệt kê 3 loại đầu; văn bản các loại còn lại vẫn tìm được, chỉ chưa lọc riêng được.

**Importer (H3):**

- `python -m soiluat.importer PATH [--ocr] [--doan]`: lọc theo `SUPPORTED_SUFFIXES`, bỏ `~$*`; mỗi file một dòng trạng thái (`đủ | cần OCR | trùng | không đổi | lỗi | bỏ qua`); lỗi một file không dừng cả lượt; cuối cùng in tổng; có file lỗi thì mã thoát 1; đầu ra UTF-8.
- `python -m soiluat.importer --check-ocr`: in một dòng JSON = `ocr_status()` rồi thoát mã 0.
- **Nạp lại cùng file** (sha256 và đường dẫn không đổi) bị bỏ qua (“không đổi”) **trừ khi cờ lần này cho kết quả khác**: có `--ocr` mà file còn trang `cho_ocr` / `loi_ocr`; hoặc có `--doan` mà văn bản chưa chia theo đoạn. Trang đã `ocr_xong` thì nạp lại với `--ocr` không làm lại.
- Trang cần OCR mà không có `--ocr`: nạp phần chữ có được, job `done` kèm cảnh báo “N trang cần OCR, nạp lại với --ocr”. `OcrUnavailable` → job `failed`.

**Search App:**

- Cổng: `--port` hoặc `SOILUAT_PORT`, mặc định 8000. Cổng bận (kết nối được tới `127.0.0.1:<cổng>` **hoặc** không bind được; app khác nghe `[::]:8000` vẫn trả lời 127.0.0.1) → thử 8001…8020, in URL thật, mở trình duyệt (tắt bằng `SOILUAT_NO_BROWSER=1`). Link đã lưu có thể sai cổng; Host guard nhận mọi cổng.
- Nút nạp trên giao diện có ô OCR / chia đoạn, kiểm tra đường dẫn tồn tại, gọi Importer qua `importer_cmd()` (mã nguồn: `python -m soiluat.importer`; đóng gói: `SoiLuatImporter.exe` cạnh exe hoặc `..\SoiLuatImporter\`), ghi `importer.log`. Trạng thái OCR ở `/jobs` lấy qua `importer --check-ocr` (subprocess, timeout 10 s) — Search App **không** import OCR.
- `/review/synonyms`: duyệt / bỏ duyệt / xoá / thêm cặp (Q7), có CSRF.
- Cache tên Điều cho tách từ: ở mức module, khoá (file DB, nhánh), phiên bản `MAX(units.id)` + `COUNT(units)` → nạp thêm là cache tự làm mới. Từ điển đọc mới mỗi lần (bảng nhỏ), nên duyệt từ điển có hiệu lực ngay.
- Tầng 6 (lõi): chọn **2 từ hiếm nhất** (IDF) còn có trong kho, không lấy 2 từ đầu.
- `db.init_schema`: nạp `synonyms_seed.csv` (Q7); bảng `app_meta(key, value)`; index `idx_units_parent`.

---

## 5. Công nghệ

Giấy phép cần kiểm tra lại trước khi dùng trong cơ quan.

| Việc | Chọn | Ghi chú |
|---|---|---|
| Ngôn ngữ | Python 3.11+ | |
| Đọc DOCX | python-docx | Tự mô phỏng numbering.xml; không tin paragraph.text đã có số. Tùy chọn Word COM `ListString` (pywin32) nếu có Word. Fixture E6: ≥ 3 file Word thật (mục 9) |
| Đọc PDF có chữ | pdfplumber | Có toạ độ chữ, số trang. Chỉ Importer |
| Vẽ trang PDF thành ảnh | pypdfium2 | OCR và xem trang gốc. Chỉ Importer |
| OCR | Tesseract 5 + `vie`; tiền xử lý bằng Pillow (xám, autocontrast, khử nghiêng, OSD có điều kiện — mục 2.9) | Chỉ Importer; một worker. 0.8 không dùng OpenCV |
| Đổi `.doc` / `.rtf` | Word COM (pywin32, tuỳ chọn) → LibreOffice `soffice` | Chỉ Importer; extra `word` |
| Đọc `.xlsx` | `zipfile` + XML | Không thêm dependency |
| CSDL + tìm kiếm | SQLite FTS5 `unicode61 remove_diacritics 0`; MATCH có dấu `{search_accent context_accent}`, bỏ dấu `{search_text context_search}` | Search App; khởi động thử FTS5 + `fts5vocab` |
| Embedding / vector / ONNX / NumPy semantic | **Không cài** | Máy văn phòng; mục 11 |
| Giao diện | FastAPI + HTMX | Không Node; Host + CSRF |
| LLM / llama.cpp | **Không cài** | Máy văn phòng; mục 11 |
| Xuất Word | python-docx | Báo cáo từ thẻ đã chọn |
| Đóng gói | PyInstaller `onedir`: `SoiLuat`, `SoiLuatImporter` | Tesseract/`vie` chỉ Importer |

---

## 6. Máy mục tiêu và ngân sách RAM

| Hạng mục | Giả định |
|---|---|
| Hệ điều hành | Windows 10/11 |
| CPU | 4–8 nhân, không GPU |
| RAM máy | **8 GB** (ràng buộc cứng); Word, Excel và trình duyệt có thể đang mở |
| Ổ đĩa | Đo theo corpus; không cam kết cố định 5–10 GB |

**Ngân sách RAM Soi Luật (không embedding, không LLM):**

| Trạng thái | RAM Soi Luật dự kiến |
|---|---|
| Tra cứu FTS5 (backend) | khoảng 250–600 MB |
| Backend + tab trình duyệt | khoảng 400 MB – 1 GB |
| OCR / Importer | thêm khoảng vài trăm MB đến hơn 1 GB, **chỉ khi nạp tài liệu** |
| Embedding | không cài |
| LLM | không cài |

**Số đo thực tế 0.8** (21/10/2026; Ryzen 5 5600GT, 6 nhân, 15,4 GB nhưng chỉ ~1,3 GB trống lúc đo, **không phải** máy 8 GB văn phòng; dữ liệu sinh tự động, `bench/BAO-CAO-DEMO.md`):

| Hạng mục | Đo được |
|---|---|
| Search App RAM lúc rảnh / đỉnh | 59 MB / 64 MB (kho 310 văn bản) |
| Search App CPU lúc rảnh | 0,2–0,5 % |
| Tra cứu từ khoá, kho 310 văn bản (p50 / p95) | 49 / 76 ms (giới hạn 2 luồng: 55 / 82 ms) |
| Tra cứu từ khoá, kho 1.762 văn bản / 133 nghìn đơn vị / DB 162 MB (trong process) | 88 / 125 ms (bản 0.7: 930 / 1.173 ms) |
| Tra “Điều n + số hiệu”, kho 1.762 | p95 ~0,8 s (**còn tồn**) |
| Importer RAM đỉnh | DOCX 163 MB, PDF chữ 74 MB, PDF scan + OCR 162 MB, bộ file bẩn 259 MB |
| Nạp | DOCX ~0,08 s/file, PDF chữ ~0,46 s/file (~0,11 s/trang), OCR ~1,2–1,4 s/trang |
| Xuất Word 10 thẻ / sao lưu SQLite 31 MB | 0,04 s / 0,16 s |

Chưa đo trên máy 8 GB thật khi Word, Excel đang mở; mục tuần 7 trong checklist vẫn `[ ]`.

Tuần 1 đo trên máy thật: RAM Importer (OCR một worker) khi Word, Excel và trình duyệt đang mở. RAM Search App đo stub FastAPI+SQLite hoặc đo lại tuần 4 khi `SoiLuat.exe` đã có. Nếu phần phát sinh của Search App + tab trình duyệt vượt 1 GB, backend vượt 600 MB hoặc máy duy trì trên khoảng 85–90% RAM, phải thu hẹp trước khi đóng gói. CPU của Search App lúc rảnh phải gần 0%; OCR chỉ chạy một worker trên máy 8 GB.

Dung lượng: file gốc + DB/chỉ mục + Tesseract/tessdata/runtime + ảnh/cache/tạm + backup + 30–50% dự phòng. Không cộng kho Word chuẩn hoá. Importer dọn tạm sau hoàn tất hoặc thất bại.

---

## 7. Vì sao không dùng nền tảng RAG/LLM có sẵn

Máy đích là văn phòng 8 GB đang mở Office. Các bộ dưới đây **không phải lựa chọn** cho Soi Luật; ghi ở đây để khỏi quay lại cân nhắc.

| Nền tảng | Điểm chính | Vì sao không dùng |
|---|---|---|
| **WeKnora** (Tencent, MIT) | Tìm kiếm BM25, vector, GraphRAG | Chạy Docker Compose, riêng phần bắt buộc đã gồm giao diện, app, PostgreSQL (ParadeDB), Redis, docreader. Cần LLM để trả lời. Không chia theo Điều/Khoản. [6] |
| **RAGFlow** (Apache-2.0) | Có phương pháp chia "Laws" | Yêu cầu CPU ≥ 4 nhân, RAM ≥ 16 GB, ổ đĩa ≥ 50 GB. Có báo lỗi chia "Laws" gộp đoạn từ nhiều phần khác nhau. [7] |
| **AnythingLLM Desktop** (MIT) | Cài như phần mềm thường, chạy CPU | Chatbot cần LLM và RAG; không chia theo Điều/Khoản; không phù hợp máy 8 GB đang mở Office [8] |

**Nên học từ WeKnora (không kéo dependency):**

- Chia đoạn cha–con: tìm trên Khoản/Điểm, hiện ngữ cảnh Điều qua `context_search` / `context_accent` (nằm trong MATCH, C3), không copy chữ con vào cha.
- Đặt BM25 ngay trong CSDL.
- Tách khâu đọc tài liệu thành bước riêng (Search App / Importer).

Không dùng AnythingLLM làm bước bắt buộc tuần 1. Thu từ khoá: cổng 5 từ tuần 0, rồi 30–50 truy vấn.

---

## 8. Lộ trình 8 tuần (1 người)

| Tuần | Việc | Xong khi |
|---|---|---|
| **0** | (1) Cập nhật `soi-luat-checklist.md` theo bản 0.8. (2) Người dùng viết **5 từ khoá thật** + đáp án: hạng thẻ 1–4, Điều/Khoản (và file nếu trùng số hiệu), có/không cần mức phạt trên thẻ. (3) Người dùng cung cấp hai danh sách Q5 (ưu tiên / hạ ưu tiên), tên đầy đủ với cụm một tiếng (F3). Đối chiếu khung 3.4/4.3.1 | Checklist 0.8 có hiệu lực. Cả 5 từ khoá biểu diễn được. Hai danh sách Q5 đã nhập (`subject_rules`). Không được thì **sửa khung, chưa code search** |
| 1 | Gom mẫu. Script 2.6 (kể cả Q2: số/tỷ lệ văn bản có “phạt tiền từ”). Đo RAM Importer. Thu thêm 30–50 truy vấn | CSV + hai số Q2; biên bản “kho không có xử phạt thì sống bằng thẻ loại 3” nếu đúng vậy; bộ truy vấn |
| 2–3 | Importer: DOCX (numbering.xml ± COM; E6 gồm 3 file Word thật), PDF, OCR 1 worker, năm cột FTS + `context_accent`, parser 3 tầng, chữ riêng + context, `path`, `unit_labels` (**F1** `CHE_TAI`), `fine_source_unit`, `effect_hints`, `import_jobs` (+ `skipped_duplicate`), `file_path` UNIQUE, `query_log` SET NULL, snapshot liên kết `(doc_id, path)` hai đầu, `subject_rules`. **Không** làm ba UI Q4 | Không mất file; nạp lại cùng path giữ links kể cả liên kết hai văn bản khi chỉ nạp một; trùng sha256 path khác → skipped_duplicate; query_log không chặn nạp lại; `"thông tin bắt buộc"` không `CHE_TAI` |
| 4 | Search App: FTS Q6 (có dấu đủ 6 tầng trước; bỏ dấu toàn kho chỉ khi 0 nhóm; **F2** luôn thêm nhánh bỏ dấu trên unit OCR), MATCH kèm context (C3), escape, NEAR, Host/CSRF, tra số hiệu C2 + **F4** `LIKE '15/2020/%'`, lắp thẻ 4.3.1, xếp Q5 theo **F3**, xem bản gốc (chỉ đọc). Khởi động probe FTS5/`fts5vocab`. Không Tesseract | Kết quả cuối `thuế` không chứa đoạn chỉ-`thuê` trên non-OCR trừ khi 0 nhóm có dấu; OCR sai dấu vẫn ra (F2, hai nhãn); `15/2020` không ra `115/2020`; p95 ≤ 1 giây trên baseline |
| 5 | Từ điển, tách từ, IDF theo từ (E3), dừng theo nhóm, query log (selected_doc_id/path). Không chính tả | Recall@10 đúng công thức B11; tầng 4 union đúng; `df` đúng cột nhánh |
| 6 | Nhãn F1, chế tài theo điểm, dẫn chiếu nội bộ, khung A–E, câu mẫu, `/review` links + `effect_hints` | Không gọi hạng 2 là “đã xác nhận pháp lý”; `CHE_TAI` đứng một mình = hạng 2; F1 fixture 100%; không lấy phạt từ bảng; hết hiệu lực xám + cuối |
| 7 | Xuất Word từ thẻ chọn, lọc, cảnh báo Q2, backup | Báo cáo có nguồn; restore được; cổng RAM mục 9 |
| 8 | Thử máy 8 GB + Office, `onedir` hai exe, máy sạch (kể probe FTS5/`fts5vocab`), hướng dẫn một trang | Chạy được; Host chỉ localhost; không Python/Tesseract trên Search App; thiếu FTS thì dừng rõ |

---

## 9. Kiểm thử

**Recall@10 trên thẻ (B11):**

```
Recall@10 = (1/|Q'|) · Σ_{q ∈ Q'} |R_q ∩ Top10_q| / |R_q|
```

- `R_q` = tập nhóm `(doc_id, Điều)` (hoặc `(doc_id, path)` tầng 3) **đúng** do người am hiểu gán cho truy vấn `q`.
- `Q'` = các `q` có `R_q` khác rỗng. Loại khỏi mẫu số mọi truy vấn `R_q = ∅`.
- `Top10_q` = 10 nhóm đầu sau xếp hạng 3.6 (thẻ, không phải từng unit).
- Đo **riêng** tỷ lệ phần E đúng trên các truy vấn cố ý không có đáp án trong kho (kỳ vọng E, không tính vào Recall@10).

Ngưỡng Recall@10 **chốt sau khi đo mốc**, không bịa trước.

| Hạng mục | Cách đo | Ngưỡng |
|---|---|---|
| Cổng tuần 0 | 5 từ khoá người dùng: khung 3.4 biểu diễn đủ loại + có/không mức phạt như đáp án | 5/5 trước khi code search |
| Tách cấu trúc | ≥ 20 văn bản đại diện, theo loại file và S | Precision/recall ≥ 98% nhóm confidence cao; file kém → tầng 3, không mất |
| C_liên_tục / S | Fixture: 0 Điều → C_lt=0; 1 Điều số 5 → C_lt=1; 1,2,4 → một cặp bất thường; S ∈ [0,1] | 100% fixture |
| Hiệu chỉnh S | S = ưu tiên sửa nguồn, không phải xác minh | Không tự đánh dấu đã xác minh |
| OCR | CER trên ≥ 20 trang; số tiền/ngày/số hiệu | Chốt sau baseline |
| Tìm kiếm | Recall@10 (công thức trên) trên ≥ 50 từ khoá có `R_q` ≠ ∅ | Chốt sau mốc |
| Phần E | Truy vấn không có đáp án trong kho | Hiện E, không bịa thẻ |
| Fold đ/d | `dieu kien` → đoạn có `Điều kiện` trên nhánh không dấu | 100% mẫu fold |
| Có dấu vs bỏ dấu (Q6) | Gõ `thuế`: kết quả **cuối cùng** trên non-OCR không chứa đoạn **chỉ** có `thuê`, trừ khi nhánh có dấu ra 0 nhóm — khi đó mọi thẻ từ nhánh bỏ dấu toàn kho mang nhãn Q6 | 100% fixture thuế/thuê (và nên có phạt/phát) |
| OCR sai dấu (F2) | Cùng câu ở DOCX (đúng dấu) và PDF scan (sai dấu); gõ **có dấu** ra **cả hai**; thẻ scan mang nhãn OCR **và** nhãn Q6; không bị loại vì nhánh có dấu đã có nhóm DOCX | 100% fixture |
| Tra số hiệu (C2) | `15/2020/nd-cp` và `15/2020/NĐ-CP` → cùng văn bản; `64/2025/QH15` bắt đủ `QH15`; có ít nhất một ký hiệu dạng `TTLT-…` | 100% |
| Số hiệu thiếu đuôi (F4) | Gõ `15/2020` khớp `15/2020/…` bằng `LIKE '15/2020/%'`; **không** ra `115/2020/…` | 100% |
| Path / so_hieu | Đổi `so_hieu` trên document đã có `links.confirmed=1` | Link còn, confirmed=1 |
| Hai file cùng số hiệu | Nạp cả hai | Hai `doc_id`, tìm theo số hiệu ra cả hai |
| Escape FTS | Query chứa `" * - : ( )` và token AND, OR, NOT, NEAR | Không 500; không thành toán tử; vẫn quote |
| Lắp thẻ 4.3.1 (D1) | Fixture bốn hạng cùng định nghĩa 3.4 / khung A–E: (1) `confirmed=1`; (2) `confirmed=0` **hoặc** `CHE_TAI` chưa nối nghĩa vụ — tên thẻ “Rủi ro có chế tài (chưa có liên kết đã duyệt)”, hiện mức phạt theo 3.4; (3) nhãn rủi ro không `CHE_TAI` không `links`; (4) định nghĩa, **không** gồm `CHE_TAI` đứng một mình | 100%; không ghi hạng 2 như xác nhận pháp lý; `CHE_TAI` một mình ≠ hạng 4 |
| Context trong BM25 (C3) | Điểm không chứa `"phạt tiền"` nhưng khoản cha có câu dẫn `"phạt tiền từ…"` vẫn ra khi gõ `"phạt tiền"`; xếp **dưới** đơn vị có chữ đó trong phần chữ riêng | 100% fixture |
| THOI_HAN / DIEU_KIEN | Fixture “trước ngày”, “phải đáp ứng” → nhãn đúng, hạng 3 nếu không link không `CHE_TAI` | 100% fixture |
| Phủ định | “không bắt buộc báo cáo” không gán NGHIA_VU | 100% fixture |
| Nhãn 200 đơn vị | Chọn ngẫu nhiên 200 unit, người gán nhãn vàng, precision/recall từng nhãn | Ngưỡng chốt sau mốc |
| Q5 đối tượng (D2) | Trên mẫu 200 đơn vị: đo tỷ lệ thẻ hạng 3 là nghĩa vụ của đối tượng quan tâm (cụm `uu_tien`). Nhãn hạ ưu tiên không đổi hạng | Ngưỡng chốt sau khi đo mốc |
| Q5 so khớp (F3) | Bốn fixture: (1) chữ có dấu, ranh giới từ — không khớp mảnh trong từ khác, không dùng fold; (2) `"Ngân hàng Nhà nước"` thắng `"ngân hàng"` khi chồng; (3) cụm dưới 2 tiếng phân biệt hoa thường (`"Bộ"` ≠ `"bộ"`); (4) tên Điều `"Trách nhiệm của " + cụm hạ ưu tiên` → xếp xuống + nhãn phụ | 100% bốn fixture |
| CHE_TAI (F1) | `"thông tin bắt buộc"` → không `CHE_TAI`; Điều `"Thẩm quyền xử phạt"` → không `CHE_TAI`; điểm dưới `"Phạt tiền từ … đối với các hành vi sau"` → `CHE_TAI`; `"ràng buộc"` / `"bắt buộc"` không gắn | 100% fixture |
| Mở rộng truy vấn | Không synonyms → tầng 4 ≡ tầng 3; có cặp → union; không AND gốc+alt | 100% fixture |
| Dừng theo nhóm | ≥ 5 nhóm nhãn hoặc ≥ 10 nhóm thì không nới tầng **trong cùng nhánh** | 100% fixture |
| Chế tài điểm | Khoản dẫn phạt + điểm a) b); fine trên điểm; `fine_source_unit` = khoản | 100% fixture |
| “gấp lần” / “%” | fine NULL; nguyên văn còn | 100% |
| Cá nhân/tổ chức không rõ | Câu mẫu không in số; có ghi chú kiểm tra mức phạt — kể cả thẻ hạng 2 | 100% |
| Rebuild nạp lại | Sửa file nguồn cùng path, nạp; FTS ra chữ mới; link `(doc_id, path)` còn thì confirmed giữ | 100% |
| Snapshot hai văn bản (E2) | Link giữa doc A và doc B; chỉ nạp lại A | Link còn nếu path A còn và B không đổi |
| query_log FK (C1) | `query_log.selected_unit` trỏ unit của văn bản; nạp lại văn bản đó | Nạp thành công; `selected_unit` NULL; `selected_doc_id`/`selected_path` còn |
| Trùng sha256 path khác (E5) | Nạp file nội dung trùng, đường dẫn khác | Job `skipped_duplicate`; `existing_file_path` = bản đã có; không `doc_id` mới |
| Câu mẫu | Không chủ thể; không số bịa | 100% |
| Host / CSRF | Host lạ → 400; POST không token → từ chối; không CORS | 100% |
| Word numbering | DOCX List Number/style không có số trong XML text → extract ra `1.` / `a)` | 100% fixture python-docx |
| Word numbering thật (E6) | ≥ 3 DOCX soạn bằng Microsoft Word: numbering trên đoạn; numbering trên style; danh sách nhiều cấp | 100% ba file |
| Tốc độ | p95 A–E | ≤ 1 giây; mở nguồn ≤ 2 giây |
| RAM / CPU / máy sạch | Như bản 0.4, **cộng** probe khởi động FTS5 + `fts5vocab` trên cả hai exe (E4) | Như mục 6; thiếu FTS → dừng, không chạy câm |
| Nguồn / OCR | Hash, phương thức, OCR | 100% truy vết |
| Bảng chưa duyệt | Không thẻ chế tài tự động từ bảng | 100% |
| Hết hiệu lực | `hieu_luc=het` xám + cuối; Importer chỉ ghi `effect_hints` | 100% |

---

## 10. Cần chốt trước khi bắt đầu

Đã chốt: **chỉ máy văn phòng Windows 8 GB**; FTS5 + từ điển + parser + quy tắc + người duyệt links/hiệu lực; **không** embedding/LLM/RAG; Q1–Q9; F1–F4; không UI ranh giới/OCR/tách file. Không song song một “bản nặng”.

Còn lại (vận hành). **Tuần 0** phải xong mục 1, 2 và 6. Tuần 1 phải có số cho mục 3:

1. Năm từ khoá thật + đáp án hạng thẻ / Điều / có cần phạt không (cổng khung).
2. Hai danh sách Q5 (ưu tiên / hạ ưu tiên) — việc người dùng cung cấp ở tuần 0; nạp vào `subject_rules`.
3. **Q2:** kho có bao nhiêu văn bản chứa “phạt tiền từ”, tỷ lệ bao nhiêu (CSV 2.6). Nếu 0: xác nhận chấp nhận sống bằng thẻ loại 3.
4. Khoảng bao nhiêu văn bản, tỷ lệ Word / PDF chữ / PDF scan.
5. Máy văn phòng thật: CPU, RAM trống khi Office đã mở; chỗ đặt data.
6. Cập nhật `soi-luat-checklist.md` theo 0.8 rồi mới tick việc.
7. Ai duyệt liên kết chế tài và `effect_hints`; bao nhiêu giờ/tuần. (Không phân công “duyệt ranh giới trên UI” — không có UI đó.)

---

## 11. Không thuộc sản phẩm (máy văn phòng)

Không cài, không đo và không để dependency ẩn trong gói: embedding, vector index, ONNX Runtime, NumPy vector, RRF, reranker, LLM, llama.cpp, RAG, Qdrant, PostgreSQL hoặc Docker.

**Không làm** (không phải “để lần sau”): ontology pháp lý đầy đủ; phát hiện mâu thuẫn giữa các văn bản. “Ontology” trong Soi Luật = tập nhãn `unit_labels` + quan hệ `links` (+ `effect_hints` chờ duyệt).

**Ba giao diện Q4 — không có trên máy văn phòng:**

- Sửa ranh giới Điều/Khoản trên màn hình (kéo/thả, thêm/bỏ).
- Sửa chữ OCR từng trang (`reviewed_text`) trong app.
- Tách một file thành nhiều văn bản trên UI.

Cũng không thuộc sản phẩm: gợi ý chính tả, kho Word chuẩn hoá bắt buộc, ô chủ thể trong câu mẫu, tự `UPDATE hieu_luc` từ “thay thế / bãi bỏ”.

Nếu Recall@10 chưa đạt: corpus, OCR, parser, từ điển, tách từ, query expansion — **không** chuyển sang embedding/LLM.

---

## 12. Kế hoạch đồng bộ code

Mục 12.6 là sprint **0.8** (21/10/2026), đang có hiệu lực. Mục 12.1–12.5 giữ lại làm lịch sử của sprint 0.7 (28/09/2026).

### 12.6 Sprint 0.8: sửa lỗ hổng sau demo (21/10/2026)

**Nguồn:** `bench/BAO-CAO-DEMO.md` (demo 300 văn bản + 18 file lệch mẫu dựng bằng Word thật, 268 truy vấn có đáp án; đo trước và sau trên cùng máy). Chia 4 phần, mỗi phần một nhóm file riêng (`bench/KE-HOACH-SUA.md`).

| Mã | Lỗ hổng 0.7 | Cách sửa 0.8 | Chỗ |
|---|---|---|---|
| L1 | Bỏ bảng, footnote, comment, text box, header/footer DOCX | Mục 2.9 | `extract.py` |
| L2 | Từ chối `.doc`, ảnh, `.xlsx` | Q8, `convert.py` | `extract.py`, `convert.py` |
| L3 | Chữ ô bảng PDF trộn lẫn | Bộ dò bảng không kẻ khung | `extract.py` |
| L4 | Thiếu Tesseract → báo thành công, 0 chữ | `ocr_status()`, `OcrUnavailable`, `--check-ocr` | `ocr.py`, `importer.py` |
| L5 | OCR sai dấu, không tiền xử lý | Render theo dpi gốc, khử nghiêng, OSD có điều kiện | `ocr.py` |
| L6 | Chỉ OCR trang < 40 ký tự | Trang `mixed` ảnh phủ nhiều, lớp chữ rác | `extract.py`, `ocr.py` |
| L7 | Trùng số Điều/khoản → crash cả file | Hậu tố `~n` (4.3.9) | `parse.py` |
| L8 | Không nhận `Điều thứ hai`, `1)`, `a.`… | Mục 2.9 | `parse.py` |
| L9 | Không tách hai văn bản một file | `#vb{k}` (4.3.9) | `parse.py`, `ingest.py` |
| L10 | Trích dẫn luôn “Trang 1–N” | Số trang thật từng đơn vị | `parse.py`, `ingest.py`, `rebuild.py` |
| L11 | Không trích ngày; `loai` = đuôi file | `ngay_ban_hanh`, `ngay_hieu_luc`, `loai` theo nội dung | `sohieu.py`, `ingest.py` |
| L12 | File ngoài thư mục dữ liệu ghi đè nhau | Đường dẫn tuyệt đối (4.3.9) | `ingest.py` |
| L13 | CLI dừng ở file lỗi đầu tiên | Tóm tắt từng file, mã thoát | `importer.py` |
| L14 | Nút nạp không OCR; exe gọi sai lệnh | `importer_cmd()`, ô OCR | `app.py` |
| L15 | Cổng 8000 cố định | Tự chọn cổng (4.3.9) | `app.py` |
| L16 | Xếp hạng trước tầng khớp (lệch 3.6) | Khoá sắp xếp mục 3.6 | `cards.py`, `search.py` |
| L17 | Hỏi “mức phạt” ra 0% | Q9 | `query.py`, `cards.py` |
| L18 | Từ điển rỗng, không UI | Q7, `/review/synonyms` | `db.py`, `app.py` |
| L19 | Câu hỏi tự nhiên loãng truy vấn | Mục 3.1 | `query.py`, `search.py` |
| L20 | Độ trễ tăng theo kho | Cache tên Điều, bỏ N+1 | `search.py`, `db.py` |
| L21 | Dẫn chiếu sang văn bản khác nối nhầm | Mục 4.3.9 | `links.py` |
| — | Nạp lại cùng file với `--ocr` / `--doan` bị bỏ qua | Mục 4.3.9 | `ingest.py` |

**Kết quả đo** (cùng máy, cùng bộ dữ liệu sinh tự động; trước → sau): file lệch mẫu nạp được 12/18 → 18/18; nội dung cần tìm trong 18 file đó 6/22 → 22/22; tra cứu kho 310 văn bản p95 343 → 76 ms; kho 1.762 văn bản p95 1.173 → 125 ms; có đáp án trong top 10: câu hỏi 70% → 100%, viết tắt 56% → 100%, hỏi mức phạt 0% → 100%, diễn đạt khác 40% → 70%. `python -m pytest`: **179 passed** (0.7: 90).

**Bổ sung cùng ngày (21/10/2026, sau khi rà lỗ hổng còn tồn):** ngoặc kép cong `“ ”` trong parser; ô lọc `loai` đủ 8 loại; tra “Điều n” giới hạn 100 thẻ (`DIEU_CAP`), kho 1.800 văn bản p95 143 ms; hỏi “thẩm quyền xử phạt” không bị coi là hỏi mức phạt; comment Word và footnote PDF gắn vào Điều cha; `_Numbering` viết lại (La Mã, `start`, `isLgl`, `%1.%2`, gạch đầu dòng) và đối chiếu `ListString` của Word thật (`bench/word_numbering.py`, 6/6 khớp); xem ảnh trang gốc `/page/{doc}/{n}`; build exe thật và chạy thử (sửa lỗi Search App chết khi stdout không UTF-8). `python -m pytest`: **188 passed**. Số liệu RAM kho 1.800 văn bản: Search exe 62 → 69 MB.

**Còn tồn sau 0.8** (không làm trong sprint; vào checklist):

- Chạy trên **văn bản thật** của cơ quan: mọi số liệu trên là dữ liệu sinh tự động.
- OCR vẫn sai dấu ~3–5% số từ (thẻ vẫn mang nhãn “OCR chưa xác minh”).
- Bản exe đã build và chạy thử trên máy dựng, **chưa** thử trên máy Windows sạch / máy 8 GB có Office; chưa tô vùng chữ (bbox) trên ảnh trang.
- 44 cặp từ điển `approved = 0` chờ người duyệt; “diễn đạt khác” chỉ lên ~70–80% sau khi duyệt.
- Cổng tuần 0 (5 từ khoá thật + hai danh sách Q5) vẫn chưa có.

---

### 12.1–12.5 Sprint 0.7 (28/09/2026, lịch sử)

Phần này là **việc làm còn lại** để code khớp hợp đồng 4.2 / 4.3 / mục 9. Không mở phạm vi (không embedding/LLM). Không bịa 5 từ khoá thật, RAM máy văn phòng, hay bộ nạp máy sạch.

**Tiêu chí xong sprint này:** `python -m pytest` xanh (**90 passed**, 29/09/2026); checklist 0.7 tick đúng những mục đã kiểm được; mục vận hành (tuần 0, RAM, máy sạch, COM/E6, Recall@10) vẫn `[ ]`. Mục 12.3 đã làm xong.

### 12.1 Nguyên tắc

1. Bám Q1–Q6, F1–F4, schema 4.2, khung thẻ 4.3.1, cascade 4.3.2. Không embedding / vector / ONNX / RRF / LLM / RAG / Docker.
2. Q4: không trả UI sửa ranh giới, sửa OCR, tách nhiều văn bản. Giữ GET xem trang OCR, POST hiệu lực / số hiệu, duyệt `links` và `effect_hints`, nhập `subject_rules`.
3. Mỗi lệch hợp đồng → một thay đổi nhỏ + test. Không refactor quanh.
4. Vận hành (5 từ khoá, hai danh sách Q5 thật, đo RAM, pack máy sạch) **không** làm trong sprint code này.

### 12.2 Việc code — đã có trong `src/soiluat/` (kiểm lại bằng test)

| Hạng | Việc 0.7 | Chỗ |
|---|---|---|
| Parser | S &lt; 0,60 → tầng 3; `--doan` / `force_doan` | `parse.py`, `ingest.py`, `importer.py` |
| Q2 | Cột `co_cum_phat_tien_tu` + dòng `_TONG` | `health.py` |
| Nhãn | triệu; gấp lần / % → fine NULL; F1 `CHE_TAI` | `labels.py` |
| Nối | `Điều này` / `khoản này` → `noi_bo`; `fine_source_unit` | `links.py`, ingest |
| Search | Q6 + F2; F4 `LIKE` không `%` đầu; `bm25` 1,1,1,0.2,0.2; `units_vocab`; escape FTS | `search.py`, `db.py` |
| Thẻ | 4 hạng D1; Q5 F3 ranh giới từ; xếp sau hạng trước hiệu lực | `cards.py` |
| App | Host + CSRF; `/review/hints`; `/review/subjects`; `q2_note`; chọn nguồn → `query_log` | `app.py` |
| Schema | Năm cột FTS + trigger `context_accent`; `path` không số hiệu | `schema.sql` |

### 12.3 Việc code — làm trong sprint này

| # | Lệch | Việc | Kiểm |
|---|---|---|---|
| 1 | `review_docs` mất decorator | Gắn lại `GET /review/docs`; form số hiệu + `so_hieu_search` | `test_review_docs_hieu_luc` → 200 |
| 2 | Tra số hiệu chỉ lấy `level=dieu` (chữ Điều = tiêu đề) | `lookup_so_hieu` không có “Điều n” trả `dieu`/`khoan`/`diem` | `test_two_files_same_so_hieu` thấy `unique_file_*` |
| 3 | Q5 “Điều cha chứa cụm” chỉ đọc tiêu đề Điều | `apply_q5` gom chữ mọi đơn vị cùng `path` Điều; test ưu tiên trên truy vấn trúng Điều 5 | `test_f3_uu_tien_and_ha_uu` |
| 4 | F3 chưa đủ 4 fixture | Thêm: không khớp mảnh trong token khác; cụm dài thắng; tên Điều hạ ưu tiên; “Bộ” ≠ “bộ” | `test_v07.py` |
| 5 | Dừng cascade / chọn thẻ / CORS | Test `enough_groups` → `tier ≤ 3`; GET `/unit` ghi `selected_*`; không header CORS | pytest |
| 6 | Checklist / README lệch trạng thái | Tick mục đã kiểm; bảng “lệch còn lại” chỉ vận hành + COM/E6 + ảnh trang | `soi-luat-checklist.md` |

### 12.4 Không làm trong sprint (vận hành / máy / phụ thuộc Word)

- Năm từ khoá thật + đáp án; hai danh sách Q5 người dùng (cổng tuần 0).
- Word COM `ListString`; E6 ba DOCX soạn bằng Microsoft Word.
- Ảnh trang PDF gốc + bbox (`page_regions.image_path` chưa ghi lúc nạp).
- Đo RAM ≤ 600 MB, p95 ≤ 1 s, pack máy Windows sạch, Recall@10 trên ≥ 50 truy vấn `R_q ≠ ∅`.
- Cache `df` theo “phiên bản kho” ngoài `fts5vocab` theo phiên SQLite hiện tại.

### 12.5 Thứ tự thực hiện

1. Sửa `#1–#3` (lỗi đang đỏ) → `pytest` tập fail cũ.
2. Bổ sung fixture `#4–#5` → `python -m pytest` toàn bộ xanh.
3. Cập nhật checklist 0.7 cho khớp code; không tick vận hành.

---

## Nguồn

1. [Toàn văn Luật số 64/2025/QH15 Ban hành văn bản quy phạm pháp luật (Chinhphu.vn)](https://xaydungchinhsach.chinhphu.vn/toan-van-luat-so-64-2025-qh15-ban-hanh-van-ban-quy-pham-phap-luat-119250311155839688.htm)
2. [Chi tiết thể thức và kỹ thuật trình bày văn bản QPPL theo Nghị định 78/2025 (Thư viện Pháp luật)](https://thuvienphapluat.vn/chinh-sach-phap-luat-moi/vn/ho-tro-phap-luat/tu-van-phap-luat/82789/chi-tiet-the-thuc-va-ky-thuat-trinh-bay-van-ban-quy-pham-phap-luat-theo-nghi-dinh-78-2025) · [Nghị định 78/2025/NĐ-CP (Chinhphu.vn)](https://xaydungchinhsach.chinhphu.vn/nghi-dinh-so-78-2025-nd-cp-quy-dinh-the-thuc-ky-thuat-trinh-bay-van-ban-quy-pham-phap-luat-119250409084740906.htm)
3. [A Unified Ontology-Based Knowledge Graph Framework for Multi-Domain Vietnamese Legal Document Retrieval (dẫn Thông tư 25/2011/TT-BTP)](https://mjsat.com.my/index.php/mjsat/article/view/684)
4. [Nguyên tắc áp dụng văn bản QPPL (Bộ Tư pháp, nhắc Nghị định 34/2016/NĐ-CP)](https://tcdcpl.moj.gov.vn/qt/tintuc/Pages/thi-hanh-phap-luat.aspx?ItemID=642)
5. [SQLite FTS5 Extension](https://www.sqlite.org/fts5.html)
6. [Tencent/WeKnora](https://github.com/Tencent/WeKnora) · [docker-compose.yml](https://github.com/Tencent/WeKnora/blob/main/docker-compose.yml)
7. [infiniflow/ragflow](https://github.com/infiniflow/ragflow) · [Issue #6877](https://github.com/infiniflow/ragflow/issues/6877)
8. [Mintplex-Labs/anything-llm](https://github.com/Mintplex-Labs/anything-llm)

---

## Changelog bản 0.7 → 0.8

| Mã | Mục đã sửa | Tóm tắt thay đổi |
|---|---|---|
| Q7 | Q-bảng đầu, 4.3.9, 12.6 | Từ điển khởi tạo `synonyms_seed.csv`: 67 viết tắt `approved = 1`, 44 diễn đạt khác `approved = 0`; “chỉ `approved = 1`” giữ nguyên |
| Q8 | Q-bảng đầu, 0, 2.9, 5 | Nhận `.doc` / `.rtf` / ảnh / `.xlsx`; DOCX đọc đủ bảng, ghi chú; nạp không im lặng thất bại |
| Q9 | Q-bảng đầu, 3.1, 3.6 | Cụm “mức phạt” thành ý định: bỏ khỏi truy vấn, thẻ chế tài lên đầu |
| 2.9 | 2.9 (mới) | Đọc file thực tế: bảng, ghi chú, OCR (dpi gốc, khử nghiêng, OSD có điều kiện), tách văn bản, metadata, số trang thật |
| 3.6 | 3.6 | Ghi khoá sắp xếp cài đặt; **đính chính**: 3.6 của 0.7 đã ghi tầng → hạng, code 0.7 sai, 0.8 sửa code |
| 4.3.9 | 4.3.9 (mới), 4.2 | `~n`, `GCn`, `#vbk`, `ghi_chu`, `loi_ocr`, đường dẫn tuyệt đối, cổng, nạp lại theo cờ, `app_meta` |
| 6 | 6 | Số đo thực tế trên máy thử (không phải máy 8 GB) |
| 12.6 | 12 | Sprint 0.8: bảng L1–L21, kết quả đo, việc còn tồn |

Không đổi: Q1–Q6, F1–F4, bốn hạng thẻ, 6 tầng tìm, phạm vi “không embedding / LLM / RAG”.

## Changelog bản 0.6 → 0.7

| Mã | Mục đã sửa | Tóm tắt thay đổi |
|---|---|---|
| F1 | 3.5, 4.3.6, 8, 9 | `CHE_TAI` chỉ dạng “phạt … đối với hành vi” hoặc điểm dưới khoản đó; “buộc” chỉ đầu đơn vị trong khoản khắc phục hậu quả; loại “bắt buộc”/“ràng buộc”; Điều quy định chung không gắn |
| F2 | 1, 3.2, 4.3.1, 4.3.2, 8, 9 | Ngoại lệ Q6: unit OCR chưa đối chiếu luôn chạy thêm nhánh bỏ dấu trên tập đó, gộp dù nhánh có dấu đã có nhóm; thẻ mang nhãn OCR + Q6 |
| F3 | 3.6, 4.2 `subject_rules`, 4.3.1, 8, 9, 10 | Q5 so trên chữ có dấu, ranh giới từ, cụm dài nhất thắng, cụm < 2 tiếng phân biệt hoa thường; xét tên Điều “Trách nhiệm của {hạ ưu tiên}”; không dùng fold |
| F4 | 4.3.3, 8, 9 | Thiếu đuôi: `so_hieu_search LIKE '15/2020/%'`; cấm `%` đầu mẫu số hiệu; gõ `15/2020` không ra `115/2020/…` |

## Changelog bản 0.5 → 0.6

| Mã | Mục đã sửa | Tóm tắt thay đổi |
|---|---|---|
| Q5 | 0, 3.4, 3.6, 4.2 `subject_rules`, 4.3.1, 8, 9, 10 | Bảng ưu tiên / hạ ưu tiên; so khớp chuỗi; xếp sau hạng thẻ, trước hiệu lực; không đổi hạng; nhãn “nghĩa vụ của cơ quan khác” |
| Q6 | 1, 3.2, 3.3, 3.6, 4.3.2, 8, 9 | Truy vấn có dấu chạy đủ 6 tầng nhánh có dấu; bỏ dấu chỉ khi 0 nhóm; nhãn “khớp khi bỏ dấu, có thể khác nghĩa” |
| C1 | 4.2 `query_log`, 4.3.4, 4.3.5, 8, 9 | `selected_unit` `ON DELETE SET NULL`; thêm `selected_doc_id`, `selected_path`; nạp lại không bị chặn |
| C2 | 3.1, 4.3.3, 9 | Regex số hiệu `(?i)\d+/\d{4}/[A-ZĐ0-9-]+` giống nhau ở 3.1 và 4.3.3; fixture `nd-cp`/`NĐ-CP`, `QH15`, `TTLT-…` |
| C3 | 2.4, 3.3, 4.2 `units_fts`, 4.3.2, 4.3.5, 9 | `context_accent` trong FTS và trigger; MATCH `{search_accent context_accent}` / `{search_text context_search}`; `bm25` đủ 5 cột, `w_context < w_chữ_riêng`; test phạt tiền ở câu dẫn cha |
| D1 | 3.4, 3.5, 4.3.1, 8, 9 | Hạng 2 = “Rủi ro có chế tài (chưa có liên kết đã duyệt)”, gồm `confirmed=0` và `CHE_TAI` chưa nối; xoá quy tắc đẩy `CHE_TAI` một mình xuống hạng 4; hiện mức phạt theo 3.4 |
| D2 | 0, 3.6, 4.2, 4.3.1, 8, 9, 10 | Áp Q5: bảng `subject_rules`; tiêu chí xếp hạng; test 200 đơn vị; tuần 0 người dùng cung cấp hai danh sách |
| E1 | 3.2, 4.3.2, 9 | Kết quả cuối `thuế` không chứa đoạn chỉ-`thuê` trừ khi nhánh có dấu 0 nhóm (khi đó có nhãn Q6) |
| E2 | 2.7, 4.3.4, 8, 9 | Snapshot `(doc_id, path)` cả hai đầu liên kết; giữ link hai văn bản khi chỉ nạp lại một; thêm test |
| E3 | 3.3, 4.3.2, 8 | `df(từ)` = số dòng MATCH `"từ"` trên đúng cột nhánh; `fts5vocab` chỉ từ một tiếng; được cache theo phiên bản kho |
| E4 | 4.2, 4.3.2, 4.3.5, 5, 8, 9 | Đóng [cần kiểm chứng] `bm25()` và `fts5vocab`: thứ tự cột khai báo; tên bảng tự đặt `units_vocab`; probe khởi động hai exe; test máy sạch |
| E5 | 2.7, 4.2 `documents`/`import_jobs`, 4.3.4, 4.3.5, 8, 9 | `file_path` UNIQUE; trùng `sha256` khác path → `skipped_duplicate` + `existing_file_path`; thêm test |
| E6 | 2.4, 5, 8, 9 | Ngoài python-docx: ≥ 3 DOCX Word thật (numbering đoạn, numbering style, danh sách nhiều cấp) |
| E7 | đầu file, 0, 8, 10 | `soi-luat-checklist.md` hết hiệu lực tới khi viết lại theo 0.6; tuần 0 cập nhật checklist |

## Changelog bản 0.4 Lite → 0.5

| Mã | Mục đã sửa | Tóm tắt thay đổi |
|---|---|---|
| A1 | 0, 1, 3.4, 3.5, 3.6, 4.2 `unit_labels`, 4.3.1, 4.3.6, 8, 9 | Rủi ro không cần chế tài; bốn hạng thẻ; đổi tên “đã xác nhận” → “liên kết đã duyệt”; nhãn THOI_HAN, DIEU_KIEN |
| A2 | 0, 2.6, 3.4 D, 8, 10 | Q2: đếm “phạt tiền từ” và tỷ lệ; kho không xử phạt → thẻ loại 3 vẫn là đầu ra đúng |
| A3 | 0, 1, 4.1, 4.3.7 | “Tổng hợp” = gom kho; xuất Word chỉ báo cáo thẻ chọn |
| A4 | 3.5, 4.3.7, 11 | Ontology đầy đủ và mâu thuẫn liên văn bản không thuộc sản phẩm; ontology = nhãn + links |
| A5 | 2.4, 2.7, 2.8, 4.1, 4.3.4, 4.3.5, 4.3.7, 8, 9, 10, 11 | Cắt ba UI (ranh giới, OCR, tách file); sửa nguồn / cờ chia đoạn / nạp lại |
| A6 | 1, 3.3, 9 | Ví dụ “rò rỉ” ≠ “lộ, lọt”; đánh đổi đo bằng Recall@10 |
| A7 | 0, 8, 9, 10 | Cổng tuần 0: 5 từ khoá thật; khung phải diễn được cả 5 trước khi code search |
| B1 | 3.2, 3.3, 4.2, 4.3.2, 5, 9 | Cột `search_accent`; FTS `remove_diacritics 0`; có dấu trước, không dấu sau; test thuế/thuê |
| B2 | 3.4, 3.5, 4.2, 4.3.1, 9 | Chế tài = điểm; kế thừa phạt; `fine_source_unit`; dẫn chiếu nội bộ; không quy đổi cá nhân/tổ chức; parse triệu / NULL với % và gấp lần |
| B3 | 2.3, 4.2, 4.3.3, 4.3.4, 9 | UNIQUE `(doc_id, path)`; địa chỉ hiển thị ghép `so_hieu` lúc render; đổi số hiệu không mất link; hai file cùng số hiệu |
| B4 | 2.4, 4.2, 4.3.1, 4.3.4, 7 | Chữ riêng từng level; `context_search` BM25 thấp |
| B5 | 3.3, 4.3.2, 9 | Quote token FTS; cấm MATCH thô; test `" * - : ( )` AND OR NOT NEAR |
| B6 | 3.3, 4.3.2, 8, 9 | Tầng NEAR 10; tách từ longest-match; bớt theo IDF `fts5vocab` |
| B7 | 3.3, 3.6, 4.3.1, 4.3.2, 9 | Dừng đếm nhóm `(doc_id, Điều)` sau gom |
| B8 | 3.5, 4.3.6, 9 | Loại “không phải / không bắt buộc / không có nghĩa vụ”; test 200 unit |
| B9 | 0, 4.1, 4.3.8, 5, 8, 9 | Host allowlist; CSRF cookie SameSite=Strict mỗi lần start; không CORS |
| B10 | 2.4, 5, 9 | numbering.xml bắt buộc; COM `ListString` dự phòng |
| B11 | 3.3, 8, 9 | Công thức Recall@10 trên nhóm thẻ; loại `R_q` rỗng; đo riêng phần E |
| B12 | 2.5, 9 | C_liên_tục mới; 0/1 Điều biên; S ∈ [0,1] |
| B13 | 3.3, 3.6, 4.2 `effect_hints`, 4.3.6, 8, 9 | Gợi ý thay thế/bãi bỏ; không tự đổi `hieu_luc`; thẻ hết hiệu lực xám + cuối |
