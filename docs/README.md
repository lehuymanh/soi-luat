# Bản đồ tài liệu của Soi Luật

Viết 31/10/2026, cho bản 0.9.0. Đây là **chỗ vào đầu tiên** cho một phiên mới (agent hoặc người). Tệp này chỉ chỉ đường. Mỗi sự thật nằm ở đúng một nơi; ở đây có đường dẫn tới nơi đó, không có bản sao số đo.

## 1. Soi Luật là gì, cho ai

Soi Luật là app tra cứu văn bản pháp luật Việt Nam **chạy hoàn toàn offline** trên máy Windows văn phòng. Nhân viên văn phòng nạp thư viện văn bản của chính họ (Word, PDF, ảnh scan), gõ từ khoá hoặc câu hỏi thường, và đọc **nguyên văn** Điều, khoản, điểm kèm văn bản nguồn và số trang. App chỉ nghe `127.0.0.1` và không gửi dữ liệu ra ngoài. Phần mềm là FastAPI, Jinja và JavaScript thuần, kho SQLite với FTS5, một luồng nền cho nạp file và nhúng vector, hai mô hình AITeamVN chạy CPU là tuỳ chọn (chế độ Advance). Trả lời bằng LLM nằm ở giai đoạn P3: lõi `src/soiluat/answer.py` đã có và đã đo, nhưng **chưa gắn vào app**. Kiến trúc đầy đủ: [`kien-truc.md`](kien-truc.md). Luật làm việc của dự án: [`../CLAUDE.md`](../CLAUDE.md).

**Máy mục tiêu:** PC Windows 16 GB RAM, không card rời (chủ dự án chốt 29/10/2026). `README.md`, `HUONG-DAN.md` và `HUONG-DAN-DON-GIAN.md` còn ghi máy 8 GB; máy 8 GB có còn được hỗ trợ không là câu hỏi mở ([lộ trình](ke-hoach/lo-trinh-1.0.md) mục 9, điều 2).

**Không bao giờ** (luật gốc: [`kien-truc.md`](kien-truc.md) mục 1.3 và 1.5, [lộ trình](ke-hoach/lo-trinh-1.0.md) mục 5 và 10):
- gửi dữ liệu ra ngoài `127.0.0.1`;
- sinh chữ thay nguyên văn: trích dẫn luôn lấy từ kho;
- tự kết luận văn bản còn hay hết hiệu lực: máy gợi ý, người xác nhận;
- sửa ranh giới Điều hay chữ OCR trong app: sửa file nguồn rồi nạp lại;
- đưa câu hỏi gold `vle` vào repo (chưa có giấy phép).

## 2. Đang ở đâu

