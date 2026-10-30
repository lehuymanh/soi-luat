# Lộ trình nâng cấp Soi Luật (0.8 → 1.0)

- **Ngày:** 29/10/2026, cập nhật 30/10/2026 · **Trạng thái:** đang làm P0 (tiến độ và số đo ở mục 6, P0). Chủ dự án đã chốt ba điểm ngày 29/10/2026 (mục 9): câu trả lời AI xong trong ≤ 45 giây; chọn mô hình theo benchmark công khai, không dùng người chấm pháp lý; có máy 16 GB để đo.
- **Đầu vào:** phản hồi người dùng (ảnh chụp Telegram ngày 29/10/2026); mã nguồn 0.8 (`src/soiluat/`, 234 test đếm từ mã; khi soạn chưa chạy lại `pytest` vì môi trường soạn chưa cài thư viện); số đo trong `bench/*/KET-QUA.md`.
- **Máy mục tiêu mới:** PC Windows **16 GB RAM, không card rời** (chủ dự án chốt 29/10/2026). Máy đo chuẩn giữ nguyên: Ryzen 5 5600GT (6 nhân/12 luồng, AVX2, DDR4).
- **Quan hệ với kế hoạch 0.8:** kế hoạch và checklist 0.8 (`soi-luat-ke-hoach.md`, `soi-luat-checklist.md`, `bench/KE-HOACH-SUA.md`) đã xoá khỏi repo ngày 29/10/2026; bản cuối nằm ở commit `904160d` trong lịch sử git. Lộ trình giữ cách nạp, tách Điều, tìm kiếm và dựng thẻ **như mã 0.8 đang chạy** (mô tả ở `TAI-LIEU-KY-THUAT.md`). Ở vài chỗ mã đã lệch kế hoạch cũ (thứ tự xếp thẻ, điều kiện chạy nhánh không dấu); lộ trình lấy mã làm chuẩn. Kế hoạch 0.8 loại LLM khỏi sản phẩm; bản 1.0 thêm mô hình sinh câu trả lời chạy ngay trên máy, theo các ràng buộc ở mục 5. Lý do đổi: máy mục tiêu lên 16 GB, và người dùng cần một câu trả lời dễ đọc thay vì một danh sách thẻ dài.

---

## 0. Tóm tắt

| Phase | Nội dung | Phản hồi được giải quyết (mục 1) | Ước tính (1 người) | Xong khi |
|---|---|---|---|---|
| **P0** | Đo và chốt | nền cho mọi phase | 1 tuần | Mô hình chọn theo benchmark công khai được xác nhận trên máy 16 GB (xong ≤ 45 giây); có bộ đo câu trả lời chấm bằng máy; người dùng duyệt mẫu giao diện |
| **P1** | Mở đúng đoạn, kết quả gọn, lịch sử chat | ① ③ ④ ⑦ | 3 tuần | Bấm trích dẫn là văn bản mở ngay trong app, cuộn tới và tô đúng đoạn; mỗi câu hỏi hiện sẵn tối đa 5 mục, không trùng; có "Cuộc trò chuyện mới" và lịch sử |
| **P2** | Kho văn bản: tag, ghi chú, @, hiệu lực | ⑤ ⑥ ⑨ ⑩ | 3 tuần | Gõ @văn bản hoặc #tag để giới hạn phạm vi hỏi; gắn tag, viết ghi chú được; hiệu lực hiện ở mọi trích dẫn, kèm lý do |
| **P3** | Trợ lý trả lời: LLM chạy CPU, có kiểm chứng | ② ⑥ ⑪ | 4 tuần | Câu trả lời 2–3 câu bằng lời thường, xong trong ≤ 45 giây, mỗi ý có nguồn bấm được; không có số liệu nào lệch nguồn; kho không có căn cứ thì nói không có |
| **P4** | Liên kết văn bản kiểu Obsidian, hiệu lực theo Điều | ⑧ ⑨ | 3 tuần | Mỗi văn bản có bảng "Liên quan" (căn cứ, hướng dẫn, sửa đổi, thay thế, dẫn chiếu) và đồ thị cục bộ; Điều đã bị sửa đổi được đánh dấu |
| **P5** | Chuyên nghiệp, chỉn chu, phát hành | tất cả | 2 tuần | Không còn cửa sổ đen; bộ cài và gói AI; người dùng thật dùng một tuần đạt cổng |
| **Song song** | Độ chính xác tìm kiếm | nền cho P3 | xen kẽ P1–P3 | Thay đổi chỉ được giữ khi tốt hơn trên cả Zalo, gold và văn bản thật |

Làm tuần tự một người: khoảng 16 tuần. P4 và nhánh độ chính xác chạy song song được với P2–P3 nếu có người thứ hai.

**Mô hình (chọn theo benchmark công khai, mục 4):** **Qwen3-VL-4B-Instruct** (Apache-2.0), GGUF Q4_K_M chính hãng, chạy bằng llama.cpp trên CPU; dự phòng **Gemma 4 E4B** (QAT Q4_0). Lý do chính: điểm tiếng Việt cao nhất nhóm 4B ở chế độ trả lời kịp 45 giây (bảng SEA-HELM), nhất là phần hỏi đáp trích từ đoạn văn. Tốc độ chưa đo: P0 xác nhận trên máy 16 GB.

**Kho dữ liệu (mục 4b):** giữ SQLite + FTS5 làm kho duy nhất; vector tìm bằng NumPy như hiện tại, thêm USearch khi vượt ngưỡng RAM. Không dùng vector DB riêng hay đồ thị tri thức dựng bằng LLM kiểu Cognee, Graphiti (dựng mất nhiều tuần CPU); chỉ lấy ý tưởng quan hệ có thời hạn hiệu lực của Graphiti.

---

## 1. Phản hồi người dùng → việc cần làm

| # | Phản hồi (tóm ý) | Hiện trạng trong mã 0.8 | Làm gì | Phase |
|---|---|---|---|---|
| ① | Bấm link phải mở được tài liệu; đoạn được tóm tắt nằm ở trang nào, đoạn nào thì cắt đúng phần đó ra | Thẻ có "Xem nguồn →" mở tab mới `/unit/{id}`: một trang kỹ thuật (hash, cách trích, trạng thái OCR); ảnh trang gốc nằm trong `<details>`; chưa tô vùng chữ (`pages.bbox_json` và bảng `page_regions` có trong lược đồ nhưng chưa dùng) | Trình đọc văn bản ngay trong app, mở đúng Điều/khoản, tô đoạn và từ khớp. Với PDF/scan: ảnh trang có khung tô và ảnh cắt đúng đoạn gốc | P1 (chữ), nhánh chính xác (khung trên ảnh) |
| ② | Câu trả lời trông như "sớ", dạng .md, người thường đọc khó hiểu | App không sinh câu trả lời. Mỗi câu hỏi trả một loạt thẻ: trên kho văn bản thật trung bình ~40 thẻ (đo 23/10/2026 với bản Advance trước, `bench/van-ban-that/KET-QUA.md`; bản hiện tại chưa đo lại), kèm nhãn kỹ thuật (4 loại rủi ro, tầng khớp) | Câu trả lời 2–3 câu bằng lời thường, rồi phần "Căn cứ" bấm được. App tự dựng HTML từ dữ liệu có khuôn, nên ký hiệu Markdown không bao giờ hiện ra | P3 (AI), P1 (bố cục gọn khi chưa bật AI) |
| ③ | Danh sách tài liệu liên quan dài quá, nhiều cái trùng nên rối | Lấy tối đa 100 đơn vị theo BM25 (Advance thêm tới 50 Điều theo nghĩa; tra số hiệu trả mọi đơn vị của văn bản, không giới hạn), gom theo (văn bản, Điều), hiện hết. Điều trùng nội dung giữa các file không được gộp (`TAI-LIEU-KY-THUAT.md` mục 11 ghi là ý tưởng chưa làm) | Hiện sẵn 3–5 mục, gom theo văn bản, gộp nội dung trùng ("Cũng có ở 2 văn bản khác"), phần còn lại thu gọn | P1 |
| ④ | Muốn xem đoạn đó phải tải file; cần mở file và cuộn tới đoạn cần tìm | Như ①: chỉ xem được ảnh từng trang PDF/ảnh, không có toàn văn có neo | Như ①: mở trong app, không phải tải | P1 |
| ⑤ | Cho phép ghi chú, gắn tag từng tài liệu để phân loại | Chưa có. (`ghi_chu` trong code là footnote/comment trích từ file gốc, khác nghĩa) | Bảng `doc_tags`, `user_notes`; gắn tag hàng loạt; ghi chú cho cả văn bản hoặc cho một đoạn | P2 |
| ⑥ | AI khôn hơn: trả lời đúng khi @ chính xác tên tài liệu hoặc tag | Phần tìm đã tìm được trong phạm vi một số văn bản (`_fts_cascade(doc_ids=…)`, dùng khi câu hỏi có số hiệu), nhưng giao diện không có cách chọn; văn bản chưa có tên dễ đọc (trích yếu) | Gõ `@` gợi ý văn bản, gõ `#` gợi ý tag; phạm vi đã chọn đi vào phần tìm và phần trả lời AI | P2 (phạm vi), P3 (AI) |
| ⑦ | Có nút new chat/clear, có lịch sử như Claude | Hỏi–đáp chỉ nằm trên trang, tải lại là mất; không có phiên | Thanh bên chứa lịch sử, "Cuộc trò chuyện mới", đổi tên, xoá; mở lại không phải tìm lại | P1 |
| ⑧ | Danh sách tài liệu có thể liên quan làm được như Obsidian không | Có `links` (chế tài ↔ nghĩa vụ, kể cả sang văn bản khác khi Điều chế tài nêu số hiệu) và `effect_hints`. Nhưng `effect_hints` chỉ bắt "thay thế Nghị định số …", gợi ý "bãi bỏ" không ghi văn bản đích, và nạp lại văn bản nguồn thì xoá cả gợi ý đã duyệt (`ingest.py`). Chưa có quan hệ căn cứ, hướng dẫn, sửa đổi; chưa có giao diện | Bảng "Liên quan" theo loại quan hệ (tương đương backlinks) và đồ thị cục bộ; văn bản được nhắc tới mà chưa có trong kho hiện như liên kết chưa tạo của Obsidian | P4 |
| ⑨ | Tự lập index, tìm nhanh theo số hiệu, văn bản; còn hiệu lực không | Chỉ mục toàn văn (FTS5) và vector đã có; gõ số hiệu là ra thẳng (tầng 0, dưới 1 giây). Hiệu lực mặc định `chua_ro`, chỉ sửa tay ở `/review/docs`; duyệt gợi ý ở `/review/hints` không đổi hiệu lực | Chỉ mục cấp văn bản (trích yếu, từ khoá, quan hệ); huy hiệu hiệu lực có lý do; app gợi ý hiệu lực từ văn bản trong kho, người bấm xác nhận | P2, P4 |
| ⑩ | PDF scan: dùng thư viện AI trích chữ lưu DB, số trang, index, từ khoá, số hiệu | Đã làm bằng Tesseract: lưu từng trang, số trang, FTS, số hiệu. Đo trên 21 văn bản thật: chữ OCR giống bản gốc 98,5%, tách đúng 341/344 Điều; còn sai 5/21 số hiệu (viết tay hoặc nằm trong ô chữ ký số) và 7/21 ngày ban hành (5 viết tay, 2 do OCR đọc hỏng) | Giữ Tesseract. Thêm hàng chờ "văn bản thiếu thông tin" có ảnh trang để người điền; lưu toạ độ chữ để tô đoạn | P2, nhánh chính xác |
| ⑪ | Hỏi đáp thì dùng LLM | Không có LLM (cố ý, theo kế hoạch 0.8) | Trợ lý trả lời có kiểm chứng | P3 |

