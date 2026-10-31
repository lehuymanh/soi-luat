# Kết quả: rò rỉ dữ liệu Zalo và mốc bộ gold (27/10/2026)

## 1. Bộ Zalo 788 câu có trùng dữ liệu huấn luyện không?

| Kiểm tra | Kết quả |
|---|---|
| 788 câu test GreenNode có trong tập train gốc Zalo 2021 (HF `NghiemAbe/Legal_Train_Zalo`, 3.196 câu) | **788/788**, khớp cả ID lẫn nguyên văn |
| 2.432 câu train GreenNode có trong tập train gốc | 2.432/2.432 |
| Câu test trùng nguyên văn câu train GreenNode | 24 (cùng câu hỏi, Điều đáp án khác) |
| Câu test gần trùng (≥ 50% bộ 8-từ) câu train | 61, không câu nào cùng Điều đáp án |
| Điều đáp án của test cũng là đáp án của câu train | 0/788 |

Đọc kết quả:

- GreenNode chỉ chia lại tập train gốc của Zalo thành 2.432 + 788 câu. Mô hình nào huấn luyện trên tập train gốc
  đều đã thấy phần lớn 788 câu.
- `bkai-foundation-models/vietnamese-bi-encoder`: model card ghi huấn luyện trên **80% tập train Zalo**. Kỳ vọng
  khoảng 630/788 câu test đã nằm trong dữ liệu huấn luyện. Không dùng Zalo để đánh giá mô hình này.
- `AITeamVN/Vietnamese_Embedding` và `Vietnamese_Reranker`: model card ghi "not trained on this dataset" và
  đánh giá trên toàn bộ tập train Zalo, nhưng không công bố dữ liệu huấn luyện (300 nghìn và 1,1 triệu bộ ba).
  Không kiểm chứng được. Phải xét trên bộ gold.
- `hiieu/halong_embedding`: ghi không huấn luyện trên tập này; dữ liệu nội bộ, không kiểm chứng được.
- Riêng cho Soi Luật: test và train GreenNode **không chung Điều đáp án nào**, nên các lần tinh chỉnh trước
  (`DENSE_MIN`, trọng số) dùng tập train không làm rò nhãn sang test.

## 2. Mốc của hệ hiện tại trên bộ gold

Hệ hiện tại = đường tìm của app (`cascade_search` + dựng thẻ), kho Zalo 61.425 Điều, gom theo Điều.

| Bộ | Số câu | Chế độ | Hit@1 | Hit@3 | Hit@5 | Hit@10 | MRR@10 | p50 |
|---|---|---|---|---|---|---|---|---|
| Zalo test | 788 | Normal | 58,9 | 82,0 | 86,2 | 90,2 | — | — |
| Zalo test | 788 | Advance | 60,2 | 83,5 | 89,1 | 92,5 | 0,723 | 1,8 s |
| **Gold `vle` (tư vấn thật)** | 500 | Normal | **51,0** | 69,2 | 76,6 | **83,4** | 0,619 | 1,1 s |
| **Gold `vle` (tư vấn thật)** | 500 | Advance | **55,4** | 76,0 | 83,0 | **87,6** | 0,671 | 1,5 s |
| Gold `van-ban-that` (21 văn bản 2026) | 84 | Normal | 82,1 | 92,9 | 96,4 | 96,4 | — | 0,5 s |

Đọc kết quả:

- Câu hỏi tư vấn thật **khó hơn Zalo**: Hit@1 thấp hơn 5–8 điểm, Hit@10 thấp hơn 5–7 điểm.
- **Advance có ích hơn trên câu hỏi thật** so với trên Zalo: +4,4 Hit@1 và +4,2 Hit@10 (Zalo chỉ +1,3 và +2,3).
  Câu hỏi đời thường ít trùng chữ với văn bản hơn, nên phần tìm theo nghĩa bù được nhiều hơn.
- Từ nay, mọi đề xuất trong `reports/LLM offline cho tra cứu luật.md` (thay embedding, thêm reranker…) phải
  được đo trên **cả Zalo lẫn gold `vle`**, và chỉ giữ khi tăng trên cả hai.

Chạy lại: xem [README.md](README.md). Số theo từng câu: `bench/zalo/ket_qua_gold_vle_{normal,advance}.json`
(chỉ trên máy, không commit vì chứa câu hỏi ViLegalExperts).


## P1 K3: đo theo mục hiển thị (31/10/2026)

Quy ước (kế hoạch P1, mục 2b, chủ dự án duyệt 31/10/2026): "theo mục" là mục hiển thị sau `cards.compact` (một mục mỗi (văn bản, Điều), Điều cùng nội dung ở văn bản khác gộp vào "Cũng có ở"). Zalo và gold tính trúng khi khoá đáp án nằm ở bản đại diện hoặc một bản trùng (kho Zalo gần như không có ngày ban hành để chọn đại diện); văn bản thật tính theo bản đại diện. Mọi bộ báo cả hai cách.

Gold `vle` 500 câu, cùng bản dựng và lệnh với Zalo (`--tag muc`, tệp kết quả bị `.gitignore` chặn):

| Cách tính | Hit@1 | Hit@5 | Hit@10 | MRR@10 |
|---|---|---|---|---|
| theo thẻ (`hien_tai`, mốc 0.8) | 51,2 | 77,0 | 84,2 | 0,624 |
| theo mục, kèm "Cũng có ở" (`hien_tai_muc`, cổng P1) | 52,6 | 77,4 | 84,4 | 0,632 |
| theo mục, chỉ bản đại diện (`hien_tai_muc_dai_dien`) | 51,2 | 76,0 | 82,8 | 0,617 |

Cổng P1: đạt (@1 +1,4 điểm, @5 +0,4).
