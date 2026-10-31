# Bản thiết kế: Soi Luật lớn từ P1 lên Dự án, Ghi chú, Rủi ro và Sơ đồ

**Ngày:** 31/10/2026 · **Dùng cho:** người dựng bản bấm thử (concept) và chủ dự án duyệt hướng · **Không thay** `mau/giao-dien-1.0.html` (đã duyệt, chỉ được đổi dữ liệu và chữ). Bản mới là tệp riêng, lấy lại token và thành phần của P1.

**Nhãn giai đoạn dùng xuyên suốt:** [P1] đã dựng · [P2] kho văn bản: tag, ghi chú, @ và #, hiệu lực · [P3] câu trả lời AI có kiểm chứng · [P4] quan hệ văn bản và sơ đồ · **[MỚI]** ý của chủ dự án ngày 31/10/2026 mà lộ trình chưa có: dự án, sổ rủi ro, tra rủi ro theo ghi chú, bản đồ dự án.

**Cách gọi:** "chị" là khách thật (chat 25/09/2026). Chữ trên giao diện dùng "bạn" như P1 ("Bạn ghi", "Bạn đặt"), vì app có nhiều người dùng chứ không chỉ một chị.

---

## 0. Tóm tắt

1. **Dự án là nhóm tham chiếu, không phải thư mục.** Văn bản nằm một bản trong kho; một văn bản thuộc nhiều dự án. Tag, quan hệ, hiệu lực thuộc kho. Ghi chú có hai tầm: "Chung" (đi theo văn bản) hoặc "Chỉ dự án X". Cuộc trò chuyện thuộc một dự án hoặc thuộc Toàn kho. [MỚI]
2. **Khung P1 giữ nguyên.** Chỉ thêm ba thứ: bộ chuyển dự án ở đầu thanh bên (thay dòng "phạm vi"), hàng chip phạm vi trong ô hỏi, và ngăn "Ghi chú và rủi ro" trong trình đọc. Không thêm ngăn cố định thứ ba.
3. **Việc chính của chị là gõ từ khoá, ra rủi ro kèm điều luật nguyên văn.** Kết quả là một "sổ cái" hai cột: bên trái lời bạn ghi, bên phải điều luật nguyên văn. Cùng một thành phần (hàng rủi ro) dùng ở kết quả tra, câu trả lời AI và Sổ rủi ro. [MỚI]
4. **Rủi ro không phải loại dữ liệu riêng.** Rủi ro là ghi chú loại "Rủi ro" gắn vào một đoạn. Sổ rủi ro chỉ là bảng nhìn các ghi chú đó theo phạm vi hiện tại. Một rủi ro chỉ vào sổ khi người dùng bấm "Thêm vào sổ rủi ro" hoặc nhập từ tệp của mình; không tự trích. [MỚI, dựng trên P2]
5. **Một bộ dấu hiệu lực dùng mọi nơi:** hình + chữ + lý do + cơ sở ("theo kho của bạn"). Không bao giờ chỉ là màu. [P2, P4]
6. **Quan hệ: bảng trước, sơ đồ sau.** Sơ đồ chỉ vẽ cục bộ: mặc định 1 bước, tối đa 2. Hàng ngang theo thứ bậc (Luật, Nghị định, Thông tư), cột theo ngày ban hành, không mô phỏng vật lý. Văn bản được nhắc mà chưa có trong kho là nút mờ nét đứt "chưa có trong kho". [P4]
7. **Bản đồ dự án có, nhưng là cách xem thứ hai của bảng văn bản trong dự án**, không phải trang chủ. Ghi chú và rủi ro là huy hiệu trên nút, không phải nút. Bố cục lực đẩy có hạt giống cố định chỉ dùng ở đây (mục 6.13). [MỚI]
8. **Mọi thứ trên bản bấm thử có nhãn giai đoạn** bật tắt được ("Hiện nhãn giai đoạn"), để chủ dự án thấy ngay cái nào đã có, cái nào mới.

---

## 1. Việc thật cần làm tốt

### 1.1 Hai nguồn yêu cầu

- **Chị (chat 25/09/2026):** dùng trên máy cá nhân; có nhiều file Word nghị định, thông tư; muốn gom về một chỗ; gõ một từ khoá thì thấy **rủi ro tiềm ẩn** (chị đã có file tóm tắt rủi ro) kèm **trích dẫn nguyên văn**; để khỏi mở từng file.
- **Chủ dự án (31/10/2026):** chia theo dự án; văn bản thuộc nhiều dự án; mỗi dự án có cuộc trò chuyện (ngữ cảnh riêng) và ghi chú ("bộ nhớ") riêng; chưa chọn dự án mà hỏi rủi ro thì tìm trong ghi chú gắn ở từng văn bản (kể cả tệp rủi ro của chị); lúc nào cũng có trích dẫn và căn cứ pháp lý; giao diện trực quan, linh hoạt, có đồ thị kiểu Obsidian khi hữu ích.

### 1.2 Ba việc dùng để thử mọi màn hình

1. Gõ "bảo hiểm xe": thấy rủi ro mình đã ghi, mỗi cái kèm điều luật nguyên văn và còn hiệu lực hay không, **không mở file nào**.
2. Mở một nghị định: biết nó còn hiệu lực không, vì sao, và văn bản nào sửa hay thay nó.
3. Trong một dự án: biết còn thiếu văn bản nào, và rủi ro nào đang chờ xử lý.

### 1.3 Ý tưởng thiết kế (theo cách taste-skill đòi)

- Trên app này, **file tóm tắt rủi ro của chị** thành **sổ cái hai cột: lời bạn ghi bên trái, điều luật nguyên văn bên phải, có hiệu lực kèm lý do**.
- Trên app này, **thứ bậc văn bản Việt Nam (Luật, Nghị định, Thông tư)** thành **các hàng của sơ đồ quan hệ**; hàng nào cũng đọc từ trái sang phải theo ngày ban hành.

Thử với đối thủ gần nhất (LuatVietnam, Thư viện Pháp luật): họ có lược đồ nhưng không có ghi chú riêng của người dùng cạnh điều luật, và phần lược đồ nằm sau thanh toán. Hai câu trên không đúng với họ.

---

## 2. Nghiên cứu nói gì, và tin được đến đâu

| Phát hiện (nhiều lăng kính cùng chỉ ra) | Quyết định trong bản này |
|---|---|
| Đồ thị cục bộ được dùng thật; đồ thị toàn cục là "tấm áp phích" (Obsidian, Capacities, van Ham và Perer) | Không có đồ thị toàn kho. Sơ đồ cục bộ ở trình đọc; bản đồ dự án chỉ là cách xem thứ hai |
| Danh sách theo nhóm có số đếm là công cụ hằng ngày; sơ đồ chỉ để thấy "chúng nối với nhau thế nào" | Tab "Liên quan" mở bằng danh sách; sơ đồ là công tắc thứ hai, cùng dữ liệu |
| Cờ hiệu lực phải có lý do và liên kết tới văn bản gây ra; "không có cờ" không có nghĩa là còn hiệu lực (KeyCite, LuatVietnam) | Huy hiệu + lý do + cơ sở; thêm "Chưa rõ" |
| Dẫn nguồn đúng chỗ chưa chứng minh nguồn ủng hộ kết luận (Stanford) | Nhãn "Đã đối chiếu nguyên văn" chỉ nghĩa là đoạn có thật; dòng giải thích đi kèm |
| Phạm vi phải nhìn thấy và ép trong truy vấn, không chỉ trong lời nhắc (NotebookLM, Kagi) | Hàng chip phạm vi; lọc bằng `doc_id IN (...)` |
| Mô hình nhiều–nhiều (một văn bản trong nhiều dự án) tốt hơn sao chép nguồn (Heptabase; Claude Projects và Perplexity thì sao chép) | Bảng thành viên dự án; "Gỡ khỏi dự án" không xoá văn bản |
| Màu chỉ mang một nghĩa; kiểu đường và chữ mang loại quan hệ (Cambridge Intelligence, Kinopio) | Sơ đồ không màu, chỉ một màu nhấn "bút bi xanh"; không bảng màu phân loại |
| Quá hai tầng mở rộng thì khó dùng (NN/g) | Tab: Văn bản, Bản gốc, Liên quan. Ghi chú và thẻ nằm trong một ngăn |

**Độ tin cậy.** Mạnh: các điểm trên có trang gốc đã mở (tài liệu Obsidian, Capacities, Kumu, Cambridge Intelligence, WCAG, NN/g, trang giúp của Google và Anthropic, trang công khai của LuatVietnam, legislation.gov.uk). Yếu: Thư viện Pháp luật bị chặn 403 nên mô tả "Lược đồ" chỉ qua đoạn trích tìm kiếm; chi tiết Ravel (giới hạn 75, trục toà án) cũng vậy; **không có số liệu người dùng văn phòng có dùng sơ đồ hay không**; **không có tiền lệ đã kiểm cho chat và bộ nhớ riêng theo dự án khi văn bản dùng chung nhiều–nhiều** (Harvey không mô tả). Các mốc số nút (25, 60, 200; 12 nút ở cỡ thường) là điểm khởi đầu ước tính, phải đo lại trên kho thật.

---

## 3. Kiến trúc thông tin

### 3.1 Hai phạm vi

- **Toàn kho:** mọi văn bản, mọi ghi chú, mọi cuộc trò chuyện chưa vào dự án. Luôn có, luôn đứng đầu bộ chuyển.
- **Dự án:** một tập văn bản (tham chiếu) cùng ghi chú và cuộc trò chuyện riêng. Ngữ cảnh hỏi đáp **chỉ gồm văn bản của dự án**, ép trong truy vấn.

### 3.2 Cái gì sống ở đâu

| Thứ | Thuộc về | Hiện ở | Ghi chú |
|---|---|---|---|
| Văn bản (tệp gốc, chữ, trang) | Kho, đúng một bản | Mọi nơi | Dự án chỉ giữ tham chiếu (bảng thành viên) [MỚI] |
| Tag | Kho | Trình đọc, trang Văn bản, `#` trong ô hỏi | [P2] |
| Hiệu lực, lý do, "Bạn đặt" | Kho | Mọi huy hiệu | Theo kho, không theo dự án [P2] |
| Quan hệ (căn cứ, hướng dẫn, sửa đổi, thay thế, dẫn chiếu) | Kho | Tab Liên quan, sơ đồ | Dự án chỉ lọc cách nhìn [P4] |
| **Ghi chú của văn bản**: chữ bạn viết, loại "Ghi chú" hoặc "Rủi ro", gắn cả văn bản hoặc một đoạn | Kho, theo văn bản. Nhãn **Chung** | Mọi dự án có văn bản đó | [P2], loại "Rủi ro" [MỚI] |
| **Tệp ghi chú, rủi ro của bạn** đính kèm một văn bản | Kho, theo văn bản | Ngăn Ghi chú; chữ trong tệp được lập chỉ mục; nhãn "Bạn ghi (từ tệp)" | [MỚI] |
| **Ghi chú trong dự án** (gắn vào văn bản nhưng chỉ ở dự án A) | Dự án. Nhãn **Dự án A** | Chỉ trong dự án A | [MỚI] |
| **Bối cảnh dự án** (500 đến 2.000 ký tự) và **Ghi chú dự án** = "bộ nhớ" | Dự án | Trang dự án; đưa vào lời nhắc AI khi có [P3] | Chữ bạn viết, xem và sửa được, không có "tóm tắt tự sinh" [MỚI] |
| Cuộc trò chuyện | Một dự án hoặc Toàn kho | Lịch sử ở thanh bên | Lưu **ảnh chụp phạm vi** (danh sách văn bản và ngày); "Chuyển vào dự án..." [P1, scope P2, dự án MỚI] |
| Sổ rủi ro | Không phải dữ liệu riêng | Bảng nhìn các ghi chú loại Rủi ro theo phạm vi | [MỚI] |
| Vị trí nút bản đồ dự án, bộ lọc sơ đồ dùng gần nhất | Dự án, lưu trong DB (không phải trình duyệt) | Mở lại đúng như cũ | [MỚI] |