| Mục | Trạng thái |
|---|---|
| Phiên bản | **0.9.0** (`src/soiluat/__init__.py`; số do chủ dự án chọn ngày 31/10/2026). Ghi chú phát hành: [`../CHANGELOG.md`](../CHANGELOG.md) |
| Nhánh | `claude/funny-feynman-xvg6dm`; PR lehuymanh/soi-luat#2 xếp trên PR lộ trình #1, cả hai không còn là bản nháp (kiểm 31/10/2026), trạng thái ở [`nghien-cuu/ghi-nho.md`](nghien-cuu/ghi-nho.md) mục 1 |
| Giai đoạn | **P0 xong** phần máy làm được. **P1 xong phần mã**: trình đọc mở đúng đoạn, kết quả gọn, lịch sử trò chuyện, giao diện mới, parser đúng hơn, nâng cấp dữ liệu tự động |
| Còn lại để phát hành 0.9.0 | Dựng bộ cài Windows (`pack/build.ps1`, chỉ chạy được trên Windows) và thử gói (việc Z0); xem tay trên Edge và Chrome Windows (Z1); 3 đến 5 người dùng thật làm 9 việc (cổng người dùng); chạy lại `bench/llm` hai nhánh trước và sau sửa parser (B1, khoảng 15 giờ máy). Chi tiết ở [`ke-hoach/ke-hoach-p1.md`](ke-hoach/ke-hoach-p1.md), mục "Nhóm Z", B1 và "Phụ lục A" |
| Quyết định chờ chủ dự án | [`ke-hoach/lo-trinh-1.0.md`](ke-hoach/lo-trinh-1.0.md) **mục 9**, phần "Còn mở" (cách tính cổng câu trả lời AI, chế độ tìm mặc định, người thử, máy 8 GB, gói AI, chứng thư ký số, người duyệt hiệu lực, ý tưởng dự án và ghi chú rủi ro ở điều 14). Thêm các câu hỏi của kế hoạch P1 ở mục 1 (hỏi a, b và người thử). Danh sách gom theo từng câu hỏi nằm cuối [`nghien-cuu/so-thu-nghiem.md`](nghien-cuu/so-thu-nghiem.md), mục "Câu hỏi còn mở" |
| Dữ liệu ngoài repo | Gold `vle` không có chỗ lưu bền: bản đang dùng nằm ở `/tmp/claude-0/work/gold_vle` của phiên soạn và mất khi máy đó bị dọn. Dựng lại bằng `bench/gold/build_vle.py` (cần mạng để tải ViLegalExperts). Lý do giữ ngoài repo: [`../bench/gold/README.md`](../bench/gold/README.md) |
| Bước đầu tiên cho phiên sau | [`nghien-cuu/ghi-nho.md`](nghien-cuu/ghi-nho.md) mục 1.1 |

## 3. Đọc theo việc

Đọc theo thứ tự trong cột giữa; dừng khi đã đủ. Cột cuối là chỗ dễ bỏ qua và làm hỏng việc.

