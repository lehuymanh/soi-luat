# Bàn giao cho lượt làm sau (ghi nhớ nghiên cứu)

Viết lần đầu 31/10/2026 ở cuối P0, viết lại cùng ngày ở cuối P1, cho bản 0.9.0. Người đọc chính: agent (hoặc người) làm tiếp lộ trình (P2), đo lại tìm kiếm hay câu trả lời AI, hoặc chạy job dài. Tài liệu này giữ **trạng thái, bước đầu tiên, kết luận, phương pháp, cách dựng lại môi trường và bẫy**. Số liệu đầy đủ nằm ở tài liệu nguồn; ở đây chỉ chép số cần để định hướng, kèm chỗ tra. Bản đồ mọi tài liệu và tệp: `docs/README.md`.

Đọc theo thứ tự này:

1. Tệp này: mục 1 là đủ nếu chỉ cần biết làm gì tiếp; mục 3 trước khi đo bất cứ gì; mục 4 khi dựng lại máy; mục 5 trước khi chạy job dài.
2. `docs/ke-hoach/lo-trinh-1.0.md`: mục 6 (P2, nhánh độ chính xác, "Việc trước P3"), mục 9 (quyết định còn mở).
3. `docs/ke-hoach/ke-hoach-p1.md`: mục "Nhóm Z", B1, "Phụ lục A", "Đã kiểm / chưa kiểm".
4. `docs/nghien-cuu/so-thu-nghiem.md`: bảng tổng hợp để biết đã thử gì, rồi "Câu hỏi còn mở".
5. `docs/quy-trinh.md`: mục 4 (cổng đo), 8 (môi trường), 11 (bẫy).
6. `bench/README.md` (bộ đo nào, chạy lệnh gì), `bench/llm/KET-QUA.md` (vòng 2 ở đầu, vòng 1 ở dưới), `bench/van-ban-that/KET-QUA.md` (mốc tìm kiếm).

---

## 1. Trạng thái bàn giao

### 1.1 Đang ở đâu và bước đầu tiên

- **Bản 0.9.0** (`src/soiluat/__init__.py`), nhánh `claude/funny-feynman-xvg6dm`. `python -m pytest -q`: **471 qua, 7 bỏ qua** (chạy 31/10/2026 ở mã `a13af05`, đo lại cùng ngày ở cây mã sau `30d68e8`; các commit sau `a13af05` không đổi hành vi: `src/` và `tests/` chỉ khác một ghi chú trong `sohieu.py`, commit `52cbbd2`). Số này đo với `.[dev,ocr,nghia]` và **không** đặt `SOILUAT_TESSDATA`; chỉ cài `.[dev]` thì 441 qua, 9 bỏ qua; đặt `SOILUAT_TESSDATA` thì 473 qua, 5 bỏ qua. Lý do từng test bỏ qua: mục 4, bước 9. Trước đó: 443 qua (`fdad4d3`), cuối P0: 258 qua. PR lehuymanh/soi-luat#2 (base `claude/hopeful-keller-jcw0pr`) xếp trên PR lộ trình lehuymanh/soi-luat#1 (base `main`). Cả hai không còn là bản nháp (chủ dự án chuyển #2 sang sẵn sàng soát ngày 31/10/2026); kiểm lại 31/10/2026: `gh api repos/lehuymanh/soi-luat/pulls/<số> --jq .draft` ra `false` cho cả #1 và #2, cả hai còn mở, chưa merge. Agent không merge PR.
- **P0 xong** phần máy làm được. **P1 xong phần mã** (lộ trình mục 6, P1; từng việc và số đo ở `docs/ke-hoach/ke-hoach-p1.md`). Chưa gắn tag, chưa dựng bộ cài (`git tag` trống ngày 31/10/2026). Ghi chú phát hành đã nháp ở `CHANGELOG.md`.
- **Còn thiếu để phát hành 0.9.0 và đóng P1**, đều cần thứ mà môi trường soạn không có: (a) dựng bộ cài bằng `pack/build.ps1` trên Windows và thử gói (Z0); (b) xem tay trên Edge và Chrome Windows (Z1); (c) 3 đến 5 người dùng thật làm 9 việc (`docs/ke-hoach/ke-hoach-p1.md`, Phụ lục A; chưa có tên người thử); (d) chạy lại `bench/llm` hai nhánh trước và sau sửa parser (B1, khoảng 15 giờ máy; parser đã chốt nên được phép bắt đầu).
- Mã trả lời AI (`src/soiluat/answer.py`) **vẫn chưa gắn vào app**; chỉ `bench/llm/run.py` gọi nó. P3 sẽ gắn. Số đo LLM của P0 là của mã `b17461f`; sau đó bản soát sửa thêm 6 lỗi (`bc9f9af`). Lần đo kế tiếp phải chạy trên mã mới và trên parser mới (chữ đưa vào mô hình đã đổi).
- **Bước đầu tiên cho phiên sau:**
  1. `git status --short` và `git log --oneline -5`; đọc `CLAUDE.md`, rồi `docs/README.md`.
  2. Hỏi chủ dự án một lần về các quyết định còn mở (mục 1.4), nhất là cách tính cổng P0 cho câu trả lời AI (lộ trình mục 9, điều 10) và chế độ tìm mặc định (điều 8), vì hai điều này quyết định cổng P3; và tên người thử cho cổng người dùng của P1.
  3. Có máy Windows: làm Z0 rồi Z1 (`docs/ke-hoach/ke-hoach-p1.md`, "Nhóm Z"), rồi tag theo `docs/quy-trinh.md` mục 10. Không có máy Windows: lập kế hoạch P2 (`superpowers:brainstorming`, `superpowers:writing-plans`, theo `docs/ke-hoach/lo-trinh-1.0.md` mục 6, P2), và chạy B1 nếu máy rảnh (một job nặng mỗi lúc, mục 5).
  4. Chưa có kế hoạch P2 được duyệt thì chưa viết mã P2 (`docs/quy-trinh.md` mục 0).

