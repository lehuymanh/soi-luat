"""Xếp hạng theo nghĩa bằng AITeamVN Vietnamese_Embedding (ONNX int8, CPU).

Chế độ "advance" (chọn trên Search App, lưu trong app_meta); "normal" (mặc định), thiếu mô hình,
thiếu onnxruntime/tokenizers/numpy, hoặc SOILUAT_SEMANTIC=0 → tìm như cũ (BM25), không nạp mô hình.
Vector tính một lần cho mỗi Điều (đơn vị gốc, parent_id IS NULL) bằng `soiluat-importer --nhung`;
khi tìm chỉ nhúng câu hỏi rồi hợp TOP Điều đầu của BM25 với DENSE_K Điều gần nghĩa nhất TOÀN KHO,
điểm = 1/(RRF_K + hạng BM25) + W/(RRF_K + hạng theo nghĩa trên toàn kho).
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
import threading
import time
from pathlib import Path

from soiluat.config import data_dir

MODEL_NAME = "aiteamvn-embedding-int8-1024-len128"  # đổi MAXLEN/DIM/mô hình thì đổi tên: vector cũ không trộn với mới
DIM = 1024  # AITeamVN Vietnamese_Embedding (bge-m3): CLS, chuẩn hoá L2
MAXLEN = 128  # token; độ dài mà mọi số đo của Advance dùng
THREADS = 2  # máy văn phòng: chừa CPU cho Office
TOP = 20  # số Điều đầu của BM25 đưa vào hợp (N)
DENSE_K = 50  # số Điều gần nghĩa nhất toàn kho đưa vào hợp (M), cả khi không chung chữ nào
RRF_K = 5
W = 2.0  # trọng số hạng theo nghĩa; (N, M, k, w) = (20, 50, 5, 2) chọn trên tập riêng, ngoài bộ đo
# cosine tối thiểu của Điều chỉ có nhờ vector (BM25 không tìm ra): chặn kết quả bịa cho câu vô nghĩa.
# Riêng cho MODEL_NAME này: đổi mô hình thì đo lại. Đo trên 1.200 câu chỉnh (ngoài bộ đo): 0,40 không làm Hit@10
# tụt (92,5 / 96,3 so với 92,2 / 96,5 khi không ngưỡng), chặn 29/30 câu vô nghĩa hoặc ngoài đề; 0,45 làm Hit@10 tụt ~0,7.
DENSE_MIN = 0.40
Q_PRE = ""
D_PRE = "{t}\n"
ONNX_FILE = "model_int8.onnx"


def model_dir() -> Path:
    raw = os.environ.get("SOILUAT_MODEL_DIR")
    if raw:
        return Path(raw)
    path = data_dir() / "models" / "aiteamvn-embedding"
    if not path.exists() and getattr(sys, "frozen", False):  # bản đóng gói: models\ nằm cạnh SoiLuat.exe
        return Path(sys.executable).resolve().parent / "models" / "aiteamvn-embedding"
    return path


class Encoder:
    def __init__(self, path: Path, threads: int | None = None):
        threads = threads or THREADS  # đọc lúc gọi: --nen đặt THREADS = 1 trước khi nạp
        import numpy as np
        import onnxruntime as ort
        from tokenizers import Tokenizer

        self.np = np
        so = ort.SessionOptions()
        so.intra_op_num_threads = threads
        so.inter_op_num_threads = 1
        so.enable_cpu_mem_arena = False  # bật: RAM giữ thêm sau lần chạy đầu; tắt: gọn hơn, chậm không đáng kể
        so.enable_mem_pattern = False
        self.sess = ort.InferenceSession(str(path / "onnx" / ONNX_FILE), so,
                                         providers=["CPUExecutionProvider"])
        self.tok = Tokenizer.from_file(str(path / "tokenizer.json"))
        self.tok.enable_truncation(MAXLEN)

    def encode(self, texts: list[str], batch: int = 8):
        np = self.np
        enc = self.tok.encode_batch(texts)
        order = np.argsort([len(e.ids) for e in enc])  # gom câu cùng độ dài: ít đệm
        out = np.zeros((len(texts), DIM), np.float32)
        for b in range(0, len(texts), batch):
            idx = order[b:b + batch]
            n = max(len(enc[i].ids) for i in idx)
            ids = np.zeros((len(idx), n), np.int64)
            mask = np.zeros((len(idx), n), np.int64)
            for r, i in enumerate(idx):
                ids[r, :len(enc[i].ids)] = enc[i].ids
                mask[r, :len(enc[i].ids)] = 1
            v = self.sess.run(["sentence_embedding"], {"input_ids": ids, "attention_mask": mask})[0][:, :DIM]
            out[idx] = v / np.linalg.norm(v, axis=1, keepdims=True)
        return out


MODES = ("normal", "advance")  # normal: BM25 thuần; advance: BM25 + xếp lại theo nghĩa


def get_mode(conn: sqlite3.Connection) -> str:
    r = conn.execute("SELECT value FROM app_meta WHERE key = 'search_mode'").fetchone()
    return r[0] if r and r[0] in MODES else "normal"  # mặc định normal: máy yếu không nạp mô hình


def set_mode(conn: sqlite3.Connection, mode: str) -> None:
    if mode not in MODES:
        raise ValueError(mode)
    with conn:
        conn.execute("INSERT OR REPLACE INTO app_meta(key, value) VALUES ('search_mode', ?)", (mode,))


def model_installed() -> bool:
    path = model_dir()
    return (path / "onnx" / ONNX_FILE).exists() and (path / "tokenizer.json").exists()


def lower_priority() -> None:
    """Chạy nền: mức ưu tiên CPU thấp nhất, không tranh với Word/Excel đang mở."""
    try:
        if os.name == "nt":
            import ctypes

            k = ctypes.windll.kernel32
            k.SetPriorityClass(k.GetCurrentProcess(), 0x00000040)  # IDLE_PRIORITY_CLASS
        else:
            os.nice(19)
    except Exception:  # noqa: BLE001 — không hạ được thì vẫn chạy, chỉ là không nhường
        pass


def pending(conn: sqlite3.Connection) -> int:
    """Số Điều gốc chưa có vector (chỉ có nghĩa khi mô hình đã cài)."""
    return conn.execute(
        "SELECT COUNT(*) FROM units u LEFT JOIN unit_vectors v ON v.unit_id = u.id AND v.model = ?"
        " WHERE u.parent_id IS NULL AND v.unit_id IS NULL", (MODEL_NAME,)).fetchone()[0]


_ENC: Encoder | None = None
_ENC_TRIED = False


def encoder() -> Encoder | None:
    """Nạp mô hình lần đầu cần dùng; lỗi/thiếu thì None (một lần mỗi process)."""
    global _ENC, _ENC_TRIED
    if os.environ.get("SOILUAT_SEMANTIC") == "0":
        return None
    if not _ENC_TRIED:
        _ENC_TRIED = True
        if model_installed():
            try:
                _ENC = Encoder(model_dir())
            except Exception:  # noqa: BLE001 — thiếu thư viện / mô hình hỏng: tìm như cũ
                _ENC = None
    return _ENC


def root_ids(conn: sqlite3.Connection, unit_ids: list[int]) -> dict[int, int]:
    """unit → Điều (hoặc đoạn) gốc chứa nó: gốc là chính nó, con lấy theo tiền tố đường dẫn 'D3.K1' → 'D3'
    (đoạn có đường dẫn 'p1.para1' nhưng không có cha nên không cắt)."""
    rows = conn.execute(
        """SELECT u.id, CASE WHEN u.parent_id IS NULL THEN u.id ELSE r.id END FROM units u
           LEFT JOIN units r ON u.parent_id IS NOT NULL AND r.doc_id = u.doc_id AND r.parent_id IS NULL
            AND r.path = substr(u.path, 1, instr(u.path, '.') - 1)
           WHERE u.id IN (SELECT value FROM json_each(?))""",
        (json.dumps(unit_ids),),
    ).fetchall()
    return {r[0]: r[1] for r in rows if r[1] is not None}


def _marker(path: str) -> str:
    """Số khoản / chữ điểm dựng lại từ đường dẫn: 'D3.K1' → '1.', 'D3.K1.Đa' → 'a)'."""
    seg = path.rsplit(".", 1)[-1]
    return seg[1:] + "." if seg.startswith("K") else seg[1:] + ")" if seg.startswith("Đ") else ""


def root_lines(conn: sqlite3.Connection, root_id: int) -> tuple[str, list[tuple[str, str]]]:
    """(tiêu đề, [(đường dẫn, dòng)]) của Điều gốc theo dạng văn bản luật mà mô hình đã được đo: 'Điều 3. Tên Điều' rồi
    từng khoản, điểm kèm số/chữ ('1.', 'a)') mỗi dòng một đơn vị. App tách số điều và số khoản khỏi chữ, nên dựng lại ở đây."""
    r = conn.execute("SELECT doc_id, path, level, title, COALESCE(reviewed_text, normalized_text) FROM units WHERE id = ?",
                     (root_id,)).fetchone()
    title = (r[3] or "").strip()
    m = re.match(r"^D(\d+[a-z]?)$", r[1] or "", re.I) if r[2] == "dieu" else None
    head = f"Điều {m.group(1)}. {title}" if m else title
    lines = [(p, f"{_marker(p)} {t}".strip()) for p, t in conn.execute(
        "SELECT path, COALESCE(reviewed_text, normalized_text) FROM units WHERE doc_id = ? AND path LIKE ? ORDER BY id",
        (r[0], r[1] + ".%")) if t]
    own = (r[4] or "").strip()
    if own and own != title:  # Điều có nội dung ngay dưới tên (đoạn mở đầu, hoặc không chia khoản)
        lines.insert(0, (r[1], own))
    return head, lines


def root_parts(conn: sqlite3.Connection, root_id: int) -> tuple[str, str]:
    """(tiêu đề, nội dung) của Điều gốc: như `root_lines`, các dòng nối bằng xuống dòng."""
    head, lines = root_lines(conn, root_id)
    return head, "\n".join(t for _, t in lines)


def root_text(conn: sqlite3.Connection, root_id: int) -> str:
    title, body = root_parts(conn, root_id)
    return D_PRE.format(t=title or "none") + body


def missing_roots(conn: sqlite3.Connection) -> list[int]:
    return [r[0] for r in conn.execute(
        "SELECT u.id FROM units u LEFT JOIN unit_vectors v ON v.unit_id = u.id AND v.model = ?"
        " WHERE u.parent_id IS NULL AND v.unit_id IS NULL ORDER BY u.id", (MODEL_NAME,))]


def embed_roots(conn: sqlite3.Connection, enc: Encoder, ids: list[int], *, chunk: int = 64,
                progress=None) -> float:
    """Nhúng và lưu vector cho các Điều gốc; trả số giây. Ghi theo từng khối: dừng giữa chừng không mất phần đã xong."""
    t0 = time.perf_counter()
    for b in range(0, len(ids), chunk):
        part = ids[b:b + chunk]
        vecs = enc.encode([root_text(conn, i) for i in part])
        with conn:
            conn.executemany(
                "INSERT OR REPLACE INTO unit_vectors(unit_id, model, vec) VALUES (?, ?, ?)",
                [(i, MODEL_NAME, v.astype("float16").tobytes()) for i, v in zip(part, vecs)])
        if progress:
            progress(b + len(part), len(ids), time.perf_counter() - t0)
    return time.perf_counter() - t0


_ALL: dict = {}  # ma trận vector toàn kho, nạp lại khi (file db, số vector, id lớn nhất) đổi
_ALL_LOCK = threading.Lock()  # một luồng nạp, luồng khác chờ rồi dùng chung (ba bản song song ≈ 1,65 GB ở kho Zalo)


def _vec_rows(conn: sqlite3.Connection, after: int):
    return conn.execute("SELECT v.unit_id, u.doc_id, v.vec FROM unit_vectors v JOIN units u ON u.id = v.unit_id"
                        " WHERE v.model = ? AND v.unit_id > ? ORDER BY v.unit_id", (MODEL_NAME, after)).fetchall()


def _all_vectors(conn: sqlite3.Connection, np):
    """(id gốc, doc_id, ma trận float32) của mọi gốc đã nhúng. Kho Zalo 61 nghìn Điều × 1024 ≈ 252 MB RAM."""
    from soiluat.jobs import JOBS  # nạp chậm: jobs import semantic

    db = conn.execute("PRAGMA database_list").fetchone()[2]
    key = (db, *conn.execute("SELECT COUNT(*), MAX(unit_id) FROM unit_vectors WHERE model = ?",
                             (MODEL_NAME,)).fetchone())
    with _ALL_LOCK:
        old = _ALL.get("key")
        if old != key:
            same = old is not None and old[0] == db
            if same and JOBS.migrate["running"]:
                pass  # đang nâng cấp: mỗi văn bản dựng lại đổi khoá; dùng ma trận cũ (rerank bỏ Điều đã mất), nạp lại khi xong
            else:
                # nhúng nền chỉ thêm hàng mới có id lớn hơn: chỉ nối thêm khi đúng như vậy, không thì nạp lại cả ma trận
                rows = _vec_rows(conn, old[2]) if same else []
                grow = bool(rows) and old[1] + len(rows) == key[1] and rows[-1][0] == key[2]
                if not grow:
                    rows = _vec_rows(conn, -1)
                mat = np.frombuffer(b"".join(r[2] for r in rows), np.float16).reshape(len(rows), -1).astype(np.float32)
                ids, docs = np.array([r[0] for r in rows]), np.array([r[1] for r in rows])
                if grow:
                    ids, docs, mat = (np.concatenate([_ALL[k], v]) for k, v in (("ids", ids), ("docs", docs), ("mat", mat)))
                _ALL.update(key=key, ids=ids, docs=docs, mat=mat)
        return _ALL["ids"], _ALL["docs"], _ALL["mat"]


def warm(conn: sqlite3.Connection) -> None:
    """Nạp trước mô hình và ma trận vector (câu hỏi đầu tiên không phải gánh ~1 phút nạp). Gọi nền khi app khởi động."""
    if get_mode(conn) == "advance" and encoder() is not None:
        import numpy as np

        _all_vectors(conn, np)


def rerank(conn: sqlite3.Connection, query: str, ids: list[int], doc_ids: list[int] | None = None) -> list[int]:
    """Hợp TOP Điều đầu của BM25 với DENSE_K Điều gần nghĩa nhất toàn kho (trong doc_ids nếu có), xếp theo
    1/(RRF_K + hạng BM25) + W/(RRF_K + hạng theo nghĩa toàn kho). Điều chưa có vector (văn bản mới nạp, đang nhúng nền)
    lấy hạng theo nghĩa = hạng BM25, không bị phạt. Điều chỉ có nhờ vector phải đạt DENSE_MIN."""
    if get_mode(conn) != "advance":
        return ids
    if not conn.execute("SELECT 1 FROM unit_vectors WHERE model = ? LIMIT 1", (MODEL_NAME,)).fetchone():
        return ids  # chưa có vector nào: khỏi nạp mô hình (~0,6–1,3 GB RAM)
    enc = encoder()
    if enc is None:
        return ids
    np = enc.np
    roots = root_ids(conn, ids)
    order = list(dict.fromkeys(roots.get(i, -i) for i in ids))  # đơn vị không tìm được gốc: tự làm gốc
    top = order[:TOP]
    bm = {r: b for b, r in enumerate(order, 1)}
    all_ids, all_docs, mat = _all_vectors(conn, np)
    sim_all = mat @ enc.encode([Q_PRE + query])[0]
    ok = np.isin(all_docs, doc_ids) if doc_ids else np.ones(len(all_ids), bool)
    best = [int(all_ids[k]) for k in np.argsort(-np.where(ok, sim_all, -np.inf))[:DENSE_K] if ok[k]]
    alive = {r[0] for r in conn.execute("SELECT id FROM units WHERE id IN (SELECT value FROM json_each(?))",
                                        (json.dumps(best),))}
    best = [r for r in best if r in alive]  # ma trận cũ dùng lúc nâng cấp còn Điều đã bị dựng lại
    dense = {r: k for k, r in enumerate(best, 1)}
    have = {int(r) for r in all_ids}
    score = {}
    for r in top:
        d = dense.get(r) if r in have else bm[r]
        score[r] = 1 / (RRF_K + bm[r]) + (W / (RRF_K + d) if d else 0)
    row = {int(r): k for k, r in enumerate(all_ids)}
    for r, k in dense.items():
        if r not in score and sim_all[row[r]] >= DENSE_MIN:  # chỉ có nhờ vector (BM25 không đưa vào hợp)
            score[r] = W / (RRF_K + k)
    head = sorted(score, key=lambda r: (-score[r], bm.get(r, len(bm) + 1)))
    pos = {r: k for k, r in enumerate(head + [r for r in order[TOP:] if r not in score])}
    new = [r for r in score if r not in bm]  # gốc là chính đơn vị Điều/đoạn nên dùng thẳng làm id
    roots.update((r, r) for r in new)
    return sorted(ids + new, key=lambda i: pos[roots.get(i, -i)])  # sorted ổn định: giữ thứ tự BM25 trong một Điều