---

## 2. Những chỗ nên làm khác với đề xuất ban đầu

1. **Không thay bộ OCR.** Số đo cho thấy OCR không phải chỗ yếu (98,5% ký tự đúng, trung vị 100%). Chỗ yếu từng là tách cấu trúc và siêu dữ liệu, đã sửa còn 3/344 Điều sai. Phần còn lại chủ yếu là chữ viết tay và ô chữ ký số: không bộ OCR nào đọc chắc được, nên cần người điền (P2). Toạ độ chữ để tô đoạn mới có một nửa: `ocr.ocr_data` đã gọi `image_to_data` (có toạ độ từng chữ) nhưng chỉ giữ chữ và độ tin cậy. Toạ độ đó đo trên ảnh đã khử nghiêng, có thể đã xoay, ở 150–300 dpi; ảnh `/page` thì không xoay và khác tỉ lệ; góc và dpi không được lưu. Muốn tô đúng phải lưu thêm các thông số này (nhánh chính xác).
2. **"Mô hình tự lập index": chỉ mục đã có.** Cái còn thiếu là chỉ mục cấp văn bản, và làm được bằng quy tắc, không cần AI, nên không có ảo giác: trích yếu lấy từ trang đầu (`pages.raw_text`, vì parser bỏ phần mở đầu khỏi `units`); tóm tắt là nguyên văn Điều 1 "Phạm vi điều chỉnh"; từ khoá là các từ hay gặp trong văn bản nhưng hiếm trên toàn kho (đếm từ chữ của chính văn bản; độ hiếm lấy từ `units_vocab`, bảng này chỉ đếm âm tiết đơn trên toàn kho). Văn bản không có cấu trúc thì lấy đoạn đầu. Bản 1.0 không dùng LLM để lập chỉ mục.
3. **"Còn hiệu lực không" chỉ trả lời được theo các văn bản đang có trong kho.** App không biết văn bản ngoài kho. Vì vậy huy hiệu luôn kèm bằng chứng ("bị thay thế bởi …, Điều …") và ngày kho được cập nhật. LLM không được tự kết luận hiệu lực; nó chỉ đọc trạng thái do app cung cấp.
4. **LLM trên CPU chậm; chủ dự án chốt chờ tối đa 45 giây**, tính từ lúc bấm Enter tới khi câu trả lời xong. Trên CPU, điều đó có nghĩa: phần tìm giữ ~5–9 giây (reranker chạy nhiều luồng hơn thì mô hình có thêm thời gian), prompt ~1.000 token, câu trả lời tối đa 200 token, và mô hình phải đủ nhanh. Đây là ràng buộc chính khi chọn mô hình (mục 4). Việc quy tắc làm được (tra số hiệu, lọc, gộp trùng, hiệu lực) thì không đưa cho LLM.
5. **Không fine-tune mô hình.** Kế hoạch 0.8 đã loại vì cần GPU thuê và khó kiểm chứng. Thay bằng: tìm tốt (đã có), khuôn đầu ra bắt buộc và kiểm tra tự động sau khi sinh (mục 5).
6. **Đồ thị toàn kho hàng nghìn nút đẹp nhưng không đọc được.** Giá trị thật của "kiểu Obsidian" là backlinks theo loại quan hệ và đồ thị cục bộ 1–2 bước. Làm hai thứ đó trước; đồ thị toàn kho chỉ làm nếu dùng rồi vẫn thấy cần.
7. **Không làm "hỏi về cả một văn bản dài" (vd. tóm tắt một luật 100 Điều) trong 1.0.** Đưa 30–50 nghìn token vào mô hình trên CPU mất nhiều phút. Chạy nền ban đêm cũng không chắc, vì máy văn phòng thường tắt app khi về. Thay bằng mục lục, Điều 1, và câu hỏi cụ thể kèm @văn bản.
8. **Bớt "chế độ".** Màn hỏi chỉ còn một công tắc "Trả lời bằng AI"; Normal/Advance chuyển vào Cài đặt với tên "Chế độ nhẹ" cho máy yếu. Đề xuất ban đầu là để Advance làm mặc định trên máy 16 GB. **Số đo P0 (30/10/2026) không ủng hộ đề xuất này:** trên 21 văn bản thật, Advance có Hit@1 72,6%, Normal 83,3% (tính rộng; tính chặt theo số Điều: 69,0% và 78,6%; `bench/van-ban-that/KET-QUA.md`). Vì vậy giữ Normal làm mặc định cho tới khi nhánh độ chính xác sửa xong bước hợp (mục 6, nhánh song song, điều 0); quyết định cuối ở mục 9.
9. **Không cần "vector DB" riêng hay đồ thị tri thức dựng bằng LLM (kiểu Cognee, Graphiti).** Phần phụ thuộc CSDL chỉ chiếm tối đa ~1 giây trong ~9 giây của một câu Advance (reranker chiếm ~5 giây). Độ chính xác nằm ở thuật toán (hai cột có dấu/không dấu, các tầng khớp BM25, mô hình nhúng, reranker), không nằm ở CSDL. Dựng đồ thị tri thức bằng LLM cho 61 nghìn Điều trên CPU ước tính mất 10–33 ngày chạy liên tục, riêng Graphiti 6–12 tháng; chính LightRAG ghi rằng chạy cục bộ cần tối thiểu mô hình cỡ Qwen3-30B-A3B. Lấy ý tưởng, không lấy framework (mục 4b).

---

## 3. Các cách đã cân nhắc

**Kiểu câu trả lời**

| Cách | Được | Mất | Chọn |
|---|---|---|---|
| Chỉ trích nguyên văn như 0.8, sửa giao diện cho gọn | Không ảo giác, nhanh | Không trả lời thẳng; người thường vẫn phải tự đọc luật (phản hồi ②) | Dùng khi tắt AI |
| LLM viết tự do (Markdown) | Dễ làm | Chính là kiểu "sớ .md" bị chê; không kiểm được nguồn từng ý; dễ bịa số | Không |
| LLM điền khuôn JSON; app dựng giao diện; app kiểm nguồn và số liệu | Ngắn, đúng khuôn, mỗi ý có nguồn, kiểm tự động được | Phải viết bộ kiểm; mô hình nhỏ đôi khi lệch khuôn (khắc phục bằng ràng buộc JSON schema của llama.cpp) | **Chọn** |

**Cách chạy mô hình**

| Cách | Được | Mất | Chọn |
|---|---|---|---|
| `llama-server.exe` của llama.cpp (MIT), chạy như tiến trình con | Không thêm thư viện Python; có sẵn ràng buộc JSON schema, trả chữ dần (stream), cache prompt; tách tiến trình nên tắt là trả RAM, mô hình lỗi không kéo app chết; nâng cấp bằng cách thay file exe | Thêm một tiến trình phải quản lý (khởi động, cổng, tắt) | **Chọn** |
| llama-cpp-python trong cùng tiến trình | Gọi hàm trực tiếp | Wheel Windows phải tự dựng hoặc lấy nguồn ngoài; PyInstaller nặng thêm; RAM mô hình dính vào app | |
| onnxruntime-genai | Dùng lại onnxruntime | Ít mô hình mới có sẵn bản ONNX int4, phải tự chuyển; ràng buộc đầu ra yếu hơn | |
| Ollama | Thử nhanh | Cài riêng, chạy dịch vụ nền, khó gói vào một bộ cài, trang web khác trên máy gọi vào được | |

**Nền giao diện**