### 3.3 Quy tắc phạm vi khi tìm và hỏi

1. **Toàn kho:** tìm ghi chú của mọi văn bản trước (cả "Chung" lẫn "Dự án B", mỗi dòng ghi nguồn "Từ dự án B"), rồi tới điều luật.
2. **Trong dự án:** ghi chú "Chung" của các văn bản thành viên và ghi chú của chính dự án; ghi chú riêng của dự án khác không lẫn vào.
3. **Hết hiệu lực không bị loại**, chỉ mờ và có cờ (P1 đã có kiểu `.faded`). Lý do: kho tự lập có thể sai hiệu lực, và quy định chuyển tiếp có thể còn dùng.
4. **Không tự mở rộng phạm vi.** Không có kết quả thì nói "Không tìm thấy trong phạm vi này (Dự án A, 14 văn bản)" và đưa nút "Mở rộng ra Toàn kho (3 văn bản có khớp)". Không lấp chỗ trống bằng trí nhớ của mô hình.
5. Mỗi kết quả và mỗi câu trả lời ghi rõ "Dựa trên N văn bản, đã đọc N/N". Không cắt lặng lẽ.

### 3.4 Bộ chuyển dự án và thanh bên

Bộ chuyển thay dòng chữ `.scope` của P1 (mục "Soi Luật" ở đầu thanh bên).

```
Thanh bên 248px
+---------------------------------+
| [logo] Soi Luật                 |
| +-----------------------------+ |
| | Xe cơ giới và bảo hiểm    v | |  bộ chuyển dự án
| | 14 văn bản                  | |  (Alt+P)
| +-----------------------------+ |
| [ Cuộc trò chuyện mới  Alt+N ]  |
| [ Tìm trong lịch sử          ]  |
| Trong dự án này                 |
|   Văn bản                       |
|   Sổ rủi ro                  3  |  số = việc cần xử lý
| Hôm nay                         |
|   Xe máy không mang giấy bảo... |
| 7 ngày qua ...                  |
| ------------------------------- |
|   Nạp văn bản                   |
|   Gợi ý quan hệ chờ xác nhận 2  |  [P4], thay "Liên kết chờ duyệt"
|   Cài đặt                       |
|   Chạy trên máy này, không gửi  |
+---------------------------------+

Bảng mở ra từ bộ chuyển
+----------------------------------------+
| Tìm dự án ____________                 |
| ( ) Toàn kho · 22 văn bản              |  luôn đứng đầu
| ( ) Đã ghim                            |
| (o) Xe cơ giới và bảo hiểm  14 · 3     |  văn bản · việc cần xử lý
| ( ) Xử phạt hành chính       5 · 1     |
| ( ) Đầu tư và thủ tục 2026   5 · 0     |
| + Dự án mới          Quản lý dự án     |
+----------------------------------------+
```

- **Đổi dự án đổi gì:** danh sách lịch sử (chỉ cuộc của dự án đó), chip phạm vi trong ô hỏi, số trên thanh bên, kết quả tìm. **Không đổi:** chữ đang gõ dở; trình đọc đang mở (nếu văn bản không thuộc dự án mới thì hiện dải "Văn bản này không thuộc dự án X. Thêm vào dự án").
- Nhớ dự án dùng lần cuối trong DB. Mở app lần đầu: Toàn kho.
- Số lượng dự án dự kiến vài đến vài chục: bảng có ô tìm và mục "Đã ghim"; không dựng trang quản lý dự án riêng ở bản này (chỉ hộp thoại đổi tên, ghim, xoá).
- Thanh bên giữ đủ chức năng P1; chỉ **thêm hai dòng điều hướng theo phạm vi** (Văn bản, Sổ rủi ro). Số chỉ xuất hiện trên hàng chờ cần hành động (quy tắc taste-skill): "Sổ rủi ro 3", không có số trên "Văn bản".
- Màn hẹp: nút tên dự án nằm ở thanh trên, mở một tờ toàn màn hình.

### 3.5 Gỡ và xoá, nói bằng lời thường

- **Gỡ khỏi dự án:** "Văn bản vẫn còn trong kho cùng ghi chú và thẻ của nó. Chỉ bỏ khỏi dự án X." Nút: "Gỡ khỏi dự án".
- **Xoá văn bản** là việc riêng, chỉ ở trang Văn bản của Toàn kho (đã có hỏi lại ở P2).
- **Xoá dự án:** "Dự án X sẽ mất bối cảnh, ghi chú riêng của dự án. Văn bản không bị xoá." Có ô chọn mặc định bật "Giữ N cuộc trò chuyện (chuyển sang Toàn kho)".

---

## 4. Bộ phận dùng chung (dựng một lần, dùng lại ở mọi màn)

### 4.1 Hiệu lực: hình, chữ, lý do, cơ sở [P2, một phần P4]

Dùng cặp màu nhạt của P1 (`--pos`, `--warn`, `--neg`, `--neu`), nhưng **luôn đi kèm hình và chữ** (không còn chỉ màu).

| Trạng thái | Hình trong huy hiệu | Cặp màu | Khi nào |
|---|---|---|---|
| Còn hiệu lực | tròn đặc | `pos` | Bạn đặt, hoặc bạn xác nhận gợi ý |
| Hết hiệu lực một phần | tròn nửa | `warn` | Có Điều bị bãi bỏ và bạn xác nhận [P4] |
| Hết hiệu lực | tròn rỗng | `neg` | Bạn đặt, hoặc xác nhận gợi ý |
| Chưa có hiệu lực | thoi rỗng | `neu` | Tính ra: ngày hiệu lực sau hôm nay [P2] |
| Có thể đã bị thay thế | dấu chấm than | `warn` | Tính ra: có gợi ý thay thế chưa xác nhận [P2] |
| Chưa rõ | dấu hỏi | `neu` | Mặc định; kho chưa có căn cứ |

- **Dòng lý do** (13px, `--muted`) luôn đi sau huy hiệu ở trình đọc, hàng rủi ro, thẻ chi tiết: `{kết luận ngắn} · {văn bản nào, Điều nào} · {cơ sở}`. Ví dụ: "Bị thay thế bởi NĐ 03/2021/NĐ-CP (chưa có trong kho) · Bạn đặt." Bấm vào tên văn bản gây ra thì mở đúng đoạn.
- **Cơ sở** chỉ có bốn giá trị: "Bạn đặt", "Bạn xác nhận gợi ý", "Máy gợi ý, chưa xác nhận", "Kho chưa có căn cứ".
- **Dải cơ sở** ở đầu danh sách và tab Liên quan: "Theo kho của bạn: dựa trên 14 văn bản, cập nhật 30/10/2026. Có thể thiếu văn bản sửa đổi chưa nạp." Không bao giờ viết "còn hiệu lực" khi chỉ là chưa thấy gì.
- **"Cần xem lại"** không phải trạng thái mà là lời nhắc một bước lan truyền [P4]: "Cần xem lại: căn cứ vào NĐ X đã bị thay thế." Có nút "Đã xem, giữ nguyên" (nhớ theo văn bản và lý do, để khỏi nhắc mãi). Không dùng chữ "hết hiệu lực" vì quy định chuyển tiếp có thể còn.
- Một hàng chỉ có **một** dấu hiệu lực (không vừa nhãn vừa huy hiệu cùng nói một điều).
- Trên sơ đồ, hai trạng thái "máy chưa chắc" (Có thể đã bị thay thế, Chưa rõ) gộp thành một dấu hỏi; chữ đầy đủ ở thẻ chi tiết.

### 4.2 Hàng rủi ro (một thành phần, ba nơi dùng) [MỚI]

Dùng ở: kết quả tra từ khoá, câu trả lời AI, Sổ rủi ro (khi mở rộng một dòng).

```
+-- Bạn ghi -----------------------+-- Luật quy định ---------------------------------+
| (bút) Bạn ghi · từ tệp "tom-tat- | Khoản 2 Điều 21 · NĐ 100/2019/NĐ-CP  [o Còn HL]  |
|  rui-ro-xe.docx" · Chung         | "…nguyên văn lấy từ kho, từ khớp gạch dưới bút   |
|                                  |  bi xanh, ba đến năm dòng…"                      |
| Không mang giấy bảo hiểm: phạt   | Bạn đặt hiệu lực 24/10/2026                      |
| theo loại xe, xe máy khác ô tô.  | [Mở đúng đoạn]  [Sao chép trích dẫn]  +1 căn cứ  |
| [Cần xử lý v]  [Sửa]             |                                                  |
+----------------------------------+--------------------------------------------------+
```

- **Cột trái "Bạn ghi":** nền `--raised`, biểu tượng bút, nguồn ("gõ ngày 12/10" hoặc "từ tệp ..."), nhãn tầm ("Chung" hoặc "Dự án X"), câu của bạn, trạng thái "Cần xử lý / Đã xử lý" (hai giá trị, không điểm số, không phần trăm).
- **Cột phải "Luật quy định":** nền `--surface`, địa chỉ (đậm, là liên kết), huy hiệu hiệu lực, **trích nguyên văn** 3 đến 5 dòng lấy từ SQLite (không bao giờ do mô hình viết), từ khớp gạch dưới bút bi xanh, dòng lý do hiệu lực, hành động. Tối đa 2 đoạn, phần còn lại "+1 căn cứ".
- Giữa hai cột là một đường kẻ mảnh như sổ cái. Dưới 640px (đo theo khung chứa, dùng container query, vì ở 1440 khi mở trình đọc cột chính chỉ còn khoảng 500px) hai cột xếp chồng: bạn ghi trên, luật dưới.
- **Trạng thái đặc biệt:**
  - *Chưa gắn căn cứ* (nhập từ tệp): cột phải là khung rỗng "Chưa gắn căn cứ. Gợi ý: Khoản 2 Điều 21 NĐ 100/2019 [Gắn] [Chọn đoạn khác]". Gợi ý lấy từ tìm kiếm, người bấm mới gắn.
  - *Đoạn đã thay đổi* (nạp lại văn bản không gắn lại được): "Đoạn này đã thay đổi trong văn bản. Đoạn bạn đã lưu: «...» [Xem đoạn hiện tại] [Gắn lại]". Không bao giờ mất ghi chú.
  - *Căn cứ có thay đổi* (có văn bản sửa đổi chạm vào Điều đã dẫn) [P4]: dòng `warn` + "Xem hai bản cạnh nhau".
  - *Cần xem lại*: dòng `warn` dưới cột phải, có "Đã xem, giữ nguyên".
- Khi bấm "Thêm vào sổ rủi ro" ở một đoạn: nhỏ một hộp "Rủi ro là gì? (viết bằng lời của bạn)", chọn tầm [Chung / Chỉ dự án X] (mặc định Chung, xem mục 14), trạng thái mặc định "Cần xử lý". Lưu kèm nguyên văn đoạn và dấu băm để gắn lại được.

### 4.3 "Bạn ghi" khác "Luật quy định", ở mọi nơi

