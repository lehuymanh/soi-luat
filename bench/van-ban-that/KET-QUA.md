# Thử trên văn bản quy phạm thật (22/10/2026)

**Bộ thử:** 21 văn bản ban hành tháng 9–10/2026, tải từ datafiles.chinhphu.vn (danh sách và đường dẫn trong `manifest.json`; PDF không lưu trong repo).
- Gồm 9 Luật, 6 Nghị định, 5 Thông tư và 1 Quyết định, tổng 443 trang.
- 18 file là **bản scan không có lớp chữ**, 3 file có lớp chữ.

**Câu hỏi:** 84 câu, 4 câu cho mỗi văn bản (2 câu từ khoá, 2 câu hỏi đời thường), lưu trong `queries.json`. Đáp án gồm Điều, trang và câu trích nguyên văn. Một agent đọc thẳng ảnh scan để lập đáp án, một agent khác kiểm lại.

Chạy lại:

```text
:: tải PDF vào bench\van-ban-that\files\ theo manifest.json (cần header Referer: https://vanban.chinhphu.vn/)
python bench\van-ban-that\import_real.py bench\van-ban-that     :: nạp vào bench\van-ban-that\data (OCR)
python bench\van-ban-that\dump_audit.py bench\van-ban-that      :: độ đúng OCR trên 84 câu trích
python bench\van-ban-that\eval_real.py bench\van-ban-that normal
python -m soiluat.importer --nhung   (SOILUAT_DATA=bench\van-ban-that\data)  rồi  eval_real.py ... advance
```

## Nạp

| | |
|---|---|
| 21 file, 443 trang | 637 s |
| Trang scan (Tesseract vie, 300 DPI) | 371 trang / 628 s = **1,69 s/trang** (file 86 trang: 143 s) |
| File có lớp chữ | 72 trang / 8,6 s = 0,12 s/trang |
| Nhúng (Advance, 2 luồng, 128 token) | 501 Điều / 150 s = 3,3 Điều/s |

**Độ đúng OCR:** so 84 câu trích (chép tay từ ảnh) với chữ OCR của đúng trang đó. Độ giống ký tự trung bình 98,5%, trung vị 100%, chỉ 2/84 câu dưới 90%. Độ tin cậy OCR trung bình theo Tesseract là 88,7. Như vậy OCR không phải chỗ yếu; chỗ yếu là bước tách cấu trúc và siêu dữ liệu (xem bên dưới).

## Tìm kiếm (84 câu, hạng = vị trí thẻ như người dùng thấy)

- *Rộng*: thẻ cùng file, và hoặc đúng Điều, hoặc trang của thẻ chứa câu trích.
- *Chặt*: phải đúng số Điều.

| | Normal (BM25) | Advance (BM25 + EmbeddingGemma) |
|---|---|---|
| Rộng Hit@1 / @3 / @5 / @10 | **76,2** / 89,3 / 91,7 / 95,2% | 65,5 / 89,3 / **94,0** / 95,2% |
| Chặt Hit@1 / @3 / @5 / @10 | 65,5 / 75,0 / 77,4 / 81,0% | 58,3 / 73,8 / 81,0 / 81,0% |
| Câu từ khoá, rộng @1 / @5 | 78,6 / 92,9% | 69,0 / 95,2% |
| Câu hỏi đời thường, rộng @1 / @5 | 73,8 / 90,5% | 61,9 / 92,9% |
| Thẻ đầu tiên đúng file | 92,9% | 90,5% |
| Độ trễ p50 / p95 (trong process) | 1050 / 1796 ms | 1525 / 2542 ms |