### 1.2 Không đo lại khi mã liên quan chưa đổi

Đã chốt; số ở tài liệu nguồn. Muốn đo lại thì phải nêu thứ gì đã đổi.

| Đã đo | Chỗ tra | Đo lại khi |
|---|---|---|
| Chọn mô hình: Qwen3-VL-4B; Gemma 4 E4B và Nemotron-3.5-Bolt-E4B đã đo, không hơn | `bench/llm/KET-QUA.md` vòng 2; sổ CN-01, CN-03, CN-04 | có ứng viên mới cùng cỡ và có lý do mới |
| Mốc tìm kiếm P0 trên văn bản thật: Hit@1 rộng Normal 83,3%, Advance 72,6% (n = 84) | `bench/van-ban-that/KET-QUA.md`, mục "Mốc P0"; sổ TK-09 | sửa bước hợp BM25 với vector (lộ trình, nhánh độ chính xác, điều 0) |
| Mốc Normal của 0.9.0 trên ba bộ (văn bản thật n = 84; Zalo test n = 788 và gold n = 500, theo mục) | mục 1.3; sổ PS-06, PS-07, HT-02; message của `a13af05` | đổi `search.py`, `sohieu.py`, `query.py`, `semantic.py`, `fold.py`, `crossrank.py` hoặc `parse.py` (cổng: `docs/quy-trinh.md` mục 4) |
| Mở trình đọc p95 27 ms; xoá văn bản 41,5 s xuống 0,01 s; nâng cấp dữ liệu | sổ HT-03, PS-05, PS-09 | đổi `reader.py`, route `/doc`, chỉ mục khoá ngoại hay `rebuild.py` |
| A/B ba biến thể `pham_vi` trên train; mốc offline bằng chứng (mục 3.2) | `bench/llm/KET-QUA.md`; sổ LM-02, LM-04 | đổi `answer.py`, lời nhắc hay khuôn JSON |

**Phải đo lại** (chưa có số hợp lệ): `bench/llm` sau sửa parser, hai nhánh trước và sau trên cùng mã (kế hoạch P1, B1); tốc độ, RAM và p95 45 giây trên máy 16 GB Windows; mọi thứ giao diện trong Edge và Chrome Windows.

### 1.3 Phiên 31/10/2026 đã làm gì

Số đo kèm bộ và n; chi tiết, cách đo và lý do giữ hay bỏ ở sổ thí nghiệm (mã trong cột cuối) và `docs/ke-hoach/ke-hoach-p1.md`. Không chép lại ở đây.

