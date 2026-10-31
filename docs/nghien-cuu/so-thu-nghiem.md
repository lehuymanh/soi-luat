# Sổ thử nghiệm của Soi Luật (0.7 đến 0.9.0)

Ghi đến commit `a13af05` (31/10/2026), cho bản 0.9.0. Sổ này kể **đã thử gì, kết quả ra sao, vì sao giữ hay bỏ, và rút ra điều gì** để phiên sau không phải đo lại, không lặp lại thử nghiệm đã thất bại, và biết chỗ nào chưa đo.

Người đọc chính: agent hoặc người làm tiếp lộ trình, đo lại tìm kiếm hay câu trả lời AI, hoặc đổi công nghệ.

## Cách đọc

1. Phần này (định nghĩa), rồi **bảng tổng hợp** ngay dưới để tìm thí nghiệm theo ID.
2. Mục của từng thí nghiệm khi cần chi tiết. Muốn kết luận xuyên suốt: cuối sổ có **"Bài học chung"** và **"Câu hỏi còn mở"**.
3. Trạng thái hiện tại và bước đầu tiên của lượt làm sau nằm ở `docs/nghien-cuu/ghi-nho.md`, không ở đây. Sổ này không thay `KET-QUA.md`: bảng đầy đủ nằm ở nguồn; ở đây chỉ chép số cần để quyết định, kèm chỗ tra. Khi hai nơi lệch nhau, nguồn đúng.

## Mã thí nghiệm

`Nhóm-số`, ví dụ `TK-03`. Mã không đánh lại; thí nghiệm mới thêm cuối nhóm. Mã việc của kế hoạch P1 (N0, N1a, N3, K1, R2, H3...) giữ nguyên nghĩa ở `docs/ke-hoach/ke-hoach-p1.md` và được nhắc trong phần "Nguồn".

| Nhóm | Nội dung |
|---|---|
| TK | Tìm kiếm: BM25, vector, reranker, Normal và Advance trên Zalo, gold, văn bản thật |
| PS | Nạp file, OCR, parser, nâng cấp dữ liệu |
| LM | Câu trả lời bằng LLM: bộ đo, vòng 1, vòng 2, bảy việc sửa |
| CN | Chọn công nghệ: mô hình ngôn ngữ, kho dữ liệu, framework đồ thị |
| HT | Kết quả gọn, trình đọc, lịch sử trò chuyện (P1) |
| GD | Giao diện mẫu |
| SO | Các đợt soát độc lập |

## Quyết định

| Nhãn | Nghĩa |
|---|---|
| **giữ** | Đang dùng trong mã hoặc là quyết định hiện hành. Muốn đổi phải có số đo mới. |
| **bỏ** | Đã thử xong và không dùng, hoặc đã dùng rồi gỡ. Chỉ thử lại khi điều kiện đổi (nêu ở mục). |
| **hoãn** | Chưa đủ bằng chứng, hoặc thiếu máy hay người. Mục ghi điều kiện để làm lại. |
| mốc | Đo để làm chuẩn so sánh, không đổi mã. |
| đã sửa | Dùng cho đợt soát: phát hiện còn đứng đã được sửa, mỗi lỗi có test hỏng trên mã cũ. |

## Tiêu chí giữ (quy tắc 7)

Nguồn: `docs/ke-hoach/lo-trinh-1.0.md` mục 5, điều 7; `bench/gold/README.md`. **Thay đổi phần tìm chỉ được giữ khi tốt hơn trên cả Zalo lẫn gold `vle` và không tụt trên văn bản thật.** Thay đổi phần trả lời phải qua `bench/llm`. Hai ngoại lệ đã được chủ dự án duyệt bằng văn bản ngày 31/10/2026 và ghi tên ở PS-06 (bản sửa parser điểm nhiều dòng, giữ có điều kiện) và HT-02 (cách tính "Hit theo mục", theo bộ). Quy tắc sinh ra từ TK-06: Zalo một mình không đủ.

## Bộ dữ liệu

| Bộ | Là gì | n | Ghi chú |
|---|---|---|---|
| **Zalo test** | `GreenNode/zalo-ai-legal-text-retrieval-vn` (MIT): 61.425 Điều thuộc 3.271 văn bản, kho 427.351 đơn vị | 788 câu test; 2.432 câu train | Chỉnh tham số trên train, đo test một lần. 788 câu test nằm trong tập train gốc của Zalo 2021 (TK-06). |
| **Gold `vle`** | ViLegalExperts (tư vấn luật thật), ánh xạ vào kho Zalo | 500 câu (35.505 câu lọc còn 5.437, lấy ngẫu nhiên, hạt giống 2026) | Chưa có giấy phép: giữ ngoài repo; `bench/zalo/ket_qua_gold*.json` bị `.gitignore`. Chỉ có một tập, chỉ để chấm. |
| **Văn bản thật** | 21 văn bản ban hành tháng 9–10/2026 (9 Luật, 6 Nghị định, 5 Thông tư, 1 Quyết định), 443 trang, 18 bản scan, 3 có lớp chữ; 344 Điều thật | 84 câu (4 câu mỗi văn bản: 2 từ khoá, 2 câu hỏi đời thường) | Đáp án có Điều, trang, câu trích. Vừa dùng tìm lỗi parser vừa dùng đo (TK-09). |
| Kho sinh tự động (demo 0.7) | 300 văn bản, mở rộng thành 1.762 (133.425 đơn vị); 18 file "bẩn" | 268 truy vấn; 22 kỳ vọng file bẩn | Dữ liệu sinh: chỉ cho hồi quy và hiệu năng (PS-01). |
| stress10 | 10 file lệch cấu trúc | 20 truy vấn | Hồi quy (PS-02). |
| Mẫu của `bench/llm` | Rút từ ba bộ trên, hạt giống 2026 | Test: Zalo 30 câu và 20 bẫy, gold 20, văn bản thật 15. Train: tối đa 12 cộng 6 bẫy (Zalo) và 6 (văn bản thật) ở A/B | Phần chỉnh (train) tách khỏi phần chấm (test) bằng `pick_sample`. Câu bẫy sinh từ cả kho nên rò rỉ giữa hai phần (LM-07). |

## Quy ước đọc số

- **Hit@k:** đúng khi Điều đáp án nằm trong k kết quả đầu, gom theo Điều. MRR@10: trung bình nghịch đảo hạng. Hạng tính theo **thẻ** (một thẻ mỗi đơn vị khớp) hoặc theo **mục** hiển thị (một mục mỗi (văn bản, Điều), HT-02).
- **Văn bản thật:** "rộng" tính đúng khi thẻ cùng file và đúng Điều hoặc trang của thẻ chứa câu trích; "chặt" đòi đúng số Điều.
- **Normal** là BM25 (FTS5). **Advance** là BM25 cộng vector theo nghĩa cộng reranker. Trước ngày 28/10/2026 Advance dùng EmbeddingGemma 300M (TK-03); từ đó dùng AITeamVN (TK-07). Mốc P0 của văn bản thật (TK-09) đo bản AITeamVN.
- **Chỉ số câu trả lời LLM** (dẫn đúng, khẳng định sai, từ chối hẳn, bị cắt...): định nghĩa ở `docs/nghien-cuu/ghi-nho.md` mục 3.1; không chép lại. Cỡ mẫu 15–30 câu mỗi bộ nên khoảng tin cậy 95% xấu nhất là ±18–25 điểm.
- **Số thập phân dùng dấu phẩy.** Mỗi số kèm bộ và n; chỗ nào thiếu thì mục ghi "chưa đo" hoặc "không ghi". **Ước tính** (không đo) luôn được gọi đúng tên.
- Thời gian đo trên máy ảo Linux 4 nhân dùng chung **không dùng được cho cổng 45 giây**; chỉ tỉ lệ chất lượng là dùng được. Chưa có số nào trên máy 16 GB Windows của người dùng (CN-02).

## Nguồn viết tắt

Đường dẫn tính từ gốc repo. Bảng tổng hợp bên dưới dùng viết tắt; phần "Nguồn" trong từng mục ghi đường dẫn đầy đủ kèm tên mục.

| Viết tắt | Tệp |
|---|---|
| `zalo` | `bench/zalo/KET-QUA.md` |
| `gold` | `bench/gold/KET-QUA.md` (và `bench/gold/README.md`) |
| `vbt` | `bench/van-ban-that/KET-QUA.md` |
| `llm` | `bench/llm/KET-QUA.md` |
| `mh` | `docs/nghien-cuu/chon-mo-hinh.md` |
| `csdl` | `docs/nghien-cuu/chon-csdl.md` |
| `demo` | `bench/BAO-CAO-DEMO.md` |
| `stress` | `bench/stress10/KET-QUA.md` |
| `kt` | `docs/kien-truc.md` |
| `kt0` | `docs/kien-truc.md` bản trước commit `6f39851` (viết lại ở 0.9.0; đọc bằng `git show 6f39851^:docs/kien-truc.md`) |
| `kh1` | `docs/ke-hoach/ke-hoach-p1.md` |
| `lt` | `docs/ke-hoach/lo-trinh-1.0.md` |
| `gn` | `docs/nghien-cuu/ghi-nho.md` |
| `mau` | `mau/` (`giao-dien-1.0.html`, `khai-niem-du-an-do-thi.html`; bản định hướng `khai-niem-du-an-do-thi-dinh-huong.md` đã chuyển sang `docs/nghien-cuu/`) |

Mã bảy ký tự hex (ví dụ `8197efd`) là commit trong lịch sử git của repo (`git show 8197efd`).

## Bảng tổng hợp

Ngày là năm 2026. Kết quả một dòng kèm bộ và n; chi tiết ở mục tương ứng.

| ID | Ngày | Câu hỏi | Kết quả một dòng | Quyết định | Nguồn |
|---|---|---|---|---|---|
| TK-01 | 22/10 | Đưa nguyên câu hỏi vào BM25 OR có hơn thang tầng AND không? | Hit@10 54,7% lên 88,5%, Hit@1 26,1% lên 52,9% (Zalo test, n = 788); p50 190 lên 962 ms | giữ | `zalo`, `8197efd` |
| TK-02 | 22/10 | Cộng điểm cặp âm tiết có tăng Hit@1 không? | Hit@1 52,9% lên 58,9%, Hit@10 88,5% lên 90,2% (Zalo test, n = 788); không đạt top 5 = 90% | giữ | `zalo`, `8197efd` |
| TK-03 | 22/10 | EmbeddingGemma xếp lại top 20 có đáng bật Advance không? | Hit@1 58,9% lên 60,2%, Hit@10 90,2% lên 91,9% (Zalo test, n = 788); RAM đỉnh 78 lên 1300 MB | bỏ (thay bằng TK-07) | `zalo`, `8197efd` |
| TK-04 | 22/10 | Mô hình tĩnh potion có thay được mô hình theo ngữ cảnh không? | Hit@1 46,6% so với 58,9% của BM25 (Zalo test, n = 788) | bỏ | `zalo`, `8197efd` |
| TK-05 | 23/10 | Thêm 20 Điều từ vector toàn kho có cứu ghi chú không chung chữ không? | Ghi chú tìm ra 0/6 lên 6/6 (5/6 sau ngưỡng); Hit@10 91,9% lên 92,5% (Zalo test, n = 788) | giữ (có ngưỡng) | `zalo`, `vbt`, `69f3734` |
| TK-06 | 27/10 | Zalo test có rò rỉ train không, có tập thứ hai không? | 788/788 câu test nằm trong train gốc; dựng gold `vle` n = 500 | giữ (thành quy tắc 7) | `gold`, `3dd903c` |
| TK-07 | 28/10 | AITeamVN cộng reranker có đạt Hit@1 90% không? | Hit@1 74,1% (Zalo test, n = 788) và 79,2% (gold, n = 500); không đạt 90% | giữ | `kt0` 5.1, `45e58f0`, `2f133e5` |
| TK-08 | 28–29/10 | Những thêm thắt nào cho Advance không đáng giữ? | Reranker top-10 hơn 0,5–1,8 điểm Hit@1 nhưng chậm gấp đôi; ba phương án khác không có số trong repo | bỏ | `kt0` 5.3 |
| TK-09 | 22/10 đến 30/10 | Advance có hơn Normal trên văn bản mới không? | Hit@1 rộng Normal 83,3% so với Advance 72,6% (văn bản thật, n = 84); ngược với Zalo và gold | giữ Normal làm mặc định (đề xuất, chốt còn mở) | `vbt`, `lt` mục 9, `7060f61` |
| PS-01 | 21/10 | Bản 0.7 chịu được file bẩn và kho lớn không? | File bẩn nạp 12/18 lên 18/18; kho 1.762 văn bản p50 930 lên 88 ms (kho sinh tự động) | giữ (các sửa) | `demo`, `8197efd` |
| PS-02 | 21/10 | File lệch cấu trúc có nạp và tìm được không? | 10/10 file nạp, 19/20 truy vấn đúng (stress10); sau TK-01: 20/20 | giữ (hồi quy) | `stress` |
| PS-03 | 22–23/10 | Parser và siêu dữ liệu có đúng trên scan thật không? | Điều đúng 259/344 lên 341/344; cơ quan ban hành 6/21 lên 21/21 (21 văn bản thật) | giữ | `vbt`, `8197efd` |
| PS-04 | 22–31/10 | Có phải thay bộ OCR không? | OCR giống 98,5% ký tự (84 câu trích); tách Điều đúng 341/344 | giữ Tesseract | `vbt`, `lt` mục 2 |
| PS-05 | 31/10 | Vì sao xoá văn bản chậm? | Xoá 89 đơn vị 41,5 s xuống 0,01 s (bản sao kho Zalo) | giữ | `kh1` N0, `ba7f1c3` |
| PS-06 | 31/10 | Sửa parser điểm nhiều dòng có làm tụt tìm kiếm không? | Zalo Hit@1 464 lên 462 trên 788; gold 254 lên 256 trên 500; văn bản thật @3 94,0% xuống 91,7% (n = 84); điểm cắt giữa câu 795 xuống 113 | giữ (ngoại lệ có điều kiện) | `kh1` 2b, `ba7f1c3` |
| PS-07 | 31/10 | Nâng parser theo hướng nào, và chọn ý chính thế nào? | B1 + B2 + B3: Điều 322 lên 345/344, rộng @1 86,9% (văn bản thật, n = 84); ý chính trích đúng số sai đối tượng | giữ B1 + B2 + B3; ý chính sang P2 | `kh1` N3, `ea122bb` |
| PS-08 | 31/10 | Gộp thẻ Phụ lục có làm mất kết quả không? | Câu "bốc xếp" mất khi trang thẻ chỉ là trang đoạn đầu; sửa bằng khoảng trang | giữ (bản đã sửa) | `kh1` N3, `ea122bb` |
| PS-09 | 31/10 | Nâng cấp kho cũ lên parser mới an toàn và nhanh thế nào? | 21 văn bản thật 5,6 s; Zalo 1.760 trên 3.271 văn bản dựng lại, 467 s, sao lưu 1,4 GB | giữ | `kh1` N1b, `e03a136` |
| PS-10 | 31/10 | Dựng lại có làm mất gợi ý hiệu lực đã duyệt không? | Có (lỗi từ 0.8); sửa kèm `rollback`, test hỏng trên mã cũ | giữ | `kh1` N1c, `ba7f1c3` |
| LM-01 | 30/10 | Qwen3-VL-4B đạt cổng P0 chưa (vòng 1)? | Dẫn đúng 66,7 / 70,0 / 46,7%; mọi JSON hỏng do cắt ở 200 token (Zalo n = 30, gold n = 20, văn bản thật n = 15) | mốc (chưa đạt, làm 7 việc sửa) | `llm`, `9d4b7c7` |
| LM-02 | 30/10 | Làm sao dòng đáp án khỏi bị cắt khỏi ngữ cảnh? | Câu trích còn ≥ 50% trong đoạn: 53% lên 80% (train văn bản thật, n = 66, offline) | giữ | `llm`, `7aec13f` |
| LM-03 | 30/10 | Làm sao JSON hết hỏng khi bị cắt? | Đọc được sau cứu 100%; nhưng 17/20 câu bẫy vẫn bị cắt, 15 mất hết ý có nguồn (Zalo test) | giữ (câu bẫy còn mở) | `llm`, `7aec13f` |
| LM-04 | 30/10 | Trường `pham_vi` có giảm khẳng định sai không? | Khẳng định sai 5/12 so với 7/12 và 8/12 (A/B train Zalo, n = 12) | giữ | `llm`, `b17461f` |
| LM-05 | 30/10 | Chặn chữ CJK ngay khi sinh được không? | CJK 3,8 / 10,0 / 0% xuống 0% (test: Zalo n = 30, gold n = 20, văn bản thật n = 15); tốc độ không đổi | giữ | `llm`, `7aec13f` |
| LM-06 | 30/10 | Nới bộ kiểm tham chiếu có cứu được ý đúng không? | Dẫn đúng sau kiểm 20 lên 23/30, 12 lên 16/20, 7 lên 8/15 (chẩn đoán trên câu trả lời vòng 1) | giữ | `llm`, `7aec13f` |
| LM-07 | 30/10 | Sau bảy việc sửa Qwen đạt cổng chưa (vòng 2)? | Dẫn đúng 83,3 / 75,0 / 86,7%; khẳng định sai 26,7 / 40,0 / 13,3%; cổng đạt 2/3 bộ | mốc (cách tính cổng chờ chủ dự án) | `llm`, `b17461f` |
| LM-08 | kế hoạch | Sửa parser đổi chất lượng câu trả lời thế nào (B1)? | Chưa đo | hoãn | `kh1` B1 |
| CN-01 | 29/10 | Chọn mô hình ngôn ngữ nào theo benchmark công khai? | SEA-HELM tiếng Việt, không suy nghĩ: Qwen3-VL-4B 64,2; Gemma 4 E4B 62,8; Qwen3.5-4B 52,2 | giữ Qwen, dự phòng Gemma; bỏ Qwen3.5-4B | `mh`, `bc540db` |
| CN-02 | 29–30/10 | Mô hình 4B có vừa 45 giây trên máy 16 GB không? | Ước tính trung tâm 53 s (prompt 1.500 token); tốc độ trên máy 16 GB chưa đo | hoãn (cần máy 16 GB) | `mh` mục 4 |
| CN-03 | 30/10 | Gemma 4 E4B hay Bolt hơn Qwen không? | Dẫn đúng gộp 53 / 48 / 44 trên 65; McNemar p = 0,30 và 0,06 (chưa vượt nhiễu) | giữ Qwen | `llm`, `3d4c0d5`, `0ed2ed6` |
| CN-04 | 30/10 | Có mô hình mới nào sửa được lỗi phạm vi bằng tiếng Việt không? | Không thấy; Bolt kém Qwen và Gemma khi gộp | bỏ (không chọn Bolt) | `mh` mục 7 |
| CN-05 | 29/10 | Có cần CSDL hay bộ máy truy hồi khác không? | Phần CSDL tối đa khoảng 1 s trong khoảng 9 s của một câu Advance | giữ SQLite + FTS5 | `csdl`, `2c2239a` |
| CN-06 | 29/10 | Giữ vector thế nào khi số vector tăng? | 250.000 vector: NumPy f32 77,0 ms và 977 MB; USearch f16 118 ms và 488 MB; sqlite-vec chậm 6–7 lần | giữ NumPy; USearch f16 khi trên khoảng 500 MB (hoãn) | `csdl` mục 5, 6 |
| CN-07 | 29/10 | Có nên dùng framework đồ thị tri thức dựng bằng LLM không? | Ước tính dựng 61.425 Điều: sàn 5,2 ngày, Cognee khoảng 23, Graphiti 175 đến 360 ngày | bỏ | `csdl` mục 4.4, 4.5 |
| HT-01 | 31/10 | Danh sách khoảng 40 thẻ có xuống 5 mục không mất đáp án? | 39,8 mục mỗi câu, 5 mục đầu từ 2,44 văn bản, 0 mục gộp (văn bản thật, n = 84) | giữ | `kh1` K1, `01170bf` |
| HT-02 | 31/10 | Hit@k theo mục hiển thị có thấp hơn mốc theo thẻ không? | Zalo @1 58,6% lên 61,0% (n = 788); gold @1 51,2% lên 52,6% (n = 500); cổng đạt | giữ | `zalo`, `gold`, `vbt` (mục K3), `fb01c53` |
| HT-03 | 31/10 | Trình đọc có mở đúng đoạn, trong 1 giây không? | p95 27 ms, lớn nhất 121 ms (bản sao Zalo, 101 văn bản); trình duyệt vẽ chưa đo | giữ | `kh1` R1 đến R3, `48a468e` |
| HT-04 | 31/10 | Mở lại cuộc trò chuyện không tìm lại có đủ nhanh không? | Cuộc 10 câu dựng đủ trung vị 2,41 s, sau "Xem lại" 713 ms | giữ (kèm "Xem lại") | `kh1` H3, `f27115c` |
| HT-05 | 31/10 | Có ghi lượt mở trích dẫn để chỉnh `SURE_GAP` ở P1 không? | `gap` NULL ở Normal; vài chục lượt mở không đủ chỉnh một ngưỡng | hoãn | `kh1` H5 |
| GD-01 | 30/10 | Mẫu giao diện thế hệ 1 có đủ để duyệt không? | Chủ dự án báo không dùng được (31/10); lý do cụ thể chưa ghi | bỏ | `mau`, `2f0f018` |
| GD-02 | 31/10 | Mẫu dựng lại theo taste-skill có được duyệt không? | 25 trạng thái Playwright 0 lỗi console, 0 cuộn ngang; 47 phát hiện soát đã sửa; được duyệt 31/10 | giữ | `mau`, `ad6e8e2`, `c6b5fef` |
| GD-03 | 31/10 | Bản khái niệm dự án, sổ rủi ro, đồ thị trông thế nào? | Bản định hướng 666 dòng cộng bản bấm thử; còn mở trên kho thật | hoãn (chưa duyệt) | `mau`, `5226a73` |
| SO-01 | 30/10 | Lõi trả lời và bộ đo còn lỗi gì (trước vòng 1)? | 9 lỗi (bộ kiểm số, đọc số, ngữ cảnh, bộ đo im lặng đổi chế độ) | đã sửa | `120eea8` |
| SO-02 | 30/10 | Còn lỗi gì sau bảy việc sửa? | 6/15 phát hiện thật ("mười năm" thành 15; câu khớp dài bị bỏ); một bản sửa gây hồi quy 80% xuống 71% | đã sửa | `llm`, `131ca78` |
| SO-03 | 31/10 | Soát ponytail còn lỗi gì? | 23 phát hiện, 9 bị bác, 14 còn đứng ("QH15" lọt số 5; dòng độn chiếm chỗ) | đã sửa | `gn` 3.5, `bc9f9af` |
| SO-04 | 31/10 | Mẫu giao diện thế hệ 2 còn lỗi gì? | 47 phát hiện (mẫu hứa phần P2, P3; bàn phím, focus; logic) | đã sửa | `9e5cf35` |
| SO-05 | 31/10 | Kế hoạch P1 lệch mã ở đâu? | 56 phát hiện còn đứng, không phát hiện nào bị bỏ; 5 người tìm, 5 người bác | đã sửa | `kh1`, `5e4df66` |
| SO-06 | 31/10 | R2a đến K2 còn lỗi gì? | 23 lỗi (logic, pdfium đa luồng hỏng 3/3, bàn phím), mỗi lỗi có test hỏng trên mã cũ | đã sửa | `db4eb27` |
| SO-07 | 31/10 | Nhóm lịch sử trò chuyện còn lỗi gì? | 12 phát hiện (D1 đến D4, UX-1 đến UX-8); 9 test và 12 kịch bản Playwright hỏng trên mã cũ | đã sửa | `eac8ebb` |
| SO-08 | 31/10 | Toàn repo còn lỗi "phải sửa" nào? | C1, C2, C3, SEC-1, F2 rồi đợt dọn; "thời hạn" kèm Thông tư 4 so với 63 kết quả | đã sửa (C8, F10 hoãn) | `50b3622`, `9780468` |

