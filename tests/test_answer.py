"""Trợ lý trả lời (lộ trình 1.0): dựng ngữ cảnh, khuôn JSON, kiểm nguồn và số liệu, gọi llama-server (giả)."""

import json
import threading
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from soiluat import answer
from soiluat.ingest import ingest_path

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


def _root(db, path):
    return db.execute("SELECT id FROM units WHERE path = ?", (path,)).fetchone()[0]


def test_numbers_normalize_money_ranges_dates_and_so_hieu():
    n = answer.numbers
    assert n("5.000.000 đồng") == n("5 triệu đồng") == {Decimal(5_000_000)}
    assert n("phạt 5.000.000.") == {Decimal(5_000_000)}  # số ở cuối câu
    assert n("từ 1 đến 2 triệu đồng") == n("1–2 triệu") == {Decimal(1_000_000), Decimal(2_000_000)}
    assert n("01 triệu đồng") == {Decimal(1_000_000)}
    assert n("1,5 triệu") == {Decimal(1_500_000)}
    assert n("ngày 01 tháng 7 năm 2025") == n("1/7/2025") == n("2025-07-01") == {"1/7/2025"}
    assert n("Nghị định 100/2019/NĐ-CP") == n("nghị định 100/2019/nd-cp") == {"100/2019/nd-cp"}
    assert Decimal(2019) in n("100/2019/NĐ-CP", lenient=True)
    assert Decimal(1) in n("từ 1 đến 2 triệu", lenient=True)


def test_build_context_orders_marks_and_budgets(db, doc):
    roots = [_root(db, "D6"), _root(db, "D5")]
    ps = answer.build_context(db, roots, "không mang giấy phép lái xe", budget=10_000)
    assert [p.n for p in ps] == [1, 2] and [p.root_id for p in ps] == roots
    assert ps[1].head.startswith("Điều 5.") and ps[1].label == "100/2019/NĐ-CP"
    assert "a) Không chấp hành" in ps[1].text  # dựng lại số khoản/chữ điểm
    assert ps[0].render().startswith("[1] 100/2019/NĐ-CP — Điều 6.")

    tight = answer.build_context(db, [_root(db, "D5")], "không mang theo giấy phép lái xe", budget=120)
    assert "giấy phép lái xe" in tight[0].text  # giữ khoản khớp câu hỏi
    assert len(tight[0].text) <= 125


def test_kept_diem_brings_its_khoan_lead_in(db, doc):
    p = answer.build_context(db, [_root(db, "D5")], "dừng xe đỗ xe ngoài đô thị", budget=180)[0]
    assert "b) Dừng xe, đỗ xe" in p.text and "400.000 đồng đến 600.000 đồng" in p.text  # mức phạt nằm ở câu dẫn khoản
    assert "giấy phép lái xe" not in p.text


def test_same_dieu_in_two_documents_is_one_passage(db, doc, tmp_path):
    p = tmp_path / "nd100_ban_sao.txt"
    p.write_text(TEXT.replace("100/2019/NĐ-CP", "123/2021/NĐ-CP"), encoding="utf-8")
    ingest_path(db, p, tmp_path)
    d5 = [r[0] for r in db.execute("SELECT id FROM units WHERE path = 'D5'")]
    assert len(d5) == 2 and answer.content_sig(db, d5[0]) == answer.content_sig(db, d5[1])
    ps = answer.build_context(db, d5 + [_root(db, "D6")], "phạt")
    assert [p.root_id for p in ps] == [d5[0], _root(db, "D6")]


def test_shares_give_short_passages_all_they_need():
    assert answer._shares([100, 5000, 5000], 3000) == [100, 1450, 1450]
    assert answer._shares([100, 200], 3000) == [100, 200]


def test_schema_enum_is_exactly_the_passages_and_branches_on_the_flag():
    co, khong = answer.schema(3)["anyOf"]
    assert co["properties"]["du_can_cu"] == {"const": True} and khong["properties"]["du_can_cu"] == {"const": False}
    assert co["properties"]["cac_y"]["items"]["properties"]["nguon"]["items"]["enum"] == [1, 2, 3]
    assert co["properties"]["cac_y"]["minItems"] == 1 and khong["properties"]["cac_y"]["maxItems"] == 0
    assert co["properties"]["pham_vi"]["enum"] == ["đúng", "hẹp hơn"] and "khác" in khong["properties"]["pham_vi"]["enum"]
    for b in (co, khong):
        assert list(b["properties"])[:4] == ["tien_de_sai", "pham_vi", "du_can_cu", "tra_loi"]  # kiểm trước khi đặt cờ
        assert all(v.get("maxLength") for k, v in b["properties"].items() if v.get("type") == "string")
        assert set(b["required"]) == set(b["properties"])