| Việc | Kết quả đáng nhớ | Chỗ tra |
|---|---|---|
| Đóng P0 | Mẫu giao diện dựng lại theo taste-skill, chủ dự án duyệt; kế hoạch P1 lập và tối ưu còn 21,5 ngày; lộ trình ghi ba đề xuất B, C, D được duyệt | sổ GD-02; `docs/ke-hoach/ke-hoach-p1.md` mục 0 |
| Parser: điểm nhiều dòng (N1a), B1 + B2 + B3 và gộp Phụ lục (N3), giữ gợi ý hiệu lực khi dựng lại (N1c), nâng cấp dữ liệu một lần `PARSE_REV = "2"` (N1b) | Điều tách được 322 lên 345/344 (21 văn bản thật, máy Linux; mốc Windows 341/344, lệch vì bộ chữ `vie`: mục 4, bước 5); nâng cấp 21 văn bản thật 5,6 s, kho Zalo 1.760/3.271 văn bản dựng lại 467 s | sổ PS-06 đến PS-10 |
| Trình đọc `/doc` và tab Bản gốc (R1 đến R3) | p95 27 ms phía máy chủ (bản sao kho Zalo, 101 văn bản) | sổ HT-03 |
| Kết quả gọn (K1 đến K3) | khoảng 40 thẻ mỗi câu (39,8 mục trước khi cắt, văn bản thật n = 84) xuống 5 mục hiện sẵn; Hit@1 theo thẻ lên theo mục: Zalo test (n = 788) 58,6% lên 61,0%, gold (n = 500) 51,2% lên 52,6% | sổ HT-01, HT-02 |
| Lịch sử trò chuyện (H1 đến H4, H6), thanh bên, hộp thoại và toast | mở lại cuộc 10 câu: dựng đủ trung vị 2,41 s, sau "Xem lại" 713 ms | sổ HT-04 |
| Nền: bốn chỉ mục khoá ngoại (N0), `static/` (N2), hệ thiết kế và phông nhúng (G0) | xoá văn bản 89 đơn vị 41,5 s xuống 0,01 s (bản sao kho Zalo) | sổ PS-05; kế hoạch P1 N0, N2, G0 |
| Soát độc lập nhiều đợt, mỗi lỗi có test hỏng trên mã cũ | 56 phát hiện ở kế hoạch, 23 lỗi ở R2a đến K2, 12 ở lịch sử trò chuyện, rồi soát toàn repo: 5 lỗi "Phải sửa" (C1, C2, C3, SEC-1, F2) | sổ SO-05 đến SO-08 |
| Đợt dọn mã cuối (`9780468`, `a13af05`): S1, S2, S4, S6, S7, F1, F7, SEC-2, SEC-3, SEC-5, SEC-6, C4, C5, C6/F5 (một phần), C7, C10, F3, F4, bỏ mã chết | Cổng quy tắc 7 giữ nguyên: văn bản thật (n = 84, rộng @1/@3/@5/@10) 86,9 / 94,0 / 97,6 / 98,8%, giống mốc; Zalo test (n = 788, theo mục) Hit@1 61,2%, Hit@5 86,5% (mốc 61,0 / 86,4); gold (n = 500, theo mục) 52,4 / 77,4% (mốc 52,6 / 77,4), khác một câu do thứ tự ngẫu nhiên giữa các bản trùng chữ, không do mã | message của `a13af05`, `9780468` |
| Phát hành | Số 0.9.0 ở mọi nơi (`eb7df1d`), tài liệu 0.9 (`af7404f`), `CHANGELOG.md` nháp (`7b41b3b`) | `docs/quy-trinh.md` mục 10 |
| Harness và tài liệu | Skill của dự án vào repo (`818efdb`); tài liệu gom về `docs/` (`fdad4d3`); sổ thí nghiệm (`51feedc`); quy trình và 4 workflow (`796e7f2`); `docs/README.md`, `bench/README.md` và bản bàn giao này | `docs/quy-trinh.md` |
| Bản mẫu khái niệm: dự án, ghi chú rủi ro, đồ thị | Chưa duyệt | sổ GD-03; `docs/nghien-cuu/khai-niem-du-an-do-thi-dinh-huong.md` |

### 1.4 Quyết định còn mở

Chỉ liệt kê chỗ ghi; không chép nội dung. Bản gom từng câu hỏi kèm việc kế tiếp: `docs/nghien-cuu/so-thu-nghiem.md`, mục "Câu hỏi còn mở".

