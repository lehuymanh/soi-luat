# Kế hoạch triển khai P1 (bản 0.9): mở đúng đoạn, kết quả gọn, lịch sử chat

Lập 31/10/2026 trên mã `bc9f9af` (HEAD hiện là `05e127b`, chỉ thêm tài liệu và script bench; `src/`, `tests/`, `pack/` không đổi). Một người làm. Đọc cùng `soi-luat-lo-trinh-1.0.md` (P1 :219-258, quy tắc 7 :190, mục 7 :428-442, mục 8 :446-453) và mẫu (chờ duyệt) `mau/giao-dien-1.0.html`.
Số có chữ "(khảo sát)" lấy từ bản đồ mã của người đọc trước, chưa chạy lại. Số khác đã chạy lại ngày 31/10 trên bản sao chỉ đọc. Mọi số tìm kiếm ghi kèm bộ và số câu (n).

## 0. Tóm tắt

- **Tổng: 15,75 ngày mã + 2,25 ngày đệm + 2 ngày thử với người dùng = 20 ngày làm việc (4 tuần).** Lộ trình ghi 3 tuần; lý do ở mục 7, thay đổi lộ trình ở mục 8.
- Thứ tự: chỉ mục khoá ngoại (cũng sửa lỗi xoá chậm của bản 0.8) → nền (parser, nâng cấp dữ liệu, `static/`) → 1a trình đọc → 1b kết quả gọn → 1c lịch sử chat. Cuối mỗi tuần có một bản chạy được.
- Việc lộ trình chưa ghi mà P1 buộc phải làm: bốn chỉ mục (N0); sửa parser điểm nhiều dòng (N1a) và nâng cấp dữ liệu một lần (N1b); lưu tham chiếu kết quả kèm băm chữ; bảng `citation_opens`.
- Hai chỗ lệch chữ của quy tắc 7 cần chủ dự án duyệt bằng văn bản, không làm lặng lẽ (mục 2b).

## 1. Cần chốt

**Trước ngày 1 (chặn việc):**
1. **Chủ dự án duyệt mẫu giao diện** (mẫu chờ duyệt, lộ trình mục 9 điều 9 :475). Chưa duyệt thì chưa viết mã P1 (mục 8 của lộ trình). Trước khi duyệt, sửa ba chỗ mẫu cho khớp bản sẽ làm: "Xem thêm" mở từng 10 mục (mẫu `:696`, bộ xử lý `:1092` đang mở hết một lần); bỏ khung tô vàng trên ảnh trang (mẫu `:900-904`, lộ trình để nhánh chính xác); thêm mục "Mở toàn văn" cho truy vấn chỉ có số hiệu.
2. **Một máy Windows** để dựng và thử gói PyInstaller (Z0). Chưa có PyInstaller ở môi trường soạn nên chưa ai biết `static/` có vào gói không.
3. **Kho đo còn dùng được** (Zalo, văn bản thật). Bản sao đo ở phiên soạn nằm trong `/tmp`, sẽ mất; dựng lại theo `GHI-NHO-NGHIEN-CUU.md` mục 4 (Zalo: `bench/zalo/build_db.py`; văn bản thật: `bench/van-ban-that/import_real.py`, cần Tesseract có `vie`). Làm trước ngày 1; không làm thì N1a, K3, B1 không đo được.

**Chốt trong quá trình** (mặc định đề xuất đã ghi, làm theo mặc định nếu chưa có trả lời):

| # | Câu hỏi | Mặc định | Hạn |
|---|---|---|---|
| 1 | Ngoại lệ quy tắc 7 cho bản sửa parser (mục 2b). | Giữ nếu Zalo và gold không thấp hơn; cần duyệt. Không duyệt thì gỡ 5 dòng, bỏ N1b, trình đọc ghi chú "điểm nhiều dòng có thể bị cắt, xem Bản gốc". | Cuối ngày 2 |
| 2 | Cổng "Hit theo mục": tính chỉ đại diện hay cả bản trùng (mục 2b). | Văn bản thật: chỉ đại diện. Zalo, gold: cả bản trùng. | Trước ngày 9 |
| 3 | "Xem thêm" mở từng 10 mục, tối đa 25 (lộ trình :234), không mở hết một lần như mẫu. | Từng 10, tối đa 25. | Cùng lúc duyệt mẫu |
| 4 | Bỏ khối chế tài khỏi danh sách (mẫu không có khối này). | Bỏ. Nhưng thẻ hạng 1-2 lấy chế tài từ Điều khác (`cards.py:413`, `:468`), phần trích từ chính Điều không thay được. Phụ lục A việc 1 kiểm điều này; thiếu thì thêm lại `c.sample` cho hạng 1-2 (3 dòng). | Ngày 19 |
| 5 | Truy vấn chỉ có số hiệu: một mục "Mở toàn văn" mỗi văn bản (K1). Mất tick từng Điều để xuất Word từ danh sách này; xuất bằng cách gõ "số hiệu + Điều n". | Chấp nhận. | Trước ngày 7 |
| 6 | Ai là 3-5 người thử. Lộ trình mục 9 điều 1 chưa có trả lời. | Cần tên. | Trước ngày 15 |
| 7 | 4 tuần thay vì 3, hay cắt (mục 7 cuối). | 4 tuần. | Trước ngày 1 |

Phím tắt cuộc trò chuyện mới: `Alt+N` (Ctrl+N/T/W trang web không chặn được; chưa thử trên Edge/Chrome Windows). Đổi nếu người thử không dùng được.

## 2. Mục tiêu và cổng

Giải quyết ① ③ ④ ⑦. Hai tiêu chí chung: số đo ghi nhãn bộ và n; chạy một mình trên máy rảnh (`ps aux --sort=-%cpu | head`), không song song với việc dựng lại. Độ trễ ghi tên máy.

| Cổng P1 (lộ trình :251-258) | Cách đo | Tự động? |
|---|---|---|
| Bấm trích dẫn: trình đọc mở đúng văn bản, đơn vị, đoạn tô, ≤ 1 giây với kho 61 nghìn Điều. | (a) test: văn bản tổng hợp 3.000 đơn vị dựng < 1,0 s. (b) `bench/doc_open.py` (mới, ~20 dòng): TestClient trên bản sao Zalo, doc 1274 (2.692 đơn vị) + 100 văn bản ngẫu nhiên, p95 theo "hạng gần nhất" `sorted[int(n*0,95)]`; khảo sát: 190-237 ms cho doc 1274. (c) bấm tay 5 lần trên máy người dùng. | (a), (b) tự động; (c) tay |
| Hit@1/@5 tính theo mục hiển thị không thấp hơn mốc hiện có trên Zalo, gold và văn bản thật. | `bench/zalo/eval.py` (Zalo test 788 câu; gold `vle` 500 câu, `bench/gold/README.md:10`) và `bench/van-ban-that/eval_real.py` (84 câu), Normal (`semantic.py:88-90`), đặt `SOILUAT_SEMANTIC=0`. Mốc = số theo thẻ (`hien_tai`) trên cùng bản dựng. Cách tính "theo mục": mục 2b. | Tự động, chạy nền (~1,6 s/câu, khảo sát: Zalo ~21 phút, gold ~13 phút) |
| Số mục hiện sẵn ≤ 5 (từ ~40). | Test đếm mục không ẩn trong HTML; `eval_real.py` thêm `hien_san = min(5, so_muc)`. Gộp trùng gần như không giảm số mục (khảo sát: Zalo ~2%, văn bản thật 0/84 câu); số 5 do mức cắt quyết định. | Tự động |
| Mở lại cuộc cũ hiện đúng kết quả, không chạy lại tìm kiếm. | Test: thay `cascade_search` bằng hàm ném lỗi, `GET /c/{id}` vẫn ra đủ mục. | Tự động + xem tay |
| 3-5 người dùng thật làm 8 việc, ≥ 90% làm được không cần hướng dẫn. | Phụ lục A. | Tay |
| `pytest` xanh, có test mới cho neo và tô đúng đơn vị, gộp trùng, thêm/sửa/xoá cuộc trò chuyện, CSRF. | `python -m pytest -q`. Hôm nay: 258 xanh, 7 bị bỏ qua (thiếu win32com, Tesseract, fitz, mô hình thật). Test mới không dùng fitz. | Tự động |

### 2b. Hai chỗ lệch chữ của quy tắc 7 (chủ dự án duyệt)

Quy tắc 7 (:190): giữ khi "tốt hơn trên cả Zalo lẫn gold và không tụt trên văn bản thật".

**Ngoại lệ 1: bản sửa parser (N1a) làm Hit@3 văn bản thật tụt.** Tôi chạy lại ngày 31/10 (văn bản thật, n = 84, Normal, bản sao), trước → sau, @1/@3/@5/@10: rộng 83,3/94,0/96,4/96,4 → 84,5/91,7/96,4/96,4; chặt 78,6/89,3/92,9/94,0 → 79,8/88,1/92,9/94,0. @3 mất 2 câu (hạng 3 → 4, vẫn trong top 5), @1 được 1 câu; phép kiểm dấu (2 mất, 0 được) cho p = 0,5, tức không phân biệt được với nhiễu, nhưng theo chữ quy tắc 7 vẫn là "tụt". Số thẻ mỗi câu 39,5 → 45,9. Lợi ích: khoảng 795 → 113 trong 1.097 điểm không còn bị cắt giữa câu (tôi đếm lại; khảo sát 860 → 121). Đây là sửa đúng cho trình đọc, không phải cải thiện xếp hạng. Zalo test và gold chưa đo.
Đề xuất: giữ nếu Zalo và gold không thấp hơn (sẽ chỉ "bằng", không "tốt hơn") và chủ dự án chấp nhận ngoại lệ với bằng chứng trên. Quyết định cuối ngày 2.

