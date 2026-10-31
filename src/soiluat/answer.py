"""Trợ lý trả lời (lộ trình 1.0: P0 đo bằng `bench/llm/run.py`, P3 gắn vào app).

Dựng ngữ cảnh 3–5 Điều từ kho, gọi `llama-server` (API kiểu OpenAI) với JSON schema, rồi kiểm lại: nguồn phải là
đoạn đã đưa vào, mọi con số phải có trong đoạn được dẫn (lộ trình mục 5, điều 1–3). Nguyên văn hiển thị cho người
dùng luôn lấy từ `units`, không lấy từ mô hình.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
import urllib.request
from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal

from soiluat import semantic
from soiluat.fold import fold_search

MAX_PASSAGES = 5
# Thân đoạn. Cộng tiêu đề, câu hỏi ≈ 1.000 token Qwen3-VL mới mỗi câu (đo ~3,1 ký tự/token, bench/llm). Từ 2.600 hạ còn
# 2.400 khi tách câu dòng dài: ngữ cảnh đầy hơn, độ dài sau khi dựng về lại mức cũ.
CTX_CHARS = 2400
LONG_LINE = 300  # dòng dài hơn thì tách theo câu: bản OCR hay dính nhiều khoản/điểm thành một dòng 1.500–10.000 ký tự
SNIP_CHARS = 350  # phần trích một mục kết quả (P1 K1): câu dẫn khoản ~130 và thân điểm ~260 ký tự, như mẫu giao diện
N_PREDICT = 200
TEMPERATURE = 0.1  # thấp cho bám đoạn; chốt ở P0
SEED = 2026
_CJK = r"⺀-鿿ꥠ-꥿가-힯豈-﫿︰-﹏＀-￯\U00020000-\U0003FFFF"  # Trung/Nhật/Hàn

SYSTEM = """Bạn là trợ lý tra cứu văn bản pháp luật Việt Nam. Người hỏi là nhân viên văn phòng, không phải luật sư.
Chỉ dùng các đoạn [1], [2]… trong tin nhắn; không dùng kiến thức bên ngoài, không đoán.

Trả về JSON:
- "tien_de_sai": câu hỏi nêu sai so với đoạn (sai mức phạt, sai thời hạn, sai đối tượng…) thì ghi điều đúng theo đoạn, ví dụ "Mức phạt là từ 1.000.000 đồng đến 2.000.000 đồng, không phải 5.000.000 đồng."; câu hỏi không nêu chi tiết nào sai (phần lớn câu hỏi) thì "".
- "pham_vi": so điều được hỏi (ai, việc gì, ở đâu, khi nào) với đoạn gần nhất: "đúng" nếu đoạn nói đúng đối tượng và đúng trường hợp được hỏi; "hẹp hơn" nếu đoạn chỉ nói một trường hợp riêng của điều được hỏi (chỉ trong khu vực biên giới, chỉ với người dưới 18 tuổi, chỉ một loại giấy phép); "khác" nếu đoạn nói đối tượng hay việc khác (doanh nghiệp khi hỏi hộ kinh doanh, mua bán khi hỏi cho thuê).
- "du_can_cu": true nếu pham_vi là "đúng" hoặc "hẹp hơn", kể cả khi câu hỏi nêu sai một chi tiết; false nếu pham_vi là "khác" hoặc không đoạn nào nói về điều được hỏi.
- "tra_loi": tối đa 3 câu, lời thường, trả lời thẳng câu hỏi. Khi pham_vi là "hẹp hơn": nói rõ đoạn chỉ quy định cho trường hợp nào. Khi du_can_cu là false: nói các đoạn không có căn cứ.
- "cac_y": khi du_can_cu là true, 1–2 ý, mỗi ý một câu ngắn không chép lại "tra_loi"; "nguon" của mỗi ý là số thứ tự các đoạn làm căn cứ. Khi false thì [].
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
    """Khoá nội dung của Điều (tên Điều và chữ các khoản/điểm, bỏ dấu, không kèm số Điều): cùng khoá là cùng nội dung,
    kể cả ở hai văn bản khác nhau (lộ trình P1, gộp trùng). Tên phải vào khoá: 'Ưu tiên trong tuyển dụng viên chức' và
    '… công chức' có khoản giống hệt nhau."""
    head, lines = semantic.root_lines(conn, root_id)
    title = re.sub(r"^Điều \w+\.\s*", "", head)
    body = " ".join([title] + [t for _, t in lines])
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