- `docs/ke-hoach/lo-trinh-1.0.md` mục 9, phần "Còn mở": điều 1 (người thử, nhân lực), 2 (máy 8 GB), 3 (≥ 100 câu hỏi thật), 4 (gói AI), 5 (chứng thư ký số), 6 (ai duyệt hiệu lực), 7 (đồ thị toàn kho), 8 (chế độ tìm mặc định), 10 (cách tính cổng P0 cho câu trả lời AI), 14 (ý tưởng dự án, ghi chú rủi ro, đồ thị). Điều 9, 11, 12, 13 đã trả lời.
- `docs/ke-hoach/ke-hoach-p1.md` mục 1: hỏi (a) dời ghi lượt mở trích dẫn sang nhánh chính xác, hỏi (b) máy quét có xuất TIFF, BMP không, và tên người thử. Chưa có trả lời thì làm theo mặc định ghi ở đó.
- Ý tưởng của chủ dự án ngày 31/10/2026, chưa duyệt và chưa có trong lộ trình: dự án (nhóm văn bản), ghi chú rủi ro, sổ rủi ro, đồ thị. Ba tên này nghĩa khác nhau, định nghĩa ở `docs/README.md` mục 5. Ghi ở lộ trình mục 9 điều 14, sổ GD-03 và "Câu hỏi còn mở" số 9, và bản định hướng `docs/nghien-cuu/khai-niem-du-an-do-thi-dinh-huong.md` mục 14 (năm câu mở). Việc đầu tiên nếu duyệt: lấy một tệp rủi ro thật của khách đã che thông tin.
- Hoãn từ đợt soát: C8 (số hiệu sửa tay phải bền qua nạp lại) và phần còn lại của F10; cả hai đi cùng việc "đánh dấu trường đã sửa tay" của P2 (lộ trình mục 7).
- Đã được chủ dự án duyệt (31/10/2026) nhưng chưa chạy: thử nghiệm C (mô hình ghi chép để tìm tốt hơn) và D (Qwen đọc ảnh trang đầu để gợi ý số hiệu, ngày); việc B (lưu toạ độ chữ) đã đưa lên P2 (lộ trình mục 6 và 9).

### 1.5 Môi trường soạn không kiểm được

- **Windows:** bộ cài (`pack/build.ps1`), gói PyInstaller có `static/` và chín tệp phông không (Z0), Word COM (SEC-1 đặt `AutomationSecurity` thành `ForceDisable`, chưa chạy với Word thật), Edge và Chrome (Z1).
- **Máy 16 GB:** tốc độ, RAM, p95 45 giây (`bench/llm/README.md`).
- **Giao diện:** chỉ có ảnh Playwright (Chromium); chưa có người dùng thật bấm.
- **Workflow:** bốn script ở `.claude/workflows/` đã kiểm cú pháp và chạy với agent giả, chưa chạy bằng công cụ Workflow thật; lần chạy thật đầu tiên cần xem tay (`docs/quy-trinh.md` mục 6).

---

## 2. Kết luận nghiên cứu

Mục 2.1 đến 2.4 là kết luận của P0 (30 và 31/10/2026). Kết luận của P1 (parser, kết quả gọn, trình đọc, lịch sử trò chuyện, các đợt soát) nằm ở `docs/nghien-cuu/so-thu-nghiem.md`, nhóm PS, HT, SO.

### 2.1 Tìm kiếm (mốc cho P1)

- Trên 21 văn bản thật 2026 (84 câu đã kiểm chứng), **Normal hơn Advance ở hạng 1**: Hit@1 rộng 83,3% so với 72,6%. Bước làm tụt là hợp điểm vector với BM25 (BM25 + vector, chưa reranker: 67,9%). Ở @10 hai bên gần bằng. Nguồn: `bench/van-ban-that/KET-QUA.md`, mục "Mốc P0".
- Hệ quả đã ghi vào lộ trình: giữ Normal làm mặc định tới khi nhánh độ chính xác (mục 6, điều 0) sửa bước hợp; P3 chạy được với Normal.

### 2.2 Trả lời bằng LLM

- Mô hình chính **Qwen3-VL-4B-Instruct Q4_K_M** (lý do chọn: `chon-mo-hinh.md`). Vòng 1 → vòng 2 trên tập test (Zalo / gold / văn bản thật): dẫn đúng Điều 66,7 / 70 / 46,7% → **83,3 / 75 / 86,7%**; khẳng định như đủ căn cứ khi đã bỏ Điều đúng 66,7 / 65 / 33,3% → **26,7 / 40 / 13,3%**; JSON dùng được 87,5 / 92,5 / 96,7% → 100%; chữ Trung 3,8 / 10 / 0% → 0%. Mức tăng chắc chắn (vượt nhiễu): dẫn đúng ở Zalo và văn bản thật, khẳng định sai ở Zalo. Gold chỉ +1 câu.
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

