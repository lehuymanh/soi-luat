# Nhật ký thay đổi

## 0.9.0 (31/10/2026)

Bản đầu tiên của lộ trình 1.0 (`docs/ke-hoach/lo-trinh-1.0.md`, giai đoạn P1: mở đúng đoạn, kết quả gọn, lịch sử trò chuyện). Kế hoạch và số đo từng việc: `docs/ke-hoach/ke-hoach-p1.md`.

### Mới

- **Mở văn bản tại đúng đoạn.** Bấm "Mở tại đoạn này": văn bản mở ngay trong app (cột bên phải ở màn rộng, phủ lên ở màn hẹp), cuộn tới đúng khoản/điểm, tô đoạn và chữ khớp, có "Sao chép trích dẫn" (ví dụ "Điểm a khoản 1 Điều 5 Nghị định 15/2020/NĐ-CP"). Tab **Bản gốc** cuộn liên tục ảnh các trang PDF/PNG/JPG, mở ở trang chứa đoạn. Liên kết cũ `/unit/{id}` (thẻ Word đã xuất) vẫn mở được.
- **Kết quả gọn.** Mỗi mục là một Điều, gom theo văn bản; địa chỉ lấy đúng dòng nằm trong phần trích 350 ký tự; Điều giống hệt ở văn bản khác gộp vào "Cũng có ở"; 5 mục đầu rồi "Xem thêm"; "hiệu lực từ" và pill hiệu lực ở đầu nhóm; cảnh báo chữ OCR một lần mỗi nhóm. Gõ số hiệu thì ra "Mở toàn văn".
- **Lịch sử trò chuyện.** Mỗi câu hỏi được lưu; thanh bên có "Cuộc trò chuyện mới" (Alt+N), tìm lại cuộc cũ (khớp không dấu), đổi tên, xoá qua hộp thoại. Mở lại cuộc cũ không phải tìm lại; nguồn đã đổi thì báo và cho "Hỏi lại".
- **Giao diện mới** theo mẫu đã duyệt (thanh bên, một màu nhấn cho chữ khớp và đoạn được dẫn, phông Be Vietnam Pro đóng kèm, không tải gì từ mạng).
- **Đọc văn bản đúng hơn** (parser): giữ đủ điểm nhiều dòng; không nuốt Điều sau dấu ngoặc mở nhầm do OCR; nhận lại đầu Điều OCR hỏng; cắt đúng khối nơi nhận và chữ ký; nội dung Phụ lục sau chữ ký thành đoạn tìm được (một mục mỗi Phụ lục). Dòng số trang lọt vào chữ không còn hiện.
- **Nâng cấp dữ liệu tự động** lần đầu mở 0.9: sao lưu kho ra `data/backup/soiluat-truoc-parse2.db`, rồi chỉ dựng lại văn bản có chữ đổi, chạy nền (thanh bên ghi "Nâng cấp dữ liệu x/y"); vẫn tìm được trong lúc đó.

### Sửa

- Xoá một văn bản trên kho lớn từ 41,5 s còn 0,01 s (bốn chỉ mục khoá ngoại).
- Dựng lại văn bản giữ gợi ý hiệu lực và liên kết đã duyệt (kèm người và ngày duyệt), lỗi giữa chừng thì hoàn lại.
- Ảnh trang PDF tải song song không còn làm sập app (khoá pdfium).
- Lỗi do các lượt soát độc lập tìm ra, mỗi lỗi có test hoặc kịch bản trình duyệt hỏng trên mã cũ: 23 ở trình đọc, kết quả gọn và giao diện; 15 ở nâng cấp dữ liệu; 12 ở lịch sử trò chuyện (một phần nhỏ của 2 điểm giao diện còn chờ chốt).

### Số đo (Normal)

| Bộ | Hit@1 | Hit@5 | Ghi chú |
|---|---|---|---|
| 21 văn bản thật, 84 câu (rộng) | 86,9% | 97,6% | 0.8: 83,3% / 96,4% |
| Zalo test, 788 câu (theo mục) | 61,0% | 86,4% | theo thẻ 0.8: 58,6% / 86,3% |
| Gold, 500 câu (theo mục) | 52,6% | 77,4% | theo thẻ 0.8: 51,2% / 77,0% |

Mở trình đọc trên kho Zalo (3.271 văn bản): p95 27 ms phía máy chủ. Điều tách được trên 21 văn bản thật, đo trên máy Linux của phiên soạn: 345/344 (0.8, cùng máy: 322). Mốc P0 trên Windows là 341/344; hai máy lệch vì bộ chữ `vie` của Tesseract khác nhau (`docs/nghien-cuu/ghi-nho.md` mục 4, bước 5).

### Cài đặt và nâng cấp

- Bộ cài Windows dựng bằng `pack/build.ps1` trên máy Windows (xem README); cài đè lên 0.8 được, kho dữ liệu giữ nguyên và tự nâng cấp lần đầu mở.
- Gói Python (wheel) cho người chạy từ mã nguồn: `pip install soiluat-0.9.0-py3-none-any.whl`.

### Chưa có trong bản này

- Thử với 3–5 người dùng thật và bấm tay trên máy Windows (việc Z1 của kế hoạch).
- Trợ lý trả lời bằng AI (P3), kho văn bản có tag/ghi chú/@ (P2), liên kết văn bản kiểu Obsidian (P4). Bản mẫu khái niệm cho project, ghi chú rủi ro và đồ thị: `mau/khai-niem-du-an-do-thi.html` (chưa duyệt).