## Nhóm TK: tìm kiếm

### TK-01 · BM25 OR thay thang tầng AND (22/10/2026)

- **Câu hỏi:** vì sao Hit@10 chỉ 54,7%, và đưa nguyên câu hỏi vào BM25 OR của FTS5 có hơn thang tầng AND không?
- **Giả thuyết:** thang tầng dừng ở tầng đầu có kết quả và khoá xếp thẻ đẩy Điều đúng xuống. BM25 tự hạ trọng số từ phổ biến nên không cần danh sách từ bỏ viết tay.
- **Cách làm:** Zalo test (n = 788), kho 61.425 Điều (427.351 đơn vị). Đúng khi Điều đáp án nằm trong 10 kết quả đầu. So cách cũ (rút câu hỏi, 6 tầng AND, xếp thẻ) với năm biến thể BM25 OR. Chẩn đoán trượt trên mẫu 120 câu (`bench/zalo/why_miss.py`). Lệnh: `python bench/zalo/eval.py <zalo> <data> test`.
- **Kết quả** (Zalo test, n = 788):

  | Cách | Hit@10 | Hit@1 | MRR@10 | 0 kết quả | p50 / p95 |
  |---|---|---|---|---|---|
  | Cũ (rút câu hỏi + 6 tầng AND + xếp thẻ) | 54,7 | 26,1 | 0,348 | 7,5% | 190 / 404 ms |
  | BM25 OR, cột có dấu | 84,9 | chưa đo | 0,603 | 0% | 398 / 677 ms |
  | BM25 OR, bỏ từ có ở > 20% đơn vị | 83,9 | chưa đo | 0,589 | 0% | 183 / 320 ms |
  | BM25 OR, bỏ từ > 35% | 84,6 | chưa đo | 0,601 | 0% | 317 / 550 ms |
  | BM25 OR, không dấu | 77,7 | chưa đo | 0,558 | 0% | 464 / 747 ms |
  | BM25 OR, có dấu + ngữ cảnh khoản cha | 86,9 | 53,4 | 0,657 | 0% | 477 / 786 ms |
  | Đường thật của app sau khi chuyển | 88,5 | 52,9 | 0,661 | 0% | 962 / 1622 ms |

  Chồng lấn giữa cách cũ và BM25 có ngữ cảnh: cả hai trúng 419 câu, chỉ BM25 trúng 266, chỉ cách cũ trúng 12, cả hai trượt 91. Trên tập train (n không ghi trong nguồn), bỏ `strip_question` tăng độ chính xác 0,800 lên 0,842.
- **Quyết định:** giữ BM25 OR có dấu kèm ngữ cảnh. App chuyển hẳn, bỏ `strip_question`.
- **Vì sao cách cũ thất bại** (mẫu 120 câu, trượt 54): 38 câu do thang tầng dừng ở tầng đầu có kết quả mà tầng đó không chứa Điều đúng, 9 câu do khoá xếp thẻ đẩy Điều đúng xuống hạng 13–31, 7 câu ra 0 kết quả (viết tắt, câu dài). **Vì sao giữ:** Hit@10 tăng từ 54,7% lên 88,5%, Hit@1 tăng gấp đôi, hết 0 kết quả. Cái giá: p50 190 ms lên 962 ms (kho Zalo lớn, kho nhỏ chưa đo lúc đó).
- **Bài học:** (1) Luật viết tay (danh sách từ bỏ, thang AND) thua công cụ xếp hạng chuẩn; chỉ đo trên câu hỏi thật mới lộ. (2) Bỏ dấu làm mất 7,2 điểm Hit@10 (84,9% so với 77,7%), nên giữ hai cột có dấu và không dấu. (3) 91 câu cả hai cách trượt là câu khác chữ ("quán karaoke" và "kinh doanh dịch vụ karaoke"): giới hạn của tìm theo chữ, chỉ vector hoặc từ điển đồng nghĩa gỡ được (xem TK-03). (4) Phát hiện phụ: `units_vocab` tạo thiếu cột nên `search._token_df` luôn lỗi và rơi vào nhánh đếm bằng `MATCH`; kết quả vẫn đúng nên test không bắt được, chỉ chậm. Lỗi bị nhánh dự phòng nuốt chỉ lộ khi đo thời gian.
- **Nguồn:** `bench/zalo/KET-QUA.md` mục "Kết quả (788 câu)", "Vì sao cách hiện tại trượt", "Phát hiện phụ", "Sau khi chuyển app sang BM25 OR"; commit `8197efd`.

### TK-02 · Cộng điểm cặp âm tiết (22/10/2026)

- **Câu hỏi:** nhân thêm điểm theo tỉ lệ cặp âm tiết liền nhau của câu hỏi có trong đơn vị thì Hit@1 có tăng không?
- **Giả thuyết:** không ghi trước. Suy ra từ mục tiêu "top 5 đạt 90%": khớp cụm là tín hiệu mạnh mà BM25 theo từ đơn không có.
- **Cách làm:** điểm mỗi ứng viên nhân `1 + 2,0 × tỉ lệ cặp âm tiết`; trọng số cột ngữ cảnh 0,3 lên 0,5. Chọn hệ số trên 300 câu train (Hit@10 0,867 lên 0,910), rồi đo một lần trên Zalo test (n = 788).
- **Kết quả** (Zalo test, n = 788), trước và sau: Hit@1 52,9% lên 58,9%; Hit@3 78,2% lên 82,0%; Hit@5 83,4% lên 86,2%; Hit@10 88,5% lên 90,2%; MRR@10 0,661 lên 0,709; p50 / p95 962 / 1622 ms đổi thành 975 / 1614 ms.
- **Quyết định:** giữ. Không đạt mục tiêu "top 5 = 90%" (86,2%).
- **Vì sao giữ:** Hit@1 tăng 6,0 điểm, không tốn thời gian. **Bài học:** mức tăng trên tập chỉnh (+4,3 điểm Hit@10, train n = 300) lớn gấp hơn hai lần mức tăng trên test (+1,7 điểm, n = 788); hai tập khác nhau nhưng đủ để nhắc rằng số trên tập chỉnh bị thổi phồng. Chỉnh trên train, báo số test.
- **Nguồn:** `bench/zalo/KET-QUA.md` mục "Thêm cộng điểm cặp âm tiết"; commit `8197efd`.

### TK-03 · EmbeddingGemma 300M xếp lại top 20 (22/10/2026)

- **Câu hỏi:** xếp lại 20 Điều đầu của BM25 bằng vector theo nghĩa (RRF) có tăng đủ để bật chế độ Advance không?
- **Giả thuyết:** câu hỏi đời thường ít trùng chữ với văn bản, nên phần nghĩa bù được chỗ BM25 trượt (TK-01, 91 câu khác chữ).
- **Cách làm:** `onnx-community/embeddinggemma-300m-ONNX` int8 (295 MB), onnxruntime CPU. Bước 1, ngoài app: chỉ nhúng 15.710 Điều nằm trong 30 kết quả đầu của BM25 cho 988 câu (nhúng cả kho quá lâu), RRF hạng BM25 và hạng nghĩa, tham số chọn trên 200 câu train (top 20, w = 1, k = 5). Bước 2, trong app (`src/soiluat/semantic.py`): nhúng 9.047 Điều mà bước xếp lại chạm tới cho 788 câu test, đo đầu-cuối qua `eval.py` và qua Search App thật bằng HTTP (60 câu, `bench/zalo/app_ram.py`). Bước 3: cắt 128 token thay vì 256.
- **Kết quả** (Zalo test, n = 788):

  | | BM25 (app) | Thử ngoài app | Trong app, 256 token | Trong app, 128 token (chốt) |
  |---|---|---|---|---|
  | Hit@1 | 58,9 | 62,3 | 60,5 | 60,2 |
  | Hit@3 | 82,0 | 83,9 | 83,0 | 83,5 |
  | Hit@5 | 86,2 | 89,2 | 89,1 | 89,1 |
  | Hit@10 | 90,2 | 92,3 | 91,8 | 91,9 |

  Trong app (256 token), từng câu: 128 câu lên hạng, 110 câu xuống hạng; 33 câu vào top 5, 10 câu rơi khỏi top 5. Chi phí: nhúng 2,29 Điều/s (256 token) và 4,51 Điều/s (128 token) ở 2 luồng; Search App (60 câu) RAM đỉnh 78 MB lên 1300 MB, câu đầu 3,2 s lên 6,5 s, p50 1118 ms lên 1471 ms. Chốt ngày 22/10 (n = 788): MRR@10 0,709 (Normal) và 0,722 (Advance).
- **Quyết định:** giữ lúc đó làm Advance (128 token, `semantic.MAXLEN = 128`). Sau đó **bỏ**: thay bằng AITeamVN (TK-07); `kt0` mục 5.3 ghi EmbeddingGemma kém AITeamVN trên bộ đo.
- **Vì sao chỉ là bước đệm:** mức tăng nhỏ (Hit@1 +1,3, Hit@10 +1,7 điểm), RAM đỉnh của Search App từ 78 MB lên 1300 MB, giấy phép Gemma không phải MIT hay Apache. **Bài học:** (1) số thử ngoài app (62,3% Hit@1) lạc quan hơn số đầu-cuối qua app (60,5%); luôn chốt bằng đo qua đường thật. (2) Mức tăng ròng che số câu tụt: 110 câu xuống hạng so với 128 câu lên; báo cả hai. (3) Cắt 128 token cho độ chính xác như 256 mà nhanh gấp đôi, nên thử cắt ngắn trước khi mua phần cứng. (4) Độ trễ câu đầu dao động mạnh theo cache ổ đĩa (4 lần đo Normal: 3,2 / 5,9 / 17,1 / 17,9 s); chỉ so độ trễ từ câu thứ hai.
- **Nguồn:** `bench/zalo/KET-QUA.md` mục "Thử nghiệm EmbeddingGemma", "EmbeddingGemma trong app", "EmbeddingGemma cắt 128 token", "Chốt (22/10/2026...)"; commit `8197efd`.

### TK-04 · Mô hình tĩnh potion-multilingual-128M (22/10/2026)

- **Câu hỏi:** mô hình tĩnh (tra bảng từ rồi lấy trung bình, không chạy mạng nơ-ron) có thay EmbeddingGemma để xếp lại cho nhanh, nhẹ không?
- **Giả thuyết:** nhanh gấp hàng trăm lần nên có thể nhúng cả kho trong vài phút; chất lượng chưa biết.
- **Cách làm:** `minishlab/potion-multilingual-128M` (MIT, model2vec), cùng cách xếp lại như TK-03, tham số chọn trên 200 câu train, đo trên Zalo test (n = 788).
- **Kết quả** (Zalo test, n = 788), BM25 / BM25 + EmbeddingGemma / BM25 + potion: Hit@1 58,9 / 62,3 / **46,6**; Hit@3 82,0 / 83,9 / 73,0; Hit@5 86,2 / 89,2 / 84,1; Hit@10 90,2 / 92,3 / 90,1. Tốc độ 3.053 Điều/s, một câu hỏi 0,7 ms; nạp mô hình 11,5 s, RAM thêm 1,1 GB (bảng từ 500.353 × 256 số float32).
- **Quyết định:** bỏ.
- **Vì sao thất bại:** xếp lại làm kết quả tệ đi, không tốt lên (Hit@1 thấp hơn BM25 một mình 12,3 điểm), và còn tốn RAM. Giải thích (suy luận, chưa kiểm): trung bình các vector từ làm mất thứ tự từ. **Bài học:** nhanh không bù được kém; đo chất lượng và tài nguyên cùng lúc. Mô hình tĩnh không thay được mô hình theo ngữ cảnh ở bước xếp lại.
- **Nguồn:** `bench/zalo/KET-QUA.md` mục "Thử mô hình tĩnh potion-multilingual-128M"; commit `8197efd`.

### TK-05 · Thêm 20 Điều từ vector toàn kho và ngưỡng cosine (23/10/2026)

- **Câu hỏi:** văn bản không chung chữ nào với câu hỏi (ghi chú viết tự do) có tìm được không? Xếp lại chỉ đụng 20 Điều BM25 đã tìm, nên không bao giờ ra.
- **Giả thuyết:** thêm 20 Điều gần nghĩa nhất toàn kho, chen sau, không xáo thứ tự BM25, sẽ cứu được ghi chú mà không làm tụt hạng đầu.
- **Cách làm:** `semantic.DENSE_K = 20`. Zalo test (n = 788) trên kho nhúng đủ 61.361 Điều (3 giờ 22 phút, 4,3 Điều/s). Kho 21 văn bản thật cộng 6 ghi chú tự viết, mỗi ghi chú cùng chủ đề một văn bản thật; câu hỏi kiểm bằng máy là không trùng âm tiết nào với ghi chú (6 câu). Ngưỡng `DENSE_MIN` chọn từ cosine cao nhất toàn kho: 15 câu vô nghĩa 0,27–0,47; Điều đáp án của 784 câu thật có p5 / p10 / p50 = 0,51 / 0,54 / 0,65.
- **Kết quả:** Zalo test (n = 788) Hit@10 91,9% lên 92,5%, Hit@1 / @3 / @5 không đổi; 6 câu tốt hơn, 6 câu kém hơn. Văn bản thật (n = 84, rộng) @5 / @10 96,4% lên 97,6%. Ghi chú tìm ra 0 trên 6 lên 6 trên 6 (hạng 7, 8, 8, 8, 15, 21); sau ngưỡng 0,50: 5 trên 6. Chi phí: thêm khoảng 65 MB RAM thường trực, đỉnh Search App 1304 MB lên 1370 MB; nạp ma trận 6,10 s (ổ đĩa chưa cache) hoặc 0,4 s.
- **Quyết định:** giữ, có ngưỡng. Hằng số hiện hành (`DENSE_K`, `DENSE_MIN`) ghi ở `docs/kien-truc.md` mục 7.7, vì sau TK-07 chúng đổi.
- **Vì sao bản đầu thất bại:** bản đầu tính chung hạng theo nghĩa cho cả hai nhóm làm xáo thứ tự top 20; Hit@1 rộng văn bản thật tụt 73,8% xuống 69,0% (n = 84). Đổi sang "chỉ thêm, không xáo" thì hết tụt. Không có ngưỡng thì câu vô nghĩa ("?", "qwzx plokm vbnrt") vẫn nhận đủ 20 thẻ không liên quan thay vì "Không tìm thấy".
- **Bài học:** (1) Thay đổi chỉ-thêm an toàn hơn thay đổi xáo trộn thứ hạng. (2) Mọi ngưỡng cần một bộ câu âm tính (câu vô nghĩa) để đặt. (3) Ghi chú tự viết chỉ 6 câu là minh hoạ, không phải số đo thống kê.
- **Nguồn:** `bench/zalo/KET-QUA.md` mục "Thêm 20 Điều từ vector toàn kho ở Advance"; `bench/van-ban-that/KET-QUA.md` mục "Ghi chú viết tự do và ứng viên từ vector"; commit `69f3734`, `8197efd`.

### TK-06 · Rò rỉ dữ liệu Zalo và dựng bộ gold `vle` (27/10/2026)

- **Câu hỏi:** 788 câu test Zalo có trùng dữ liệu huấn luyện không, và có tập thứ hai độc lập để đo không?
- **Giả thuyết:** không ghi trước; nghi vì mô hình `bkai-foundation-models/vietnamese-bi-encoder` ghi huấn luyện trên 80% tập train Zalo.
- **Cách làm:** so 788 câu test của GreenNode với tập train gốc Zalo 2021 (`NghiemAbe/Legal_Train_Zalo`, 3.196 câu) theo ID và nguyên văn, cộng gần trùng bộ 8-từ. Dựng `vle` từ ViLegalExperts: 35.505 câu, chỉ giữ câu mà câu trả lời dẫn đúng một văn bản và một Điều có trong kho Zalo, đoạn trích khớp ≥ 40% nội dung Điều, không gần trùng câu Zalo: còn 5.437; lấy ngẫu nhiên 500 (hạt giống 2026). `python -I bench/gold/build_vle.py ...`.
- **Kết quả:** 788 trên 788 câu test nằm trong tập train gốc (khớp cả ID); 24 câu trùng nguyên văn câu train; 61 câu gần trùng; 0 trên 788 Điều đáp án trùng đáp án của câu train, nên các lần chỉnh trên train GreenNode không rò nhãn sang test. Mốc lúc đó (đường tìm của app, Advance dùng EmbeddingGemma), Hit@1 / @10: gold `vle` (n = 500) Normal 51,0 / 83,4, Advance 55,4 / 87,6; Zalo test (n = 788) Normal 58,9 / 90,2, Advance 60,2 / 92,5. Gold khó hơn Zalo: Hit@1 thấp hơn 5–8 điểm; Advance có ích hơn trên gold (+4,4 Hit@1) so với Zalo (+1,3).
- **Quyết định:** giữ làm quy tắc 7: chỉ giữ thay đổi khi tốt hơn trên cả Zalo và gold. `vle` chưa có giấy phép nên chỉ nằm trên máy; kết quả từng câu `ket_qua_gold*.json` bị `.gitignore`.
- **Vì sao giữ:** Zalo một mình không đủ tin cậy cho mô hình đã thấy dữ liệu. AITeamVN ghi "không huấn luyện trên tập này" nhưng không công bố dữ liệu (300 nghìn và 1,1 triệu bộ ba), nên không kiểm chứng được; phải xét trên gold. **Bài học:** benchmark công khai có thể nằm trong dữ liệu huấn luyện; kiểm rò rỉ trước khi tin số, và luôn có tập thứ hai từ nguồn khác. Gold vẫn có giới hạn: câu hỏi lấy từ thuvienphapluat.vn, cùng nguồn bộ huấn luyện của BKAI, nên rò rỉ thấp hơn Zalo nhưng không bằng 0.
- **Nguồn:** `bench/gold/KET-QUA.md` mục 1, 2; `bench/gold/README.md`; commit `3dd903c`.

### TK-07 · AITeamVN embedding và reranker (Advance hiện hành) (28–29/10/2026)

- **Câu hỏi:** mô hình nhúng tiếng Việt chuyên dụng cộng reranker có đưa Hit@1 lên 90% như mục tiêu ban đầu không?
- **Giả thuyết:** mục tiêu Hit@1 90% (ghi trong `kt0` mục 5.1; kết luận hiện hành ở `docs/kien-truc.md` mục 11.1).
- **Cách làm:** `AITeamVN/Vietnamese_Embedding` (nền BGE-M3, ONNX int8, 1024 chiều, cắt 128 token) hợp BM25 và vector toàn kho bằng RRF (K = 5, W = 2), rồi `AITeamVN/Vietnamese_Reranker` top-5 (cross-encoder int8, 384 token). `DENSE_MIN` 0,40 chọn trên 1.200 câu chỉnh ngoài bộ đo. Đo qua app. Nghiệm thu: 300 câu ngẫu nhiên, nửa Zalo nửa gold, app tự nhúng lại cả 61.361 Điều, 2 luồng.
- **Kết quả** (Hit@1 / @5 / @10; kho 61.425 Điều):

  | Cấu hình | Zalo test (n = 788) | Gold `vle` (n = 500) |
  |---|---|---|
  | Normal (BM25) | 58,9 / 86,2 / 90,2 | 51,0 / 76,6 / 83,4 |
  | Chỉ vector AITeamVN | 60,2 / 84,1 / 87,8 | 72,4 / 87,4 / 92,8 |
  | Hợp BM25 + vector | 68,3 / 90,4 / 95,6 | 68,4 / 89,8 / 95,4 |
  | **Advance** (hợp + reranker top-5) | **74,1** / 90,4 / 95,6 | **79,2** / 89,8 / 95,4 |

  Nghiệm thu qua app (300 câu ngẫu nhiên nửa Zalo nửa gold): Hit@1 / @3 / @5 / @10 = 79,3 / 90,0 / 92,3 / 97,3%; nhãn "độ tin cậy cao" ở 61% số câu với Hit@1 94,0%; độ trễ p50 8,6 s, p95 9,6 s (câu đầu khi chưa nạp sẵn khoảng 31 s); RAM đỉnh khoảng 2,2 GB. Trần lý thuyết: khoảng 12,7% câu sai thật; tính cả Điều tương đương ở văn bản khác thì Hit@1 tối đa khoảng 86–87%.
- **Quyết định:** giữ làm chế độ Advance. Mục tiêu Hit@1 90% **không đạt**. Chế độ mặc định của bản 1.0 là việc còn mở, xem TK-09.
- **Vì sao giữ:** so với Normal, Hit@1 tăng 15,2 điểm (Zalo) và 28,2 điểm (gold). Reranker chỉ xếp lại top 5 nên Hit@5 và Hit@10 không đổi khi thêm nó (90,4 và 95,6 ở Zalo); mức tăng Hit@1 đến từ đây (Zalo 68,3 lên 74,1) và nó chiếm khoảng 5 s trong khoảng 9 s mỗi câu. **Bài học:** hai bộ cho cùng chiều nhưng phải đọc cùng TK-09: trên văn bản thật chiều ngược lại. Số độ trễ phải ghi cùng máy và số luồng.
- **Nguồn:** `docs/kien-truc.md` mục 7.7 và 11.1 (hằng số và kết luận hiện hành); `kt0` mục 4.2, 5.1; commit `45e58f0`, `2f133e5`, `1e489f1`, `c743a08`.

### TK-08 · Phương án tìm đã đo và loại