Tiêu chí (từ `chon-mo-hinh.md` mục 1): mở trọng số, giấy phép cho dùng thương mại ngoại tuyến, GGUF chạy llama.cpp trên CPU, RAM mô hình ~4 GB (trần 6 GB), tắt chế độ suy nghĩ, kịp 45 giây p95 kể cả phần tìm. Cách làm lần 30/10/2026: bốn hướng tìm song song (mô hình nhỏ mới của các hãng; bản tinh chỉnh tiếng Việt/Đông Nam Á; bảng xếp hạng bám ngữ cảnh, tiếng Việt, làm theo chỉ dẫn; hỗ trợ llama.cpp), một bước xếp hạng theo đúng lỗi đang gặp, hai tác tử kiểm chứng ngược tại nguồn (thẻ mô hình, giấy phép, tệp GGUF, llama.cpp). Rồi đo ứng viên trên đúng bộ đo, cùng mã, không chỉnh riêng. Bài học: số bám ngữ cảnh do hãng công bố bằng tiếng Anh (Bolt: GaRAGe +9,8 điểm) không chuyển sang tiếng Việt.

### 3.7 Đo tìm kiếm và parser (quy tắc 7)

Lệnh của từng cổng, tiêu chí qua và cách ghi số: `docs/quy-trinh.md` mục 4; lệnh theo từng script: `bench/README.md`. Điều rút ra khi làm P1:

- Đo trước và sau **trên cùng một bản dựng và bản sao riêng**; luôn truyền `--tag`; mỗi số kèm bộ, tập chia, n và mã.
- Sửa không nhằm đổi thứ hạng (dọn mã, tăng tốc) thì cổng là "Hit@1 và Hit@5 không thấp hơn trước"; sửa nhằm cải thiện thì phải tốt hơn trên cả Zalo lẫn gold và không tụt trên văn bản thật. Chênh nhỏ mà theo chữ thấp hơn thì cần ngoại lệ có tên (sổ PS-06, HT-02).
- Một câu đổi hạng sau khi dựng lại kho: dựng **biến thể A** (mã mới, các văn bản đổi chữ giữ chữ của parser cũ) để biết do mã tìm kiếm hay do parser. Thứ tự giữa các bản trùng chữ là ngẫu nhiên (id đơn vị lớn hơn thì lên trước), nên một câu tụt từ hạng 1 xuống 2 giữa các bản trùng không phải hồi quy (đợt `a13af05`, bộ gold).
- Không so p50 của hai lượt chạy khác `--only` hoặc khác bản sao: lượt `hien_tai_muc` riêng tính cả thời gian tìm, còn số của K3 chỉ là phần gom mục.
- `bench/parse_khac.py <data>` cho biết kho đã lưu có cần nâng cấp không: 0 văn bản đổi thì không cần tăng `PARSE_REV`; khác 0 thì tăng và chạy cổng quy tắc 7 (`docs/kien-truc.md` mục 6.5).

---

## 4. Môi trường và chạy lại

**Mọi đường dẫn `/tmp/claude-0/...` là của phiên soạn (31/10/2026) và mất khi container bị thu hồi.** `KET-QUA.md` và `docs/nghien-cuu/so-thu-nghiem.md` là bản ghi chính thức. JSON thô (kết quả `bench/llm/run.py`, `bench/zalo/ket_qua_gold*.json`) không commit: câu hỏi gold `vle` chưa có giấy phép (`bench/gold/README.md`) và JSON thô của LLM chứa chữ lấy từ các bộ đó. Vị trí các kho đo ở phiên soạn và cách dùng từng công cụ: `docs/quy-trinh.md` mục 8. Chính sách tệp kết quả: `bench/README.md`.

Dựng lại để đo (Linux, CPU):