Ghi chú của người dùng không được lẫn với luật. Phân biệt bằng **hình + nền + biểu tượng + chữ** (không bằng màu):

| | Luật quy định | Bạn ghi |
|---|---|---|
| Nền | `--surface` | `--raised` |
| Biểu tượng đầu | không | bút |
| Chip nguồn | vuông bo 4px, chỉ số `[3]` | hình viên thuốc (bo tròn hết), chữ "Ghi chú của bạn" |
| Chữ nhãn | "Luật quy định" / "Nguyên văn" | "Bạn ghi" |
| Trong kết quả | nhóm theo văn bản (P1) | nhóm "Bạn đã ghi (4)" đứng trên |
| Trên sơ đồ | nút | huy hiệu số nhỏ trên nút (không phải nút) |
| Trong tìm kiếm của AI [P3] | thẻ trích nguyên văn | chip "Đã dùng: 2 ghi chú của bạn" |

### 4.4 Chip phạm vi [P2 cho @ và #; chip dự án MỚI]

- Nằm **trong khung ô hỏi**, dòng trên cùng, phía trên chỗ gõ: `[Dự án: Xe cơ giới · 14] [NĐ 100/2019 x] [#bảo-hiểm x]`. Chip dự án luôn có; đổi bằng menu của chip ("Chuyển sang Toàn kho" hoặc dự án khác). Dưới khung vẫn là ba ô lọc của P1.
- Gõ `@` mở danh sách văn bản (số hiệu, trích yếu cắt ngắn, dấu hiệu lực); gõ `#` mở danh sách thẻ. Khớp **không dấu** ("nghi dinh 15" ra "Nghị định 15/2020"). Mũi tên chọn, Enter nhận, Esc đóng, Backspace khi ô trống bỏ chip cuối. Chip là nút thật, nút x có nhãn đọc màn hình ("Bỏ phạm vi NĐ 100/2019").
- Mỗi câu trả lời **lặp lại phạm vi** ở đầu, chỉ đọc: chip và "Dựa trên 14 văn bản, đã đọc 14/14. 2 đã hết hiệu lực (vẫn hiện, có đánh dấu)". Bấm vào số 14 thì mở danh sách 14 văn bản đó.
- Phạm vi lưu theo cuộc trò chuyện; câu sau dùng tiếp tới khi bỏ chip.

### 4.5 Chip trích dẫn và kiểm căn cứ [P1 bấm mở; P3 phần kiểm]

Ba loại chip, khác nhau cả hình lẫn chữ:

| Loại | Hình | Nghĩa |
|---|---|---|
| `[3]` | vuông 22×20, bo 4px, viền `--control` (đang có ở P1) | Một đoạn luật có địa chỉ |
| "cả văn bản" | chữ nhật có biểu tượng tờ giấy và chữ "cả văn bản" | Chỉ trỏ tới cả văn bản, **không** phải một đoạn; không bao giờ trông như `[3]` |
| "Ghi chú của bạn" | hình viên thuốc bo tròn, nền `--raised`, biểu tượng bút | Mở ghi chú trong ngăn của trình đọc |

- **Di chuột hoặc focus** vào `[n]` (sau khoảng 150 ms): hiện hộp nhỏ rộng chừng 360px: địa chỉ đậm ("Khoản 2 Điều 21 · NĐ 100/2019/NĐ-CP"), huy hiệu hiệu lực, trích nguyên văn 3 đến 5 dòng, trạng thái đối chiếu, nút "Mở văn bản". **Bấm** thì trình đọc trượt ra đúng đoạn, cuộc trò chuyện giữ nguyên vị trí cuộn. Esc đóng hộp. Chữ trong hộp có trong DOM cho trình đọc màn hình. Màn cảm ứng: chạm là mở trình đọc, không qua hộp.
- **Ba trạng thái đối chiếu**, nói thật:
  1. "Đã đối chiếu nguyên văn": trích có thật trong văn bản, số liệu, ngày, số hiệu trong câu khớp với trích, Điều thuộc đúng văn bản.
  2. "Chưa đối chiếu được": hàng bị làm mờ, xuống dưới; câu viết của máy không hiện như câu đã kiểm.
  3. "Không tìm thấy căn cứ": là một đoạn chữ, không có chip.
- Một dòng nhỏ ở cuối phần Căn cứ: "Đã đối chiếu nghĩa là đoạn này có thật trong văn bản. Bạn vẫn cần đọc để biết có đủ để kết luận."
- Dưới mỗi câu trả lời có **dải "Kiểm tra hiệu lực căn cứ"**: "4 căn cứ: 3 còn hiệu lực · 1 cần xem lại". Mục bình thường gộp thành số; mục có vấn đề mở ra kèm lý do.
- **Chữ do máy viết** có nhãn nhỏ "Tóm tắt (do máy viết)"; chữ trích có nhãn "Nguyên văn". Hai khối khác nền, để người đọc biết cái nào đã kiểm.

---

## 5. Các màn hình

Mỗi màn có một câu hỏi duy nhất mà khối lớn nhất phải trả lời, một "phát hiện" đặt ngay dưới tiêu đề, và việc hay làm nhất cách một cú bấm.

### 5.1 Trang dự án (= "Cuộc trò chuyện mới" khi đang ở trong một dự án) [MỚI]

- **Câu hỏi:** "Dự án này có gì, đang dở việc gì?"
- **Phát hiện** (một dòng dưới tiêu đề, mỗi số là liên kết): "Cần chú ý: 3 rủi ro cần xử lý · 1 văn bản căn cứ đã hết hiệu lực mà 2 rủi ro còn dẫn tới · 4 văn bản được nhắc tới mà chưa có trong kho."
- **Việc hay làm nhất:** hỏi. Ô hỏi nằm ngay dưới, như mọi màn (kèm chip phạm vi). Gợi ý câu hỏi lấy từ thẻ và ghi chú của bạn, không bịa.
- Bố cục 1440 (khung cột rộng tối đa 1.000px; không có trình đọc đang mở):

```
Xe cơ giới và bảo hiểm                       [Thêm văn bản] [Mở sổ rủi ro]
14 văn bản · 7 rủi ro · cập nhật hôm nay 09:14
Cần chú ý: 3 rủi ro cần xử lý · 1 căn cứ hết hiệu lực · 4 chưa có trong kho
+------------------------------------+ +---------------------------------+
| Rủi ro đang mở (5 trên 7)          | | Bối cảnh và ghi chú dự án       |
|  hàng rủi ro dạng gọn x5           | |  [ chữ bạn viết, sửa tại chỗ ]  |
|  Xem sổ rủi ro (7)                 | |  máy đọc phần này khi trả lời   |
+------------------------------------+ +---------------------------------+
| Văn bản trong dự án (6 trên 14)    | | Cuộc trò chuyện gần đây (5)     |
|  số hiệu · trích yếu · hiệu lực    | +---------------------------------+
|  Xem cả 14                         | | Chưa có trong kho (4)  Thêm tệp |
+------------------------------------+ +---------------------------------+
[ ô hỏi, chip phạm vi, ba ô lọc ]
```

- Cột phải là dòng thông tin ổn định (bối cảnh, lịch sử, thiếu gì); cột trái là việc cần làm. Khối nào có hành động thì đứng trước khối chỉ để đọc (khi xếp chồng ở màn hẹp).
- **Bối cảnh dự án:** ô chữ 500 đến 2.000 ký tự, có bộ đếm; lời giải thích một dòng "Máy đọc phần này mỗi khi trả lời trong dự án này (khi bật AI)". Không có tóm tắt do máy sinh.
- **Dự án trống:** giữ khung và tiêu đề; một câu "Dự án chưa có văn bản"; nút "Thêm văn bản từ kho"; gợi ý "Chọn theo thẻ #bảo-hiểm (6 văn bản)".
- **Toàn kho** không có trang tổng quan; màn đầu là trạng thái trống của P1 (câu hỏi mẫu), thêm một dòng "Chọn hoặc tạo dự án để gom văn bản".

### 5.2 Hỏi đáp và tra rủi ro theo từ khoá [P1 khung; P2 chip và ghi chú; P3 AI; tra rủi ro MỚI]

- **Câu hỏi:** "Từ khoá này có rủi ro gì, căn cứ ở đâu?"
- **Quy tắc tra:** nếu có ghi chú loại Rủi ro khớp từ khoá thì nhóm "Bạn đã ghi" đứng đầu, bất kể câu hỏi viết thế nào. Không có thì kết quả như P1. **Không cần AI**: nhóm này hiện ngay từ chỉ mục chữ (P2); AI chỉ thêm đoạn tóm tắt phía trên (P3).
- **Giải phẫu một lượt trả lời:**

1. Dòng phạm vi: chip chỉ đọc + "Dựa trên 22 văn bản".
2. Tiêu đề kết quả và **phát hiện**: "Bạn đã ghi 4 rủi ro cho 'bảo hiểm xe', 2 còn cần xử lý. 1 căn cứ đã hết hiệu lực."
3. *(P3, khi bật AI)* "Tóm tắt (do máy viết)": 2 đến 3 câu, có chip `[n]`.
4. Nhóm **"Bạn đã ghi (4)"**: hàng rủi ro (mục 4.2), mặc định 5 hàng, "Xem thêm N".
5. Nhóm **"Điều luật khớp từ khoá, chưa có ghi chú (6)"**: kết quả gọn của P1, mỗi mục thêm nút "Thêm vào sổ rủi ro". Nhóm theo văn bản như P1.
6. Dải "Kiểm tra hiệu lực căn cứ" (mục 4.5).
7. *(P3)* "Đã dùng: Bối cảnh dự án · 2 ghi chú của bạn" (chip, bấm mở): để người dùng biết vì sao câu trả lời thế này.
8. Hành động: "Lưu vào ghi chú" (lưu mã đơn vị, không sao chép chữ, để khi văn bản đổi thì chip báo "căn cứ đã thay đổi"), "Xuất Word" [P5].

- **Không có tệp, không có ghi chú:** nhóm "Bạn đã ghi" không hiện. Có một dòng nhỏ ở cuối: "Chưa có ghi chú rủi ro nào khớp. Bấm 'Thêm vào sổ rủi ro' ở một điều luật, hoặc nhập tệp tóm tắt của bạn."
- **Không có kết quả trong phạm vi:** khung đã có sẵn của P1 (`.none`), chữ "Không tìm thấy trong phạm vi này (Dự án X, 14 văn bản)", nút "Mở rộng ra Toàn kho (3 văn bản có khớp)", và "Thêm tệp" nếu thấy văn bản được nhắc mà chưa có.
- **Đang chờ:** kết quả tìm hiện trước (P1); AI chạy sau (dòng "đang kiểm tra nguồn..." của P3). Không bao giờ chặn bảng rủi ro chờ AI.
- **Ô hỏi:** thêm hàng chip phạm vi (mục 4.4); phần còn lại như P1.

### 5.3 Sổ rủi ro [MỚI, dựng trên ghi chú P2]