**Ngoại lệ 2: "Hit theo mục" cần một định nghĩa.** Mục đại diện của nhóm trùng có thể không phải bản mà câu trả lời đúng nằm. Hai cách tính, báo cả hai ở mọi bộ:

| Bộ | n | Có ngày để chọn đại diện? | Cổng đề xuất | Báo thêm |
|---|---|---|---|---|
| Văn bản thật | 84 | 13/21 văn bản có ngày ban hành | chỉ đại diện | cả bản trùng |
| Zalo test | 788 | 3/3.271 văn bản; tất cả hiệu lực "chưa rõ" | cả bản trùng | chỉ đại diện (chẩn đoán) |
| gold `vle` | 500 | như Zalo (cùng kho) | cả bản trùng | chỉ đại diện (chẩn đoán) |

Khảo sát (100 câu Zalo, chưa chạy lại): chỉ đại diện thì @5 83 → 79, @10 89 → 85; cả bản trùng không tụt. Lý do đề xuất: kho Zalo không có ngày nên đại diện gần như tuỳ ý, và người dùng vẫn mở được bản trùng qua "Cũng có ở". Mặt yếu: cổng Zalo/gold nhẹ hơn. Chủ dự án có thể chọn "chỉ đại diện" cho cả ba bộ và chấp nhận phần tụt.

**Việc kèm theo: chạy lại `bench/llm`.** Bản sửa parser đổi chữ đưa vào mô hình (`semantic.root_lines` dùng cho `answer.build_context`), còn mốc P0 đo trên parser cũ và mã trước `bc9f9af`. Quy tắc 7 câu cuối buộc đo lại. Lịch ở B1 (chạy nền, không nằm trên đường găng).

## 3. Việc cần làm, theo thứ tự

Mỗi việc: file và hàm, test viết trước, ngày. Số dòng là của mã hiện tại (`bc9f9af`).

### Nhóm N: nền (tuần 1)
#### N0. Bốn chỉ mục khoá ngoại (0,25 ngày), làm đầu tiên
- Khoá ngoại là cột trỏ sang bảng khác. Xoá một dòng ở bảng gốc thì SQLite phải tìm các dòng con trỏ tới nó; không có chỉ mục (như mục lục của cột) thì nó quét cả bảng. Bốn cột thiếu chỉ mục: `units.fine_source_unit` (`schema.sql:70`), `page_regions.unit_id` (`:88`), `query_log.selected_unit` (`:160`), `effect_hints.source_unit_id` (`:178`). `EXPLAIN QUERY PLAN` ra `SCAN` cho cả bốn (chỉ mục hiện có: `:187-194`).
- Tôi đo trên bản sao kho Zalo (428.874 đơn vị, 3.271 văn bản): xoá văn bản 89 đơn vị mất **41,5 s** khi chưa có chỉ mục, **0,01 s** khi có; tạo bốn chỉ mục mất 0,37 s. Bản 0.8 đang chậm như vậy mỗi khi nạp lại file (`ingest.py:317`) hay duyệt trang OCR (`rebuild.py:96`, `:132-145`). Không có chỉ mục này thì N1b ước 50 giờ cho kho Zalo.
- Sửa: bốn dòng `CREATE INDEX IF NOT EXISTS` sau `schema.sql:194`. `init_schema` chạy lại file này mỗi lần mở kết nối (`db.py:49-64`), nên kho cũ tự có chỉ mục lần mở đầu.
- Test trước: `tests/test_schema_index.py`: với mỗi cặp (bảng, cột), `EXPLAIN QUERY PLAN SELECT 1 FROM <bảng> WHERE <cột> = 1` phải chứa `INDEX`, không `SCAN`. Dựng DB từ `tests/fixtures/schema_08.sql` (lưu `git show HEAD:src/soiluat/schema.sql` trước khi sửa), chạy `init_schema`, chỉ mục xuất hiện (dùng lại ở H1). Kiểm đo: xoá rồi rollback văn bản 89 đơn vị trên bản sao Zalo, phải ≤ 1 s.

#### N1a. Sửa parser: dòng nối của điểm (0,75 ngày)
- `_parse_lines` không có biến "điểm hiện tại": dòng thứ 2 trở đi của một điểm bị nối vào khoản cha (`add_line`, `parse.py:282-289`), điểm chỉ giữ dòng đầu.
- Sửa 5 chỗ (khớp diff bản vá thử): khai báo `current_diem = None` sau `:263`; `add_line` dùng `current_diem or current_khoan or current_dieu` (`:283`); Điều mới đặt `current_khoan = current_diem = None` (`:335`); khoản mới đặt `current_diem = None` trước `:378`; điểm mới gán `current_diem = new_unit(` (`:389`).
- Test trước: `tests/test_parse.py::test_diem_nhieu_dong` (khoản chỉ còn câu dẫn; điểm a, b giữ đủ dòng; điểm sau không nuốt dòng điểm trước; khoản không có điểm không đổi).
- Đo: hai bản dựng cùng máy, cùng mã tìm. Văn bản thật đã có (mục 2b). Còn: Zalo test 788 và gold 500 trên bản sao Zalo chưa dựng lại (mốc) và đã dựng lại bằng `rebuild_if_changed` (N1b); chạy nền từ cuối ngày 1. Quyết giữ hay gỡ cuối ngày 2; đây là một quyết định giữ/gỡ, không chỉnh thêm tham số trên các bộ này.
- Tác động kèm theo (đo trên 21 văn bản thật): 1.242/2.610 đơn vị đổi chữ, 16/21 văn bản đổi; liên kết 73 → 121 (thêm 48 gợi ý máy vào `/review`, không mất liên kết nào, không có liên kết đã duyệt để thử); nhãn `CHE_TAI` 187 → 173; gợi ý hiệu lực 6 → 5. Ghi vào ghi chú phát hành: sau nâng cấp hàng chờ duyệt dài hơn.

#### N1b. Nâng cấp dữ liệu, bản nhỏ (0,75 ngày; bỏ nếu parser bị từ chối)
Chỉ dựng lại văn bản mà parse lại khác với đơn vị đang lưu, chạy trong luồng `soiluat-jobs` có sẵn.
- `rebuild.rebuild_if_changed(conn, doc_id) -> bool` (~12 dòng): bỏ qua văn bản `fallback_doan = 1` (người dùng có thể ép chia đoạn lúc nạp, `ingest.py:285`, `:355`; cột không phân biệt "ép" với "parse hỏng", và `rebuild_document` gọi `parse_pages` không có `force_doan`, `rebuild.py:89`, nên sẽ chuyển ngược về Điều). Parse như `rebuild.py:84-90`, so `{path: (level, raw_text)}` của đơn vị khác `ghi_chu` với dữ liệu lưu. Khác thì `rebuild_document`; giống thì không đụng gì (giữ vector, nhãn, liên kết).
- Giữ gợi ý hiệu lực đã duyệt (3 dòng): `rebuild.py:97` thành `DELETE ... AND confirmed = 0`; `suggest_effect_hints` (`ingest.py:174-198`) bỏ qua bộ (doc, kind, target) đã có (so `target_so_hieu IS ?` để NULL so được). Sửa luôn đường duyệt trang OCR (`set_page_reviewed`). Đường nạp lại file đổi nội dung (`ingest.py:318`) giữ nguyên, P2 lo (lộ trình mục 7).
- `jobs.py`: thêm `self.migrate = {"running", "done", "total"}` cạnh `self.embed` (`:50`); `_migrate_chunk(conn)` gọi trong `_run` sau hàng đợi nạp, trước `_embed_chunk` (`:146-166`), mỗi lần một văn bản nên nạp file xen vào được; `snapshot` (`:100-125`) trả thêm `migrate` và `active` tính cả nó; nút "Nạp file" hiện "Nâng cấp x/y" như "Nhúng x%" (`index.html:349`). `main()` thêm `JOBS.wake()` sau `get_conn()` (`app.py:805`) để luồng chạy ngay.
- Lần đầu (`app_meta.parse_rev` khác `PARSE_REV = '2'`): kho có văn bản thì sao lưu một lần bằng `db.backup_db` (`db.py:96-106`) ra `data/backup/soiluat-truoc-0.9.db`, không ghi đè nếu đã có; sao lưu lỗi (đĩa đầy) thì không dựng lại, thử lại lần mở sau. Duyệt hết mới ghi `parse_rev`; mở lại giữa chừng chỉ kiểm lại (văn bản đã dựng so ra giống nên bỏ qua). Văn bản bị khoá ghi (`OperationalError` sau 5 s, `db.py:22`): bỏ qua, không ghi `parse_rev`, thử lại lần sau; luồng không được chết im như `_warm_models` (`app.py:774-782`). Xong thì `self._todo = None` để nhúng lại Điều mất vector (chỉ Advance). Kho trống: ghi cờ ngay, không sao lưu. Quy tắc để lại: đổi đầu ra parser thì tăng `PARSE_REV` (ghi vào `TAI-LIEU-KY-THUAT.md`).
- Đo: 21 văn bản thật dựng lại 9,1 s (người soát đo, gồm khởi động Python). Zalo chưa đo với chỉ mục: đo ở ngày 1 bằng chính hàm này (vòng lặp qua mọi `doc_id`) rồi ghi vào bảng cổng. Zalo có 2.784/3.271 văn bản có điểm nên bộ lọc "khác mới dựng" ít tiết kiệm ở đó; số văn bản đổi sẽ biết khi đo.
- Rủi ro đã tính: bản chạy thứ hai (cổng 8001, `pick_port` `app.py:767`) cùng kho; trong lúc nâng cấp, cuộc trò chuyện vừa lưu mang băm chữ cũ nên có thể bị báo "nguồn đã thay đổi"; ở Advance mỗi văn bản dựng lại làm đổi khoá `_all_vectors` (`semantic.py:217-227`) nên tìm đồng thời phải nạp lại ma trận vector (tạm chậm; Normal không ảnh hưởng).
- Test trước (`tests/test_rebuild_all.py`): sửa tay `raw_text` một đơn vị cho lệch, `rebuild_if_changed` trả True và chữ trở lại; văn bản không đổi giữ nguyên id đơn vị; bỏ qua `fallback_doan = 1`; gợi ý `confirmed = 1` còn sau `rebuild_document` và không bị nhân đôi; luồng: có file sao lưu, `parse_rev` ghi sau cùng, chạy lần hai không làm gì, kho trống không sao lưu, văn bản bị khoá thì không ghi `parse_rev`.

