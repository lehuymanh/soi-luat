"""N1b soát lần hai: tìm kiếm Normal không phải dựng lại chỉ mục tên Điều cho mỗi văn bản được nâng cấp (T1)."""

import threading
import time
from pathlib import Path

from soiluat import search
from soiluat.db import connect
from soiluat.ingest import ingest_path
from soiluat.jobs import JOBS

VB1 = "Nghị định số 9/2021/NĐ-CP\nĐiều 1. Phạm vi điều chỉnh\nNghị định này quy định về xử phạt.\n"
VB2 = "Nghị định số 10/2021/NĐ-CP\nĐiều 1. Giá dịch vụ công\n1. Cơ sở phải niêm yết giá.\n"


def _nap(db, tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return ingest_path(db, p, tmp_path)


def test_t1_dang_nang_cap_giu_chi_muc_ten_dieu_cu(db, tmp_path, monkeypatch):
    monkeypatch.setattr(search, "_TITLE_CACHE", {})
    _nap(db, tmp_path, "a.txt", VB1)
    cu = search._title_index(db, True)
    _nap(db, tmp_path, "b.txt", VB2)  # đổi (MAX(id), COUNT(*)) như mỗi văn bản được dựng lại
    monkeypatch.setitem(JOBS.migrate, "running", True)
    assert search._title_index(db, True) is cu  # không dựng lại 1 s mỗi lần tìm trong 5–10 phút nâng cấp
    monkeypatch.setitem(JOBS.migrate, "running", False)
    assert search._title_index(db, True) is not cu  # xong nâng cấp: khoá đổi nên dựng lại đúng một lần


def test_t1_hai_tim_kiem_dong_thoi_dung_chung_mot_lan_dung_chi_muc(db, tmp_path, monkeypatch):
    monkeypatch.setattr(search, "_TITLE_CACHE", {})
    _nap(db, tmp_path, "a.txt", VB1)
    n = []
    real = search.phrase_index

    def cham(titles):
        n.append(1)
        time.sleep(0.3)
        return real(titles)

    monkeypatch.setattr(search, "phrase_index", cham)

    def tim():
        c = connect(Path(tmp_path) / "soiluat.db")
        search._title_index(c, True)
        c.close()

    ts = [threading.Thread(target=tim) for _ in range(3)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert len(n) == 1