| Việc | Đọc, theo thứ tự | Lưu ý |
|---|---|---|
| **Làm tiếp lộ trình, bắt đầu P2** | 1. [`nghien-cuu/ghi-nho.md`](nghien-cuu/ghi-nho.md) mục 1. 2. [`ke-hoach/lo-trinh-1.0.md`](ke-hoach/lo-trinh-1.0.md) mục 6 (P2, nhánh song song), mục 7 (thay đổi dữ liệu), mục 9. 3. [`ke-hoach/ke-hoach-p1.md`](ke-hoach/ke-hoach-p1.md) mục "Nhóm Z" và "Đã kiểm / chưa kiểm". 4. [`quy-trinh.md`](quy-trinh.md) mục 3 | P2 chưa có kế hoạch triển khai: lập trước khi viết mã (`superpowers:brainstorming`, `superpowers:writing-plans`). Mẫu giao diện cho Kho và @ làm ở đầu P2 khi lập kế hoạch (lộ trình mục 6, P0 bước 5). `lo-trinh-1.0.md` bị `ke-hoach-p1.md` trích theo số dòng (`:486`, `:497`) và `ke-hoach-p1.md` bị sổ thí nghiệm trích một chỗ ("mục 1 dòng 4"): sửa cả hai tại chỗ, giữ số dòng |
| **Đổi tìm kiếm** (`search.py`, `sohieu.py`, `query.py`, `semantic.py`, `fold.py`, `crossrank.py`) | 1. [`kien-truc.md`](kien-truc.md) mục 7. 2. [`nghien-cuu/so-thu-nghiem.md`](nghien-cuu/so-thu-nghiem.md) nhóm TK, "Tiêu chí giữ". 3. [`quy-trinh.md`](quy-trinh.md) mục 4 (cổng quy tắc 7). 4. [`../bench/README.md`](../bench/README.md) | Quy tắc 7: chỉ giữ khi tốt hơn trên cả Zalo lẫn gold và không tụt trên văn bản thật. Luôn `--tag`. Chạy trên bản sao kho |
| **Đổi parser** (`parse.py`) | 1. [`kien-truc.md`](kien-truc.md) mục 6.5 (nâng cấp dữ liệu, `PARSE_REV`). 2. [`nghien-cuu/so-thu-nghiem.md`](nghien-cuu/so-thu-nghiem.md) nhóm PS. 3. [`quy-trinh.md`](quy-trinh.md) mục 4 (cổng parser). 4. [`../bench/van-ban-that/KET-QUA.md`](../bench/van-ban-that/KET-QUA.md) | Đổi đầu ra parser thì tăng `PARSE_REV` và chạy cổng quy tắc 7. Skill `legal-doc-structure-parsing` |
| **Đổi giao diện** | 1. [`quy-trinh.md`](quy-trinh.md) mục 4 (cổng giao diện), mục 11 (bẫy giao diện). 2. [`../mau/giao-dien-1.0.html`](../mau/giao-dien-1.0.html) (mẫu đã duyệt). 3. [`ke-hoach/ke-hoach-p1.md`](ke-hoach/ke-hoach-p1.md) nhóm G0, K2, H4 | Theo taste-skill, kiểm bằng ảnh Playwright rồi mở từng ảnh (skill `html-mockup-visual-check`). App thật không tải gì từ mạng, kể cả phông |
| **Đo** (tìm kiếm, parser, trình đọc, câu trả lời AI) | 1. [`nghien-cuu/ghi-nho.md`](nghien-cuu/ghi-nho.md) mục 1 (số nào đã chốt, không đo lại), mục 3 (phương pháp). 2. [`../bench/README.md`](../bench/README.md). 3. [`quy-trinh.md`](quy-trinh.md) mục 4, 8 và 11 (bẫy) | Chỉnh trên train, chấm test một lần. Mỗi số kèm bộ, tập chia, n, mã. Đĩa trống từ 1 GB trước khi chép kho |
| **Đo câu trả lời AI** | 1. [`nghien-cuu/ghi-nho.md`](nghien-cuu/ghi-nho.md) mục 2.2, 3.1, 3.2, 4. 2. [`../bench/llm/README.md`](../bench/llm/README.md). 3. [`../bench/llm/KET-QUA.md`](../bench/llm/KET-QUA.md) | Đo offline bằng `bench/llm/bang_chung.py` trước; chỉ biến thể thắng mới tốn giờ chạy mô hình. Một job nặng mỗi lúc trên máy 4 nhân |
| **Phát hành** | 1. [`quy-trinh.md`](quy-trinh.md) mục 10. 2. [`../CHANGELOG.md`](../CHANGELOG.md). 3. [`../pack/build.ps1`](../pack/build.ps1). 4. [`kien-truc.md`](kien-truc.md) mục 9 | Skill `release-version-sync`. Bộ cài Windows chỉ dựng được trên Windows. Agent không merge PR |
| **Viết tài liệu** | 1. [`quy-trinh.md`](quy-trinh.md) mục 12. 2. Skill `handoff-memo`, `vietnamese-decimal-format`, `plan-doc-line-reference-edits` | Tiếng Việt, câu ngắn, không dấu gạch dài, số thập phân dùng dấu phẩy (86,9%), mỗi số kèm bộ và n. Dẫn đường dẫn từ gốc repo và kiểm bằng `ls`, `grep -n` |
| **Chọn skill và workflow theo việc** | [`quy-trinh.md`](quy-trinh.md) mục 5 (giao việc), 6 (workflow), 7 (skill) | Soát mã: workflow `review-lenses` và `superpowers:requesting-code-review`; sửa phát hiện bằng skill `review-findings-fix-loop`. Đổi giao diện: taste-skill, skill `html-mockup-visual-check`, `/ponytail:ponytail`, `bench/kiem_anh.js`; mẫu khái niệm dùng workflow `ui-prototype-research`. Một bước kế hoạch: workflow `plan-step-tdd`, `superpowers:test-driven-development`; cả kế hoạch đã duyệt: skill `execute-approved-plan`. Phát hành: skill `release-version-sync`, workflow `ponytail-audit` trước khi phát hành, `stacked-draft-pr`, `git-delivery` |
| **Giao việc cho agent, soát mã** | 1. [`quy-trinh.md`](quy-trinh.md) mục 5, 6. 2. [`../.claude/workflows/`](../.claude/workflows/) | Việc vài lệnh thì tự làm. Mỗi workflow dưới khoảng 10 agent. Trailer ghi công truyền qua `args.trailer` |
| **Hiểu sản phẩm từ phía người dùng** | [`../HUONG-DAN-DON-GIAN.md`](../HUONG-DAN-DON-GIAN.md), rồi [`../HUONG-DAN.md`](../HUONG-DAN.md), [`../README.md`](../README.md) | Hai hướng dẫn giữ nguyên tới P5 (lộ trình mục 6, P5), nên `HUONG-DAN-DON-GIAN.md` chỉ có thêm mục "Có gì mới ở bản 0.9" |