- **Rộng cao hơn chặt khoảng 14 điểm** vì thẻ thường trỏ đúng chỗ nhưng mang sai số Điều: phần tách cấu trúc gộp nhiều Điều vào một Điều (xem dưới).
- **Advance làm tụt hạng 1 trên văn bản thật:** 13 câu tụt khỏi hạng 1, chỉ 4 câu lên hạng 1. Ngược lại, Hit@5 tăng 2,3 điểm.
  - Các Điều đúng bị tụt dài trung vị **1.399 token**, các Điều giữ được hạng 1 dài trung vị 536 token. Mô hình chỉ nhúng 128 token đầu mỗi Điều, nên câu trả lời nằm sâu trong Điều dài thì phần ngữ nghĩa không thấy.
  - Lỗi gộp Điều làm Điều dài thêm, nên càng hại Advance.
  - Khuyến nghị: giữ Normal làm mặc định, sửa phần tách cấu trúc trước rồi đo lại Advance.
- **Độ trễ không giảm khi kho nhỏ:** 21 văn bản vẫn mất ~1 s/câu. Nguyên nhân tìm ra sau đó (xem "Sau khi sửa"): nhánh F2 cho trang OCR chưa đối chiếu lọc bằng `f.rowid IN (SELECT value FROM json_each(?))`, SQLite chạy lại cả truy vấn FTS cho từng id.
- **Nguyên nhân 38 câu không ở hạng 1** (agent phân tích, agent khác phản biện): tách cấu trúc 15, xếp hạng BM25 10, xếp lại theo nghĩa 9, lỗi OCR 3, nằm trong phụ lục ngoài Điều 1.

## Cấu trúc và siêu dữ liệu

Agent đối chiếu từng file với bản scan, rồi một agent thứ hai cố bác bỏ từng kết luận.

**Điều:** văn bản thật có 344 Điều (không tính Điều được trích trong luật sửa đổi). Chương trình tách được 267, trong đó **đúng 249 (72%)**. 11/21 file đúng từ 90% trở lên. Ba file tệ nhất:
- 18/2026/QH16: 19/66
- 385/2026/NĐ-CP: 11/39
- 384/2026/NĐ-CP: 6/12

**Siêu dữ liệu đúng trên 21 file:**

| Trường | Đúng |
|---|---|
| Loại | 20/21 |
| Ngày hiệu lực | 15/21 |
| Số hiệu | 12/21 |
| Ngày ban hành | 9/21 |
| Cơ quan | 6/21 |

## Lỗi tìm thấy (đã xác minh trên scan và code), xếp theo ảnh hưởng

1. **Một dấu ngoặc kép lạc làm mất nhận diện Điều đến hết văn bản.**
   - Cơ chế: `parse._quote_state` bật/tắt theo mọi “ ” " xuất hiện trên dòng. Khi cờ đang bật, `_parse_lines` dồn mọi dòng vào khoản hiện tại.
   - Tesseract hay chèn ngoặc lạc giữa chữ.
   - Hậu quả: 18/2026 mất 43 Điều, 384 mất 5, 388 mất 2. Điều 1 của các luật sửa đổi 17, 21, 22 bị chia thành đoạn.
   - Cách sửa: chỉ coi “ là mở trích dẫn khi nó ở đầu dòng hoặc dòng trước kết thúc bằng "như sau:"; bỏ qua ngoặc nằm giữa chữ; đặt lại trạng thái khi gặp tiêu đề "Điều N." chuẩn.
2. **PDF có lớp chữ: bộ dò bảng nhận nhầm văn bản căn đều thành bảng.**
   - Dòng tiêu đề thành `| Điều 15. … |`, mọi regex `^Điều` trượt (385/2026 mất 24/39 Điều).
   - Cách sửa: bóc hàng chỉ có một ô trước khi tách.
3. **Tiêu đề Điều có ký tự rác đầu dòng** (ˆ ‹ Ă) hoặc bị OCR đọc thành "Đ1eu", "Đlgu", "Điều M".
   - Các Điều này bị gộp vào Điều trước: 18/2026 Điều 21, 34, 60; 391 Điều 50; 389 Điều 12; 89 Điều 20.
