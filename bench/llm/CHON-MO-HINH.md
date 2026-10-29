# Chọn mô hình ngôn ngữ cho bản 1.0 (29/10/2026)

**Cách làm:** chỉ dùng bảng xếp hạng, thẻ mô hình, báo cáo kỹ thuật và issue/PR của llama.cpp, đọc tại nguồn ngày 29/10/2026. Số do hãng tự công bố ghi *(hãng)*; số của hai hãng khác nhau thường đo khác cách, khác chế độ, nên không so thẳng được. Số chỉ có trong ảnh biểu đồ coi là chưa kiểm. **Mọi số tốc độ trên máy chuẩn ở mục 4 là ước tính, chưa đo trên máy nào.**
**Ký hiệu:** R = bật chế độ suy nghĩ (thinking), NR = tắt. pp = tốc độ đọc prompt, tg = tốc độ sinh chữ (token/giây).
**Kết luận:** chọn **Qwen3-VL-4B-Instruct** (Q4_K_M), dự phòng **Gemma 4 E4B** (QAT Q4_0). Với ngân sách 45 s, mô hình 4B chỉ vừa nếu prompt khoảng 1.000 token hoặc máy chạy nhanh hơn ước tính trung tâm; phải đo (mục 5).
**Kiểm lại độc lập (29/10/2026):** các số SEA-HELM ở mục 3.2, bảng Vectara ở mục 3.1, thông số và GGUF của Qwen3-VL-4B-Instruct, llama.cpp #16780 và #30231 đã được đọc lại tại nguồn và khớp.

## 1. Câu hỏi và ràng buộc

Bản 1.0 cần một LLM mở trọng số, nhỏ, chỉ trả lời từ 3–5 đoạn đã tìm (~1.500 token tiếng Việt). Đầu ra là JSON theo schema qua `llama-server`: câu trả lời ≤ 3 câu, các ý kèm mã đoạn, lưu ý ngoại lệ/mâu thuẫn, tiền đề sai, cờ đủ căn cứ. App tự kiểm mọi con số và từ chối khi thiếu căn cứ (`soi-luat-lo-trinh-1.0.md` mục 4 và P3). Không có luật sư chấm tay, nên mô hình được chọn theo benchmark công khai. Máy: PC Windows 16 GB, không card rời; máy chuẩn Ryzen 5 5600GT (6 nhân/12 luồng Zen 3, AVX2, không AVX-512), DDR4-3200 hai kênh. Office và trình duyệt chiếm 5–7 GB, app 2,2 GB, nên LLM dùng tối đa ~4 GB RAM (trần cứng 6 GB). Chạy llama.cpp, GGUF, chỉ CPU. **Độ trễ: ≤ 45 giây p95 từ lúc bấm Enter tới khi xong câu trả lời** (chủ dự án nâng từ 30 s ngày 29/10/2026). Tìm kiếm mất 5–9 s, nên LLM còn ~35–40 s cho ~1.500 token vào và 150–250 token ra. Vì vậy câu trả lời mặc định phải tắt chế độ suy nghĩ.

## 2. Ứng viên