1. **Đĩa:** `df -h /` trước. Mỗi bản kho Zalo 1,4 đến 1,6 GB. Giữ trống từ 1 GB; luôn chép bản sao rồi mới ghi, không bao giờ ghi vào kho gốc.
2. **Python:** venv riêng (từ 3.11; phiên soạn dùng 3.13). Đây là chỗ duy nhất ghi cách dựng; `CLAUDE.md` và `docs/quy-trinh.md` mục 8 trỏ về đây. Chạy bench bằng `python -I`.

   ```bash
   python3 -m venv <venv>
   <venv>/bin/pip install -e '.[dev,ocr,nghia]'  # pytest, build, OCR, Advance: đủ để ra 471 qua, 7 bỏ qua (bước 9)
   <venv>/bin/pip install -e '.[bench]'          # thêm khi dựng kho Zalo và gold (pandas, pyarrow)
   <venv>/bin/pip install pymupdf openpyxl       # chỉ cho bench/stress10/gen.py (10 tệp đã commit, thường không cần chạy)
   sudo apt install tesseract-ocr tesseract-ocr-vie   # Linux; tên gói chưa thử trên máy trống (xem dưới)
   export SOILUAT_TESSDATA=/usr/share/tesseract-ocr/5/tessdata
   <venv>/bin/python -m soiluat.importer --check-ocr   # phải in "ok": true trước import_real.py hay stress10
   ```

   Chú thích: `pytesseract` nằm trong `.[ocr]`. `pymupdf` cung cấp module `fitz`; thiếu nó thì hai test của `tests/test_e_gaps.py` bị bỏ qua. `gen.py` còn cần `openpyxl` (import ở đầu tệp, không nằm trong extra nào) và phông Arial của Windows (`ARIAL` ở dòng 19 là đường dẫn Windows). Tên gói apt khớp `dpkg -S` trên máy soạn (`tesseract-ocr` có `/usr/bin/tesseract`, `tesseract-ocr-vie` có `vie.traineddata`) nhưng chưa thử cài trên máy trống. Ở máy soạn, không đặt `SOILUAT_TESSDATA` thì `--check-ocr` ra `"ok": false` dù tệp `vie` đã có, và `stress10` ra 18/20 (`docs/quy-trinh.md` mục 11). Cho `bench/llm`: `pip install llama-cpp-python==0.3.36` (bản PyPI; dựng llama.cpp từ git bị chặn trong môi trường này; bản 0.3.36 có kiến trúc `qwen3vl` và `gemma4`).