4. **Dòng tiếp theo của một điểm bị nối vào khoản cha**, không nối vào điểm (gặp ở mọi văn bản). Thẻ Điểm chỉ còn dòng đầu, khoản thành một mớ lộn thứ tự.
5. **Khoản đánh "1," (dấu phẩy do OCR) không được nhận** là khoản.
6. **Không cắt "Nơi nhận" và phụ lục.** Điều kiện cắt yêu cầu dòng chữ ký ≤20 ký tự, nên phụ lục và mẫu biểu bị gộp vào Điều cuối. Riêng 388/2026 sinh thêm 8 Điều trùng từ các mẫu Quyết định trong phụ lục.
7. **Số hiệu:**
   - `SO_LINE` chỉ nhận dòng bắt đầu bằng "Số", nên bỏ sót "Luật số:".
   - Không chịu dấu cách trước "/", nên trượt "388 /2026" và "61      /2026".
   - Vì `IGNORECASE`, nó khớp nhầm dòng căn cứ bị ngắt ("số 28/2023/QH15…").
   - Khi trượt, chương trình lấy số hiệu đầu tiên trong văn bản, tức là luật được trích dẫn.
   - Số viết tay hoặc nằm trong ô chữ ký số (154, 26, 61, 89, 27) không đọc được; phải duyệt tay.
8. **Cơ quan ban hành:** tìm trên cả văn bản thay vì phần đầu; thiếu QUỐC HỘI và THỦ TƯỚNG CHÍNH PHỦ; hai cột tiêu đề bị gộp thành một dòng.
9. **Ngày tháng:**
   - Ngày ban hành của Luật nằm ở câu kết "thông qua ngày …", ngoài 40 dòng đầu mà code đọc.
   - Ngày viết tay bị OCR đọc thành "ÁS tháng 40".
   - `HIEU_LUC_RE` không chịu các biến thể OCR như "thị hành", "kê từ".
10. **`struct_score` che lỗi:** 22/2026 được 0,99 điểm dù mất Điều 1.

## Sau khi sửa lỗi 1, 2, 7 (23/10/2026)

Sửa trong `parse.py` / `extract.py` / `search.py`, thử lại trên đúng 21 văn bản và 84 câu trên (nạp lại bằng OCR, nhúng lại, đo lại). Test mới: `tests/test_van_ban_that.py` (10 test; cả bộ 209 pass).

| Sửa | Nội dung |
|---|---|
| 1 | `_quote_state`: khối trích dẫn chỉ mở bằng ngoặc đầu dòng hoặc ngay sau ":"; ngoặc kẹp giữa chữ bị bỏ qua. Nếu ngoặc đóng bị OCR làm mất, dòng "Điều n+1." đúng thứ tự của văn bản đóng khối (trừ khi nối tiếp Điều đang được trích) |
| 2 | `_real_table`: bỏ "bảng" là khung tô nền (≥70% hàng chỉ một ô) hoặc chữ căn đều bị chia mỗi chữ một ô |
| 7 | `SO_LINE` nhận "Luật số:", "Nghị quyết số:"…, dấu cách trước "/"; phân biệt hoa thường để dòng căn cứ ngắt "số 40/2019/QH14." không bị nhận |
| thêm | `_score`: khoản đánh lại từ 1 giữa chừng (tiêu đề Điều bị mộc đè) không còn kéo cả văn bản về chia đoạn (Luật 19/2026) |
| thêm | `scored_units`: `+f.rowid IN (…json_each…)` (nhánh F2 của kho OCR: 744 ms → 3 ms/câu, kết quả y hệt) |

| | Trước | Sau |
|---|---|---|
| Điều tách đúng số (đếm thô, chưa xét trang) | 259 / 344 (75%) | **335 / 344 (97%)** |
| Số hiệu đúng | 12 / 21 | 16 / 21 |
| Normal, rộng Hit@1 / @3 / @5 / @10 | 76,2 / 89,3 / 91,7 / 95,2% | **81,0 / 92,9 / 96,4 / 96,4%** |
| Normal, chặt (đúng số Điều) | 65,5 / 75,0 / 77,4 / 81,0% | **79,8 / 92,9 / 96,4 / 96,4%** |
| Advance, rộng | 65,5 / 89,3 / 94,0 / 95,2% | 73,8 / 95,2 / 97,6 / 97,6% |
| Advance, chặt | 58,3 / 73,8 / 81,0 / 81,0% | 71,4 / 94,0 / 97,6 / 97,6% |
| Độ trễ p50 / p95 Normal | 1050 / 1796 ms | **370 / 494 ms** |
| Độ trễ p50 / p95 Advance | 1525 / 2542 ms | 725 / 958 ms |