| Cách | Được | Mất | Chọn |
|---|---|---|---|
| Giữ FastAPI + Jinja + JavaScript thuần, tách JS/CSS ra `static/` | Không thêm công cụ build; test hiện có (TestClient) dùng tiếp; đóng gói như cũ | Phải tự viết @mention, ngăn kéo, đồ thị | **Chọn** |
| SPA (React/Svelte) + Node | Có sẵn thư viện giao diện | Thêm chuỗi build Node (kế hoạch 0.8 đã loại); viết lại toàn bộ giao diện | |
| Vỏ desktop (pywebview, Electron, Tauri) | Cửa sổ riêng | Thêm phụ thuộc lớn; Edge `--app` cho kết quả gần như vậy bằng một dòng lệnh | |

**Kho dữ liệu cho phần truy hồi** (chi tiết mục 4b)

| Cách | Được | Mất | Chọn |
|---|---|---|---|
| Giữ SQLite + FTS5 làm kho duy nhất; vector tìm vét cạn bằng NumPy như hiện tại, thêm USearch khi vượt ngưỡng RAM | Không thêm byte nào vào bộ cài; một file, một giao dịch, một cơ chế sao lưu; FTS5 đủ cụm từ, NEAR, trọng số cột; giữ nguyên các hệ số đã chỉnh trên bộ đo | Phần hợp kết quả tự viết (đã có) | **Chọn** |
| Thêm kho thứ hai (LanceDB, Qdrant, DuckDB…) | Có sẵn tìm kết hợp, chỉ mục ANN | Hai kho phải đồng bộ; viết lại `search.py` và chỉnh lại BM25; LanceDB bỏ dấu mặc định; không làm câu trả lời đúng hơn | |
| Framework đồ thị tri thức (Cognee, Graphiti, LightRAG, GraphRAG) | Đồ thị tự dựng, hỏi theo quan hệ | Dựng mất nhiều tuần tới nhiều tháng CPU; thêm lệnh LLM khi hỏi nên vượt 45 giây; cần mô hình lớn hơn; Graphiti cần Neo4j (GPL-3.0, JVM) | Không, chỉ lấy ý tưởng |

**Đồ thị liên quan:** backlinks + đồ thị cục bộ vẽ bằng SVG, không thư viện (**chọn trước**); đồ thị toàn kho bằng thư viện nhúng sẵn, giấy phép MIT, vd. Cytoscape.js (chỉ khi cần, mục 9).

---

## 4. Chọn mô hình (16 GB, không card rời, ≤ 45 giây)

Yêu cầu của chủ dự án: nhỏ, đủ ngữ cảnh, ít ảo giác, phản biện và làm luật tốt, chạy CPU; chọn theo benchmark công khai. Đầy đủ số liệu, nguồn và các mô hình đã loại: `bench/llm/CHON-MO-HINH.md` (tra 29/10/2026).

**Chọn: Qwen3-VL-4B-Instruct**, GGUF Q4_K_M chính hãng của Qwen (2,33 GiB), chạy như mô hình chữ (không cần file ảnh `mmproj`). **Dự phòng: Gemma 4 E4B**, GGUF QAT Q4_0 chính hãng của Google, tắt thinking.

| | **Qwen3-VL-4B-Instruct** | Gemma 4 E4B | Qwen3.5-4B (đề xuất cũ) |
|---|---|---|---|
| Giấy phép, ngày | Apache-2.0; repo tạo 11/10/2025; llama.cpp hỗ trợ từ 30/10/2025 | Apache 2.0; repo tạo 02/03/2026, Google công bố 31/03–02/04/2026 | Apache-2.0; repo tạo 27/02/2026, công bố 02/03/2026 |
| Chế độ chạy kịp 45 giây | không suy nghĩ (bản Instruct chỉ có chế độ này) | tắt thinking | tắt thinking |
| SEA-HELM tiếng Việt, tổng | **64,2** | 62,8 | 52,2 |
| Hỏi đáp trích từ đoạn văn (XQuAD-vi) | **77,5** | 44,7 | 75,0 |
| Suy ra / mâu thuẫn (XNLI-vi) | **50,0** | 39,9 | 14,3 |
| Làm theo chỉ dẫn tiếng Việt (SEA-IFEval) | 87,0 | 88,2 | 77,9 |
| Ảo giác khi tóm tắt (Vectara), đo trên mô hình cùng họ | họ Qwen3: 4,8–5,7% | họ Gemma 4: 5,2–7,4% | họ Qwen3.5: 10,5–12,1% |
| File GGUF Q4 | 2,33 GiB | 4,8 GiB (giữ mmap thì RAM ~3,4 GB) | 2,81 GiB |

Nguồn: SEA-HELM của AI Singapore, phần tiếng Việt, cập nhật 18/09/2026, chế độ không suy nghĩ (trên trang phải bật "Non-reasoning variants" mới thấy các dòng này); bảng ảo giác Vectara cập nhật 22/10/2026 (không có đúng ba mô hình trên, chỉ có mô hình cùng họ). Các số trong bảng đã được đọc lại tại nguồn ngày 29/10/2026.

**Vì sao chọn Qwen3-VL-4B:**

- Hai bài gần việc của app nhất là hỏi đáp trích từ đoạn văn (chỉ trả lời từ tài liệu đưa vào) và suy ra/mâu thuẫn (chỉ ra tiền đề sai). Ở chế độ chạy kịp 45 giây, Qwen3-VL-4B cao nhất nhóm 4B ở cả hai.
- Bật chế độ suy nghĩ thì Qwen3.5-4B mạnh hơn (tổng 69,0), nhưng chế độ đó sinh thêm hàng trăm token, không vừa 45 giây trên CPU.
- File nhỏ nhất nhóm nên sinh chữ nhanh nhất; kiến trúc attention thường, llama.cpp hỗ trợ ổn định từ 10/2025.

**Rủi ro** (đo ở P0, `bench/llm/KET-QUA.md`: vòng 1 chèn chữ Trung ở 0–10% câu trả lời và khi đã bỏ Điều đúng vẫn nói đủ căn cứ ở 33–73% số câu, nhóm lớn nhất là khái quát quá phạm vi đoạn; vòng 2 chặn được chữ Trung bằng grammar, còn khẳng định như đủ căn cứ ở 13–40%): chưa có số đo bám ngữ cảnh công khai cho đúng mô hình này; kiến thức tiếng Việt thấp (43,4), nên khi ngữ cảnh thiếu căn cứ nó có thể điền bằng kiến thức sai, và cờ `du_can_cu` cùng bộ kiểm số liệu phải chặn được; có thể chèn chữ Trung hoặc Anh (kiểm tự động được).

**Không chọn:** Qwen3.5-4B (tiếng Việt thấp nhất nhóm khi tắt suy nghĩ; họ Qwen3.5 ảo giác gấp đôi). Qwen3.5-9B và Vi-Qwen2-7B-RAG (ước tính 92–113 giây mỗi câu; 9B còn vượt trần RAM). Gemma 4 12B (file 7,65 GB). Mô hình 2B (vừa 45 giây nhưng tiếng Việt kém rõ, tổng ≤ 53,3). MoE 26B–35B (cần 15–20 GB RAM).

**Ngân sách RAM trên máy 16 GB**

| Thành phần | RAM |
|---|---|
| Windows + Office + trình duyệt | 5–7 GB (ước tính máy văn phòng) |
| App ở Advance (hai mô hình AITeamVN + ma trận vector 61 nghìn Điều) | ~2,2 GB (đã đo) |
| Qwen3-VL-4B Q4_K_M + KV cho 2–4 nghìn token | ~3,2–3,5 GB (ước tính, P0 đo) |
| **Tổng app** | **~5,5–6 GB**, còn dư ≥ 3 GB |

**Thời gian (ước tính, chưa đo; P0 đo):** trên CPU AVX2 6 nhân, mô hình 4B đọc prompt khoảng 30–70 token/giây (trung tâm ~45) và sinh chữ ~12–15 token/giây với DDR4-3200 hai kênh. Với prompt 1.500 token, tổng ước tính ~53 giây, quá 45 giây. **Vì vậy đặt trần prompt ~1.000 token và tối đa 200 token ra**: tổng trung tâm ~42–45 giây. Để p95 cũng ≤ 45 giây, máy phải đọc prompt ≥ ~60 token/giây. Máy cắm một thanh RAM (một kênh) sinh chữ chậm gần gấp đôi. Nếu đo thấy chậm hơn, có ba cách, chủ dự án chọn: đưa 3 đoạn thay vì 5 và cắt sát khoản khớp; dùng mô hình 2B (yếu hơn rõ); hoặc nới thời gian chờ.

**Xác nhận trên máy 16 GB (P0), chấm hoàn toàn bằng máy**

Chủ dự án không có người chấm pháp lý, nên mô hình được chọn theo benchmark công khai, rồi chỉ cần xác nhận trên máy thật bằng các phép kiểm có đáp án sẵn:

- Máy 16 GB, Office và trình duyệt đang mở. Mô hình chính và mô hình dự phòng; `llama-bench` (pp512, tg128) ở 4 và 6 luồng; đo RAM.
- Đáp án lấy từ các bộ đo có sẵn, không cần người viết: mỗi câu trong Zalo test, gold `vle` (chỉ giữ trên máy) và văn bản thật đều đã có Điều đúng.
  - **Dẫn đúng Điều:** khi Điều đúng có trong ngữ cảnh, câu trả lời có dẫn Điều đó không.
  - **Từ chối đúng:** cùng câu hỏi nhưng bỏ Điều đúng khỏi ngữ cảnh: mô hình có trả `du_can_cu = false` không.
  - **Tiền đề sai:** câu bẫy sinh tự động từ các Điều có mức phạt (`units.fine_min`, `fine_max`), hỏi với mức tiền sai; mô hình có chỉ ra và nêu đúng mức trong nguồn không (kiểm bằng so số).
  - Mọi câu: JSON hợp lệ, nguồn hợp lệ, số liệu khớp nguồn, thời gian từ lúc bấm Enter tới khi xong.