#### N2. Tách JS/CSS ra `static/` (0,75 ngày)
- `static/app.css` (từ `index.html:7-122`) và `static/app.js` (từ `:261-448`); `_style.html` giữ như cũ (10 template include nó).
- `app.py:40-45`: mount `/static` bằng lớp con `StaticFiles` thêm `Cache-Control: no-cache` (đã thử: mặc định chỉ có ETag và Last-Modified, trình duyệt có thể dùng `app.js` cũ sau nâng cấp). Thêm `mimetypes.add_type("text/javascript", ".js")` và `".css"` (Windows đọc MIME từ registry, máy lỗi trả `text/plain`).
- Thư mục `static/` phải có thật: thiếu thì `StaticFiles` ném `RuntimeError` lúc import và app không chạy (đã thử). Test Linux không bắt được lỗi gói thiếu thư mục, nên có Z0.
- Thay `{{ csrf_token | tojson }}`, `{{ suffixes... | tojson }}` (`index.html:263-264`) bằng `data-csrf`, `data-suffixes` trên `<body>`. Giữ id `btn-import`, `btn-settings`, `composer` (`tests/test_d_app.py:205`).
- **`post()` chịu được khởi động lại app:** token CSRF đổi mỗi lần chạy (`app.py:42`), tab mở sẵn sẽ bị 403. `_check_csrf` (`:82-88`) đòi cả cookie lẫn header bằng token mới, nên chỉ đọc `document.cookie` lúc gửi không đủ (cookie cũ chỉ đổi khi có một phản hồi bất kỳ, `HostGuard` `:64-76`). Cách làm: gặp 403 thì `fetch("/api/status")` một lần (để nhận cookie mới), đọc lại cookie, gửi lại đúng một lần. Dùng cho mọi POST trong `app.js` (hiện ở `index.html:267`, `:391`, `:409`, `:419`) và POST mới.
- `pyproject.toml:36`: thêm `static/*` vào `package-data`. `pack/SoiLuat.spec:11` dùng `collect_data_files` nên tự lấy; thêm đoạn kiểm tường minh như đoạn seed `:12-15`.
- Test trước: `tests/test_static.py` (GET `/static/app.js` ra 200, kiểu `javascript`, có `Cache-Control: no-cache`; Host sai ra 400; `index.html` không còn `tojson`); `tests/test_pack_spec.py:7-14` thêm `static`. Hợp đồng phía máy chủ cho `post()`: đổi `app.CSRF_TOKEN` bằng `monkeypatch`, POST token cũ ra 403, GET rồi POST token mới ra 200 (xem H6).

### Nhóm 1a: trình đọc
#### R1. `src/soiluat/reader.py` (1,25 ngày)
Một truy vấn `SELECT ... FROM units WHERE doc_id = ? ORDER BY id` (chỉ mục `idx_units_doc`, `schema.sql:188`); id trong văn bản liền nhau và đúng thứ tự (khảo sát).
- `resolve_sel(conn, doc_id, u, path)`: tìm theo `path` trước (`UNIQUE(doc_id, path)` `schema.sql:73`), chỉ dùng `u` khi `units.doc_id == doc_id`. `units.id` là `INTEGER PRIMARY KEY` không AUTOINCREMENT (`:48`) nên id bị tái dùng sau xoá.
- `build_view(...)`: mỗi dòng có `id`, độ thụt (đếm đoạn của `path`), nhãn `1.` hay `a)` bỏ hậu tố `~n` (`semantic._marker` `:158-161` giữ `~n`, không dùng thẳng), lớp `sel` / `sel-in` (đơn vị chọn và con, theo `parent_id`), ghi chú `ghi_chu` dưới đơn vị cha. Chữ: `reviewed_text or raw_text` (`cards.py:97-98`); thân Điều là `raw_text[len(title):].strip()` (322/322 Điều thật, 61.141/61.141 Điều Zalo bắt đầu bằng tên; 287 Điều Zalo tên rỗng, nên không tách theo dòng đầu). `white-space: normal`, `pre-line` chỉ cho `from_table` (mẫu `:249` dùng `pre-line` cho mọi đơn vị; PDF ngắt dòng cứng).
- Mục lục: một dòng mỗi Điều, nhãn `fold.pretty_path` (`fold.py:103-120`). Không có Chương/Mục (parser không lưu, `parse.py:38`). Văn bản không cấu trúc (`fallback_doan = 1`): mục lục theo trang (`page_from`), vẫn có neo.
- Tô từ: `answer._words` đổi tên `query_words` (`answer.py:98-99`; dùng ở `:120`, `:122`, `:131`; `cards.py:204` có `_words` riêng, không đụng). Bỏ qua khi `query.classify_query(q) == "so_hieu"` (`query.py:159-172`). Luật dấu theo `query._eq` (`:90-92`): gõ có dấu so `search_accent`, gõ không dấu so `fold_search`. Quét `re.finditer(r"\w+")` như `answer._window` (`:132`); mọi chữ qua `markupsafe.escape` rồi bọc `<mark>` (chữ OCR không đáng tin). Chỉ tô trong đơn vị chọn và con của nó (tô cả văn bản dài ra hàng trăm chỗ và tốn 147-377 ms ở văn bản lớn nhất; khảo sát).
- `cite(doc, path)`: "Điểm a Khoản 1 Điều 5 Nghị định 15/2020/NĐ-CP" theo `fold._PATH_RE` (`:94-96`) và bảng mã loại (`index.html:168`). Chưa có hàm nào ra thứ tự này.
- Test trước (`tests/test_reader.py`): neo `u{id}` đúng thứ tự; điểm nhiều dòng đọc đúng (phụ thuộc N1a; bị từ chối thì bỏ ca này); `?path=` thắng `?u=` cũ, `?u=` của văn bản khác bị bỏ; "muc phat" tô "mức phạt", "phạt" không tô "phat"; `<script>` được thoát; truy vấn số hiệu không tô; `D9.K2~4` ra nhãn `2.`, Điều trùng số hiện "(lần n)"; Điều tên rỗng không mất chữ; ghi chú dưới đơn vị cha; `fallback_doan` có mục lục trang; `cite()` đủ dạng; 3.000 đơn vị dựng < 1,0 s.