## 4. Bản đồ tệp của repo

### Gốc

| Tệp | Là gì |
|---|---|
| `CLAUDE.md` | Luật ngắn tự nạp vào mọi phiên: con trỏ tới tài liệu, quy trình, luật gold |
| `README.md` | Giới thiệu và cài đặt, cho người chạy từ mã nguồn |
| `CHANGELOG.md` | Ghi chú phát hành từng bản |
| `HUONG-DAN-DON-GIAN.md`, `HUONG-DAN.md` | Hướng dẫn cho người dùng cuối (ngắn; đầy đủ) |
| `pyproject.toml` | Gói Python, phụ thuộc, `package-data` (gồm `static/`, `templates/`) |
| `data/` | Kho thử cục bộ của máy dev (`soiluat.db`); `.gitignore` bỏ qua, không commit |

### `docs/`

| Tệp | Là gì |
|---|---|
| `docs/README.md` | Tệp này |
| `docs/kien-truc.md` | Kiến trúc, lược đồ dữ liệu, luồng nạp và tìm, đóng gói, giới hạn đã biết |
| `docs/quy-trinh.md` | Cách làm việc: luật và lý do, vòng làm việc, cổng đo, giao việc, workflow, skill, môi trường, commit, phát hành, bẫy |
| `docs/ke-hoach/lo-trinh-1.0.md` | Lộ trình 0.8 đến 1.0: phản hồi người dùng, các phase P0 đến P5, nhánh độ chính xác, thay đổi dữ liệu, **mục 9 quyết định của chủ dự án** |
| `docs/ke-hoach/ke-hoach-p1.md` | Kế hoạch triển khai P1 từng việc, kèm trạng thái và số đo |
| `docs/nghien-cuu/ghi-nho.md` | **Bản bàn giao**: trạng thái, bước đầu tiên, kết luận, phương pháp đo, dựng lại môi trường, bẫy |
| `docs/nghien-cuu/so-thu-nghiem.md` | Sổ mọi thí nghiệm (50 mã), kể cả thất bại, bài học chung, câu hỏi còn mở |
| `docs/nghien-cuu/chon-mo-hinh.md`, `docs/nghien-cuu/chon-csdl.md` | Ghi chú nghiên cứu: chọn mô hình ngôn ngữ theo benchmark công khai; chọn cơ sở dữ liệu và framework đồ thị (ước tính, chưa đo trên máy 16 GB) |
| `docs/nghien-cuu/khai-niem-du-an-do-thi-dinh-huong.md` | Bản định hướng của bản khái niệm dự án, ghi chú rủi ro, đồ thị (chưa duyệt; sổ GD-03) |

### `src/soiluat/` (mã app)

Bản đồ module Python và giao diện (`templates/`, `static/`): [`kien-truc.md`](kien-truc.md) mục 3.1 và 3.2. Không chép lại ở đây.

### Các thư mục còn lại