| Mô hình | Giấy phép | Ngày | Cỡ | Ngữ cảnh | GGUF Q4 | Ghi chú |
|---|---|---|---|---|---|---|
| **Qwen3-VL-4B-Instruct** (thêm) | Apache-2.0 ([thẻ](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct)) | repo tạo 11/10/2025 ([API HF](https://huggingface.co/api/models/Qwen/Qwen3-VL-4B-Instruct)); Qwen công bố 15/10/2025 ([README](https://github.com/QwenLM/Qwen3-VL)) | 4,44 tỉ kể cả phần ảnh; LM 36 lớp attention thường (GQA 32/8) | 256K | Q4_K_M 2,33 GiB, GGUF chính hãng ([repo](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct-GGUF), 31/10/2025) | Chỉ có chế độ không suy nghĩ. llama.cpp hỗ trợ từ 30/10/2025 ([#16780](https://github.com/ggml-org/llama.cpp/pull/16780)) |
| **Gemma 4 E4B** | Apache 2.0 ([thẻ](https://huggingface.co/google/gemma-4-E4B-it)) | repo tạo 02/03/2026; Google: 31/03/2026 ([trang releases](https://ai.google.dev/gemma/docs/releases)), blog 02/04/2026 ([blog](https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/)) | 4,5 tỉ hiệu dụng, 8 tỉ kể cả embedding theo lớp (PLE) | 128K | QAT Q4_0 chính hãng 4,8 GiB ([repo](https://huggingface.co/google/gemma-4-E4B-it-qat-q4_0-gguf), 01/05/2026) | Thẻ: dùng ngay 35+ ngôn ngữ, huấn luyện trên 140+; không nêu tên tiếng Việt |
| **Qwen3.5-4B** | Apache-2.0 ([thẻ](https://huggingface.co/Qwen/Qwen3.5-4B)) | repo tạo 27/02/2026; Qwen công bố 02/03/2026 ([README](https://github.com/QwenLM/Qwen3.5)) | 4,66 tỉ; lai 24 lớp Gated DeltaNet + 8 lớp attention | 262.144 | Q4_K_M 2,81 GiB ([bartowski](https://huggingface.co/bartowski/Qwen_Qwen3.5-4B-GGUF)) | Mặc định bật thinking |
| Qwen3.5-9B | Apache-2.0 | repo 27/02/2026; công bố 02/03/2026 | 9,65 tỉ | 262.144 | Q4_K_M 5,29–5,75 GiB | |
| Qwen3.5-2B | Apache-2.0 | repo 28/02/2026; công bố 02/03/2026 | 2,27 tỉ | 262.144 | Q4_K_M 1,30 GiB | Mặc định tắt thinking |
| Gemma 4 E2B | Apache 2.0 | như E4B | 2,3 tỉ hiệu dụng / 5,1 tỉ | 128K | QAT Q4_0 3,12 GiB ([repo](https://huggingface.co/google/gemma-4-E2B-it-qat-q4_0-gguf)) | |
| Gemma-SEA-LION-v4.5-E2B-IT (thêm) | MIT (trường `license` của [thẻ](https://huggingface.co/aisingapore/Gemma-SEA-LION-v4.5-E2B-IT); `license_link` lại trỏ giấy phép Gemma 4) | repo 18/05/2026 | 5,1 tỉ (gốc Gemma 4 E2B) | 128K | GGUF của AI Singapore (17/06/2026) | Tinh chỉnh cho 7 ngôn ngữ Đông Nam Á, có tiếng Việt |
| Qwen-SEA-LION-v4-4B-VL (thêm) | MIT ([thẻ](https://huggingface.co/aisingapore/Qwen-SEA-LION-v4-4B-VL)) | repo 21/11/2025 | 4,44 tỉ (gốc Qwen3-VL-4B) | 256K | | |
| Qwen3-4B-Instruct-2507 (thêm) | Apache-2.0 ([thẻ](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)) | repo 05/08/2025 | 4,02 tỉ, cùng cỡ LM với Qwen3-VL-4B | 262.144 | Q4_K_M 2,33 GiB | Không có trên SEA-HELM |
| Vi-Qwen2-7B-RAG | Apache-2.0 | repo 01/10/2024 | 7,62 tỉ (gốc Qwen2-7B-Instruct) | 8.192 (thẻ) | ~4,7 GB (ước tính) | Điểm trên thẻ chỉ ở dạng ảnh |
| Gemma 4 12B Unified | Apache 2.0 | repo 23/05/2026; Google công bố 03/06/2026 | 11,95 tỉ | 256K | Q4_0 7,65 GB ([báo cáo kỹ thuật](https://arxiv.org/abs/2607.02770), bảng 3) | **Loại:** vượt trần 6 GB |

Tra thêm ngày 29/10/2026 rồi loại:
- **Sailor2-8B-Chat:** Apache-2.0, repo 03/12/2024, 8,55 tỉ. Không có trên SEA-HELM hiện tại, nặng hơn 4B.
- **Qwen3-VL-8B-Instruct** (Apache-2.0, repo 11/10/2025) và **Qwen-SEA-LION-v4-8B-VL** (MIT, repo 21/11/2025): tiếng Việt NR cao hơn bản 4B (66,8 và 65,9 trên SEA-HELM), nhưng 8,77 tỉ tham số, Q4_K_M ~5 GB (ước tính) và chậm gần gấp đôi bản 4B, nên không vừa RAM và độ trễ.
- **Họ Qwen sau 3.5:** trong danh sách repo của Qwen trên Hugging Face không tìm thấy bản Qwen3.6/3.8 dùng chung nào ≤ 10B. Có Qwen3.8-27B (27,8 tỉ), Qwen3.8-Flash-Next (180 tỉ, giấy phép "other"), và Qwen-Drive-1.0-4B (bản dành cho lái xe, tinh chỉnh từ Qwen3.5-4B).
- **AITeamVN:** mô hình sinh mới nhất vẫn là GRPO-VI-Qwen2-* (04–05/2025), gốc Qwen2.

## 3. Benchmark

### 3.1 Bám ngữ cảnh, ảo giác (ưu tiên 1)

**Vectara Hallucination Leaderboard** ([README](https://github.com/vectara/hallucination-leaderboard), cập nhật 22/10/2026, giám khảo HHEM-2.3). Mô hình tóm tắt hơn 7.700 bài, chỉ được dùng thông tin trong bài; tỉ lệ ảo giác càng thấp càng tốt. **Không có** Qwen3.5-4B/9B, Gemma 4 E2B/E4B hay Qwen3-VL-4B trên bảng; dưới đây là các mô hình cùng họ.

| Mô hình | Ảo giác | Tỉ lệ chịu trả lời |
|---|---|---|
| qwen3-8b | 4,8% | 99,9% |
| gemma-4-26b-a4b-it | 5,2% | 99,8% |
| qwen3-4b | 5,7% | 99,9% |
| gemma-3-4b-it | 6,4% | 67,3% |
| gemma-4-31b-it | 7,4% | 100% |
| qwen3.5-35b-a3b | 10,5% | 99,8% |
| qwen3.5-27b | 12,1% | 99,8% |
| ministral-3-8b-2512 | 21,7% | 99,1% |
| Phi-4-mini-instruct | 23,5% | 92,5% |

- Ở mọi cỡ đã đo, họ Qwen3.5 có tỉ lệ ảo giác khoảng gấp đôi họ Qwen3 và Gemma 4. Bản 4B của Qwen3.5 chưa được đo.
- README không ghi các mô hình Qwen3.5 và Gemma 4 chạy có thinking hay không. HHEM hiện chỉ chấm tiếng Anh.

**RAG trên báo cáo ESG** ([arXiv 2609.15242](https://arxiv.org/abs/2609.15242), 14/09/2026). 100 câu hỏi tiếng Anh, mỗi câu 1 đoạn ngữ cảnh, chạy qua Ollama (4-bit, tham số mặc định), chấm RAGAS bằng chính qwen3:4b-instruct.

| Mô hình | Faithfulness (bám ngữ cảnh) | Factual correctness |
|---|---|---|
| gemma4:e4b | 0,796 | 0,405 |
| gemma4:e2b | 0,784 | 0,423 |
| qwen3:4b-instruct | 0,719 | 0,449 |
| ministral-3:8b | 0,607 | 0,405 |

- Bằng chứng yếu: mẫu nhỏ, giám khảo chỉ 4B, tiếng Anh. Nhưng đây là số đo bám ngữ cảnh trực tiếp duy nhất tìm được cho Gemma 4 E4B. Giám khảo cùng họ Qwen, nếu có thiên vị thì thiên về qwen3, vậy mà Gemma vẫn cao hơn.

**Nguồn khác:**
- **FACTS Grounding** ([Kaggle](https://www.kaggle.com/benchmarks/google/facts-grounding)): trang cần JavaScript, không đọc được. Tìm kiếm ngày 29/10/2026 không thấy điểm nào cho các ứng viên.
- **AA-Omniscience** của Artificial Analysis ([bài 05/03/2026](https://artificialanalysis.ai/articles/qwen3-5-small-models)): hỏi kiến thức **không kèm ngữ cảnh**, nên khác bài toán RAG. Tỉ lệ ảo giác: Qwen3.5-4B 80%, Qwen3.5-9B 82%, Qwen3-4B-2507 84%. [Trang AA của Gemma 4 E4B](https://artificialanalysis.ai/models/gemma-4-e4b) không có số này.
- **Bài MAM-AI** (Gemma 4 E4B trong RAG y tế, [arXiv 2606.29580](https://arxiv.org/abs/2606.29580)): tác giả đã rút cả ba phiên bản, nên không dùng.

### 3.2 Tiếng Việt (ưu tiên 2)

**SEA-HELM, phần tiếng Việt** ([bảng ≤ 10B, có cả bản không suy nghĩ](https://leaderboard.sea-lion.ai/detailed/vi?minSize=0&maxSize=10&showNonReasoningModels=true), AI Singapore, cập nhật 18/09/2026). Trang mặc định chỉ hiện bản có suy nghĩ của mỗi mô hình; các dòng NR dưới đây chỉ hiện khi bật "Non-reasoning variants" (tham số `showNonReasoningModels=true`). Chạy BF16 bằng vLLM với tham số mặc định của từng mô hình; prompt tiếng Việt zero-shot; 8 lần chạy; khoảng tin cậy 95% ([cách đo](https://leaderboard.sea-lion.ai/eval-details)). Bộ dữ liệu ([SEA-HELM](https://github.com/aisingapore/SEA-HELM/blob/main/docs/datasets_and_prompts.md)): **QA** là XQuAD tiếng Việt (trích câu trả lời từ đoạn văn cho sẵn, chấm F1); **NLI** là XNLI (suy ra / mâu thuẫn / trung lập); kiến thức là Global-MMLU-Lite; IF là SEA-IFEval; hội thoại là SEA-MTBench.

| Mô hình | Chế độ | VI tổng | QA trích từ đoạn | NLI | SEA-IFEval | Kiến thức | Hội thoại |
|---|---|---|---|---|---|---|---|
| **Qwen3-VL-4B-Instruct** | NR | 64,2 | 77,5 | 50,0 | 87,0 | 43,4 | 73,3 |
| Qwen-SEA-LION-v4-4B-VL | NR | 63,1 | 75,9 | 51,1 | 87,2 | 45,3 | 73,2 |
| **Gemma 4 E4B** | NR | 62,8 | 44,7 | 39,9 | 88,2 | 51,1 | 78,1 |
| Qwen3.5-9B | NR | 58,5 | 76,6 | 27,2 | 79,7 | 55,3 | 78,4 |
| Gemma-SEA-LION-v4.5-E2B | NR | 53,3 | 46,8 | 27,1 | 85,4 | 39,0 | 70,1 |
| **Qwen3.5-4B** | NR | 52,2 | 75,0 | 14,3 | 77,9 | 43,6 | 71,1 |
| Gemma 4 E2B | NR | 49,9 | 40,1 | 21,9 | 83,2 | 36,2 | 72,0 |
| Qwen3.5-9B | R | 71,9 | 80,0 | 54,4 | 92,2 | 76,6 | 84,0 |
| Qwen3.5-4B | R | 69,0 | 77,6 | 52,6 | 90,9 | 70,4 | 78,7 |
| Gemma 4 E4B | R | 67,1 | 55,0 | 55,1 | 85,1 | 66,5 | 82,0 |
| *Qwen3-VL-8B-Instruct (tham khảo, > 4 GB)* | NR | 66,8 | 82,6 | 47,8 | 86,5 | 55,0 | 80,0 |

Khoảng tin cậy: VI tổng ±1,5–2; QA ±5–6; NLI ±2–4; SEA-IFEval và kiến thức ±5.

- **Tắt thinking làm Qwen3.5-4B tụt mạnh:** VI tổng 69,0 → 52,2, NLI 52,6 → 14,3. Gemma 4 E4B chỉ tụt 67,1 → 62,8. Ở chế độ dùng được trong 45 s (NR), Qwen3.5-4B đứng cuối nhóm 4B.
- **QA trích từ đoạn văn gần với việc của app nhất.** Qwen3-VL-4B đạt 77,5 (CI 71–83), Gemma 4 E4B chỉ 44,7 (CI 39–50). Lý do Gemma thấp chưa rõ: F1 phạt câu trả lời dài hơn đáp án, nên có thể do Gemma viết dài hoặc diễn giải chứ không hẳn do hiểu sai.
- **NLI gần với việc chỉ ra tiền đề sai và mâu thuẫn:** Qwen3-VL-4B 50,0 (CI 46–54), Gemma 4 E4B 39,9 (CI 36–44).
- Gemma 4 E4B hơn ở kiến thức và hội thoại tiếng Việt, nhỉnh hơn ở làm theo chỉ dẫn. VI tổng của hai mô hình nằm trong khoảng tin cậy của nhau.
- Bản SEA-LION của Qwen3-VL-4B không hơn bản gốc (63,1 so với 64,2). Bản SEA-LION của E2B hơn bản gốc (53,3 so với 49,9).
- Không có trên SEA-HELM: Qwen3.5-2B, Qwen3-4B-Instruct-2507, Vi-Qwen2-7B-RAG, Sailor2.

**Nguồn tiếng Việt khác:**
- **VMLU** ([bảng](https://vmlu.ai/leaderboard), tra 29/10/2026): không có ứng viên nào. Qwen2-7B-Instruct, gốc của Vi-Qwen2-7B-RAG, chỉ đạt 28,85 (đánh giá 01/08/2024). Để so: Qwen2.5-7B-Instruct 57,51; gemma-2-9b-it 59,04.
- **Luật Việt Nam:** VLegal-Bench ([arXiv 2512.14554](https://arxiv.org/abs/2512.14554), bản 7 ngày 27/10/2026; 10.450 mẫu, có tác vụ RAG; [trang bảng](https://vilegalbench.cmcai.vn/)) chỉ chấm các mô hình cũ (Qwen2.5, Gemma 2, Llama 3.1, gpt-oss-20b…), không có ứng viên nào. VLSP 2025 có hai tác vụ luật (DRILL tìm văn bản, MLQA-TSR biển báo); không thấy kết quả cho ứng viên.
- **MMLU-ProX / INCLUDE:** các thẻ chỉ ghi trung bình nhiều ngôn ngữ, không có cột tiếng Việt. Qwen3.5-4B 71,5 / 71,0 *(hãng, thẻ không ghi chế độ)*. Qwen3-VL-4B-Instruct 59,4 / 61,4 *(hãng, NR, [báo cáo Qwen3-VL](https://arxiv.org/abs/2511.21631) bảng 6)*. Qwen3-4B-Instruct-2507 61,6 / 60,1 *(hãng, NR)*. Gemma 4 E4B chỉ có MMMLU 76,6 *(hãng, thinking)*.

**Số token cho tiếng Việt.** Đo trong phiên soạn ngày 29/10/2026 bằng `tokenizer.json` tải từ Hugging Face và thư viện `tokenizers` 0.23.3. Mẫu: 1.000 Điều của bộ [Zalo](https://huggingface.co/datasets/GreenNode/zalo-ai-legal-text-retrieval-vn) (255.695 âm tiết), cộng 84 câu hỏi và câu trích của `bench/van-ban-that`. Không tìm thấy số công bố nào khác.

| Tokenizer | Từ vựng | Token/âm tiết (Zalo) | Token/âm tiết (văn bản thật) | Token mỗi Điều: trung vị / TB / p90 |
|---|---|---|---|---|
| Qwen3, Qwen3-VL, Qwen2 (Vi-Qwen2) | 151.669 | 1,293 | 1,269 | 232 / 331 / 659 |
| Qwen3.5 | 248.070 | 1,204 | 1,177 | 214 / 308 / 613 |
| Gemma 4 | 262.144 | 1,251 | 1,203 | 223 / 320 / 636 |

- Chênh nhau tối đa 7%, không phải yếu tố quyết định.
- 1.500 token ≈ 1.160–1.250 âm tiết, tức khoảng 5 Điều cỡ trung vị. Điều dài (p90 ~650 token) làm prompt phình nhanh, nên prompt cần có trần.

### 3.3 Làm theo chỉ dẫn, đầu ra có khuôn (ưu tiên 3)

| Mô hình | IFEval *(hãng)* | IFBench *(hãng)* | IFBench, Artificial Analysis (R / NR) | SEA-IFEval tiếng Việt (R / NR) |
|---|---|---|---|---|
| Qwen3-VL-4B-Instruct | 82,3 (NR) [b] | – | – | – / 87,0 |
| Gemma 4 E4B | 96,7 (thinking) [c] | 44,0 (thinking) [c] | 44,2 / 40,5 | 85,1 / 88,2 |
| Qwen3.5-4B | 89,8 (thẻ không ghi chế độ) [a] | 59,2 [a] | 52,0 / 33,3 | 90,9 / 77,9 |
| Qwen3.5-9B | 91,5 [a] | 64,5 [a] | 66,7 / 37,8 | 92,2 / 79,7 |
| Qwen3.5-2B | 78,6 thinking / 61,2 NR [d] | 41,3 (thinking) [d] | – | – |
| Gemma 4 E2B | 94,6 (thinking) [c] | 38,0 (thinking) [c] | 38,0 / – | 86,8 / 83,2 |
| Qwen3-4B-Instruct-2507 | 83,4 (NR) [e] | – | – | – |

Nguồn: [a] [thẻ Qwen3.5-4B/9B](https://huggingface.co/Qwen/Qwen3.5-4B) (bảng so với các mô hình thinking); [b] [báo cáo Qwen3-VL](https://arxiv.org/abs/2511.21631), 27/11/2025, bảng 6; [c] [báo cáo Gemma 4](https://arxiv.org/abs/2607.02770), bản 2 ngày 24/07/2026, bảng 5 ("thinking trừ khi ghi khác"); [d] [thẻ Qwen3.5-2B](https://huggingface.co/Qwen/Qwen3.5-2B); [e] [thẻ Qwen3-4B-Instruct-2507](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507). IFBench độc lập lấy từ trang mô hình của [Artificial Analysis](https://artificialanalysis.ai/models/qwen3-5-4b-non-reasoning) (tra 29/10/2026). SEA-IFEval lấy từ bảng ở mục 3.2.

- Khi tắt thinking, IFBench độc lập: Gemma 4 E4B 40,5 > Qwen3.5-9B 37,8 > Qwen3.5-4B 33,3.
- Cú pháp JSON do `llama-server` bảo đảm bằng grammar sinh từ `json_schema` ([README server](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)). Không tìm thấy benchmark công khai nào đo việc tuân thủ JSON schema cho các mô hình này.

### 3.4 Suy luận (ưu tiên thấp)

| Mô hình | MMLU-Pro *(hãng)* | GPQA *(hãng)* | GPQA Diamond, Artificial Analysis (R / NR) |
|---|---|---|---|
| Qwen3-VL-4B-Instruct | 67,1 (NR) | 55,9 (NR) | – |
| Gemma 4 E4B | 69,4 (thinking) | 58,6 (Diamond, thinking) | 57,6 / 54,9 |
| Qwen3.5-4B | 79,1 | 76,2 (Diamond) | 77,1 / 71,2 |
| Qwen3.5-9B | 82,5 | 81,7 (Diamond) | 80,6 / 78,6 |
| Qwen3-4B-Instruct-2507 | 69,6 (NR) | 62,0 (NR) | – |
| Gemma 4 E2B | 60,0 (thinking) | 43,4 (thinking) | 43,3 / – |

Nguồn như mục 3.3. Qwen3.5 mạnh nhất về suy luận chung, kể cả khi tắt thinking. Đây là ưu tiên thấp và không bù được điểm tiếng Việt NR thấp ở mục 3.2.

### 3.5 Tốc độ CPU: số đo công khai

| Nguồn, ngày | Máy, luồng | Mô hình | pp | tg |
|---|---|---|---|---|
| [llama.cpp #30231](https://github.com/ggml-org/llama.cpp/issues/30231), 09/10/2026 | 8 luồng, bản **chỉ AVX2** (issue nêu máy Xeon 6985P-C cho phần đo từng hàm, không ghi riêng CPU của llama-bench) | Gemma 4 E4B Q8_0 | pp512 39,8–40,1 | tg128 9,2–9,3 |
| cùng nguồn | cùng máy, bản AVX-512 (5600GT không có) | Gemma 4 E4B Q8_0 | pp512 152–156 | tg128 10,4–10,8 |
| [llama.cpp #27851](https://github.com/ggml-org/llama.cpp/pull/27851), bình luận 28/08/2026, merge 26/09/2026 | 8 luồng, bản AVX2 (máy không ghi; bảng matmul của tác giả chạy trên Ryzen 9 9950X3D) | Qwen3.5-27B Q5_K | pp2048 14,98 → 25,36 (nhân tiled) | tg64 2,90 |
| [debian-ai](https://lists.debian.org/debian-ai/2025/01/msg00136.html), 27/01/2025 (bản llama.cpp cũ, build 3267) | Ryzen 9 5950X (16 nhân Zen 3), DDR4-3600, 16 luồng | llama 7B Q5_K_M | pp512 48,6 | tg128 9,7 |

- Tra ngày 29/10/2026, không tìm thấy số đo CPU x86 công khai nào cho Qwen3.5-4B/9B, Gemma 4 E4B ở Q4, hay Qwen3-VL-4B.
- **Đường Gated DeltaNet của Qwen3.5 trên CPU:** op `GATED_DELTA_NET` có bản CPU từ 07/03/2026 ([#19504](https://github.com/ggml-org/llama.cpp/pull/19504)) và đường chunked từ 11/03/2026 ([#20340](https://github.com/ggml-org/llama.cpp/pull/20340)). Việc được chia theo head cho nhiều luồng (`ggml/src/ggml-cpu/ops.cpp`, bản b11982). Tính từ cấu hình, phần hồi quy chỉ cỡ 0,05 GFLOP/token, so với ~7 GFLOP/token của các phép nhân ma trận, nên về lý thuyết không phải nút cổ chai. Chưa có số đo.
- **llama.cpp từ cuối 09/2026, trên CPU AVX2:** trọng số Q4_K và Q4_0 được sắp xếp lại khi nạp (`ggml-cpu/repack.cpp`); Q5_K và Q6_K dùng nhân ma trận theo khối (tiled), bật mặc định ([#27851](https://github.com/ggml-org/llama.cpp/pull/27851), biến `GGML_CPU_TILED_MM`). Bảng matmul AVX2 trong PR (Ryzen 9 9950X3D, 8 luồng, TFLOPS): Q4_K 1,03 thường / 1,27 sắp xếp lại / 1,43 tiled; Q5_K 0,68 thường / 1,41 tiled. Như vậy Q5_K_M không còn chậm hơn Q4_K_M ở phần đọc prompt, chỉ chậm hơn ở phần sinh chữ vì phải đọc nhiều byte hơn.
- **Dùng lại system prompt:** `llama-server` tạo checkpoint ở đầu tin nhắn user (`tools/server/server-context.cpp`, bản b11982). Nhờ vậy system prompt cố định được dùng lại cả với mô hình lai (Qwen3.5) và mô hình cửa sổ trượt (Gemma 4). Mô hình attention thường (Qwen3-VL-4B) dùng lại được sẵn.

## 4. Ước tính thời gian trả lời so với ngân sách 45 giây

**Tất cả là ước tính.** Giả định:
1. **Đọc prompt (pp) bị giới hạn bởi tính toán.** Hai số đo ở mục 3.5 (E4B Q8_0 bản AVX2; 5950X) cho ~38–40 GFLOPS hiệu dụng mỗi nhân, tức ~220 GFLOPS cho 6 nhân (bi quan). Nhân thêm ~1,4–1,5 lần nhờ sắp xếp lại/tiled (bảng matmul của #27851) được ~330 GFLOPS (trung tâm). Đầu lạc quan là ~510 GFLOPS, nếu một nhân Zen 3 bằng nửa nhân Zen 5 trong số đo Qwen3.5-27B. Với mô hình 7,3 GFLOP/token, ra **30 / 45 / 70 token/s** (bi quan / trung tâm / lạc quan). Q8_0 không có đường tiled, nên lấy 200–260 GFLOPS.
2. **Số phép tính mỗi token** bằng 2 × số tham số không tính embedding, tính từ `config.json`: Qwen3-VL-4B 7,3 GFLOP; Qwen3.5-4B 7,1; Gemma 4 E4B ~7,8; Qwen3.5-2B 2,7; Gemma 4 E2B ~3,0; Qwen2-7B 13,1; Qwen3.5-9B ~16,4.
3. **Sinh chữ (tg) bị giới hạn bởi băng thông RAM.** DDR4-3200 hai kênh có 51,2 GB/s lý thuyết. Lấy 34–42 GB/s hiệu dụng: 5950X đạt ~87% (4,78 GiB × 9,73 t/s ≈ 50 GB/s trên 57,6 GB/s), trừ thêm phần iGPU của 5600GT và Office. tg = 0,9 × băng thông / số byte trọng số đọc mỗi token. Gemma 4 E4B tính ~2,8 GB/token, không tính bảng PLE vì mỗi token chỉ đọc một hàng. **Máy chỉ cắm một thanh RAM thì tg giảm gần một nửa.**
4. **Mỗi câu hỏi:** 1.500 token prompt mới (system prompt đã cache), 200 token ra, tìm kiếm 5 s. Kịch bản p95 bi quan: tốc độ thấp nhất, 250 token ra, tìm kiếm 9 s. Chạy 6 luồng; Office mở nhưng không chạy nặng.

| Mô hình | RAM của LLM | pp (t/s): khoảng; trung tâm | tg (t/s) | Tổng trung tâm | Tổng p95 bi quan | Tổng lạc quan | Prompt tối đa để tổng trung tâm ≤ 45 s |
|---|---|---|---|---|---|---|---|
| **Qwen3-VL-4B Q4_K_M** | ~3,2–3,5 GB | 30–70; 45 | 12–15 | 53 s | 79 s | 36 s | ~1.150 token |
| Qwen3-VL-4B Q5_K_M (~2,7 GiB, suy từ bản Qwen3-4B cùng cỡ) | ~3,5–3,8 GB | 30–70; 45 | 11–13 | 55 s | 83 s | 38 s | ~1.050 |
| Qwen3-VL-4B Q8_0 (3,99 GiB) | ~5 GB | 27–36; 32 | 7–9 | 78 s | 99 s | 64 s | ~470 |
| **Gemma 4 E4B QAT Q4_0** | ~3,4 GB nếu giữ mmap; ~5,6 GB nếu tắt mmap | 28–66; 42 | 11–13,5 | 57 s | 85 s | 39 s | ~1.000 |
| **Qwen3.5-4B Q4_K_M** | ~3,6 GB | 31–72; 46 | 10–12,5 | 55 s | 82 s | 38 s | ~1.030 |
| Qwen3.5-2B Q4_K_M | ~1,9 GB | 81–189; 122 | 22–27 | 26 s | 39 s | 19 s | ~3.900 |
| Gemma 4 E2B / SEA-LION E2B Q4_0 | ~2 GB nếu giữ mmap | 73–170; 110 | 20–25 | 27 s | 42 s | 20 s | ~3.400 |
| Vi-Qwen2-7B-RAG Q4_K_M | ~5,3 GB | 17–39; 25 | 6,5–8 | 92 s | 137 s | 62 s | ~320 |
| Qwen3.5-9B Q4_K_M (5,29 GiB) | ~6,3 GB, vượt trần | 13–31; 20 | 5,4–6,7 | 113 s | 168 s | 76 s | ~140 |

RAM gồm trọng số, KV f16 cho ngữ cảnh 2.048–4.096 token và bộ đệm tính toán ~0,3–0,5 GB. KV của Qwen3-VL-4B ~144 KiB/token; của Qwen3.5-4B ~32 KiB/token cộng ~50 MB trạng thái hồi quy. Bật thinking thêm hàng trăm tới hàng nghìn token ở 10–14 t/s, nên không mô hình nào vừa 45 s khi bật.

**Đọc kết quả:**
- **Với 45 s, không mô hình 4B nào chắc chắn vừa khi prompt dài 1.500 token.** Ước tính trung tâm là 53–57 s. Mô hình 4B chỉ vừa nếu tốc độ thật nằm ở nửa trên khoảng ước tính: pp ≥ ~60 t/s để vừa ở mức trung tâm, ≥ ~85–90 t/s để vừa ở p95 (với tg ~13 t/s).
- **Cắt prompt còn ~1.000 token thì vừa ở tốc độ trung tâm** (~42–45 s). Để p95 cũng ≤ 45 s, pp phải ≥ ~60 t/s. Kế hoạch P3 hiện đặt ngân sách 1.500–2.000 token, cao hơn mức này.
- **45 s không mở đường cho mô hình lớn hơn.** Mô hình 7B/9B tốn gấp 1,8–2,2 lần phép tính (tổng trung tâm 92–113 s), và 9B Q4_K_M đã vượt trần 6 GB.
- **Q8_0 không vừa:** sinh chữ chậm gần gấp đôi, và Q8_0 không có đường tiled.
- **Q5_K_M:** đọc prompt không chậm hơn (tiled), sinh chữ chậm ~15% (thêm 2–3 s cho 200 token), RAM thêm ~0,4 GB. Chỉ đáng thử nếu đo thấy còn dư ≥ 5 s. Với Gemma, bản QAT Q4_0 được Google huấn luyện để giữ chất lượng khi lượng tử, nên không cần Q5/Q8.
- **Mô hình 2B vừa 45 s** kể cả ở kịch bản bi quan (39–42 s), nhưng tiếng Việt kém rõ (mục 3.2).
- **So với ngân sách 30 s cũ:** khi đó mô hình 4B chỉ chứa được ~450–650 token prompt ở tốc độ trung tâm. Ngân sách 45 s nới lên ~1.000–1.150 token.
- **Cách giảm thời gian:**
  - Đặt trần prompt ~1.000 token: chỉ giữ khoản khớp và khoản liền kề; dùng 3 đoạn thay vì 5 khi các Điều dài.
  - Đặt `n_predict` ≤ 200 và dùng khoá JSON ngắn.
  - Gửi một câu hỏi mồi lúc mở app để system prompt nằm sẵn trong cache.
  - Chạy 6 luồng; thử `-tb 12` cho phần đọc prompt.
  - Gemma 4 E4B và Qwen3.5 có đầu dự đoán nhiều token (MTP) cho speculative decoding, có thể tăng tg; chưa có số đo trên CPU.

## 5. Khuyến nghị

**1. Chính: Qwen3-VL-4B-Instruct**, GGUF Q4_K_M chính hãng Qwen (2,33 GiB). Chạy như mô hình chữ, không cần file `mmproj`. Trần prompt ~1.000 token, ≤ 200 token ra, 6 luồng.

Lý do:
- Ở chế độ không suy nghĩ, đây là mô hình ≤ 5B cao nhất trên SEA-HELM tiếng Việt (64,2).
- Hai tác vụ gần với việc của app nhất là QA trích từ đoạn văn ("chỉ trả lời từ đoạn văn") và NLI ("chỉ ra tiền đề sai, mâu thuẫn"). Ở QA, mô hình này cao nhất nhóm ≤ 5B (77,5); ở NLI, chỉ sau bản SEA-LION của chính nó (50,0 so với 51,1). Cả hai đều hơn hẳn Gemma 4 E4B (44,7 và 39,9).
- Bản Instruct chỉ có chế độ không suy nghĩ, nên điểm SEA-HELM đo đúng chế độ app sẽ chạy.
- File nhỏ nhất nhóm 4B: sinh chữ nhanh nhất, RAM ~3,2 GB. Kiến trúc attention thường: llama.cpp hỗ trợ từ 10/2025, cache prompt đơn giản.
- Họ Qwen3 có tỉ lệ ảo giác HHEM thấp (Qwen3-4B 5,7%, Qwen3-8B 4,8%), khác hẳn họ Qwen3.5 (10,5–12,1%).
- Apache-2.0; ngữ cảnh 256K, thừa cho 1.000–1.500 token.

Rủi ro:
- Chưa có số bám ngữ cảnh đo trực tiếp cho đúng mô hình này. Trong bài ESG, bản chữ cùng họ (qwen3:4b-instruct) có faithfulness 0,719, thấp hơn Gemma 4 E4B (0,796).
- Kiến thức tiếng Việt thấp (43,4). Chấp nhận được vì app chỉ cho trả lời từ đoạn đưa vào. Nhưng khi ngữ cảnh thiếu căn cứ, mô hình có thể điền bằng kiến thức sai; cờ `du_can_cu` và bộ kiểm số liệu phải chặn được trường hợp này.
- Mô hình Qwen đôi khi chèn chữ Trung hoặc Anh; kiểm tự động được.
- Ra 10/2025, cũ hơn Gemma 4 và Qwen3.5.
- Chưa chắc đạt p95 ≤ 45 s (mục 4).

**2. Dự phòng: Gemma 4 E4B**, GGUF QAT Q4_0 chính hãng Google, tắt thinking. Dùng khi Qwen3-VL-4B trượt các phép kiểm chất lượng tự động ở dưới. Không dùng để chữa chậm: Gemma 4 E4B không nhanh hơn.

Lý do:
- Có số bám ngữ cảnh đo trực tiếp duy nhất, và số đó tốt: faithfulness 0,796 trong bài ESG, cao thứ hai trong 7 mô hình.
- Họ Gemma 4 có tỉ lệ ảo giác HHEM 5,2–7,4%.
- Tiếng Việt NR 62,8, ngang Qwen3-VL-4B trong khoảng tin cậy. Làm theo chỉ dẫn và hội thoại tiếng Việt tốt nhất nhóm NR ≤ 5B.
- IFBench độc lập khi tắt thinking 40,5, cao nhất trong các mô hình nhỏ Artificial Analysis đã đo.
- Bản QAT Q4_0 do Google huấn luyện để giữ chất lượng khi lượng tử. Mới hơn Qwen3-VL-4B (04/2026 so với 10/2025).

Rủi ro:
- QA trích từ đoạn văn tiếng Việt chỉ 44,7 (CI 39–50); NLI 39,9.
- File 4,8 GiB vì bảng embedding theo lớp. Phải giữ mmap để RAM làm việc ~3,4 GB; tắt mmap thì ~5,6 GB, sát trần.
- Thẻ không nêu tiếng Việt trong 35+ ngôn ngữ dùng ngay.
- llama.cpp mới hỗ trợ Gemma 4 từ 04/2026 và vẫn còn sửa lỗi Gemma 4 tới 10/2026.

**Không chọn:**
- **Qwen3.5-4B**, đề xuất hiện tại của lộ trình mục 4. Khi tắt thinking: tiếng Việt 52,2 (thấp nhất nhóm 4B), NLI 14,3, IFBench độc lập 33,3. Họ Qwen3.5 có tỉ lệ ảo giác HHEM gấp đôi Qwen3 và Gemma 4. Bật thinking thì mạnh (69,0) nhưng không vừa 45 s trên CPU. Chỉ hợp với chế độ "Phân tích kỹ" do người dùng chủ động bấm, ước tính 1,5–3 phút.
- **Qwen3.5-9B, Vi-Qwen2-7B-RAG:** quá chậm (tổng trung tâm 92–113 s, ước tính); 9B còn vượt trần 6 GB. Vi-Qwen2 thêm ba điểm yếu: gốc Qwen2 (VMLU 28,85), ngữ cảnh 8.192, điểm benchmark chỉ ở dạng ảnh.
- **Gemma 4 12B:** bản Q4_0 nặng 7,65 GB.
- **Mô hình 2B** (Gemma-SEA-LION-v4.5-E2B, Gemma 4 E2B, Qwen3.5-2B): vừa 45 s nhưng yếu. Hai bản E2B có tiếng Việt NR ≤ 53,3 và QA trích đoạn ≤ 46,8; Qwen3.5-2B không có trên SEA-HELM và IFEval NR chỉ 61,2 *(hãng)*. Chỉ cân nhắc khi đo thấy không mô hình 4B nào đạt 45 s p95 dù đã cắt prompt và chủ dự án chấp nhận chất lượng thấp hơn; cách còn lại là nới ngân sách. Nếu phải dùng 2B, Gemma-SEA-LION-v4.5-E2B có điểm tiếng Việt cao nhất nhóm (53,3 NR).

**Cần đo trên máy 16 GB để chốt (không cần luật sư):**
1. **Tốc độ.** Chạy `llama-bench -m <gguf> -t 6 -p 1000,1500 -n 200 -r 5` cho hai mô hình, với Office và trình duyệt đang mở. Dùng đúng bản llama.cpp sẽ đóng gói (≥ b11982); thử thêm `-tb 12`. Từ số đo, tính trần prompt cho p95: số token prompt tối đa = pp × (36 − 250/tg). Ví dụ tg = 13 t/s: prompt 1.500 token cần pp ≥ ~89 t/s, prompt 1.000 token cần ≥ ~60 t/s. Ở mức trung tâm (tìm 5 s, ra 200 token), con số tương ứng là ~61 và ~41 t/s.
2. **Độ trễ đầu-cuối.** Đo p50/p95 trên ≥ 100 câu thật qua `llama-server` với JSON schema, `cache_prompt` bật, có câu hỏi mồi lúc mở app.
3. **RAM.** Đo Working set và Private bytes của `llama-server` bằng Process Explorer, để mmap mặc định. Mục tiêu ≤ 4 GB, trần 6 GB.
4. **Chất lượng tự động** (vòng 1 của P0), cho cả hai mô hình trên cùng ngữ cảnh:
   - JSON hợp lệ;
   - `nguon` chỉ gồm mã đã đưa vào;
   - mọi con số khớp nguyên văn đoạn được dẫn;
   - từ chối đúng (`du_can_cu = false`) khi đã bỏ đoạn chứa đáp án khỏi ngữ cảnh;
   - câu bẫy tiền đề sai do script sinh (đổi con số trong câu hỏi so với văn bản): `tien_de_sai` phải khác rỗng;
   - câu trả lời bằng tiếng Việt, ≤ 3 câu, không có ký tự CJK.

   Trong các mô hình đạt độ trễ, chọn mô hình có tỉ lệ số khớp và từ chối đúng cao hơn.
5. **RAM hai kênh.** Kiểm máy chạy RAM hai kênh; một kênh thì tg giảm gần một nửa.

## 6. Chưa kiểm được

- **Bám ngữ cảnh:** không tìm thấy điểm nào cho đúng các ứng viên. Vectara không có các bản nhỏ; trang FACTS Grounding không đọc được; tìm kiếm ngày 29/10/2026 không ra.
- **Bài ESG:** tag Ollama `qwen3:4b-instruct` được hiểu là Qwen3-4B-Instruct-2507, nhưng bài không ghi rõ. Giám khảo là chính mô hình đó; bài tiếng Anh, 100 câu.
- **Tiếng Việt:**
  - không có kết quả benchmark luật Việt Nam nào cho ứng viên; VMLU không có ứng viên nào;
  - không có điểm tiếng Việt riêng cho MMLU-ProX/INCLUDE/Global-MMLU, ngoài Global-MMLU-Lite trong SEA-HELM;
  - chưa rõ Gemma 4 E4B thấp ở QA tiếng Việt vì viết dài hay vì hiểu sai.
- **Chế độ chạy của các bảng:** thẻ Qwen3.5-4B/9B không ghi bảng điểm đo ở chế độ nào; README Vectara không ghi Qwen3.5 và Gemma 4 có bật thinking không.
- **Tốc độ:**
  - mọi số tốc độ ở mục 4 là ước tính; không có số đo công khai trên CPU x86 cho các ứng viên ở Q4;
  - chưa chạy được `llama-bench` trong môi trường soạn;
  - chưa đo: hiệu năng thực của đường Gated DeltaNet trên CPU, RAM làm việc của Gemma 4 E4B khi giữ mmap, lợi ích của MTP trên CPU, chi phí grammar JSON với từ vựng 248–262 nghìn token.
- **Vi-Qwen2-7B-RAG:** điểm benchmark chỉ có trong ảnh biểu đồ, coi như chưa kiểm.
- **AA-Omniscience:** số của Qwen3.5 chỉ có trong bài 05/03/2026; trang mô hình hiện tại không hiện số này; Gemma 4 E4B không có số.
- **Ngày phát hành Gemma 4 E2B/E4B:** có ba mốc khác nhau: repo Hugging Face 02/03/2026, trang releases của Google 31/03/2026, blog Google 02/04/2026.
- **Mô hình khác:** giấy phép của Ministral 3 và Phi-4-mini chưa tra, vì hai mô hình này chỉ xuất hiện để tham khảo trong bảng HHEM, không phải ứng viên.
