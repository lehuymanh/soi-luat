"""Trợ lý trả lời (lộ trình 1.0: P0 đo bằng `bench/llm/run.py`, P3 gắn vào app).

Dựng ngữ cảnh 3–5 Điều từ kho, gọi `llama-server` (API kiểu OpenAI) với JSON schema, rồi kiểm lại: nguồn phải là
đoạn đã đưa vào, mọi con số phải có trong đoạn được dẫn (lộ trình mục 5, điều 1–3). Nguyên văn hiển thị cho người
dùng luôn lấy từ `units`, không lấy từ mô hình.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import urllib.request
from dataclasses import dataclass, field
from decimal import Decimal

from soiluat import semantic
from soiluat.fold import fold_search

MAX_PASSAGES = 5
CTX_CHARS = 3000  # thân đoạn; cộng tiêu đề, câu hỏi ≈ 1.000 token Qwen3-VL mới mỗi câu (đo trên Zalo, bench/llm)
N_PREDICT = 200
TEMPERATURE = 0.1  # thấp cho bám đoạn; chốt ở P0
SEED = 2026

SYSTEM = """Bạn là trợ lý tra cứu văn bản pháp luật Việt Nam. Người hỏi là nhân viên văn phòng, không phải luật sư.
Chỉ dùng các đoạn [1], [2]… trong tin nhắn; không dùng kiến thức bên ngoài, không đoán.

Trả về JSON:
- "du_can_cu": true nếu có đoạn nói về đúng điều được hỏi, kể cả khi câu hỏi nêu sai một chi tiết; false nếu không đoạn nào nói về điều đó.
- "tien_de_sai": câu hỏi nêu sai so với đoạn (sai mức phạt, sai thời hạn, sai đối tượng…) thì ghi điều đúng theo đoạn, ví dụ "Mức phạt là từ 1.000.000 đồng đến 2.000.000 đồng, không phải 5.000.000 đồng."; câu hỏi không nêu chi tiết nào sai (phần lớn câu hỏi) thì "".
- "tra_loi": tối đa 3 câu, lời thường, trả lời thẳng câu hỏi. Khi du_can_cu là false: nói các đoạn không có căn cứ.
- "cac_y": khi du_can_cu là true, 1–3 ý ngắn; "nguon" của mỗi ý là số thứ tự các đoạn làm căn cứ. Khi false thì [].
- "luu_y": ngoại lệ, điều kiện áp dụng, chỗ các đoạn nói khác nhau; không có thì [].