#### R2. Route `/doc`, template, ngăn kéo (1,75 ngày: R2a 1,0 ở tuần 1; R2b 0,75 ở tuần 2)
- **R2a:** `GET /doc/{doc_id}` nhận `u`, `path`, `q`, `page`; trả `doc.html` (đủ trang) hoặc `_reader.html` (chỉ thân) khi có header `HX-Request` (như `app.py:204`). Không ghi DB; không có văn bản thì 404 như `app.py:527`.
- `/unit/{id}` (`app.py:521-562`) thành 303 sang `/doc/{doc_id}?path=…&u={id}#u{id}`; xoá `_unit_notes` (`:584-602`) và câu `UPDATE query_log` (`:537-545`); `unit.html` xoá; sửa `review_docs.html:42` và `unit.html:25` (link tới `/unit`). `query_log.selected_*` không nơi nào đọc ngoài test (`tests/test_v07.py:337-346`, `tests/test_review_queue.py:83-99`), cột giữ nguyên, bỏ ghi là an toàn (H5 ghi thay).
- `doc.html`: đầu trang (loại + số hiệu, huy hiệu hiệu lực, cơ quan, ngày; trích yếu "Chưa có trích yếu" vì cột chờ P2), thanh trích dẫn, tab Văn bản | Bản gốc, mục lục + thân, "Chi tiết kỹ thuật" thu gọn (chép từ `unit.html:13-20`, `:28-36`). Hiện **tên file cạnh nút "Sao chép trích dẫn"** và liên kết "Số hiệu sai? Sửa ở trang Văn bản" tới `/review/docs#d{id}` (thêm `id="d{{id}}"` vào `review_docs.html:14`): số hiệu đã sửa được ngay qua `POST /docs/{id}/so-hieu` (`app.py:500-518`, `review_docs.html:33-38`, test `tests/test_review_queue.py:45-51`); khảo sát: sai ở 5/21 văn bản thật (ví dụ `154_2026_TT-BTC.pdf` mang số 80/2019/TT-BTC).
- **Phần ngoài Điều (lộ trình :226):** parser bỏ phần mở đầu, khối sau "Nơi nhận" (`in_sign` bật ở `parse.py:365-367`, bỏ dòng ở `:357-358`, tắt ở `:333`) và phụ lục. Bản nhỏ nhất của P1: nếu không có ảnh trang (docx, txt, Zalo, hoặc file gốc mất), "Chi tiết kỹ thuật" có mục thu gọn "Nguyên văn trang N" (`<pre>` từ `pages.raw_text`, ~10 dòng). Văn bản PDF/ảnh đã có tab Bản gốc. Chèn đúng chỗ trong thân là sửa parser lần hai nên sang P2 (mục 8). `shortcut:` chép thẳng vào HTML, văn bản lớn nhất (548.000 ký tự) thêm ~0,5 MB; chậm thì nạp khi mở `<details>`.
- **R2b:** `app.js` bắt bấm `a[data-doc]`, `fetch` với `HX-Request`, đưa vào `<aside id="reader">`, rồi cuộn tới `#u{sel}` bằng JS (HTML chèn bằng `innerHTML` không tự cuộn theo neo, `index.html:293`; `block: center`, đơn vị cao hơn khung nhìn thì cuộn tới `<mark>` đầu); bấm mục lục thì cuộn; sao chép bằng `navigator.clipboard`; nút toàn màn hình đổi một lớp CSS; Esc đóng. CSS lấy từ mẫu `:217-290`, `:101-103`, `:373-380`.
- Sửa test (`tests/test_d_app.py:294-312`: theo chuyển hướng, `/doc` có ghi chú và hai ngày; `tests/test_e_gaps.py:156`: cần `<img src="/page/{did}/1">` trong HTML (R3), test bị bỏ qua ở đây vì thiếu fitz; `tests/test_review_queue.py:41-44`: `nd15`, `15/2020` ở "Chi tiết kỹ thuật" và đầu trang). Test trước: `/unit` ra 303; `/doc` 404; mảnh không có `<html>`; `/doc` không ghi `query_log`; "Nguyên văn trang 1" có với `.txt`, không có với PDF còn file gốc.

#### R3. Tab "Bản gốc", gồm TIFF/BMP (0,75 ngày)
- Tab chỉ hiện khi `pageimg.can_view` và `pageimg.source_file` đều đúng (`pageimg.py:15-24`; `can_view` chỉ xét đuôi). Bộ chuyển trang theo `pages.page_no`, bắt đầu ở `page_from`; `<img loading="lazy" src="/page/{doc}/{n}">` dựng sẵn cho trang đầu. `file#vbN` dùng được (`source_file` bỏ `#vbN`).
- **TIFF/BMP:** `VIEWABLE` (`pageimg.py:11`) thêm `.tif`, `.tiff`, `.bmp`; hàm mới `render_image_page(src, page_no)` (~8 dòng): Pillow mở, `seek(page_no - 1)` (bộ nạp đã hỗ trợ TIFF nhiều trang, `extract.py:831`, `ocr.py:210`), đổi RGB, ghi PNG vào `BytesIO`; thiếu Pillow thì trả None (404). `page_image` (`app.py:565-581`) gọi nó; PNG/JPG đơn: trang khác 1 thì 404 (hiện phục vụ mọi số trang, `:581`). Đã thử Pillow 13.0.0: TIFF 3 trang, BMP, và PDF 1 trang tạo bằng Pillow đều chạy; `pageimg` dùng pypdfium2 (`:43`, đã cài), không cần fitz.
- Test trước: tab ẩn với `.txt`; hiện với `.png`; `/page/{id}/2` của PNG đơn ra 404; TIFF 3 trang: trang 2 ra PNG, trang 4 ra 404; BMP ra PNG; PDF tạo bằng Pillow ra PNG.

### Nhóm 1b: kết quả gọn
#### K1. Gộp, trích, cắt (2,0 ngày)
- Tách `_search_ctx` (`app.py:116-192`) làm đầu tiên, test cũ phải xanh: `_search(conn, q, loai, co_quan, hieu_luc)` trả kết quả đã lọc (gồm `ids` sau lọc và cắt); `_ctx(conn, q, ...)` dựng `assemble_cards` → `compact` → `summarize` → `_card_dates`. `_search_ctx` = `_search` + `_ctx` + `_log_query` (giữ nguyên `INSERT query_log` `:164-171`, `n` là số thẻ trước gộp; trang "Truy vấn bỏ sót" lọc `result_count = 0`, `:605-613`). H3 mở lại dùng đúng `_ctx`.
- `answer.py`: thêm `SNIP_CHARS = 250` và `snippet(conn, root_id, query, budget) -> (head, text)`: `semantic.root_lines` (`:164-178`) → bỏ dòng rỗng → `_pick` (`:144-201`) → nối dòng bằng khoảng trắng (văn bản OCR: 53-55% mục có dòng < 20 ký tự, khảo sát) → bỏ dòng đầu nếu trùng tên Điều. Đúng khuôn `build_context` (`:226-244`).
- `cards.py`: `Card` (`:26-52`) thêm trường có mặc định `doc_id`, `path`, `head`, `snippet`, `also_in`; gán `doc_id`, `path` từ `primary` (`:410`, `:457-489`). Không đổi `title`, `duty_text`, `sanction_text`, thứ tự sắp (`:495-505`): `tests/test_c_search.py:210`, `export_word.py:34` dùng `title`; `/export` dựng thẻ từ `uid` (`app.py:723-739`) nên Word không đổi.
- `compact(conn, cards, query, limit=25)`: lấy `cards[:DIEU_CAP]` (`search.py:285`, = 100; bộ luật 600 Điều tốn ~1,2 s chỉ cho băm, khảo sát). `semantic.root_ids` một lượt (`:145-155`; đơn vị không gốc tự làm gốc `roots.get(i, -i)`, như `:251`). Khoá `answer.content_sig` (`:74-81`); thân rỗng khoá riêng theo `root_id` (nếu không mọi đơn vị rỗng cùng `sha1("")`). Chỉ gộp thẻ khác `doc_id` (hai Điều giống nhau trong một văn bản vẫn là hai mục). Đại diện = (`hieu_luc != 'con'`, ngày ban hành mới hơn, thứ tự); thẻ khác văn bản vào `also_in`. Vị trí mục là lần xuất hiện đầu nên gộp không đẩy ai xuống. `answer.snippet` cho `limit` mục đầu. Còn hơn 25 mục: thêm dòng "Còn N mục nữa, thêm số hiệu hoặc từ khoá" vào `q2_note` (kiểu `app.py:145-150`).
- `doc_groups(items)` theo `doc_id`, giữ thứ tự xuất hiện đầu, chỉ áp dụng trong từng nhóm hiển thị (5 mục đầu, rồi từng 10); tập mục trang 1 đúng bằng `items[:5]`. Không dùng `groupby` Jinja (sắp theo khoá, phá thứ hạng). Thẻ thiếu `doc_id` (test dựng bằng `SimpleNamespace`) tính là nhóm riêng.
- **Truy vấn chỉ có số hiệu** (`note == "so_hieu"` và `find_dieu_so(q)` rỗng, `sohieu.py:29`): `_cascade` (`search.py:643-644`) trả mọi đơn vị của mọi văn bản khớp, kể cả khớp tiền tố "15/2020" (`:222-239`, `_units_for_docs` `:247-272`), không bị `DIEU_CAP` (`app.py:145` chỉ chặn note `dieu`). Mức cắt 25 và dòng "thêm số hiệu" sai ngữ cảnh ở đây. Thay bằng **một mục "Mở toàn văn" mỗi văn bản** (tối đa 5 văn bản; ghi số Điều) mở trình đọc; bỏ qua `assemble_cards`. Gõ "số hiệu + Điều n" vẫn ra thẻ như cũ.
- Neo "Mở tại đoạn này" = `(doc_id, path)` của `unit_ids[0]` (như "Xem nguồn" hiện nay); phần trích và neo có thể lệch khoản. Chấp nhận, xem người thử; muốn khớp tuyệt đối thì lấy `path` dòng điểm cao nhất trong `_scores` (`answer.py:117-126`).
- Test trước (`tests/test_compact_results.py`, khuôn `tests/test_answer.py:13-28`, `:67-74`): hai văn bản cùng Điều 5 gộp một mục, đại diện là văn bản `hieu_luc='con'`; hai Điều giống nhau trong một văn bản không gộp; đơn vị thân rỗng không gộp nhầm; trang 1 đúng 5 mục hiện, tập == `items[:5]`, hạng 1 đầu; phần trích có khoản khớp kèm câu dẫn, ≤ ngân sách, `<mark>` đã thoát; `/export` với `uid` của mục đại diện còn `duty_text`; 600 thẻ chỉ xử lý `DIEU_CAP`, danh sách rỗng không lỗi; số hiệu một mình ra "Mở toàn văn" không ra 25 mục; `tests/test_d_app.py:271-291` và `tests/test_e_gaps.py:73` xanh không sửa.