- **Câu hỏi:** "Rủi ro nào của tôi đang chờ, và căn cứ còn vững không?"
- **Phát hiện:** dải đếm ngay dưới tiêu đề, **chính là bộ lọc**: `Cần xử lý 3 · Đã xử lý 4 · Chưa gắn căn cứ 1 · Cần xem lại 1` (một khối chia bằng đường kẻ mảnh, không phải bốn thẻ; số theo khung nhìn hiện tại). Có nút "Bỏ lọc".
- **Bảng** (từ 1100px): Rủi ro (lời bạn) | Căn cứ (địa chỉ và hai dòng đầu của trích) | Hiệu lực (huy hiệu) | Văn bản | Dự án | Trạng thái. Bấm một dòng thì mở thành hàng rủi ro đầy đủ (mục 4.2). Số gạch ngang xám cho ô trống, không số 0 giả. Dưới 640px mỗi dòng thành hai dòng (rủi ro và trạng thái ở dòng 1; địa chỉ và hiệu lực ở dòng 2).
- **Việc hay làm nhất:** thêm một rủi ro (nút "Thêm rủi ro"); nhập từ tệp (nút "Nhập từ tệp tóm tắt"); mở đúng đoạn ngay ở dòng.
- **Nhập từ tệp tóm tắt của bạn:** mỗi dòng của tệp thành một ghi chú loại Rủi ro "chưa gắn căn cứ", nhãn "Bạn ghi (từ tệp)". Màn hình "Gắn căn cứ" cho từng dòng: gợi ý Điều khớp nhất từ tìm kiếm, người bấm "Gắn" hoặc "Chọn đoạn khác". Không tự gắn. (Cột của tệp chị chưa biết: mục 14.)
- **Phạm vi:** theo thanh bên (dự án hoặc Toàn kho). Ở Toàn kho có cột "Dự án".
- **Xuất:** "Xuất Excel" [MỚI], "Xuất Word" [P5]. Có nhãn "Bạn ghi" và "Luật quy định" tách cột, ngày xuất, hiệu lực theo kho.
- **Trống:** giữ khung, một câu "Chưa có rủi ro nào. Chọn một đoạn trong văn bản rồi bấm 'Thêm vào sổ rủi ro', hoặc nhập tệp của bạn."
- Không có điểm số, không có phần trăm, không có "mức độ" tự sinh. (Cột "mức độ" chỉ thêm nếu tệp của chị đang có.)

### 5.4 Văn bản (Danh sách và Sơ đồ), cho cả hai phạm vi [P2 danh sách; sơ đồ dự án MỚI]

- **Câu hỏi:** "Có những văn bản nào, tình trạng ra sao, còn thiếu gì?"
- Bảng: Số hiệu · Trích yếu · Loại · Hiệu lực · Thẻ · Dự án (tối đa 2 chip, rồi "+n") · Ghi chú (số, kèm số rủi ro cần xử lý) · Ngày. Lọc: loại, hiệu lực, thẻ, "Thiếu thông tin". Chọn nhiều dòng để gắn thẻ hoặc thêm vào dự án.
- Trong một dự án thêm: "Thêm văn bản từ kho" (hộp chọn có tìm), "Gỡ khỏi dự án" (mục 3.5), nhóm **"Gợi ý thêm vào dự án (từ quan hệ)"**: danh sách tick chọn dựng từ căn cứ, hướng dẫn, sửa đổi của các văn bản đã có; người chọn cái nào đem vào. [MỚI, dùng P4]
- **Nhóm "Được nhắc tới nhưng chưa có trong kho (4)"**: danh sách phẳng xếp theo số lần được nhắc, mỗi dòng có số lần nhắc, văn bản nhắc tới, nút "Thêm tệp" (kéo thả Word hoặc PDF). Khi tệp được thêm và khớp thì dòng tự biến mất kèm một thông báo ngắn, không đổi lặng lẽ. [P4]
- **Công tắc "Danh sách ⇄ Sơ đồ"** (chỉ ở khung dự án): "Sơ đồ" là bản đồ dự án (mục 6.13). Danh sách là bản thay thế cho người dùng bàn phím và màn hình đọc.

### 5.5 Trình đọc [P1 + ngăn ghi chú P2 + tab Liên quan P4]

Giữ nguyên bố cục P1: ngăn trượt bên phải, nút mở rộng, đầu trang, các tab. Thay đổi:

- **Đầu trang:** loại và số hiệu, huy hiệu hiệu lực, nút **"Ghi chú · 3"** (mở ngăn), nút mở rộng, đóng. Dòng meta như P1, rồi **dòng lý do hiệu lực** (một dòng, mục 4.1), rồi tối đa 3 chip thẻ ("+2"). "Sao chép trích dẫn" như P1.
- **Ba tab:** Văn bản · Bản gốc · Liên quan (kèm số). Không thêm tab thứ tư.
- **Ngăn "Ghi chú và rủi ro"** (rộng khoảng 320px; trong chế độ mở rộng thì gắn bên phải thân văn bản, thân văn bản hẹp lại; ở ngăn thường thì phủ lên phần phải của trình đọc), theo thứ tự:
  1. **Thẻ:** chip + "Thêm thẻ". [P2]
  2. **Có trong dự án:** các chip dự án + "Thêm vào dự án". Một dòng nhỏ: "Gỡ khỏi dự án không xoá văn bản." [MỚI]
  3. **Ghi chú:** hai nhóm "Chung của văn bản" và "Trong dự án X". Mỗi ghi chú có biểu tượng loại (bút = ghi chú, cờ = rủi ro), chữ của bạn, địa chỉ đoạn (liên kết), trạng thái nếu là rủi ro, "Sửa". Nút "Ghi chú cho cả văn bản". [P2; loại Rủi ro MỚI]
  4. **Tệp của bạn:** tên tệp, "Bạn ghi (từ tệp)", "Mở tệp", "Nhập các dòng rủi ro (7)". [MỚI]
- **Bôi chọn một đoạn:** thanh nổi nhỏ: "Ghi chú · Thêm vào sổ rủi ro · Sao chép trích dẫn".
- **Lề thân văn bản:**
  - Dấu bút nhỏ ở lề nếu đoạn có ghi chú; bấm thì ngăn mở tới ghi chú đó. [P2]
  - Dưới tên Điều bị sửa: nhãn "Đã sửa bởi NĐ 214/2013 Điều 1 · Xem hai bản" mở hai cột nguyên văn cạnh nhau (bản cũ, bản sửa) kèm câu tạo ra quan hệ. Tự phát hiện thì thêm "Tự nhận diện, nên kiểm tra". Không dựng "nội dung hợp nhất". [P4]
- **Tab Bản gốc:** như P1; thêm khung tô trên ảnh trang [P2]; ghi chú gắn vào đoạn hiện thành một dấu trên khung.
- **Văn bản không thuộc dự án đang chọn:** dải trên đầu "Văn bản này không thuộc dự án X. [Thêm vào dự án]".
- **Chế độ mở rộng:** mục lục Điều (trái) | thân văn bản | ngăn ghi chú (phải, khi mở).

### 5.6 Tab Liên quan [P4]

- **Câu hỏi:** "Văn bản này nối với văn bản nào, và cái nào đổi hiệu lực của nó?"
- **Phát hiện** (câu mở đầu, như LuatVietnam viết thành câu): "Hết hiệu lực. Bị thay thế bởi NĐ 03/2021/NĐ-CP (chưa có trong kho). Trong kho có 1 văn bản sửa đổi và 1 văn bản hướng dẫn." Dưới đó là dải cơ sở (mục 4.1).
- **Thanh công cụ:** công tắc "Danh sách ⇄ Sơ đồ"; chip đếm là bộ lọc: `Tất cả 9 · Căn cứ 3 · Hướng dẫn 1 · Sửa đổi 1 · Thay thế 2 · Dẫn chiếu 2` + "Bỏ lọc" (không cần phím Shift hay thao tác ẩn).
- **Danh sách**, xếp theo mức ảnh hưởng tới hiệu lực: sửa đổi, thay thế, bãi bỏ trước; rồi hướng dẫn; rồi căn cứ; rồi dẫn chiếu. Tiêu đề nhóm viết từ góc nhìn của văn bản đang mở: "Bị sửa đổi, bổ sung bởi", "Sửa đổi", "Bị thay thế bởi", "Thay thế", "Được hướng dẫn bởi", "Căn cứ vào", "Dùng làm căn cứ cho", "Dẫn chiếu tới", "Được dẫn chiếu bởi".
  - Mỗi dòng: tên (số hiệu + trích yếu ngắn), huy hiệu hiệu lực, ngày, **câu trích nguyên văn tạo ra quan hệ** (số hiệu khớp gạch dưới bút bi xanh), "Mở đúng đoạn" (ở văn bản nguồn), nhãn nguồn: "Đọc từ văn bản" hoặc "Bạn xác nhận" hoặc "Tự phát hiện, nên kiểm tra" kèm [Xác nhận] [Bỏ qua].
  - **Dòng mờ** (văn bản chưa có): "Có nhắc tới, chưa có trong kho" + "Thêm tệp".
- **Dòng thời gian "Lịch sử văn bản"** (danh sách dọc, có ngày): ban hành · có hiệu lực · sửa đổi lần 1 · thay thế. Nhãn giống chú giải sơ đồ. Không vẽ thêm biểu đồ thời gian.
- **"Gợi ý quan hệ (2)"** (hộp thư đến cho chỗ nhắc mà chưa nối): hiện câu nguyên văn, "đúng số hiệu, năm và cơ quan", nút [Xác nhận: Dẫn chiếu ▾] [Bỏ qua]. Danh sách chọn chỉ có loại trong bảng đóng (không gõ tự do). Cạnh gợi ý vẽ nhạt kèm dấu "?" cho tới khi người dùng xác nhận.
- **"Nội dung tương tự (không phải quan hệ pháp lý)"**: mục riêng, **thu gọn, tắt mặc định**, dựng từ vector.
- Nút "Xuất danh sách (CSV, Word)".

---

## 6. Sơ đồ quan hệ cục bộ: đặc tả [P4]

### 6.1 Mục đích

Một câu hỏi: **"Văn bản này nối với những văn bản nào, và cái nào đổi hiệu lực của nó?"** Sơ đồ không phải trang chủ, không phải chỗ làm việc; việc thật (đọc, ghi chú, trích dẫn) xảy ra ở thẻ chi tiết và trình đọc. Mọi thứ trên sơ đồ có trong danh sách cùng tab.

### 6.2 Khi nào vẽ

| Số văn bản liên quan | Hiện |
|---|---|
| 0 | Trạng thái trống: "Văn bản này chưa có quan hệ nào trong kho." + "Gợi ý quan hệ (n)" + "Thêm tệp" nếu có chỗ nhắc |
| 1 đến 3 | **Chỉ danh sách** và câu mở đầu. Ẩn công tắc "Sơ đồ" (vẽ 3 nút là thừa) |
| 4 đến 25 | Vẽ đủ |
| 26 đến 60 | Vẽ có gộp ("+N văn bản khác") |
| trên 60 | Chỉ vẽ 60 nút điểm cao nhất; dòng "Đang hiện 60 trên 134. Xem đủ ở dạng danh sách" |
| trần kỹ thuật | 200 nút dựng và vẽ ≤ 1 giây (ràng buộc của lộ trình; không phải mục tiêu hiển thị) |

### 6.3 Nút

Quy tắc: **bốn kênh tối đa**: vị trí (hàng và cột), hình trong nút (hiệu lực), kiểu viền (vai trò), huy hiệu (rủi ro). Không dùng kích thước nút, không dùng màu phân loại.