def _ps(db):
    return answer.build_context(db, [_root(db, "D5"), _root(db, "D6")], "giấy phép lái xe", budget=10_000)


def _reply(**kw):
    base = {"du_can_cu": True, "tien_de_sai": "", "tra_loi": "Bị phạt tiền.", "cac_y": [], "luu_y": []}
    return json.dumps({**base, **kw}, ensure_ascii=False)


def test_check_keeps_matching_numbers_and_drops_wrong_ones(db, doc):
    ps = _ps(db)
    r = answer.check(_reply(
        tra_loi="Phạt từ 1 đến 2 triệu đồng.",
        cac_y=[{"y": "Phạt 1.000.000 đồng đến 2.000.000 đồng theo khoản 2 Điều 5.", "nguon": [1]},
               {"y": "Phạt 3 triệu đồng.", "nguon": [1]},  # số không có trong đoạn
               {"y": "Mũ bảo hiểm phạt 100.000 đồng.", "nguon": [1]},  # số có ở đoạn [2], không ở đoạn được dẫn
               {"y": "Phạt 100.000 đồng.", "nguon": [9]}],  # nguồn không có
    ), ps, "Không mang giấy phép lái xe bị phạt bao nhiêu?")
    assert r.json_ok and not r.replaced
    assert [y["nguon"] for y in r.answer["cac_y"]] == [[1]]
    assert sorted(r.dropped) == ["cac_y:nguon", "cac_y:so", "cac_y:so"] and r.answer["chua_kiem_duoc"] == 3


def test_check_replaces_answer_with_foreign_number_or_cjk(db, doc):
    ps = _ps(db)
    r = answer.check(_reply(tra_loi="Phạt 7 triệu đồng."), ps, "phạt bao nhiêu?")
    assert r.replaced and r.answer["trich_nguyen_van"] and r.answer["tra_loi"].startswith("Trích nguyên văn Điều 5")
    assert r.dropped == ["tra_loi:so"]
    assert answer.check(_reply(tra_loi="Bị phạt 罚款."), ps, "phạt?").replaced


def test_check_allows_question_numbers_only_outside_cited_points(db, doc):
    ps = _ps(db)
    q = "Không mang giấy phép lái xe bị phạt 5 triệu đồng phải không?"
    r = answer.check(_reply(
        tien_de_sai="Không phải 5 triệu đồng; mức phạt là từ 01 triệu đồng đến 02 triệu đồng.",
        tra_loi="Không, mức phạt không phải 5 triệu đồng.",
        cac_y=[{"y": "Mức phạt là 5 triệu đồng.", "nguon": [1]}],
    ), ps, q)
    assert r.answer["tien_de_sai"] and not r.replaced
    assert r.answer["cac_y"] == [] and r.dropped == ["cac_y:so"]


def test_check_invalid_json_falls_back_to_quote(db, doc):
    ps = _ps(db)
    for bad in ('{"tra_loi": "thiếu khoá"}', "không phải JSON", None):
        r = answer.check(bad, ps, "q")
        assert not r.json_ok and r.replaced and r.answer["du_can_cu"] is None


