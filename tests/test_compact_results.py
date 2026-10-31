"""P1 K1: gộp trùng, phần trích có địa chỉ khớp, cắt danh sách, "Mở toàn văn" cho số hiệu."""

import random

import pytest

from soiluat import answer, cards
from soiluat.answer import _scores, _sentences, _window
from soiluat.ingest import ingest_path


# Bản chép nguyên _pick trước khi tách _pick_keep (K1): _pick mới phải trả đúng chuỗi cũ.
def _pick_cu(lines: list[tuple[str, str]], query: str, budget: int) -> str:
    """Giữ dòng khớp câu hỏi nhất và dòng liền kề, theo thứ tự gốc, trong `budget` ký tự. Dòng nào được giữ thì giữ cả
    câu dẫn của nó (điểm 'b) Làm giả…' kéo theo khoản '2. Phạt tiền từ … đối với các hành vi sau'): mất câu dẫn là mất
    mức phạt. Câu khớp nhất không vừa thì bỏ bớt dòng khớp rất yếu rồi lấy một khúc quanh chỗ khớp; không ưu tiên nó
    trước mọi dòng khác vì ở bản OCR câu khớp nhất đôi khi là khối rác (chữ ký dính phụ lục), đáp án nằm ở câu thứ hai."""
    texts = [t for _, t in lines]
    if sum(len(t) + 1 for t in texts) <= budget:
        return "\n".join(texts)
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
    out, prev = [], None
    for j in sorted(keep):
        if prev is not None and j > prev + 1:
            out.append("…")
        out.append(texts[j])
        prev = j
    return "\n".join(out)


TEXT = """Nghị định số 100/2019/NĐ-CP
Điều 5. Xử phạt người điều khiển xe ô tô
1. Phạt tiền từ 400.000 đồng đến 600.000 đồng đối với một trong các hành vi vi phạm sau đây:
a) Không chấp hành hiệu lệnh, chỉ dẫn của biển báo hiệu;
b) Dừng xe, đỗ xe trên phần đường xe chạy ở đoạn đường ngoài đô thị;
2. Phạt tiền từ 01 triệu đồng đến 02 triệu đồng đối với hành vi không mang theo giấy phép lái xe.
Điều 6. Xử phạt người điều khiển xe mô tô
1. Phạt tiền từ 100.000 đồng đến 200.000 đồng đối với hành vi không đội mũ bảo hiểm.
"""


@pytest.fixture
def doc(db, tmp_path):
    p = tmp_path / "nd100.txt"
    p.write_text(TEXT, encoding="utf-8")
    return ingest_path(db, p, tmp_path)


def _uid(db, path, doc_id=None):
    q, a = "SELECT id FROM units WHERE path = ?", [path]
    if doc_id:
        q, a = q + " AND doc_id = ?", a + [doc_id]
    return db.execute(q, a).fetchone()[0]


def test_pick_tra_dung_chuoi_cu():
    rnd = random.Random(7)
    words = "phạt tiền đồng hành vi xe ô tô giấy phép lái xe dừng đỗ biển báo hiệu lệnh mức người điều khiển".split()
    for _ in range(300):
        lines = []
        for k in range(1, rnd.randint(1, 6) + 1):
            lines.append((f"D5.K{k}", f"{k}. " + " ".join(rnd.choice(words) for _ in range(rnd.randint(3, 120))) + "."))
            for d in "ab"[: rnd.randint(0, 2)]:
                lines.append((f"D5.K{k}.Đ{d}", f"{d}) " + " ".join(rnd.choice(words) for _ in range(rnd.randint(3, 60))) + ";"))
        q = " ".join(rnd.choice(words) for _ in range(rnd.randint(1, 6)))
        for budget in (60, 200, 350, 900):
            assert answer._pick(lines, q, budget) == _pick_cu(lines, q, budget)


def test_snippet_dia_chi_khop_phan_trich(db, doc):
    head, text, path = answer.snippet(db, _uid(db, "D5"), "dừng xe đỗ xe ngoài đô thị")
    assert head.startswith("Điều 5.") and path == "D5.K1.Đb"
    assert "b) Dừng xe, đỗ xe" in text and "400.000 đồng" in text  # câu dẫn khoản đi cùng điểm
    assert "\n" not in text and len(text) <= answer.SNIP_CHARS + 5