- Mô hình chính đạt cổng P0 thì giữ; không đạt thì thử mô hình dự phòng.

---

## 4b. Kho dữ liệu cho phần truy hồi

Chủ dự án yêu cầu tìm CSDL mã nguồn mở phù hợp, kể cả loại "bộ nhớ AI / đồ thị tri thức" như Cognee, Graphiti. Đầy đủ so sánh (khoảng 30 lựa chọn), nguồn và số đo: `bench/llm/CHON-CSDL.md` (tra và đo ngày 29/10/2026). Số đo chạy trên máy ảo khác máy chuẩn, chỉ dùng để so tương đối.

- **Giữ SQLite (WAL) + FTS5 làm kho duy nhất.** Mọi bảng mới của 1.0 (lịch sử chat, tag, ghi chú, quan hệ văn bản) nằm cùng file, cùng giao dịch, cùng sao lưu, cùng cascade khi xoá văn bản.
- **Vector: giữ tìm vét cạn bằng NumPy như hiện tại.** Trên vector giả 1024 chiều, 1 luồng: 61 nghìn vector ~19 ms, 250 nghìn ~77 ms. Tốc độ không phải vấn đề; ràng buộc thật là RAM (ma trận float32: 252 MB ở 61 nghìn vector, ~977 MB ở 250 nghìn).
- **Ngưỡng nâng cấp**, khi nhúng theo khoản (nhánh độ chính xác, mục 2) làm số vector tăng:

  | Khi | Làm |
  |---|---|
  | Ma trận float32 > ~500 MB (≈ 125 nghìn vector), hoặc RAM đỉnh Advance > 2,5 GB | Giữ float16 trong RAM, tìm chính xác bằng USearch (Apache-2.0, wheel Windows 0,34 MB) |
  | Ma trận float16 > ~500 MB (≈ 250 nghìn vector) | int8 + USearch lấy top-200, rồi chấm lại bằng float16 |
  | Bước tìm vector > ~150 ms (p95) trên máy chuẩn | Chỉ mục HNSW của USearch, lưu file như bộ nhớ đệm, lệch với SQLite thì dựng lại |

  Mỗi bước phải qua quy tắc giữ ở mục 5 (điều 7). USearch bản Windows phải đo trên máy chuẩn trước khi dùng.
- **Không dùng:**
  - sqlite-vec: bản ổn định chỉ quét toàn bộ, chậm hơn NumPy 6–7 lần trên vector giả; chỉ mục ANN mới ở bản alpha (05/2026).
  - LanceDB, Qdrant, DuckDB, Chroma, Meilisearch…: là kho thứ hai, hoặc trái ràng buộc. Meilisearch bỏ dấu chữ Latin; tìm kết hợp của Chroma chỉ có trên bản Cloud; chỉ mục HNSW lưu đĩa của DuckDB còn thử nghiệm.
  - Framework đồ thị tri thức dựng bằng LLM (mục 2, điều 9).
  - Kho đồ thị: Neo4j (GPL-3.0, cần JVM), Kùzu (ngừng từ 10/10/2025), FalkorDB (SSPL), Memgraph và ArangoDB (BSL).
- **Ý tưởng lấy từ Graphiti, Cognee mà không cần framework** (áp vào P2, P4):
  - Mỗi quan hệ có hai trục thời gian: hiệu lực từ ngày–đến ngày, và ghi nhận lúc–xác nhận lúc. Quan hệ hết hiệu lực thì đánh dấu, không xoá; tra được "theo ngày X".
  - Mỗi quan hệ nhớ nguồn: văn bản, đơn vị, đoạn trích.
  - Cạnh "nội dung tương tự" dựng từ vector sẵn có (top-k và ngưỡng cosine, chạy nền vài phút), ghi rõ là tương tự chứ không phải quan hệ pháp lý.

---

## 5. Nguyên tắc chính xác (áp dụng cho mọi phase)

1. **Nguyên văn đến từ kho, không đến từ mô hình.** Phần trích dẫn luôn lấy từ `units` theo id. Mô hình chỉ viết phần diễn giải ngắn.
2. **Mỗi ý phải có nguồn nằm trong danh sách đã đưa vào.** Ràng buộc bằng JSON schema (mã nguồn là enum), rồi kiểm lại sau khi sinh.
3. **Số liệu phải khớp nguyên văn.** Mọi số tiền, số ngày, tỉ lệ, ngày tháng, "Điều n" trong câu trả lời phải có trong đoạn được dẫn, sau khi chuẩn hoá cách viết ("5.000.000 đồng" ↔ "5 triệu đồng"). Không khớp thì bỏ ý đó và ghi "chưa kiểm được".
4. **Không đủ căn cứ thì nói không đủ căn cứ**, kèm văn bản gần nhất tìm được.
5. **Hiệu lực hiện cạnh mọi trích dẫn.** Văn bản hết hiệu lực không được dùng làm căn cứ, trừ khi người dùng bật.
6. **Máy gợi ý, người quyết.** Hiệu lực, quan hệ văn bản, số hiệu, liên kết chế tài chỉ đổi khi có người bấm xác nhận (giữ nguyên tắc 0.8).
7. **Đo trước khi giữ.** Thay đổi phần tìm chỉ được giữ khi tốt hơn trên cả Zalo lẫn gold `vle` (quy tắc ở `bench/gold/README.md`) và không tụt trên văn bản thật. Đây là quy tắc giữ duy nhất cho phần tìm. Thay đổi phần trả lời phải qua `bench/llm` (dựng ở P0).
8. **Không gửi gì ra ngoài.** Giữ 0 kết nối ngoài `127.0.0.1`; P5 kiểm lại trên bản đóng gói.

---

## 6. Các phase

### P0 — Đo và chốt (1 tuần)

**Mục tiêu:** quyết định bằng số đo; có thước đo câu trả lời và mốc tìm kiếm trước khi viết tính năng.

1. Chọn mô hình theo benchmark công khai (`bench/llm/CHON-MO-HINH.md`), rồi xác nhận trên máy 16 GB theo mục 4, ghi `bench/llm/KET-QUA.md`; chốt mô hình, mức lượng tử, số luồng.
2. Dựng bộ đo câu trả lời `bench/llm/`, chấm hoàn toàn bằng máy (mục 4): kịch bản chạy qua `llama-server`; đáp án là Điều đúng có sẵn trong các bộ đo; câu bẫy sinh từ mức phạt. Câu lấy từ ViLegalExperts chỉ giữ trên máy, như `bench/gold` (bộ này chưa ghi giấy phép).
3. **Đo lại mốc tìm kiếm trên văn bản thật** (21 văn bản, 84 câu) với Advance hiện tại (AITeamVN): Hit@k và số thẻ trung bình mỗi câu. Chưa có lần đo nào của bản Advance này trên văn bản thật (`bench/gold/KET-QUA.md` chỉ ghi Normal); cổng P1 cần mốc này.
4. Gom ≥ 100 câu hỏi thật của văn phòng kèm Điều đúng (`bench/gold/README.md`, phần `van-phong`). Việc này của người dùng; phải có trước cổng P3.
5. Làm mẫu giao diện bấm thử được (HTML tĩnh): màn chat có thanh lịch sử, câu trả lời gọn, trình đọc văn bản, @mention, trang Kho, bảng Liên quan. Người dùng góp ý trước khi code.

**Cổng:** mô hình được chọn, trên máy 16 GB đang mở Office: trả lời xong ≤ 45 giây (p95, tính cả phần tìm); JSON hợp lệ ≥ 99%; dẫn đúng Điều ≥ 80% khi Điều đúng có trong ngữ cảnh; từ chối đúng ≥ 80% khi đã bỏ Điều đúng. Các ngưỡng chất lượng là đề xuất, chốt khi có số. Cả mô hình chính lẫn dự phòng đều không đạt thì dừng P3 và báo lại; P1, P2, P4 vẫn làm. Người dùng đồng ý với mẫu giao diện.

**Trạng thái P0 (30/10/2026)**

| Bước | Trạng thái |
|---|---|
| 1. Xác nhận mô hình | **Vòng 2 trên máy ảo (sau 7 việc sửa), Qwen3-VL-4B, tập test:** dẫn đúng Điều 83,3 / 75,0 / 86,7% (vòng 1: 66,7 / 70,0 / 46,7%; Zalo / gold / văn bản thật); JSON dùng được 100% ở cả ba bộ (đọc ngay 78,8 / 95,0 / 96,7%; ở Zalo do câu bẫy dài chạm trần 200 token); khẳng định như đủ căn cứ khi đã bỏ Điều đúng 26,7 / 40 / 13,3% (vòng 1: 66,7 / 65 / 33,3%); từ chối hẳn 16,7 / 20 / 60%, tính cả câu nêu phạm vi hẹp hơn 73,3 / 60 / 86,7%; chữ Trung 0%. **Cổng chưa đạt trọn:** dẫn đúng đạt 2/3 bộ; JSON và từ chối đạt hay không tùy cách tính (mục 9, điều 10). Gemma 4 E4B (dự phòng) không hơn: dẫn đúng gộp ba bộ 48/65 so với 53/65 của Qwen, khẳng định sai 19/65 so với 18/65 (chênh lệch chưa vượt nhiễu), viết dài hơn và tốn thêm ~30% thời gian; giữ Qwen làm mô hình chính vì nhanh hơn và tệp nhỏ bằng nửa. Ứng viên mới tìm thêm, Nemotron-3.5-Bolt-E4B (23/10/2026), kém cả hai: dẫn đúng 44/65, khẳng định sai 24/65 (`bench/llm/CHON-MO-HINH.md` mục 7). Đổi mô hình cùng cỡ không sửa được lỗi phạm vi; hướng tiếp theo ở luồng xử lý. Chi tiết: `bench/llm/KET-QUA.md`. Còn lại: đo tốc độ, RAM, p95 45 giây trên máy 16 GB |
| 2. Bộ đo câu trả lời | **Xong.** `bench/llm/run.py` (dẫn đúng, từ chối, tiền đề sai, JSON, số liệu, chữ CJK, thời gian) dùng chung mã với app: `src/soiluat/answer.py` (ngữ cảnh, lời nhắc, khuôn JSON, bộ kiểm số liệu) |
| 3. Mốc tìm kiếm trên văn bản thật | **Xong.** Hit@1 (rộng) Normal 83,3%, Advance 72,6%; ~40 thẻ mỗi câu (`bench/van-ban-that/KET-QUA.md`); xem mục 2 điều 8 |
| 4. ≥ 100 câu hỏi thật của văn phòng | Chưa (người dùng) |
| 5. Mẫu giao diện | **Xong**, chờ người dùng duyệt: `mau/giao-dien-1.0.html` |