#### K2. Template và CSS (1,0 ngày)
- `_results.html`: đầu danh sách thành một dòng "N kết quả" với bốn loại rủi ro nhỏ, nhãn kỹ thuật vào `title` (mẫu `:693`); "Độ tin cậy" viết lại bằng lời thường (`_results.html:21-26`). Vòng thẻ (`:35-68`) thành `doc_groups(cards[:5])`, các khối 10 mục sau trong `<div hidden>` với nút "Xem thêm 10 kết quả" (`data-more`, bộ xử lý uỷ quyền trong `app.js`). `[hidden]` đã có (`index.html:41`).
- Mỗi mục: `c.head or c.title` (Điều trùng số `D5~2` làm `head` mất "Điều 5.", `semantic.py:164-178`), số hiệu, huy hiệu hiệu lực, `highlight(c.snippet or c.duty_text, q)`, "Mở tại đoạn này" mang `data-doc/path/q/msg`, `<details>` "Cũng có ở", `c.warnings`.
- **Quyết định về `tests/test_d_app.py:271-291`: giữ bốn thứ test đòi, ở dạng gọn, không sửa test.** Giữ: nhãn trang (`card_pages`, `_results.html:55`), huy hiệu "Ý định: mức phạt" (`:40`), ghi chú tối đa 3 (đưa vào `<details>` "Ghi chú", chữ vẫn nằm trong HTML), "ban hành {ngày}" (`:56`); thêm "Hiệu lực chưa rõ" (`tests/test_app_export.py:41` cần). Lý do: bốn thứ này đều là một dòng đã có bảo vệ `is defined`, giữ chúng tốn 0 dòng sửa test; viết lại test cũng tốn công mà mất tính năng ghi chú (A4, `tests/test_c_search.py:200-210`) và thông tin trang/hiệu lực mà nguyên tắc 5 đòi. Bỏ: ba khối `sample`/`duty_text`/`sanction_text` (thay bằng phần trích), `link_status` (`:58`, chỉ có nghĩa cạnh khối chế tài). Giữ `synonym_note` và nhãn tầng 7 (`:59-60`) vì chúng báo "khớp không theo từ khoá".
- Giữ `<article class="card r{{rank}}">` và ô "Chọn xuất" `value=unit_ids[0]` (`:41`): `bench/stress10/run.py:52` tách HTML bằng regex `<article class="card[ \"]`, `tests/test_e_gaps.py:73` đếm `class="card`, `/export` đọc `uid`.
- Đăng ký `highlight`, `doc_groups` vào `TEMPLATES.env.globals` (`app.py:41`). `bench/stress10/run.py`: đổi sang gọi `_search_ctx` như `bench/run_bench.py:179`, `:298` (thẻ giờ chỉ có phần trích; `duty_text` đầy đủ vẫn còn trong `Card`).

#### K3. Đo theo mục (0,75 ngày công, phần còn lại máy chạy)
- `bench/zalo/eval.py`: `current()` (`:52-67`) gọi `compact`, trả danh sách `frozenset` khoá `file+Điều` (đại diện và mọi thẻ trong `also_in`); vòng chính `k in want` (`:132`) đổi thành `bool(k & want)`. Thêm `hien_tai_muc` (cả bản trùng) và `hien_tai_muc_dai_dien` vào `METHODS` (`:99-107`); giữ `hien_tai` làm mốc. Nhớ kết quả theo câu để `cascade_search` (~1,6 s, khảo sát) chạy một lần cho ba phương pháp. Báo thêm Hit@1, @5 (`:140-143` hiện chỉ in Hit@10, Recall, MRR).
- `bench/van-ban-that/eval_real.py`: gọi `compact` sau `cards_for` (`:31-37`); thử `[c, *c.also_in]` ở `:54-62`; thêm `so_muc`, `hien_san` (`:64-65`) và `muc_tb`, `hien_san_tb` (`:74-77`). Chú ý: `semantic.set_mode(conn, MODE)` (`:27`) ghi `search_mode` vào DB, nên chạy trên bản sao.
- `bench/doc_open.py` (cổng đầu). Bảng cổng điền từ file JSON kết quả bằng script, không gõ tay; mỗi số ghi bộ và n; chênh dưới vài câu trên 84 câu là nhiễu (1 câu = 1,2 điểm), không kết luận hơn kém.
- Ghi vào `bench/zalo/KET-QUA.md`, `bench/gold/KET-QUA.md`, `bench/van-ban-that/KET-QUA.md` kèm quy ước hai cách tính. Mốc "văn bản thật" của P1 là số sau sửa parser (84,5 / 91,7 / 96,4 / 96,4); cổng chỉ đòi @1, @5. Advance không thuộc cổng P1: mặc định là Normal (`semantic.py:88-90`), Advance đang thấp hơn ở @1 trên văn bản thật (lộ trình mục 9 điều 8).

#### B1. Chạy lại `bench/llm` (nền, không nằm trên đường găng; phần việc tay nằm trong K3)
- Khi: sau khi chủ dự án chốt ngoại lệ 1 (nếu gỡ parser thì bỏ B1). Không sửa mã trong lúc chạy; sửa thì dừng và chạy lại.
- Hai nhánh cùng mã `bc9f9af` (cộng thay đổi P1 không chạm `answer.py`), cùng máy, cùng llama.cpp, cùng tham số: nhánh cũ = bản sao kho trước khi dựng lại; nhánh mới = bản sao đã dựng lại. Lý do: số P0 là của mã `b17461f` và bản soát `bc9f9af` đã đổi bộ kiểm và phần dựng ngữ cảnh, nên so thẳng với P0 sẽ lẫn hai nguyên nhân.
- Ba lệnh ở `bench/llm/README.md` (Phụ lục B), ước ~7,5 giờ máy mỗi nhánh (~45 s/lần gọi: Zalo ~3 giờ, gold ~2,5 giờ, văn bản thật ~2 giờ), tức ~15 giờ cho hai nhánh. Văn bản thật chạy trước (nơi parser đổi nhiều nhất). Mỗi lệnh chạy nền kèm dòng `EXIT=$?`, tự bỏ qua phần đã xong (container có thể khởi động lại, `GHI-NHO-NGHIEN-CUU.md` mục 5); kiểm RAM và CPU trước khi bắt đầu, không chạy việc nặng khác cùng lúc (tranh CPU làm sinh chữ chậm ~10 lần).
- Báo: dẫn đúng Điều, JSON hợp lệ, số liệu khớp, mỗi số kèm bộ (test) và n. Không đặt ngưỡng mới ở P1: kết quả thành mốc cho "Việc trước P3" (lộ trình mục 6, P3) và cổng P3; tụt rõ so với nhánh cũ thì báo chủ dự án trước khi phát hành.

### Nhóm 1c: cuộc trò chuyện
#### H1. Lược đồ (0,25 ngày)
- `schema.sql`, toàn `CREATE TABLE IF NOT EXISTS` (chạy lại mỗi request vẫn an toàn, `db.py:49-64`):
  - `conversations(id, title NOT NULL, scope_json NOT NULL DEFAULT '[]', created_at, updated_at)` + chỉ mục `updated_at`.
  - `messages(id, conversation_id REFERENCES conversations ON DELETE CASCADE, role CHECK IN ('user','bot'), text, result_json, answer_json, created_at)` + chỉ mục `(conversation_id, id)`. Không khoá ngoại tới `units` (nạp lại đổi id, cascade sẽ xoá nhầm). `answer_json` để P3 (lộ trình :244).
  - `citation_opens(id, message_id, query_raw NOT NULL, doc_id, path, pos, gap REAL, opened_at)`. Không khoá ngoại: xoá cuộc trò chuyện (cascade `messages`) không làm mất dữ liệu chỉnh `SURE_GAP`. Bỏ cột `sure` (suy ra từ `gap >= SURE_GAP`). Ở Normal `gap` là NULL (`search.py:51-65`), chỉ Advance có (`:599-600`, `:621-624`).
- `ON DELETE CASCADE` chạy khi kết nối qua `db.connect` (`db.py:23`); mọi đường vào đều qua đó.
- Test trước (`tests/test_conversations.py::test_nang_cap_tu_0_8`): từ `schema_08.sql` thêm một văn bản, một đơn vị, một dòng `query_log`; `init_schema`; ba bảng mới có, dữ liệu cũ nguyên, chạy lại lần hai không đổi. Đây là "test nâng cấp trên bản sao DB 0.8" (lộ trình :442).

#### H2. Lưu câu hỏi: `POST /ask` (1,5 ngày)
- `src/soiluat/conversations.py`:
  - `refs_of(conn, ids, ...)`: mỗi id **sau lọc và cắt** (đúng cái người dùng thấy) thành `[doc_id, path, h, tier, fold, f2]`, `h` = 10 ký tự đầu sha1 chữ đơn vị. Một `SELECT` dùng `json_each` (như `semantic.root_ids`). Tối đa 100 (`RETURN_TOP`, `search.py:459`), ~6 KB.
  - `resolve(conn, refs)`: `SELECT id FROM units WHERE doc_id = ? AND path = ?` (như `rebuild.restore_links`, `:37-56`), chỉ nhận khi `h` khớp; trả (ids theo thứ tự cũ, số ref hỏng).
  - Vì sao cần `h`: lộ trình dặn tìm lại theo `(doc_id, path)` (:244), nhưng `documents.id` cũng tái dùng (`schema.sql:6`; đã thử: xoá id 3 thì lần chèn sau nhận 3) và `path` có thể đổi khi nạp lại (`p1.para{k}` `parse.py:351`, hậu tố `~n` `:274`). Chỉ `(doc_id, path)` có thể hiện nhầm đoạn mà không báo.
  - `save(...)`: ghi tin người dùng và tin trả lời trong một giao dịch ngắn, cập nhật `updated_at`. Tiêu đề = câu hỏi đầu, `unicodedata.normalize("NFC")`, cắt 60 ký tự thêm "…". Không tạo dòng `conversations` rỗng trước khi lưu được tin đầu.
  - `result_json` = `{q, filters, note, intent, sure, gap, q2_note, refs}`; không lưu thẻ dựng sẵn: mở lại dựng từ dữ liệu hiện tại để hiệu lực luôn mới (nguyên tắc 5).
