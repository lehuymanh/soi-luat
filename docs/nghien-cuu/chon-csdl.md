# Chọn cơ sở dữ liệu cho phần truy hồi (RAG) bản 1.0 (29/10/2026)

**Cách làm:** đọc tại nguồn ngày 29/10/2026: tài liệu chính thức, README/LICENSE/mã nguồn trên GitHub, trang PyPI (phiên bản, ngày phát hành, wheel Windows). Số do hãng tự công bố ghi *(hãng)*. Tìm không thấy thì ghi "không thấy trong tài liệu (29/10/2026)", không suy ra "không hỗ trợ". Phần vector đo trong sandbox trên dữ liệu tổng hợp (mục 5). **Sandbox không phải máy chuẩn**, số đo chỉ dùng để so tương đối. Thời gian dựng đồ thị tri thức bằng LLM (mục 4.5) là **ước tính** từ tốc độ ước tính trong `chon-mo-hinh.md`, chưa đo.
**Ký hiệu:** 61K = 61.425 vector (một vector cho mỗi Điều, như hiện nay); 250K = 250.000 vector (nếu nhúng theo khoản); MB = 2^20 byte; p50 = trung vị.
**Kiểm lại độc lập (29/10/2026):** Kùzu archived 10/10/2025; GraphRAG "largely in maintenance mode"; LightRAG ghi Qwen3-30B-A3B là mức tối thiểu khi chạy cục bộ; Graphiti cần Neo4j 5.26/FalkorDB/Neptune ("Kuzu is deprecated"); ngày phát hành sqlite-vec 0.1.6–0.1.10a4; USearch 2.26.6 (Apache-2.0, wheel cp311 `win_amd64` 344.881 byte); charabia bỏ dấu (nonspacing marks) với chữ Latin; Search API của Chroma chỉ có trên Cloud. Đã đọc lại tại nguồn và khớp.
**Kết luận (lộ trình mục 4b ghi lại):** giữ **SQLite (WAL) + FTS5** làm kho duy nhất. Vector giữ cách tìm vét cạn (brute-force) trong RAM như hiện nay. Khi ma trận float32 vượt ~500 MB (≈ 125K vector) hoặc RAM chạm ngưỡng ở mục 6.2, thêm **USearch** (Apache-2.0, wheel Windows 0,8 MB) để tìm chính xác trên float16, rồi int8 + chấm lại khi vượt ~250K. Chỉ mục HNSW chỉ cần khi độ trễ vượt ngưỡng; ngoại suy từ số sandbox, i8 với 4 luồng vẫn dưới ~150 ms tới khoảng 1 triệu vector. Quan hệ văn bản (P4) để trong bảng SQLite, đi đồ thị bằng CTE đệ quy, mượn mô hình thời gian hai trục của Graphiti. **Không dùng** framework đồ thị tri thức dựng bằng LLM (Cognee, Graphiti, LightRAG, GraphRAG…). Ước tính dựng cho 61K Điều trên máy chuẩn mất 10–33 ngày CPU chạy liên tục; riêng Graphiti mất 6–12 tháng. Đổi CSDL không làm câu trả lời đúng hơn: độ chính xác nằm ở thuật toán (mục 2.3), còn phần phụ thuộc CSDL chỉ chiếm ≤ ~1 s trong ~9 s của Advance.

## 1. Câu hỏi và ràng buộc

Bản 1.0 cần đưa 3–5 đoạn luật đúng nhất cho Qwen3-VL-4B (llama.cpp, prompt ~1.000 token; `chon-mo-hinh.md` mục 5). Câu hỏi: dùng CSDL hay bộ máy truy hồi mã nguồn mở nào cho phần đó, và có nên thêm kho vector, kho đồ thị, hay một framework "bộ nhớ AI" kiểu Cognee/Graphiti không.

| Ràng buộc | Giá trị (nguồn) |
|---|---|
| Giấy phép | OSI. Đánh dấu copyleft (GPL/AGPL) và giấy phép không phải OSI (SSPL, BSL) |
| Nền | Windows 10/11 chạy thẳng: không Docker, không WSL, không quyền admin. PyInstaller onedir, một bộ cài, một người dùng, offline hoàn toàn |
| Máy | 16 GB RAM, không card rời, dùng chung với Office và trình duyệt. App tối đa ~6 GB, trong đó LLM ~3,2–3,5 GB (`chon-mo-hinh.md` mục 4), nên phần truy hồi ≤ ~2–2,5 GB. Hiện Advance đo được đỉnh ~2,2 GB (`docs/nghien-cuu/so-thu-nghiem.md` TK-07) |
| Độ trễ | ≤ 45 s từ Enter tới khi xong câu trả lời. Phần tìm ~5–9 s (lộ trình mục 2, điều 4); phần CSDL nên dưới 1 s |
| Độ chính xác | Câu có dấu và không dấu, khớp cụm và khớp gần (phrase/NEAR), đồng nghĩa, hợp BM25 + vector + reranker, lọc theo văn bản/loại/cơ quan/hiệu lực/tag |
| Ghi | Giao dịch trong khi luồng nền nạp file và nhúng vector (`jobs.py`) |
| Tăng trưởng | 250K–500K vector nếu nhúng Điều dài theo từng khoản (lộ trình, nhánh chính xác, mục 2) |

## 2. Hiện trạng

### 2.1 Kho SQLite đang làm gì

| Phần | Ở đâu | Đang làm |
|---|---|---|
| Kết nối | `src/soiluat/db.py` `connect` | Một file `soiluat.db`, WAL, `busy_timeout=5000`, khoá ngoại bật. Mỗi request mở kết nối riêng (`app.get_conn`); luồng nền `jobs.py` cũng có kết nối riêng để nạp file và nhúng vector |
| Full-text | `schema.sql` `units_fts` | FTS5 external content trên `units`, đồng bộ bằng trigger. 5 cột: `title_search`, `search_accent` (có dấu), `search_text` (không dấu), `context_search`, `context_accent`. Tokenizer `unicode61 remove_diacritics 0`; việc bỏ dấu do `fold.py` làm, ghi sẵn vào cột không dấu. `units_vocab` (fts5vocab) dùng để đếm số đơn vị chứa mỗi từ |
| BM25 nhiều tầng | `search.py` `scored_units`, `_run_cascade` | Một truy vấn OR lấy 300 ứng viên với `bm25(units_fts, 1, 1, 1, 0.5, 0.5)`; lọc `doc_ids` bằng `IN`, nhãn bằng truy vấn con trên `unit_labels`, `only_ids` bằng `json_each`. Sau đó chấm tầng bằng Python trên chữ ứng viên (cụm 2,0; gần 1,5; đủ từ/đồng nghĩa 1,3; một phần 1,0) và cộng điểm cặp âm tiết. Có nhánh có dấu, nhánh không dấu, nhánh trang OCR |
| Vector | `semantic.py` `_all_vectors`, `rerank` | Vector float16 trong bảng `unit_vectors`, nạp thành ma trận float32 trong RAM (61K × 1024 ≈ 252 MB). Mỗi câu: nhân ma trận × vector, `argsort` toàn bộ, lọc `doc_ids` bằng `np.isin`; hợp RRF BM25 top-20 với vector top-50 (k = 5, w = 2); Điều chỉ có nhờ vector phải đạt cosine ≥ 0,40. Mỗi câu còn chạy `COUNT(*), MAX(unit_id)` để kiểm cache |
| Reranker | `crossrank.py` | Cross-encoder top-5, 384 token, 2 luồng. Không dùng CSDL ngoài việc lấy chữ Điều |
| Bảng kiểu đồ thị | `links`, `effect_hints`, `unit_labels` | Liên kết chế tài ↔ nghĩa vụ, gợi ý thay thế. Bản 1.0 thêm `conversations`, `messages`, `doc_tags`, `user_notes` (+ FTS), `doc_relations`, tất cả là bảng SQLite (lộ trình mục 7) |

### 2.2 Thời gian của một câu Advance nằm ở đâu

| Bước | Thời gian (máy chuẩn, 2 luồng) | Nguồn | Phụ thuộc CSDL? |
|---|---|---|---|
| BM25 nhiều tầng + dựng thẻ (= cả chế độ Normal) | ~1 s; p50 975 ms trên kho 427K đơn vị | `docs/kien-truc.md` mục 5.2 của bản trước `6f39851` (`git show 6f39851^:docs/kien-truc.md`); `bench/zalo/KET-QUA.md` (22/10/2026) | Có: truy vấn FTS5 (riêng truy vấn BM25 OR p50 ~400–480 ms) và các SQL lấy chữ |
| Nhúng câu hỏi (AITeamVN, int8) | chưa đo riêng; EmbeddingGemma 300M từng đo +213 ms | `bench/zalo/KET-QUA.md` | Không |
| Tìm vector toàn kho | ~5 ms nhân ma trận + ~7 ms kiểm cache (61K × 256 chiều, đo 23/10/2026). Ở 1024 chiều: 19 ms (1 luồng) / 3,8 ms (4 luồng) trong sandbox (mục 5) | `bench/zalo/KET-QUA.md`; mục 5 | Không (RAM) |
| Reranker top-5 | ~5 s | `docs/kien-truc.md` mục 5.2 của bản trước `6f39851` (`git show 6f39851^:docs/kien-truc.md`) | Không |
| Phần còn lại (dựng thẻ cho tới 50 Điều thêm từ vector, dựng chữ cho reranker…) | ~2–3 s, chưa tách được | suy từ tổng ~9 s | Một phần |
| **Tổng Advance** | p50 8,6 s, p95 9,6 s | `docs/nghien-cuu/so-thu-nghiem.md` TK-07 | |