### P1 — Mở đúng đoạn, kết quả gọn, lịch sử chat (3 tuần)

**Giải quyết:** ① ③ ④ ⑦.

**1a. Trình đọc văn bản** (thay trang `/unit/{id}`)

- Route `/doc/{doc_id}` hiển thị toàn văn. Thân văn bản dựng từ `units` theo thứ tự (Điều, khoản, điểm, đoạn), mục lục Điều ở bên trái, mỗi đơn vị có neo `#u{id}`. Mở `/doc/{id}#u{unit}` thì cuộn tới, tô nền đoạn và tô đậm từ khớp câu hỏi.
- Phần parser bỏ khỏi `units` lấy từ `pages.raw_text`: phần mở đầu (căn cứ, trích yếu), khối nơi nhận/chữ ký và mọi thứ sau nó cho tới Điều kế tiếp (`parse.py`: `_preamble_line`; cờ `in_sign` chỉ tắt khi gặp Điều mới). Tên Chương/Mục cũng bị bỏ (`parse.CHUONG_MUC`), nên mục lục 1.0 chỉ theo Điều; muốn có Chương thì phải lưu thêm khi nạp (builder quyết).
- Mở dạng ngăn kéo bên phải màn chat, để không mất cuộc trò chuyện; có nút mở toàn màn hình.
- Đầu trang: số hiệu, trích yếu (P2), loại, cơ quan, ngày, huy hiệu hiệu lực; nút "Sao chép trích dẫn" theo dạng "Khoản 1 Điều 5 Nghị định 15/2020/NĐ-CP".
- Tab "Bản gốc" cho PDF/ảnh: ảnh đúng trang của đơn vị (dùng `/page/{doc}/{n}` có sẵn), chuyển trang được. `/page` hiện chỉ phục vụ PDF, PNG, JPG (`pageimg.VIEWABLE`) dù app nhận cả TIFF, BMP: thêm hai loại này (đổi sang PNG bằng Pillow khi có; bản đóng gói đủ có Pillow vì OCR dùng). Khung tô trên ảnh làm ở nhánh chính xác.
- Văn bản không có cấu trúc: hiện theo trang/đoạn, vẫn có neo.
- Thông tin kỹ thuật (hash, cách trích, trạng thái OCR) chuyển vào mục "Chi tiết kỹ thuật" thu gọn.

**1b. Kết quả gọn**

- Mặc định hiện 5 mục đầu theo thứ tự xếp hạng hiện có; "Xem thêm" mở thêm từng 10 mục.
- Mỗi mục: tên Điều và số hiệu; 1–3 câu trích quanh chỗ khớp, cắt theo khoản/điểm khớp chứ không đổ cả Điều; từ khớp tô đậm; nút "Mở tại đoạn này".
- Gộp trùng: các Điều có nội dung chuẩn hoá giống nhau (băm chữ của Điều và các đơn vị con) ở nhiều file thành một mục, ghi "Cũng có ở: …"; mục đại diện ưu tiên văn bản còn hiệu lực, mới hơn.
- Một văn bản có ≥ 2 mục trong nhóm đầu thì gom lại: "15/2020/NĐ-CP · 3 đoạn".
- Bốn ô thống kê rủi ro thu thành một dòng nhỏ; nhãn kỹ thuật chuyển vào chú thích khi rê chuột. Giữ nguyên bốn hạng thẻ (`cards.KIND_RANK1`–`KIND_RANK4`) và thứ tự xếp hiện tại của `cards.assemble_cards`.
- Nhãn "Độ tin cậy cao / Chưa chắc chắn" giữ, viết lại bằng lời thường. Xuất Word giữ nguyên.

**1c. Cuộc trò chuyện**

- Bảng `conversations(id, title, scope_json, created_at, updated_at)` và `messages(id, conversation_id, role, text, result_json, answer_json, created_at)`. `result_json` lưu id đơn vị kèm `(doc_id, path)` và nhãn tin cậy, để mở lại không phải tìm lại. Nạp lại một văn bản làm đổi id đơn vị (`ingest.py` xoá rồi tạo lại `units`), nên khi mở lại thì tìm lại theo `(doc_id, path)`, như `rebuild.restore_links` đang làm với liên kết; không thấy nữa thì báo "nguồn đã thay đổi, hãy hỏi lại".
- Thanh bên trái: "+ Cuộc trò chuyện mới"; danh sách chia Hôm nay / 7 ngày qua / Cũ hơn; ô tìm trong lịch sử; đổi tên; xoá (hỏi lại trước khi xoá). Tiêu đề lấy từ câu hỏi đầu (cắt 60 ký tự), không cần AI.
- URL `/c/{id}`; có phím tắt mở cuộc trò chuyện mới. `query_log` giữ nguyên (dùng cho đo và trang "Truy vấn bỏ sót").
- Ghi lượt mở trích dẫn cho đúng câu hỏi: khi người dùng bấm trích dẫn, app gửi (mã tin nhắn, id đơn vị) về server. Cách cũ không dùng tiếp được: `/unit/{id}` ghi vào dòng `query_log` mới nhất bất kể câu nào sinh ra thẻ, còn neo `#u…` của trình đọc không tới server. Dữ liệu này cần cho việc chỉnh `SURE_GAP` (nhánh chính xác).

**Kỹ thuật:** tách JS/CSS khỏi `index.html` (450 dòng) ra `static/`, phục vụ bằng `StaticFiles`, thêm vào `package-data` và `pack/SoiLuat.spec`. Giữ Jinja trả HTML từng phần; không thêm Node hay SPA. Mọi endpoint ghi mới đi qua `_check_csrf`.

**Cổng P1:**

- Bấm một trích dẫn: trình đọc mở đúng văn bản, đúng đơn vị, đoạn được tô, trong ≤ 1 giây với kho 61 nghìn Điều.
- Hit@1/@5 tính theo mục hiển thị không thấp hơn mốc hiện có trên Zalo và gold, và mốc đo ở P0 trên văn bản thật (gộp trùng và gom nhóm không được làm tụt).
- Số mục hiện sẵn ≤ 5 (từ ~40).
- Mở lại cuộc trò chuyện cũ hiện đúng kết quả mà không chạy lại tìm kiếm.
- 3–5 người dùng thật làm 8 việc (tìm đoạn, mở đúng đoạn, mở cuộc mới, tìm lại cuộc cũ…): ≥ 90% việc làm được không cần hướng dẫn.
- `pytest` xanh, có test mới cho: neo và tô đúng đơn vị, gộp trùng, thêm/sửa/xoá cuộc trò chuyện, CSRF.

### P2 — Kho văn bản: tag, ghi chú, @, hiệu lực (3 tuần)

**Giải quyết:** ⑤ ⑥ ⑨ ⑩.

**2a. Trang Kho** (cho người dùng thường; `/review/docs` giữ cho người duyệt)

- Danh sách văn bản: số hiệu, trích yếu, loại, cơ quan, ngày, hiệu lực, tag, số Điều. Lọc theo các cột, theo tag và theo "thiếu thông tin"; tìm theo tên hoặc số hiệu.
- Sửa thông tin ngay tại chỗ (số hiệu, trích yếu, ngày, cơ quan, hiệu lực), có ảnh trang đầu bên cạnh với bản scan. Đây là cách xử lý 5/21 số hiệu viết tay hoặc nằm trong ô chữ ký số.
- Xoá văn bản: hỏi lại trước khi xoá; units, vector, FTS xoá theo cascade; hỏi có xoá bản sao trong `data/files` không. Lấp giới hạn "không có nút xoá/sửa từng văn bản" (`TAI-LIEU-KY-THUAT.md` mục 11).
- Cột mới `documents.trich_yeu`: lấy tự động từ `pages.raw_text` trang đầu (dòng sau tên loại, vd. sau "NGHỊ ĐỊNH" là "Quy định xử phạt…"; parser bỏ phần này khỏi `units`); người dùng sửa được.
- Giữ giá trị người dùng đã sửa khi nạp lại. Hiện nạp lại cùng file ghi đè `so_hieu`, `loai`, `co_quan` bằng giá trị máy trích, và ghi đè ngày nếu lần mới trích được (`ingest.py`, nhánh UPDATE `documents`). Cần đánh dấu trường đã sửa tay và bỏ qua chúng khi nạp lại (cách đánh dấu: builder quyết).

**2b. Tag và ghi chú**