Còn sai:
- 9 Điều chưa tách: 18/2026 (3 Điều), mỗi file 1 Điều ở 19/2026, 155, 26, 389, 391 và 89. Chưa kiểm từng Điều; theo phân tích lần đầu, nguyên nhân thường là OCR đọc hỏng chữ "Điều" hoặc số ("Đ1eu", "Điều M") hoặc ký tự rác đầu dòng (lỗi 3, chưa sửa).
- 5 số hiệu: 154, 26, 27, 61, 89. Số hiệu viết tay hoặc nằm trong ô chữ ký số, chương trình không đọc được, vẫn phải duyệt tay.
- Ngày ban hành, cơ quan ban hành vẫn sai như bảng trên (lỗi 8, 9 chưa sửa).
- Advance vẫn kém Normal ở hạng 1 (73,8 so với 81,0%) và hơn ở hạng 5 (97,6 so với 96,4%).

**Lưu ý khi đọc:**
- Bộ 84 câu là bộ tôi dùng để tìm lỗi, chưa được giữ riêng làm tập kiểm: số "sau" có thể cao hơn thực tế trên văn bản lạ.
- Chưa chạy lại bộ Zalo. Bản sửa `scored_units` chỉ chạy khi kho có trang OCR; kho Zalo toàn văn bản có chữ nên không đi qua nhánh đó.
- Khối trích dẫn nhiều Điều mà Điều trích có số bằng số Điều của văn bản + 1 và ngoặc đóng bị mất thì vẫn bị nuốt (giống code cũ).

## Sau khi sửa lỗi 3, 8, 9 (23/10/2026)

Nạp lại 21 văn bản bằng OCR, tính lại ngày/cơ quan từ chữ OCR đã lưu sau lần chỉnh cuối, nhúng lại, đo lại. Test mới thêm vào `tests/test_van_ban_that.py` (nay 14 test; cả bộ 213 pass). Kiểm siêu dữ liệu bằng `sieu_du_lieu.py` (giá trị thật đọc trên scan; chạy trên kho cũ cho đúng số kiểm lần đầu: loại 20, ngày ban hành 9, hiệu lực 15, cơ quan 6).

| Sửa | Nội dung |
|---|---|
| 3 | `_dieu_match`: bỏ ký tự rác đầu dòng ("ˆ Điều 21.", "‹ Điều 60.", "ĂĐỉều 50.", "\| Điều 15. … \|"); nhận "Đ1eu 12.", "Đlgu 20." (cần số và dấu . hoặc :); "Điều M Thẩm quyền…" (số bị đọc thành chữ cái) suy số từ Điều trước (số Điều trước + 1) |
| 8 | `infer_co_quan`: chỉ xét 14 dòng đầu, bỏ phần "CỘNG HÒA XÃ HỘI…" dính cùng dòng và dấu `\|` của hàng bảng, thêm QUỐC HỘI / ỦY BAN THƯỜNG VỤ QUỐC HỘI / CHỦ TỊCH NƯỚC / THỦ TƯỚNG CHÍNH PHỦ; "QUÓỐC HỘI" do OCR được chuẩn hóa về "QUỐC HỘI" |
| 9 | `find_ngay_ban_hanh`: Luật/Nghị quyết lấy ngày ở câu kết "… Kỳ họp … thông qua ngày …" (cần "Kỳ họp" ngay trước; "Căn cứ … Quốc hội thông qua ngày …" không tính). `HIEU_LUC_RE` cho phép tối đa 3 từ lạ giữa "có hiệu lực" và "từ ngày" ("thi bành", "thị hành", "kê từ") và ưu tiên câu "Luật này có hiệu lực…" hơn đoạn trích của luật khác |