- `POST /ask` (form `q`, `conversation_id`, `loai`, `co_quan`, `hieu_luc`): `_check_csrf`; tìm trước, ghi sau (không giữ khoá ghi suốt phần tìm Advance ~9 s); trả mảnh `_results.html` cộng header `X-Conversation-Id`, `X-Message-Id`. `GET /?q=` giữ nguyên (tìm không trạng thái; nhiều test dựa vào: `tests/test_review_queue.py:64-76`, `:105-116`, `tests/test_app_export.py:37`).
- Khoá ghi: khi đang nạp file, `INSERT` có thể chờ 5 s rồi ném `OperationalError` (`db.py:22`). Bắt lỗi, vẫn trả kết quả, thêm dòng "Chưa lưu được vào lịch sử (đang nạp file)"; không nuốt lỗi như `query_log` (`app.py:170`).
- `app.js` `ask()` (`index.html:278-298`) thành `POST` bằng `FormData` qua `post()` (N2). Xếp các lần hỏi thành một chuỗi promise (mã hiện cho hỏi chồng nhau; cuộc mới chưa có id tới khi có câu trả lời đầu, hai lần Enter nhanh sẽ tạo hai cuộc). Sau mỗi câu: `history.replaceState` sang `/c/{id}`, làm mới thanh bên.
- Test trước: lưu hai tin; tiêu đề NFC cắt 60; `refs_of`/`resolve` khứ hồi; `resolve` báo hỏng khi mất `path`, khi chữ đổi, khi `doc_id` bị văn bản khác dùng; sau `rebuild_document` vẫn tìm lại bằng `path`; khoá ghi (kết nối khác giữ `BEGIN IMMEDIATE`, POST ra 200 kèm dòng cảnh báo, không 500; test chờ ~5 s).

#### H3. Mở lại: `GET /c/{id}` (1,0 ngày)
- Mỗi tin trả lời: `resolve` → kết quả dựng từ `refs` (giữ thứ tự, bỏ ref hỏng) → `_ctx` → `TEMPLATES.get_template("_results.html").render(ctx)` ra chuỗi (`{% include %}` không dùng được vì `_results.html` đọc biến cấp trang). Không gọi `cascade_search`, không tốn ~9 s của Advance. Nhãn "độ tin cậy" chỉ giữ khi thẻ đầu còn là ref đầu đã lưu (cùng luật `app.py:152`). `ctx` mỗi tin có `msg_id` để in `data-msg`.
- Ref hỏng: dòng cảnh báo đầu câu trả lời đó ("N/M kết quả không còn đúng nguồn vì văn bản đã nạp lại hoặc xoá, hãy hỏi lại"), theo từng tin. `id` không có: 303 về `/`. `index.html`: `{% if thread %}` lặp các tin; `{% elif q %}` giữ; còn lại màn chào.
- Chi phí: mỗi tin dựng lại `assemble_cards` (~193 ms trên Zalo, khảo sát) + `compact` (~100-150 ms). Đo ở ngày 13; nếu cuộc 10 câu > 2 s thì chỉ dựng 3 câu cuối, câu trước hiện nút "Xem lại" gọi `GET /c/{id}/m/{mid}`. Chỉ làm nếu đo ra như vậy.
- Test trước: `cascade_search` thay bằng hàm ném lỗi, `GET /c/{id}` vẫn đủ mục (cổng 4); sau `rebuild_document` (id đổi) vẫn mở đúng; sau `UPDATE documents SET hieu_luc='het'` hiện "Hết hiệu lực"; ref hỏng có cảnh báo; id lạ ra 303.

#### H4. Thanh bên (1,25 ngày)
- `index.html` bọc `<header>/<main>/<form>` vào khung hai cột; `<aside class="side">` 264 px, ẩn dưới 760 px có nút mở (CSS mẫu `:101-103`, `:373-380`). Danh sách là `<a href="/c/{id}">` (tải lại cả trang, lùi/tiến và đánh dấu trang miễn phí; lộ trình :249 "không SPA").
- `_history.html`: "+ Cuộc trò chuyện mới" (liên kết `/`), ô tìm, nhóm Hôm nay / 7 ngày qua / Cũ hơn. "Đổi tên" và "Xoá" gọi `post()` (N2: chịu được khởi động lại; không dùng `<form>`), rồi tải lại; xoá hỏi bằng `confirm()` qua `data-confirm`, nói rõ `query_log` và `citation_opens` còn.
- Nhóm theo ngày địa phương, không theo UTC (`_now()` lưu UTC, `app.py:48`; tin 00:30 giờ Việt Nam nằm nhầm nhóm tới 07:00): `datetime.fromisoformat(ts).astimezone()`, hàm thuần `nhom(ts, now)`. Sắp `updated_at DESC, id DESC`.
- `GET /history?q=`: `fold_search` câu hỏi so với tiêu đề + tin người dùng, bằng Python. `shortcut:` lọc bằng Python, quá ~10 nghìn tin thì chuyển FTS.
- `POST /c/{id}/rename` (không rỗng, ≤ 80 ký tự, như mẫu), `POST /c/{id}/delete`; mọi route mới đóng kết nối trong `finally` (route hiện tại không làm vậy, `app.py:122-178`). `Alt+N`: `location.href = "/"`.
- Test trước: nhóm ngày quanh nửa đêm UTC+7 (`TZ` + `time.tzset()`); tìm không dấu ("ma tuy" thấy "ma túy"); đổi tên (rỗng, 81 ký tự bị từ chối); xoá cascade (`messages` về 0, `query_log` còn); id lạ ra 404.

#### H5. Ghi lượt mở trích dẫn (0,5 ngày)
- `search.py`: `CascadeResult` (`:51-65`) thêm `gap: float | None = None`, gán ở `:599-600` và `:621-624` (`gap` đã có ở đó, `_sure` `:581-582` mới bỏ nó).
- `POST /api/open` (`message_id`, `doc_id`, `path`, `pos`): `_check_csrf` (token ở header); đọc `q`, `gap` từ `result_json` của tin; `INSERT citation_opens`; tin không có: 404. `app.js`: bấm "Mở tại đoạn này" gọi `post()` với `keepalive: true`, không chờ, rồi mở ngăn kéo (`sendBeacon` không đặt được header CSRF). Kết quả không lưu (GET `/?q=`, hoặc lưu lỗi) không có `data-msg` nên không ghi.
- Viết lại `tests/test_review_queue.py:83-99`: ghi đúng dòng cho đúng tin; tin 1 và tin 2 cùng cuộc ghi đúng câu hỏi từng tin (lỗi của cách cũ: `/unit/{id}` ghi vào dòng mới nhất, `app.py:537-545`).

#### H6. Test CSRF cho mọi POST mới (0,25 ngày)
`tests/conftest.py:13-15` bật bypass CSRF cho mọi test. Một test tham số hoá cho `/ask`, `/c/{id}/rename`, `/c/{id}/delete`, `/api/open`: `monkeypatch.delenv("SOILUAT_ALLOW_TEST_HOST")`, `Host: 127.0.0.1:<cổng>`; không token ra 403, có token ra 200 hoặc 303 (khuôn `tests/test_host_csrf.py:4-24`, `tests/test_d_app.py:169-179`). Thêm ca "khởi động lại": đổi `app.CSRF_TOKEN`, POST token cũ ra 403, một GET, POST token mới ra 200.

### Nhóm Z

- **Z0. Thử gói trên Windows (0,25 ngày, ngày 5):** dựng bằng `pack/build.ps1` ngay khi `static/` có; mở gói, kiểm `/static/app.js` ra 200 và trình đọc mở được.
- **Z. Tài liệu, phiên bản (0,75 ngày):** `TAI-LIEU-KY-THUAT.md` mục 2.1 (`:43`: `reader.py`, `conversations.py`, `static/`, route mới), mục 2.2 (`:65`: ba bảng, bốn chỉ mục, `app_meta.parse_rev`), mục 11 (`:251-258`: `SURE_GAP` giờ có dữ liệu, dòng "không có nút xoá/sửa" giữ cho P2). **`HUONG-DAN.md:109-131` và `HUONG-DAN-DON-GIAN.md:67-92`** mô tả thẻ kết quả, "Xem nguồn →", "Chọn xuất", ô "Chế tài": viết lại cho "Mở tại đoạn này", ngăn kéo, "Cũng có ở", "Xem thêm", thanh lịch sử (cũng sửa `HUONG-DAN.md:117`, `:169` và `HUONG-DAN-DON-GIAN.md:75`, `:92`, `:144` nhắc "Xem nguồn"). Đồng bộ phiên bản 0.9: `__init__.py:3` (đang 0.7.0), `pyproject.toml:7` (đang 0.8.0), `pack/SoiLuat.iss:9` (đang 0.8). Bảng trạng thái P1 trong lộ trình.

## 4. Dùng lại gì (không viết mới)