3. **Công cụ ngoài:** Tesseract có gói `vie` (thiếu thì đặt `SOILUAT_TESSDATA`); Node có Playwright cho `bench/kiem_anh.js` (`NODE_PATH=$(npm root -g) node ...`).
4. **Kho đo:**
   - **Zalo:** dùng **một** thư mục `<zalo>` có đủ bốn tệp. `corpus_test-00000-of-00001.parquet` là corpus: chỉ `build_db.py` và `build_vle.py` đọc, từ tham số đầu. `queries.jsonl`, `qrels_test.jsonl`, `qrels_train.jsonl` là câu hỏi và đáp án: `eval.py` và `embed_needed.py` đọc từ tham số đầu (`qrels_<tập>.jsonl`, tập `test` hay `train`; tập `gold` đọc `qrels_gold.jsonl` trong thư mục gold), cùng `tune.py`, `why_miss.py`, `app_ram.py`; `build_vle.py` chỉ đọc `queries.jsonl`. Tham số thứ hai của các script này là `<data>`, thư mục nhận hay có `soiluat.db`. Tải từ Hugging Face (MIT, cần mạng và `pip install huggingface_hub` để có lệnh `hf`), rồi đổi tên, vì tên tệp trên Hugging Face khác tên script cần. Bố cục kiểm ngày 31/10/2026 ở bản `12d76d4` (danh sách tệp, cột `id, title, text` của corpus, khoá `_id` và `query-id, corpus-id` của JSONL); `build_vle.py` chạy được trên bản tải này (500 câu), còn `build_db.py` (~510 giây) chưa chạy lại trên nó:

     ```bash
     hf download GreenNode/zalo-ai-legal-text-retrieval-vn corpus/test-00000-of-00001.parquet queries.jsonl qrels/test.jsonl qrels/train.jsonl --repo-type dataset --local-dir <hf_zalo>
     mkdir -p <zalo>
     cp <hf_zalo>/corpus/test-00000-of-00001.parquet <zalo>/corpus_test-00000-of-00001.parquet
     cp <hf_zalo>/queries.jsonl <zalo>/
     cp <hf_zalo>/qrels/test.jsonl <zalo>/qrels_test.jsonl
     cp <hf_zalo>/qrels/train.jsonl <zalo>/qrels_train.jsonl
     python -I bench/zalo/build_db.py <zalo> <data>   # ~510 giây, 427 nghìn đơn vị; dựng bằng parser hiện tại nên đã là kho "sau"
     ```

     `bench/llm/run.py` đọc được cả `qrels/<tập>.jsonl` (bố cục gốc), nên với nó không cần đổi tên. Chi tiết số đo: `bench/zalo/KET-QUA.md`.
   - **Gold `vle`:** `<ViLegalExperts>` là thư mục có trực tiếp `test_data.json` và `dev_data.json` (không có thư mục con `QA_single_context/`). Chỉ giữ trên máy (`bench/gold/README.md`). Bố cục kiểm ngày 31/10/2026 ở bản `0bb255d`: tải hai tệp (khoảng 111 MB) rồi chạy `build_vle.py` ra 500 câu (từ 35.505 còn 5.437 đạt, như `bench/gold/README.md`):

     ```bash
     hf download DatNguyenAIML/ViLegalExperts QA_single_context/test_data.json QA_single_context/dev_data.json --repo-type dataset --local-dir <hf_vle>
     mkdir -p <ViLegalExperts>
     cp <hf_vle>/QA_single_context/test_data.json <hf_vle>/QA_single_context/dev_data.json <ViLegalExperts>/
     python -I bench/gold/build_vle.py <zalo> <ViLegalExperts> <gold> --n 500   # <gold> ngoài repo; ghi queries.jsonl, qrels_gold.jsonl
     ```
   - **Văn bản thật:** tải 21 PDF theo `bench/van-ban-that/manifest.json` (cần header `Referer: https://vanban.chinhphu.vn/`), đặt trong `<realdocs>/files/` cùng `manifest.json` và `queries.json` (bản có sẵn ở `bench/van-ban-that/`), rồi `python bench/van-ban-that/import_real.py <realdocs>`. Bộ chữ `vie` khác bản làm số Điều tách được lệch (lần dựng P0 trên Linux ra 321/344 so với 341/344 trên Windows: `bench/van-ban-that/KET-QUA.md`). Kho cần vector cho Advance: `python -m soiluat.importer --nhung` với `SOILUAT_DATA=<realdocs>/data`.
5. **Mô hình Advance (AITeamVN):** `python pack/export_models.py <OUT_DIR>` (cần mạng, torch và vài GB trống); trỏ `SOILUAT_MODEL_DIR` tới `<OUT_DIR>/aiteamvn-embedding` và `SOILUAT_RERANK_DIR` tới `<OUT_DIR>/aiteamvn-reranker`. Thiếu hai biến này thì lượt chạy không phải Advance. Kho Zalo chỉ nhúng Điều cần: `bench/zalo/embed_needed.py`.
6. **Mô hình sinh (Hugging Face, tải bằng `huggingface_hub`):** `Qwen/Qwen3-VL-4B-Instruct-GGUF` tệp `Qwen3VL-4B-Instruct-Q4_K_M.gguf`; `google/gemma-4-E4B-it-qat-q4_0-gguf` tệp `gemma-4-E4B_q4_0-it.gguf`; `bartowski/NVIDIA-Nemotron-3.5-Bolt-E4B-GGUF` tệp `NVIDIA-Nemotron-3.5-Bolt-E4B-Q4_K_M.gguf`.
7. **Máy chủ:** `python -m llama_cpp.server --model <gguf> --n_ctx 4096 --n_threads 4 --host 127.0.0.1 --port 8080`; đợi `/v1/models` trả lời (`curl --noproxy '*'`). Khởi động bằng `setsid nohup ... &` để sống qua giới hạn 2 giờ của lệnh nền; lưu PID, dừng bằng `kill <PID>`.
8. **Chấm:** ba lệnh ở `bench/llm/KET-QUA.md`, mục "Chạy lại"; lệnh B1 (hai nhánh từ worktree cố định) ở `docs/ke-hoach/ke-hoach-p1.md`, Phụ lục B. Trên máy 16 GB (Windows, `llama-server`): `bench/llm/README.md`.
9. **Kiểm nhanh môi trường:** `python -m pytest -q -rs` (`-rs` in lý do bỏ qua) ra dòng cuối `471 passed, 7 skipped` khi đã cài `.[dev,ocr,nghia]` (bước 2) và chưa đặt `SOILUAT_TESSDATA`. Số khác là do môi trường, không phải lỗi mã:
   - Chỉ cài `.[dev]`: 441 qua, 9 bỏ qua. So với bảy dòng dưới thì thêm ba: `tests/test_jobs.py` và `tests/test_semantic.py` bị bỏ cả tệp vì không có `numpy` (mỗi tệp tính một), `tests/test_a_ocr.py:89` vì không có `pytesseract`. Bớt một: dòng 7, vì cả `tests/test_semantic.py` đã bị bỏ.
   - Đặt `SOILUAT_TESSDATA` (bước 2): hai test OCR thật chạy, ra 473 qua, 5 bỏ qua.
   - Bảy test bị bỏ qua ở 471/7 (số dòng ở cây mã sau `30d68e8`):
     1. `tests/test_a_formats.py:165`: không có `win32com.client` (Word COM, chỉ có trên Windows).
     2. `tests/test_a_ocr.py:135`: "máy không có Tesseract + vie" (hết khi đặt `SOILUAT_TESSDATA`).
     3. `tests/test_a_ocr.py:205`: "máy không có Tesseract + vie + osd" (hết khi đặt `SOILUAT_TESSDATA`).
     4. `tests/test_crossrank.py:122`: cần `SOILUAT_RERANK_DIR` trỏ tới mô hình thật.
     5. `tests/test_e_gaps.py:100`: không có `fitz` (`pip install pymupdf`).
     6. `tests/test_e_gaps.py:133`: không có `fitz`.
     7. `tests/test_semantic.py:178`: cần `SOILUAT_MODEL_DIR` trỏ tới mô hình thật.