| | Trước (sau sửa 1, 2, 7) | Sau |
|---|---|---|
| Điều tách đúng số | 335 / 344 (97%) | **341 / 344 (99%)** |
| Cơ quan ban hành đúng | 6 / 21 | **21 / 21** |
| Ngày hiệu lực đúng | 15 / 21 | 19 / 21 |
| Ngày ban hành đúng | 9 / 21 | 14 / 21 |
| Số hiệu đúng | 16 / 21 | 16 / 21 |
| Normal rộng @1 / @3 / @5 / @10 | 81,0 / 92,9 / 96,4 / 96,4% | 82,1 / 92,9 / 96,4 / 96,4% |
| Normal chặt @1 | 79,8% | 81,0% |
| Advance rộng @1 / @3 / @5 / @10 | 73,8 / 95,2 / 97,6 / 97,6% | 75,0 / 96,4 / 96,4 / 96,4% |
| Độ trễ p50 / p95 Normal, Advance | 370 / 494, 725 / 958 ms | 336 / 401, 650 / 747 ms |

Chênh lệch giữa hai lần đo tìm kiếm chỉ cỡ một câu (1 câu = 1,2 điểm) nên nằm trong nhiễu. Cải thiện thật là ở dữ liệu (Điều, cơ quan, ngày), vì bộ lọc "Cơ quan ban hành" và "Hiệu lực" dùng chúng.

Còn sai:
- 3 Điều chưa tách: 155/2026 (1), 19/2026 (1), 26/2026 (1).
- 5 số hiệu: 154, 26, 27, 61, 89 (viết tay hoặc trong ô chữ ký số).
- 7 ngày ban hành: ngày viết tay (154, 26, 27, 61, 89), Luật 18/2026 (câu kết bị OCR bỏ mất) và Luật 19/2026 (năm bị OCR đọc hỏng).
- Ngày hiệu lực của 19/2026 và 89/2026; loại của 18/2026 (dòng "LUẬT -" có dấu gạch).
- 3 câu không vào top 10: 391 Điều 60 (câu hỏi chung "Chủ tịch UBND xã … vi phạm về đặt cược"), 27/2026 phụ lục ("bốc xếp thủ công vật nặng", file không xuất hiện), 24/2026 ("khí cười N2O" chỉ có trong văn bản là "N2O").
- Advance vẫn tụt hạng 1 ở 12 câu và lên hạng 1 ở 6 câu so với Normal.

Phương pháp: ngày/cơ quan sau cùng được tính lại từ chữ OCR đã lưu bằng đúng ba hàm của luồng nạp (không OCR lại lần nữa); Điều, trang, nhúng và tìm kiếm là từ lần nạp OCR đầy đủ trước đó với cùng mã tách.

## Ghi chú viết tự do và ứng viên từ vector (23/10/2026)

Câu hỏi: văn bản không theo thể thức Điều/khoản (ghi chú kinh nghiệm) có tìm được không? Ghi chú rơi vào nhánh "đoạn" (không cấu trúc), BM25 vẫn tìm bình thường **nếu câu hỏi chung chữ**. Thử khó hơn: 6 ghi chú tự viết, mỗi cái cùng chủ đề với một văn bản thật trong kho (389 xổ số, 390 vàng, 391 cá độ, 89 học bạ, 22 xuất khẩu lao động, 27 giàn giáo), câu hỏi được kiểm bằng máy là **không trùng âm tiết nào** với ghi chú (kể cả bỏ dấu).

Trước: Normal và Advance đều không ra ghi chú nào (0/6): BM25 không có chữ để khớp, Advance chỉ xếp lại 20 Điều BM25 đã tìm. Tìm thuần vector trên toàn kho thì ghi chú hạng 1 ở 4/6 câu (hạng 3, 6 ở hai câu còn lại).