| Cần | Dùng sẵn | Chỗ |
|---|---|---|
| Gộp trùng; chọn dòng khớp giữ câu dẫn; mẫu ghép | `answer.content_sig`; `_pick`, `_sentences`, `_scores`, `_window`; `build_context` | `answer.py:74-81`; `:102-201`; `:226-244` |
| Dòng của Điều; Điều gốc một lô | `semantic.root_lines` (cho phần trích, không cho thân trình đọc: quét cả văn bản mỗi lần, 457 ms so với 12-22 ms, khảo sát), `semantic.root_ids` | `semantic.py:164-178`, `:145-155` |
| Từ khoá, luật dấu, loại truy vấn | `answer._words` (đổi tên), `answer.STOP`, `query._eq`, `query.classify_query` | `answer.py:47-50`, `:98-99`; `query.py:90-92`, `:159-172` |
| Bỏ dấu, nhãn đường dẫn | `fold.fold_search`, `search_accent`, `pretty_path`, `display_addr`, `_PATH_RE` | `fold.py:65-128` |
| Gắn lại theo `(doc_id, path)`; dựng lại; luồng nền; sao lưu | `rebuild.restore_links`, `rebuild_document`; `JOBS.wake`, `semantic.missing_roots`; `db.backup_db` | `rebuild.py:37-56`, `:77-106`; `jobs.py:81-86`; `semantic.py:192-195`; `db.py:96-106` |
| Dựng thẻ từ id; CSRF, kết nối, mẫu, `HX-Request` | `cards.assemble_cards`, `summarize`, `_display_text`, `app._card_dates`; `_check_csrf`, `get_conn`, `_tpl` | `cards.py:385-524`, `:97-98`; `app.py:102-113`, `:82-99`, `:204` |
| Ảnh trang gốc; nhãn trang, hiệu lực | `pageimg.source_file`, `can_view`, `/page/{doc}/{n}`; `export_word.page_label`, `HIEU_LUC` | `pageimg.py:15-54`, `app.py:565-581`; `export_word.py:12-18`, `:9` |
| Khuôn test; CSS, JS | `tests/test_answer.py`, `test_host_csrf.py`, `conftest.py`; mẫu (chờ duyệt) | `test_answer.py:13-28`, `:67-74`; `mau/giao-dien-1.0.html:217-290`, `:861-904` |

Không dùng được: `answer.unique_roots` (`answer.py:84-95`) chỉ trả `limit` gốc đầu và vứt bản trùng; `answer.roots_in_order` (`:68-71`) bỏ đơn vị không gốc; `fold.pretty_path` ra "Điều 5 khoản 1", không phải thứ tự trích dẫn.

## 5. Không làm trong P1

| Cắt | Lý do | Sang đâu |
|---|---|---|
| Bộ khung `MIGRATIONS`, `app_meta.schema_version` | P1 chỉ thêm bảng và chỉ mục; một cờ `parse_rev` đủ. | P2 (`trich_yeu` là lần `ALTER` đầu; cột mới chỉ qua hàm nâng cấp) |
| Chèn phần mở đầu, khối sau "Nơi nhận", phụ lục đúng chỗ trong thân; tên Chương/Mục; tìm được nội dung phụ lục | Cần parser ghi khoảng dòng: đổi parser lần hai, cùng cổng đo. P1 có "Nguyên văn trang N". | P2 (cùng `trich_yeu`); nhánh chính xác mục 7 |
| `messages_fts`, hộp thoại xoá riêng, đồng bộ `scope_json` (cột có, luôn `'[]'`) | Lọc bằng Python và `confirm()` đủ cho một người dùng. | Quá ~10 nghìn tin; P5; P2 |
| Tab Liên quan, gắn tag, "Hỏi trong văn bản này", Ghi chú | Mẫu có nút; chức năng ở phase sau. | P4, P2 |
| Khung tô trên ảnh, ảnh cắt đoạn | Cần toạ độ chữ. | Nhánh chính xác mục 5 |
| Tô từ khớp cả văn bản; phân trang văn bản dài; khử chồng 50 từ của đoạn không cấu trúc | Nhiễu và chậm (R1); 548.000 ký tự ra ~800 KB HTML, dựng 0,24 s (khảo sát); 14 văn bản Zalo, 0 văn bản thật. | Nếu người thử muốn; khi gặp văn bản lớn hơn nhiều; không dự kiến |
| Tick từng Điều để xuất Word từ truy vấn chỉ số hiệu; đo Advance | Thay bằng "Mở toàn văn" (K1); Advance không phải mặc định. | P2 (xuất từ trình đọc); nhánh chính xác |
| Kiểm tự động giao diện (trình duyệt không đầu) | Không có trình duyệt ở môi trường soạn; không thêm Node. Thay bằng danh sách xem tay 14 mục (ngăn kéo, cuộn, `keepalive`, hàng đợi hỏi, `Alt+N`, clipboard, bố cục hẹp) ở ngày 5, 10, 15 trên Edge và Chrome Windows. | P5 |

## 6. Rủi ro và cách giảm

| # | Rủi ro | Giảm bằng |
|---|---|---|
| 1 | Sửa parser tụt tìm kiếm trên Zalo/gold (văn bản thật đã tụt @3, mục 2b). | Đo ở N1a; ngoại lệ cần duyệt; không đạt thì gỡ 5 dòng. |
| 2 | Dựng lại làm mất gợi ý hiệu lực đã duyệt, liên kết, vector. | Sửa 3 dòng giữ `confirmed = 1` (N1b); liên kết khôi phục theo `path`; sao lưu trước; vector nhúng lại. Kho thử chưa có gợi ý đã duyệt nên test phải tự tạo ca. |
| 3 | Dựng lại Zalo chậm (~50 giờ nếu thiếu chỉ mục). | N0 làm đầu tiên; đo ngày 1; tiến độ hiện trên giao diện; mỗi văn bản commit riêng. |
| 4 | Nâng cấp chết im, lặp mãi, hoặc hai bản chạy tranh nhau. | Bắt `OperationalError` từng văn bản, không ghi `parse_rev` khi còn sót, thử lại lần sau; chỉ ghi cờ khi xong hết. |
| 5 | Hiện nhầm đoạn khi mở lại cuộc cũ; mất câu hỏi khi đang nạp file. | Băm chữ `h` trong ref, báo theo từng tin, test ba ca; bắt lỗi ghi, vẫn hiện kết quả, dòng "chưa lưu được". |
| 6 | 403 sau khi app khởi động lại, hoặc bản thứ hai (cổng 8001) ghi đè cookie; test không bắt được thiếu CSRF (`conftest.py:13-15`). | `post()` gặp 403 thì GET một lần rồi gửi lại một lần (N2); test phía máy chủ; test tham số hoá tắt bypass (H6). |
| 7 | `static/` không vào gói; JS cũ bị dùng lại; `.js` thành `text/plain` trên Windows. | Z0 ngày 5; `no-cache`; `mimetypes.add_type`. |
| 8 | Phần trích đọc lủng củng trên OCR; "Mở tại đoạn này" mở khoản khác phần trích; đơn vị khổng lồ (58.945 ký tự ở Zalo) làm `block: center` rơi giữa khối. | Nối thành văn xuôi, 250 ký tự, bỏ dòng trùng tên Điều; người thử đánh giá, cách sửa nhỏ ở K1; cuộn tới `<mark>` đầu nếu đơn vị cao hơn khung nhìn. |
| 9 | Bỏ khối chế tài làm người dùng không thấy mức phạt. | Phụ lục A việc 1; thêm lại `c.sample` hạng 1-2 nếu thiếu (quyết định 4). |
| 10 | Mở lại cuộc nhiều câu chậm. | Đo ngày 13; phương án ở H3. |
| 11 | Hành vi giao diện không có test tự động; người làm một mình có thể không có máy Windows. | Danh sách xem tay (mục 5); điều kiện trước ngày 1 số 2. |
| 12 | Nâng cấp thêm 48 gợi ý liên kết vào hàng duyệt; sao lưu cần dung lượng trống bằng kho (Zalo 1,4 GB). | Ghi chú phát hành; sao lưu lỗi thì không dựng lại, chỉ báo. |

## 7. Lịch 4 tuần

Ngày công: N0 0,25; N1a 0,75; N1b 0,75; N2 0,75; R1 1,25; R2 1,75; R3 0,75; K1 2,0; K2 1,0; K3 0,75; H1 0,25; H2 1,5; H3 1,0; H4 1,25; H5 0,5; H6 0,25; Z0 0,25; Z 0,75 = **15,75 ngày mã**. Đệm 2,25 ngày (14%): 0,75 ở tuần 3, 1,5 ở tuần 4 (gồm ngày dựng gói và chạy lại cổng). Thử với người dùng 2 ngày. **Tổng 20 ngày.** Chênh so với bản nháp (13,75 + 1 đệm): N0, N1b có tiến độ, TIFF/BMP, "Nguyên văn trang", "Mở toàn văn", `post()` chịu khởi động lại, hai tệp hướng dẫn, đo hai cách tính.