Phần phụ thuộc CSDL tối đa khoảng 1 s trong ~9 s. Phần lớn là reranker (~5 s), và lộ trình đã có việc riêng cho nó (nhánh chính xác, mục 3: chạy 4–6 luồng). Đổi CSDL chỉ có thể bớt một phần của ~1 s đó.

### 2.3 Đổi CSDL có làm câu trả lời đúng hơn không?

Không, nếu thuật toán giữ nguyên. Độ chính xác hiện tại (Advance Hit@1 79,3%, Hit@5 92,3%; `docs/nghien-cuu/so-thu-nghiem.md` TK-07) đến từ những phần không phụ thuộc CSDL: hai cột có dấu/không dấu, các tầng khớp và hệ số đã chỉnh trên `bm25()` của FTS5, từ điển đồng nghĩa, mô hình nhúng và `MAXLEN`, tham số RRF, reranker.
- FTS5 đã có mọi tính năng mà các tầng đó cần: BM25 có trọng số cột, phrase, `NEAR`, tokenizer tự viết qua C API, `remove_diacritics` 0/1/2 ([FTS5](https://sqlite.org/fts5.html)).
- Chỉ mục ANN (HNSW, IVF…) chỉ có thể mất recall so với tìm vét cạn, vì hiện app đã tìm chính xác.
- Bộ máy luôn bỏ dấu sẽ làm kết quả kém đi. Repo đã đo: BM25 trên cột không dấu đạt Hit@10 77,7%, trên cột có dấu 84,9% (`bench/zalo/KET-QUA.md`, 22/10/2026). Tokenizer của Meilisearch bỏ dấu với mọi chữ Latin (mục 4.1).
- Chuyển sang bộ máy khác thì phải chỉnh lại BM25 và các hệ số, rồi qua lại cổng "tốt hơn trên cả Zalo và gold" (lộ trình mục 5, điều 7). Không có ứng viên nào mang tới tính năng truy hồi mà FTS5 + NumPy chưa có.

Cách duy nhất CSDL ảnh hưởng tới độ chính xác là gián tiếp: nhúng theo khoản (đã đề xuất trong lộ trình) làm số vector tăng 4–8 lần, và phần vector phải chịu được. Mục 5–6 xử lý việc này mà không cần đổi CSDL.

## 3. Tiêu chí

| # | Tiêu chí | Loại | Cách xét |
|---|---|---|---|
| 1 | Giấy phép OSI, không copyleft nằm trong tiến trình app | bắt buộc | LICENSE trong repo, trường license trên PyPI |
| 2 | Windows chạy thẳng: wheel `win_amd64` cho Python 3.11 hoặc file exe; không Docker/WSL/admin | bắt buộc | Danh sách file trên PyPI, asset của bản phát hành, tài liệu cài đặt |
| 3 | Offline: không tải extension hay mô hình lúc chạy | bắt buộc | Tài liệu |
| 4 | RAM phần truy hồi ≤ ~2–2,5 GB kể cả hai mô hình; phần CSDL < 1 s | bắt buộc | Mục 5, số đã đo trong repo |
| 5 | Tiếng Việt: giữ được nhánh có dấu và không dấu, phrase/NEAR, BM25 có trọng số cột, đồng nghĩa; hợp BM25 + vector | bắt buộc | Tài liệu tokenizer/truy vấn |
| 6 | Lọc theo văn bản, loại, cơ quan, hiệu lực, tag | bắt buộc | Tài liệu |
| 7 | Giao dịch; một luồng ghi nền song song với đọc | bắt buộc | Tài liệu concurrency |
| 8 | Bảo trì: có bản phát hành trong 6 tháng, không archived | nên có | PyPI/GitHub |
| 9 | Thêm ít dung lượng cho bộ cài (hiện 840 MB) | nên có | Cỡ wheel/binary nén |
| 10 | Chi phí sửa `search.py`/`semantic.py`, đo lại, chuyển dữ liệu | nên có | Mục 7 |

## 4. So sánh ứng viên

Mọi nguồn trong mục này đọc ngày 29/10/2026. "Bản mới nhất" là bản ổn định mới nhất trên PyPI hoặc GitHub tính tới ngày đó. Cỡ bộ cài là cỡ wheel/file nén.

### 4.1 Kho chính (CSDL, full-text, vector)

**Giấy phép, phiên bản, nền**

| Ứng viên | Giấy phép | Bản mới nhất (ngày) | Windows, không admin | Kiểu | Thêm vào bộ cài | Bảo trì |
|---|---|---|---|---|---|---|
| **SQLite + FTS5** (đang dùng) | public domain | 3.54.1, 16/10/2026 ([chronology](https://sqlite.org/chronology.html)). Python 3.11 bản Windows kèm 3.45.1 ([get_externals.bat](https://github.com/python/cpython/blob/3.11/PCbuild/get_externals.bat)) | có. CPython Windows build với FTS5 và cho nạp extension (`PY_SQLITE_ENABLE_LOAD_EXTENSION`, [_sqlite3.vcxproj](https://github.com/python/cpython/blob/3.11/PCbuild/_sqlite3.vcxproj)) | nhúng | 0 | rất tốt |
| + **sqlite-vec** | MIT / Apache-2.0 ([PyPI](https://pypi.org/project/sqlite-vec/)) | 0.1.9, 31/03/2026; 0.1.10-alpha.4, 18/05/2026 ([releases](https://github.com/asg017/sqlite-vec/releases)) | wheel `py3-none-win_amd64` | extension SQLite | 0,3 MB | ngừng 16 tháng (0.1.6 ngày 20/11/2024 → 0.1.7 ngày 17/03/2026, "after a long hiatus"); README: "pre-v1, so expect breaking changes" |
| **DuckDB** (fts, vss) | MIT | 2.0.0, 21/10/2026 ([PyPI](https://pypi.org/project/duckdb/)) | wheel cp311 `win_amd64`. Extension fts/vss được tải về khi `INSTALL` rồi cache ([docs](https://duckdb.org/docs/2.0/extensions/installing_extensions.html)), nên phải gói sẵn | nhúng | 14,7 MB + extension | rất tích cực |
| **LanceDB** | Apache-2.0 | 0.41.0, 29/10/2026 ([PyPI](https://pypi.org/project/lancedb/)) | wheel abi3 `win_amd64` | nhúng | 81,6 MB + pyarrow 27,2 MB | rất tích cực |
| **Chroma** | Apache-2.0 | 1.5.9, 05/05/2026 ([PyPI](https://pypi.org/project/chromadb/)) | wheel `win_amd64`; phụ thuộc bắt buộc gồm kubernetes, grpcio, opentelemetry, onnxruntime | nhúng/server | 22,5 MB + phụ thuộc | không có bản nào từ 05/2026 |
| **Qdrant** server | Apache-2.0 | v1.20.0, 22/10/2026 ([release](https://github.com/qdrant/qdrant/releases/tag/v1.20.0)) | `qdrant-x86_64-pc-windows-msvc.zip` | server (tiến trình riêng) | 29,4 MB | rất tích cực |
| Qdrant local (`qdrant-client`) | Apache-2.0 | 1.20.0, 22/10/2026 | Python thuần | nhúng, NumPy | 0,4 MB | mã nguồn cảnh báo "Local mode is not recommended for collections with more than 20,000 points" ([qdrant_local.py](https://github.com/qdrant/qdrant-client/blob/master/qdrant_client/local/qdrant_local.py)) |
| Qdrant Edge (tìm thêm) | Apache-2.0 ([PyPI](https://pypi.org/project/qdrant-edge-py/)) | 0.9.0, 22/10/2026 | wheel abi3 `win_amd64` | nhúng | 12 MB | "Qdrant Edge is in beta" ([docs](https://qdrant.tech/documentation/edge/)) |
| **Meilisearch** | MIT, riêng phần Enterprise là BUSL-1.1 ([LICENSE](https://github.com/meilisearch/meilisearch/blob/main/LICENSE)) | v1.56.0, 26/10/2026 | `meilisearch-windows-amd64.exe` ([assets](https://github.com/meilisearch/meilisearch/releases/tag/v1.56.0)) | server | 337 MB | rất tích cực |
| **Typesense** | **GPL-3.0** ([LICENSE](https://github.com/typesense/typesense/blob/v30/LICENSE.txt)) | 30.2, 19/04/2026 | tài liệu cài đặt chỉ nêu WSL cho Windows ([docs](https://typesense.org/docs/guide/install-typesense.html)) | server | – | tích cực |
| **Weaviate** | BSD-3-Clause, riêng thư mục `wl` là giấy phép doanh nghiệp từ 2026 ([LICENSE](https://github.com/weaviate/weaviate/blob/main/LICENSE)) | v1.40.3, 28/10/2026 | asset chỉ có darwin và linux ([v1.40.3](https://github.com/weaviate/weaviate/releases/tag/v1.40.3)); bản embedded "supported on Linux and macOS", còn "experimental" ([docs](https://docs.weaviate.io/deploy/installation-guides/embedded)) | server | – | rất tích cực |
| **Milvus Lite** | Apache-2.0 | 3.2.2, 13/10/2026 ([PyPI](https://pypi.org/project/milvus-lite/)) | bản 3.x viết lại bằng Python thuần; CI thử Windows trên Python 3.10 ([README](https://github.com/milvus-io/milvus-lite)) | nhúng/gRPC | faiss-cpu 15,5 + pyarrow 27,2 MB + grpcio | tích cực; README: "intended for prototyping and local workloads" |
| **PostgreSQL + pgvector** | PostgreSQL License | PG 18 (bảng Windows, [postgresql.org](https://www.postgresql.org/download/windows/)); pgvector 0.8.7, 01/10/2026 | PG có zip binaries "to include Postgres as part of another application installer". pgvector trên Windows phải tự build bằng Visual Studio, "run … as administrator" ([README](https://github.com/pgvector/pgvector)) | server | chưa đo | tích cực |
| ParadeDB `pg_search` | **AGPL-3.0** ([LICENSE](https://github.com/paradedb/paradedb/blob/main/LICENSE)) | v0.26.3, 23/10/2026 | danh sách binary dựng sẵn chỉ gồm Debian, Ubuntu, RHEL, macOS ([docs](https://www.paradedb.com/docs/deploy/self-hosted/extension)) | extension PG | – | tích cực |
| **OpenSearch** | Apache-2.0 | 3.9.0, 20/10/2026 | zip Windows kèm JDK; heap khởi điểm khuyên "half of the available system memory" ([docs](https://docs.opensearch.org/latest/install-and-configure/install-opensearch/windows/)) | server JVM | lớn, chưa đo | rất tích cực |
| **Elasticsearch** | **AGPL-3.0 / SSPL / Elastic License 2.0**; x-pack chỉ ELv2 ([LICENSE](https://github.com/elastic/elasticsearch/blob/main/LICENSE.txt)) | 9.5.5, 06/10/2026 | zip Windows kèm OpenJDK ([docs](https://www.elastic.co/docs/deploy-manage/deploy/self-managed/install-elasticsearch-with-zip-on-windows)) | server JVM | lớn, chưa đo | rất tích cực |
| **Tantivy** (`tantivy`, tantivy-py) | MIT | 0.27.0, 22/10/2026 ([PyPI](https://pypi.org/project/tantivy/)) | wheel abi3 `win_amd64` | thư viện full-text | 4,1 MB | 4 bản/12 tháng |
| **txtai** | Apache-2.0 | 9.14.0, 06/10/2026 ([PyPI](https://pypi.org/project/txtai/)) | Python thuần, nhưng bắt buộc torch (wheel Windows 120,8 MB), transformers, faiss-cpu | nhúng | ≥ 150 MB | tích cực |
| zvec (tìm thêm) | Apache-2.0 | 0.8.0, 21/10/2026; bản đầu 31/12/2025 ([PyPI](https://pypi.org/project/zvec/)) | wheel cp311 `win_amd64` | nhúng | 11,7 MB | mới, trước 1.0 |
| libSQL (tìm thêm) | MIT ([LICENSE](https://github.com/tursodatabase/libsql/blob/main/LICENSE.md)) | gói Python `libsql` 0.1.11, 02/09/2025 ([PyPI](https://pypi.org/project/libsql/)); bản viết lại `pyturso` 0.8.3 không có wheel Windows | wheel `win_amd64` (libsql) | nhúng (fork SQLite) | 3,9 MB | gói Python: 0 bản trong 12 tháng |

**Năng lực truy hồi**

| Ứng viên | Vector: chỉ mục, lượng tử | Full-text, tiếng Việt | Hợp (hybrid) sẵn | Lọc, giao dịch | Kết luận |
|---|---|---|---|---|---|
| **SQLite + FTS5** | không có (app tìm bằng NumPy) | BM25 trọng số cột, phrase, `NEAR`, tokenizer tự viết, `remove_diacritics` 0/1/2 ([FTS5](https://sqlite.org/fts5.html)); hai nhánh có dấu/không dấu đã chạy | không (app tự làm RRF) | SQL đầy đủ, ACID; WAL một ghi nhiều đọc | **Giữ** |
| sqlite-vec | `vec0` quét toàn bộ (bản 0.1.9). ANN (rescore, DiskANN; IVF còn thử nghiệm, chưa bật) chỉ có ở 0.1.10-alpha. Kiểu float, int8, bit | – | – | cột metadata/partition/auxiliary; cùng giao dịch với SQLite | Chưa dùng (mục 6.3) |
| DuckDB | VSS: HNSW, chỉ FLOAT. Lưu chỉ mục xuống đĩa vẫn là thử nghiệm: WAL chưa khôi phục được chỉ mục, tắt đột ngột có thể mất dữ liệu hoặc hỏng chỉ mục, tài liệu khuyên chưa dùng cho production; chỉ mục phải nằm trọn trong RAM ([vss](https://duckdb.org/docs/2.0/core_extensions/vss.html)) | BM25 (k1, b); mặc định stemmer và stopwords tiếng Anh, `strip_accents`, mẫu `ignore` bỏ mọi ký tự ngoài a–z (nên phải tự đặt lại cho chữ như "đ"); không thấy phrase/NEAR trong tài liệu (29/10/2026); chỉ mục không tự cập nhật trừ khi tạo với `incremental = 1` ([fts](https://duckdb.org/docs/2.0/core_extensions/full_text_search.html)) | không | MVCC lạc quan; chỉ một tiến trình được ghi ([concurrency](https://duckdb.org/docs/2.0/connect/concurrency.html)) | Loại |
| LanceDB | IVF + PQ/RQ/SQ, IVF_HNSW; dưới ~100K vector thường không cần chỉ mục ([FAQ](https://docs.lancedb.com/faq/faq-oss), [indexing](https://docs.lancedb.com/indexing)) | BM25; `ascii_folding` bật mặc định, nên cần hai chỉ mục cho có dấu/không dấu; phrase cần `with_position=True`; dòng mới chỉ vào chỉ mục sau `optimize()` ([FTS](https://docs.lancedb.com/search/full-text-search)) | RRF mặc định, có CrossEncoder ([hybrid](https://docs.lancedb.com/search/hybrid-search)) | `where` lọc trước hoặc sau; FAQ: "too many concurrent writers can lead to failing writes" | Đường nâng cấp chỉ khi ≫ 1 triệu vector |
| Chroma | HNSW | `where_document` chỉ để lọc (`$contains`, `$regex`), "case-sensitive"; không thấy xếp hạng BM25 ([docs](https://docs.trychroma.com/docs/querying-collections/full-text-search)) | "Search API is available in Chroma Cloud only" ([docs](https://docs.trychroma.com/cloud/search-api/overview)) | lọc metadata | Loại |
| Qdrant server | HNSW; lượng tử int8, binary 1/1,5/2 bit, PQ, TurboQuant; vector để trên đĩa được ([quantization](https://qdrant.tech/documentation/guides/quantization/)) | text index (word, multilingual…), `ascii_folding` từ v1.16, phrase matching; **BM25 scoring chỉ có từ v1.20.0 (22/10/2026)** ([indexing](https://qdrant.tech/documentation/concepts/indexing/)) | Query API prefetch + RRF (v1.10) / DBSF (v1.11) ([hybrid](https://qdrant.tech/documentation/concepts/hybrid-queries/)) | lọc payload | Dùng được nhưng thêm tiến trình và kho thứ hai; không cần |
| Meilisearch | có (hybrid, README) | tokenizer charabia, với chữ Latin: "nonspacing-marks removal" ([charabia](https://github.com/meilisearch/charabia)), tức là bỏ dấu, mất nhánh có dấu; không thấy trong tài liệu cách tắt (29/10/2026) | có (README) | lọc | Loại |
| Typesense, Weaviate | – | – | – | – | Loại vì nền (chỉ WSL / không có bản Windows); không xét tiếp |
| Milvus Lite | HNSW, HNSW_SQ, IVF_FLAT, IVF_SQ8, FLAT; "No … float16 … or int8 vector fields" | BM25 qua sparse, analyzer standard/Jieba; "BM25 IDF statistics are segment-local" | RRF, Weighted | lọc scalar; "concurrent writers are not supported safely"; một tiến trình mỗi thư mục | Loại |
| PG + pgvector / ParadeDB | HNSW, IVFFlat; halfvec, bit, sparsevec ([README](https://github.com/pgvector/pgvector)) | ParadeDB có BM25 nhưng AGPL | tự viết | ACID đầy đủ | Loại (phải build pgvector, server, AGPL) |
| OpenSearch / Elasticsearch | có | có | có | có | Loại (JVM nặng; Elasticsearch AGPL/SSPL); không xét tiếp |
| Tantivy | không | BM25, phrase; tokenizer `regex`/`ngram` + filter `ascii_fold`, `lowercase` ([tantivy.pyi](https://github.com/quickwit-oss/tantivy-py/blob/master/tantivy/tantivy.pyi)) | không | một IndexWriter | Không cần: FTS5 đã đủ |
| txtai | Faiss/HNSW/NumPy…; đồ thị NetworkX | `bm25`/`tfidf`/`sif`, chuẩn hoá điểm ([scoring](https://neuml.github.io/txtai/embeddings/configuration/scoring/)) | có (sparse + dense) | – | Loại (kéo theo torch) |
| zvec | Flat, HNSW, HNSW-RaBitQ, DiskANN, IVF ([docs](https://zvec.org/en/docs/db/concepts/vector-index/)) | có FTS "native"; không thấy tài liệu về phrase hay tiếng Việt (29/10/2026) | có (README) | "writes are single-process exclusive" | Theo dõi; còn quá mới |
| libSQL | DiskANN qua `libsql_vector_idx`, `vector_top_k` ([docs](https://docs.turso.tech/features/ai-and-embeddings)) | FTS5 (fork SQLite) | không | như SQLite | Không: phải thay driver `sqlite3`; tài liệu chỉ nói tới libSQL Server, không nói file cục bộ |

### 4.2 Thư viện chỉ mục vector (đặt cạnh SQLite)

| Thư viện | Giấy phép | Bản mới nhất (ngày) | Windows | Chỉ mục | Lượng tử | Lọc trong Python | Ghi chú |
|---|---|---|---|---|---|---|---|
| NumPy (đang dùng) | BSD-3 | – | có | vét cạn | app lưu f16, tính f32 | mặt nạ NumPy | Đơn giản nhất; RAM = 4 byte × chiều × số vector |
| **USearch** | Apache-2.0 | 2.26.6, 25/10/2026 ([PyPI](https://pypi.org/project/usearch/)) | wheel cp311 `win_amd64` 0,33 MB + `numkong` 0,47 MB | HNSW; `search(..., exact=True)` vét cạn bằng SIMD | f32, bf16, f16, e5m2, e4m3, i8, b1 | README: Python **không** có "filter predicates" ([README](https://github.com/unum-cloud/usearch)) | save/load/`view` (mmap); 161 bản phát hành từ 2023 |
| FAISS (`faiss-cpu`) | MIT | 1.15.1, 16/09/2026 ([PyPI](https://pypi.org/project/faiss-cpu/)) | wheel cp311 `win_amd64` | Flat, HNSW, IVF, PQ, SQ fp16/8 bit… ([wiki](https://github.com/facebookresearch/faiss/wiki/Faiss-indexes)) | có | chưa kiểm | Nặng gấp ~20 lần USearch |
| hnswlib | Apache-2.0 | 0.8.0, 03/12/2023 ([PyPI](https://pypi.org/project/hnswlib/)) | **chỉ có sdist**, phải build C++ | HNSW | – | – | Loại: không build từ mã nguồn; ngừng phát hành từ 2023 |
| sqlite-vec | xem 4.1 | | | vét cạn (bản ổn định) | float/int8/bit | cột metadata | Số đo ở mục 5 |

### 4.3 Kho đồ thị (cho P4 và cho các framework ở 4.4)

| Kho | Giấy phép | Bản mới nhất (ngày) | Windows chạy thẳng | Kiểu | Ghi chú |
|---|---|---|---|---|---|
| **SQLite + CTE đệ quy** | public domain | như 4.1 | có | nhúng | "hierarchical or recursive queries of trees and graphs" ([lang_with](https://sqlite.org/lang_with.html)) |
| NetworkX | BSD-3-Clause | 3.7, 21/09/2026 ([PyPI](https://pypi.org/project/networkx/)) | Python thuần | thư viện trong RAM | 3.7 cần Python ≥ 3.12; app chạy 3.11 nên chỉ dùng được bản cũ hơn |
| Kùzu | MIT | 0.11.3, 10/10/2025 ([PyPI](https://pypi.org/project/kuzu/)) | wheel `win_amd64` | nhúng | **"archived by the owner on Oct 10, 2025"** ([GitHub](https://github.com/kuzudb/kuzu)) |
| LadybugDB (fork của Kùzu) | MIT ([PyPI](https://pypi.org/project/ladybug/)) | 0.22.1, 28/10/2026 | wheel cp311 `win_amd64` | nhúng (Cypher, FTS, vector) | "formerly known as Kuzu" ([README](https://github.com/LadybugDB/ladybug)); kho đồ thị mặc định của Cognee |
| Neo4j Community | **GPL-3.0** ([LICENSE](https://github.com/neo4j/neo4j/blob/dev/LICENSE.txt)) | 2026.10.1 ([yêu cầu](https://neo4j.com/docs/operations-manual/current/installation/requirements/)) | Windows 11 cho "personal use and software development"; cần JVM 21/25 cài sẵn; RAM "2GB minimum, 16GB or more recommended" | server JVM | Graphiti và neo4j-graphrag cần nó |
| FalkorDB | **SSPL-1.0** (không phải OSI) ([LICENSE](https://github.com/FalkorDB/FalkorDB/blob/master/LICENSE.txt)) | v4.22.3, 28/10/2026 | FalkorDBLite 0.11.0 chỉ có wheel Linux/macOS ([PyPI](https://pypi.org/project/falkordblite/)) | module Redis | Loại |
| Memgraph | **BSL 1.1** + MEL (không phải OSI) ([LICENSE](https://github.com/memgraph/memgraph/blob/master/LICENSE)) | v3.14.0, 21/10/2026 | Windows "through WSL" ([docs](https://memgraph.com/docs/getting-started/install-memgraph)) | server | Loại |
| ArangoDB | **BSL 1.1** ([LICENSE](https://github.com/arangodb/arangodb/blob/devel/LICENSE)) | 3.12.12 | "Starting with version 3.12, ArangoDB packages for Windows and macOS are not provided anymore" ([docs](https://docs.arango.ai/arangodb/stable/operations/installation/)) | server | Loại |
| Apache AGE | Apache-2.0 | 1.8.0 (PG18 06/08/2026, PG15 19/09/2026) | README chỉ hướng dẫn build cho Linux/macOS; Windows chỉ có link video ([README](https://github.com/apache/age)) | extension PG | Loại (cần PostgreSQL + build) |
| DuckPGQ | chưa thấy giấy phép trên trang | – | trang có cột Windows nhưng ô trạng thái trống ([trang](https://duckdb.org/community_extensions/extensions/duckpgq.html)) | extension DuckDB | "part of an ongoing research project"; loại |

**Copyleft, nói ngắn (không phải tư vấn pháp lý):**
- GPL-3.0 (Typesense, Neo4j Community): kèm binary vào bộ cài thì phải kèm giấy phép và mã nguồn (hoặc lời đề nghị cung cấp mã nguồn) của chính phần đó. Chạy thành tiến trình riêng, nói chuyện qua socket, thường được coi là gộp chung (aggregate), không bắt mã của app theo GPL. Nạp thư viện GPL vào cùng tiến trình Python thì khác.
- AGPL-3.0 (ParadeDB, một lựa chọn của Elasticsearch): như GPL, cộng điều khoản dùng qua mạng.
- SSPL và BSL không phải giấy phép OSI, nên trái yêu cầu của chủ dự án.

### 4.4 Framework RAG đồ thị tri thức / bộ nhớ AI (Cognee, Graphiti và tương tự)

**Giấy phép, kho, nền, LLM cục bộ**

| Framework | Giấy phép | Bản mới nhất (ngày); bảo trì | Kho mặc định / hỗ trợ | Windows chạy thẳng, offline | LLM cục bộ |
|---|---|---|---|---|---|
| **Cognee** | Apache-2.0 | 1.6.5, 16/10/2026; 106 bản/12 tháng ([PyPI](https://pypi.org/project/cognee/)) | SQLite + LanceDB + **Ladybug** ("kuzu" là tên cũ); hỗ trợ Postgres, PGVector, Chroma, Neo4j, Neptune, Memgraph ([cấu hình](https://docs.cognee.ai/setup-configuration/overview)) | về lý thuyết được: ba kho mặc định đều có wheel Windows. Nhưng có khoảng 50 phụ thuộc bắt buộc (litellm 35,7 MB, lancedb, pylance, ladybug, dlt…) | `LLM_PROVIDER` = `ollama`, `llama_cpp`, `custom` |
| **Graphiti** | Apache-2.0 | 0.31.2, 20/10/2026; 32 bản/12 tháng ([PyPI](https://pypi.org/project/graphiti-core/)) | Neo4j 5.26 / FalkorDB 1.1.2 / Neptune; "Kuzu is deprecated" ([README](https://github.com/getzep/graphiti)) | trên thực tế cần server Neo4j (JVM, GPL). README chạy FalkorDB qua Docker; FalkorDBLite không có wheel Windows | `OpenAIGenericClient` tới endpoint `/v1` (Ollama, vLLM, llama.cpp). README cảnh báo dịch vụ không có Structured Output "may result in incorrect output schemas and ingestion failures… particularly problematic when using smaller models" |
| **LightRAG** | MIT | 1.5.7, 02/09/2026; 31 bản/12 tháng ([PyPI](https://pypi.org/project/lightrag-hku/)) | JSON KV + NanoVectorDB + NetworkX, "only for small-scale testing… not suitable for production"; khuyên dùng PostgreSQL ([README](https://github.com/HKUDS/LightRAG)) | Python thuần; tiktoken phải tải trước nếu chạy offline (README) | endpoint OpenAI-compatible, Ollama. README: cho trích xuất cục bộ "Qwen3-30B-A3B-Instruct is a reasonable minimum"; mô hình "below ~50 tokens/second" dễ quá thời gian |
| **Microsoft GraphRAG** | MIT | 3.3.0, 08/10/2026 ([PyPI](https://pypi.org/project/graphrag/)); README: "largely in maintenance mode, and won't be accepting new PRs or implementing new features" | file parquet + LanceDB ([defaults.py](https://github.com/microsoft/graphrag/blob/main/packages/graphrag/graphrag/config/defaults.py)) | Python thuần + spacy, pyarrow | qua LiteLLM; mô hình "must support returning structured outputs adhering to a JSON schema", với mô hình qua proxy thì "frequently see issues with malformed responses" ([docs](https://microsoft.github.io/graphrag/config/models/)) |
| nano-graphrag | MIT | 0.0.8.2, 19/10/2024; commit cuối 27/01/2026 ([PyPI](https://pypi.org/project/nano-graphrag/)) | NetworkX + nano-vectordb | được | có |
| HippoRAG 2 | MIT ([LICENSE](https://github.com/OSU-NLP-Group/HippoRAG/blob/main/LICENSE)) | PyPI 2.0.0a4, 24/06/2025 (alpha); commit 06/10/2026 | đồ thị igraph; `setup.py` ghim `torch==2.5.1`, `transformers==4.45.2` | ví dụ cục bộ chạy vLLM với Llama-3.3-70B trên 2 GPU (README) | `llm_base_url` tới endpoint OpenAI-compatible |
| Mem0 | Apache-2.0 | 2.2.1, 25/09/2026 ([PyPI](https://pypi.org/project/mem0ai/)) | phụ thuộc bắt buộc qdrant-client, sqlalchemy; tích hợp kho đồ thị ngoài (Neo4j, Memgraph, Kuzu, AGE, Neptune) "has been replaced" bằng Graph Memory tích hợp ([docs](https://docs.mem0.ai/open-source/features/graph-memory)) | được | nhiều nhà cung cấp; làm cho bộ nhớ hội thoại, không cho kho văn bản |
| LlamaIndex PropertyGraphIndex | MIT | llama-index-core 0.14.25, 21/09/2026 | `SimplePropertyGraphStore` (RAM, lưu ra đĩa); Neo4j, Nebula, TiDB, FalkorDB ([guide](https://developers.llamaindex.ai/python/framework/module_guides/indexing/lpg_index_guide/)) | được | qua các gói LLM của LlamaIndex (chưa kiểm từng gói) |
| neo4j-graphrag | Apache-2.0 | 1.23.0, 28/10/2026 ([PyPI](https://pypi.org/project/neo4j-graphrag/)) | bắt buộc Neo4j | cần server Neo4j | `ollama`, `openai`… ([README](https://github.com/neo4j/neo4j-graphrag-python)) |
| txtai graph | Apache-2.0 | 9.14.0, 06/10/2026 | NetworkX (mặc định) hoặc `rdbms` ([graph](https://neuml.github.io/txtai/embeddings/configuration/graph/)) | được, nhưng kéo theo torch | không cần LLM: cạnh được dựng từ độ tương tự embedding (`minscore` 0,1, `limit` 15), chủ đề bằng Louvain |

**Gọi LLM khi nạp và khi hỏi**

| Framework | Gọi LLM khi nạp | Gọi LLM khi hỏi |
|---|---|---|
| Cognee | `cognify`: mặc định 2 lệnh LLM mỗi chunk (trích đồ thị + tóm tắt); chunk 512–4.096 token. Có bộ trích GLiNER cục bộ không cần LLM nhưng tên là `gliner_demo` ([cognify](https://docs.cognee.ai/core-concepts/main-operations/cognify)) | `GRAPH_COMPLETION`: một lệnh trả lời |
| Graphiti | Mỗi episode: trích nút, khử trùng nút (khi cần), trích cạnh, tóm tắt nút (mỗi lô 30 nút); **mỗi cạnh** thêm một lệnh "lightweight" lấy `valid_at`/`invalid_at`, và một lệnh khử trùng khi đã có cạnh liên quan ([edge_operations.py](https://github.com/getzep/graphiti/blob/main/graphiti_core/utils/maintenance/edge_operations.py), [node_operations.py](https://github.com/getzep/graphiti/blob/main/graphiti_core/utils/maintenance/node_operations.py)). Ngữ cảnh kèm 3 episode trước (`EPISODE_WINDOW_LEN = 3`) | tìm kiếm không cần LLM |
| LightRAG | trích thực thể–quan hệ mỗi chunk 1.200 token, `DEFAULT_MAX_GLEANING = 1` (thêm một lượt), tóm tắt khi gộp mô tả ([constants.py](https://github.com/HKUDS/LightRAG/blob/main/lightrag/constants.py)) | một lệnh trích từ khoá + một lệnh trả lời; ngữ cảnh mặc định tới `DEFAULT_MAX_TOTAL_TOKENS = 30000` |
| GraphRAG | trích mỗi chunk 1.200/100 token + `max_gleanings 1`, tóm tắt mô tả, báo cáo cộng đồng (`max_input_length 8000`, `max_length 2000`) | local: một lệnh; global: map-reduce nhiều lệnh |
| HippoRAG 2 | OpenIE: một lệnh NER + một lệnh bộ ba cho mỗi đoạn | lọc bộ ba bằng LLM (`DSPyFilter`) + một lệnh trả lời ([HippoRAG.py](https://github.com/OSU-NLP-Group/HippoRAG/blob/main/src/hipporag/HippoRAG.py)) |
| Mem0 | "Single-pass ADD-only extraction -- one LLM call" mỗi lần add ([README](https://github.com/mem0ai/mem0)) | tìm theo nghĩa + BM25 + thực thể |
| LlamaIndex | `SimpleLLMPathExtractor`: một lệnh mỗi chunk (chunk mặc định 1.024 token, `max_paths_per_chunk=10`); `ImplicitPathExtractor` không cần LLM | mặc định `LLMSynonymRetriever` gọi LLM sinh từ khoá |
| neo4j-graphrag | một lệnh trích mỗi chunk (`SimpleKGPipeline`) | tuỳ retriever |
| txtai graph | không | không bắt buộc |

### 4.5 Dựng đồ thị tri thức bằng LLM cho 61K Điều trên máy 16 GB: ước tính

**Giả định:** đọc prompt 45 token/s, sinh 13 token/s (ước tính trung tâm cho Qwen3-VL-4B Q4_K_M, 6 luồng; `chon-mo-hinh.md` mục 4; chưa đo). Kho có 61.425 Điều × trung bình 331 token (tokenizer Qwen3; `chon-mo-hinh.md` mục 3.2), tức ≈ 20,3 triệu token. Phần chỉ dẫn cố định đứng đầu prompt được `llama-server` dùng lại, chỉ phần mới phải đọc ("có cache"). Cỡ chỉ dẫn đếm thô từ mã nguồn (số ký tự / 4). Cỡ đầu ra là giả định. Cách tính ghi trong script ước tính (mục 5, cuối).

| Cách | Giả định chính | Thời gian CPU chạy liên tục (ước tính) |
|---|---|---|
| **Sàn cho mọi framework**: đọc kho một lượt, không chỉ dẫn, không sinh | 20,3 triệu token / 45 t/s | **5,2 ngày** |
| Sàn + sinh bộ ba gọn bằng ~30% số token vào | + 6,1 triệu token / 13 t/s | 10,7 ngày |
| LlamaIndex `SimpleLLMPathExtractor` | 24.674 chunk 1.024/200; ~150 token ra mỗi chunk | ~10 ngày |
| Mem0 (mỗi Điều một lần add) | ~200 token ra mỗi Điều | ~17 ngày (và viết lại thành "fact", không giữ nguyên văn) |
| Cognee | 19.855 chunk ~1.024; lệnh trích ra ~500 token, lệnh tóm tắt ~150 | ~23 ngày |
| LightRAG | 18.483 chunk 1.200/100; lượt đầu ~700 token ra, gleaning ~250 | ~25 ngày, chưa tính các lần tóm tắt khi gộp mô tả |
| GraphRAG | trích như LightRAG (~23 ngày) + báo cáo cộng đồng (giả định 5.000 cộng đồng, 4.000 token vào, 1.000 ra) | ~33 ngày |
| HippoRAG 2 | NER (~80 token ra) + bộ ba (~300 token ra) mỗi Điều | ~33 ngày |
| Graphiti | 1 Điều = 1 episode, 5 cạnh; 4 lệnh chính + 2 lệnh mỗi cạnh; ngữ cảnh có 3 episode trước | **~175 ngày (có cache) tới ~360 ngày (không cache)** |

Đọc kết quả:
- **Không khả thi trên máy 16 GB không GPU.** Ngay mức sàn đã là 5 ngày CPU 100% (6 luồng). Các framework cần từ ~10 ngày (LlamaIndex) tới ~3,5 tuần (Cognee, LightRAG) và ~5 tuần (GraphRAG, HippoRAG 2); Graphiti cần nửa năm tới một năm. Máy văn phòng không chạy liên tục được như vậy, và Office bị chậm trong suốt thời gian đó. Để so sánh, nhúng vector cả kho hiện mất 5–7 giờ (`docs/kien-truc.md` mục 5.2 của bản trước `6f39851` (`git show 6f39851^:docs/kien-truc.md`)). Mỗi văn bản mới nạp vào lại tốn thêm tương ứng.
- **Chất lượng chưa có bảo đảm.** Chính các framework khuyên dùng mô hình lớn hơn nhiều: LightRAG cho rằng Qwen3-30B-A3B là mức tối thiểu khi chạy cục bộ; Graphiti và GraphRAG cảnh báo mô hình nhỏ trả sai schema. Không tìm thấy benchmark trích thực thể–quan hệ tiếng Việt nào cho Qwen3-VL-4B (29/10/2026). Prompt và loại thực thể mặc định viết cho tiếng Anh (tổ chức, người, địa điểm, sự kiện), không có các loại "văn bản / Điều / cơ quan / chủ thể / hành vi / chế tài".
- **Khi hỏi.** Mỗi lệnh LLM thêm tốn ~5–25 s trên CPU (ước tính), tuỳ có cache hay không và dài bao nhiêu token. Ngân sách 45 s đã gần chạm với một lệnh trả lời ~1.000 token (`chon-mo-hinh.md` mục 4). Vì vậy luồng hỏi của LightRAG (từ khoá + trả lời, ngữ cảnh mặc định 30K token), GraphRAG global, HippoRAG 2 (lọc + trả lời) và LlamaIndex mặc định (từ khoá đồng nghĩa + trả lời) không vừa. Graphiti không gọi LLM khi hỏi, nhưng lại cần Neo4j.
- **Trái nguyên tắc của lộ trình.** Mục "Không làm" (§10) có dòng "Dùng LLM để lập chỉ mục hay tóm tắt cả văn bản, chạy nền"; mục 5 điều 6 yêu cầu "Máy gợi ý, người quyết". Không ai duyệt nổi hàng trăm nghìn cạnh do LLM sinh.
- **So với trích quan hệ bằng quy tắc (P4).** Quan hệ cần cho P4 (căn cứ, hướng dẫn, sửa đổi, thay thế, bãi bỏ, dẫn chiếu) có câu chữ gần như cố định ("Căn cứ Luật … số …", "sửa đổi, bổ sung Điều … như sau"). Quy tắc chạy vài mili giây mỗi văn bản, cho kết quả cố định, và cổng P4 đo được bằng nhãn tay (đúng ≥ 95%, đủ ≥ 85%).
- **Nếu sau P4 đo thấy quy tắc bỏ sót nhiều:** có thể cho LLM đọc *riêng phần mở đầu* của từng văn bản (khoảng 1 lệnh, ~20 s mỗi văn bản). Với 3.271 văn bản, ước tính ~18 giờ CPU chạy nền; kết quả vào hàng chờ duyệt. Đây là tuỳ chọn sau P4, không phải framework.

**Mô hình thời gian của Graphiti so với hiệu lực văn bản** (trường của `EntityEdge` trong [edges.py](https://github.com/getzep/graphiti/blob/main/graphiti_core/edges.py))

| Trường Graphiti | Nghĩa trong Graphiti | Ánh xạ sang hiệu lực pháp lý |
|---|---|---|
| `valid_at` | "when the fact became true" | ngày có hiệu lực của quy định hoặc quan hệ (vd. ngày văn bản thay thế có hiệu lực) |
| `invalid_at` | "when the fact stopped being true" | ngày hết hiệu lực: bị thay thế, bãi bỏ, hoặc Điều bị sửa đổi; để trống nếu chưa biết |
| `created_at` | lúc cạnh được tạo trong hệ | lúc app nạp văn bản nguồn và ghi nhận quan hệ |
| `expired_at` | "when the node was invalidated" (trong hệ) | lúc người duyệt xác nhận hoặc gỡ gợi ý |
| `episodes` | các episode nguồn của cạnh | `src_doc_id`, `src_unit_id`, đoạn trích (đã có trong `effect_hints`) |

- Graphiti tự vô hiệu cạnh khi LLM thấy hai sự kiện mâu thuẫn. Với luật, việc vô hiệu phải dựa trên câu chữ của văn bản ("thay thế", "bãi bỏ", "sửa đổi") và có người xác nhận.
- Một khoảng thời gian cho mỗi cạnh là đủ cho quan hệ giữa hai văn bản. Trạng thái hiệu lực còn cần thêm phạm vi (cả văn bản / Điều / khoản), hết hiệu lực một phần, và điều khoản chuyển tiếp. "Chưa có hiệu lực" (ngày hiệu lực sau hôm nay) tính lúc hiển thị, đúng như lộ trình 2d.

**Ý tưởng lấy về mà không cần framework**

| Ý tưởng | Từ | Làm trong SQLite? | Cần framework/LLM? |
|---|---|---|---|
| Cạnh có hai trục thời gian (hiệu lực từ–đến; ghi nhận–xác nhận); vô hiệu chứ không xoá; tra "theo ngày X" | Graphiti | có: thêm cột ngày vào `doc_relations`, điều kiện `tu <= :x AND (den IS NULL OR den > :x)` | không |
| Mỗi cạnh nhớ nguồn (văn bản, đơn vị, đoạn trích) | Graphiti `episodes` | có | không |
| Bảng thực thể/quan hệ có kiểu theo một ontology luật (văn bản, Điều, cơ quan, chủ thể, mức phạt, thời hạn) | Cognee/Graphiti (kiểu tự định nghĩa) | có, trích bằng regex và từ điển; `fine_min/fine_max` đã có | không |
| Backlinks, đồ thị cục bộ 1–2 bước | Obsidian, GraphRAG local | có: CTE đệ quy | không |
| Cạnh "nội dung tương tự" từ vector sẵn có (gợi ý "Cũng có ở…", "Liên quan") | txtai graph | có: top-k + ngưỡng cosine, chạy nền bằng NumPy/USearch, vài phút; phải ghi rõ là tương tự chứ không phải quan hệ pháp lý | không |
| Nhóm văn bản theo cộng đồng (Louvain) | GraphRAG, txtai | NetworkX trên đồ thị quan hệ (chỉ khi cần) | không cần LLM |
| Tóm tắt thực thể/cộng đồng, trích quan hệ tự do trên toàn văn | LightRAG, GraphRAG, Cognee | – | **cần LLM**, mất nhiều tuần CPU; lộ trình §10 không làm |
| Personalized PageRank để lan điểm từ Điều khớp sang văn bản liên quan | HippoRAG 2 | làm được (NetworkX hoặc SQL lặp) | không; chỉ nên thử sau khi có `doc_relations` và bộ đo |

## 5. Số đo trong sandbox

**Máy đo không phải máy chuẩn.** Sandbox: Intel Xeon @ 2,10 GHz (KVM), 4 vCPU, có AVX-512/AMX, L3 260 MiB (chia với máy chủ ảo), 15 GB RAM; Python 3.13.17, NumPy 2.5.4 (OpenBLAS 0.3.34), SQLite 3.45.1, sqlite-vec 0.1.9, USearch 2.26.6. Máy chuẩn: Ryzen 5 5600GT (6 nhân/12 luồng, AVX2, không AVX-512, L3 16 MB, DDR4-3200 hai kênh). Chỉ so tương đối giữa các cách.
**Dữ liệu:** 250.000 vector tổng hợp 1024 chiều (512 cụm + nhiễu, chuẩn hoá L2). 61K là 61.425 dòng đầu. 100 câu hỏi; doc_id gán theo thứ tự cho 3.271 văn bản như kho Zalo. Cosine của kết quả hạng 1 ~0,43, hạng 50 ~0,38, cùng khoảng với ngưỡng `DENSE_MIN = 0,40` của mô hình thật. recall@50 so với tìm chính xác bằng f32. Độ trễ là p50 của top-50, mỗi câu một truy vấn.

**5.1 Tìm vét cạn** (ms; luồng = luồng BLAS hoặc USearch)

| Cách | RAM 61K | 61K, 1 luồng | 61K, 4 luồng | RAM 250K | 250K, 1 luồng | 250K, 4 luồng | recall@50 (61K / 250K) |
|---|---|---|---|---|---|---|---|
| **NumPy f32 (cách app đang làm)** | 240 MB | 19,0 | 3,8 | 977 MB | 77,0 | 26,5 | 1 / 1 |
| NumPy f32 + `argsort` toàn bộ (đúng như `semantic.rerank`) | 240 MB | 19,8 | 4,5 | 977 MB | 80,3 | 27,8 | 1 / 1 |
| NumPy f16 trong RAM, đổi sang f32 theo khối 16K dòng | 120 MB | 145 | 131 | 488 MB | 667 | 633 | 0,9998 / 1 |
| NumPy i8 (thang 127/max\|x\|), đổi sang f32 theo khối | 60 MB | 47 | 45 | 244 MB | 252 | 210 | 0,991 / 0,983 |
| — rồi chấm lại top-200 bằng f16 | 60 + 120 MB | 46 | 56 | 244 + 488 MB | 249 | 225 | 0,9998 / 1 |
| USearch exact f32 | 240 MB | 47 | 13,6 | 977 MB | 194 | 57,7 | 1 / 1 |
| **USearch exact f16** | 120 MB | 28,5 | 8,0 | 488 MB | 118 | 38,0 | 0,9998 / 1 |
| USearch exact i8 (USearch tự đưa về thang ±127) | 60 MB | 17,3 | 5,5 | 244 MB | 73,6 | 29,6 | 0,950 / 0,909 |

Lọc theo 20 văn bản bằng mặt nạ NumPy (như `semantic.rerank`): 18,2 ms (61K) và 76,3 ms (250K) ở 1 luồng, bằng thời gian không lọc vì vẫn nhân cả ma trận.

**5.2 sqlite-vec `vec0`** (bảng `vec0(unit_id, emb float[1024] hoặc int8[1024] distance_metric=cosine, doc_id integer)`, cột `doc_id` là metadata; SQLite chạy 1 luồng; ms)

| Bảng | Cỡ file | Nạp | Không lọc | Lọc 20 văn bản (`doc_id IN`) | Lọc 1 văn bản (`=`) | recall@50 |
|---|---|---|---|---|---|---|
| float, 61K | 242 MB | 13,2 s | 123 | 61 | 59 | 1 |
| int8, 61K | 62 MB | 2,0 s | 125 | 19 | 15 | 0,946 |
| float, 250K | 989 MB | 59,8 s | 521 | 255 | 254 | 1 |
| int8, 250K | 253 MB | 9,3 s | 526 | 88 | 59 | 0,906 |

**5.3 USearch HNSW** (M = 16, `expansion_add` = 128; dựng bằng 4 luồng; truy vấn 1 luồng; ms / recall@50)

| Chỉ mục | Dựng | RAM tăng | ef = 64 | ef = 128 | ef = 256 |
|---|---|---|---|---|---|
| f16, 61K | 13,8 s (1 luồng: 59,7 s) | 137 MB | 0,55 / 0,999 | 0,85 / 0,999 | 2,7 / 0,999 |
| i8, 61K | 9,4 s (1 luồng: 40,2 s) | 75 MB | 0,31 / 0,924 | 0,55 / 0,924 | 1,3 / 0,924 |
| f16, 250K | 57,1 s | 554 MB | 0,82 / 0,918 | 0,87 / 0,986 | 1,14 / 0,999 |
| i8, 250K | 39,4 s | 303 MB | 0,51 / 0,823 | 0,76 / 0,864 | 0,86 / 0,864 |

Đọc kết quả:
- **Phần vector không phải là chỗ chậm.** Mọi cách vét cạn trong RAM đều ≤ 0,2 s ở 250K vector, 1 luồng, trừ hai đường NumPy phải đổi kiểu. Con số đó dưới 2–3% của ~9 s; HNSW chỉ ~1 ms. Chọn CSDL nào cũng không đổi được độ trễ đáng kể.
- **RAM mới là ràng buộc.** f32 ở 250K tốn 977 MB, ở 500K khoảng 1,95 GB (tính). Cộng với hai mô hình thì vượt ngân sách 2–2,5 GB. f16 tốn một nửa. HNSW f16 tốn vector + đồ thị (554 MB ở 250K).
- NumPy không có đường SIMD cho f16/i8, nên đổi kiểu theo khối chậm 3–10 lần so với f32. Muốn giữ f16 trong RAM thì nên dùng USearch exact: ở 61K chậm hơn NumPy f32 khoảng 2 lần khi có 4 luồng (8 so với 3,8 ms) nhưng vẫn dưới 10 ms, và RAM chỉ bằng một nửa.
- **sqlite-vec chậm hơn NumPy f32 6–7 lần** ở 1 luồng (123 so với 19 ms ở 61K; 521 so với 77 ms ở 250K), đổi lại không giữ RAM thường trực (dữ liệu nằm trong page cache của OS). Lọc metadata chỉ làm nhanh ~2 lần với float, 6–9 lần với int8. Chưa thử cột partition key.
- **i8 với thang ±127** (cách mặc định của USearch cho vector đơn vị) mất 5–9% recall@50 khi tìm chính xác và 8–14% với HNSW trên dữ liệu này. Thang theo max|x| giữ được 0,98–0,99; chấm lại top-200 bằng f16 đưa về ~1. Với vector thật phải đo lại.
- HNSW f16 cần `ef` ≥ 256 thì mới giữ recall@50 ≥ 0,999 ở 250K. Với `DENSE_K = 50`, nên đặt `ef` = 256.
- `argsort` toàn bộ trong code hiện tại chỉ thêm ~1–3 ms, không cần sửa.
- **Ước tính cho máy chuẩn:** quét ma trận bị giới hạn bởi băng thông DDR4, khoảng 34–42 GB/s hiệu dụng (`chon-mo-hinh.md` mục 4). Sàn cho 240 MB là ~6–7 ms khi chạy nhiều luồng, cho 977 MB là ~25 ms. Cùng bậc với số sandbox, nên kết luận không đổi. Nhưng ma trận 61K gần như nằm trọn trong L3 260 MiB của sandbox (máy chuẩn chỉ có 16 MB), nên số 61K ở đây có thể lạc quan hơn.
- Script đo nằm ngoài repo, trong scratchpad của phiên soạn: `csdl/bench_vec.py` (đo), `csdl/run_all.sh` (chạy tuần tự), `csdl/results.jsonl` (kết quả từng dòng), `csdl/uoc_tinh_kg.py` (ước tính ở mục 4.5).

## 6. Khuyến nghị (đề xuất cho chủ dự án)

### 6.1 Kho chính: giữ SQLite + FTS5

Lý do:
- Đáp ứng mọi ràng buộc bắt buộc: public domain; có sẵn trong Python Windows nên không thêm byte nào vào bộ cài; WAL cho một luồng ghi và nhiều luồng đọc, đúng như `jobs.py` đang chạy; FTS5 có đủ tính năng mà các tầng khớp cần.
- Mọi bảng mới của 1.0 (lịch sử chat, tag, ghi chú + FTS, `doc_relations`) vào cùng file, cùng giao dịch, cùng cơ chế sao lưu `db.backup_db`, cùng cascade khi xoá văn bản (cổng P2: "không để lại units, vector hay dòng FTS mồ côi").
- Độ chính xác không phụ thuộc CSDL (mục 2.3), và phần CSDL chỉ chiếm ≤ ~1 s trong ~9 s (mục 2.2).
- Mọi ứng viên khác hoặc trái ràng buộc (mục 6.5), hoặc thêm kho thứ hai và buộc viết lại `search.py` mà không có lợi ích đo được.

### 6.2 Vector: thêm theo ngưỡng

Ràng buộc chính là RAM, không phải tốc độ (mục 5). Vì vậy bước đầu là giảm số byte mỗi vector mà vẫn tìm chính xác; chỉ mục HNSW để sau cùng.

| Khi nào (ngưỡng cụ thể) | RAM vector | Làm gì |
|---|---|---|
| Bây giờ: 61K vector | 252 MB (f32) | **Giữ NumPy f32 như hiện tại.** Không bắt buộc đổi gì |
| Ma trận f32 > ~500 MB (≈ 125K vector, khi bắt đầu nhúng theo khoản), hoặc RAM đỉnh Advance đo trên máy chuẩn > 2,5 GB | f16: 244 MB ở 125K, 488 MB ở 250K | f16 trong RAM + **USearch exact** (phương án A ở mục 7). Sandbox ở 250K: 38 ms với 4 luồng, 118 ms với 1 luồng, recall 1. Phải đo trên máy chuẩn trước (mục 6.6) |
| Ma trận f16 > ~500 MB (≈ 250K vector) | i8: 244 MB ở 250K, 488 MB ở 500K | i8 + USearch exact lấy top-200, rồi chấm lại bằng f16 đọc từ `unit_vectors` (phương án A2). Sandbox: i8 exact 74 ms với 1 luồng ở 250K; i8 + chấm lại bằng f16 (đo với NumPy) cho recall 1. Chưa đo USearch i8 + chấm lại |
| Bước tìm vector > ~150 ms p95 trên máy chuẩn. Ngoại suy tuyến tính từ số sandbox, i8 exact với 4 luồng còn ~120 ms ở 1 triệu vector | HNSW f16: 554 MB ở 250K (RAM không giảm) | **USearch HNSW** (M = 16, ef = 256), lưu file `.usearch` cạnh DB (phương án B). File chỉ là cache dựng từ `unit_vectors`: lúc mở app so (số vector, id lớn nhất) như khoá `_ALL` hiện nay, lệch thì dựng lại (sandbox: 57 s ở 250K). Câu hỏi có phạm vi @/# thì tìm chính xác trên tập con, vì USearch Python không lọc trong lúc duyệt đồ thị |

Mỗi bước phải qua quy tắc giữ của lộ trình (mục 5, điều 7: không tụt trên Zalo, gold và văn bản thật), vì f16, i8 và HNSW đều có thể đổi thứ hạng.

### 6.3 sqlite-vec: chưa dùng

sqlite-vec có cái lợi là vector nằm ngay trong SQL và giao dịch. Nhưng bản ổn định chỉ quét toàn bộ và chậm hơn NumPy 6–7 lần (mục 5.2). ANN mới ở bản alpha. Dự án vừa nghỉ 16 tháng mới phát hành lại và ghi rõ là trước v1. Xét lại khi ANN có bản ổn định và có bản phát hành đều đặn; dữ liệu `unit_vectors` không phải đổi.

### 6.4 Quan hệ văn bản (P4) và "đồ thị kiểu Obsidian": bảng SQLite

`doc_relations` như lộ trình mục 7, thêm cột thời gian hai trục và cột nguồn (mục 4.5). Backlinks và đồ thị cục bộ 1–2 bước dùng `WITH RECURSIVE`. Đồ thị ≤ 200 nút là bài toán nhỏ, không cần kho đồ thị. NetworkX chỉ thêm khi thật sự cần thuật toán đồ thị, và phải dùng bản hỗ trợ Python 3.11. LadybugDB (fork của Kùzu, MIT, có wheel Windows) là phương án dự phòng nếu sau này cần Cypher, nhưng hiện không có nhu cầu.

### 6.5 Không chọn

- **Framework đồ thị tri thức** (Cognee, Graphiti, LightRAG, GraphRAG, nano-graphrag, HippoRAG 2, Mem0, LlamaIndex PropertyGraph, neo4j-graphrag): dựng đồ thị mất nhiều tuần tới nhiều tháng CPU; thêm lệnh LLM khi hỏi; cần mô hình lớn hơn; trái lộ trình §10 (mục 4.5). Chỉ lấy ý tưởng.
- **DuckDB:** lưu HNSW xuống đĩa còn là thử nghiệm, có thể hỏng chỉ mục; không thấy phrase/NEAR; extension phải gói sẵn; thiết kế cột (OLAP) không hợp với ghi nhỏ, liên tục.
- **LanceDB:** dùng được, nhưng là kho thứ hai (+110 MB), bỏ dấu mặc định, phải viết lại các tầng khớp; chỉ đáng khi vượt xa 1 triệu vector.
- **Chroma:** full-text chỉ để lọc, không xếp hạng BM25; tìm hybrid chỉ có trên Cloud.
- **Qdrant** (server, local, Edge): server dùng được nhưng thêm tiến trình và kho thứ hai, BM25 mới có từ 22/10/2026; bản local không khuyên dùng quá 20K điểm; bản Edge còn beta.
- **Meilisearch:** bỏ dấu với chữ Latin, exe 337 MB, là server, phần Enterprise theo BUSL.
- **Typesense** (GPL-3.0, Windows chỉ qua WSL), **Weaviate** (asset và bản embedded không có Windows), **Milvus Lite** (làm cho thử nghiệm, IDF theo từng segment, không có float16), **PostgreSQL + pgvector/ParadeDB** (pgvector phải tự build với quyền admin; ParadeDB AGPL, danh sách binary không có Windows), **OpenSearch/Elasticsearch** (JVM nặng; Elasticsearch AGPL/SSPL/ELv2).
- **Tantivy:** chỉ là full-text, không hơn FTS5 mà lại phải tách dữ liệu khỏi SQLite. **txtai:** kéo theo torch. **hnswlib:** chỉ có sdist, ngừng phát hành từ 2023. **FAISS:** dùng được nhưng nặng hơn USearch ~20 lần mà không thêm gì cho bài toán này.
- **Kho đồ thị:** Kùzu (archived 10/10/2025), FalkorDB (SSPL), Memgraph (BSL; Windows qua WSL), ArangoDB (BSL; không còn gói Windows từ 3.12), Neo4j (GPL-3.0, server JVM), Apache AGE (cần PostgreSQL + build), DuckPGQ (dự án nghiên cứu, chưa xác nhận có bản Windows).
- **zvec, libSQL:** zvec còn quá mới (bản đầu 31/12/2025); libSQL buộc thay driver `sqlite3`, gói Python không có bản mới trong 12 tháng.

### 6.6 Rủi ro của đề xuất

- **USearch trên Windows chưa được đo.** Wheel Windows của `numkong` chỉ 0,47 MB, so với 10,1 MB bản Linux, nên có thể có ít nhân SIMD hơn. Phải đo exact f16/i8 trên máy chuẩn trước khi dùng. Nếu chậm, thử FAISS `IndexScalarQuantizer` (fp16 hoặc 8 bit, quét phẳng; wheel 15,5 MB; chưa đo).
- i8 và HNSW đều xấp xỉ, có thể làm tụt Hit@k. Phải chấm lại bằng f16 (i8) hoặc để `ef` cao (HNSW), rồi chạy lại bộ đo.
- Nếu tới bước HNSW, file chỉ mục có thể lệch với SQLite (tắt máy giữa chừng, xoá văn bản). Vì vậy coi nó là cache: kiểm khoá lúc mở app, dựng lại khi lệch, ghi file tạm rồi đổi tên. Hai bước trước không có file nào phải đồng bộ.
- FTS5 không tách từ tiếng Việt. App đã tự nhận cụm từ bằng Python (tên Điều, từ điển); giới hạn này giữ nguyên với mọi CSDL.
- Python 3.11 kèm SQLite 3.45.1 (2024). Bản đó đủ cho FTS5 và cho sqlite-vec (khuyên ≥ 3.41). Thay `sqlite3.dll` lên bản mới là tuỳ chọn, phải chạy lại test.

## 7. Chi phí chuyển đổi

| Phương án | Mã phải đổi | Công (ước tính, 1 người) | Rủi ro |
|---|---|---|---|
| **A. f16 + USearch exact** (khi ma trận f32 > ~500 MB) | `semantic.py`: `_all_vectors` giữ f16 (bỏ `astype(float32)`), `rerank` gọi `usearch.index.search(..., exact=True)` và đổi khoảng cách thành cosine cho `DENSE_MIN`; nhánh `doc_ids` tìm trên tập con. `pyproject.toml` extra `nghia` thêm `usearch`; `pack/SoiLuat.spec` thêm `usearch`, `numkong` vào hidden imports vì `semantic.py` import lười; `tests/test_semantic.py`, `tests/test_pack_spec.py` | 0,5–1 ngày + chạy lại Zalo/gold | thứ hạng có thể đổi khi điểm bằng nhau |
| **A2. i8 exact + chấm lại** (khi ma trận f16 > ~500 MB) | A + giữ i8 thay cho f16; lấy top-200 rồi đọc f16 của 200 Điều đó từ `unit_vectors` (một truy vấn `json_each`) để chấm lại | +0,5 ngày + đo | recall của i8 trên vector thật |
| **B. USearch HNSW lưu file** (khi bước tìm vector > ~150 ms p95) | A + dựng/lưu/nạp chỉ mục; `jobs._embed_chunk` thêm vector mới vào chỉ mục; xoá văn bản (P2) gọi `remove`; kiểm khoá lúc mở app; test | 2–4 ngày + đo trên máy chuẩn | recall; đồng bộ file |
| C. sqlite-vec | `db.connect` nạp extension; `schema.sql` thêm bảng `vec0` và đồng bộ với `unit_vectors`; viết lại phần tìm của `semantic.py` bằng SQL; gói DLL | 2–3 ngày | chậm hơn 6–7 lần; API trước v1 |
| D. Thay cả kho (LanceDB, Qdrant, DuckDB…) | Viết lại mọi chỗ dùng cú pháp FTS5 trong `search.py`: `fts_quote`, `_fts_term`, `fts_phrase`, `fts_and`, `fts_near`, `scored_units` (lọc cột `{search_accent context_accent}`, `bm25()` có trọng số, `json_each`), `_token_df`/`_or_terms` (fts5vocab), `_ocr_unit_ids`; trigger trong `schema.sql`; ghi hai kho trong `ingest.py`/`rebuild.py`; sao lưu, xoá cascade; chuyển 1,5 GB dữ liệu; chỉnh lại BM25 và hệ số tầng | nhiều tuần, cộng thêm 15–340 MB bộ cài | độ chính xác dự kiến không tăng; có thể tụt cho tới khi chỉnh lại xong |
| E. P4 trên SQLite | bảng `doc_relations` (đã có trong lộ trình) + cột thời gian + truy vấn CTE | nằm trong P4 | không thêm phụ thuộc |

## 8. Chưa kiểm được

- **Chưa đo gì trên máy chuẩn.** Sandbox có AVX-512 và L3 260 MiB, nên tìm vét cạn ở đây có thể nhanh hơn tương đối so với 5600GT. Phải đo lại 5.1–5.3 trên máy 16 GB (Office đang mở), nhất là USearch bản Windows.
- **Vector tổng hợp, không phải AITeamVN thật.** recall của HNSW và i8 trên vector thật chưa biết. Phải đo trên `unit_vectors` của kho Zalo bằng Hit@k, không chỉ recall.
- **Chưa tách thời gian của một câu Advance.** Mới biết reranker ~5 s trong ~9 s; nhúng câu hỏi, SQL lấy chữ và dựng thẻ chưa đo riêng. Cần đặt timer từng bước trong `search._fts_cascade`.
- **Mục 4.5 là ước tính.** Tốc độ LLM chưa đo (`chon-mo-hinh.md` mục 6). Số token ra, số cạnh mỗi Điều và số cộng đồng của GraphRAG là giả định. Cỡ prompt đếm thô bằng số ký tự / 4.
- Chưa tìm thấy benchmark trích thực thể–quan hệ tiếng Việt nào cho Qwen3-VL-4B, hay cho mô hình ≤ 5B nói chung (29/10/2026).
- Tài liệu Cognee không nói rõ bộ trích `gliner_demo` có trích quan hệ hay chỉ trích thực thể.
- DuckPGQ: chưa xác nhận giấy phép và bản Windows (bảng tương thích trống). libSQL: tài liệu không nói chỉ mục vector có chạy trên file cục bộ không. zvec: không thấy tài liệu về phrase và tiếng Việt. Qdrant Edge: tài liệu không nêu hệ điều hành và các tính năng còn thiếu.
- Meilisearch: không thấy cách tắt việc bỏ dấu cho chữ Latin.
- Chưa đo RAM và đĩa của LanceDB, DuckDB, Qdrant, Chroma… trên kho thật. Bảng 4.1 chỉ ghi yêu cầu theo tài liệu: chỉ mục HNSW của DuckDB phải nằm trọn trong RAM; OpenSearch khuyên heap khởi điểm bằng nửa RAM máy; Neo4j tối thiểu 2 GB.
- Chưa đo dung lượng OpenSearch/Elasticsearch/PostgreSQL khi đóng gói; chưa kiểm bộ cài EDB có kèm pgvector dựng sẵn không.
- sqlite-vec: chưa thử cột partition key, chưa thử bản 0.1.10-alpha (ANN).
- Giấy phép: phần 4.3 chỉ mô tả chung về copyleft, không phải ý kiến pháp lý.
