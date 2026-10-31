# Soi Luật

App tra cứu văn bản pháp luật Việt Nam chạy offline (Python, SQLite FTS5). Tài liệu, commit và PR viết bằng tiếng Việt.

- **Bàn giao**: đọc `GHI-NHO-NGHIEN-CUU.md` trước khi làm tiếp lộ trình, đo lại tìm kiếm hay câu trả lời AI, hoặc chạy job dài.
- **Kế hoạch**: `soi-luat-lo-trinh-1.0.md` (các giai đoạn; quyết định còn mở ở mục 9); khi làm P1 thì theo `soi-luat-ke-hoach-p1.md`.
- **Kiểm tra**: `python -m pytest`.
- **Câu hỏi gold `vle`** không có giấy phép: giữ ngoài repo.

## Quy trình

- **Sai sót → `/autoharness:learn`**: mỗi lần phát hiện mình sai (chạy sai lệnh, giả định thiếu, thiên kiến, kiểm không kỹ, kết luận chủ quan), sửa xong thì gọi `/autoharness:learn` ngay trong lượt đó để bài học thành skill.
- **Viết mã**: `/ponytail:ponytail` (thay đổi nhỏ nhất đủ việc, kèm test).
- **Giao diện**: theo taste-skill (repo `leonxlnx/taste-skill`, `references/app-screens.md`; chưa cài làm skill nên clone vào thư mục riêng và đọc, không chạy script của nó), viết mã theo `/ponytail:ponytail`, kiểm bằng ảnh Playwright (skill `html-mockup-visual-check`).
- **Kế hoạch, kiến trúc, sửa, soát mã**: dùng skill superpowers hợp việc: `brainstorming` và `writing-plans` khi lên kế hoạch; `test-driven-development` khi sửa; `systematic-debugging` khi gặp lỗi; `requesting-code-review` và `receiving-code-review` khi soát; `verification-before-completion` trước khi báo xong.
- **Chia việc cho agent**: việc độc lập chạy song song (`superpowers:dispatching-parallel-agents`, `superpowers:subagent-driven-development`); soát độc lập giao agent chỉ đọc mã, không đọc kết luận của mình. Cân chất lượng với chi phí: tra cứu vài lệnh thì tự làm, mỗi workflow dưới ~10 agent.