| Thứ | Biểu diễn |
|---|---|
| Văn bản trong kho | Chữ nhật bo 6px, cao 28px: **[hình hiệu lực] + nhãn ngắn** 12px/500: "NĐ 100/2019", "TT 22/2016/BTC". Tên đầy đủ ở thẻ chi tiết và tooltip |
| Hình hiệu lực | tròn đặc (còn), tròn nửa (một phần), tròn rỗng (hết), thoi rỗng (chưa có hiệu lực), dấu hỏi (chưa rõ hoặc có thể đã bị thay thế). Nhãn chữ nằm trong chú giải và trong đọc màn hình |
| Trung tâm | Viền bút bi xanh 2px, nền `--pen-tint`, cao 34px |
| Đang chọn | Viền bút bi xanh 2px (nền giữ nguyên). Các cạnh của nút đang chọn đổi sang nét bút bi xanh |
| Trong dự án (khi đang ở phạm vi dự án) | Viền `--muted` liền 1px, nền `--surface` |
| Ngoài dự án | Nền trong suốt, viền `--control`, chữ `--muted`, thẻ chi tiết có "Thêm vào dự án" |
| **Nút mờ (chưa có trong kho)** | **Viền nét đứt**, nền trong suốt, có dấu "+" ở cuối nhãn. Nét đứt chỉ dành cho nút mờ và cạnh nối tới nó |
| Có rủi ro cần xử lý | Huy hiệu tròn 16px góc trên phải, số trắng trên nền mực, "2" |
| Gộp "+N khác" | Chữ nhật nét liền có số; bấm thì mở **danh sách** đã lọc (không phình tại chỗ, để khỏi xê dịch bố cục) |
| Nội dung tương tự (khi bật) | Nút thường, có dấu "≈" nhỏ ở đầu |

Dưới nút hiện ngày ban hành 11px `--muted` khi nút được chọn hoặc rê chuột, không hiện sẵn hết (giảm chữ).

### 6.4 Cạnh: kiểu đường, đầu mũi tên, nhãn

Năm kiểu, **gộp loại hiếm** (nghiên cứu: quá năm kiểu thì người xem không phân biệt nổi). Nét tối thiểu 1,5px để dấu chấm và nét đứt không biến mất.

| Quan hệ | Kiểu vẽ | Hướng | Nhãn chữ |
|---|---|---|---|
| Căn cứ, hướng dẫn | Nét liền mảnh 1,5px, màu `--edge`, mũi tên nhỏ | Từ văn bản nêu quan hệ tới văn bản gốc | "căn cứ" hoặc "hướng dẫn" |
| Sửa đổi, bổ sung | Nét liền **dày 3px**, màu `--edge-heavy`, mũi tên đặc | Từ văn bản sửa tới văn bản bị sửa | "sửa đổi" |
| Thay thế, bãi bỏ | Nét dày 3px, **đầu chặn (vạch ngang)** ở văn bản bị chấm dứt | Từ văn bản thay tới văn bản bị thay | "thay thế" hoặc "bãi bỏ" |
| Dẫn chiếu | Chấm tròn, mảnh 1,5px, mũi tên nhỏ | Từ văn bản dẫn tới văn bản được dẫn | "dẫn chiếu" |
| Nội dung tương tự (tắt mặc định) | Chấm thưa 1px, không mũi tên, vạch "≈" giữa cạnh | Không hướng | Chú giải ghi "Gợi ý theo nội dung, không phải quan hệ pháp lý" |

- **Nguồn của cạnh** là một kênh riêng: cạnh "Tự phát hiện" (chưa xác nhận) vẽ nhạt 60% và có dấu "?" ở giữa cạnh; đã xác nhận hoặc đọc chắc từ văn bản thì không có dấu.
- Cạnh nối tới nút mờ vẽ **nét đứt** (cùng nghĩa: đầu kia chưa có trong kho).
- Nhãn chữ trên cạnh chỉ hiện cho cạnh của nút đang rê chuột, đang chọn, hoặc trung tâm; còn lại nằm trong chú giải. Điều này tránh nhãn chồng nhau.
- Bấm vào cạnh (vùng bắt chuột rộng 12px, vô hình) hiện **câu nguyên văn tạo ra quan hệ** ở thẻ chi tiết.

### 6.5 Bố cục: "Tầng" (tất định, không mô phỏng vật lý)

- **Bốn hàng** (nhãn hàng ở lề trái, 12px `--muted`, ngăn cách bằng đường kẻ `--rule`): Luật (Luật, Bộ luật, Pháp lệnh, Nghị quyết) · Nghị định (kể cả Quyết định của Thủ tướng) · Thông tư (kể cả liên tịch, quyết định của Bộ) · Khác. Nút mờ đặt hàng theo loại đọc được từ câu nhắc ("Nghị định số 03/2021/NĐ-CP"); không đọc được thì hàng "Khác".
- **Cột:** theo ngày ban hành, từ trái (cũ) sang phải (mới), **cách đều theo thứ tự ngày** (không theo tỉ lệ thời gian: tỉ lệ thời gian làm nút dồn cục và để trống nhiều). Trục "ngày ban hành →" ở đáy, chỉ ghi năm đầu và năm cuối. Hai nút trùng ngày xếp thành hai tầng con (tối đa hai mỗi hàng); phá thế hoà bằng số hiệu theo thứ tự chữ.
- **Hệ quả đọc được:** căn cứ nằm hàng trên; hướng dẫn nằm hàng dưới; sửa đổi và thay thế cùng hàng, lệch sang phải (mới hơn). Cạnh cùng hàng vẽ thành cung cố định phía trên hoặc phía dưới hàng, để không đi xuyên nút.
- **Tính một lần trên bản 2 bước (đã gồm mọi nút lớp 1 và lớp 2, trong ngân sách), rồi hiện lớp 1 trước.** Bấm "Mở rộng thêm một bước" chỉ hiện thêm nút, **không nút nào đổi chỗ**. Vì vậy vị trí luôn giống nhau mỗi lần mở: bố cục là hàm của dữ liệu, không cần lưu toạ độ. (Tỉ lệ khung có thể đổi để vừa; thứ tự và vị trí tương đối giữ nguyên.)
- Chu trình (A dẫn B, B dẫn A): phá bằng ngày; cạnh ngược vẽ thành cung. Không có số ngẫu nhiên nào ở bất kỳ bước nào.
- **Kiểm tra bắt buộc:** cùng đầu vào cho cùng toạ độ (có test); 200 nút dựng và vẽ ≤ 1 giây trên máy chuẩn (có thước đo).
- Vì sao không dùng lực đẩy cho sơ đồ cục bộ: vị trí đổi mỗi lần mở làm mất trí nhớ không gian (người dùng Obsidian phàn nàn đúng chuyện này), tốn CPU, và không có trục nào mang nghĩa. Yêu cầu ban đầu nêu bố cục lực đẩy có hạt giống cố định: nó được giữ cho bản đồ dự án (mục 6.13), nơi hàng thứ bậc không đủ.

### 6.6 Ngân sách nút, gộp, và nút "nhắc quá nhiều"

- Lần vẽ đầu (1 bước) tối đa **25 nút**; sau khi mở rộng tối đa **60**; trần kỹ thuật 200. Các số này là điểm khởi đầu, đo lại trên kho thật.
- **Sức chứa theo bề rộng:** mỗi hàng chứa khoảng `rộng khung ÷ 124px` nút (nhãn + hình + khoảng cách). Ở ngăn trình đọc thường (khoảng 620px) vừa 5 nút mỗi hàng, tức khoảng 12 nút cả bốn hàng; ở chế độ mở rộng (khoảng 1.000px) vừa 8 mỗi hàng, tức khoảng 25. **Chữ trên nút không bao giờ nhỏ hơn 12px:** khi không đủ chỗ thì gộp thêm, không thu nhỏ chữ. Khi quá 12 nút ở ngăn thường, sơ đồ đề nghị "Mở rộng để xem đủ" và danh sách vẫn là tab mặc định.
- **Điểm quan tâm** (đề xuất của tôi, chưa có nguồn): thay thế, sửa đổi, bãi bỏ = 5; hướng dẫn = 4; căn cứ = 3; dẫn chiếu = 2; tương tự = 1; cộng 2 nếu trong dự án; cộng 2 nếu có ghi chú rủi ro; cộng 1 nếu ban hành trong 12 tháng. Dòng giải thích: "Sắp xếp: quan hệ pháp lý trước, rồi dự án."
- **Quy tắc đúng-sai, không phải kiểu dáng:** **không bao giờ gộp** nút láng giềng của trung tâm theo quan hệ sửa đổi, thay thế, bãi bỏ, kể cả nút mờ. Chúng quyết định cái gì còn hiệu lực.
- **Văn bản nhắc quá nhiều** (nút ngoài trung tâm, có ≥ 8 văn bản trong khung nhìn nhắc tới, và không nối tới trung tâm bằng sửa đổi hay thay thế): ẩn mặc định, dòng "Đang ẩn 1 văn bản được nhắc nhiều (Luật Xử lý vi phạm hành chính) · Hiện" (không im lặng). Vẽ nó một lần với số đếm thay cho 150 cạnh.
- Luôn có "đang ẩn N văn bản" kèm nút; không cắt lặng.

### 6.7 Tương tác (đều dùng được bằng bàn phím và chuột; không có thao tác chỉ kéo thả)

| Thao tác | Kết quả |
|---|---|
| Rê chuột hoặc focus vào nút | Nút và láng giềng trực tiếp giữ nguyên độ đậm; phần còn lại mờ còn 45% (vẫn đủ đọc); nhãn cạnh của nút đó hiện |
| Bấm hoặc Space | Chọn: thẻ chi tiết cập nhật (mục 6.8), cạnh của nút chuyển sang bút bi xanh |
| Enter | Mở văn bản trong trình đọc (ở tab Văn bản, tại đoạn nếu chọn từ cạnh) |
| Bấm đúp hoặc phím C hoặc nút "Đặt làm trung tâm" | Đổi trung tâm; có nút "← Quay lại NĐ 103/2008" (ngăn xếp quay lại, tối đa 10) |
| Nút "Mở rộng thêm một bước (thêm khoảng 14 văn bản)" / "Thu lại một bước" hoặc phím + và − | Đổi độ sâu (1 hoặc 2); số văn bản thêm hiện **trước** khi bấm |
| Bấm cạnh | Thẻ chi tiết hiện câu nguyên văn tạo quan hệ |
| Esc | Bỏ chọn; lần hai thì ra khỏi sơ đồ |
| Phím 0 hoặc nút "Vừa khung" | Căn lại; nút + và − thu phóng; Ctrl+cuộn cũng thu phóng (cuộn thường vẫn cuộn trang) |
| Kéo để dịch chuyển | Có, nhưng chỉ bổ sung; mọi việc đều có nút hoặc phím tương đương. **Không có kéo nút** |

**Bàn phím:** sơ đồ là **một điểm dừng Tab**; trong đó mũi tên đi qua các nút **theo thứ tự của danh sách** (nhóm theo loại quan hệ), không theo toạ độ. Vòng focus 2px bút bi xanh, chừa lề trong khung để không bị cắt (kiểm trên cửa sổ Edge app thật).

### 6.8 Thẻ chi tiết (cùng tab, dưới sơ đồ khi hẹp, bên phải khi chế độ mở rộng)

- **Khi chọn nút:** tên đầy đủ, huy hiệu + dòng lý do, **câu nguyên văn tạo ra quan hệ với trung tâm** (số hiệu gạch dưới bút bi xanh), ghi chú rủi ro cần xử lý (nếu có), thuộc dự án nào. Nút: [Mở văn bản] [**Hỏi về văn bản này**] (mở cuộc trò chuyện mới có chip `@văn bản`, giữ nguyên dự án) [Đặt làm trung tâm] [Thêm vào dự án] (nếu ngoài dự án) [Thêm tệp] (nếu là nút mờ).
- **Khi chọn cạnh:** loại, hướng, câu nguyên văn, nguồn (đọc từ văn bản / bạn xác nhận / tự phát hiện) và [Xác nhận] [Bỏ qua] [Đổi loại ▾] (danh sách đóng).
- Đây là bộ kiểm tra của bạn: mỗi quan hệ trên sơ đồ kiểm chứng được bằng một câu nguyên văn, cũng như một trích dẫn.