Con số (số tiền, số ngày, tỉ lệ, ngày tháng, số Điều, khoản) chép đúng như trong đoạn. Không tự kết luận văn bản còn hay hết hiệu lực. Chỉ viết tiếng Việt."""

HIEU_LUC = {"con": "còn hiệu lực", "het": "hết hiệu lực"}  # 'chua_ro' không ghi: tốn token, không giúp trả lời
STOP = frozenset(
    "cua va la thi co khong duoc cac nhung trong cho voi nay do theo khi ve nguoi bi mot de tai neu hoac phai "
    "bao nhieu gi nao the ra sao nhu".split()
)


@dataclass
class Passage:
    n: int  # mã [n] đưa cho mô hình
    root_id: int  # Điều (hoặc đoạn) gốc trong units
    doc_id: int
    label: str  # số hiệu, không có thì tên file
    head: str  # 'Điều 5. Tên Điều'
    text: str  # các khoản/điểm đã chọn, mỗi dòng một đơn vị
    meta: str = ""  # 'ban hành 2020-02-03; còn hiệu lực'

    def render(self) -> str:
        top = f"[{self.n}] {self.label} — {self.head}".rstrip(" —")
        return "\n".join(x for x in (top, f"({self.meta})" if self.meta else "", self.text) if x)


def roots_in_order(conn: sqlite3.Connection, unit_ids: list[int]) -> list[int]:
    """Điều gốc theo thứ tự kết quả tìm (khoản/điểm đi theo Điều của chúng), không trùng."""
    roots = semantic.root_ids(conn, unit_ids)
    return list(dict.fromkeys(roots[i] for i in unit_ids if i in roots))


def content_sig(conn: sqlite3.Connection, root_id: int) -> str:
    """Khoá nội dung của Điều (chữ các khoản/điểm, bỏ dấu, không kèm số Điều): cùng khoá là cùng nội dung, kể cả ở hai
    văn bản khác nhau (lộ trình P1, gộp trùng)."""
    head, lines = semantic.root_lines(conn, root_id)
    body = " ".join(t for _, t in lines) or head
    return hashlib.sha1(" ".join(fold_search(body).split()).encode()).hexdigest()


def unique_roots(conn: sqlite3.Connection, roots: list[int], limit: int) -> list[int]:
    """`limit` Điều đầu, bỏ Điều trùng nội dung với Điều xếp trên (chép y nguyên ở văn bản khác)."""
    seen: set[str] = set()
    out = []
    for r in roots:
        sig = content_sig(conn, r)
        if sig not in seen:
            seen.add(sig)
            out.append(r)
            if len(out) == limit:
                break
    return out


def _words(text: str) -> list[str]:
    return [w for w in re.findall(r"\w+", fold_search(text)) if w not in STOP]


def _pick(lines: list[tuple[str, str]], query: str, budget: int) -> str:
    """Giữ dòng khớp câu hỏi nhất và dòng liền kề, theo thứ tự gốc, trong `budget` ký tự. Dòng nào được giữ thì giữ cả
    câu dẫn của nó (điểm 'b) Làm giả…' kéo theo khoản '2. Phạt tiền từ … đối với các hành vi sau'): mất câu dẫn là mất
    mức phạt."""
    texts = [t for _, t in lines]
    if sum(len(t) + 1 for t in texts) <= budget:
        return "\n".join(texts)
    q = _words(query)
    qs, qb = set(q), set(zip(q, q[1:]))

    def score(line: str) -> int:
        w = _words(line)
        return len(qs & set(w)) + 2 * len(qb & set(zip(w, w[1:])))

    at = {p: i for i, (p, _) in enumerate(lines)}
    keep: set[int] = set()

    def with_parents(i: int) -> list[int]:
        out, p = [i], lines[i][0]
        while "." in p:
            p = p.rsplit(".", 1)[0]
            if p in at:
                out.append(at[p])
        return [j for j in out if j not in keep]

    ranked = sorted(range(len(texts)), key=lambda i: (-score(texts[i]), i))
    used = 0
    for i in ranked:
        for j in (i, i - 1, i + 1):
            if 0 <= j < len(texts):
                group = with_parents(j)
                cost = sum(len(texts[k]) + 1 for k in group)
                if group and used + cost <= budget:
                    keep.update(group)
                    used += cost
    if not keep:  # một dòng đã dài hơn ngân sách: cắt dòng khớp nhất
        return texts[ranked[0]][: max(budget - 1, 0)] + "…"
    out, prev = [], None
    for j in sorted(keep):
        if prev is not None and j > prev + 1:
            out.append("…")
        out.append(texts[j])
        prev = j
    return "\n".join(out)


def _shares(lengths: list[int], budget: int) -> list[int]:
    """Chia ngân sách: đoạn ngắn lấy đủ, phần dư chia đều cho đoạn dài."""
    share = [0] * len(lengths)
    rest = sorted(range(len(lengths)), key=lambda i: lengths[i])
    left = budget
    while rest:
        fair = left // len(rest)
        if lengths[rest[0]] > fair:
            for i in rest:
                share[i] = fair
            break
        i = rest.pop(0)
        share[i] = lengths[i]
        left -= lengths[i]
    return share


def _meta(doc: sqlite3.Row) -> str:
    bits = [f"ban hành {doc['ngay_ban_hanh']}" if doc["ngay_ban_hanh"] else "", HIEU_LUC.get(doc["hieu_luc"] or "", "")]
    return "; ".join(b for b in bits if b)


def build_context(
    conn: sqlite3.Connection, roots: list[int], query: str, *, max_passages: int = MAX_PASSAGES, budget: int = CTX_CHARS
) -> list[Passage]:
    """Đoạn [1]…[n] từ các Điều gốc (đã xếp hạng, bỏ Điều trùng nội dung); tổng chữ thân đoạn ≤ `budget` ký tự."""
    parts = []
    for rid in unique_roots(conn, roots, max_passages):
        head, lines = semantic.root_lines(conn, rid)
        doc = conn.execute(
            "SELECT d.id, d.so_hieu, d.file_path, d.ngay_ban_hanh, d.hieu_luc FROM documents d"
            " JOIN units u ON u.doc_id = d.id WHERE u.id = ?",
            (rid,),
        ).fetchone()
        label = doc["so_hieu"] or doc["file_path"].replace("\\", "/").rsplit("/", 1)[-1]
        parts.append((rid, doc, label, head, [(p, t) for p, t in lines if t.strip()]))
    shares = _shares([sum(len(t) + 1 for _, t in p[4]) for p in parts], budget)
    return [
        Passage(k, rid, doc["id"], label, head, _pick(lines, query, share), _meta(doc))
        for k, ((rid, doc, label, head, lines), share) in enumerate(zip(parts, shares), 1)
    ]


def messages(passages: list[Passage], question: str) -> list[dict]:
    ctx = "\n\n".join(p.render() for p in passages)
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": f"Các đoạn:\n\n{ctx}\n\nCâu hỏi: {question}"}]


def schema(n: int) -> dict:
    """Khuôn trả lời; `nguon` là enum gồm đúng các mã đã đưa vào. Hai nhánh theo cờ: đủ căn cứ thì phải có 1–3 ý có
    nguồn, không đủ thì không có ý nào. Cờ và tiền đề sai đứng trước câu trả lời để mô hình quyết định trước khi viết
    (thứ tự thuộc tính là thứ tự sinh)."""
    src = {"type": "integer", "enum": list(range(1, n + 1))}
    y = {
        "type": "object",
        "properties": {"y": {"type": "string"}, "nguon": {"type": "array", "items": src, "minItems": 1, "maxItems": n}},
        "required": ["y", "nguon"],
        "additionalProperties": False,
    }

    def branch(ok: bool) -> dict:
        props = {
            "du_can_cu": {"const": ok},
            "tien_de_sai": {"type": "string"},
            "tra_loi": {"type": "string"},
            "cac_y": {"type": "array", "items": y, "minItems": 1, "maxItems": 3} if ok else {"type": "array", "items": y, "maxItems": 0},
            "luu_y": {"type": "array", "maxItems": 2, "items": {"type": "string"}},
        }
        return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}

    return {"anyOf": [branch(True), branch(False)]}


def chat(
    url: str,
    msgs: list[dict],
    fmt: dict,
    *,
    api_key: str = "",
    n_predict: int = N_PREDICT,
    temperature: float = TEMPERATURE,
    timeout: float = 300.0,
) -> dict:
    """Một lượt /v1/chat/completions của llama-server. Không qua proxy: máy chủ mô hình chỉ ở 127.0.0.1."""
    body = {
        "messages": msgs,
        "max_tokens": n_predict,
        "temperature": temperature,
        "seed": SEED,
        "cache_prompt": True,
        "response_format": {"type": "json_object", "schema": fmt},
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(url.rstrip("/") + "/v1/chat/completions", json.dumps(body).encode(), headers)
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=timeout) as r:
        return json.load(r)


# --- Kiểm số liệu -------------------------------------------------------------------------------------------------

CJK = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af\uf900-\ufaff]")
_SO_HIEU = re.compile(r"\b\d+(?:/\d{4})?/[A-Za-zĐđ][\wĐđ]*(?:-[\wĐđ]+)*")
_DATE = re.compile(
    r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b|ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})|\b(\d{4})-(\d{2})-(\d{2})\b",
    re.IGNORECASE,
)
_NUM = re.compile(r"(?<![\w.,])(\d{1,3}(?:\.\d{3})+(?!\.?\d)|\d+)(?:,(\d+))?(?:\s*(nghìn|ngàn|triệu|tỷ|tỉ)(?!\w))?", re.IGNORECASE)
_RANGE_GAP = re.compile(r"\s*(?:-|–|—|đến|tới)\s*", re.IGNORECASE)
_MULT = {"nghìn": 10**3, "ngàn": 10**3, "triệu": 10**6, "tỷ": 10**9, "tỉ": 10**9}


def numbers(text: str, *, lenient: bool = False) -> set:
    """Các con số trong câu theo giá trị: '5.000.000 đồng' = '5 triệu đồng'; '1–2 triệu' = {1e6, 2e6}; ngày viết số
    hay viết chữ như nhau; số hiệu so sau khi bỏ dấu. `lenient` (phía nguồn) thêm cả số trần của khoảng và các số trong
    số hiệu, để câu trả lời viết '1 đến 2 triệu' hay 'Nghị định 15 năm 2020' vẫn khớp.
    shortcut: số viết bằng chữ ('ba mươi ngày') không bắt; nâng cấp nếu bộ đo thấy mô hình hay viết vậy."""
    out: set = set()
    for m in _SO_HIEU.finditer(text):
        out.add(fold_search(m.group(0)))
        if lenient:
            out.update(Decimal(x) for x in re.findall(r"\d+", m.group(0)))
    text = _SO_HIEU.sub(" ", text)
    for m in _DATE.finditer(text):
        if m.group(7):
            y, mo, d = (int(x) for x in m.group(7, 8, 9))
        else:
            d, mo, y = (int(x) for x in (m.group(1, 2, 3) if m.group(1) else m.group(4, 5, 6)))
        out.add(f"{d}/{mo}/{y}")
    text = _DATE.sub(" ", text)
    found = list(_NUM.finditer(text))
    for i, m in enumerate(found):
        v = Decimal(m.group(1).replace(".", "") + ("." + m.group(2) if m.group(2) else ""))
        unit = (m.group(3) or "").lower()
        if not unit and i + 1 < len(found) and found[i + 1].group(3):
            if _RANGE_GAP.fullmatch(text[m.end() : found[i + 1].start()]):
                if lenient:
                    out.add(v)
                unit = found[i + 1].group(3).lower()
        out.add(v * _MULT[unit] if unit else v)
    return out


@dataclass
class Checked:
    answer: dict  # câu trả lời đã kiểm: bỏ ý sai nguồn/số, thay câu trả lời khi có số lạ
    json_ok: bool
    dropped: list[str] = field(default_factory=list)  # mỗi phần không qua kiểm: 'cac_y:so', 'tra_loi:cjk'…
    replaced: bool = False  # tra_loi đã thay bằng trích nguyên văn


def _shape_ok(a) -> bool:
    return (
        isinstance(a, dict)
        and isinstance(a.get("du_can_cu"), bool)
        and isinstance(a.get("tien_de_sai"), str)
        and isinstance(a.get("tra_loi"), str)
        and isinstance(a.get("luu_y"), list)
        and all(isinstance(x, str) for x in a["luu_y"])
        and isinstance(a.get("cac_y"), list)
        and all(
            isinstance(y, dict) and isinstance(y.get("y"), str) and isinstance(y.get("nguon"), list) for y in a["cac_y"]
        )
    )


def extractive(passages: list[Passage]) -> str:
    """Câu thay thế khi không tin được chữ mô hình: câu đầu của đoạn [1], nguyên văn."""
    if not passages:
        return "Không tìm thấy căn cứ trong kho."
    first = passages[0].text.split("\n", 1)[0]
    return f"Trích nguyên văn {passages[0].head or passages[0].label}: {first[:300]}"


def check(content: str, passages: list[Passage], question: str) -> Checked:
    """Kiểm câu trả lời của mô hình theo lộ trình mục 5 (điều 2–3). Số người dùng tự nêu trong câu hỏi được phép
    nhắc lại ở `tra_loi` và `tien_de_sai` (để bác tiền đề sai), không được dùng làm căn cứ trong `cac_y`."""
    try:
        a = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        a = None
    if not _shape_ok(a):
        return Checked({"du_can_cu": None, "tien_de_sai": "", "tra_loi": extractive(passages), "cac_y": [],
                        "luu_y": [], "trich_nguyen_van": True}, json_ok=False, replaced=True)
    by_n = {p.n: p for p in passages}
    src_nums = {p.n: numbers(p.render(), lenient=True) for p in passages}
    all_nums = set().union(*src_nums.values()) if src_nums else set()
    q_nums = numbers(question)
    out = Checked(dict(a), json_ok=True)

    ys = []
    for y in a["cac_y"]:
        cited = y["nguon"]
        if not cited or any(n not in by_n for n in cited):
            out.dropped.append("cac_y:nguon")
        elif CJK.search(y["y"]):
            out.dropped.append("cac_y:cjk")
        elif not numbers(y["y"]) <= set().union(*(src_nums[n] for n in cited)):
            out.dropped.append("cac_y:so")
        else:
            ys.append(y)
    out.answer["cac_y"] = ys

    luu = []
    for x in a["luu_y"]:
        if CJK.search(x) or not numbers(x) <= all_nums:
            out.dropped.append("luu_y:cjk" if CJK.search(x) else "luu_y:so")
        else:
            luu.append(x)
    out.answer["luu_y"] = luu

    tds = a["tien_de_sai"]
    if CJK.search(tds) or not numbers(tds) <= all_nums | q_nums:
        out.dropped.append("tien_de_sai:cjk" if CJK.search(tds) else "tien_de_sai:so")
        out.answer["tien_de_sai"] = ""

    if CJK.search(a["tra_loi"]) or not numbers(a["tra_loi"]) <= all_nums | q_nums:
        out.dropped.append("tra_loi:cjk" if CJK.search(a["tra_loi"]) else "tra_loi:so")
        out.answer["tra_loi"] = extractive(passages)
        out.answer["trich_nguyen_van"] = True
        out.replaced = True
    out.answer["chua_kiem_duoc"] = len(out.dropped)
    return out