- **Câu hỏi:** những thêm thắt nào cho Advance không đáng giữ?
- **Giả thuyết:** không ghi trước.
- **Cách làm:** repo không ghi cách đo, chỉ ghi kết luận trong tài liệu kiến trúc bản trước `6f39851` (`kt0` mục 5.3).
- **Kết quả (như ghi trong `kt0` mục 5.3):** reranker top-10 thay top-5: Hit@1 hơn 0,5–1,8 điểm nhưng chậm gấp đôi, nên giữ top-5. Phạt "hubness" và ưu tiên văn bản mới khi hoà điểm: không ổn định giữa hai bộ đo. Reranker gte và EmbeddingGemma-2: kém AITeamVN trên bộ đo. Fine-tune trên GPU thuê hoặc huấn luyện từ đầu: loại vì yêu cầu chạy offline và không thuê hạ tầng.
- **Quyết định:** bỏ cả bốn (reranker top-10 là "hoãn" nếu ngân sách thời gian cho phép: lộ trình nhánh chính xác điều 3).
- **Vì sao:** trừ top-10, nguồn không ghi số cho từng phương án; `grep` trong repo chỉ thấy các dòng này. **Bài học:** ghi số cùng với kết luận loại. Thiếu số thì lượt sau không biết loại vì chênh 0,5 điểm hay vì kém xa, và không biết có nên thử lại khi điều kiện đổi.
- **Nguồn:** `kt0` mục 5.3 (bảng này không còn trong `docs/kien-truc.md`; số liệu duy nhất là các dòng ở mục này); `docs/ke-hoach/lo-trinh-1.0.md` mục 6 (nhánh song song, điều 3).

### TK-09 · Normal và Advance trên 21 văn bản thật (22/10, 23/10, 30/10/2026)

- **Câu hỏi:** Advance có hơn Normal trên văn bản mới (2026, scan) như trên Zalo và gold không?
- **Giả thuyết:** có, vì câu hỏi đời thường ít trùng chữ (theo TK-06, Advance hơn Normal nhiều hơn trên gold).
- **Cách làm:** 21 văn bản 2026 (9 Luật, 6 Nghị định, 5 Thông tư, 1 Quyết định; 443 trang, 18 bản scan), 84 câu (4 câu mỗi văn bản). "Rộng" tính đúng nếu thẻ cùng file và đúng Điều hoặc trang của thẻ chứa câu trích; "chặt" đòi đúng số Điều. Ba lần đo: 22/10 (EmbeddingGemma, trước sửa parser), 23/10 (sau sửa parser, PS-03), 30/10 (AITeamVN cộng reranker; kho dựng lại trên Linux, 321 trên 344 Điều khớp; Normal và Advance đo trên cùng kho). Lệnh: `python bench/van-ban-that/eval_real.py <realdocs> normal|advance`.
- **Kết quả** (văn bản thật, n = 84, rộng):

  | Lần đo | Mô hình nhúng | Normal @1 / @5 / @10 | Advance @1 / @5 / @10 |
  |---|---|---|---|
  | 22/10, trước sửa parser | EmbeddingGemma | 76,2 / 91,7 / 95,2 | 65,5 / 94,0 / 95,2 |
  | 23/10, sau sửa lỗi 1, 2, 7 | EmbeddingGemma | 81,0 / 96,4 / 96,4 | 73,8 / 97,6 / 97,6 |
  | 23/10, sau sửa lỗi 3, 8, 9 | EmbeddingGemma | 82,1 / 96,4 / 96,4 | 75,0 / 96,4 / 96,4 |
  | 30/10, mốc P0 | AITeamVN + reranker | **83,3** / 96,4 / 96,4 | 72,6 / 95,2 / 97,6 |

  Mốc 30/10, nhánh trung gian (BM25 + vector, chưa reranker): @1 67,9 / @5 95,2 / @10 97,6. Chặt @1: Normal 78,6, BM25 + vector 63,1, Advance 69,0. Đúng file ở hạng 1: 94,0 / 85,7 / 89,3%.
- **Quyết định:** giữ Normal làm mặc định cho tới khi nhánh độ chính xác sửa bước hợp (đề xuất trong lộ trình mục 2 điều 8; chốt cuối ở mục 9 điều 8, còn mở). Sửa bước hợp: chưa làm.
- **Vì sao Advance thất bại ở đây:** bước hợp BM25 với vector làm tụt Hit@1 khoảng 15 điểm (83,3% xuống 67,9%); reranker gỡ lại khoảng 5 điểm. Hệ số hợp (`TOP`, `DENSE_K`, `RRF_K`, `W = 2`) được chọn trên kho Zalo 61.425 Điều, chưa chắc hợp kho nhỏ văn bản mới. Ở lần đo 22/10, các Điều đúng bị tụt dài trung vị 1.399 token, các Điều giữ hạng 1 dài trung vị 536 token, trong khi mô hình chỉ nhúng 128 token đầu (13 câu tụt khỏi hạng 1, 4 câu lên). Phân tích 38 câu không ở hạng 1 (lần 22/10, nguồn không ghi chế độ; một agent phân tích, một agent phản biện): tách cấu trúc 15, xếp hạng BM25 10, xếp lại theo nghĩa 9, lỗi OCR 3, nằm trong phụ lục ngoài Điều 1.
- **Bài học:** (1) Hai bộ lớn (Zalo, gold) cùng nói "Advance hơn" nhưng bộ nhỏ thứ ba (văn bản thật) nói ngược, ở cả ba mô hình nhúng. Tham số chọn trên một phân bố không chuyển sang phân bố khác; quy tắc 7 có điều khoản "không tụt trên văn bản thật" vì lý do này. (2) n = 84 thì 1 câu bằng 1,2 điểm; chênh 1 câu là nhiễu (lần 23/10). (3) 84 câu này vừa dùng để tìm lỗi parser vừa dùng để đo, nên số "sau" có thể cao hơn trên văn bản lạ. (4) Độ trễ không giảm khi kho nhỏ (21 văn bản vẫn ~1 s mỗi câu): nguyên nhân là `+f.rowid IN (… json_each …)` ở nhánh trang OCR, 744 ms xuống 3 ms mỗi câu (xem PS-03).
- **Nguồn:** `bench/van-ban-that/KET-QUA.md` mục "Tìm kiếm", "Sau khi sửa lỗi 1, 2, 7", "Sau khi sửa lỗi 3, 8, 9", "Mốc P0 của lộ trình 1.0"; `docs/ke-hoach/lo-trinh-1.0.md` mục 2 điều 8 và mục 6 (nhánh song song, điều 0); commit `7060f61`.

## Nhóm PS: nạp file, parser và dữ liệu

### PS-01 · Chạy thử bản 0.7 trên kho sinh tự động và file bẩn, rồi sửa (21/10/2026)

- **Câu hỏi:** bản 0.7 chịu được file văn phòng không đúng format và kho lớn không?
- **Giả thuyết:** không ghi trước.
- **Cách làm:** máy Ryzen 5 5600GT, 15,4 GB RAM (chỉ còn khoảng 1,3 GB trống lúc đo). Kho sinh tự động: 300 văn bản (248 DOCX, 40 PDF chữ, 12 PDF scan), thêm 1.452 DOCX thành 1.762 văn bản, 133.425 đơn vị. 268 truy vấn có đáp án. 18 file "bẩn" dựng bằng Word thật (Word tự đánh số Điều, bảng, footnote, `.doc` cũ, PDF scan nghiêng, hai văn bản trong một file...) với 22 kỳ vọng. Lệnh: `python bench/gen_corpus.py DIR`, `python bench/word_tools.py DIR`, `python bench/run_bench.py DIR`.
- **Kết quả** trước, rồi sau khi sửa (bản 0.8, cùng máy, cùng bộ):

  | Chỉ số | Trước (0.7) | Sau (0.8) |
  |---|---|---|
  | File bẩn nạp được (n = 18) | 12 | 18 |
  | Kỳ vọng file bẩn tìm thấy (n = 22) | 6 | 22 |
  | Tra cứu kho 310 văn bản, p50 / p95 | 188 / 343 ms | 49 / 76 ms |
  | Tra cứu kho 1.762 văn bản, p50 / p95 (trong process) | 930 / 1.173 ms | 88 / 125 ms |
  | Câu hỏi có đáp án trong top 10 (kho 310 văn bản) | 70% | 100% |
  | Viết tắt có đáp án trong top 10 | 56% | 100% |
  | Hỏi mức phạt có đáp án trong top 10 | 0% | 100% |
  | Diễn đạt khác có đáp án trong top 10 | 40% | 70% |
  | `pytest` | 90 | 177 |

  Độ trễ tăng tuyến tính theo kích thước kho: `search.vocab_phrases()` đọc và chuẩn hoá lại tên toàn bộ Điều mỗi truy vấn, chiếm khoảng 90% thời gian tìm. 21 lỗ hổng L1–L21 được ghi (nặng nhất: L7 trùng số Điều làm hỏng cả file, L12 file trùng tên ở hai thư mục ghi đè nhau và mất dữ liệu, L20 độ trễ theo kho).
- **Quyết định:** giữ các sửa. Bốn agent chạy song song, mỗi agent sở hữu một nhóm file riêng nên không đụng nhau.
- **Vì sao giữ:** mất dữ liệu và hỏng cả file nặng hơn lỗi xếp hạng. **Bài học:** (1) Dùng file bẩn dựng bằng công cụ thật (Word thật) mới lộ lỗi mà tài liệu sạch không có. (2) Độ trễ tăng theo kích thước kho là dấu hiệu thuật toán quét toàn kho; nên đo ở hai cỡ kho. (3) Dữ liệu sinh tự động cho số đẹp (100%); nguồn tự ghi "chưa thử với kho văn bản thật", và đó là lý do có TK-09 và PS-03.
- **Nguồn:** `bench/BAO-CAO-DEMO.md` mục 2–7; commit `8197efd`.

### PS-02 · Mười file lệch cấu trúc (stress10) (21/10/2026)

- **Câu hỏi:** file không theo thể thức Điều/khoản (thông báo, biên bản, hợp đồng, markdown, Excel, ảnh JPG) có nạp và tìm được không?
- **Giả thuyết:** không ghi trước.
- **Cách làm:** 10 file do `bench/stress10/gen.py` sinh, mỗi file 2 truy vấn (từ khoá, câu hỏi), kho nền 318 văn bản demo. Đúng khi thẻ chứa cụm đáp án nằm trong top 10.
- **Kết quả:** 10/10 file nạp, 19/20 truy vấn đúng (n = 20); sau khi chuyển BM25 OR (TK-01) đo lại 20/20. Hạn chế: cả 10 file chỉ ra một đơn vị "đoạn" mỗi file nên trích dẫn chỉ là "cả văn bản"; "Điều 1 – Tên" (dấu gạch ngang) không được nhận là Điều; OCR đọc năm 2026 thành 2028.
- **Quyết định:** giữ làm bộ hồi quy (`bench/stress10/run.py`).
- **Vì sao giữ:** nhỏ, chạy nhanh, và là bộ duy nhất đo file không có Điều.
- **Bài học:** tìm đúng chưa phải trích dẫn đúng. OCR đọc nhầm một chữ số (năm) vô hại với tìm kiếm nhưng nguy hiểm trong văn bản luật; bộ kiểm số liệu của câu trả lời AI phải coi chữ số là dữ liệu cần đối chiếu (LM-06).
- **Nguồn:** `bench/stress10/KET-QUA.md`; `bench/zalo/KET-QUA.md` mục "Sau khi chuyển app sang BM25 OR".

### PS-03 · Lỗi cấu trúc và siêu dữ liệu trên 21 văn bản thật, và các sửa (22–23/10/2026)

- **Câu hỏi:** parser và bộ đọc siêu dữ liệu có đúng trên văn bản scan thật không? OCR có phải chỗ yếu?
- **Giả thuyết:** không ghi trước.
- **Cách làm:** 21 văn bản 2026 (mô tả ở TK-09), 18 bản scan không có lớp chữ. Một agent đối chiếu từng file với bản scan, một agent thứ hai cố bác bỏ từng kết luận. 84 câu trích chép tay từ ảnh dùng để so với chữ OCR của đúng trang. Hai đợt sửa (lỗi 1, 2, 7; rồi 3, 8, 9) trong `parse.py`, `extract.py`, `sohieu.py`, `search.py`, nạp lại bằng OCR rồi đo lại. Lệnh: `python bench/van-ban-that/import_real.py ...`, `bench/van-ban-that/cau_truc.py`, `bench/van-ban-that/sieu_du_lieu.py`.
- **Kết quả** (21 văn bản thật; 344 Điều thật không tính Điều được trích trong luật sửa đổi):

  | Chỉ số | Lúc đầu | Sau sửa lỗi 1, 2, 7 | Sau sửa lỗi 3, 8, 9 |
  |---|---|---|---|
  | Điều tách đúng | 249/344 (72%, xét trang); 259/344 (75%, đếm thô) | 335/344 (97%, đếm thô) | 341/344 (99%) |
  | Số hiệu đúng | 12/21 | 16/21 | 16/21 |
  | Cơ quan ban hành đúng | 6/21 | 6/21 | 21/21 |
  | Ngày ban hành đúng | 9/21 | 9/21 | 14/21 |
  | Ngày hiệu lực đúng | 15/21 | 15/21 | 19/21 |
  | Loại văn bản đúng | 20/21 | 20/21 | 20/21 |

  Tìm kiếm (n = 84, Normal, rộng): Hit@1 76,2% lên 81,0% lên 82,1%; độ trễ p50 / p95 1050 / 1796 ms xuống 370 / 494 ms rồi 336 / 401 ms. Mười lỗi, xếp theo ảnh hưởng: (1) một dấu ngoặc kép lạc do OCR làm mất nhận diện Điều đến hết văn bản (18/2026 mất 43 Điều); (2) bộ dò bảng nhận văn bản căn đều thành bảng (385/2026 mất 24 trên 39 Điều); (3) ký tự rác hoặc chữ "Điều" bị OCR đọc hỏng ("Đ1eu", "Điều M"); (4) dòng nối của điểm bị nối vào khoản cha; (5) khoản đánh "1,"; (6) không cắt "Nơi nhận" và phụ lục; (7) số hiệu: khi không đọc được thì lấy số đầu tiên trong văn bản, tức luật được trích dẫn; (8) cơ quan ban hành tìm trên cả văn bản; (9) ngày ban hành của Luật nằm ở câu kết; (10) `struct_score` che lỗi (22/2026 được 0,99 điểm dù mất Điều 1). Chưa sửa ở thời điểm đó: 3 Điều, 5 số hiệu (viết tay hoặc nằm trong ô chữ ký số), 7 ngày ban hành.
- **Quyết định:** giữ các sửa. Các lỗi còn lại (số hiệu và ngày viết tay) hoãn sang hàng chờ người điền ở P2 (xem PS-04).
- **Vì sao giữ:** sửa lỗi 1, 2, 7 đưa Điều đúng từ 259 lên 335 trên 344; sửa lỗi 3, 8, 9 đưa cơ quan ban hành từ 6/21 lên 21/21. **Bài học:** (1) Máy trạng thái "đang trong khối trích dẫn" không có điểm đặt lại thì một ký tự rác làm mất cả văn bản; mọi cờ trạng thái cần điều kiện đặt lại ở tín hiệu chắc (tiêu đề "Điều N." đúng thứ tự). (2) Điểm tự đánh giá (`struct_score`) che lỗi; đối chiếu bằng đáp án đếm tay bên ngoài. (3) Sửa dữ liệu thì dùng chỉ số trực tiếp (đếm Điều, siêu dữ liệu): chênh giữa hai lần đo tìm kiếm chỉ cỡ một câu, trong khi dữ liệu cải thiện rõ. (4) Hàm dự phòng "lấy cái đầu tiên khớp" (lỗi 7) trả sai mà không báo; nó tái xuất hiện ở SO-08 (C1). (5) Bộ 84 câu vừa tìm lỗi vừa đo, nên số sau sửa có thể cao hơn trên văn bản lạ.
- **Nguồn:** `bench/van-ban-that/KET-QUA.md` mục "Cấu trúc và siêu dữ liệu", "Lỗi tìm thấy", "Sau khi sửa lỗi 1, 2, 7", "Sau khi sửa lỗi 3, 8, 9"; commit `8197efd`.

### PS-04 · OCR: giữ Tesseract, không thay (22/10 đến 31/10/2026)

- **Câu hỏi:** phản hồi ⑩ ("dùng thư viện AI trích chữ") có nghĩa là phải thay bộ OCR không?
- **Giả thuyết:** OCR chưa chắc là chỗ yếu; chỗ yếu có thể là bước tách cấu trúc sau OCR.
- **Cách làm:** so 84 câu trích chép tay từ ảnh với chữ OCR của đúng trang (21 văn bản thật; Tesseract `vie`, 300 DPI). Đo thời gian trên 371 trang scan.
- **Kết quả** (21 văn bản thật, 84 câu trích): độ giống ký tự trung bình 98,5%, trung vị 100%, 2 câu dưới 90%; độ tin cậy OCR trung bình theo Tesseract 88,7; 1,69 s mỗi trang scan (371 trang trong 628 s; bản 0.7 trên bộ scan sinh tự động: khoảng 1,05 s mỗi trang ở 200 dpi, độ đúng khoảng 97% số từ với bản sạch và khoảng 95% với bản nghiêng, nhiễu). Sau PS-03, tách đúng 341/344 Điều.
- **Quyết định:** giữ Tesseract (lộ trình mục 2 điều 1 và mục 10 "Không làm"). Bộ OCR hoặc mô hình PDF chuyên dụng (Docling, MinerU, PaddleOCR-VL) cho cả kho: chưa dùng, ước 1–2 phút mỗi trang trên CPU, chỉ xét lại nếu bộ đo thấy lỗi bố cục mà quy tắc không sửa được. Việc D (Qwen3-VL-4B đọc ảnh trang đầu và vùng chữ ký để gợi ý số hiệu, ngày): hoãn sang P2, đo trước trên 12 trường đang sai.
- **Vì sao:** OCR không phải chỗ yếu; chỗ yếu từng là tách cấu trúc (PS-03), đã sửa. Phần còn lại là chữ viết tay và ô chữ ký số, không bộ OCR nào đọc chắc, nên cần người điền. **Bài học:** đo nút cổ chai trước khi đổi công nghệ; 98,5% cho thấy lỗi nằm ở bước sau. Số 98,5% đo trên câu trích đã chọn theo câu hỏi, không phải mẫu ngẫu nhiên của mọi trang.
- **Nguồn:** `bench/van-ban-that/KET-QUA.md` mục "Nạp"; `bench/BAO-CAO-DEMO.md` mục 3; `docs/ke-hoach/lo-trinh-1.0.md` mục 1 (phản hồi ⑩), mục 2 điều 1, mục 10.

### PS-05 · N0: bốn chỉ mục khoá ngoại (31/10/2026)

- **Câu hỏi:** vì sao xoá hoặc nạp lại một văn bản chậm trên kho Zalo?
- **Giả thuyết:** bốn cột khoá ngoại trỏ vào `units` thiếu chỉ mục nên mỗi lần xoá, SQLite quét cả bảng.
- **Cách làm:** `EXPLAIN QUERY PLAN` cho từng cột khoá ngoại; đo xoá văn bản 89 đơn vị trên bản sao kho Zalo (428.874 đơn vị, 3.271 văn bản) trước và sau khi thêm bốn chỉ mục; test `tests/test_schema_index.py`.
- **Kết quả** (bản sao kho Zalo): xoá văn bản 89 đơn vị 41,5 s xuống 0,01 s; tạo bốn chỉ mục mất 0,37 s. Kế hoạch ước N1b không có chỉ mục này sẽ mất khoảng 50 giờ cho kho Zalo (ước tính). Dựng lại cả kho Zalo (3.257 văn bản) mất 746 s, 0,23 s mỗi văn bản (máy đang chạy việc khác nên là cận trên).
- **Quyết định:** giữ.
- **Vì sao:** lỗi có từ bản 0.8 (nạp lại file chậm), chỉ lộ khi đo ở kho lớn. **Bài học:** quét toàn bảng ẩn sau `ON DELETE CASCADE`; thêm khoá ngoại thì chạy `EXPLAIN QUERY PLAN` cho cột đó.
- **Nguồn:** `docs/ke-hoach/ke-hoach-p1.md` mục N0; commit `ba7f1c3`.

### PS-06 · N1a: sửa parser dòng nối của điểm (31/10/2026)

- **Câu hỏi:** dòng thứ hai trở đi của một điểm bị nối vào khoản cha; sửa năm chỗ trong `_parse_lines` có làm tụt tìm kiếm không?
- **Giả thuyết:** sửa đúng cho trình đọc, kỳ vọng xếp hạng không đổi hoặc nhích nhẹ.
- **Cách làm:** thêm biến `current_diem`; test `tests/test_parse.py::test_diem_nhieu_dong` hỏng trên mã cũ. Đo Normal (`SOILUAT_SEMANTIC=0`), hai bản dựng cùng máy, trước và sau: Zalo test (n = 788), gold `vle` (n = 500), văn bản thật (n = 84).
- **Kết quả:**

  | Bộ | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Ghi chú |
  |---|---|---|---|---|---|
  | Zalo test, n = 788 (số câu) | 464 lên 462 | 647 lên 652 | 682 lên 680 | 714 lên 713 | MRR@10 0,71 giữ nguyên; 54 câu đổi hạng |
  | Gold `vle`, n = 500 (số câu) | 254 lên 256 | 348 lên 350 | 385 giữ 385 | 418 lên 421 | MRR@10 0,62 lên 0,624; 60 câu đổi hạng |
  | Văn bản thật, n = 84, rộng (%) | 83,3 lên 84,5 | 94,0 xuống 91,7 | 96,4 giữ | 96,4 giữ | @3 mất 2 câu (hạng 3 xuống 4); phép kiểm dấu p = 0,5 |

  Điểm không còn bị cắt giữa câu: 795 xuống 113 trên 1.097 điểm. Tác động kèm theo (21 văn bản thật): 1.242 trên 2.610 đơn vị đổi chữ, 16 trên 21 văn bản đổi; liên kết 73 lên 121 (thêm 48 gợi ý máy cần duyệt); nhãn `CHE_TAI` 187 xuống 173; gợi ý hiệu lực 6 xuống 5.
- **Quyết định:** giữ. Chủ dự án duyệt có điều kiện ngày 31/10/2026: "giữ nếu Zalo và gold không thấp hơn", kèm yêu cầu nghiên cứu N3. Zalo thấp hơn theo chữ ở Hit@1, @5, @10 (1–2 câu trên 788), nên điều kiện chưa đạt theo chữ; chủ dự án chọn giữ cùng N3.
- **Vì sao giữ dù tụt trong nhiễu:** đây là sửa đúng cho trình đọc (điểm nhiều dòng đang bị cắt), không phải chỉnh xếp hạng. Ngoại lệ chỉ phủ N1a; ứng viên của N3 phải tự qua quy tắc 7. **Bài học:** ghi tiêu chí giữ hoặc gỡ trước khi đo; khi sửa đúng mà số tụt trong nhiễu thì xin ngoại lệ có tên, có điều kiện, có người duyệt. Với chênh 1–2 câu dùng phép kiểm dấu, không so phần trăm. Thêm chỉ số đúng mục tiêu sửa (điểm bị cắt giữa câu) cạnh chỉ số tìm kiếm.
- **Nguồn:** `docs/ke-hoach/ke-hoach-p1.md` mục 2b, N1a, "Đã kiểm"; `docs/ke-hoach/lo-trinh-1.0.md` mục 9 điều 11; commit `ba7f1c3`, `91763de`, `7a81562`.