### 6.9 Chú giải

Luôn có ở góc dưới trái của khung vẽ (thu gọn được, mở mặc định): chỉ liệt kê các kiểu **đang có trên màn hình**. Mỗi mẫu trong chú giải là chính nét vẽ thu nhỏ (cùng đối tượng kiểu với nét thật, để không lệch nhau). Gồm: hình hiệu lực (năm hình, mỗi hình một chữ), kiểu viền nút (trung tâm, trong dự án, ngoài dự án, chưa có trong kho), năm kiểu cạnh, dấu "?" (tự phát hiện), huy hiệu rủi ro.

### 6.10 Màu và kênh

- Sơ đồ **không màu**: mực, xám, một màu nhấn. Bút bi xanh chỉ dành cho: trung tâm, nút và cạnh đang chọn, từ khớp trong câu bằng chứng, vòng focus. Dưới 5% pixel màn hình.
- **Không dùng bảng màu phân loại.** Lý do: bốn loại quan hệ phân biệt bằng nét và đầu mút, loại văn bản bằng hàng, hiệu lực bằng hình; màu không thêm thông tin, thất bại ở thang xám và với người mù màu, và nghiên cứu Kinopio cho thấy màu thành trang trí khi không gắn một nghĩa. Màu của huy hiệu hiệu lực (`pos`, `warn`, `neg`) chỉ xuất hiện ở thẻ chi tiết và bảng, nơi luôn đi kèm chữ.
- Tương phản: cạnh và viền nút ≥ 3:1 so với nền khung vẽ (WCAG 1.4.11), chữ ≥ 4,5:1; kiểm cả sáng và tối.

### 6.11 Các trạng thái

| Trạng thái | Hiện |
|---|---|
| Trống | Câu mở đầu, "Gợi ý quan hệ", "Thêm tệp" |
| Thưa (1–3) | Chỉ danh sách, không sơ đồ |
| Đủ (4–25) | Vẽ đủ, chú giải, thẻ chi tiết |
| Dày (26–60) | Gộp "+N khác" theo loại ("14 Thông tư hướng dẫn"), ẩn nút nhắc quá nhiều có thông báo |
| Quá trần | Dòng "Đang hiện 60 trên N"; danh sách có đủ |
| Đang tải | Khung và nhãn hàng hiện ngay; chỗ nút là thanh xám phẳng đúng cỡ thật (không lấp lánh); thường dưới 1 giây nên có thể không thấy |
| Lỗi | Trong khung vẽ: "Không dựng được sơ đồ. Danh sách vẫn xem được." + "Thử lại"; không biểu ngữ toàn màn |
| Giảm chuyển động | Không có hoạt hoạ nào; không làm gì thêm |
| Tối | Dùng token tối (mục 7) |

### 6.12 Tiếp cận (là trung tâm, không phải phụ lục)

- **Danh sách là bản chính**, sơ đồ là hình vẽ từ cùng truy vấn; chọn ở một bên là chọn ở bên kia. Bảng danh sách nhìn thấy được và đứng trước, không phải bảng ẩn dành riêng cho trình đọc màn hình.
- Khung vẽ: `role="group"` có nhãn tóm tắt: "Sơ đồ quan hệ của Nghị định 103/2008/NĐ-CP: 1 căn cứ, 1 hướng dẫn, 1 sửa đổi, 2 thay thế, 2 chưa có trong kho." Mỗi nút là nút thật (`<a>` hoặc `button`) có nhãn: "Nghị định 214/2013/NĐ-CP, sửa đổi, bổ sung văn bản đang xem, còn hiệu lực. Nhấn Enter để mở." Vùng thông báo (`aria-live`) đọc khi đổi focus.
- Nút + − 0 và "Mở rộng thêm một bước" là nút thật, mục tiêu cảm ứng ≥ 44px ở màn hẹp. Tuân thủ WCAG 2.5.7: không việc nào chỉ làm được bằng kéo.
- **Bản kiểm thử đi kèm P4:** kịch bản chỉ bàn phím (Tab, mũi tên, Enter, Space, Esc, +, −, 0); kiểm nhanh với trình đọc màn hình; kiểm tương phản sáng/tối.
- **Xuất:** "Xuất ảnh (PNG)" để dán vào file tóm tắt rủi ro; "Xuất danh sách (CSV, Word)" vì ảnh thôi thì không dùng lại được. [P4/P5]

### 6.13 Bản đồ dự án [MỚI]

**Có cần không? Có, nhưng nhỏ và là cách xem thứ hai.** Lý do và giới hạn, nói thẳng:

- **Nó trả lời một câu mà bảng trả lời kém:** "Dự án này còn thiếu gì, văn bản nào lẻ loi, rủi ro dồn ở văn bản nào?" Bảng phải sắp xếp mới thấy; bản đồ cho thấy ngay (nút mờ, cụm, nút đơn lẻ, huy hiệu rủi ro).
- **Dự án là tập nhỏ** (dưới 60 văn bản) nên không thành mớ rối; toàn kho thì có thể có hàng nghìn văn bản, **nên không có bản đồ toàn kho**.
- **Nhưng nghiên cứu không cho thấy người dùng văn phòng dùng nó.** Mọi nguồn đều nói đồ thị toàn cục là trang trí (Obsidian), và khách thật không cần đồ thị để làm việc chính. Vì vậy: không phải trang đầu, không có trong thanh bên, chỉ là công tắc "Danh sách ⇄ Sơ đồ" ở trang Văn bản của dự án (mục 5.4). **Tiêu chí bỏ:** nếu sau một tuần dùng thử chị không mở lần nào, giữ ở mức nhỏ hoặc bỏ. Khớp với lộ trình mục 9, điều 7.
- **Nút = văn bản.** Ghi chú và rủi ro là **huy hiệu trên nút**, không phải nút: mỗi ghi chú chỉ gắn vào một văn bản, thêm nút cho chúng chỉ tạo ra các "lá" quanh nút cha, ba lần số nút mà không thêm thông tin. **Một lớp tuỳ chọn** (tắt mặc định, "Hiện rủi ro nối nhiều văn bản"): một rủi ro dẫn tới ≥ 2 văn bản thì vẽ thành nút vuông nhỏ có chữ "R" nối các văn bản đó. Đây là chỗ duy nhất rủi ro có ý nghĩa như một nút; để chủ dự án xem và quyết trong bản thử.
- **Cạnh và chú giải:** y như mục 6.4 và 6.9, chỉ gồm quan hệ giữa các văn bản trong dự án và các nút mờ nối với chúng. Công tắc "Chỉ văn bản đã có" tắt nút mờ.
- **Bố cục "Cụm"** (tất định, đây là chỗ dùng lực đẩy có hạt giống cố định theo yêu cầu):
  1. Tách thành các cụm liên thông; cụm lớn nhất đứng trước, xếp thành hàng.
  2. Mỗi cụm chạy lực đẩy: điểm bắt đầu xếp xoắn ốc kiểu hạt hướng dương (phyllotaxis) có hạt giống `băm(mã dự án)`; khoảng cách cạnh: sửa đổi, thay thế 70px, hướng dẫn, căn cứ 110px, dẫn chiếu 150px; lực đẩy giữa nút tỉ lệ nghịch bình phương; chống chồng lấn theo nửa bề rộng nút; **300 bước chạy đồng bộ một lần, không hoạt hoạ**.
  3. Nút đơn lẻ (không nối với văn bản nào) xếp thành một dải riêng dưới cùng, có tên "Chưa nối với văn bản nào (3)".
  4. **Lưu toạ độ vào DB theo dự án.** Chỉ tính lại khi bấm "Sắp xếp lại"; khi thêm hoặc gỡ văn bản, các nút cũ giữ chỗ, nút mới đặt gần láng giềng đã có.
  5. Không có kéo nút (chống mất trí nhớ không gian bằng nút "Sắp xếp lại", không bằng kéo thả).
  6. Chi phí ước: lực đẩy tính theo cặp nút, 60 nút × 300 bước khoảng nửa triệu phép tính cặp; 200 nút khoảng 6 triệu, kỳ vọng dưới 1 giây trong JavaScript thuần. Đây là ước tính, phải đo trên máy chuẩn.
- Nút, tương tác, bàn phím, ngân sách, trạng thái, tiếp cận: dùng lại nguyên mục 6.3 đến 6.12 (kể cả danh sách thay thế và "Hỏi về văn bản này").

### 6.14 Ghi chú kỹ thuật cho người dựng

- Dữ liệu: `doc_relations` (P4) + `WITH RECURSIVE` của SQLite cho 1 và 2 bước; không dựng kho đồ thị. Bố cục tính ở trình duyệt bằng JavaScript thuần trong một tệp `static/graph.js`; SVG tự vẽ, không thư viện.
- Mỗi cạnh lưu: nguồn, đích, loại, câu nguyên văn, **nguồn** (đọc từ văn bản / bạn xác nhận / tự phát hiện) và độ chắc, để người dùng sửa được.
- Đồ thị chỉ dùng quan hệ đã đọc hoặc đã xác nhận; quan hệ tự phát hiện vẽ nhạt kèm dấu "?" (mục 6.4).

---

## 7. Hệ thống hình ảnh

**Giữ nguyên toàn bộ token P1** (`--ground`, `--surface`, `--raised`, `--active`, `--border`, `--rule`, `--control`, `--text`, `--muted`, `--faint`, `--primary`, `--pen`, `--pen-tint`, bốn cặp `pos/neg/warn/neu`, bán kính 8/6/4, chữ Be Vietnam Pro 12/13/14/16/22, sáng và tối). Chỉ thêm đúng các token sau, không màu mới:

```css
:root {
  --edge: #7a7a74;         /* cạnh mảnh: 4,3:1 trên trắng, 3,9:1 trên --ground */
  --edge-heavy: #2b2b29;   /* cạnh sửa đổi, thay thế */
  --dim: .45;              /* độ mờ của nút không liên quan khi rê chuột */
  --lane: var(--rule);     /* đường kẻ giữa các hàng */
  --canvas: var(--surface);
}
:root[data-theme="dark"] { /* cùng quy tắc :root:not([data-theme="light"]) trong @media dark như P1 */
  --edge: #9a9a94;         /* 6,3:1 trên --surface tối */
  --edge-heavy: #d0d0ca;
}
```

Các giá trị tương phản ở đây tính nhẩm; **phải chạy lại bộ kiểm tương phản** trước khi chốt.