Sửa (`semantic.rerank`, `DENSE_K = 20`): ở Advance thêm 20 Điều gần nghĩa nhất toàn kho (trong văn bản đang tra nếu có số hiệu). **Chỉ thêm, không xáo**: 20 Điều đầu BM25 giữ đúng điểm như cũ; Điều thêm có hạng theo nghĩa tính trên toàn kho, có ở BM25 sau hạng 20 thì cộng hạng đó, không có thì chỉ có điểm theo nghĩa (≤ 1/6 nên không vượt hạng 1). Bản đầu tính chung hạng theo nghĩa cho cả hai nhóm làm thứ tự top 20 bị xáo: rộng @1 tụt 73,8 → 69,0%, nên đổi sang cách trên.

| Advance, kho 21 văn bản + 6 ghi chú | Chỉ xếp lại (cũ) | + 20 Điều từ vector |
|---|---|---|
| 84 câu: rộng @1 / @3 / @5 / @10 | 73,8 / 96,4 / 96,4 / 96,4% | 73,8 / 96,4 / **97,6 / 97,6%** |
| 84 câu: chặt @1 | 71,4% | 71,4% |
| Ghi chú tìm ra (6 câu không chung chữ) | 0 / 6 | **6 / 6** (hạng 7, 8, 8, 8, 15, 21) |
| Văn bản cùng chủ đề hạng 1 | 5 / 6 | 5 / 6 (27/2026 giàn giáo: không ra → hạng 33) |
| Số thẻ trung bình | 39,2 | 48,8 |
| Độ trễ p50 / p95 | 662 / 758 ms | 667 / 762 ms |

Câu đổi hạng trong 84 câu: 24/2026 "khí cười N2O" 22 → **5**; 27/2026 "bốc xếp thủ công vật nặng" không ra → 12; 391 Điều 60 22 → 30 (đều ngoài top 10 trước và sau). Normal không đổi (không gọi vector).

Hạn chế: ghi chú và câu hỏi do người đo tự viết, chỉ 6 câu; ghi chú tìm ra nhưng ở hạng 7–21, chưa phải đầu. Trên bộ Zalo (788 câu, kho nhúng đủ 61 nghìn Điều): Hit@1/3/5 không đổi, Hit@10 91,9 → 92,5%; xem `bench/zalo/KET-QUA.md`.

Sau đó thêm ngưỡng cosine 0,50 cho Điều thêm từ vector (câu vô nghĩa không còn nhận 20 thẻ bịa; lý do và số đo ở `bench/zalo/KET-QUA.md`). Đo lại trên kho này: 84 câu y như bảng trên (rộng 73,8 / 96,4 / 97,6 / 97,6%), số thẻ trung bình 48,8 → 40,5; ghi chú tìm ra **5 / 6** (hạng 7, 8, 8, 8, 21) — ghi chú học bạ (cosine < 0,50) không còn, và 27/2026 với câu giàn giáo lại không ra. Xuất Word thẻ "tìm theo nghĩa": tạo file bình thường; Word không ghi mức khớp của thẻ nào (kể cả đồng nghĩa), chỉ nội dung quy định. Kịch bản: `realtools/notes_exp2.py`, `run_k.py` trong scratchpad của phiên đo (không đưa vào dự án).

## Mốc P0 của lộ trình 1.0: Advance AITeamVN trên văn bản thật (30/10/2026)

Lộ trình 1.0 (P0 bước 3) cần mốc của bản Advance hiện tại (AITeamVN embedding + reranker top-5) trên 84 câu này, vì cổng P1 so với nó. Chưa lần đo nào trước đây dùng bản này: các bảng ở trên là Advance với mô hình nhúng cũ.