- `doc_tags(doc_id, tag)`: gắn/bỏ tag ở trình đọc và trang Kho; gắn hàng loạt nhiều văn bản.
- `user_notes(id, doc_id, unit_id, text, created_at, updated_at)`, `unit_id` có thể trống. Đặt tên khác `ghi_chu` (footnote/comment của file gốc) để khỏi lẫn. Ghi chú cho cả văn bản, hoặc cho một đoạn (bôi chọn → "Ghi chú"). Hiện ở lề trình đọc, và trong kết quả khi đoạn có ghi chú. Chữ thường, không định dạng. Ghi chú gắn với đoạn lưu kèm `path` của đơn vị và được gắn lại sau khi nạp lại văn bản (id đơn vị đổi), theo cách `rebuild.snapshot_links`/`restore_links`; không gắn lại được thì chuyển thành ghi chú cấp văn bản, không xoá.
- Ghi chú tìm được bằng FTS riêng (`user_notes_fts`), hiện thành mục "Ghi chú của bạn", không trộn vào xếp hạng văn bản luật.

**2c. @ và # trong ô hỏi**

- Gõ `@` gợi ý văn bản (số hiệu, trích yếu, tên file; khớp cả khi gõ không dấu); gõ `#` gợi ý tag. Chọn xong thành "chip" phạm vi.
- Phạm vi đổi thành danh sách `doc_ids`, đưa vào `_fts_cascade(doc_ids=…)` và `semantic.rerank(…, doc_ids)` (cả hai đã hỗ trợ). Phạm vi lưu theo cuộc trò chuyện (`scope_json`), câu sau dùng tiếp cho tới khi bỏ chip.
- Trình đọc có nút "Hỏi trong văn bản này".
- Không có kết quả trong phạm vi thì nói rõ "Không thấy trong <văn bản>" và gợi ý tìm toàn kho; không tự mở rộng phạm vi mà không báo.

**2d. Hiệu lực dễ thấy**

- Huy hiệu ở mọi trích dẫn, trình đọc, trang Kho: Còn / Hết / Chưa rõ. Thêm hai trạng thái **tính ra lúc hiển thị** (không phải sửa ràng buộc CHECK của `documents.hieu_luc`): "Chưa có hiệu lực" (ngày hiệu lực sau hôm nay) và "Có thể đã bị thay thế" (có `effect_hints` trỏ tới số hiệu này; hiện chỉ bắt được "thay thế Nghị định số …", P4 mở rộng).
- Bấm huy hiệu thì thấy lý do: văn bản nào, Điều nào nói gì, ai xác nhận, ngày nào.
- Duyệt gợi ý thay thế/bãi bỏ ngay trên huy hiệu: "Xác nhận → đặt Hết hiệu lực", một bấm, ghi người và ngày. Chưa có người xác nhận thì không tự đổi.
- Gợi ý đã duyệt phải còn sau khi nạp lại văn bản nguồn. Hiện nạp lại xoá hết `effect_hints` của văn bản đó, kể cả gợi ý đã duyệt (`ingest.py`, `rebuild.py`); làm như liên kết: chụp lại trước, gắn lại sau.

**2e. Chỉ mục cấp văn bản không cần AI**

- Tóm tắt văn bản: nguyên văn Điều 1 (Phạm vi điều chỉnh), thêm Điều 2 (Đối tượng áp dụng) nếu có.
- Từ khoá: 5–8 từ hoặc cụm đặc trưng: đếm trong chữ của chính văn bản, nhân với độ hiếm trên toàn kho (số đơn vị chứa từ, lấy từ `units_vocab`). Bảng này chỉ có âm tiết đơn, nên cụm 2–3 âm tiết phải đếm trực tiếp (builder quyết cách).

**Cổng P2:**

- Hỏi kèm @ đúng văn bản: trên 84 câu văn bản thật, Hit@1 ≥ 95% (phạm vi loại bỏ nhầm lẫn giữa các văn bản).
- Nâng cấp một bản sao kho 0.8 thật (61 nghìn Điều): không mất dữ liệu, không phải nạp hay nhúng lại, chạy ≤ 1 phút.
- Xoá văn bản không để lại units, vector hay dòng FTS mồ côi (có test).
- Nạp lại một văn bản sau khi đã sửa tay số hiệu, trích yếu và gắn ghi chú cấp đoạn: giá trị sửa tay còn nguyên, ghi chú được gắn lại, gợi ý hiệu lực đã duyệt còn (có test).
- Trích yếu đúng ≥ 18/21 văn bản thật (kiểm tay).
- Người dùng thử gắn tag, viết ghi chú, dùng @ mà không cần hướng dẫn.

### P3 — Trợ lý trả lời (4 tuần)

**Giải quyết:** ② ⑥ ⑪.

**Luồng một câu hỏi**