### PS-07 · N3: nghiên cứu nâng cấp parser và chọn ý chính (31/10/2026)

- **Câu hỏi:** nâng parser theo hướng nào để tối ưu hiệu suất, và chọn "ý chính, điểm quan trọng" của văn bản thế nào? (yêu cầu của chủ dự án.)
- **Giả thuyết:** "hiệu suất" là chất lượng cấu trúc, không phải tốc độ: parse 21 văn bản mất 479 ms, dựng lại 9,1 s, nên parser chỉ chiếm khoảng 5% giờ dựng lại.
- **Cách làm:** workflow 5 agent (3 khảo sát: cấu trúc trên 21 văn bản thật, ý chính, thay đổi trên Zalo; 1 dựng ứng viên và đo; 1 kiểm chứng ngược, tái lập mọi số). Chỉ số và ngưỡng ghi trước khi chạy: (1) tách Điều 341/344 không giảm; (2) điểm bị cắt giữa câu ≤ 113; (3) Hit@k ba bộ theo quy tắc 7; (4) giờ dựng lại không quá +10%; (5) tốc độ parse chỉ ghi nhận. Bộ đo từng phần mới: `bench/van-ban-that/cau_truc_chi_tiet.py`; so parser với kho: `bench/parse_khac.py`.
- **Kết quả** (21 văn bản thật; mốc trước là parser có N1a: 321/344 Điều đúng, 93,3%, 15/21 văn bản trọn vẹn). Bảng ứng viên, tìm kiếm văn bản thật n = 84 Normal (mốc N1a rộng 84,5 / 91,7 / 96,4 / 96,4):

  | Ứng viên | Kết quả | Quyết định |
  |---|---|---|
  | B1 ngoặc " thừa không đóng | Điều 322 lên 342; rộng @5 mất 1 câu (nhiễu), @10 thêm 1; 0 văn bản Zalo đổi | giữ |
  | B3 đầu Điều OCR hỏng ("Điều §.", "Điều 3,") | rộng không đổi, chặt +2 / +3 / +3 / +2, mất 0; 0 văn bản Zalo đổi | giữ |
  | B2 cắt khối chữ ký, Phụ lục thành đơn vị `PLk.paraN` | rộng +2 / +2 / +1−1 / +1; mảnh bảng Phụ lục chen vào 5 mục đầu ở vài câu | giữ, kèm điều kiện gộp thẻ theo Phụ lục |
  | Gộp B1 + B2 + B3 | rộng 86,9 / 94,0 / 96,4 / 98,8; không mốc nào thấp hơn | giữ |
  | Mục con N.M, cắt câu kết khoản | 0 đổi trên văn bản thật; 47 và 366 văn bản Zalo đổi (hai biến thể, nguồn không tách) | sang P2 |
  | Kích hoạt Phụ lục không cần khối chữ ký | văn bản Zalo 2821 mất 26 Điều | gỡ |
  | Ý chính P1 (mức phạt nguyên văn, huy hiệu hiệu lực, trích yếu, phạm vi, chip thời hạn) | mức phạt đúng số 290/290 nhưng sai đối tượng (NĐ 391 Điều 4: cá nhân bằng 1/2 mức tổ chức, câu ở Điều khác); huy hiệu trái quyết định để hiệu lực ở P2 | không đứng, sang P2 |

  Sau khi áp B1 + B2 + B3 và gộp thẻ Phụ lục (chủ dự án chọn): Điều 322 lên 345/344 (thiếu 23 còn 0, thừa 1); dòng bảng bị bỏ 301 xuống 21; chữ ký lọt vào đơn vị 212 xuống 41; Phụ lục bị bỏ 775 xuống 25. Tìm kiếm văn bản thật (n = 84, Normal): rộng 86,9 / 94,0 / 97,6 / 98,8, chặt 83,3 / 92,9 / 96,4 / 97,6 (mốc P0 rộng 83,3 / 94,0 / 96,4 / 96,4). Zalo: 0 văn bản đổi (`bench/parse_khac.py`, 3.257 văn bản dựng được trên 3.271), nên Zalo và gold không đổi so với số K3. Giờ parse tăng khoảng 60% nhưng giờ dựng lại chỉ tăng 3–8%.
- **Quyết định:** giữ B1 + B2 + B3 kèm gộp thẻ theo Phụ lục (áp ở `ea122bb`); gỡ "kích hoạt Phụ lục không cần chữ ký"; mục con N.M và mọi "ý chính" sang P2. Thêm giảm nhiễu: dòng chỉ có 1–3 chữ số (số trang) không hiện ở trình đọc và phần trích (`b2b407d`); chỉ mục giữ chữ gốc nên kết quả tìm không đổi; bộ đo đếm 293 dòng như vậy trong 21 văn bản.
- **Vì sao ý chính thất bại:** quy tắc trích đúng con số nhưng sai đối tượng áp dụng. **Bài học:** (1) Số đúng chưa đủ, phải đúng phạm vi áp dụng; đây cùng lớp lỗi với "khái quát quá phạm vi" của LLM (LM-01, LM-07) và với thẻ chế tài lấy từ Điều khác (`docs/ke-hoach/ke-hoach-p1.md` mục 1 dòng 4). (2) Ghi ngưỡng trước khi chạy, mỗi ứng viên tự qua quy tắc 7, đo từng ứng viên riêng rồi mới gộp. (3) Nhóm thử "ngoài DB" (trích yếu, Điều 1) giữ ý chính khỏi vào app khi chưa có cổng kiểm tay.
- **Nguồn:** `docs/ke-hoach/ke-hoach-p1.md` mục N3; `bench/van-ban-that/cau_truc_chi_tiet.py`, `bench/parse_khac.py`; commit `ee6ecaf`, `e8e49f0`, `ea122bb`, `b2b407d`.

### PS-08 · Hồi quy gộp thẻ Phụ lục: trang của thẻ (31/10/2026)

- **Câu hỏi:** gộp mỗi Phụ lục thành một thẻ có làm mất kết quả nào không?
- **Giả thuyết:** (suy từ điều kiện của ứng viên B2 ở PS-07) gộp thẻ theo Phụ lục bỏ được mảnh bảng chen vào 5 mục đầu mà không mất kết quả.
- **Cách làm:** chạy 84 câu văn bản thật hai lần, có gộp và không gộp, so từng câu (phép đo "rộng" tính đúng nếu trang của thẻ chứa câu trích).
- **Kết quả:** khi trang của thẻ chỉ là trang đoạn đầu của Phụ lục, câu "bốc xếp thủ công vật nặng" (27/2026, đáp án nằm ở phụ lục) mất khỏi kết quả. Sửa bằng cách lấy trang của thẻ là cả khoảng trang các đoạn (`page_from` đến `page_to`). Sau sửa không mốc nào thấp hơn P0 (số ở PS-07).
- **Quyết định:** giữ bản gộp có khoảng trang; 7 test của N3 có ca gộp Phụ lục hỏng trên mã cũ.
- **Vì sao suýt thất bại:** gộp đơn vị mà không gộp thuộc tính định vị. **Bài học:** khi một thay đổi gộp đơn vị, thuộc tính định vị (trang) phải đi theo; so từng câu có và không thay đổi, đừng chỉ nhìn số tổng, vì một câu là 1,2 điểm trên n = 84.
- **Nguồn:** `docs/ke-hoach/ke-hoach-p1.md` mục N3 (trạng thái); commit `ea122bb`.

### PS-09 · N1b: nâng cấp dữ liệu một lần khi parser đổi (31/10/2026)

- **Câu hỏi:** nâng kho cũ lên parser mới thế nào cho nhanh và không làm mất dữ liệu người dùng?
- **Giả thuyết:** không ghi trước; thiết kế là chỉ dựng lại văn bản mà parse lại khác đơn vị đang lưu, để giữ vector, nhãn, liên kết của phần không đổi.
- **Cách làm:** `parse.PARSE_REV = "2"`; `rebuild.rebuild_if_changed` chỉ dựng lại văn bản mà parse lại khác đơn vị đang lưu; chạy trong luồng nền `soiluat-jobs`; sao lưu một lần trước (`data/backup/soiluat-truoc-parse2.db`, ghi tệp tạm theo pid rồi `os.replace`); cờ `parse_rev` ghi sau cùng. Workflow 4 agent: làm theo TDD, soát an toàn dữ liệu, soát tải và giao diện, sửa.
- **Kết quả** (đo qua luồng nền thật): 21 văn bản thật dựng lại 21/21 trong 5,6 s, sau đó `parse_khac` 0 văn bản khác, lần chạy thứ hai 0 việc. Zalo 3.271 văn bản: 1.760 dựng lại, 1.497 giữ nguyên, 14 `fallback_doan` bỏ qua; 467 s; sao lưu 1,4 GB mất 13,5 s; sau đó 0 khác, số đơn vị không đổi. Tìm kiếm văn bản thật (n = 84) không đổi (rộng 86,9 / 94,0 / 97,6 / 98,8).
- **Quyết định:** giữ.
- **Vì sao giữ:** soát độc lập tìm ra các lỗi an toàn, đã sửa: khoá ghi làm luồng chết im; văn bản bị khoá thoáng qua phải thử lại cuối lượt; giữ khoá ghi 25 s ở văn bản 1.221 đơn vị; giữ người và ngày duyệt liên kết; giữ vector của Điều không đổi chữ; trong lúc nâng cấp tìm kiếm dùng chỉ mục cũ thay vì dựng lại mỗi lần. Chấp nhận một điểm yếu: liên kết và gợi ý đã bác hiện lại một lần sau dựng lại (giữ cặp đã bác cần bảng mới, để P2). **Bài học:** (1) Trạng thái "đã thử" phải nằm trong tiến trình, không chỉ trong cơ sở dữ liệu, nếu không "lần sau" thành "vòng sau" và duyệt lại cả kho. (2) Sao lưu ghi tệp tạm rồi đổi tên: đĩa đầy giữa chừng không được để tệp cụt mang đúng tên (lần mở sau sẽ bỏ qua sao lưu). (3) Luồng nền bắt lỗi từng văn bản và báo ra giao diện, không chết im. Xem thêm skill `sqlite-table-rebuild`.
- **Nguồn:** `docs/ke-hoach/ke-hoach-p1.md` mục N1b; commit `e03a136`.

### PS-10 · N1c: giữ gợi ý hiệu lực đã duyệt khi dựng lại (31/10/2026)

- **Câu hỏi:** duyệt gợi ý hiệu lực rồi dựng lại văn bản có làm mất gợi ý đã duyệt không?
- **Giả thuyết:** có; kế hoạch ghi lỗi này có sẵn ở 0.8, không phụ thuộc parser.
- **Cách làm:** test viết trước ở `tests/test_rebuild_all.py` (gợi ý `confirmed = 1` còn sau `rebuild_document` và không bị nhân đôi; hai đơn vị `bai_bo` vẫn ra hai gợi ý; ép lỗi giữa chừng thì văn bản còn nguyên đơn vị), rồi sửa.
- **Kết quả:** có (lỗi có từ 0.8): `rebuild_document` xoá mọi `effect_hints` kể cả `confirmed = 1`, và không `rollback` khi lỗi giữa chừng nên văn bản kế tiếp commit chốt luôn việc xoá. Sửa: chỉ xoá `confirmed = 0`, `suggest_effect_hints` không thêm bản trùng gợi ý đã duyệt, bọc `try/except` với `rollback`. Test `tests/test_rebuild_all.py` hỏng trên mã cũ.
- **Quyết định:** giữ (làm cả khi gỡ parser). Phần đường nạp lại file được sửa ở SO-08 (S6).
- **Vì sao giữ:** mất dữ liệu người dùng đã duyệt, sửa rẻ (0,25 ngày).
- **Bài học:** lỗi mất dữ liệu có thể nằm ở đường dùng chung (dựng lại) chứ không ở tính năng đang làm; tìm mọi nơi gọi một hàm xoá. Giao dịch dở trên kết nối dùng chung lây sang văn bản kế tiếp.
- **Nguồn:** `docs/ke-hoach/ke-hoach-p1.md` mục N1c; commit `ba7f1c3`.

## Nhóm LM: câu trả lời bằng LLM

Chung cho cả nhóm: máy đo là máy ảo Linux 4 nhân (Xeon có AVX-512), 15 GB RAM, llama-cpp-python 0.3.36, 4 luồng, nhiệt độ 0,1, seed 2026. **Đây chưa phải máy 16 GB Windows của người dùng**: tỉ lệ chất lượng dùng được cho quyết định, thời gian thì không. Bộ đo `bench/llm/run.py` chấm hoàn toàn bằng máy; ba phép và các chỉ số định nghĩa ở `docs/nghien-cuu/ghi-nho.md` mục 3.1, không chép lại ở đây. Tập chấm (test) và tập chỉnh (train) tách theo seed 2026 (`pick_sample`).

### LM-01 · Vòng 1: Qwen3-VL-4B trên ba bộ test (30/10/2026)

- **Câu hỏi:** Qwen3-VL-4B-Instruct (Q4_K_M) trả lời từ 5 Điều đã tìm có đạt cổng P0 chưa (JSON ≥ 99%, dẫn đúng Điều ≥ 80%, từ chối đúng ≥ 80%, xong ≤ 45 s)?
- **Giả thuyết:** cổng là "đề xuất, chốt khi có số" (`docs/ke-hoach/lo-trinh-1.0.md` mục 6, P0).
- **Cách làm:** mã `9d4b7c7`. Mỗi câu hỏi hai lần gọi: `dan` (Điều đúng có trong ngữ cảnh) và `tu_choi` (đã bỏ Điều đúng và các bản gần như cùng chữ); thêm câu bẫy tiền đề sai (`bay`, chỉ sinh được ở kho Zalo). Chọn cấu hình trên train trước khi chấm: giữ câu dẫn của khoản khi giữ một điểm; gộp Điều trùng nội dung; ngân sách ngữ cảnh 2.600 ký tự (đo 3,1 ký tự mỗi token, nên 3.000 ký tự vượt trần khoảng 1.000 token mới); JSON schema hai nhánh theo `du_can_cu`; `tien_de_sai` đứng trước `du_can_cu` (bẫy 6/6 so với 5/6 trên 8 câu và 6 bẫy train); trần độ dài. Chấm test một lần.
- **Kết quả** (test: Zalo n = 30 câu cộng 20 bẫy, gold `vle` n = 20, văn bản thật n = 15):

  | Chỉ số | Zalo | Gold `vle` | Văn bản thật |
  |---|---|---|---|
  | JSON hợp lệ | 87,5% | 92,5% | 96,7% |
  | Dẫn đúng Điều | 66,7% | 70,0% | 46,7% |
  | Từ chối đúng (`du_can_cu = false` khi đã bỏ Điều đúng) | 26,7% | 35,0% | 66,7% |
  | Khẳng định như đủ căn cứ khi đã bỏ Điều đúng | 66,7% | 65,0% | 33,3% |
  | Chỉ ra tiền đề sai (bẫy) | 75,0% (15/20) | không có | không có |
  | Có chữ Trung, Nhật, Hàn | 3,8% | 10,0% | 0% |
  | Mô hình p50 / p95 trên máy ảo | 71,8 / 93,2 s | 63,4 / 81,5 s | 57,1 / 85,0 s |

  Tốc độ máy ảo: đọc prompt khoảng 27 token/giây, sinh khoảng 5,2 token/giây (trung vị, từ log 72 lần gọi). Mọi JSON hỏng (14 trên 150 lần gọi) đều do bị cắt ở trần 200 token. Soát câu từ chối sai bằng hai giám khảo là mô hình Claude (không phải người): Zalo 22 câu, gold 13, văn bản thật 5; nhóm lớn nhất là "một phần", tức khái quát quy định của trường hợp hẹp cho câu hỏi chung (ví dụ lấy mức chỉ áp dụng tại đường ngang, cầu chung để trả lời phạt vượt đèn đỏ). Tính câu "hỗ trợ" là trả lời được thì từ chối đúng ước khoảng 40–43% (Zalo) và khoảng 50% (gold). Văn bản thật: ở 5 trên 7 câu dẫn sai, đoạn sau khi cắt chỉ còn ≤ 31% bộ 3-từ của câu trích đáp án (3 câu dưới 10%).
- **Quyết định:** chưa đạt cổng; làm bảy việc sửa (LM-02 đến LM-06; việc 6 đo ở CN-03; việc 7, máy 16 GB, chưa đo, xem CN-02) rồi đo vòng 2.
- **Vì sao chưa đạt, tách được ba nguyên nhân:** (a) cắt JSON ở 200 token, lỗi của mã ta; (b) dòng chứa đáp án bị cắt khỏi ngữ cảnh vì Điều dài và dòng OCR dính nhiều khoản, lỗi của mã ta; (c) khái quát quá phạm vi đoạn, lỗi của mô hình. **Bài học:** (1) Tách lỗi mã khỏi lỗi mô hình bằng chỉ số trung gian ("câu trích bằng chứng còn trong đoạn") trước khi kết luận về mô hình. (2) Chấm tự động theo con số bỏ sót loại lỗi "số đúng, sai phạm vi"; cần giám khảo khác hoặc tín hiệu khác. (3) Đừng chỉnh và chấm trên cùng câu bẫy (xem LM-07).
- **Nguồn:** `bench/llm/KET-QUA.md` mục "Vòng 1"; commit `cc1fbf0` (bộ đo), `40a80c4` (ngân sách ngữ cảnh), `9d4b7c7`, `535bf3c`.

### LM-02 · Việc 1: ngữ cảnh cho Điều dài (30/10/2026)

- **Câu hỏi:** làm sao để dòng chứa đáp án không bị cắt khỏi ngữ cảnh khi Điều dài (bản OCR dính nhiều khoản và điểm thành một dòng 1.500–10.000 ký tự)?
- **Giả thuyết:** lỗi nằm ở đơn vị chọn (dòng quá dài), không ở hàm chấm điểm dòng.
- **Cách làm:** đo **offline**, không gọi mô hình (một lần gọi mất khoảng 50–80 s, một vòng ba bộ khoảng 2,5–3,5 giờ mỗi mô hình): lưu kết quả tìm của mọi câu, dựng ngữ cảnh bằng mã đang thử, đo phần bộ 3-từ của câu trích đáp án còn trong đoạn. 66 câu train văn bản thật có câu trích. Biến thể: tách dòng dài hơn 300 ký tự theo câu, câu đầu dòng là câu dẫn; chấm dòng theo độ hiếm trong Điều (IDF); IDF toàn kho; BM25 theo dòng; 3 đoạn thay 5. Công cụ: `bench/llm/bang_chung.py`.
- **Kết quả** (train văn bản thật, n = 66, ngữ cảnh tự nhiên): câu trích còn ≥ 50% trong đoạn 53% lên 80% (Advance) và 82% (Normal); khi chèn Điều đúng như phép `dan`: 55% lên 82% và 83%; câu còn dưới 10%: 29% xuống 6%. Chỉ đổi cách chấm mà không tách câu: +1 câu. 3 đoạn thay 5: không thêm gì khi đã tách câu. Sau soát (`bc9f9af`, train): 80,3% (Advance), 81,8% (Normal); Normal còn dưới 10% ở 4,5%.
- **Quyết định:** giữ tách câu, IDF trong Điều, lấy khúc quanh chỗ khớp; ngân sách 2.600 xuống 2.400 ký tự (độ dài ngữ cảnh giữ khoảng 2.658 ký tự); giữ 5 đoạn.
- **Vì sao giữ:** đây là thay đổi tác dụng lớn nhất của vòng 2 (lời giải là tách câu, không phải chấm điểm khác). Bản cuối bỏ hẳn tách ở dấu hai chấm làm câu còn bằng chứng tụt 80% xuống 71% (train), nên giữ tách câu dẫn đầu dòng và chỉ gộp nhãn giữa dòng. Không ưu tiên "câu khớp nhất" trước mọi dòng khác: bản đó làm tụt 80,3% xuống 77,3% vì câu khớp nhất đôi khi là khối rác OCR. **Bài học:** (1) Chọn biến thể offline rồi mới chạy mô hình: tiết kiệm hàng giờ máy. (2) Lần ra nguyên nhân bằng cách in độ dài dòng chứa đáp án, hạng của nó theo điểm, độ dài cả Điều: dòng đáp án đứng hạng 0–1 nhưng dài hàng nghìn ký tự thì không vừa ngân sách. (3) So từng câu (trước/sau) những câu có độ phủ đổi hơn 0,2 để thấy lỗi mà số trung bình che.
- **Nguồn:** `bench/llm/KET-QUA.md` mục "Bảy việc đã làm", việc 1; `docs/nghien-cuu/ghi-nho.md` mục 2.3, 3.2, 3.4; commit `7aec13f`, `131ca78`, `bc9f9af`.

### LM-03 · Việc 2: hết cắt JSON (30/10/2026)

- **Câu hỏi:** làm sao để JSON không hỏng khi bị cắt ở trần 200 token?
- **Giả thuyết:** giữ các ý đã viết xong thay vì thay bằng trích nguyên văn sẽ giữ được nội dung có nguồn.
- **Cách làm:** khi bị cắt, giữ các ý đã viết xong (ý đang dở bỏ cả), không thay bằng trích nguyên văn; hạ trần tiền đề sai 200 xuống 150 ký tự và câu trả lời 320 xuống 240 (p95 đo trên train: 101 và 191); khi chuỗi chạm trần bị grammar cắt giữa chữ, bộ kiểm bỏ chữ cuối đang dở.
- **Kết quả:** 7 trên 7 câu bị cắt ở các lần chạy train vòng 1 cứu được và còn ít nhất một ý. Train vòng 2 (126 lần gọi, ba biến thể): bị cắt 2–4 trên 30 ở Zalo, 0 trên 12 ở văn bản thật; đọc được sau cứu 100%. Trên test vòng 2 (Zalo): JSON dùng được 100% nhưng đọc được ngay chỉ 78,8%; bị cắt 21,3%, **cả 17 lần cắt đều là câu bẫy** (17 trên 20 câu bẫy), 15 trong số đó mất hết ý có nguồn.
- **Quyết định:** giữ cách cứu; vấn đề câu bẫy chạm trần còn mở (việc trước P3, điều 1).
- **Vì sao giữ nhưng chưa xong:** JSON đọc được 100% nhưng câu bẫy vẫn đúng 15 trên 17 (chấm theo tiền đề sai) mà mất chip dẫn nguồn. **Bài học:** chỉ số "đọc được" che việc mất nội dung có nguồn; thêm chỉ số "còn ít nhất một ý có nguồn" (đề xuất ở lộ trình mục 9 điều 10a).
- **Nguồn:** `bench/llm/KET-QUA.md` mục "Bảy việc đã làm", việc 2, và "Đọc kết quả (Qwen)"; commit `7aec13f`.