| Hạng mục | Quy định |
|---|---|
| Chữ | Không thêm cỡ mới. Nhãn nút 12px/500; ngày dưới nút 11px (mức thấp nhất, `--muted`); thẻ chi tiết 13 và 14px; tiêu đề 22px |
| Biểu tượng | Cùng bộ nét 1,6px, 16px, màu xám như P1. Thêm: thư mục (dự án), bút (ghi chú), cờ nét (rủi ro), tờ giấy (cả văn bản), dấu tick (đã đối chiếu), liên kết. Không đặt trong ô màu |
| Bán kính | Nút 6px; chip phạm vi 6px; chip nguồn 4px; ghi chú hình viên thuốc 999px; hộp thoại 12px. Không thêm cỡ |
| Bóng đổ | Chỉ cho thứ nổi: hộp xem trước trích dẫn, bảng bộ chuyển dự án, hộp thoại. Không mờ kính, không gradient |
| Chuyển động | Không hoạt hoạ trong sơ đồ. Ngăn trượt như P1 (0,18 giây), hộp xem trước hiện ngay. Tôn trọng `prefers-reduced-motion` |
| Mật độ | Hàng rủi ro: hàng chữ 14px, khoảng cách theo bước 4px. Danh sách quan hệ: hàng 56px |
| Số | Chữ số tabular ở mọi bảng và số đếm; số căn phải |
| Sáng và tối | Mỗi mục trong bản này vẽ cả hai chế độ; bản bấm thử có công tắc sáng/tối. Màu bút bi xanh tối `#84adf0` như P1 |
| Màu "bút bi xanh" | Dưới 5% màn hình. **Dùng cho:** từ khớp, đoạn được dẫn, trung tâm và nút đang chọn của sơ đồ, câu bằng chứng khớp số hiệu, vòng focus. **Không dùng cho:** tiêu đề, biểu tượng thanh bên, viền chip, tab đang chọn, nút |

---

## 8. Co giãn: 1440, 1100, 768, 390

| Chiều rộng | Khung | Trang dự án | Hàng rủi ro | Trình đọc và sơ đồ | Bộ chuyển và ô hỏi |
|---|---|---|---|---|---|
| **1440** | Thanh bên 248 · cột chính · trình đọc `clamp(520px, 46vw, 720px)` (như P1) | Hai cột; mọi khối hiện tiêu đề và vài dòng đầu ngay màn đầu (1440×900) | Hai cột khi khung chứa ≥ 640px; khi mở trình đọc, cột chính chỉ còn khoảng 500px nên xếp chồng | Ngăn thường: tối đa 12 nút dễ đọc; trên đó "Mở rộng để xem đủ". Chế độ mở rộng: mục lục · thân · ngăn ghi chú; hoặc khung vẽ rộng (khoảng 1.000px, 25 nút) + thẻ chi tiết (360px) | Bộ chuyển ở đầu thanh bên; chip phạm vi trong khung ô hỏi |
| **1100** | Trình đọc phủ lên cột chính (đúng quy tắc ≤1240px của P1) | Một cột, cột phải nằm dưới | Xếp chồng | Ngăn 720px; mở rộng toàn cửa sổ, thẻ chi tiết xếp dưới khung vẽ | Như 1440 |
| **768** | Thanh bên thành ngăn kéo (≤900px của P1) | Một cột; khối có hành động lên trước | Xếp chồng; bảng thành dòng hai tầng | Trình đọc toàn chiều rộng; **Danh sách là tab mặc định**; Sơ đồ chỉ 1 bước, nhiều nút thì gộp | Nút tên dự án ở thanh trên; chip phạm vi một hàng cuộn ngang |
| **390** | Thanh trên 48px | Một cột: dòng "Cần chú ý" · Rủi ro đang mở · Văn bản · Bối cảnh · Chưa có trong kho | Xếp chồng; mục tiêu cảm ứng ≥ 44px | **Chỉ danh sách và câu mở đầu.** Tab Sơ đồ thay bằng "Sơ đồ xem được trên màn hình rộng hơn 700px. Dùng danh sách." (sơ đồ là thứ đầu tiên phải bỏ ở màn nhỏ) | Bộ chuyển là tờ toàn màn; chip phạm vi một hàng cuộn; chạm vào `[n]` mở thẳng trình đọc |

Quy tắc chung (từ taste-skill): lề ngang 16px; bảng thành danh sách hai dòng dưới 640px (định danh và số chính ở dòng 1, trường khác ở dòng 2, không bỏ trường nào); khối có hành động đi lên trước, không xuống dưới; trang không bao giờ cuộn ngang.

---

## 9. Bảng đối chiếu giai đoạn

| Thành phần | Giai đoạn | Ghi chú |
|---|---|---|
| Thanh bên: "Cuộc trò chuyện mới", lịch sử, tìm lịch sử | P1 | Đã dựng |
| Kết quả gọn, nhóm theo văn bản, "Cũng có ở", "Mở tại đoạn này" | P1 | Đã dựng |
| Trình đọc: tô đúng đoạn, mục lục, "Sao chép trích dẫn", tab Bản gốc | P1 | Đã dựng |
| Cặp màu hiệu lực `pos/neg/warn/neu`, ba giá trị (còn/hết/chưa rõ) do người đặt | P1 | Đã dựng |
| Xem trước "câu trả lời AI" | P1 (bản thử của P3) | Đã có trong mẫu |
| Hình trong huy hiệu, dòng lý do, dải cơ sở, "Chưa có hiệu lực", "Có thể đã bị thay thế", nhãn "Bạn đặt" | P2 | Mở rộng huy hiệu P1 |
| Trang Văn bản (kho): bảng, lọc, thiếu thông tin | P2 | |
| Thẻ, ghi chú theo văn bản và theo đoạn, ngăn "Ghi chú và rủi ro", dấu ghi chú ở lề | P2 | |
| `@` và `#`, chip phạm vi, "Hỏi trong văn bản này", "Không tìm thấy trong phạm vi này" | P2 | |
| Khung tô trên ảnh trang | P2 | |
| Ghi chú loại **Rủi ro**, hàng rủi ro hai cột, "Thêm vào sổ rủi ro" | **MỚI** | Dựng trên `user_notes`, thêm cột loại và trạng thái |
| **Nhóm "Bạn đã ghi" đứng đầu khi tra từ khoá; tìm ghi chú trước ở Toàn kho** | **MỚI** | Không cần AI |
| **Tệp ghi chú, rủi ro đính kèm theo văn bản; nhập thành rủi ro chưa gắn căn cứ** | **MỚI** | Cột tệp của chị chưa biết |
| **Sổ rủi ro** (bảng, đếm lọc, xuất Excel) | **MỚI** | Xuất Word ở P5 |
| **Dự án** (bộ chuyển, thành viên nhiều–nhiều, trang dự án, bối cảnh dự án, ghi chú theo dự án, cuộc trò chuyện theo dự án, "Chuyển vào dự án...", "Gỡ khỏi dự án") | **MỚI** | Bảng `projects`, `project_docs`, cột `project_id` ở `conversations` và `user_notes` |
| **"Gợi ý thêm vào dự án (từ quan hệ)"** | **MỚI** (dùng dữ liệu P4) | |
| Chip trích dẫn ba loại; hộp xem trước khi rê chuột | P3 | Chip `[n]` bấm mở đã có ở P1 |
| Ba trạng thái đối chiếu, dải "Kiểm tra hiệu lực căn cứ", "Đã dùng: ghi chú", nhãn "Tóm tắt (do máy viết)" | P3 | |
| "Lưu vào ghi chú" từ câu trả lời (lưu mã đơn vị) | P3 | Cần P2 |
| Tab **Liên quan**: câu mở đầu, bảng nhóm theo quan hệ, chip đếm, câu trích tạo quan hệ | P4 | |
| Dòng nhắc "Cần xem lại" (lan truyền một bước), "Hết hiệu lực một phần" | P4 | |
| Dòng thời gian "Lịch sử văn bản" | P4 | Danh sách dọc |
| "Gợi ý quan hệ" (hộp thư đến), nút mờ "chưa có trong kho", danh sách "Được nhắc tới nhưng chưa có" | P4 | Đã ghi ở lộ trình 4a |
| Nhãn "Đã sửa bởi ..." ở lề và hai bản cạnh nhau | P4 | Lộ trình 4b |
| "Nội dung tương tự (không phải quan hệ pháp lý)" | P4 | Lộ trình 4c |
| **Sơ đồ cục bộ:** bố cục Tầng, nút, cạnh, chú giải, thẻ chi tiết, bàn phím, danh sách thay thế | P4 | Đặc tả mục 6 |
| "Hỏi về văn bản này" từ nút sơ đồ; huy hiệu rủi ro trên nút; chế độ trong và ngoài dự án | **MỚI** (trên P4) | |
| **Bản đồ dự án** (bố cục Cụm có hạt giống, lớp rủi ro nối nhiều văn bản) | **MỚI** | Có tiêu chí bỏ |
| Xuất ảnh sơ đồ (PNG), xuất danh sách (CSV, Word) | P4/P5 | |
| Bộ chuyển dự án Alt+P | **MỚI** | Alt+N đã có ở P1 |

**Gợi ý xếp vào lộ trình (chưa ước lượng ngày):** phần "Dự án + ghi chú loại Rủi ro + tra rủi ro theo ghi chú + Sổ rủi ro" nhẹ vì chỉ thêm một bảng thành viên, hai cột và vài màn; nên xếp cùng P2 để khách thật thấy giá trị sớm (không cần AI, không cần quan hệ). Sơ đồ chờ P4. Cần lập lại kế hoạch P2 trước khi hứa ngày.

---

## 10. Ba cách bố cục đã cân nhắc

| | A. Bàn làm việc kiểu Obsidian | B. Ba vùng cố định kiểu NotebookLM | C. Khung P1 + trang dự án + ngăn trượt (**đề xuất**) |
|---|---|---|---|
| Ý chính | Cây dự án và văn bản bên trái, tab ở giữa (văn bản, sơ đồ, chat), bảng quan hệ bên phải. Sơ đồ là điểm xuất phát | Nguồn, Chat, Ghi chú luôn hiện cạnh nhau cho mỗi dự án | Giữ nguyên khung đã duyệt. Thêm bộ chuyển dự án, chip phạm vi, ngăn ghi chú, tab Liên quan |
| Điểm mạnh | Mạnh cho người ghi chú nhiều; giống thứ chị có thể từng thấy | Thấy rõ máy được phép đọc gì; mô hình dễ hiểu | Ít thay đổi nhất; đúng việc chính (từ khoá ra rủi ro); nhiều nhất hai vùng cùng lúc; một trạng thái chọn dùng chung cho sơ đồ, bảng, trích dẫn |
| Điểm yếu | Ba bốn ngăn trên màn nhỏ; tab chồng chất; đồ thị toàn cục là "áp phích"; không giúp việc chính; bỏ khung P1 vừa duyệt | Bốn vùng khi mở trình đọc, chật ở 1440; vùng ghi chú thường trống; đổi khung P1 | Nguồn của dự án không luôn hiện, ghi chú không luôn hiện; sơ đồ ít "ấn tượng" hơn |
| Cách bù | | | Chip "Dựa trên 14 văn bản" mở danh sách; dấu bút ở lề; nút "Ghi chú · 3"; thử với chị xem có cần hơn không |
| Kết luận | Bỏ: trái bằng chứng nghiên cứu và quá nặng cho người văn phòng | Bỏ: tốn chỗ, đổi khung đã duyệt | **Chọn** |

**Quyết định nhỏ đi kèm: sơ đồ đặt ở đâu.** Trong tab Liên quan của trình đọc (cục bộ) và trong công tắc ở trang Văn bản của dự án (bản đồ). Không có mục "Sơ đồ" riêng trên thanh bên: vì nhiều nghiên cứu nói nó thành màn "để xem" rồi không ai quay lại, và vì quan hệ luôn gắn với một văn bản đang mở.

---

## 11. Không làm (và vì sao)