1. Tìm như hiện nay (Advance trên máy 16 GB, theo phạm vi @/# nếu có). Kết quả gọn của P1 hiện ngay.
2. **Chặn sớm:** không có kết quả, hoặc kết quả đầu chỉ khớp theo nghĩa (tầng 7) với điểm thấp, thì trả "Không tìm thấy căn cứ trong kho" kèm gợi ý, **không gọi mô hình**.
3. **Dựng ngữ cảnh:** 3–5 Điều đầu sau reranker. Mỗi Điều cắt còn tên Điều, các khoản/điểm khớp và khoản liền kề; kèm số hiệu, ngày ban hành, hiệu lực, và quan hệ sửa đổi nếu P4 đã có. Trần ~1.000 token để vừa 45 giây (mục 4). Dòng dài (bản OCR dính nhiều khoản/điểm) tách theo câu, câu đầu dòng là câu dẫn đi theo mọi câu được giữ; dòng chọn theo độ hiếm trong Điều của từ câu hỏi (P0 vòng 2: câu trích bằng chứng còn trong đoạn từ 53% lên 80% câu văn bản thật; đưa 3 đoạn thay 5 không thêm gì). Mỗi đoạn mang mã [1]…[5].
4. **Gọi `llama-server` với JSON schema:**

   ```json
   {
     "tien_de_sai": "câu hỏi giả định sai thì chỉ ra, không thì để trống",
     "pham_vi": "đúng | hẹp hơn | khác",
     "du_can_cu": true,
     "tra_loi": "tối đa 3 câu, lời thường",
     "cac_y": [{"y": "…", "nguon": [1, 3]}],
     "luu_y": ["ngoại lệ, điều kiện áp dụng, chỗ các văn bản nói khác nhau"]
   }
   ```

   Thứ tự trường là thứ tự sinh: kiểm tiền đề và phạm vi trước khi đặt cờ (đo ở P0). `nguon` là enum, chỉ gồm các mã đã đưa vào. Mọi chuỗi có trần độ dài và không cho sinh chữ Trung/Nhật/Hàn (grammar).
5. **Kiểm tự động** (mục 5, điều 2–3): bỏ ý có nguồn sai hoặc số liệu không khớp. `tra_loi` chứa số không có trong nguồn, hoặc lẫn chữ Trung, thì thay bằng câu trả lời trích nguyên văn (đoạn đầu). Câu bị cắt ở trần token thì giữ các ý đã viết xong.
6. **Hiển thị:** `pham_vi` là "hẹp hơn" thì câu trả lời mang dải cảnh báo "Chỉ tìm thấy quy định cho trường hợp hẹp hơn câu hỏi", không hiện như câu trả lời đủ căn cứ. Câu trả lời ngắn → các ý có chip [1][2] (bấm là mở trình đọc ở đúng đoạn, P1) → "Căn cứ": trích đoạn nguyên văn lấy từ kho, kèm huy hiệu hiệu lực → "Lưu ý" → các kết quả tìm khác (thu gọn). Không có ký hiệu Markdown nào hiện ra vì app tự dựng HTML từ JSON.
7. Lưu vào cuộc trò chuyện (`answer_json`).

**Chi tiết**

- Mô hình chạy trong tiến trình con `llama-server`, chỉ nghe `127.0.0.1`, cổng ngẫu nhiên, `--api-key` ngẫu nhiên mỗi lần chạy (trang web khác trên máy không gọi được). Khởi động ở câu hỏi AI đầu tiên; tự tắt sau 20 phút không dùng để trả RAM; app tắt thì tắt theo.
- Nhúng vector nền (`jobs.py`) tạm dừng khi đang sinh câu trả lời, để hai việc không tranh CPU. Khi trả lời, mô hình chạy 6 luồng; tối đa 200 token ra (`n_predict`).
- Lúc mở app, gửi một câu hỏi mồi để phần lời nhắc cố định nằm sẵn trong bộ nhớ đệm, câu hỏi thật không phải đọc lại phần đó.
- Chữ hiện dần (SSE): phần `tra_loi` hiện ngay khi đang sinh, có dòng "đang kiểm tra nguồn…" cho tới khi kiểm xong.
- Một mức trả lời, không bật chế độ suy nghĩ (thinking), để vừa 45 giây. Phần phản biện (điều kiện áp dụng, ngoại lệ, văn bản mới/cũ, chỗ mâu thuẫn) nằm trong các trường `luu_y` và `tien_de_sai` của khuôn. Chế độ suy nghĩ hay mô hình lớn hơn chỉ thêm nếu đo thấy vẫn xong trong 45 giây.
- Hỏi tiếp: câu ngắn hoặc thiếu chủ ngữ ("còn mức phạt thì sao?") được mô hình viết lại thành câu đầy đủ dựa trên câu trước. App hiện câu đã viết lại để người dùng thấy máy hiểu thế nào.
- Prompt tiếng Việt, cố định trong mã, có test. Nhiệt độ thấp; giá trị chốt ở P0.
- Không có mô hình hoặc máy không đủ RAM: app chạy như P1, ẩn công tắc AI, Cài đặt báo rõ lý do.
- Chữ do mô hình sinh luôn được escape khi hiển thị.

**Cổng P3** (bộ `bench/llm`, máy chuẩn, Office đang mở)

- Nguồn hợp lệ 100% và số liệu khớp nguồn 100% (bắt buộc bằng bộ kiểm tự động).
- Dẫn đúng Điều không thấp hơn mức đạt ở P0; từ chối đúng ≥ 90% khi đã bỏ Điều đúng khỏi ngữ cảnh; chỉ ra tiền đề sai ≥ 80% trên câu bẫy mức phạt (đều chấm bằng máy, mục 4).
- Trên ≥ 100 câu thật của văn phòng: người dùng chấm "dùng được" ≥ 80% (đánh giá độ hữu ích, không phải chấm pháp lý).
- Trả lời xong ≤ 45 giây tính từ lúc bấm Enter (p95, máy 16 GB, Office đang mở; chủ dự án chốt 29/10/2026); kết quả tìm hiện trước, trong ~5–9 giây. RAM toàn app ≤ 6 GB. Máy thật của người dùng đo lại ở P5 (máy một kênh RAM sinh chữ chậm hơn).
- Tắt AI thì kết quả và độ trễ như P1.

### P4 — Liên kết văn bản kiểu Obsidian, hiệu lực theo Điều (3 tuần)

**Giải quyết:** ⑧ ⑨.

**4a. Trích quan hệ khi nạp** (bằng quy tắc, mở rộng `ingest.suggest_effect_hints` và `links.py`)

| Quan hệ | Dấu hiệu | Ví dụ |
|---|---|---|
| căn cứ | dòng "Căn cứ Luật/Nghị định … số …" ở phần mở đầu (đọc từ `pages.raw_text`; parser không giữ phần này) | Nghị định → Luật |
| hướng dẫn, quy định chi tiết | trích yếu "hướng dẫn …/quy định chi tiết … Nghị định số …" | Thông tư → Nghị định |
| sửa đổi, bổ sung | trích yếu hoặc Điều 1 "sửa đổi, bổ sung … của … số …" | Luật sửa đổi → Luật gốc |
| thay thế, bãi bỏ | có một phần (`effect_hints`): mở rộng ngoài "Nghị định", ghi văn bản đích cho "bãi bỏ", giữ gợi ý đã duyệt khi nạp lại (P2) | |
| dẫn chiếu | "theo quy định tại Điều n … số …" trong thân văn bản; mở rộng từ `links._target_doc`, hiện chỉ chạy cho Điều chế tài | |

- Bảng `doc_relations(src_doc_id, src_unit_id, kind, target_so_hieu, target_doc_id, target_dieu, confirmed)`, thêm hai trục thời gian và đoạn trích nguồn theo mục 4b. `target_doc_id` tự nối khi văn bản đích được nạp sau. Đi đồ thị (backlinks, 1–2 bước) bằng `WITH RECURSIVE` của SQLite; không cần kho đồ thị.
- Nếu cổng P4 cho thấy quy tắc bỏ sót nhiều quan hệ: tuỳ chọn cho LLM đọc **riêng phần mở đầu** của từng văn bản để gợi ý quan hệ vào hàng chờ duyệt (ước tính ~18 giờ CPU chạy nền cho 3.271 văn bản của kho Zalo). Không đọc toàn văn, không tự xác nhận.
- Văn bản được nhắc tới nhưng chưa có trong kho hiện thành nút mờ "chưa có trong kho" (như liên kết chưa tạo của Obsidian), đồng thời là gợi ý nên nạp thêm văn bản nào.

**4b. Sửa đổi theo Điều.** Văn bản sửa đổi ("Sửa đổi, bổ sung Điều 5 như sau: …") làm Điều 5 của văn bản gốc mang nhãn "Đã được sửa đổi bởi Khoản 3 Điều 1 Luật …"; trình đọc mở song song bản cũ và bản sửa. P3 đưa bản sửa vào ngữ cảnh trước bản gốc.

**4c. Giao diện**

- Bảng "Liên quan" trong trình đọc, nhóm theo loại: căn cứ, được hướng dẫn bởi, sửa đổi, bị sửa đổi bởi, thay thế, bị thay thế bởi, dẫn chiếu, được dẫn chiếu bởi. Đây là phần "backlinks".
- Đồ thị cục bộ 1–2 bước (SVG tự vẽ): nút là văn bản, màu theo hiệu lực; cạnh theo loại quan hệ; bấm nút để mở văn bản; lọc theo loại cạnh.
- Ghi chú (P2) có nhắc @văn bản cũng hiện trong "Liên quan", như Obsidian.
- Nhóm riêng "Nội dung tương tự", dựng từ vector sẵn có (mục 4b), ghi rõ không phải quan hệ pháp lý.

**4d. Gợi ý hiệu lực theo quan hệ.** Văn bản B (còn hiệu lực) thay thế A thì A được gợi ý "Hết hiệu lực"; quan hệ sửa đổi thì gợi ý ở cấp Điều. Người xác nhận bằng một bấm (2d).

**Cổng P4:**

- Gán nhãn tay quan hệ trên 21 văn bản thật và các văn bản chúng nhắc tới: trích quan hệ đúng ≥ 95%, đủ ≥ 85%.
- Các Điều bị sửa đổi trong ba luật sửa đổi của bộ văn bản thật được gắn nhãn đúng ≥ 90%.
- Đồ thị cục bộ ≤ 200 nút hiện trong ≤ 1 giây.

### P5 — Chuyên nghiệp, chỉn chu, phát hành (2 tuần)

- **Cửa sổ app:** bỏ cửa sổ đen (PyInstaller `console=False`); mở bằng Edge chế độ app (`msedge --app=<url>`; Edge có sẵn trên Windows 10/11, không có thì dùng trình duyệt mặc định) để trông như một phần mềm riêng. Thêm nút "Thoát Soi Luật" trong Cài đặt (hoặc biểu tượng ở khay hệ thống) để tắt hẳn. Hướng dẫn hiện phải dặn "đừng tắt cửa sổ đen"; bỏ được câu đó.
- **Lần đầu mở app:** màn chào 3 bước (nạp văn bản → hỏi thử → mở đoạn); câu hỏi mẫu lấy từ chính kho.
- **Thống nhất giao diện:** một bộ token màu và chữ (đã có `_style.html`). Mọi màn có trạng thái trống, đang tải, lỗi viết bằng lời thường. Kiểm tra độ tương phản, thao tác bằng bàn phím, trình đọc màn hình (`aria-live` cho câu trả lời đang hiện).
- **Xuất Word câu trả lời và căn cứ** (báo cáo tra cứu có ngày, nguồn, hiệu lực), mở rộng `export_word.py`.
- **Đóng gói:** bộ cài chính giữ ~840 MB. **Gói AI** riêng (`llama-server` + GGUF Qwen3-VL-4B Q4_K_M, ~2,5 GB) cài vào `models\llm\`; hoặc gộp thành một bộ cài ~3,3 GB (mục 9). `build.ps1` kiểm SHA-256 mô hình; NOTICE và giấy phép Apache-2.0/MIT đi kèm, như hai mô hình hiện tại.
- **Chữ ký số** cho bộ cài để hết cảnh báo SmartScreen (cần mua chứng thư, mục 9).
- **Nghiệm thu** trên máy Windows sạch 16 GB, Office và trình duyệt đang mở: cài → nạp 21 văn bản thật → hỏi 20 câu → mở đoạn → gắn tag, ghi chú → xuất Word → sao lưu, khôi phục → gỡ cài. 0 kết nối ngoài `127.0.0.1`. Gộp `HUONG-DAN.md` và `HUONG-DAN-DON-GIAN.md` thành một hướng dẫn mới cho bản 1.0 (chủ dự án chốt 29/10/2026: hai file giữ nguyên tới P5 vì giao diện còn đổi); cập nhật `TAI-LIEU-KY-THUAT.md`.

**Cổng P5:** nghiệm thu trên đạt hết; 5 người dùng thật dùng một tuần, không có lỗi chặn việc, điểm hài lòng ≥ 4/5.

### Nhánh song song — Độ chính xác tìm kiếm

Câu trả lời AI chỉ đúng khi đoạn đúng nằm trong 5 đoạn đưa vào mô hình. Hiện Hit@5 của Advance khoảng 90% (Zalo 90,4%, tư vấn thật 89,8%): đó là trần độ đúng của P3.

0. **Hợp BM25 với vector làm tụt hạng 1 trên văn bản thật** (đo ở P0, 30/10/2026; `bench/van-ban-that/KET-QUA.md`). Trên 84 câu của 21 văn bản 2026, Hit@1 là 83,3% với Normal, 67,9% với BM25 + vector (chưa reranker), 72,6% với Advance đủ bước. Ở @10 Advance hơn 1 câu trên 84 (97,6% so với 96,4%). Các hệ số hợp (`semantic.TOP`, `DENSE_K`, `RRF_K`, `W = 2`) được chọn trên kho Zalo 61 nghìn Điều, có thể không hợp kho nhỏ gồm văn bản mới. Việc cần thử: giảm `W`, chỉ cho vector chen vào sau top-k của BM25, hoặc chỉ dùng reranker. Đo theo quy tắc giữ ở mục 5 (điều 7): phải không tụt trên Zalo và gold. Làm trước các mục dưới, vì nó quyết định chế độ mặc định (mục 2, điều 8).
1. **Gộp Điều tương đương khi đo:** dùng chung khoá băm với phần gộp trùng của P1. Tài liệu kỹ thuật ước tính trần Hit@1 ~86–87% vì cùng nội dung nằm ở nhiều văn bản.
2. **Điều dài:** mô hình nhúng chỉ đọc 128 token đầu (`semantic.MAXLEN`), nên Điều dài bị tụt hạng (văn bản thật, đo với mô hình nhúng trước đó cũng cắt 128 token: các Điều đúng bị tụt dài trung vị 1.399 token). Thử nhúng thêm theo khoản rồi lấy điểm cao nhất cho Điều, hoặc tăng `MAXLEN` lên 256/512. Máy 16 GB đủ RAM cho ma trận lớn hơn; nhúng lại chạy nền. Số vector vượt ~125 nghìn thì làm theo ngưỡng ở mục 4b.
3. **Reranker nhiều luồng hơn (giúp vừa ngân sách 45 giây):** phần tìm Advance hiện ~9 giây ở 2 luồng, trong đó reranker ~5 giây; giây nào bớt được ở đây là thêm cho mô hình trả lời. Đo reranker ở 4–6 luồng trước. Reranker top-10 (đã đo +0,5–1,8 điểm Hit@1 nhưng chậm gấp đôi) chỉ thử nếu vẫn trong ngân sách.
4. **Chỉnh `SURE_GAP`** trên lượt mở trích dẫn thật, ghi đúng câu hỏi từ P1, như `TAI-LIEU-KY-THUAT.md` mục 11 đã đề ra. `query_log.selected_unit` hiện có không đủ tin cậy vì luôn ghi vào dòng mới nhất.
5. **Lưu toạ độ chữ khi nạp:** OCR giữ thêm toạ độ từ `image_to_data` vào `pages.bbox_json`, kèm dpi, góc khử nghiêng và góc xoay để quy đổi sang ảnh `/page`; PDF có lớp chữ lấy toạ độ từ pdfplumber. Dùng cho khung tô trên ảnh trang và ảnh cắt đoạn gốc (①). Kho đã nạp: tính khi mở trang lần đầu, lưu vào `page_regions`.
6. **Từ điển viết tắt và đồng nghĩa:** lấy từ trang "Truy vấn bỏ sót", người duyệt.
7. **Phụ lục:** nội dung sau khối nơi nhận không vào `units` (cờ `in_sign` trong `parse.py` chỉ tắt khi gặp Điều mới), nên không tìm được. Ví dụ: câu "bốc xếp thủ công vật nặng" của 27/2026 nằm ở phụ lục và không ra trong top 10. Nạp phần này thành đơn vị cấp đoạn mang nhãn "Phụ lục".

**Cổng:** mỗi thay đổi theo quy tắc giữ ở mục 5 (điều 7); Advance p95 ≤ 10 giây. Mục tiêu, không phải điều kiện của P3: Hit@5 Advance ≥ 92% trên cả Zalo và gold (hiện ~90%).

---

## 7. Thay đổi dữ liệu

| Thay đổi | Phase | Ghi chú |
|---|---|---|
| Bảng `conversations`, `messages` | P1 | Bảng mới |
| Cột `documents.trich_yeu` | P2 | `init_schema` đang chạy lại `schema.sql` ở mỗi request, nên thêm cột phải qua một hàm nâng cấp riêng, chạy một lần, đánh dấu bằng `app_meta.schema_version` |
| Bảng `doc_tags`, `user_notes`, `user_notes_fts` | P2 | Bảng mới |
| Đánh dấu trường `documents` đã sửa tay | P2 | Để nạp lại không ghi đè; cách làm do builder quyết |
| Chụp và gắn lại ghi chú cấp đoạn, gợi ý hiệu lực đã duyệt khi nạp lại | P2 | Theo mẫu `rebuild.snapshot_links` / `restore_links` |
| Bảng `doc_relations` | P4 | Bảng mới, có hai trục thời gian (hiệu lực; ghi nhận–xác nhận) và cột nguồn (mục 4b); `effect_hints` giữ nguyên |
| Vector | nhánh chính xác | Lược đồ `unit_vectors` (float16) không đổi; chỉ đổi cách nạp vào RAM khi vượt ngưỡng ở mục 4b |
| `pages.bbox_json`, `page_regions` | nhánh chính xác | Cột và bảng đã có, bắt đầu dùng; lưu kèm dpi và góc xoay của ảnh OCR |
| Không đổi CHECK của `documents.hieu_luc` | P2 | Trạng thái mới tính ra lúc hiển thị. SQLite không sửa được CHECK nếu không dựng lại bảng |

Nguyên tắc: chỉ thêm, không xoá hay đổi cột; tự sao lưu trước lần nâng cấp đầu; có test nâng cấp trên bản sao DB 0.8.

---

## 8. Thứ tự

- Đường chính: P0 → P1 → P2 → P3 → P5.
- P4 làm sau P2 (cần trích yếu và trình đọc); có người thứ hai thì làm song song với P3.
- Nhánh độ chính xác xen kẽ; nên xong mục 1–3 trước cổng P3, nhưng đó không phải điều kiện cứng. Riêng mục 3 (reranker nhiều luồng) ảnh hưởng trực tiếp tới việc P3 có vừa 45 giây không, nên làm sớm.
- Mỗi phase kết thúc bằng một bản chạy được giao người dùng thử (0.9, 0.10, …), không dồn tới cuối.
- Sau khi lộ trình được duyệt: mỗi phase có kế hoạch triển khai chi tiết riêng (việc nhỏ, file cụ thể, test trước) trước khi viết mã.

---

## 9. Quyết định của chủ dự án

**Đã chốt (29/10/2026)**

- **Thời gian chờ:** câu trả lời AI xong trong ≤ 45 giây, tính từ lúc bấm Enter tới khi câu trả lời xong (không phải tới khi chữ đầu hiện). Ban đầu chốt 30 giây, nâng lên 45 giây cùng ngày.
- **Chấm chất lượng:** không có người chấm pháp lý. Chọn mô hình theo benchmark công khai, rồi kiểm trên kho bằng máy chấm có đáp án sẵn (mục 4, P0).
- **Máy đo:** có máy 16 GB.

**Còn mở**, xếp theo mức chặn việc:

1. **Người thử và nhân lực:** ai là 3–5 người thử ở P0–P2 và 5 người dùng một tuần ở P5? Có người làm thứ hai không (có thì khoảng 12 tuần thay vì 16)?
2. **Máy 8 GB còn phải hỗ trợ không.** Đề xuất: còn, nhưng chỉ chế độ tìm (không AI); AI yêu cầu 16 GB. Câu trả lời quyết định có phải thử trên hai loại máy không.
3. **≥ 100 câu hỏi thật kèm Điều đúng từ văn phòng**, cần trước cổng P3 (đã hỏi từ 0.8, chưa có).
4. **Gói AI tách riêng hay gộp vào bộ cài.** Đề xuất tách: máy không cần AI thì không phải tải.
5. **Có mua chứng thư ký số cho bộ cài không** (để bỏ cảnh báo "Windows protected your PC").
6. **Ai duyệt hiệu lực và quan hệ văn bản, bao nhiêu giờ mỗi tuần** (đã hỏi từ 0.8, chưa có câu trả lời).
7. **Có cần đồ thị toàn kho không:** quyết sau khi dùng đồ thị cục bộ ở P4.
8. **Chế độ tìm mặc định trên máy 16 GB: Normal hay Advance.** Đề xuất (theo số đo P0): giữ Normal cho tới khi nhánh độ chính xác (điều 0) đưa Advance lên không thấp hơn Normal ở Hit@1 trên văn bản thật. Phần trả lời AI (P3) vẫn dùng được với Normal: ngữ cảnh là 5 Điều đầu.
9. **Duyệt mẫu giao diện** (`mau/giao-dien-1.0.html`): cổng P0, cần trước khi viết mã P1.
10. **Cách tính cổng P0 cho câu trả lời AI** (`bench/llm/KET-QUA.md`, vòng 2). (a) JSON: tính câu bị cắt ở trần token mà app cứu được các ý đã viết xong, hay chỉ tính JSON đọc được ngay. Lưu ý: 15/20 câu Qwen bị cắt, sau khi cứu không còn ý nào có nguồn (chỉ còn câu trả lời và tiền đề sai). Đề xuất: chỉ tính câu đã cứu còn ít nhất một ý có nguồn, và sửa việc câu bẫy chạm trần trước. (b) Từ chối: chỉ tính `du_can_cu = false`, hay tính cả câu trả lời gắn `pham_vi` "hẹp hơn" kèm dải cảnh báo trên giao diện (đề xuất: tính cả, vì trên train biến thể này ít khẳng định sai nhất: 5/12 so với 7/12 và 8/12 ở Zalo; cách tính không đổi số khẳng định sai, chỉ đổi cách đọc cổng).

---

## 10. Không làm

- Fine-tune hay huấn luyện mô hình; dùng GPU; dịch vụ đám mây; tự cập nhật qua mạng.
- Dùng LLM để lập chỉ mục hay tóm tắt cả văn bản, chạy nền (mục 2, điều 2 và 7). Ngoại lệ có điều kiện duy nhất: đọc phần mở đầu để gợi ý quan hệ chờ duyệt (P4).
- Framework đồ thị tri thức dựng bằng LLM (Cognee, Graphiti, LightRAG, GraphRAG…); kho vector hay kho đồ thị thứ hai cạnh SQLite (mục 4b).
- Tự kết luận hiệu lực khi chưa có người xác nhận; tự sửa văn bản gốc.
- Giao diện sửa ranh giới Điều, sửa chữ OCR (giữ quyết định của kế hoạch 0.8: sửa file nguồn rồi nạp lại).
- Thay Tesseract bằng bộ OCR khác (chỉ xét lại nếu bộ đo cho thấy OCR là nguyên nhân sai).
- Nhiều người dùng, đăng nhập, đồng bộ giữa các máy.
- SPA, Node, Electron.