| Tuần | Việc theo ngày | Bản chạy được cuối tuần |
|---|---|---|
| 1: đọc đúng đoạn | 1: N0, N1a; cuối ngày dựng bản sao Zalo (đo giờ), chạy Zalo và gold nền. 2: N1b, bắt đầu N2; chiều đọc số, **chốt ngoại lệ parser**. 3: N2, bắt đầu R1; khởi động B1 sau khi chốt. 4: R1, bắt đầu R2a. 5: R2a, Z0. | **0.9-a:** bấm "Xem nguồn" mở `/doc/{id}?path=…#u{id}` (trang đầy đủ), đúng khoản/điểm, đoạn tô, "Sao chép trích dẫn", "Chi tiết kỹ thuật"; dữ liệu cũ đã nâng cấp; danh sách kết quả vẫn như 0.8. |
| 2: kết quả gọn | 6: R2b (ngăn kéo), bắt đầu R3. 7: R3, bắt đầu K1 (tách `_search_ctx`, test trước). 8: K1. 9: K1 xong, K2. 10: K2 xong, K3 (sửa hai script, chạy nền qua cuối tuần); xem tay Edge/Chrome. | **0.9-b:** ngăn kéo, tab Bản gốc (cả TIFF/BMP), 5 mục đầu, "Xem thêm", "Cũng có ở", "Mở toàn văn"; Word không đổi; chưa có lịch sử. |
| 3: lịch sử chat | 11: đọc số K3, điền bảng cổng, H1, bắt đầu H2. 12: H2. 13: H3, đo thời gian mở lại. 14: H4. 15: H4 xong, đệm. | **0.9-c:** lưu và mở lại cuộc trò chuyện, thanh bên, đổi tên, xoá, tìm; chưa ghi lượt mở. |
| 4: đóng gói, thử | 16: H5, H6. 17: Z (tài liệu, phiên bản). 18: dựng gói Windows, chạy lại cổng tự động, xem tay lần cuối, giao người thử. 19: 3-5 người thử 8 việc (Phụ lục A). 20: sửa, ghi kết quả, cập nhật lộ trình. | **0.9:** đủ ba nhóm, đóng gói. |

**Cắt theo thứ tự này nếu trễ:** (1) `Alt+N` 0,1; (2) ô tìm lịch sử 0,25; (3) nút toàn màn hình 0,1; (4) thanh bên thu gọn ở màn hẹp 0,25 (cộng 0,7 ngày). Cắt hết vẫn chưa về 3 tuần; muốn 3 tuần phải bỏ thêm `citation_opens` + `/api/open` (0,5) và đưa TIFF/BMP về P5 (0,25), tức đổi lộ trình, cần chủ dự án. **Không cắt:** N0, sao lưu, test CSRF và `post()` chịu khởi động lại, băm `h`, đo cổng, test nâng cấp 0.8.

## 8. Sửa lộ trình, phần P1

1. P1 từ 3 tuần lên 4 tuần (20 ngày làm việc: 15,75 mã + 2,25 đệm + 2 thử).
2. Thêm việc lộ trình chưa ghi: bốn chỉ mục khoá ngoại; nâng cấp dữ liệu một lần trong luồng nền (có sao lưu); sửa parser điểm nhiều dòng **kèm ngoại lệ quy tắc 7** nếu chủ dự án duyệt (mục 2b); tăng `PARSE_REV` khi đổi đầu ra parser.
3. Mục 1c (:244): tham chiếu kết quả lưu `(doc_id, path)` **kèm băm chữ**, vì `documents.id` cũng tái dùng. Mục 7: thêm bảng `citation_opens` và bốn chỉ mục; `gap` chỉ có ở Advance.
4. Mục 1b: "Xem thêm" 10 mục mỗi lần, tối đa 25; truy vấn chỉ có số hiệu ra một mục "Mở toàn văn" mỗi văn bản; gộp trùng gần như không giảm số mục; cổng "Hit theo mục" có hai cách tính, cổng đề xuất theo bộ (mục 2b).
5. Mục 1a (:226): phần ngoài Điều ở P1 chỉ có "Nguyên văn trang N" cho văn bản không có ảnh trang; chèn đúng chỗ trong thân sang P2, vì cần sửa parser lần hai. TIFF/BMP giữ trong P1.
6. Mốc `bench/llm` của cổng P3 là hai nhánh đo lại sau sửa parser (B1), không phải số P0.

## Phụ lục A: 8 việc cho người thử (cổng người dùng)

Mỗi người làm lần lượt, không hướng dẫn; ghi "làm được / làm được sau gợi ý / không làm được". Đạt khi ≥ 90% ở mức "làm được".

1. Hỏi một câu **mức phạt** cho trước; nói Điều nào trả lời và số tiền phạt là bao nhiêu (kiểm quyết định 4).
2. Từ kết quả, bấm "Mở tại đoạn này", chỉ ra đoạn được tô.
3. Sao chép trích dẫn của đoạn đó và dán vào Word.
4. Xem ảnh trang gốc của đoạn đó (văn bản PDF hoặc ảnh).
5. Xem thêm kết quả ngoài 5 mục đầu, tìm một mục cho trước.
6. Mở cuộc trò chuyện mới, hỏi một câu khác.
7. Tìm lại cuộc cũ bằng ô tìm trong lịch sử, mở lại.
8. Đổi tên một cuộc, rồi xoá nó.

Ghi thêm mỗi người: phần trích có đọc ra câu không; có muốn tô từ khớp cả văn bản không; `Alt+N` có chạy trên máy họ không; có thấy lạ khi gõ số hiệu mà ra "Mở toàn văn" không.

## Phụ lục B: lệnh đo

- Test: `python -m pytest -q` (ở môi trường soạn: `/tmp/claude-0/venv/bin/python`).
- Tìm kiếm Normal (trên bản sao; PowerShell dùng `$env:SOILUAT_SEMANTIC="0"`): `SOILUAT_SEMANTIC=0 python -I bench/zalo/eval.py <zalo> <data> test`; cùng lệnh với `<gold_vle> ... gold`; `SOILUAT_SEMANTIC=0 python -I bench/van-ban-that/eval_real.py <realdocs> normal`.
- Mở trình đọc: `python -I bench/doc_open.py <data Zalo>`.
- Câu trả lời (B1; `bench/llm/README.md`): `python bench/llm/run.py <kho Zalo>\soiluat.db <thư mục zalo> --split test --n 100 --bay 50 --out zalo_llm.json`; `... <thư mục gold vle> --split gold --n 100 --out vle_llm.json`; `python bench/llm/run.py <realdocs>\data\soiluat.db <realdocs>\queries.json --n 84 --bay 0 --out real_llm.json`.

## Đã kiểm / chưa kiểm

**Đã kiểm trong mã và trên bản sao (31/10/2026, mã `bc9f9af`):**
- Mọi `file:line` trong tệp này đã đối chiếu bằng `grep`/`sed`; `answer.py` đọc lại sau `bc9f9af` (`_words` `:98`, `content_sig` `:74`, `_window` `:129`, `_pick` `:144-201`, `build_context` `:226-244`).
- Bốn chỉ mục: `EXPLAIN` ra `SCAN` cả bốn; xoá văn bản 89 đơn vị trên bản sao Zalo 41,5 s → 0,01 s; tạo chỉ mục 0,37 s (tôi đo). Kho Zalo: 3.271 văn bản, 3 có ngày ban hành, tất cả "chưa rõ", 14 `fallback_doan = 1`, mỗi văn bản 1 trang, 2.784 có điểm; kho thật thử: 13/21 có ngày.
- Bản vá parser: diff với bản vá thử của người soát đúng 5 chỗ; `eval_real` chạy lại (số ở mục 2b); liên kết 73 → 121, `CHE_TAI` 187 → 173, gợi ý 6 → 5, 1.242/2.610 đơn vị đổi chữ, 16/21 văn bản đổi.
- `StaticFiles` thiếu thư mục ném `RuntimeError`, chỉ có ETag/Last-Modified. Pillow: TIFF 3 trang, BMP, PDF tạo bằng Pillow chạy qua `pageimg`. `pytest` hôm nay xanh, 7 bỏ qua.
- Critique: 7 `wrong_refs` đúng cả và đã sửa, trừ hai chỗ lệch: **`parse.py:353-354` critique nêu cho `if in_sign: continue` là sai** (đó là chữ đoạn mồ côi; `if in_sign:` ở `:357-358`, điều kiện bật ở `:365-367` đúng như critique nói); import pypdfium2 ở `pageimg.py:43` (critique ghi `:1`, `:39`). Mọi mục `missing`, `risks_missed`, `overbuilt` đã áp dụng; riêng `citation_opens` giữ `query_raw` và `gap` (xoá cuộc trò chuyện làm mất `result_json`), chỉ bỏ cột `sure`.
- Phát hiện thêm: `DIEU_CAP = 100` (không phải 25) nên `compact` lấy `cards[:100]`; truy vấn tiền tố số hiệu ("15/2020") liệt kê Điều của nhiều văn bản.

**Chưa kiểm:**
- Không có trình duyệt: ngăn kéo, cuộn tới đoạn, `keepalive`, hàng đợi hỏi, `Alt+N`, clipboard, `post()` thử lại khi 403, bố cục hẹp chỉ đọc từ mã và mẫu. Không có PyInstaller, không có Windows: chưa biết `static/` có vào gói không (Z0).
- Chưa chạy: Zalo test và gold sau sửa parser; thời gian dựng lại kho Zalo với chỉ mục; p95 mở trình đọc (`bench/doc_open.py` chưa có); số "Hit theo mục" (Zalo 83 → 79, 89 → 85 và 0/84 thẻ trùng ở văn bản thật là khảo sát); mở lại cuộc nhiều câu; `bench/llm` sau sửa parser (~15 giờ máy). Chưa kiểm lại: 5/21 số hiệu sai, 53-55% dòng ngắn của OCR, `HostGuard` bọc cả mount `/static` (test N2 sẽ kiểm).
- Rủi ro cần biết nhất: 20 ngày là ước lượng của một người, chưa đo thật ở nhóm K và H; hai ngoại lệ ở mục 2b cần chủ dự án duyệt trước khi giữ bản sửa parser.