### LM-04 · Việc 3: trường `pham_vi` và A/B ba biến thể (30/10/2026)

- **Câu hỏi:** làm sao để mô hình không khẳng định như đủ căn cứ khi đoạn chỉ nói trường hợp hẹp hơn điều được hỏi?
- **Giả thuyết:** thêm trường `pham_vi` (đúng, hẹp hơn, khác) sinh trước `du_can_cu`, và cho "hẹp hơn" vẫn trả lời kèm phạm vi, sẽ giảm khẳng định sai.
- **Cách làm:** A/B trên train (Zalo 12 câu cộng 6 bẫy; văn bản thật 6 câu), cùng mẫu, mỗi biến thể đổi đúng một thứ, mã `7aec13f`, mỗi biến thể chạy từ một git worktree riêng.
- **Kết quả** (số "a · b" là Zalo · văn bản thật; "khẳng định sai" là câu `tu_choi` trả lời đủ căn cứ với `pham_vi` "đúng"):

  | Biến thể | Dẫn đúng | Từ chối hẳn | Khẳng định sai | Bẫy | Bị cắt |
  |---|---|---|---|---|---|
  | Không có `pham_vi` | 10/12 · 4/6 | 4/12 · 5/6 | 8/12 · 1/6 | 5/6 | 2/30 · 0/12 |
  | "hẹp hơn" buộc từ chối | 10/12 · 4/6 | 5/12 · 5/6 | 7/12 · 1/6 | 5/6 | 3/30 · 0/12 |
  | **"hẹp hơn" vẫn trả lời, nêu phạm vi (chọn)** | 10/12 · 4/6 | 2/12 · 3/6 | **5/12 · 1/6** | 5/6 | 4/30 · 0/12 |

  Đọc tay 8 câu bị gắn "hẹp hơn" khi Điều đúng đã bị bỏ: 5 câu nói rõ đoạn không quy định hoặc không áp dụng, 3 câu vẫn trả lời kèm giới hạn.
- **Quyết định:** giữ biến thể cuối.
- **Vì sao giữ:** ít khẳng định sai nhất trên train (5/12 so với 7/12 và 8/12 ở Zalo). Khi "hẹp hơn" buộc từ chối, mô hình né nhãn đó (3/12 câu so với 6/12) và trả lời "đúng" nhiều hơn. Cái giá: từ chối hẳn giảm nên chỉ số `tu_choi_dung` cũ thấp đi; phải tính cả câu nêu phạm vi hẹp hơn mới phản ánh đúng hành vi. **Bài học:** luật chọn biến thể được đặt là "từ chối hẳn cao nhất" rồi đổi sang "khẳng định sai thấp nhất" sau khi đã xem số; lý do đổi ghi lại (đây là thiết kế đã ghi từ vòng 1 và khẳng định sai mới là chỉ số an toàn), nhưng lần sau chọn đúng chỉ số an toàn ngay từ đầu. Đọc tay các câu đổi kết quả trước khi tin một chỉ số mới. Cỡ mẫu 12 và 6 câu: chỉ đủ chọn hướng, không đủ kết luận.
- **Nguồn:** `bench/llm/KET-QUA.md` mục "Bảy việc đã làm", việc 3, "A/B việc 3"; `docs/nghien-cuu/ghi-nho.md` mục 3.3; commit `b17461f`.

### LM-05 · Việc 4: chặn chữ CJK ngay khi sinh (30/10/2026)

- **Câu hỏi:** chữ Trung, Nhật, Hàn lẫn vào câu trả lời (vòng 1: 3,8% Zalo, 10% gold) có chặn được từ gốc không?
- **Giả thuyết:** loại ký tự CJK khỏi chuỗi trong grammar hiệu quả hơn chỉ lọc sau khi sinh.
- **Cách làm:** mọi chuỗi trong khuôn JSON có `pattern` loại chữ CJK và lối viết `\uXXXX`; trần độ dài ghi trong pattern (`{0,n}`) vì llama.cpp bỏ qua `maxLength` khi có `pattern`.
- **Kết quả:** câu hỏi cố tình đòi trả lời tiếng Trung: không còn chữ CJK (mô hình chuyển sang tiếng Anh hoặc Việt); tốc độ không đổi (23,6 s so với 24,3 s cùng câu); 126 lần gọi train: 0% CJK; test vòng 2 (ba bộ): 0%.
- **Quyết định:** giữ.
- **Vì sao giữ:** CJK về 0% ở mọi bộ, tốc độ không đổi, không cần gọi thêm mô hình.
- **Bài học:** ràng buộc ở lúc sinh (grammar) tốt hơn lọc sau; đo ảnh hưởng tốc độ của ràng buộc. Bẫy: `maxLength` bị bỏ qua khi có `pattern`.
- **Nguồn:** `bench/llm/KET-QUA.md` mục "Bảy việc đã làm", việc 4; `docs/quy-trinh.md` mục 11 (bẫy "llama.cpp bỏ qua `maxLength`"); commit `7aec13f`.

### LM-06 · Việc 5: nới bộ kiểm tham chiếu (30/10/2026)

- **Câu hỏi:** bộ kiểm số liệu bỏ ý vì "số lạ" ở gold (6 lần), không lần nào là số tiền bịa; có quá chặt không?
- **Giả thuyết:** nhãn khoản, số hiệu cụt và số viết bằng chữ làm bộ kiểm bỏ nhầm ý đúng.
- **Cách làm:** "khoản a" là điểm a; số hiệu bị cắt cụt khớp theo phần đầu; đọc số viết bằng chữ ("dưới mười lăm tuổi" cho phép 15, "mười năm" là 10). Đo chẩn đoán: giữ nguyên câu trả lời vòng 1 của tập test (dựng lại đúng ngữ cảnh cũ bằng worktree mã cũ), chỉ thay bộ kiểm và phần cứu JSON.
- **Kết quả** (test, dẫn đúng sau kiểm, trước và sau): Zalo 20 lên 23 trên 30; gold 12 lên 16 trên 20; văn bản thật 7 lên 8 trên 15. Ý bị bỏ vì "số lạ" ở gold 6 xuống 1.
- **Quyết định:** giữ.
- **Vì sao:** bộ kiểm chặn đúng thứ cần chặn (số tiền bịa) nhưng ném nhầm cả ý đúng. Các lượt soát độc lập (SO-01 trước đó, SO-02 và SO-03 sau đó) vẫn tìm thêm lỗi ở cả hai phía: bộ kiểm quá lỏng ("trong 15 ngày" bịa vẫn qua vì số hiệu `QH15`, mã đoạn `[1]`, nhãn khoản `1.` bảo lãnh cho số bịa) lẫn quá chặt ("mười năm" đọc thành 15). **Bài học:** bộ kiểm có hai loại lỗi, bỏ nhầm ý đúng và cho qua số bịa, cần test cho cả hai; thêm luật mới thì thêm test cho đúng loại "bảo lãnh nhầm" này (skill `vietnamese-legal-number-check`). Thử bộ kiểm mới trên câu trả lời cũ đo được phần tăng mà không gọi lại mô hình.
- **Nguồn:** `bench/llm/KET-QUA.md` mục "Bảy việc đã làm", việc 5; commit `7aec13f`, `120eea8`, `131ca78`.

### LM-07 · Vòng 2: Qwen3-VL-4B trên ba bộ test sau bảy việc sửa (30/10/2026)

- **Câu hỏi:** sau bảy việc sửa, Qwen đạt cổng P0 chưa?
- **Giả thuyết:** một phần lỗi vòng 1 nằm ở mã của ta (cắt JSON, cắt mất dòng đáp án), nên sửa mã trước khi kết luận về mô hình sẽ nâng dẫn đúng và giảm khẳng định sai.
- **Cách làm:** mã `b17461f`, đúng ba bộ và cùng mẫu câu như vòng 1; mọi lựa chọn làm trên train hoặc offline; chấm test một lần. **Ngoại lệ:** câu bẫy sinh từ cả kho, không chia train hoặc test, nên 6 trong 20 câu bẫy test đã dùng ở A/B; việc chọn biến thể không dựa vào bẫy (bẫy 5/6 ở cả ba biến thể). Lệnh: ba lệnh ở `bench/llm/KET-QUA.md` mục "Chạy lại".
- **Kết quả** (test: Zalo n = 30 câu cộng 20 bẫy, gold n = 20, văn bản thật n = 15; vòng 1 sang vòng 2):

  | Chỉ số | Zalo | Gold `vle` | Văn bản thật |
  |---|---|---|---|
  | JSON dùng được (tính cả câu cứu) | 87,5% lên 100% | 92,5% lên 100% | 96,7% lên 100% |
  | Dẫn đúng Điều | 66,7% lên 83,3% (20 lên 25/30) | 70,0% lên 75,0% (14 lên 15/20) | 46,7% lên 86,7% (7 lên 13/15) |
  | Khẳng định như đủ căn cứ khi đã bỏ Điều đúng | 66,7% xuống 26,7% (20 xuống 8/30) | 65,0% xuống 40,0% (13 xuống 8/20) | 33,3% xuống 13,3% (5 xuống 2/15) |
  | Từ chối hẳn | 26,7% xuống 16,7% | 35,0% xuống 20,0% | 66,7% xuống 60,0% |
  | Từ chối hoặc nêu phạm vi hẹp hơn | 26,7% lên 73,3% | 35,0% lên 60,0% | 66,7% lên 86,7% |
  | Có Điều đúng mà bị gắn "hẹp hơn" hoặc "khác" | không đo, rồi 26,7% | không đo, rồi 10,0% | không đo, rồi 40,0% |
  | Chữ Trung, Nhật, Hàn | 3,8% xuống 0% | 10,0% xuống 0% | 0% giữ 0% |
  | Mô hình p50 / p95 trên máy ảo | 72 / 93 s thành 57 / 72 s | 63 / 81 s thành 53 / 71 s | 57 / 85 s thành 49 / 68 s |

  So với cổng P0 đề xuất: dẫn đúng ≥ 80% đạt 2 trên 3 bộ; JSON ≥ 99% đạt nếu tính câu đã cứu (đọc ngay chỉ 78,8% ở Zalo); từ chối ≥ 80% không đạt theo cách tính cũ (`du_can_cu = false`), đạt ở văn bản thật nếu tính cả câu nêu phạm vi hẹp hơn. Thời gian không so được giữa hai vòng (máy ảo dùng chung).
- **Quyết định:** mốc, không đạt trọn cổng. Cách tính cổng (câu cứu có tính không; từ chối có tính câu nêu phạm vi hẹp không) là việc chủ dự án chốt (lộ trình mục 9 điều 10, còn mở).
- **Vì sao tăng:** dẫn đúng ở Zalo và văn bản thật, và khẳng định sai ở Zalo, vượt nhiễu; gold chỉ +1 câu (trong nhiễu). Trong 6 câu văn bản thật đổi từ sai sang đúng: 1 nhờ cứu JSON, 3 từ từ chối sang trả lời đúng, 2 từ dẫn nhầm Điều sang dẫn đúng. Không tách được phần của từng việc sửa vì test không chạy bỏ từng phần. **Cái giá:** từ chối hẳn giảm; cảnh báo thừa 10–40% câu có Điều đúng. Cỡ mẫu 15–30 câu mỗi bộ, khoảng tin cậy 95% xấu nhất ±18–25 điểm: chênh 1–2 câu không có nghĩa.
- **Bài học:** (1) Sau khi viết báo cáo, cho hai tác tử độc lập tính lại mọi số từ JSON thô: bắt được "8/8" thật ra là 5/8, rò rỉ câu bẫy, và câu "tăng ở cả ba bộ" trong khi gold chỉ +1 câu. (2) Rò rỉ giữa phần chỉnh và phần chấm phải ghi trong báo cáo (ở đây là câu bẫy). (3) Số test là của `b17461f`; bản soát sau sửa thêm 6 lỗi (`bc9f9af`), nên đo lại ở đợt sau.
- **Nguồn:** `bench/llm/KET-QUA.md` mục "Vòng 2" (bảng "Qwen3-VL-4B, vòng 1 sang vòng 2", "Đọc kết quả (Qwen)", "So với cổng P0 đề xuất"); `docs/nghien-cuu/ghi-nho.md` mục 2.2, 3.5; commit `da68c97`, `b17461f`.

### LM-08 · Chạy lại `bench/llm` sau khi sửa parser: B1 (kế hoạch, chưa có số)

- **Câu hỏi:** sửa parser (N1a, N3) đổi chữ đưa vào mô hình thì chất lượng câu trả lời đổi thế nào?
- **Giả thuyết:** không ghi trước; quy tắc đo lại khi mã liên quan đổi (kế hoạch P1, mục 2b) buộc phải đo.
- **Cách làm đã lên kế hoạch:** hai nhánh cùng mã `bc9f9af` chạy từ một git worktree cố định, chỉ khác kho dữ liệu (bản trước và bản sau khi dựng lại bằng parser cuối); nhúng lại vector cho nhánh mới trước khi chạy; ba lệnh ở `bench/llm/README.md`; ước khoảng 7,5 giờ máy mỗi nhánh.
- **Kết quả:** chưa đo. Ở commit `a13af05`, `bench/llm/KET-QUA.md` vẫn là số P0 của `b17461f`; không thấy kết quả B1 trong repo.
- **Quyết định:** hoãn. Chỉ chạy khi parser đã chốt (đã chốt sau N3) và máy rảnh.
- **Vì sao hoãn:** tranh CPU làm sinh chữ chậm khoảng 10 lần (0,48 so với 5 token/giây) nên số đo hỏng; chạy trên parser chưa chốt thì phải chạy lại khoảng 15 giờ.
- **Bài học:** không so thẳng với số P0 khi mã hoặc dữ liệu liên quan đã đổi; đo lại hai nhánh trước và sau trên cùng mã. Chạy từ worktree cố định để sửa mã không lọt vào lần đo.
- **Nguồn:** `docs/ke-hoach/ke-hoach-p1.md` mục B1; `docs/nghien-cuu/ghi-nho.md` mục 1, 5.

## Nhóm CN: chọn công nghệ (mô hình, kho dữ liệu)

Chung cho cả nhóm: nghiên cứu bằng đọc tài liệu tại nguồn (thẻ mô hình, bảng xếp hạng, README, giấy phép, trang PyPI) vào ngày 29/10/2026 hoặc 30/10/2026; số do hãng tự công bố được đánh dấu "(hãng)" và không so thẳng với số của hãng khác. Mỗi tài liệu có đợt "kiểm lại độc lập" bằng tác tử khác đọc lại tại nguồn.

### CN-01 · Chọn mô hình ngôn ngữ theo benchmark công khai (29/10/2026)

- **Câu hỏi:** mô hình mở nào, chạy llama.cpp trên CPU, RAM khoảng 4 GB (trần 6 GB), tắt chế độ suy nghĩ, kịp 45 s p95 kể cả phần tìm, đáng được chọn khi không có luật sư chấm tay?
- **Giả thuyết:** lộ trình ban đầu đề xuất Qwen3.5-4B.
- **Cách làm:** hơn 10 ứng viên (bảng ứng viên và các mô hình tra thêm rồi loại), so theo bốn nhóm số: bám ngữ cảnh (Vectara Hallucination Leaderboard, một bài RAG báo cáo ESG), tiếng Việt (SEA-HELM bảng ≤ 10B, kể cả bản không suy nghĩ), làm theo chỉ dẫn (IFEval, IFBench, SEA-IFEval), suy luận. Đếm token tiếng Việt bằng `tokenizer.json` trên 1.000 Điều Zalo (255.695 âm tiết) cộng 84 câu của văn bản thật. Ước tính thời gian từ FLOPs và băng thông RAM (xem CN-02).
- **Kết quả** (SEA-HELM tiếng Việt, chế độ không suy nghĩ, điểm trung bình VI; QA trích từ đoạn văn; NLI):

  | Mô hình | VI tổng | QA | NLI | Ghi chú |
  |---|---|---|---|---|
  | Qwen3-VL-4B-Instruct | 64,2 | 77,5 | 50,0 | chỉ có chế độ không suy nghĩ |
  | Gemma 4 E4B | 62,8 | 44,7 | 39,9 | bật suy nghĩ: 67,1 |
  | Qwen3.5-4B | 52,2 | 75,0 | 14,3 | bật suy nghĩ: 69,0 (không vừa 45 s) |

  Vectara (tiếng Anh, giám khảo HHEM-2.3): họ Qwen3.5 có tỉ lệ ảo giác khoảng gấp đôi họ Qwen3 và Gemma 4 (qwen3-4b 5,7%; qwen3.5-27b 12,1%); các bản nhỏ của Qwen3.5 và Gemma 4 không có trên bảng. Bài RAG báo cáo ESG (tiếng Anh, 100 câu, giám khảo cũng là mô hình 4B): faithfulness gemma4:e4b 0,796, qwen3:4b-instruct 0,719. Đếm token: Qwen3 1,293 token mỗi âm tiết (Zalo), Qwen3.5 1,204, Gemma 4 1,251; chênh tối đa 7%.
- **Quyết định:** chọn Qwen3-VL-4B-Instruct (GGUF Q4_K_M chính hãng, 2,33 GiB), dự phòng Gemma 4 E4B (QAT Q4_0). Bỏ Qwen3.5-4B (đề xuất cũ của lộ trình), Qwen3.5-9B và Vi-Qwen2-7B-RAG (quá chậm), Gemma 4 12B (Q4_0 nặng 7,65 GB, vượt trần), các mô hình 2B (yếu tiếng Việt).
- **Vì sao:** ở chế độ dùng được trong 45 s (không suy nghĩ), Qwen3-VL-4B cao nhất nhóm ≤ 5B ở tiếng Việt, và hơn hẳn Gemma ở hai tác vụ gần việc của app nhất (QA trích đoạn 77,5 so với 44,7; NLI 50,0 so với 39,9). Tắt suy nghĩ làm Qwen3.5-4B tụt mạnh (VI 69,0 xuống 52,2; NLI 52,6 xuống 14,3). Rủi ro đã ghi: chưa có số bám ngữ cảnh đo trực tiếp cho đúng mô hình này; kiến thức tiếng Việt thấp (43,4); đôi khi chèn chữ Trung (đã thành LM-05). **Bài học:** (1) Chọn theo tác vụ gần nhất với ứng dụng (QA trích đoạn, NLI), không theo điểm tổng. (2) Điểm của hãng thường đo ở chế độ suy nghĩ; ngân sách 45 s buộc dùng chế độ không suy nghĩ, nên phải lấy số ở đúng chế độ. (3) Không có benchmark luật Việt nào cho ứng viên (VLegalBench, VMLU, VLSP chưa chấm các mô hình này): benchmark công khai chỉ chọn được danh sách rút gọn, quyết định cuối phải đo trên bộ riêng (LM-07, CN-03).
- **Nguồn:** `docs/nghien-cuu/chon-mo-hinh.md` mục 2, 3, 5, 6; commit `bc540db`.

### CN-02 · Ngân sách 45 giây và tốc độ: ước tính, chưa đo trên máy 16 GB (29–30/10/2026)

- **Câu hỏi:** mô hình 4B có chạy xong trong 45 s p95 (từ Enter đến hết câu trả lời, gồm phần tìm) trên máy chuẩn không?
- **Giả thuyết:** không ghi trước; 45 s là ràng buộc chủ dự án chốt ngày 29/10/2026 (nâng từ 30 s), và là ràng buộc chính khi chọn mô hình.
- **Cách làm:** ước tính, không đo. Đọc prompt bị giới hạn bởi tính toán (khoảng 38–40 GFLOPS hiệu dụng mỗi nhân, theo hai số đo công khai trên CPU AVX2, nhân thêm khoảng 1,4–1,5 nhờ sắp xếp lại trọng số và nhân theo khối); sinh chữ bị giới hạn bởi băng thông RAM (34–42 GB/s hiệu dụng cho DDR4-3200 hai kênh). Mỗi câu: 1.500 token prompt mới, 200 token ra, tìm 5 s.
- **Kết quả (ước tính, Qwen3-VL-4B Q4_K_M, máy Ryzen 5 5600GT):** đọc prompt 30–70 token/giây (trung tâm 45), sinh 12–15 token/giây; tổng trung tâm 53 s, p95 bi quan 79 s, lạc quan 36 s; prompt tối đa để vừa 45 s ở mức trung tâm khoảng 1.150 token. Gemma 4 E4B: 57 s, 85 s, 39 s. Mô hình 2B vừa 45 s nhưng yếu. Đo thật duy nhất, trên máy ảo 4 nhân Xeon (không đại diện): đọc prompt khoảng 27 token/giây, sinh khoảng 5,2 token/giây, p50 của Qwen 49–57 s mỗi câu (LM-07). **Trên máy 16 GB Windows: chưa đo.**
- **Quyết định:** hoãn đo; trần prompt giữ khoảng 1.000 token (ngân sách ngữ cảnh 2.400 ký tự, LM-02). Việc cần máy 16 GB: `llama-bench -m <gguf> -t 6 -p 1000,1500 -n 200 -r 5` với Office mở; công thức trần prompt cho p95: prompt tối đa = pp × (36 − 250 / tg); đo p50 và p95 trên từ 100 câu thật; đo RAM của `llama-server`; kiểm máy chạy RAM hai kênh (một kênh thì sinh chữ chậm gần một nửa).
- **Vì sao chỉ ước tính:** môi trường soạn không có máy chuẩn; mọi số tốc độ trong `docs/nghien-cuu/chon-mo-hinh.md` mục 4 là ước tính. **Bài học:** (1) Không mô hình 4B nào chắc chắn vừa 45 s với prompt 1.500 token; ngân sách 45 s buộc cắt prompt. (2) Máy ảo dùng chung không dùng được cho cổng thời gian; chỉ dùng cho tỉ lệ chất lượng. (3) Mọi con số "ước tính" phải được đánh dấu để lượt sau không coi là đã đo.
- **Nguồn:** `docs/nghien-cuu/chon-mo-hinh.md` mục 4, 5 ("Cần đo trên máy 16 GB"), 6; `bench/llm/KET-QUA.md` đoạn mở đầu và "Vòng 1" (tốc độ máy ảo); `bench/llm/README.md`.

### CN-03 · Ba mô hình cùng mã, cùng mẫu: Qwen, Gemma 4 E4B, Nemotron-3.5-Bolt-E4B (30/10/2026)