def test_snippet_khong_dong_nao_khop_thi_path_rong(db, doc):
    assert answer.snippet(db, _uid(db, "D6"), "thuế thu nhập doanh nghiệp")[2] == ""


def test_snippet_dong_path_nam_trong_phan_trich(db, doc):
    for q in ("giấy phép lái xe", "biển báo hiệu", "mũ bảo hiểm", "phạt tiền"):
        for root in ("D5", "D6"):
            rid = _uid(db, root)
            _, text, path = answer.snippet(db, rid, q, budget=120)
            if path:
                line = db.execute("SELECT normalized_text FROM units WHERE id = ?", (_uid(db, path),)).fetchone()[0]
                assert line[:30] in text or "…" in text


def _cards_for(db, paths_docs, query="phạt tiền"):
    ids = [_uid(db, p, d) for p, d in paths_docs]
    return cards.assemble_cards(db, ids)


def _second(db, tmp_path, so="123/2021/NĐ-CP", hieu_luc="con", ngay="2021-01-01"):
    p = tmp_path / f"{so.replace('/', '_')}.txt"
    p.write_text(TEXT.replace("100/2019/NĐ-CP", so), encoding="utf-8")
    did = ingest_path(db, p, tmp_path)
    db.execute("UPDATE documents SET hieu_luc = ?, ngay_ban_hanh = ? WHERE id = ?", (hieu_luc, ngay, did))
    db.commit()
    return did


def test_hai_van_ban_cung_dieu_gop_mot_muc_dai_dien_con_hieu_luc(db, doc, tmp_path):
    other = _second(db, tmp_path)
    cs = _cards_for(db, [("D5.K2", doc), ("D5.K2", other)])
    items = cards.compact(db, cs, "giấy phép lái xe")
    assert len(items) == 1
    it = items[0]
    assert it.doc_id == other and it.hieu_luc == "con"  # văn bản kia hiệu lực chưa rõ
    assert [c.doc_id for c in it.also_in] == [doc]
    assert it.path == "D5.K2" and "giấy phép lái xe" in it.snippet


def test_hai_dieu_giong_nhau_trong_mot_van_ban_khong_gop(db, tmp_path):
    p = tmp_path / "trung.txt"
    p.write_text(TEXT + TEXT.split("\n", 1)[1].replace("Điều 5.", "Điều 7.").replace("Điều 6.", "Điều 8."), encoding="utf-8")
    did = ingest_path(db, p, tmp_path)
    items = cards.compact(db, _cards_for(db, [("D5.K2", did), ("D7.K2", did)]), "giấy phép")
    assert len(items) == 2


def test_than_rong_khong_gop_nham(db, doc, tmp_path):
    other = _second(db, tmp_path)
    for d in (doc, other):
        db.execute("INSERT INTO units(doc_id, path, level, title, raw_text, normalized_text, search_text, extraction_method,"
                   " verification_status) VALUES (?, 'D9', 'dieu', '', '', '', '', 'txt', 'auto')", (d,))
    db.commit()
    assert len(cards.compact(db, _cards_for(db, [("D9", doc), ("D9", other)]), "x")) == 2


def test_the_ghi_chu_khong_loi_va_hien_duty_text(db, doc):
    k = _uid(db, "D5.K1")
    db.execute("INSERT INTO units(doc_id, parent_id, path, level, raw_text, normalized_text, search_text, extraction_method,"
               " verification_status) VALUES (?, ?, 'GC1', 'ghi_chu', 'Chú thích riêng', 'Chú thích riêng', '', 'txt', 'auto')",
               (doc, k))
    db.commit()
    items = cards.compact(db, cards.assemble_cards(db, [_uid(db, "GC1")]), "chú thích")
    assert len(items) == 1 and items[0].snippet == items[0].duty_text and items[0].path


def test_path_mac_dinh_va_cung_dieu_con_khop(db, doc):
    items = cards.compact(db, _cards_for(db, [("D5.K1.Đb", doc), ("D5.K1.Đa", doc), ("D5.K2", doc)]), "dừng xe đỗ xe")
    it = items[0]
    assert it.path == "D5.K1.Đb" and it.path not in it.more and "D5.K2" in it.more
    one = cards.compact(db, _cards_for(db, [("D6.K1", doc)]), "thuế thu nhập")[0]
    assert one.path == "D6.K1" and one.more == []  # không dòng nào khớp: path của đơn vị đầu