| Thư mục | Là gì |
|---|---|
| `tests/` | Bộ `pytest` (`python -m pytest -q`); dữ liệu mẫu ở `tests/fixtures/`. Số test hiện tại ở [`nghien-cuu/ghi-nho.md`](nghien-cuu/ghi-nho.md) mục 1 |
| `bench/` | Bộ đo và kết quả; bảng từng script ở [`../bench/README.md`](../bench/README.md). Thư mục con: `zalo/` (Zalo test), `gold/` (gold `vle` và bộ văn phòng), `van-ban-that/` (21 văn bản thật), `llm/` (câu trả lời AI), `stress10/` (10 file lệch cấu trúc) |
| `pack/` | Đóng gói Windows: `SoiLuat.spec` (PyInstaller), `SoiLuat.iss` (Inno Setup), `build.ps1`, `export_models.py` (xuất mô hình Advance), `run_search.py` |
| `mau/` | Mẫu giao diện: `giao-dien-1.0.html` (đã duyệt 31/10/2026), `khai-niem-du-an-do-thi.html` (bản khái niệm, chưa duyệt; bản định hướng ở `docs/nghien-cuu/`) |
| `.claude/skills/` | Các skill của dự án, mỗi skill ép một thói quen đã từng bị bỏ quên; bảng ở [`quy-trinh.md`](quy-trinh.md) mục 7 |
| `.claude/workflows/` | 4 workflow có tham số: `review-lenses`, `ponytail-audit`, `plan-step-tdd`, `ui-prototype-research`; tham số ở [`quy-trinh.md`](quy-trinh.md) mục 6 |

## 5. Từ điển thuật ngữ