- **Câu hỏi:** mô hình dự phòng hoặc mô hình mới có hơn Qwen ở lỗi còn lại (khái quát quá phạm vi) không? Lộ trình quy định thử mô hình dự phòng trước khi kết luận về mô hình.
- **Giả thuyết:** Gemma 4 E4B bám ngữ cảnh tốt hơn (faithfulness 0,796 trong bài ESG), đúng chỗ Qwen yếu.
- **Cách làm:** cùng mã vòng 2 (`b17461f`), cùng ba bộ test, cùng mẫu, cùng lời nhắc, khuôn, bộ kiểm, nhiệt độ 0,1; không chỉnh riêng cho mô hình nào. Gemma: GGUF QAT Q4_0 chính hãng 5,15 GB. Bolt: bản bartowski Q4_K_M 5,16 GB. So hai mô hình trên cùng câu bằng McNemar ghép cặp.
- **Kết quả** (gộp ba bộ test: 65 câu `dan`, 65 câu `tu_choi`, 20 câu bẫy, 150 lần gọi mỗi mô hình):

  | | Qwen3-VL-4B | Gemma 4 E4B | Nemotron-3.5-Bolt-E4B |
  |---|---|---|---|
  | Dẫn đúng Điều | **53/65 (81,5%)** | 48/65 (73,8%) | 44/65 (67,7%) |
  | Khẳng định như đủ căn cứ khi đã bỏ Điều đúng | 18/65 (27,7%) | 19/65 (29,2%) | 24/65 (36,9%) |
  | Từ chối hoặc nêu phạm vi hẹp hơn | 47/65 | 46/65 | 41/65 |
  | Từ chối hẳn | 18/65 | 36/65 | 34/65 |
  | Chỉ ra tiền đề sai (bẫy) | 17/20 | 19/20 | 17/20 |
  | Bị cắt ở trần 200 token | 20/150 | 39/150 | 31/150 |
  | Mô hình p50 trên máy ảo (Zalo / gold / văn bản thật) | 57 / 53 / 49 s | 73 / 69 / 67 s | 74 / 65 / 67 s |

  McNemar ghép cặp trên 65 câu `dan`: Qwen với Gemma p = 0,30; Qwen với Bolt p = 0,06.
- **Quyết định:** giữ Qwen làm chính, Gemma làm dự phòng, không chọn Bolt và không đo Bolt trên máy 16 GB.
- **Vì sao:** chênh lệch chất lượng **chưa vượt nhiễu**, nên lý do chọn dựa vào tốc độ và RAM: Qwen nhanh hơn khoảng 20–27% (p50 từng bộ, tệp 2,5 GB so với khoảng 5,2 GB) và viết ngắn nhất. Gemma hơn ở gold (dẫn đúng 17 so với 15 trên 20) và ở bẫy (19 so với 17 trên 20), đều trong nhiễu, nhưng kém ở Zalo (19 so với 25 trên 30). Cả ba mô hình khẳng định sai ở 28–37% số câu khi gộp: **đổi mô hình cùng cỡ không sửa được lỗi phạm vi.** **Bài học:** (1) Dùng McNemar ghép cặp trên cùng câu, không so hai tỉ lệ rời. (2) Khi chênh nằm trong nhiễu, chọn theo chi phí (tốc độ, RAM, dung lượng). (3) Gemma QAT Q4_0 và Bolt Q4_K_M không cùng cách lượng tử hoá, nên so Bolt với Gemma gốc không sạch hoàn toàn. (4) Thời gian chỉ so tương đối: ba mô hình chạy ở các giờ khác nhau trên máy ảo dùng chung.
- **Nguồn:** `bench/llm/KET-QUA.md` mục "Vòng 2" (bảng "Ba mô hình"); `docs/nghien-cuu/ghi-nho.md` mục 2.2; commit `3d4c0d5`, `0ed2ed6`.

### CN-04 · Tìm thêm một ứng viên sau vòng 2 (30/10/2026)

- **Câu hỏi:** có mô hình mới nào, vừa RAM và 45 s, có bằng chứng sửa được lỗi khái quát quá phạm vi bằng tiếng Việt không? (Người dùng yêu cầu tìm thêm.)
- **Giả thuyết:** một mô hình mới, được huấn luyện thêm cho việc bám ngữ cảnh (Nemotron-3.5-Bolt-E4B), có thể sửa được lỗi này.
- **Cách làm:** bốn hướng tìm độc lập (mô hình nhỏ mới của các hãng; bản tinh chỉnh tiếng Việt và Đông Nam Á; bảng xếp hạng bám ngữ cảnh, tiếng Việt, làm theo chỉ dẫn; hỗ trợ llama.cpp), một bước gộp và xếp hạng theo đúng lỗi đang gặp, hai bước kiểm chứng ngược tại nguồn (thẻ mô hình, giấy phép, tệp GGUF, llama.cpp, số benchmark). Rồi đo ứng viên trên đúng bộ đo, cùng mã, không chỉnh riêng.
- **Kết quả:** xếp hạng: (1) Nemotron-3.5-Bolt-E4B (Gemma 4 E4B huấn luyện thêm bằng RL; số của hãng, tiếng Anh: GaRAGe 40,73 so với Gemma 4 E4B 30,91 khi bật suy nghĩ); (2) LFM3-1.7B (giấy phép giới hạn doanh thu dưới 10 triệu USD; 1,7B khó đọc đúng phạm vi); (3) Granite 4.2 3B (tiếng Việt chưa thử); (4) Gemma-SEA-LION-v4-4B-VL (gốc cũ); (5) MiniCPM5-2B (chỉ en và zh). Đo Bolt: CN-03, kém Qwen và Gemma khi gộp; không thấy mức tăng GaRAGe; một phép thử RAG tiếng Hàn độc lập (299 câu, tắt suy nghĩ) cũng không thấy Bolt hơn Gemma 4 E4B (63,2% so với 65,2%).
- **Quyết định:** không chọn Bolt. Kết luận của lần tìm: trong các mô hình mới tới 30/10/2026 vừa ràng buộc, không thấy mô hình nào có bằng chứng sửa lỗi này bằng tiếng Việt; hướng tiếp theo ở luồng xử lý (bước kiểm phạm vi riêng, tín hiệu điểm tìm kiếm thấp), không ở việc đổi mô hình cùng cỡ.
- **Vì sao thất bại:** số bám ngữ cảnh do hãng công bố bằng tiếng Anh không chuyển sang tiếng Việt, và mức tăng GaRAGe là phụ phẩm (không có môi trường RL nhắm bám ngữ cảnh). **Bài học:** (1) Xếp hạng ứng viên theo đúng lỗi đang gặp, không theo điểm tổng. (2) Số của hãng, bằng ngôn ngữ khác, là giả thuyết, không phải bằng chứng; đo lại trên bộ của mình. (3) Ghi cả chỗ nguồn tự mâu thuẫn (giấy phép của Gemma-SEA-LION-v4.5-E2B ghi MIT ở trường `license` nhưng `license_link` trỏ giấy phép Gemma 4), để người quyết định tự đọc lại.
- **Nguồn:** `docs/nghien-cuu/chon-mo-hinh.md` mục 7, 2; `docs/nghien-cuu/ghi-nho.md` mục 3.6; commit `0ed2ed6`.

### CN-05 · Chọn kho dữ liệu cho phần truy hồi: giữ SQLite + FTS5 (29/10/2026)

- **Câu hỏi:** có nên thêm CSDL hoặc bộ máy truy hồi khác (vector DB, kho đồ thị, framework "bộ nhớ AI") cho phần tìm của bản 1.0 không?
- **Giả thuyết:** đổi CSDL có thể làm câu trả lời đúng hơn hoặc nhanh hơn.
- **Cách làm:** mười tiêu chí; bắt buộc: giấy phép OSI không copyleft trong tiến trình app, Windows chạy thẳng (không Docker, WSL, quyền admin), offline, RAM phần truy hồi ≤ khoảng 2–2,5 GB, tiếng Việt có dấu và không dấu, phrase và NEAR, BM25 có trọng số cột, lọc, giao dịch. Hơn 20 ứng viên đọc tại nguồn ngày 29/10/2026 (SQLite, sqlite-vec, DuckDB, LanceDB, Chroma, Qdrant, Meilisearch, Typesense, Weaviate, Milvus Lite, PostgreSQL + pgvector, OpenSearch, Elasticsearch, Tantivy, txtai, zvec, libSQL; thư viện vector USearch, FAISS, hnswlib; kho đồ thị Kùzu, LadybugDB, Neo4j, FalkorDB, Memgraph, ArangoDB, Apache AGE). Đối chiếu với thời gian thật của một câu Advance.
- **Kết quả:** phần phụ thuộc CSDL chỉ chiếm tối đa khoảng 1 s trong khoảng 9 s của một câu Advance (p50 8,6 s); reranker chiếm khoảng 5 s. Độ chính xác nằm ở thuật toán: BM25 trên cột không dấu Hit@10 77,7%, trên cột có dấu 84,9% (Zalo test, n = 788; TK-01). Lý do loại: Meilisearch bỏ dấu với chữ Latin và không thấy cách tắt; Typesense GPL-3.0 và Windows chỉ qua WSL; Weaviate không có bản Windows; Chroma có full-text chỉ để lọc, tìm kết hợp chỉ có trên Cloud; DuckDB lưu chỉ mục HNSW xuống đĩa còn thử nghiệm và không thấy phrase hay NEAR; LanceDB bỏ dấu mặc định và là kho thứ hai (thêm khoảng 110 MB); Qdrant thêm tiến trình và kho thứ hai (BM25 mới có từ 22/10/2026); Elasticsearch AGPL, SSPL; Kùzu đã archived 10/10/2025; FalkorDB SSPL; Memgraph, ArangoDB BSL; Neo4j GPL-3.0 và JVM.
- **Quyết định:** giữ SQLite (WAL) + FTS5 làm kho duy nhất; vector giữ vét cạn bằng NumPy trong RAM (CN-06); quan hệ văn bản (P4) để trong bảng SQLite, đi đồ thị bằng CTE đệ quy; không dùng framework đồ thị tri thức (CN-07); sqlite-vec chưa dùng (bản ổn định chỉ quét toàn bộ, chậm hơn NumPy 6–7 lần, trước v1).
- **Vì sao giữ:** không thêm byte vào bộ cài (SQLite có sẵn trong Python Windows), một file, một giao dịch, một cơ chế sao lưu; mọi ứng viên khác trái ràng buộc hoặc thêm kho thứ hai và buộc viết lại `search.py` mà không có lợi ích đo được. **Bài học:** (1) Hỏi "bước này chiếm bao nhiêu giây" trước khi đổi công nghệ: đổi CSDL không làm đúng hơn và chỉ bớt được một phần của khoảng 1 s. (2) Ràng buộc cứng (nền Windows không admin, giấy phép, offline) loại gần hết ứng viên trước khi so tính năng; xếp ràng buộc cứng lên trước. (3) Ghi "không thấy trong tài liệu (ngày)" thay vì suy ra "không hỗ trợ".
- **Nguồn:** `docs/nghien-cuu/chon-csdl.md` mục 2–4, 6; `docs/ke-hoach/lo-trinh-1.0.md` mục 4b; commit `2c2239a`.

### CN-06 · Đo tìm vector trong sandbox: NumPy, USearch, sqlite-vec (29/10/2026)

- **Câu hỏi:** nếu nhúng theo khoản (250.000 vector thay vì 61.000), cách giữ vector nào vừa RAM và nhanh?
- **Giả thuyết:** RAM mới là ràng buộc, không phải tốc độ.
- **Cách làm:** 250.000 vector tổng hợp 1024 chiều (512 cụm cộng nhiễu, chuẩn hoá L2), 61.425 dòng đầu làm bộ 61K; 100 câu hỏi; p50 của top-50; recall@50 so với tìm chính xác bằng float32. Sandbox Xeon 2,10 GHz, 4 vCPU, có AVX-512, L3 260 MiB (máy chuẩn: AVX2, L3 16 MB). Kịch bản nằm ngoài repo (thư mục tạm của phiên soạn).
- **Kết quả** (p50 một truy vấn, 1 luồng / 4 luồng):

  | Cách | RAM 61K | 61K | RAM 250K | 250K | recall@50 |
  |---|---|---|---|---|---|
  | NumPy f32 (cách app đang làm) | 240 MB | 19,0 / 3,8 ms | 977 MB | 77,0 / 26,5 ms | 1 |
  | USearch exact f16 | 120 MB | 28,5 / 8,0 ms | 488 MB | 118 / 38,0 ms | 0,9998 / 1 |
  | USearch exact i8 (thang ±127) | 60 MB | 17,3 / 5,5 ms | 244 MB | 73,6 / 29,6 ms | 0,950 / 0,909 |
  | sqlite-vec `vec0` float (1 luồng) | 242 MB (tệp) | 123 ms | 989 MB (tệp) | 521 ms | 1 |
  | USearch HNSW f16, ef = 256 | thêm 137 MB | 2,7 ms | thêm 554 MB | 1,14 ms | 0,999 |

- **Quyết định:** giữ NumPy f32 ở 61.000 vector; khi ma trận f32 vượt khoảng 500 MB (khoảng 125.000 vector) hoặc RAM đỉnh Advance trên máy chuẩn vượt 2,5 GB thì chuyển f16 trong RAM cộng USearch exact; i8 cộng chấm lại bằng f16 khi vượt khoảng 250.000 vector; HNSW chỉ khi bước tìm vector vượt khoảng 150 ms p95. Mỗi bước phải qua quy tắc 7.
- **Vì sao:** mọi cách vét cạn trong RAM đều ≤ 0,2 s ở 250K vector, nhỏ hơn 2–3% của khoảng 9 s; RAM mới chặn (f32 ở 500K khoảng 1,95 GB, cộng hai mô hình thì vượt ngân sách 2–2,5 GB). sqlite-vec chậm hơn NumPy 6–7 lần. i8 thang ±127 mất 5–9% recall@50. **Chưa kiểm:** USearch trên Windows (wheel `numkong` chỉ 0,47 MB so với 10,1 MB bản Linux, có thể ít nhân SIMD hơn); vector thật AITeamVN (recall của HNSW và i8 trên vector thật chưa biết); máy chuẩn (L3 260 MiB làm số 61K lạc quan). **Bài học:** đặt ngưỡng kích hoạt cụ thể (500 MB, 150 ms) thay vì tối ưu sớm; vector tổng hợp chỉ cho so sánh tương đối.
- **Nguồn:** `docs/nghien-cuu/chon-csdl.md` mục 5, 6.2, 6.6, 8.

### CN-07 · Framework đồ thị tri thức dựng bằng LLM: không dùng (29/10/2026)

- **Câu hỏi:** có nên dùng Cognee, Graphiti, LightRAG, GraphRAG, HippoRAG 2, Mem0, LlamaIndex PropertyGraph hay neo4j-graphrag để dựng đồ thị tri thức cho kho luật?
- **Giả thuyết:** đồ thị tự dựng giúp hỏi theo quan hệ (phản hồi ⑧).
- **Cách làm:** đọc mã nguồn và tài liệu từng framework để đếm số lệnh LLM khi nạp và khi hỏi; ước tính thời gian dựng cho 61.425 Điều (khoảng 331 token mỗi Điều, tổng khoảng 20,3 triệu token) với giả định Qwen3-VL-4B đọc 45 token/giây, sinh 13 token/giây (CN-02, chưa đo), phần chỉ dẫn cố định dùng lại từ cache. Cỡ chỉ dẫn đếm thô (số ký tự chia 4), số token ra và số cạnh mỗi Điều là giả định.
- **Kết quả (ước tính, thời gian CPU chạy liên tục):** sàn cho mọi framework (chỉ đọc kho một lượt): 5,2 ngày; LlamaIndex `SimpleLLMPathExtractor` khoảng 10 ngày; Mem0 khoảng 17 ngày; Cognee khoảng 23 ngày; LightRAG khoảng 25 ngày; GraphRAG và HippoRAG 2 khoảng 33 ngày; Graphiti khoảng 175 ngày (có cache) đến 360 ngày (không cache). Khi hỏi, mỗi lệnh LLM thêm khoảng 5–25 s (ước tính), ngân sách 45 s đã gần chạm với một lệnh trả lời. Chính các framework khuyên mô hình lớn hơn: LightRAG ghi Qwen3-30B-A3B là mức tối thiểu khi chạy cục bộ; Graphiti và GraphRAG cảnh báo mô hình nhỏ trả sai schema. Không tìm thấy benchmark trích thực thể và quan hệ tiếng Việt nào cho Qwen3-VL-4B.
- **Quyết định:** bỏ. Chỉ lấy ý tưởng: cạnh có hai trục thời gian và vô hiệu chứ không xoá (Graphiti), mỗi cạnh nhớ nguồn, backlinks và đồ thị cục bộ 1–2 bước bằng CTE đệ quy, cạnh "nội dung tương tự" từ vector có sẵn (ghi rõ không phải quan hệ pháp lý).
- **Vì sao:** không khả thi trên máy 16 GB không GPU (sàn đã là 5 ngày CPU 100%); chất lượng chưa có bảo đảm; trái nguyên tắc "máy gợi ý, người quyết" và "không dùng LLM lập chỉ mục chạy nền" (lộ trình mục 5 và 10). Quan hệ cần cho P4 (căn cứ, hướng dẫn, sửa đổi, thay thế, bãi bỏ, dẫn chiếu) có câu chữ gần như cố định nên trích bằng quy tắc, chạy vài mili giây mỗi văn bản. **Bài học:** một phép nhân thô (token nhân tốc độ) đủ để loại cả một họ giải pháp, miễn là ghi rõ đó là ước tính và các giả định; chỉ lấy ý tưởng khi framework không hợp ràng buộc.
- **Nguồn:** `docs/nghien-cuu/chon-csdl.md` mục 4.4, 4.5, 6.5; `docs/ke-hoach/lo-trinh-1.0.md` mục 2 điều 9, mục 10.

## Nhóm HT: kết quả gọn, trình đọc, lịch sử trò chuyện (P1)

Chung cho cả nhóm: mã nằm ở `src/soiluat/` (`cards.py`, `answer.py`, `reader.py`, `conversations.py`, `app.py`), kế hoạch ở `docs/ke-hoach/ke-hoach-p1.md` (mã việc K, R, H ghi trong ngoặc). Đo trên bản sao chỉ đọc của kho, Normal (`SOILUAT_SEMANTIC=0`).

### HT-01 · K1: kết quả gọn theo (văn bản, Điều) (31/10/2026)

- **Câu hỏi:** danh sách khoảng 40 thẻ mỗi câu (phản hồi ③) có xuống tối đa 5 mục hiển thị mà không mất đáp án không?
- **Giả thuyết:** gộp theo (văn bản, Điều) và gộp nội dung trùng giữa các văn bản ("Cũng có ở") sẽ làm danh sách ngắn.
- **Cách làm:** `cards.compact` (gộp theo `cards._group_key`; Điều cùng nội dung ở văn bản khác gộp theo `content_sig`, bản đại diện còn hiệu lực rồi mới hơn); `answer.snippet` (phần trích 350 ký tự quanh dòng khớp); `_pick` tách ruột nhưng trả đúng chuỗi cũ (test so 1.200 ca ngẫu nhiên với bản chép nguyên, nên `bench/llm` không đổi); số hiệu một mình ra mục "Mở toàn văn". Đo trên 84 câu văn bản thật. 16 test mới.
- **Kết quả** (văn bản thật, n = 84 câu, Normal): 39,8 mục mỗi câu; 5 mục đầu đến từ 2,44 văn bản; 0 mục gộp (21 văn bản không có Điều nào trùng nội dung); `_ctx` trung vị 219 ms, p95 379 ms; độ phủ dòng bằng chứng trong phần trích 350 ký tự là 76%. Khảo sát (chưa chạy lại): gộp trùng chỉ giảm khoảng 2% số mục ở Zalo.
- **Quyết định:** giữ. Bỏ khối chế tài khỏi danh sách (mẫu không có khối này); thẻ hạng 1–2 lấy chế tài từ Điều khác nên phần trích từ chính Điều không thay được, kế hoạch dặn kiểm điều này.
- **Vì sao:** số mục hiện sẵn giảm từ khoảng 40 xuống 5 là do mức cắt hiển thị, không do gộp trùng. **Bài học:** đo đóng góp của từng cơ chế trước khi hứa kết quả: phần gộp trùng tốn công (`content_sig`, đại diện) nhưng gần như không góp vào mục tiêu giảm số mục ở dữ liệu hiện có.
- **Nguồn:** `docs/ke-hoach/ke-hoach-p1.md` mục K1, "Đã kiểm"; commit `01170bf`.

### HT-02 · K3: đo theo mục hiển thị, cổng P1 (31/10/2026)

- **Câu hỏi:** Hit@k tính theo mục hiển thị (sau `cards.compact`) có thấp hơn mốc theo thẻ không? (Cổng P1: Hit@1 và @5 theo mục không thấp hơn mốc theo thẻ trên cùng bản dựng.)
- **Giả thuyết:** gộp theo mục không làm tụt Hit@1 và Hit@5.
- **Cách làm:** hai cách tính, báo cả hai ở mọi bộ: "kèm Cũng có ở" (trúng nếu đáp án nằm ở bản đại diện hoặc một bản trùng) và "chỉ bản đại diện". Cổng theo bộ (chủ dự án duyệt 31/10/2026): Zalo và gold tính kèm bản trùng vì kho Zalo gần như không có ngày ban hành để chọn bản đại diện; văn bản thật tính bản đại diện. Lệnh: `python -I bench/zalo/eval.py <zalo> <data> test --tag muc --only hien_tai,hien_tai_muc,hien_tai_muc_dai_dien`; `bench/van-ban-that/eval_real.py`.
- **Kết quả** (Normal, bản dựng sau N1a, mã `c803116`):

  | Bộ | Cách tính | Hit@1 | Hit@5 | Hit@10 | MRR@10 |
  |---|---|---|---|---|---|
  | Zalo test, n = 788 | theo thẻ (mốc) | 58,6 | 86,3 | 90,5 | 0,710 |
  | | theo mục, kèm "Cũng có ở" (cổng) | 61,0 | 86,4 | 90,5 | 0,723 |
  | | theo mục, chỉ bản đại diện | 58,6 | 83,6 | 87,7 | 0,697 |
  | Gold `vle`, n = 500 | theo thẻ (mốc) | 51,2 | 77,0 | 84,2 | 0,624 |
  | | theo mục, kèm "Cũng có ở" (cổng) | 52,6 | 77,4 | 84,4 | 0,632 |
  | | theo mục, chỉ bản đại diện | 51,2 | 76,0 | 82,8 | 0,617 |
  | Văn bản thật, n = 84 (rộng) | theo thẻ và theo mục | 83,3 | 96,4 | 96,4 | không ghi |

  Theo mục chỉ thêm khoảng 74 ms mỗi câu (p50, Zalo). Văn bản thật: 0 mục gộp nên theo mục bằng theo thẻ; 39,5 mục mỗi câu, 5 mục hiện sẵn.