def _sentences(lines: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Tách dòng dài theo câu (sau '.', ';', ':' đứng sau chữ, không tách '2. ' đầu khoản). Câu đầu giữ đường dẫn của
    dòng, các câu sau là con của nó ('D5.K2.~1'): giữ một câu thì giữ cả câu dẫn. Câu giữa dòng kết thúc bằng ':' là
    nhãn ('b) Đối với tổ chức:'), gộp với câu sau để nhãn đi cùng mức phạt của nó."""
    out = []
    for p, t in lines:
        parts = [x for x in re.split(r"(?<=[^\s\d][.;:])\s+", t) if x] if len(t) > LONG_LINE else [t]
        for k in range(len(parts) - 2, 0, -1):
            if parts[k].endswith(":"):
                parts[k:k + 2] = [parts[k] + " " + parts[k + 1]]
        out.append((p, parts[0]))
        out += [(f"{p}.~{k}", x) for k, x in enumerate(parts[1:], 1)]
    return out


def _scores(texts: list[str], query: str) -> list[float]:
    """Điểm mỗi dòng: tổng độ hiếm trong Điều (IDF, mỗi dòng là một tài liệu) của từ và cặp từ câu hỏi có trong dòng.
    Từ lặp ở nhiều dòng ('thí điểm cơ chế' ở 7/22 dòng) nhẹ; từ chỉ dòng đáp án có ('thời gian') nặng."""
    q = _words(query)
    qs, qb = set(q), set(zip(q, q[1:]))
    ws = [_words(t) for t in texts]
    df = Counter(w for x in ws for w in set(x) & qs)
    idf = {w: math.log(1 + (len(texts) - df[w] + 0.5) / (df[w] + 0.5)) for w in qs}
    return [sum(idf[w] for w in qs.intersection(x)) + sum((idf[a] + idf[b]) / 2 for a, b in qb.intersection(zip(x, x[1:])))
            for x in ws]


def _window(text: str, query: str, size: int) -> str:
    """Khúc ≤ `size` ký tự của một câu quá dài, chứa nhiều từ câu hỏi nhất; '…' đánh dấu chỗ cắt."""
    qs = set(_words(query))
    hits = [(m.start(), w) for m in re.finditer(r"\w+", text) if (w := fold_search(m.group())) in qs]
    size -= 2
    starts = [max(0, min(h - size // 4, len(text) - size)) for h, _ in hits] or [0]
    a = max(starts, key=lambda b: (len({w for h, w in hits if b <= h < b + size}), -b))
    e = min(a + size, len(text))
    if a and text[a - 1] != " ":  # cắt ở khoảng trắng, không để số hay chữ cụt ('2.000…')
        a = text.find(" ", a, e) + 1 or e
    if e < len(text) and text[e] != " ":
        e = max(text.rfind(" ", a, e), a)
    return ("…" if a else "") + text[a:e].strip() + ("…" if e < len(text) else "")


def _pick_keep(lines: list[tuple[str, str]], query: str, budget: int):
    """Giữ dòng khớp câu hỏi nhất và dòng liền kề, theo thứ tự gốc, trong `budget` ký tự. Dòng nào được giữ thì giữ cả
    câu dẫn của nó (điểm 'b) Làm giả…' kéo theo khoản '2. Phạt tiền từ … đối với các hành vi sau'): mất câu dẫn là mất
    mức phạt. Câu khớp nhất không vừa thì bỏ bớt dòng khớp rất yếu rồi lấy một khúc quanh chỗ khớp; không ưu tiên nó
    trước mọi dòng khác vì ở bản OCR câu khớp nhất đôi khi là khối rác (chữ ký dính phụ lục), đáp án nằm ở câu thứ hai.
    Trả (dòng, chữ từng dòng, chỉ số dòng giữ, điểm từng dòng) để người gọi biết dòng nào thật sự nằm trong phần trích."""
    texts = [t for _, t in lines]
    if sum(len(t) + 1 for t in texts) <= budget:
        return lines, texts, set(range(len(texts))), _scores(texts, query)
    lines = _sentences(lines)
    texts = [t for _, t in lines]
    scores = _scores(texts, query)
    at = {p: i for i, (p, _) in enumerate(lines)}
    keep: set[int] = set()

    def parents(i: int) -> list[int]:
        out, p = [], lines[i][0]
        while "." in p:
            p = p.rsplit(".", 1)[0]
            if p in at:
                out.append(at[p])
        return out

    def with_parents(i: int) -> list[int]:
        return [j for j in (i, *parents(i)) if j not in keep]

    ranked = sorted(range(len(texts)), key=lambda i: (-scores[i], i))
    used = 0
    for i in ranked:
        for j in (i, i - 1, i + 1):
            if j != i and i not in keep:
                break  # dòng khớp không vừa thì không tiêu ngân sách cho dòng bên cạnh nó
            if 0 <= j < len(texts):
                group = with_parents(j)
                cost = sum(len(texts[k]) + 1 for k in group)
                if group and used + cost <= budget:
                    keep.update(group)
                    used += cost
    best = ranked[0]
    if best not in keep:  # câu khớp nhất (kèm câu dẫn) không vừa: bỏ bớt dòng khớp rất yếu để lấy khúc quanh chỗ khớp
        need = min(len(texts[best]) + 1, budget // 2)
        weak = scores[best] / 4
        leads = {k for j in keep if scores[j] > weak for k in parents(j)}
        for k in sorted(keep, reverse=True):
            if budget - used >= need:
                break
            if scores[k] <= weak and k not in leads:
                keep.discard(k)
                used -= len(texts[k]) + 1
        if budget - used > 40 or not keep:
            texts[best] = _window(texts[best], query, max(budget - used - 1, 3))
            keep.add(best)
    return lines, texts, keep, scores


def _join(texts: list[str], keep: set[int], sep: str) -> str:
    out, prev = [], None
    for j in sorted(keep):
        if prev is not None and j > prev + 1:
            out.append("…")
        out.append(texts[j])
        prev = j
    return sep.join(out)


def _pick(lines: list[tuple[str, str]], query: str, budget: int) -> str:
    _, texts, keep, _ = _pick_keep(lines, query, budget)
    return _join(texts, keep, "\n")


def snippet(conn: sqlite3.Connection, root_id: int, query: str, budget: int = SNIP_CHARS) -> tuple[str, str, str]:
    """(tên Điều, phần trích một đoạn ≤ budget ký tự, path dòng khớp nhất trong phần trích) cho một mục kết quả (P1 K1).
    path lấy trong số dòng được giữ, nên địa chỉ của mục khớp chữ người đọc; rỗng khi không dòng nào khớp câu hỏi."""
    head, lines = semantic.root_lines(conn, root_id)
    lines = [(p, t) for p, t in lines if t.strip()]
    title = re.sub(r"^Điều \w+\.\s*", "", head)
    if lines and title and lines[0][1].startswith(title):  # dòng đầu là thân Điều bắt đầu bằng tên: bỏ phần tên
        lines[0] = (lines[0][0], lines[0][1][len(title):].strip())
        lines = [x for x in lines if x[1]]
    if not lines:
        return head, "", ""
    lines, texts, keep, scores = _pick_keep(lines, query, budget)
    best = max(sorted(keep), key=lambda i: scores[i])
    path = re.sub(r"\.~\d+$", "", lines[best][0]) if scores[best] > 0 else ""
    return head, _join(texts, keep, " "), path


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


# Một ký tự chuỗi JSON trừ chữ Trung/Nhật/Hàn (và trừ \uXXXX, lối viết CJK bằng mã): mô hình 4B thỉnh thoảng chêm chữ Hán.
_TEXT_CHAR = rf'([^"\\\x00-\x1F\x7F{_CJK}]|\\["\\/bfnrt])'


CAPS = {"tien_de_sai": 150, "tra_loi": 240, "y": 160, "luu_y": 140}  # ký tự; ~p95 độ dài đo trên train, hai cái đầu thấp hơn


def _text(n: int) -> dict:
    """Chuỗi ≤ n ký tự, không có chữ CJK. llama.cpp bỏ qua maxLength khi có pattern nên độ dài ghi cả trong pattern."""
    return {"type": "string", "maxLength": n, "pattern": f"^{_TEXT_CHAR}{{0,{n}}}$"}


def schema(n: int) -> dict:
    """Khuôn trả lời; `nguon` là enum gồm đúng các mã đã đưa vào. Hai nhánh theo cờ: đủ căn cứ thì phải có 1–2 ý có
    nguồn, không đủ thì không có ý nào. Thứ tự thuộc tính là thứ tự sinh: tiền đề sai rồi mới đến cờ (đo trên tập train
    Zalo: hỏi với mức phạt sai thì mô hình vẫn đặt đủ căn cứ và dẫn nguồn), cả hai trước câu trả lời. `pham_vi` (đoạn nói
    đúng/hẹp hơn/khác điều được hỏi) cũng đứng trước cờ: 'hẹp hơn' vẫn được trả lời kèm phạm vi, giao diện phải hiện
    cảnh báo (A/B trên train Zalo: ít câu khẳng định như đủ căn cứ khi đã bỏ Điều đúng nhất, 5/12 so với 7/12 khi 'hẹp
    hơn' buộc từ chối và 8/12 khi không có trường này). Độ dài có trần
    (~p95 độ dài đo trên train, tiền đề sai và câu trả lời thấp hơn) cho đuôi ngắn lại; phần vẫn bị cắt ở N_PREDICT thì
    `check` giữ các ý đã đủ."""
    src = {"type": "integer", "enum": list(range(1, n + 1))}
    y = {
        "type": "object",
        "properties": {"y": _text(CAPS["y"]), "nguon": {"type": "array", "items": src, "minItems": 1, "maxItems": n}},
        "required": ["y", "nguon"],
        "additionalProperties": False,
    }

    def branch(ok: bool) -> dict:
        props = {
            "tien_de_sai": _text(CAPS["tien_de_sai"]),
            "pham_vi": {"enum": ["đúng", "hẹp hơn"] if ok else ["đúng", "hẹp hơn", "khác"]},
            "du_can_cu": {"const": ok},
            "tra_loi": _text(CAPS["tra_loi"]),
            "cac_y": {"type": "array", "items": y, "minItems": 1, "maxItems": 2} if ok else {"type": "array", "items": y, "maxItems": 0},
            "luu_y": {"type": "array", "maxItems": 1, "items": _text(CAPS["luu_y"])},
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

CJK = re.compile(f"[{_CJK}]")
_SO_HIEU = re.compile(r"\b\d+(?:/\d{4})?/[A-Za-zĐđ][\wĐđ]*(?:-[\wĐđ]+)*")
_DATE = re.compile(
    r"\b(\d{1,2})[/.](\d{1,2})[/.](\d{4})\b|ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})|\b(\d{4})-(\d{2})-(\d{2})\b",
    re.IGNORECASE,
)
_PASSAGE_REF = re.compile(r"\[\d+(?:\s*[,;–-]\s*\d+)*\]|\bđoạn\s+\d+(?:\s*(?:,|và|-|–)\s*\d+)*\b", re.IGNORECASE)  # mã đoạn: đã kiểm bằng `nguon`
_REF = re.compile(
    r"\b(điều|khoản|điểm)\s+((?:\d+[a-z]?|[a-zđ])\b(?:\s*(?:,|và|hoặc)\s*(?:\d+[a-z]?|[a-zđ])\b)*)", re.IGNORECASE
)
_LEAD = re.compile(r"^\s*(?:(\d+[a-z]?)\.|([a-zđ])\))\s+")  # số khoản / chữ điểm đầu dòng do root_lines dựng lại
_THOUSANDS = re.compile(r"\d{1,3}(?:\.\d{3})+")
_NUM = re.compile(
    r"(?<![\w.,])(\d{1,3}(?:\.\d{3})+(?!\.?\d)|\d+\.\d{1,2}(?!\d)|\d+)(?:,(\d+))?(?:\s*(nghìn|ngàn|triệu|tỷ|tỉ)(?!\w))?",
    re.IGNORECASE,
)
_RANGE_GAP = re.compile(r"\s*(?:-|–|—|đến|tới)\s*", re.IGNORECASE)
_MULT = {"nghìn": 10**3, "ngàn": 10**3, "triệu": 10**6, "tỷ": 10**9, "tỉ": 10**9}
_CHU_SO = {"không": 0, "một": 1, "mốt": 1, "hai": 2, "ba": 3, "bốn": 4, "tư": 4, "năm": 5, "lăm": 5, "sáu": 6, "bảy": 7,
           "tám": 8, "chín": 9}
_SO_CHU = re.compile(r"\b(?:{w})(?:\s+(?:{w}))*\b".format(w="|".join([*_CHU_SO, "mười", "mươi", "trăm", "linh", "lẻ", *_MULT])),
                     re.IGNORECASE)
_MO_HO = {"một", "năm", "không", "tư", "lăm", "mốt"}  # đứng một mình thường không phải số ('một trong các', 'năm 2020')


def _doc_so_chu(words: list[str]) -> list[int]:
    """Giá trị của một chuỗi số viết bằng chữ: 'mười lăm' → [15], 'hai trăm năm mươi nghìn' → [250000]; hai chữ số
    liền nhau là hai số. 'năm' giữa số chỉ là 5 khi đứng sau 'linh'/'lẻ' hay trước 'mươi'/'trăm'/hàng nghìn; còn lại
    là danh từ 'năm': 'mười năm' → [10] (số 15 viết 'mười lăm'), 'hai năm' → [2]."""
    out: list[int] = []
    total = group = 0
    d: int | None = None
    seen = False

    def flush() -> None:
        nonlocal total, group, d, seen
        if seen:
            out.append(total + group + (d or 0))
        total = group = 0
        d, seen = None, False

    for i, w in enumerate(words):
        nxt = words[i + 1] if i + 1 < len(words) else ""
        if w == "năm" and seen and words[i - 1] not in ("linh", "lẻ") and nxt not in ("mươi", "trăm", *_MULT):
            flush()
            continue
        if w in _CHU_SO:
            if d is not None:
                flush()
            d, seen = _CHU_SO[w], True
        elif w == "mười":
            if d is not None or group % 100:
                flush()
            group, seen = group + 10, True
        elif w in ("mươi", "trăm"):
            if d is None:
                flush()
                continue
            group += d * (10 if w == "mươi" else 100)
            d = None
        elif w in _MULT:
            if not seen:
                continue
            total += (group + (d or 0)) * _MULT[w]
            group, d = 0, None
    flush()
    return out


def numbers(text: str, *, lenient: bool = False) -> set:
    """Các con số trong câu theo giá trị: '5.000.000 đồng' = '5 triệu đồng' = '5.0 triệu'; '1–2 triệu' = {1e6, 2e6};
    ngày viết số hay viết chữ như nhau; số hiệu so sau khi bỏ dấu; 'khoản 2 Điều 5' thành nhãn 'khoan:2', 'dieu:5'
    (không thành số 2, 5, để 'trong 5 ngày' không khớp nhờ tên Điều). `lenient` (phía nguồn) thêm số trần của khoảng
    và các số của số hiệu, để câu trả lời viết '1 đến 2 triệu' hay 'Nghị định 15 năm 2020' vẫn khớp, và số viết bằng
    chữ ('dưới mười lăm tuổi' cho phép '15'). Chữ cái luôn là điểm: 'khoản a' = 'điểm a'.
    shortcut: phía câu trả lời không đọc số viết bằng chữ ('một trong các' không thành số 1); nâng cấp nếu bộ đo thấy
    mô hình viết số bằng chữ mà số đó không có trong đoạn."""
    out: set = set()
    text = _PASSAGE_REF.sub(" ", text)
    for m in _SO_HIEU.finditer(text):
        out.add(fold_search(m.group(0)))
        if lenient:  # '64/2025/QH15' → 64, 2025; không lấy 15 trong 'QH15'
            out.update(Decimal(x) for x in re.findall(r"(?<![\wĐđ])\d+", m.group(0)))
    text = _SO_HIEU.sub(" ", text)
    for m in _REF.finditer(text):
        kind = fold_search(m.group(1))
        for x in re.split(r"\s*(?:,|và|hoặc)\s*", m.group(2), flags=re.IGNORECASE):  # tách theo dấu nối: 'hoặc' không thành 'c'
            out.add(f"{'diem' if x.isalpha() else kind}:{x.lower()}")
    text = _REF.sub(" ", text)
    for m in _DATE.finditer(text):
        if m.group(7):
            y, mo, d = (int(x) for x in m.group(7, 8, 9))
        else:
            d, mo, y = (int(x) for x in (m.group(1, 2, 3) if m.group(1) else m.group(4, 5, 6)))
        out.add(f"{d}/{mo}/{y}")
        if lenient:  # 'hiệu lực từ năm 2025', 'từ tháng 7' khi nguồn ghi ngày đầy đủ
            out.update(map(Decimal, (d, mo, y)))
    text = _DATE.sub(" ", text)
    if lenient:
        for m in _SO_CHU.finditer(text):
            words = m.group(0).lower().split()
            if len(words) > 1 or words[0] not in _MO_HO:
                out.update(Decimal(v) for v in _doc_so_chu(words))
    found = list(_NUM.finditer(text))
    for i, m in enumerate(found):
        g = m.group(1)
        whole = g.replace(".", "") if _THOUSANDS.fullmatch(g) else g
        v = Decimal(whole + ("." + m.group(2) if m.group(2) and "." not in whole else ""))
        unit = (m.group(3) or "").lower()
        # '1 đến 2 triệu': số đầu mượn đơn vị số sau; '500.000 đến 1 triệu' thì không (số đầu đã là số tiền đủ)
        if not unit and v < 1000 and not _THOUSANDS.fullmatch(g) and i + 1 < len(found) and found[i + 1].group(3):
            if _RANGE_GAP.fullmatch(text[m.end() : found[i + 1].start()]):
                if lenient:
                    out.add(v)
                unit = found[i + 1].group(3).lower()
        out.add(v * _MULT[unit] if unit else v)
    return out


@dataclass
class Checked:
    answer: dict  # câu trả lời đã kiểm: bỏ ý sai nguồn/số, thay câu trả lời khi có số lạ
    json_ok: bool  # đọc được JSON (kể cả khi phải cứu phần bị cắt)
    dropped: list[str] = field(default_factory=list)  # mỗi phần không qua kiểm: 'cac_y:so', 'tra_loi:cjk'…
    replaced: bool = False  # tra_loi đã thay bằng trích nguyên văn
    raw: dict = field(default_factory=dict)  # JSON mô hình trả, trước khi kiểm
    cut: bool = False  # JSON bị cắt giữa chừng, đã cứu các phần đã đủ


def _salvage(s: str) -> dict | None:
    """JSON bị cắt ở N_PREDICT: lùi về chỗ cuối cùng vừa xong một giá trị (trước dấu phẩy, sau dấu đóng ngoặc) rồi đóng
    các ngoặc còn mở. Giá trị đang viết dở (một ý, một chuỗi) bị bỏ cả, không giữ nửa câu."""
    stack: list[str] = []
    cuts: list[tuple[int, str]] = []
    in_str = esc = False
    for i, ch in enumerate(s):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch in "{[":
            stack.append("}" if ch == "{" else "]")
        elif ch in "}]":
            if not stack:
                return None
            stack.pop()
            cuts.append((i + 1, "".join(reversed(stack))))
        elif ch == ",":
            cuts.append((i, "".join(reversed(stack))))
    for end, close in reversed(cuts):
        try:
            a = json.loads(s[:end] + close)
        except json.JSONDecodeError:
            continue
        return a if isinstance(a, dict) else None
    return None


def _claimed(text: str, cap: str) -> set:
    """Số trong một chuỗi của câu trả lời. Chuỗi chạm trần độ dài bị grammar cắt giữa chừng: bỏ chữ cuối đang viết dở
    ('Nghị định 155/20') thay vì coi phần còn lại là số lạ."""
    return numbers(re.sub(r"\S*$", "", text) if len(text) >= CAPS[cap] else text)


def _covered(claim: set, allowed: set) -> bool:
    """claim ⊆ allowed, trừ số hiệu bị trần độ dài cắt cụt ('155/2020/nd'): khớp số hiệu đầy đủ có cùng phần đầu."""
    return all(
        x in allowed
        or (isinstance(x, str) and "/" in x and re.search("[a-z]", x)
            and any(isinstance(s, str) and s.startswith(x) for s in allowed))
        for x in claim
    )


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


def source_numbers(p: Passage) -> set:
    """Số và nhãn đoạn `p` cho phép câu trả lời dùng: chữ đoạn, tên Điều (nhãn 'dieu:n'), số khoản/chữ điểm đầu dòng
    (nhãn 'khoan:n', 'diem:x'), số hiệu, ngày. Không lấy mã [n] và tên file: các số đó không phải nội dung."""
    tags, body = set(), []
    for line in p.text.split("\n"):
        m = _LEAD.match(line)
        if m:
            tags.add(f"khoan:{m.group(1).lower()}" if m.group(1) else f"diem:{m.group(2).lower()}")
            line = line[m.end():]
        body.append(line)
    label = p.label if _SO_HIEU.search(p.label) else ""
    return tags | numbers("\n".join([label, p.head, p.meta, *body]), lenient=True)


def extractive(passages: list[Passage]) -> str:
    """Câu thay thế khi không tin được chữ mô hình: câu đầu của đoạn [1], nguyên văn."""
    if not passages:
        return "Không tìm thấy căn cứ trong kho."
    first = passages[0].text.split("\n", 1)[0]
    if len(first) > 300:  # cắt ở khoảng trắng: không để số tiền cụt hiện như nguyên văn
        first = first[:300].rsplit(" ", 1)[0] + "…"
    return f"Trích nguyên văn {passages[0].head or passages[0].label}: {first}"


def check(content: str, passages: list[Passage], question: str) -> Checked:
    """Kiểm câu trả lời của mô hình theo lộ trình mục 5 (điều 2–3). Số người dùng tự nêu trong câu hỏi được phép
    nhắc lại ở `tra_loi` và `tien_de_sai` (để bác tiền đề sai), không được dùng làm căn cứ trong `cac_y`."""
    cut = False
    try:
        a = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        a = _salvage(content) if isinstance(content, str) else None
        if a is not None:  # các phần sau chỗ cắt coi như rỗng; ý đang viết dở (thiếu nguồn) bỏ
            cut = True
            a = {"cac_y": [], "luu_y": [], **a}
            if isinstance(a["cac_y"], list):
                a["cac_y"] = [y for y in a["cac_y"] if not isinstance(y, dict) or "nguon" in y]
    if not _shape_ok(a):
        return Checked({"du_can_cu": None, "tien_de_sai": "", "tra_loi": extractive(passages), "cac_y": [],
                        "luu_y": [], "trich_nguyen_van": True}, json_ok=False, replaced=True, cut=cut)
    by_n = {p.n: p for p in passages}
    src_nums = {p.n: source_numbers(p) for p in passages}
    all_nums = set().union(*src_nums.values()) if src_nums else set()
    q_nums = numbers(question)
    out = Checked(dict(a), json_ok=True, raw=a, cut=cut)

    ys = []
    for y in a["cac_y"]:
        cited = y["nguon"]
        if not cited or any(n not in by_n for n in cited):
            out.dropped.append("cac_y:nguon")
        elif CJK.search(y["y"]):
            out.dropped.append("cac_y:cjk")
        elif not _covered(_claimed(y["y"], "y"), set().union(*(src_nums[n] for n in cited))):
            out.dropped.append("cac_y:so")
        else:
            ys.append(y)
    out.answer["cac_y"] = ys

    luu = []
    for x in a["luu_y"]:
        if CJK.search(x) or not _covered(_claimed(x, "luu_y"), all_nums):
            out.dropped.append("luu_y:cjk" if CJK.search(x) else "luu_y:so")
        else:
            luu.append(x)
    out.answer["luu_y"] = luu

    tds = a["tien_de_sai"]
    if CJK.search(tds) or not _covered(_claimed(tds, "tien_de_sai"), all_nums | q_nums):
        out.dropped.append("tien_de_sai:cjk" if CJK.search(tds) else "tien_de_sai:so")
        out.answer["tien_de_sai"] = ""

    if CJK.search(a["tra_loi"]) or not _covered(_claimed(a["tra_loi"], "tra_loi"), all_nums | q_nums):
        out.dropped.append("tra_loi:cjk" if CJK.search(a["tra_loi"]) else "tra_loi:so")
        out.answer["tra_loi"] = extractive(passages)
        out.answer["trich_nguyen_van"] = True
        out.replaced = True
    out.answer["chua_kiem_duoc"] = len(out.dropped)
    return out