| Thuật ngữ | Nghĩa trong dự án |
|---|---|
| **Điều, khoản, điểm** | Ba tầng cấu trúc của văn bản luật. Điều (`Điều 5.`) chứa khoản (`1.`), khoản chứa điểm (`a)`). Phần không có cấu trúc chia theo đoạn |
| **path** | Địa chỉ của một đơn vị trong văn bản. `D5.K1.Đa` là Điều 5, khoản 1, điểm a. Phụ lục có dạng `PL1.para3`; số lặp có hậu tố `~2` (`parse.py`) |
| **unit, đơn vị** | Một dòng bảng `units`: đơn vị tìm kiếm, `level` là `dieu`, `khoan`, `diem` hoặc `doan`. Điều gốc (không có `parent_id`) là đơn vị được nhúng vector. Lược đồ: [`kien-truc.md`](kien-truc.md) mục 4.1 |
| **thẻ (card)** | Kết quả tìm kiếm được dựng từ các đơn vị, có nhãn rủi ro và chế tài (`cards.assemble_cards`); 0.8 hiện hết thẻ |
| **mục** | Từ 0.9: một dòng kết quả hiển thị cho mỗi (văn bản, Điều), do `cards.compact` gộp từ thẻ; Điều giống hệt ở văn bản khác vào "Cũng có ở" |
| **Normal, Advance** | Hai chế độ tìm. Normal: BM25 và quy tắc, ~1 giây. Advance: thêm vector toàn kho và reranker, ~9 giây, cần hai mô hình AITeamVN. Normal là mặc định (chốt còn mở ở lộ trình mục 9, điều 8) |
| **tầng khớp** | Mức khớp của một kết quả. Tầng 0 tra thẳng số hiệu hoặc "Điều n"; 1 cụm liền; 2 gần nhau; 3 đủ từ; 4 đồng nghĩa; 6 một phần; 7 chỉ khớp theo nghĩa (Advance). [`kien-truc.md`](kien-truc.md) mục 7.2 |
| **Hit@k rộng, chặt** | Tỉ lệ câu hỏi có đáp án trong k kết quả đầu. **Chặt** đòi đúng số Điều. **Rộng** (chỉ bộ văn bản thật) tính cả thẻ cùng file có trang phủ trang chứa câu trích. Zalo và gold tính theo Điều. Định nghĩa đủ ở [`nghien-cuu/so-thu-nghiem.md`](nghien-cuu/so-thu-nghiem.md), mục "Quy ước đọc số" |
| **theo thẻ, theo mục** | Hạng tính trên danh sách thẻ (0.8) hay trên danh sách mục hiển thị (0.9). Theo mục có hai cách: chỉ bản đại diện, hay cả bản trong "Cũng có ở" (lộ trình mục 9, điều 12) |
| **quy tắc 7** | Nguyên tắc chính xác số 7 ([lộ trình](ke-hoach/lo-trinh-1.0.md) mục 5): đo trước khi giữ. Thay đổi phần tìm chỉ được giữ khi tốt hơn trên cả Zalo lẫn gold và không tụt trên văn bản thật. Ngoại lệ phải có tên và do chủ dự án duyệt bằng văn bản |
| **PARSE_REV** | Hằng số trong `parse.py` (hiện `"2"`). Đổi đầu ra parser thì tăng nó; kho cũ được nâng cấp một lần khi mở app, sao lưu trước ([`kien-truc.md`](kien-truc.md) mục 6.5) |
| **gold `vle`** | Câu hỏi tư vấn luật thật từ ViLegalExperts ánh xạ vào kho Zalo (số câu: [`nghien-cuu/so-thu-nghiem.md`](nghien-cuu/so-thu-nghiem.md), mục "Bộ dữ liệu"). **Chưa có giấy phép: giữ ngoài repo**; kết quả `bench/zalo/ket_qua_gold*.json` bị `.gitignore`. [`../bench/gold/README.md`](../bench/gold/README.md) |
| **Zalo test** | Phần test của bộ câu hỏi Zalo AI 2021 trên kho văn bản của Zalo (số câu, kho: mục "Bộ dữ liệu" của sổ thí nghiệm). Chỉnh tham số trên train, đo test một lần. Có rò rỉ train gốc, nên cần cả gold |
| **văn bản thật** | Bộ văn bản ban hành tháng 9 và 10/2026 (phần lớn là scan) với câu hỏi đã kiểm chứng và số Điều thật đếm tay (số liệu: mục "Bộ dữ liệu" của sổ thí nghiệm). Bộ nhỏ nhưng mới hơn mọi mô hình. [`../bench/van-ban-that/KET-QUA.md`](../bench/van-ban-that/KET-QUA.md) |
| **train, test** | Phần chỉnh và phần chấm của mỗi bộ đo. Chỉnh trên train, chấm test một lần ở mã cuối (skill `benchmark-split-hygiene`) |
| **P0 đến P5, nhánh chính xác** | Các giai đoạn của lộ trình; nhánh song song "Độ chính xác tìm kiếm" xen kẽ P1 đến P3. [`ke-hoach/lo-trinh-1.0.md`](ke-hoach/lo-trinh-1.0.md) mục 0 và 6 |
| **cổng** | Điều kiện phải đạt trước khi giữ một thay đổi hay đóng một phase (cổng đo ở [`quy-trinh.md`](quy-trinh.md) mục 4; cổng P1, P3 ở lộ trình) |
| **ngoại lệ có tên** | Chỗ chủ dự án duyệt bằng văn bản cho phép lệch chữ của một luật, ví dụ PS-06 và HT-02 ở sổ thí nghiệm |
| **ghi chú rủi ro, sổ rủi ro, tệp rủi ro** | Ba tên cho ý tưởng chưa duyệt của chủ dự án (31/10/2026; lộ trình mục 9, điều 14). **Ghi chú rủi ro**: ghi chú loại "Rủi ro" gắn vào một đoạn. **Sổ rủi ro**: bảng nhìn các ghi chú rủi ro theo phạm vi dự án. **Tệp rủi ro**: file tóm tắt rủi ro có sẵn của khách (Word hay Excel), dùng làm đầu vào cho phần nạp. [`nghien-cuu/khai-niem-du-an-do-thi-dinh-huong.md`](nghien-cuu/khai-niem-du-an-do-thi-dinh-huong.md) mục 0 |
| **harness** | Mọi thứ giữ chất lượng khi nhiều agent làm song song: luật ngắn, skill, workflow, cổng đo, quy ước commit ([`quy-trinh.md`](quy-trinh.md) mục 1) |