- **Quyết định:** giữ; cổng P1 đạt ở cả ba bộ.
- **Vì sao:** chỉ tính bản đại diện thì Zalo @5 thấp hơn 2,7 điểm vì đáp án Zalo hay nằm ở bản trùng mà bản đại diện (chọn theo hiệu lực và ngày ban hành) khác, kho Zalo thiếu cả hai. **Bài học:** định nghĩa "theo mục" cần chốt trước khi đo; báo cả hai cách để thấy phần chênh; đo xong trước lô sửa theo soát nên ghi rõ có phải đo lại không (kế hoạch ghi: không, vì các sửa sau không đổi Điều của mục).
- **Nguồn:** `bench/zalo/KET-QUA.md`, `bench/gold/KET-QUA.md`, `bench/van-ban-that/KET-QUA.md` (cùng mục "P1 K3: đo theo mục hiển thị"); `docs/ke-hoach/ke-hoach-p1.md` mục 2b, K3; commit `c803116`, `fb01c53`.

### HT-03 · Trình đọc trong app: R1, R2, R3 (31/10/2026)

- **Câu hỏi:** bấm trích dẫn có mở đúng đoạn trong app, trong ≤ 1 giây với kho 61 nghìn Điều không? (Cổng P1.)
- **Giả thuyết:** dựng thân văn bản có neo ở máy chủ đủ nhanh (kế hoạch khảo sát: 190–237 ms cho văn bản 2.692 đơn vị).
- **Cách làm:** `reader.py` dựng thân văn bản; route `/doc` (GET `/unit` chuyển hướng 303); ngăn kéo hoặc cột thứ ba; tab "Bản gốc" cuộn liên tục các trang PDF, PNG, JPG (chủ dự án yêu cầu 31/10/2026: "cho phép cuộn pdf trong giao diện, để cho phép trích dẫn hay cuộn đến đúng đoạn"; thay cho bộ chuyển trang của kế hoạch). Đo `python -I bench/doc_open.py <data Zalo>` bằng TestClient trên bản sao Zalo (văn bản nhiều đơn vị nhất và 100 văn bản ngẫu nhiên).
- **Kết quả:** phía máy chủ: p50 14 ms, p95 27 ms (n = 101 văn bản); văn bản lớn nhất (2.823 đơn vị, HTML 1,6 MB) 121 ms. Cổng ≤ 1 s đạt phía máy chủ; thời gian trình duyệt vẽ trang 1,6 MB **chưa đo** (bấm tay ở Z1). 9 test của R1 hỏng trên mã cũ. Kiểm ảnh Playwright trên kho 21 văn bản thật: 12/12 đạt (1440/768/390, sáng và tối, không cuộn ngang, đúng một h1). Phát hiện khi kiểm R3: `388/2026/NĐ-CP` điểm g khoản 4 Điều 9 mở đúng trang 9, nhưng trang đó là Phụ lục (bảng mẫu biểu) mà parser gộp vào Điều 9 thành "khoản 5" và "điểm g", nên đoạn được chọn là rác; phát hiện này dẫn tới ứng viên B2 của PS-07. Khi trình đọc mở ở 1440px, cột giữa chỉ còn khoảng 500 px và thẻ cũ của 0.8 bị cắt mép phải; danh sách mới phải vừa cột này (đo sau ở K2: 432 px, không phần tử nào tràn).
- **Vì sao giữ:** cổng ≤ 1 s đạt phía máy chủ với dư rất lớn; cuộn liên tục thay bộ chuyển trang vì chủ dự án muốn cuộn tới đúng đoạn để trích dẫn.
- **Quyết định:** giữ. Khung tô đoạn trên ảnh trang: hoãn sang P2 (cần lưu toạ độ chữ khi nạp). TIFF và BMP trong tab Bản gốc: dời sang P5 (21/21 văn bản thật là `.pdf`).
- **Bài học:** (1) Kiểm trên kho thật bằng ảnh lộ lỗi dữ liệu mà test đơn vị không thấy (parser gộp Phụ lục). (2) Kiểm bố cục ở trạng thái ghép (mở trình đọc cạnh danh sách), không chỉ từng màn riêng. (3) Phải ghi rõ phần đo phía máy chủ khác phần trình duyệt.
- **Nguồn:** `docs/ke-hoach/ke-hoach-p1.md` mục R1, R2, R3, "Đã kiểm"; `bench/van-ban-that/KET-QUA.md` mục "P1 K3"; commit `1f06ddc`, `48a468e`, `8354462`, `fb01c53`.

### HT-04 · Lịch sử trò chuyện: lưu, mở lại không tìm lại, "Xem lại" (31/10/2026)

- **Câu hỏi:** mở lại một cuộc trò chuyện cũ có thể hiện đúng kết quả mà không chạy lại tìm kiếm, và đủ nhanh không?
- **Giả thuyết:** dựng lại từng tin từ danh sách tham chiếu đã lưu bằng `cards.compact` đủ nhanh (kế hoạch ước 100–150 ms mỗi tin, cuộc 10 câu không quá khoảng 1,8 s).
- **Cách làm:** lưu mỗi kết quả thành tham chiếu `(doc_id, path, băm chữ và số hiệu)`, tối đa 150, không lưu chữ; `GET /c/{id}` dựng lại từ tham chiếu, tham chiếu hỏng (văn bản bị xoá, nạp lại đổi chữ, id bị văn bản khác chiếm) hiện dải "N/M kết quả không còn đúng nguồn" kèm "Hỏi lại". Ngưỡng quyết định đặt trước: xây "Xem lại" (chỉ dựng sẵn các tin cuối) nếu dựng đủ cuộc 10 câu trung vị vượt 2 s.
- **Kết quả:** `compact` thật trung vị 197 ms (p95 290 ms), không phải 100–150 ms như ước; cuộc 10 câu dựng đủ trung vị 2,41 s, tối đa 2,69 s, 7 trên 8 cuộc vượt 2 s (TestClient). Sau khi xây "Xem lại" (3 tin cuối dựng sẵn, tin cũ bấm mới dựng): qua HTTP thật mở cuộc 10 câu trung vị 713 ms, tối đa 918 ms; một tin 233 ms (p95 319 ms). `POST /ask` trung vị 411 ms so với `GET` 390 ms; `result_json` khoảng 4,1–4,2 KB cho 100 tham chiếu; 17 test của H2 và 12 test của H3 đều hỏng trên mã cũ.
- **Quyết định:** giữ, kèm "Xem lại".
- **Vì sao:** ước tính sai gần gấp đôi (197 ms so với 100–150 ms) nên cuộc 10 câu vượt ngưỡng; ngưỡng đặt trước giúp quyết nhanh, không cãi. Lưu tham chiếu kèm băm thay vì chữ để văn bản đổi thì báo "không còn đúng nguồn". **Bài học:** đo trước khi xây phần tối ưu có điều kiện; lưu tham chiếu có băm kiểm tính toàn vẹn; lượt soát sau (SO-07) vẫn tìm ra tham chiếu cũ nhận nhầm khi id bị tái dùng.
- **Nguồn:** `docs/ke-hoach/ke-hoach-p1.md` mục H1, H2, H3, H4, H6; commit `d6656ee`, `2117677`, `f27115c`, `0bfc8ee`, `877d59e`.

### HT-05 · H5: ghi lượt mở trích dẫn để chỉnh `SURE_GAP` (hoãn)

- **Câu hỏi:** có nên ghi lượt mở trích dẫn (bảng `citation_opens`, route `POST /api/open`) ở P1 để chỉnh ngưỡng `SURE_GAP` của nhãn "độ tin cậy cao"?
- **Giả thuyết:** lượt mở trích dẫn của người dùng thật cho đủ dữ liệu để chỉnh `SURE_GAP`.
- **Cách làm:** chỉ thiết kế, không xây ở P1 (bảng, route và ca CSRF dời cùng).
- **Kết quả:** chưa có số; kế hoạch chốt ngày 31/10/2026 dời việc này (lộ trình mục 9 điều 13 đã nêu bỏ `citation_opens` là một đường cắt).
- **Quyết định:** hoãn sang nhánh độ chính xác (0 ngày ở P1).
- **Vì sao:** việc duy nhất của nó là chỉnh `SURE_GAP`, mà `gap` là NULL ở Normal (chế độ mặc định đề xuất) và Advance không thuộc cổng P1; hai ngày thử với 3–5 người cho vài chục lượt mở, không đủ để chỉnh một ngưỡng; H5 còn sửa `CascadeResult` trong `search.py`, tức đụng mã tìm kiếm chịu quy tắc 7. Thiết kế để lại cho nhánh chính xác (bảng không khoá ngoại để xoá cuộc không làm mất dữ liệu chỉnh ngưỡng; `AUTOINCREMENT` của `messages` giữ id không tái dùng). Tiết kiệm 0,5 ngày và bỏ một ca CSRF. **Bài học:** đừng xây hạ tầng thu số liệu khi cỡ mẫu dự kiến không đủ để dùng số đó.
- **Nguồn:** `docs/ke-hoach/ke-hoach-p1.md` mục H5, mục 1 (hỏi (a)); `docs/ke-hoach/lo-trinh-1.0.md` mục 6 (nhánh song song, điều 4).

## Nhóm GD: giao diện mẫu

### GD-01 · Mẫu giao diện thế hệ 1 (30/10/2026): chủ dự án đánh giá không dùng được