1. **Đồ thị toàn kho kiểu "tấm áp phích", hoặc đồ thị làm màn đầu.** Không có thao tác nào đi tiếp từ nó; vị trí đổi mỗi lần mở.
2. **Mớ rối hình trang trí:** bố cục lực đẩy chạy mỗi lần mở, nút nhảy múa, nút kéo được, hoạt hoạ "phát lại theo thời gian". Tốn CPU máy 16 GB, phá trí nhớ không gian.
3. **Sơ đồ là cách duy nhất xem quan hệ.** Luôn có danh sách thay thế đầy đủ và bằng bàn phím.
4. **Màu là kênh duy nhất cho hiệu lực hay loại quan hệ.** Luôn hình, chữ, nét.
5. **Coi "chưa thấy gì" là "còn hiệu lực".** Offline chỉ biết kho của mình: "Chưa rõ", kèm dải cơ sở.
6. **Tự trích rủi ro, tự tạo quan hệ, tự gắn căn cứ.** Mọi thứ vào sổ hoặc thành cạnh đã xác nhận cần một lần bấm của người dùng.
7. **Câu trả lời dài như bài markdown.** Tóm tắt 2 đến 3 câu; bảng rủi ro 5 hàng rồi "Xem thêm"; không điểm số, không phần trăm, không ký hiệu markdown.
8. **Coi dẫn nguồn đúng là chứng minh nguồn ủng hộ.** Nhãn "Đã đối chiếu" chỉ nghĩa là đoạn có thật.
9. **Ghi chú của người dùng trông như luật.** Hình, nền, biểu tượng, chữ luôn khác.
10. **Phạm vi bị ẩn hoặc tự rộng ra.** Luôn nói "Dựa trên N văn bản", luôn nói "Không tìm thấy trong phạm vi này".
11. **Bộ nhớ dự án do máy tự tóm tắt, ẩn, không sửa được.** Chỉ có chữ bạn viết hoặc bạn bấm lưu.
12. **Sao chép văn bản vào từng dự án; "Gỡ khỏi dự án" nghe như xoá.** Tham chiếu, và câu xác nhận nói rõ.
13. **Quá nhiều tab, bốn ngăn cố định, hàng loạt nút điều khiển trên một trang.** Ba tab, một ngăn ghi chú, hai vùng cùng lúc.
14. **Từ kỹ thuật trên giao diện:** "node", "backlink", "graph", "tag", "hop". Dùng "văn bản liên quan", "Liên quan", "Sơ đồ", "thẻ", "Mở rộng thêm một bước".
15. **Bộ lọc kiểu truy vấn hoặc trình dựng nhóm màu.** Chỉ chip có số đếm và nút "Bỏ lọc".
16. **Làm giả quan hệ pháp lý bằng độ giống nội dung.** Cạnh "tương tự" mảnh, tắt mặc định, ghi rõ.
17. **Màu mới, gradient, mờ kính, bóng đổ nặng, biểu tượng trong ô màu, KPI kèm sparkline.** Giữ phong cách "sổ cái không màu" đã duyệt.

---

## 12. Cho bản bấm thử

**Tệp:** một tệp HTML, CSS và JS nhúng sẵn, không khung (framework), lấy token và thành phần từ `mau/giao-dien-1.0.html`; tệp mới, không sửa mẫu đã duyệt. Phông và kiểu như P1 (chỉ bản Artifact mới tải Be Vietnam Pro từ Google Fonts; app thật nhúng sẵn).

**Dữ liệu minh hoạ**, lấy lại `LAW`, `DOCS`, `ANS` của mẫu P1 (chữ luật là nguyên văn từ dữ liệu đo, **không soạn chữ luật mới**):

- **Ba dự án:** "Xe cơ giới và bảo hiểm" (NĐ 100/2019, NĐ 103/2008, NĐ 214/2013, NĐ 46/2016, NĐ 115/1997, TT 22/2016/BTC), "Xử phạt hành chính" (NĐ 100/2019, NĐ 38/2021, NĐ 142/2017, NĐ 391/2026, NĐ 389/2026), "Đầu tư và thủ tục 2026" (Luật 24/2026/QH16, NĐ 385/2026, TT 156/2026/TT-BTC). **NĐ 100/2019 nằm trong hai dự án** (để thấy nhiều–nhiều); TT 27/2026/TT-BNV và hai bản quét chưa thuộc dự án nào.
- **Quan hệ minh hoạ** (trung tâm tốt nhất để trình bày: **NĐ 103/2008**, vì đủ hết hiệu lực, sửa đổi, thay thế, hướng dẫn và nút mờ): NĐ 214/2013 sửa đổi NĐ 103/2008 (bằng chứng: trích yếu của NĐ 214/2013 có trong dữ liệu); NĐ 103/2008 thay thế NĐ 115/1997 (bạn xác nhận ở Điều 44 của NĐ 103/2008, như dữ liệu P1); NĐ 100/2019 thay NĐ 46/2016 (máy gợi ý ở Điều 84, chưa xác nhận: để có dấu "?"); NĐ 03/2021/NĐ-CP thay NĐ 103/2008 (**nút mờ**, chưa có trong kho); TT 22/2016/BTC hướng dẫn (tự phát hiện, chờ xác nhận); vài quan hệ căn cứ tới các Luật chưa có (nút mờ ở hàng Luật). **Các câu bằng chứng nào không có sẵn trong dữ liệu P1 thì ghi "(câu minh hoạ)"; đây là dữ liệu mẫu, không phải nhận định pháp lý.**
- Một nút trung tâm khác (NĐ 100/2019) có một **văn bản bị nhắc quá nhiều** (ví dụ một Luật nhiều nghị định dẫn) để thấy ẩn mặc định và "+N khác".
- **Năm hàng rủi ro** đủ trạng thái: có căn cứ, còn hiệu lực; có căn cứ nhưng văn bản đã hết hiệu lực; từ tệp, chưa gắn căn cứ (kèm gợi ý); đoạn đã thay đổi; cần xem lại. Chữ ghi của bạn do bản thử soạn, ngắn, ghi rõ là minh hoạ.

**Sáu đường bấm cần chạy được:**

1. **Toàn kho:** gõ "bảo hiểm xe" → nhóm "Bạn đã ghi (4)" đứng trên, rồi điều luật; rê `[n]` hiện hộp xem trước; bấm "Mở đúng đoạn" → trình đọc trượt ra đúng đoạn.
2. **Trình đọc NĐ 103/2008** → tab Liên quan: câu mở đầu, chip đếm lọc, danh sách → "Sơ đồ": rê, chọn, nút mờ NĐ 03/2021 → "Thêm tệp" (hộp thoại + thông báo), mở rộng thêm một bước, đổi chế độ lọc, đi bằng bàn phím.
3. **Chuyển sang dự án "Xe cơ giới"** → trang dự án: dòng "Cần chú ý" → "Sổ rủi ro" → mở một dòng → "Mở đúng đoạn".
4. **Trong dự án:** thêm chip `@NĐ 38/2021`, hỏi → "Không tìm thấy trong phạm vi này" → "Mở rộng ra Toàn kho". Một câu khác ra bản xem trước câu trả lời có bảng, dải kiểm hiệu lực, "Đã dùng: ghi chú".
5. **Trong trình đọc:** bôi chọn một đoạn → "Thêm vào sổ rủi ro" → lưu → hàng mới xuất hiện ở Sổ rủi ro (trạng thái trong bộ nhớ trang, không cần lưu lâu).
6. **Trang Văn bản của dự án** → "Sơ đồ" (bản đồ dự án, Cụm, có dải "Chưa nối với văn bản nào") → "Gỡ khỏi dự án" (hộp thoại với câu "Văn bản vẫn còn trong kho...").

**Trạng thái phải vẽ:** dự án trống, Sổ rủi ro trống, sơ đồ 0 / 2 / 12 / dày có gộp, nút mờ, lỗi dựng sơ đồ, đang tải, sáng và tối, bốn chiều rộng (1440, 1100, 768, 390).

**Công tắc rà soát:** góc trên có "Hiện nhãn giai đoạn", đặt chip nhỏ lên từng thành phần: **P2, P3, P4 viền nhẹ; MỚI nền đen chữ trắng; P1 không nhãn.** Có chú giải một dòng. Đây là công cụ cho chủ dự án, không phải một phần của sản phẩm.

**Kiểm trước khi giao** (theo phương pháp đã dùng cho mẫu P1): ảnh chụp bốn chiều rộng, sáng và tối; đi chỉ bằng bàn phím sáu đường trên; kiểm tương phản các token mới; không có mục nào dùng màu ngoài token.

**Không cần ở bản bấm thử:** tìm kiếm thật, lưu bền, gọi AI, bảng lệnh Ctrl+K (chỉ là phím tắt thêm, không phải con đường duy nhất; để sau), điều khiển "xem theo ngày" (tính lại mọi huy hiệu theo một ngày: nặng, để sau), dải chấm thời gian trong đầu trình đọc (đã có "Lịch sử văn bản" dạng danh sách).

---

## 13. Cách thử với chị

Ba việc ở mục 1.2, không hướng dẫn trước. Đo: làm được không cần chỉ (mục tiêu ≥ 90%, như cổng P1); chị **với tới sơ đồ hay bảng** trước; chị có hiểu "Bạn ghi" khác "Luật quy định" không (hỏi: "ô nào là luật?"); chị có hiểu "Chưa rõ" và "Theo kho của bạn" không. Ghi lại cả lúc chị không bấm vào sơ đồ: đó là kết quả, không phải thất bại. Một tuần sau: bản đồ dự án và sơ đồ cục bộ có được mở không (tiêu chí bỏ ở 6.13).

---

## 14. Còn mở (cần chủ dự án hoặc chị)

1. **File tóm tắt rủi ro của chị:** Word hay Excel, một dòng là một rủi ro không, có cột nào (mức độ, văn bản, Điều, ghi chú)? Cần một bản mẫu đã che thông tin để chốt chức năng nhập và các cột của Sổ rủi ro.
2. **Mặc định tầm của ghi chú khi viết trong một dự án:** "Chung" (đề xuất: an toàn, không mất thông tin) hay "Chỉ dự án này"? Bản thử để công tắc hai lựa chọn ngay trong hộp ghi chú.
3. **Chị có khoảng mấy dự án?** 3 hay 30 quyết định bộ chuyển chỉ cần danh sách ngắn hay phải có tìm và ghim (bản này làm sẵn cả hai).
4. **Bản đồ dự án:** vẽ trong bản thử để xem, quyết giữ hay bỏ sau một tuần (đề xuất ở 6.13).
5. **Xuất Excel của Sổ rủi ro:** ở P2 cùng sổ, hay để cùng xuất Word ở P5.

---

## 15. Chưa kiểm chứng, và rủi ro

- Chưa dựng thử gì: các tỉ lệ tương phản của token mới tính nhẩm; số nút theo bề rộng (khoảng 124px một nút, 12 và 25 nút) và điểm quan tâm là ước tính của tôi, chưa đo trên kho thật hay trên máy 16 GB.
- Nghiên cứu: nhiều chi tiết của Thư viện Pháp luật, Ravel, Harvey chỉ qua đoạn trích; không có bằng chứng người dùng văn phòng dùng sơ đồ, cũng như không có tiền lệ đã kiểm cho bộ nhớ riêng theo dự án khi văn bản dùng chung.
- Rủi ro lớn nhất: dựng quá nhiều một lúc (bản đồ dự án, nhập tệp rủi ro) khi chưa biết tệp thật của chị trông thế nào; và sơ đồ có thể hoá ra không được dùng. Vì thế "Sổ rủi ro + tra rủi ro theo ghi chú" là phần nên làm trước, sơ đồ làm sau và nhỏ.