def test_dieu_trung_so_giu_so_dieu(db, doc):
    from soiluat import reader

    d5 = _uid(db, "D5")
    db.execute("INSERT INTO units(doc_id, path, level, title, raw_text, normalized_text, search_text, extraction_method,"
               " verification_status) VALUES (?, 'D5~2', 'dieu', 'Điều lặp', 'Điều lặp', 'Điều lặp', '', 'txt', 'auto')", (doc,))
    db.execute("INSERT INTO units(doc_id, parent_id, path, level, raw_text, normalized_text, search_text, extraction_method,"
               " verification_status) VALUES (?, last_insert_rowid(), 'D5~2.K1', 'khoan', 'Nộp phạt tại kho bạc',"
               " 'Nộp phạt tại kho bạc', '', 'txt', 'auto')", (doc,))
    db.commit()
    it = cards.compact(db, cards.assemble_cards(db, [_uid(db, "D5~2.K1")]), "nộp phạt kho bạc")[0]
    assert reader.addr(it.path).endswith("Điều 5 (lần 2)") and it.head == "Điều lặp" and d5


def test_chi_xu_ly_toi_cap_va_rong_khong_loi(db, doc):
    cs = _cards_for(db, [("D5.K2", doc)])
    assert cards.compact(db, [], "x") == []
    assert len(cards.compact(db, cs * 600, "x", cap=100)) <= 100


def test_doc_groups_giu_thu_tu_xuat_hien(db, doc, tmp_path):
    from types import SimpleNamespace as N

    a1, b1, a2, x = N(doc_id=1), N(doc_id=2), N(doc_id=1), N()
    assert cards.doc_groups([a1, b1, a2, x]) == [[a1, a2], [b1], [x]]


# --- _search_ctx tách _search, _ctx; "Mở toàn văn" cho truy vấn chỉ có số hiệu ---
def _ctx(monkeypatch, tmp_path, q):
    from soiluat import app as appmod

    monkeypatch.setenv("SOILUAT_DATA", str(tmp_path))
    return appmod._search_ctx(q, "", "", "")


def _logged(db):
    return db.execute("SELECT result_count FROM query_log ORDER BY id DESC LIMIT 1").fetchone()[0]


def test_so_hieu_mot_minh_ra_mo_toan_van(db, sample_doc, tmp_path, monkeypatch):
    c = _ctx(monkeypatch, tmp_path, "15/2020/NĐ-CP")
    assert len(c["items"]) == 1 and c["items"][0].full and c["items"][0].doc_id == sample_doc
    assert c["items"][0].n_dieu > 5 and _logged(db) == 1
    assert len(_ctx(monkeypatch, tmp_path, "15/2020")["items"]) == 1  # số hiệu một phần


def test_so_hieu_kem_muc_phat_van_ra_the(db, doc, tmp_path, monkeypatch):
    c = _ctx(monkeypatch, tmp_path, "100/2019/NĐ-CP mức phạt")
    assert c["items"] and not getattr(c["items"][0], "full", False)


def test_so_hieu_kem_dieu_khong_co(db, sample_doc, tmp_path, monkeypatch):
    c = _ctx(monkeypatch, tmp_path, "Điều 99 Nghị định 15/2020/NĐ-CP")
    it = c["items"][0]
    assert it.full and it.missing_dieu == "99" and _logged(db) == 1
    c2 = _ctx(monkeypatch, tmp_path, "Điều 5 Nghị định 15/2020/NĐ-CP")
    assert not getattr(c2["items"][0], "full", False)  # có Điều 5: thẻ của Điều đó


def test_tim_thuong_ra_muc_gon(db, sample_doc, tmp_path, monkeypatch):
    c = _ctx(monkeypatch, tmp_path, "báo cáo định kỳ")
    assert c["items"] and all(it.snippet for it in c["items"][:5])
    assert c["n_items"] == len(c["items"]) and _logged(db) == len(c["cards"])