- **Câu hỏi:** một mẫu HTML tĩnh bấm thử được cho P1 có đủ để chủ dự án duyệt hướng giao diện không? (Lộ trình P0, bước 5.)
- **Giả thuyết:** người dùng góp ý được trên mẫu trước khi viết mã P1 (theo thông điệp commit).
- **Cách làm:** `mau/giao-dien-1.0.html` bản đầu: màn hỏi đáp có lịch sử, câu trả lời AI có căn cứ và tiền đề sai, kết quả gọn khi tắt AI, trình đọc mở đúng đoạn, `@văn bản` và `#tag`, trang Kho, bảng Liên quan và đồ thị cục bộ, huy hiệu hiệu lực có lý do. Chữ luật lấy nguyên văn từ kho Zalo; ngày, hiệu lực, quan hệ là dữ liệu minh hoạ.
- **Kết quả:** ngày 31/10/2026 chủ dự án báo giao diện này không dùng được. Lý do cụ thể chủ dự án không ghi lại trong repo; chỉ có câu "không dùng được" ở `docs/ke-hoach/lo-trinh-1.0.md` mục 9 điều 9.
- **Quyết định:** bỏ, dựng lại (GD-02).
- **Vì sao thất bại (suy luận, chưa xác nhận):** mẫu vẽ cả phần P2 đến P4 (Kho, @ và #, Liên quan, huy hiệu hiệu lực có lý do) trong khi P1 chỉ làm một phần; mẫu thế hệ 2 đặt quy tắc "chỉ vẽ những gì P1 làm, kể cả trạng thái lỗi và rỗng". **Bài học:** hỏi rõ lý do khi một mẫu bị bác và ghi lại ngay; thiếu lý do thì lượt sau chỉ đoán được từ cách sửa.
- **Nguồn:** commit `2f0f018`, `ad6e8e2`, `ba12152`; `docs/ke-hoach/lo-trinh-1.0.md` mục 9 điều 9.

### GD-02 · Mẫu thế hệ 2 dựng lại theo taste-skill, được duyệt (31/10/2026)

- **Câu hỏi:** dựng lại toàn bộ mẫu theo taste-skill (repo `leonxlnx/taste-skill`, `references/app-screens.md`: màn hình làm việc, kiểu "achromatic ledger", một màu nhấn) có đạt duyệt không?
- **Giả thuyết:** không ghi trước; mục tiêu là một mẫu "dùng được" theo chủ dự án.
- **Cách làm:** khung thanh bên lịch sử, luồng ở giữa, trình đọc bên phải; kết quả gọn 5 mục, "Cũng có ở"; đoạn được dẫn tô một màu (bút bi xanh) kèm vạch lề; một cuộc "xem trước câu trả lời AI" ghi rõ là bản thử. Kiểm bằng ảnh Playwright (skill `html-mockup-visual-check`), không chạy script đo của taste-skill vì đó là mã tải về và bị bộ phân loại quyền chặn. Hai lượt soát: soát độc lập (47 phát hiện còn đứng sau bước bác bỏ, SO-04) và soát đối chiếu phản hồi gốc (`c6b5fef`).
- **Kết quả:** Playwright 25 trạng thái ở 1440/1100/768/390, sáng và tối: 0 lỗi console, 0 cuộn ngang, đúng một h1. Một lỗi bố cục đáng kể do soát đối chiếu tìm ra: mẫu vẽ mỗi điểm một hàng và lặp tên Điều, trong khi app thật gộp theo (văn bản, Điều); mẫu hứa một hình mà P1 không ra. Sau duyệt, mẫu chỉ được sửa dữ liệu minh hoạ và chữ cho khớp mã. Bẫy CSS: quy tắc `.scrim { display: grid }` đè thuộc tính `hidden`, luôn thêm `[hidden] { display: none !important; }`. Khi làm P1 thật, `bench/kiem_anh.js` chụp lại: 12/12 ở G0 và R2a, 24/24 ở K2 (4 truy vấn).
- **Quyết định:** giữ; chủ dự án duyệt ngày 31/10/2026 (lộ trình mục 9 điều 9). Mẫu P1 gỡ chặn mã P1.
- **Vì sao giữ:** vẽ đúng thứ mã làm được, kể cả trạng thái lỗi và rỗng (ref hỏng, chưa lưu được lịch sử, tệp gốc mất, kho trống, nâng cấp dữ liệu). **Bài học:** (1) Mẫu phải khớp mã: nếu mẫu hứa một bố cục mà bộ gộp của app không tạo ra thì người duyệt duyệt một thứ không tồn tại. (2) Kiểm giao diện bằng ảnh ở nhiều cỡ, sáng và tối, từng trạng thái, rồi mở từng ảnh mà xem; không kiểm bằng đọc mã. (3) Không chạy script tải từ ngoài để lách bộ chặn.
- **Nguồn:** commit `ad6e8e2`, `9e5cf35`, `c6b5fef`; `docs/quy-trinh.md` mục 11 (bẫy giao diện, "Kiểm giao diện bằng đọc mã"); `docs/ke-hoach/lo-trinh-1.0.md` mục 9 điều 9.

### GD-03 · Bản mẫu khái niệm: dự án, sổ rủi ro, trình đọc có Liên quan và đồ thị (31/10/2026, chưa duyệt)

- **Câu hỏi:** giao diện lớn từ P1 lên dự án (nhóm văn bản), ghi chú, sổ rủi ro và sơ đồ quan hệ kiểu Obsidian trông thế nào để việc thật của khách (gõ từ khoá, ra rủi ro kèm điều luật nguyên văn) làm tốt nhất? (Yêu cầu của chủ dự án 31/10/2026.)
- **Giả thuyết:** không ghi trước; bản định hướng nêu ba việc dùng để thử mọi màn hình (gõ từ khoá ra rủi ro kèm điều luật; biết một nghị định còn hiệu lực không; biết dự án còn thiếu văn bản nào).
- **Cách làm:** workflow 9 agent: nghiên cứu bốn góc (công cụ tra cứu luật, công cụ ghi chú có đồ thị, trợ lý AI theo dự án, cách trình bày đồ thị), tổng hợp bản định hướng (666 dòng), dựng bản thử (một tệp HTML bấm được, 1.858 dòng; dữ liệu thật từ 21 văn bản, quan hệ rút từ dòng "Căn cứ" và "sửa đổi"; rủi ro và dự án là ví dụ), soát theo taste-skill và theo nhu cầu người dùng, sửa.
- **Kết quả:** các hướng chính của bản định hướng: dự án là nhóm tham chiếu (một văn bản thuộc nhiều dự án), không phải thư mục; đồ thị cục bộ chứ không toàn kho (nhiều lăng kính cùng chỉ ra đồ thị toàn cục là "tấm áp phích"); bảng Liên quan trước, sơ đồ sau; hiệu lực luôn kèm hình, chữ và lý do. Còn mở theo soát: trên kho thật đồ thị chủ yếu là văn bản chưa có trong kho; cần tệp rủi ro thật để thiết kế phần nạp; không có số liệu người dùng văn phòng có dùng sơ đồ hay không; chưa có tiền lệ đã kiểm cho chat và bộ nhớ riêng theo dự án khi văn bản dùng chung nhiều–nhiều; các mốc số nút (25, 60, 200) là điểm khởi đầu ước tính.
- **Quyết định:** hoãn: chưa duyệt, không thay mẫu P1 đã duyệt. Nhãn giai đoạn (P1, P2, P3, P4, MỚI) trên bản bấm thử để chủ dự án thấy phần nào đã có.
- **Vì sao hoãn:** chờ chủ dự án duyệt hướng; thiếu dữ liệu thật để kiểm (đồ thị chủ yếu là văn bản chưa có trong kho, chưa có tệp rủi ro thật, chưa có số liệu dùng sơ đồ).
- **Bài học:** nghiên cứu nhiều góc hội tụ vào vài quyết định ít ngờ (đồ thị cục bộ, danh sách trước sơ đồ) và chỉ ra rõ cái chưa kiểm được; ý tưởng "mới" của chủ dự án (dự án, sổ rủi ro) phải ghi là MỚI để không lẫn với lộ trình đã duyệt.
- **Nguồn:** `docs/nghien-cuu/khai-niem-du-an-do-thi-dinh-huong.md` mục 0, 2, 14, 15; `mau/khai-niem-du-an-do-thi.html`; commit `5226a73`.

## Nhóm SO: các đợt soát độc lập

Giả thuyết chung của cả nhóm: người viết không tự thấy hết lỗi của mình. Cách làm chung (`docs/nghien-cuu/ghi-nho.md` mục 3.5, `.claude/skills/review-findings-fix-loop`): mỗi đợt, nhiều tác tử chỉ đọc mã soát theo các góc nhìn khác nhau (lỗi; test, an toàn, tốc độ; mã thừa); mỗi phát hiện được một tác tử khác cố bác bỏ; chỉ sửa phát hiện còn đứng; mỗi lỗi có một test (hoặc kịch bản Playwright) hỏng trên mã cũ rồi mới sửa. Quyết định của cả nhóm là "đã sửa" trừ khi ghi khác. Bảng tổng hợp loại lỗi ở cuối nhóm.

### SO-01 · Soát lõi trả lời và bộ đo, trước vòng 1 (30/10/2026)

- **Phạm vi và kết quả:** 9 lỗi, mỗi lỗi được kiểm chứng riêng. (a) Bộ kiểm số liệu cho qua số bịa nhờ nhãn khác: "Điều 5", "khoản 2", "điểm a" nay là nhãn riêng; mã `[n]`, tên file và chữ số trong "QH15" không còn là số nguồn (trước đó "trong 15 ngày", "8 ngày", "1 ngày" bịa vẫn qua). (b) Đọc số: "500.000 đến 1 triệu" thành 5e11; "1.5 triệu", "0.5%" và ngày "01.08.2030" đọc sai. (c) Dựng ngữ cảnh: khi dòng khớp nhất không vừa ngân sách, hai dòng bên cạnh chiếm chỗ của dòng khớp thứ hai; khoá gộp Điều trùng thiếu tên Điều ("viên chức" khác "công chức"). (d) Bộ đo: "cùng nội dung" nay tính theo Điều dài hơn với ngưỡng 0,7 (không coi Điều 5, 6, 7 của NĐ 100/2019 là một); `--mode advance` trước đó lặng lẽ tìm như Normal mà báo cáo vẫn ghi advance (nay dừng nếu chưa có vector); câu bẫy tính cả việc nhắc lại số tiền của chính câu hỏi là "nêu đúng mức".
- **Bài học:** lỗi nguy hiểm nhất là lỗi im lặng (chế độ bị đổi mà báo cáo không đổi nhãn; số bịa được "bảo lãnh" bởi một số khác).
- **Nguồn:** commit `120eea8`.

### SO-02 · Soát sau bảy việc sửa, trước vòng 2 (30/10/2026)

- **Phạm vi và kết quả:** 4 góc nhìn (cứu JSON, bộ kiểm số, dựng ngữ cảnh, grammar và bộ đo), mỗi phát hiện được kiểm chứng ngược: 6 trên 15 phát hiện là thật. Hai lỗi nặng: "mười năm" đọc thành 15 (và "hai năm" thành {2, 5}); câu khớp nhất quá dài bị bỏ nên đoạn gần như rỗng. Bốn lỗi còn lại: "điểm a hoặc b" thêm nhầm điểm c; chuỗi chạm trần bị cắt giữa số hiệu ("Nghị định 155/20"); tách ở dấu hai chấm làm "b) Đối với tổ chức:" rời mức phạt của nó; `--skip` dựa vào tiền tố của `random.sample` nên có thể trùng phần chấm khi thuật toán đổi theo cỡ mẫu (nay `pick_sample` lấy phần chỉnh từ các câu ngoài đúng tập chấm).
- **Hồi quy do chính bản sửa:** bản sửa đầu bỏ hẳn tách ở dấu hai chấm làm câu còn bằng chứng tụt 80% xuống 71% (train văn bản thật); bản cuối giữ tách câu dẫn đầu dòng, chỉ gộp nhãn giữa dòng, lấy lại 80%.
- **Bài học:** một bản sửa cũng cần đo lại bằng chỉ số của vùng nó chạm vào; rò rỉ tập chỉnh sang tập chấm có thể đến từ chi tiết thư viện (thuật toán lấy mẫu đổi theo cỡ).
- **Nguồn:** `bench/llm/KET-QUA.md` mục "Vòng 2" ("Soát độc lập"); commit `131ca78`.

### SO-03 · Soát bằng ponytail sau vòng 2 (31/10/2026)

- **Phạm vi và kết quả:** 23 phát hiện, 9 bị bác, 14 còn đứng (ghi nhớ: "14/23 phát hiện là thật"; tiêu đề commit: 14 phát hiện, 9 bị bác). Lỗi nặng: số hiệu "QH15" để lọt số 5 vào tập số nguồn vì lookbehind chỉ cấm chữ cái (nay cấm cả chữ số); câu khớp nhất kèm câu dẫn vượt ngân sách thì bị dòng độn chiếm chỗ (Luật 23/2026 Điều 1, ngân sách 480). Lỗi vừa: cửa sổ cắt giữa số ("2.000…"), trích nguyên văn cắt giữa số ở 300 ký tự, năm và tháng của ngày đầy đủ trong nguồn bị coi là số lạ, mã đoạn "các đoạn 1 và 2" và "[1–2]" để lại số. Thêm test cho điểm cắt của JSON, mọi trường hiển thị đều được kiểm, chat gửi seed và temperature, `pick_sample`. Kết quả: 258 test qua, 7 bỏ qua; mỗi lỗi nặng có test hỏng trên mã cũ.
- **Bài học:** thử ưu tiên "câu khớp nhất trước mọi dòng khác" bị bác bằng số (câu còn bằng chứng tụt 80,3% xuống 77,3% trên train vì câu khớp nhất đôi khi là khối rác OCR): một hướng sửa hợp lý trên giấy cũng phải qua đo.
- **Nguồn:** `docs/nghien-cuu/ghi-nho.md` mục 3.5; commit `bc9f9af`.

### SO-04 · Soát mẫu giao diện thế hệ 2 (31/10/2026)

- **Phạm vi và kết quả:** 47 phát hiện còn đứng sau bước bác bỏ. Loại lỗi (theo các sửa trong commit): mẫu hứa phần của P2 và P3 mà P1 không làm (dòng trích yếu, hộp thoại lý do hiệu lực, gợi ý văn bản gần nhất ở trạng thái rỗng, nhãn độ chắc chắn ngoài chế độ Advance); trạng thái P1 chưa vẽ (kho trống, bảng nạp, tiến độ nâng cấp dữ liệu, ref hỏng); từ tô không theo luật `answer._words`; bàn phím và focus (hộp thoại khoá nền và trả focus, ngăn kéo đóng ra khỏi thứ tự Tab, tab bằng mũi tên); logic (id cuộc mới trùng, trạng thái mở rộng dính, câu trả lời đến muộn kéo trang đang đọc).
- **Bài học:** soát mẫu đối chiếu với đặc tả P1 chứ không chỉ nhìn ảnh; mẫu hứa nhiều hơn mã làm là lỗi sản phẩm.
- **Nguồn:** commit `9e5cf35`; GD-02.

### SO-05 · Soát kế hoạch P1 đối chiếu với mã (31/10/2026)

- **Phạm vi và kết quả:** 5 người tìm theo phần và 5 người cố bác bỏ; 56 phát hiện còn đứng, không phát hiện nào bị bỏ; mỗi tham chiếu được kiểm lại trong mã. Loại lỗi: tham chiếu `file:line` sai hoặc đã dịch; phụ thuộc bị bỏ sót (bốn chỉ mục khoá ngoại, PS-05; `rebuild_document` gọi `parse_pages` không có `force_doan` nên đổi 14 văn bản `fallback_doan = 1` mà nâng cấp dữ liệu bỏ qua); giả định sai về mã (`DIEU_CAP = 100`, không phải 25; `semantic.root_ids` bỏ sót ghi chú có cha và `root_lines(-id)` ném `TypeError`; `bench/zalo/ket_qua_test.json` đang được git theo dõi nên chạy `eval.py` không có `--tag` sẽ ghi đè). Một lượt phản biện sau đó (critique): 7 tham chiếu sai đều đúng và đã sửa, trừ hai chỗ lệch. Lượt soát kế hoạch tiếp theo (một agent soát theo phản hồi gốc) thêm N3, dời H5 và TIFF, BMP, rút từ 22 xuống 21,5 ngày.
- **Bài học:** kế hoạch có số dòng thì phải đối chiếu lại bằng `grep` trước khi dùng; sửa lộ trình "tại chỗ, không đổi số dòng" (skill `plan-doc-line-reference-edits`).
- **Nguồn:** `docs/ke-hoach/ke-hoach-p1.md` mục "Đã kiểm / chưa kiểm"; commit `5e4df66`, `241ff6b`.

### SO-06 · Soát R2a đến K2 (31/10/2026)

- **Phạm vi và kết quả:** 23 lỗi (theo tiêu đề commit), mỗi lỗi có test hoặc kịch bản Playwright hỏng trên mã cũ. Python: ô "Chọn để xuất" và nhãn trang theo đơn vị ở địa chỉ mục; tra "Điều n" và "số hiệu + Điều n" chấm điểm dòng bằng số trong câu hỏi; "Mở toàn văn" không chịu bộ lọc; lọc cơ quan khớp đúng giá trị. Ổn định và an toàn: pdfium không an toàn đa luồng (6 luồng song song hỏng 3 trên 3 lần thử; sau khi thêm khoá `RLock` quanh mở, vẽ, đóng thì xanh 5 trên 5); tệp gốc mất; URL ảnh trang thiếu phiên bản; id vượt số nguyên SQLite trả 500 thay vì 404. Giao diện: tab Bản gốc không cuộn được bằng bàn phím, Esc trong ô hỏi giật focus, mỗi mục thiếu tên truy cập, nút biểu tượng sai cỡ, phản hồi cũ ghi đè trình đọc mới mở.
- **Bài học:** lỗi đồng thời (thư viện render PDF dùng chung) chỉ lộ khi thử song song; lỗi truy cập (focus, tên nút) gần như luôn có khi lần đầu viết giao diện.
- **Nguồn:** commit `db4eb27`.

### SO-07 · Soát nhóm lịch sử trò chuyện (31/10/2026)

- **Phạm vi và kết quả:** D1 đến D4 (dữ liệu, tham chiếu đã lưu) và UX-1 đến UX-8 (giao diện), 12 phát hiện. D1: băm của tham chiếu chỉ băm chữ đơn vị nên một Điều chỉ có tiêu đề y hệt ở văn bản khác được nhận khi id văn bản bị dùng lại hoặc tệp bị ghi đè (nay băm cả số hiệu của văn bản). D2, D3: mở lại "toàn văn" khẳng định sai "không có Điều n" hoặc hiện thẻ cho văn bản nạp lại với id mới. D4: thanh bên cần trần số cuộc hiển thị (nay tối đa 200 kèm dòng "Còn N cuộc cũ hơn"; ô tìm chỉ gọi `/history` sau khi ngừng gõ 250 ms, trước đó gõ 7 ký tự gọi 7 lần). UX: phím hộp thoại, dòng đang chọn ra ngoài tầm nhìn, cuộc dài mở ở đầu thay vì câu cuối, ô tìm và nút sai cỡ, `Alt+N` bỏ ngang hộp thoại. Kiểm: 9 test mới hỏng trên mã cũ; Playwright 12 trên 12 kịch bản hỏng với bản cũ, 12 trên 12 và 5 trên 5 phụ qua với bản mới.
- **Bài học:** tham chiếu lưu lâu dài cần đủ thông tin để phát hiện "id bị tái dùng"; chỉ băm chữ thì hai thứ khác nhau có chữ giống nhau lẫn vào nhau.
- **Nguồn:** commit `eac8ebb`; `docs/ke-hoach/ke-hoach-p1.md` mục H3, H4.

### SO-08 · Soát toàn repo cho v0.9.0 (ponytail-audit) (31/10/2026)

- **Phạm vi và kết quả:** năm lỗi "Phải sửa" ở `50b3622`, rồi đợt dọn ở `9780468`.
  - **C1** bản quét có dòng "Số:" hỏng bị gán số hiệu của văn bản được dẫn trong "Căn cứ" (cùng gốc với lỗi 7 của PS-03: lấy số đầu tiên khớp); nay trả `None` để người duyệt điền.
  - **C2** Word xuất thẻ máy dựng lại ("Hạng 2 · Điều 49", "có thể bị xử phạt theo", thiếu khoản 2–4 của Điều được tick) thay vì nguyên văn đơn vị đã tick.
  - **C3** bộ lọc loại, cơ quan, hiệu lực áp sau khi cắt top-100 nên ẩn kết quả có thật ("thời hạn" kèm Thông tư: 4 kết quả thay vì 63 trên kho 21 văn bản; nay lọc trong truy vấn).
  - **SEC-1** Word COM mở `.doc` và `.rtf` với `AutomationSecurity` mặc định (chạy macro; nay `ForceDisable`; chưa chạy với Word thật vì máy Linux).
  - **F2** `/review` dựng 50 MB HTML và `/review/docs` 39 MB trên kho Zalo (nay phân trang: 0,08 MB và 0,14 MB trên 5.927 liên kết chờ).
  - **Đợt dọn:** cookie CSRF không phân biệt cổng nên hai bản app (8000, 8001) ghi đè token của nhau (nay `soiluat_csrf_<cổng>`; chạy thật hai tiến trình); POST có `Origin` khác bị chặn trước khi đọc thân; nạp file giữ khoá ghi khi truy vấn FTS gợi ý liên kết; nhúng vector lỗi làm chết luồng nền và chip "Nhúng" quay mãi; nạp lại cùng đường dẫn xoá gợi ý hiệu lực đã duyệt; tệp tạm sao lưu trùng tên giữa hai lần gọi; tải `.docx` nén dạng bom (đo trên mã cũ: 20.000 đoạn rỗng, file 36 KB, mất 10,4 s, không bị từ chối; nay có trần 64 MiB và 300.000 đoạn); mã chết (route `/review/pages`, `templates/jobs.html`) bị xoá.
  - Số test sau đợt: [`ghi-nho.md`](ghi-nho.md) mục 1.1.
- **Hoãn (cần chủ quyết định):** C8 (số hiệu sửa tay bền qua nạp lại: cần đánh dấu trường đã sửa tay, đã xếp ở P2); phần còn lại của F10 (bản sao `ImportError` ở các tệp khác).
- **Bài học:** soát theo từng tính năng ở các đợt trước bỏ sót lỗi cắt ngang nhiều tính năng (CSRF theo cổng, bộ lọc sau cắt, khoá ghi dùng chung); soát toàn repo cuối cùng bắt được chúng. Lỗi nghiệp vụ nặng nhất (C1, C2, C3) đều là chức năng "chạy được, ra kết quả trông hợp lý, nhưng sai".
- **Nguồn:** commit `50b3622`, `9780468`.

### Bảng tổng hợp: loại lỗi các đợt soát tìm ra

| Lớp lỗi | Ví dụ | Đợt |
|---|---|---|
| Bộ kiểm số liệu sai cả hai phía (cho qua số bịa, bỏ nhầm ý đúng) | số hiệu "QH15" bảo lãnh số 5; "mười năm" thành 15 | SO-01, SO-02, SO-03 |
| Cắt và tách chuỗi | cắt giữa số hiệu; tách ở dấu hai chấm; cắt ở 300 ký tự giữa số | SO-02, SO-03 |
| Bộ đo lẫn tập chỉnh với tập chấm, hoặc im lặng đổi chế độ | `--skip`; `--mode advance` tìm như Normal | SO-01, SO-02 |
| Chức năng chạy nhưng lệch đặc tả | Word xuất câu máy dựng; bộ lọc áp sau cắt top-100; tra "Điều n" chấm điểm bằng số trong câu hỏi | SO-06, SO-08 |
| Tham chiếu cũ nhận nhầm | băm chỉ chữ đơn vị, id văn bản bị tái dùng | SO-07 |
| Đồng thời và tài nguyên dùng chung | pdfium 6 luồng; luồng nền chết im; giữ khoá ghi khi truy vấn FTS | SO-06, SO-08 (và PS-09) |
| An toàn dữ liệu và bảo mật | macro Word; docx nén dạng bom; CSRF cookie theo cổng; `Origin` | SO-08 |
| Quy mô trang | `/review` 50 MB HTML | SO-08 |
| Bàn phím, focus, tên truy cập | Esc, Tab, focus sau "Xem thêm", tab bằng mũi tên | SO-04, SO-06, SO-07 |
| Mẫu hoặc kế hoạch lệch mã | mẫu vẽ mỗi điểm một hàng; số dòng sai; mẫu hứa phần P2, P3 | SO-04, SO-05 |

## Bài học chung

Rút ra từ nhiều thí nghiệm; mỗi bài học ghi ID để tra ví dụ. Bài học có skill tương ứng trong `.claude/skills/` thì ghi tên skill.

**Cách đo**

1. **Chọn tiêu chí và chỉ số an toàn trước khi xem số.** Chỉnh trên train, chấm test một lần. Mức tăng trên tập chỉnh bị thổi phồng (TK-02: +4,3 điểm trên train so với +1,7 trên test). Đổi luật chọn sau khi xem số thì ghi lý do và lần sau chọn đúng chỉ số ngay từ đầu (LM-04). Skill `benchmark-split-hygiene`.
2. **Một bộ đo không đủ.** Hai bộ lớn (Zalo, gold) cùng nói "Advance hơn", bộ nhỏ thứ ba (văn bản thật) nói ngược (TK-09). Benchmark công khai có thể nằm trong dữ liệu huấn luyện (TK-06). Vì vậy quy tắc 7 đòi cả ba.
3. **Đo qua đường thật, báo cả lên và xuống.** Số thử bằng script riêng lạc quan hơn số đầu-cuối qua app (TK-03: 62,3% so với 60,5% Hit@1); mức tăng ròng che số câu tụt (128 câu lên, 110 câu xuống); dữ liệu sinh tự động cho số đẹp (PS-01). Độ trễ câu đầu theo cache ổ đĩa, chỉ so từ câu thứ hai (TK-03).
4. **Chênh nhỏ thì dùng phép kiểm đúng.** Phép kiểm dấu cho chênh 1–2 câu (PS-06), McNemar ghép cặp cho hai mô hình trên cùng câu (CN-03); với n = 84 thì một câu bằng 1,2 điểm (TK-09). Khi sửa đúng mà số tụt trong nhiễu, xin ngoại lệ có tên, có điều kiện, có người duyệt (PS-06).
5. **Tách lỗi mã khỏi lỗi mô hình bằng chỉ số trung gian**, và chọn biến thể offline trước khi tốn giờ chạy mô hình (LM-01, LM-02). Đổi mô hình cùng cỡ không sửa được lỗi phạm vi (CN-03, CN-04).
6. **Ước tính khác đo.** Gắn nhãn "ước tính" và "chưa đo" (CN-02, CN-07); máy ảo dùng chung không gác được cổng thời gian; ước tính 100–150 ms sai gần gấp đôi (HT-04); tranh CPU làm sinh chữ chậm khoảng 10 lần (LM-08). Skill `background-job-orchestration`.

**Cách làm và kiểm lỗi**

7. **Số đúng chưa đủ, phải đúng phạm vi áp dụng.** Lỗi này lặp lại ở ba nơi: LLM khái quát quy định hẹp (LM-01, LM-07), quy tắc trích mức phạt đúng số nhưng sai đối tượng (PS-07), thẻ chế tài lấy từ Điều khác. Bộ kiểm số không bắt được; cần tín hiệu khác (điểm tìm kiếm thấp) hoặc người đọc.
8. **Hàm dự phòng im lặng sinh lỗi âm thầm.** "Lấy số đầu tiên khớp" gán số hiệu của văn bản được dẫn (PS-03 lỗi 7, tái xuất ở SO-08 C1); `_token_df` lỗi bị nhánh dự phòng nuốt (TK-01); `--mode advance` lặng lẽ tìm như Normal (SO-01). Thà trả `None` để người điền, hoặc dừng có thông báo.
9. **Chỉ số tự đánh giá che lỗi.** `struct_score` 0,99 dù mất Điều 1 (PS-03); "JSON đọc được 100%" che việc mất ý có nguồn (LM-03). Đối chiếu bằng đáp án bên ngoài, và thêm chỉ số đúng mục tiêu sửa (PS-06).
10. **Đo nút cổ chai trước khi đổi công nghệ.** OCR 98,5% cho thấy lỗi nằm ở bước sau (PS-04); phần CSDL chỉ khoảng 1 s trong khoảng 9 s (CN-05); ràng buộc vector là RAM chứ không phải tốc độ (CN-06); quét toàn bảng ẩn sau `ON DELETE CASCADE` (PS-05); một phép nhân thô loại cả họ giải pháp (CN-07).
11. **Thay đổi chỉ-thêm an toàn hơn thay đổi xáo trộn thứ hạng** (TK-05). Gộp đơn vị phải mang theo thuộc tính định vị như trang, và so từng câu có và không thay đổi (PS-08).
12. **Máy trạng thái cần điểm đặt lại.** Một ký tự rác làm mất cả văn bản khi cờ "đang trong trích dẫn" không bao giờ tắt (PS-03).
13. **Bộ kiểm số liệu có hai loại lỗi**, bỏ nhầm ý đúng và cho qua số bịa, cần test cho cả hai (LM-06, SO-01, SO-02, SO-03). Skill `vietnamese-legal-number-check`.
14. **Mất dữ liệu nặng hơn xếp hạng sai.** Hỏng cả file, ghi đè cùng tên (PS-01), xoá gợi ý đã duyệt (PS-10). Nâng cấp dữ liệu người dùng: sao lưu trước, ghi tệp tạm rồi đổi tên, trạng thái "đã thử" trong tiến trình, luồng nền không chết im, chỉ dựng lại phần đổi (PS-09, SO-08). Skill `sqlite-table-rebuild`.

**Giao diện, soát, nghiên cứu**

15. **Mẫu giao diện phải khớp mã.** Mẫu hứa một bố cục mà bộ gộp của app không tạo ra thì người duyệt duyệt một thứ không tồn tại (GD-02, SO-04). Kiểm bằng ảnh Playwright ở nhiều cỡ, sáng và tối, từng trạng thái; không lách bộ chặn bằng script tải từ ngoài; thêm `[hidden] { display: none !important; }`. Khi một mẫu bị bác, ghi lại lý do ngay (GD-01). Skill `html-mockup-visual-check`.
16. **Soát độc lập: tìm, bác bỏ, test hỏng trên mã cũ, rồi sửa.** Mỗi đợt tìm một lớp lỗi khác (bảng cuối nhóm SO). Soát từng tính năng bỏ sót lỗi cắt ngang, soát toàn repo cuối mới bắt (SO-08); bản sửa có thể gây hồi quy nên đo lại (SO-02); số trong báo cáo phải có người khác tính lại từ JSON thô (LM-07). Skill `review-findings-fix-loop`.
17. **Nghiên cứu công nghệ:** ràng buộc cứng (nền Windows không admin, giấy phép, offline) loại trước khi so tính năng (CN-05); đọc tại nguồn kèm ngày; phân biệt số của hãng với số độc lập; số tiếng Anh không chuyển sang tiếng Việt (CN-04); chọn theo tác vụ gần việc của app nhất, không theo điểm tổng (CN-01).
18. **Ghi cả số của phương án bị loại.** Loại mà không ghi số thì lượt sau không biết loại vì chênh 0,5 điểm hay vì kém xa (TK-08).
19. **Phiên làm việc có thể bị thu hồi.** Commit sớm, script chạy dài tự bỏ qua phần đã xong (`docs/quy-trinh.md` mục 11, bẫy "Container khởi động lại").

## Câu hỏi còn mở

Mỗi dòng nêu ai giữ câu hỏi và nơi ghi chi tiết. Tất cả còn mở theo các tài liệu nguồn ở commit `a13af05`.

| # | Câu hỏi | Giữ ở | Việc kế tiếp |
|---|---|---|---|
| 1 | Cách tính cổng P0 cho câu trả lời AI: câu JSON bị cắt mà cứu được có tính không; từ chối có tính câu nêu phạm vi hẹp hơn không (LM-07) | Chủ dự án; `docs/ke-hoach/lo-trinh-1.0.md` mục 9, điều 10 | Trả lời, rồi đọc lại cổng ở LM-07 |
| 2 | Chế độ tìm mặc định trên máy 16 GB: Normal hay Advance (TK-09) | Chủ dự án (mục 9, điều 8); nhánh độ chính xác điều 0 | Thử giảm `W`, chỉ cho vector chen sau top-k của BM25, hoặc chỉ dùng reranker; đo theo quy tắc 7 |
| 3 | Tốc độ, RAM, p95 45 giây của Qwen trên máy 16 GB Windows; USearch bản Windows; gói PyInstaller có `static/` và phông; Edge, Chrome Windows (CN-02, CN-06, HT-03) | Người có máy 16 GB; `bench/llm/README.md` | `llama-bench`, đo p50 và p95 trên từ 100 câu, đo RAM `llama-server`; Z0 và Z1 của kế hoạch P1 |
| 4 | Từ 100 câu hỏi thật của văn phòng kèm Điều đúng, cần trước cổng P3 | Người dùng; `bench/gold/README.md` phần `van-phong` | Gom vào `queries.json` |
| 5 | Chạy lại `bench/llm` sau sửa parser (LM-08) và các việc trước P3: câu bẫy chạm trần (LM-03), tách câu bẫy train và test (LM-07), lỗi phạm vi 28–37% (CN-03), cảnh báo thừa 10–40% câu có Điều đúng | Người làm tiếp; `docs/ke-hoach/lo-trinh-1.0.md` mục 6, P3 | Hướng thử: dùng điểm tìm kiếm thấp làm tín hiệu cảnh báo; bước kiểm phạm vi bằng mô hình rất nhỏ (LFM3-1.7B có giấy phép giới hạn doanh thu, CN-04) khi còn ngân sách 45 giây |
| 6 | Điều dài bị nhúng chỉ 128 token đầu nên tụt hạng (TK-09) | Nhánh độ chính xác, điều 2 | Thử nhúng theo khoản rồi lấy điểm cao nhất cho Điều, hoặc `MAXLEN` 256 hoặc 512 |
| 7 | Thử nghiệm C (mô hình ghi chép để tìm tốt hơn) và D (Qwen đọc ảnh trang đầu để gợi ý số hiệu, ngày) | Chủ dự án duyệt 31/10/2026, chưa chạy; `docs/ke-hoach/lo-trinh-1.0.md` mục 6, 9 | C qua quy tắc 7; D đo trước trên 12 trường đang sai của 21 văn bản thật |
| 8 | Số hiệu viết tay hoặc nằm trong ô chữ ký số (5/21 số hiệu và 7/21 ngày ban hành ở lần đo 23/10, chưa đo lại sau N3; PS-03) | P2 | Hàng chờ người điền kèm ảnh trang |
| 9 | Bản mẫu khái niệm (dự án, sổ rủi ro, đồ thị) chưa duyệt: khách có bao nhiêu dự án, tệp rủi ro thật trông thế nào, đồ thị trên kho thật (GD-03) | Chủ dự án (`docs/ke-hoach/lo-trinh-1.0.md` mục 9, điều 14); `docs/nghien-cuu/khai-niem-du-an-do-thi-dinh-huong.md` mục 14, 15 | Duyệt hoặc đổi hướng; lấy tệp rủi ro thật |
| 10 | Chỉnh `SURE_GAP` và bảng `citation_opens` (HT-05) | Nhánh độ chính xác, điều 4 | Làm khi Advance có thể thành mặc định và có người dùng thật |
| 11 | Số hiệu sửa tay bền qua nạp lại (C8) và phần còn lại của F10 (SO-08) | P2 (đánh dấu trường đã sửa tay) | Quyết cùng cách đánh dấu của P2 |
| 12 | Giới hạn chung của số đo: gold `vle` chưa có giấy phép; AITeamVN không công bố dữ liệu huấn luyện nên Zalo và gold có thể lẫn (TK-06); mẫu LLM chỉ 15–30 câu mỗi bộ (khoảng tin cậy ±18–25 điểm) | Mọi lượt đo | Dùng bộ văn phòng (mục 4) và cỡ mẫu từ 100 câu |
| 13 | Các quyết định còn mở khác của chủ dự án: người thử, máy 8 GB còn hỗ trợ không, gói AI tách hay gộp, chứng thư ký số, ai duyệt hiệu lực | Chủ dự án; `docs/ke-hoach/lo-trinh-1.0.md` mục 9 | Xem mục 9, không chép lại ở đây |