**Kho:** dựng lại từ 21 PDF theo `manifest.json` trên máy ảo Linux (Tesseract 5.3.4, gói `vie` của Ubuntu), mã nguồn hiện tại. Kết quả: 21/21 file nạp được; 321/344 Điều khớp theo `cau_truc.py` (thấp hơn bản chuẩn trên Windows, 341/344, chủ yếu do 391/2026 chỉ khớp 49/65 Điều, nghi do bộ chữ `vie` khác bản). Mô hình xuất bằng `pack/export_models.py`, nhúng 327 Điều gốc. Normal và Advance đo trên **cùng kho này**, nên so sánh giữa hai chế độ là hợp lệ. Normal ở đây gần như trùng lần đo 23/10 (rộng @1 83,3% so với 82,1%).

| 84 câu | Rộng @1 / @3 / @5 / @10 | Chặt @1 / @10 | Từ khoá @1 | Câu hỏi @1 | Đúng file ở hạng 1 | Thẻ TB |
|---|---|---|---|---|---|---|
| Normal (BM25) | **83,3** / 94,0 / 96,4 / 96,4 | **78,6** / 94,0 | **90,5** | **76,2** | **94,0** | 39,5 |
| BM25 + vector, không reranker | 67,9 / 89,3 / 95,2 / 97,6 | 63,1 / 95,2 | 71,4 | 64,3 | 85,7 | 40,1 |
| **Advance** (BM25 + vector + reranker top-5) | 72,6 / 90,5 / 95,2 / **97,6** | 69,0 / **95,2** | 76,2 | 69,0 | 89,3 | 40,1 |

Kết luận cho lộ trình:
- **Trên văn bản thật, Advance làm tụt hạng 1 khoảng 10 điểm so với Normal**, dù hơn ở @10 (thêm 1 câu). Bước gây tụt là **hợp BM25 với vector** (−15 điểm @1); reranker gỡ lại được ~5 điểm. Cùng chiều với các lần đo bằng mô hình nhúng cũ ở trên (Advance 73,8–75,0% so với Normal 81–82%). Trên Zalo và gold, Advance hơn Normal rõ (`bench/zalo/KET-QUA.md`), nên hệ số hợp (`semantic.TOP`, `DENSE_K`, `RRF_K`, `W = 2`) chọn trên kho lớn 61 nghìn Điều có thể không hợp kho nhỏ, văn bản mới. Lộ trình mục 2 (điều 8) đề xuất để Advance làm mặc định trên máy 16 GB; mốc này cho thấy cần sửa phần hợp trước (nhánh độ chính xác, đo theo quy tắc ở lộ trình mục 5, điều 7) hoặc giữ Normal làm mặc định.
- **Số thẻ trung bình ~40 mỗi câu** ở cả hai chế độ: đây là mốc "số mục hiện sẵn" mà cổng P1 hạ xuống ≤ 5.
- Độ trễ đo ở lần này không dùng được: máy ảo 4 nhân đang chạy song song mô hình sinh câu trả lời.


## P1 K3: đo theo mục hiển thị (31/10/2026)

84 câu, Normal, bản sao kho dựng ở P0 (chưa dựng lại sau sửa parser N1a); `python -I bench/van-ban-that/eval_real.py <realdocs> normal`. Theo mục (bản đại diện, cách tính của cổng P1) và kèm "Cũng có ở" đều bằng theo thẻ: rộng 83,3 / 94,0 / 96,4 / 96,4, chặt 78,6 / 89,3 / 92,9 / 94,0 (@1 / @3 / @5 / @10), vì 21 văn bản không có Điều nào trùng nội dung (0 mục gộp). 39,5 mục mỗi câu, 5 mục hiện sẵn. Cổng P1: đạt.

Mở trình đọc (`python -I bench/doc_open.py <data Zalo>`, bản sao Zalo 3.271 văn bản, văn bản nhiều đơn vị nhất và 100 văn bản ngẫu nhiên, TestClient): p50 14 ms, p95 27 ms, văn bản lớn nhất (2.823 đơn vị, HTML 1,6 MB) 121 ms. Cổng ≤ 1 giây đạt ở phía máy chủ; thời gian trình duyệt vẽ trang 1,6 MB chưa đo (bấm tay ở Z1).