class _Fake(BaseHTTPRequestHandler):
    seen: list = []

    def do_POST(self):  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        _Fake.seen.append((self.path, self.headers.get("Authorization"), body))
        out = json.dumps({"choices": [{"message": {"content": _reply()}}], "usage": {"prompt_tokens": 9}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *a):
        pass


def test_chat_posts_schema_to_local_server_without_proxy(db, doc, monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:9")  # proxy chết: nếu dùng proxy thì lỗi
    srv = HTTPServer(("127.0.0.1", 0), _Fake)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        ps = _ps(db)
        res = answer.chat(f"http://127.0.0.1:{srv.server_port}", answer.messages(ps, "Hỏi?"), answer.schema(len(ps)),
                          api_key="k1")
    finally:
        srv.shutdown()
    path, auth, body = _Fake.seen[-1]
    assert path == "/v1/chat/completions" and auth == "Bearer k1"
    assert body["response_format"]["schema"]["anyOf"][0]["properties"]["cac_y"]["items"]["properties"]["nguon"]["items"]["enum"] == [1, 2]
    assert body["max_tokens"] == answer.N_PREDICT and body["messages"][0]["content"] == answer.SYSTEM
    assert "[2] 100/2019/NĐ-CP — Điều 6." in body["messages"][1]["content"]
    assert answer.check(res["choices"][0]["message"]["content"], ps, "Hỏi?").json_ok


def test_review_number_cases():
    n = answer.numbers
    assert n("Phạt từ 500.000 đến 1 triệu đồng") == {Decimal(500_000), Decimal(1_000_000)}  # không mượn 'triệu'
    assert n("1.5 triệu đồng") == {Decimal(1_500_000)} and n("0.5%") == {Decimal("0.5")}
    assert n("ngày 01.08.2030") == {"1/8/2030"}
    assert n("khoản 1, 2 và điểm a Điều 5") == {"khoan:1", "khoan:2", "diem:a", "dieu:5"}
    assert n("Đoạn [1] và đoạn 2 nêu điều kiện") == set()  # mã đoạn và chữ 'điều kiện' không phải số


def test_structural_digits_do_not_vouch_for_invented_numbers():
    p = answer.Passage(1, 1, 1, "36/2024/QH15", "Điều 8. Mức phạt", "1. Phạt tiền từ 500.000 đồng đến 1.000.000 đồng.")

    def kept(y):
        return answer.check(_reply(cac_y=[{"y": y, "nguon": [1]}]), [p], "q").answer["cac_y"] != []

    assert not kept("Nộp phạt trong 15 ngày.")  # 15 trong 'QH15'
    assert not kept("Thời hạn 8 ngày.")  # 8 trong 'Điều 8'
    assert not kept("Thời hạn 1 ngày.")  # 1 trong '[1]' / '1.'
    assert kept("Theo khoản 1 Điều 8 Luật 36/2024/QH15, phạt từ 500.000 đến 1 triệu đồng.")
    assert kept("Đoạn [1] nêu mức phạt tối đa 1.0 triệu đồng.")
    assert not kept("Phạt tối đa 1.5 triệu đồng.")


def test_pick_does_not_spend_budget_beside_a_line_that_did_not_fit():
    lines = [("D1.K1", "1. Mở đầu " + "y" * 40), ("D1.K2", "2. Xe máy đi vào đường cấm " + "x" * 300),
             ("D1.K3", "3. Câu bên cạnh " + "z" * 34), ("D1.K4", "4. Xe máy đi vào khu vực cấm bị phạt.")]
    out = answer._pick(lines, "xe máy đi vào đường cấm", 120)  # K1 + K3 trước thì K4 không còn chỗ
    assert "4. Xe máy đi vào khu vực cấm" in out and "Mở đầu" not in out


def test_reference_checker_cases_from_round_one():
    n = answer.numbers
    assert n("khoản a Điều 5") == n("điểm a Điều 5") == {"diem:a", "dieu:5"}  # chữ cái luôn là điểm
    assert n("khoản 2a") == {"khoan:2a"}
    assert Decimal(15) in n("người dưới mười lăm tuổi", lenient=True) and n("mười lăm tuổi") == set()
    assert Decimal(250_000) in n("hai trăm năm mươi nghìn đồng", lenient=True)
    assert {Decimal(25), Decimal(30), Decimal(1005)} <= n("hai mươi lăm, ba mươi, một nghìn không trăm linh năm", lenient=True)
    assert n("một trong các hành vi; đầu tư; không quá 05 năm", lenient=True) == {Decimal(5)}  # chữ một mình mơ hồ
    p = answer.Passage(1, 1, 1, "155/2020/NĐ-CP", "Điều 3. Độ tuổi", "1. Trẻ em gồm:\na) Người dưới mười lăm tuổi.")

    def kept(y):
        return answer.check(_reply(cac_y=[{"y": y, "nguon": [1]}]), [p], "q").answer["cac_y"] != []

    assert kept("Theo Nghị định 155/2020/NĐ-")  # số hiệu bị trần độ dài cắt cụt
    assert kept("Người dưới 15 tuổi, theo khoản a.")
    assert not kept("Theo Nghị định 156/2020/NĐ-") and not kept("Người dưới 16 tuổi.")


def test_salvage_keeps_finished_points_of_a_cut_reply(db, doc):
    ps = _ps(db)
    head = '{"tien_de_sai": "", "du_can_cu": true, "tra_loi": "Phạt từ 1 đến 2 triệu đồng.", "cac_y": ['
    one = '{"y": "Phạt 1.000.000 đồng đến 2.000.000 đồng.", "nguon": [1]}'
    r = answer.check(head + one + ', {"y": "Mức phạt áp dụng cho người điều khi', ps, "q")
    assert r.json_ok and r.cut and not r.replaced and r.answer["cac_y"] == [json.loads(one)] and r.answer["luu_y"] == []
    r = answer.check(head + '{"y": "Phạt 1.000.000 đồng.", "nguon": [1, ', ps, "q")  # cắt giữa danh sách nguồn
    assert r.cut and [y["nguon"] for y in r.answer["cac_y"]] == [[1]]
    r = answer.check(head + '{"y": "Phạt 1.000.000 đồng đến', ps, "q")  # ý đầu chưa xong: đủ căn cứ mà không có ý
    assert r.cut and r.answer["cac_y"] == [] and r.answer["tra_loi"].startswith("Phạt")
    r = answer.check('{"tien_de_sai": "", "du_can_cu": true, "tra_loi": "Phạt từ 1 đến', ps, "q")  # câu trả lời dở
    assert not r.json_ok and r.replaced


def test_schema_strings_block_cjk_and_cap_length():
    import re

    pat = answer.schema(2)["anyOf"][0]["properties"]["tra_loi"]["pattern"]
    body = re.compile(pat[1:-1])  # cùng cú pháp regex mà llama.cpp dịch sang grammar
    assert body.fullmatch('Phạt 1.000.000 đồng – “đúng” theo điểm a) \\"khoản 2\\".')
    assert not body.fullmatch("Bị phạt 罚款.") and not body.fullmatch("Phạt ｘ") and not body.fullmatch("\\u4e00")
    assert body.fullmatch("x" * 240) and not body.fullmatch("x" * 241)
    assert answer.CJK.search("thẩm权") and not answer.CJK.search("Điều 5, khoản 2 – “đ”")


def test_pick_weights_words_rare_in_the_dieu_and_splits_long_ocr_lines():
    # Vòng 1, văn bản thật: 7/22 dòng có 'thí điểm cơ chế', dòng đáp án chỉ khác ở 'thời gian' và bị cắt
    lines = [(f"D8.K{i}", f"{i}. Thí điểm cơ chế, chính sách đặc thù về lĩnh vực số {i} " + "y" * 60) for i in range(1, 8)]
    lines.append(("D8.K8", "8. Thời gian thí điểm không quá 05 năm."))
    out = answer._pick(lines, "thời gian thí điểm cơ chế chính sách", 120)
    assert "Thời gian thí điểm không quá 05 năm" in out

    # bản OCR: một dòng 2.000 ký tự dính nhiều điểm; câu đáp án nằm sâu bên trong
    filler = " ".join(f"{c}) Hồ sơ thứ {c} gồm giấy tờ " + "z" * 80 + ";" for c in "abcdefghiklmnopq")
    long = f"2. Doanh nghiệp phải nộp hồ sơ sau: {filler} r) Thời hạn lưu chiểu ít nhất 10 ngày trước khi phát hành."
    assert len(long) > answer.LONG_LINE * 5
    out = answer._pick([("D3.K1", "1. Phạm vi áp dụng."), ("D3.K2", long)], "lưu chiểu trước khi phát hành ít nhất", 260)
    assert "r) Thời hạn lưu chiểu ít nhất 10 ngày" in out and out.count("\n") >= 1
    assert "2. Doanh nghiệp phải nộp hồ sơ sau:" in out  # câu dẫn của dòng đi theo câu được giữ
    assert [p for p, _ in answer._sentences([("D3.K2", long)])][:2] == ["D3.K2", "D3.K2.~1"]
    assert answer._sentences([("K", "2. " + "x" * 400)]) == [("K", "2. " + "x" * 400)]  # không tách sau số khoản


def test_content_sig_keeps_different_titles_apart(db, tmp_path):
    p = tmp_path / "hai.txt"
    p.write_text("Nghị định số 7/2020/NĐ-CP\nĐiều 1. Ưu tiên trong tuyển dụng viên chức\n1. Con liệt sĩ.\n"
                 "Điều 2. Ưu tiên trong tuyển dụng công chức\n1. Con liệt sĩ.\n", encoding="utf-8")
    ingest_path(db, p, tmp_path)
    assert answer.content_sig(db, _root(db, "D1")) != answer.content_sig(db, _root(db, "D2"))


def test_review_round2_number_words_and_reference_lists():
    n = answer.numbers
    # 'năm' sau mười/mươi hay sau một chữ số là danh từ 'năm' (thời gian), không phải số 5
    assert n("phạt tù từ mười năm đến hai mươi năm", lenient=True) == {Decimal(10), Decimal(20)}
    assert n("thời hạn hai năm", lenient=True) == {Decimal(2)} and n("năm năm", lenient=True) == {Decimal(5)}
    assert n("hai trăm năm mươi nghìn; một trăm linh năm", lenient=True) == {Decimal(250_000), Decimal(105)}
    p = answer.Passage(1, 1, 1, "", "Điều 9. Hình phạt", "1. Phạt tù từ mười năm đến hai mươi năm.")

    def kept(y, src=p):
        return answer.check(_reply(cac_y=[{"y": y, "nguon": [1]}]), [src], "q").answer["cac_y"] != []

    assert kept("Phạt tù từ 10 năm đến 20 năm.") and not kept("Phạt tù từ 15 năm đến 25 năm.")
    # chữ cuối của 'hoặc' không thành 'điểm c'
    assert n("điểm a hoặc b khoản 1") == {"diem:a", "diem:b", "khoan:1"} and n("khoản 1 hoặc 2") == {"khoan:1", "khoan:2"}
    ab = answer.Passage(1, 1, 1, "", "Điều 5. Vi phạm", "1. Vi phạm một trong các hành vi sau:\na) Xả rác.\nb) Đổ chất thải.")
    assert kept("Vi phạm điểm a hoặc b khoản 1 bị phạt.", ab) and not kept("Vi phạm điểm c khoản 1.", ab)


def test_review_round2_string_cut_at_its_cap_ignores_the_partial_last_token(db, doc):
    ps = _ps(db)  # [1] Điều 5 của 100/2019/NĐ-CP
    y = "Phạt 1.000.000 đồng đến 2.000.000 đồng theo Nghị định 100/20"
    y = " " * (160 - len(y)) + y  # đúng trần 160 ký tự: trần độ dài cắt giữa số hiệu
    assert answer.check(_reply(cac_y=[{"y": y, "nguon": [1]}]), ps, "q").answer["cac_y"] != []
    short = "Phạt 1.000.000 đồng theo Nghị định 100/20"  # chưa chạm trần: '20' là số lạ thật
    assert answer.check(_reply(cac_y=[{"y": short, "nguon": [1]}]), ps, "q").answer["cac_y"] == []


def test_review_round2_oversize_piece_still_gives_a_window_and_colon_keeps_label_with_amount():
    body = ", ".join(f"{i}) nội dung thứ {i} gồm nhiều chữ " + "x" * 60 for i in range(1, 9))
    line = "Các khoản sau đây. " + body + ", 9) thời hạn lưu chiểu là ít nhất 10 ngày trước khi phát hành " + "y" * 200
    out = answer._pick([("D3", line)], "thời hạn lưu chiểu ít nhất bao nhiêu ngày", 400)
    assert "thời hạn lưu chiểu là ít nhất 10 ngày" in out and len(out) <= 420

    line = ("2. Mức phạt tiền đối với hành vi quy định tại Điều này như sau: a) Đối với cá nhân: phạt từ 1.000.000 đồng "
            "đến 2.000.000 đồng; b) Đối với tổ chức: phạt từ 2.000.000 đồng đến 4.000.000 đồng; c) Tái phạm thì phạt "
            "gấp đôi. " + "Câu bổ sung về thủ tục nộp phạt và cơ quan có thẩm quyền xử lý. " * 4)
    label_and_amount = "b) Đối với tổ chức: phạt từ 2.000.000 đồng đến 4.000.000 đồng;"
    assert label_and_amount in [t for _, t in answer._sentences([("D7.K2", line)])]  # không tách ở dấu hai chấm
    out = answer._pick([("D7.K1", "1. Phạm vi."), ("D7.K2", line)], "mức phạt đối với tổ chức", 220)
    assert label_and_amount in out