Thời lượng trên máy ảo 4 nhân: Qwen ~50 đến 60 giây mỗi lần gọi, Gemma và Bolt ~65 đến 80 giây; ba bộ test = 150 lần gọi. Một vòng B1 hai nhánh ước ~15 giờ máy.

---

## 5. Bẫy đã gặp

Một bảng duy nhất, có cột hậu quả và cách tránh: [`docs/quy-trinh.md`](../quy-trinh.md) mục 11 (tiến trình và máy, đo, git và cộng tác, giao diện, môi trường). Không chép lại ở đây.

---

## 6. Việc tiếp theo

Theo thứ tự nên làm. Kế hoạch chi tiết của từng việc nằm ở tài liệu được dẫn, không ở đây.

1. **Đóng 0.9.0** (cần Windows và người): Z0, Z1, cổng người dùng (`docs/ke-hoach/ke-hoach-p1.md`), rồi tag và ghi chú phát hành (`docs/quy-trinh.md` mục 10, skill `release-version-sync`). Số phiên bản 0.9.0 đã được chủ dự án chốt (`eb7df1d`).
2. **B1** (máy, nền): chạy lại `bench/llm` hai nhánh trước và sau sửa parser; kết quả là mốc cho "Việc trước P3" và cổng P3. Một job nặng mỗi lúc (`docs/quy-trinh.md` mục 11).
3. **Kế hoạch P2** (kho văn bản: tag, ghi chú, @, hiệu lực; việc B lưu toạ độ chữ và việc D gợi ý số hiệu từ ảnh đi cùng): lập theo `docs/ke-hoach/lo-trinh-1.0.md` mục 6 (P2) và mục 7 (thay đổi dữ liệu), rồi xin duyệt. Mẫu giao diện cho Kho và @ làm ở đầu P2.
4. **Nhánh độ chính xác** (lộ trình mục 6, "Nhánh song song"): điều 0 (hợp BM25 với vector làm tụt hạng 1 trên văn bản thật) trước, vì nó quyết định chế độ mặc định; điều 3 (reranker nhiều luồng) sớm vì ảnh hưởng ngân sách 45 giây của P3.
5. **Việc trước P3** (lộ trình mục 6, P3): câu bẫy chạm trần token; tín hiệu điểm tìm kiếm thấp cho lỗi phạm vi; tách câu bẫy train và test; chạy lại `bench/llm` (việc 2 ở trên); máy 16 GB; ≥ 100 câu hỏi thật.
6. **Quyết định của chủ dự án:** mục 1.4.

## 7. Bản đồ tệp

Bản đồ tệp của repo và từ điển thuật ngữ nằm ở một nơi: `docs/README.md` (mục 4 và 5). Bảng riêng của tệp này đã bỏ để khỏi lệch.
