"""Nạp file và nhúng vector chạy nền ngay trong Search App: một luồng, lần lượt từng file.

Search App không tự import OCR/trích chữ ở mức module: chúng chỉ nạp khi luồng nền chạy lần đầu,
nên chế độ Normal không tốn RAM cho phần nạp. Khi hàng đợi trống và đang ở chế độ Advance,
luồng này nhúng nốt các Điều chưa có vector, từng khối nhỏ để file mới nạp xen vào được ngay.
Kho cũ (app_meta.parse_rev khác PARSE_REV) được nâng cấp một lần ở đây: sao lưu, rồi dựng lại từng văn bản có chữ đổi.
"""

from __future__ import annotations

import sqlite3
import threading
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from soiluat import semantic
from soiluat.config import data_dir, db_path
from soiluat.parse import PARSE_REV

# trùng importer.SUPPORTED_SUFFIXES (có test giữ hai tập khớp nhau)
SUFFIXES = frozenset(".docx .doc .rtf .pdf .txt .md .jpg .jpeg .png .tif .tiff .bmp .xlsx".split())
LABELS = {
    "cho": "Chờ", "dang_nap": "Đang nạp…", "du": "Xong", "can_ocr": "Cần OCR", "trung": "Trùng",
    "khong_doi": "Không đổi", "loi": "Lỗi", "bo_qua": "Bỏ qua",
}
BUSY = ("cho", "dang_nap")
KEEP = 300  # số dòng giữ lại trong danh sách (xoá dòng đã xong cũ nhất trước)
EMBED_CHUNK = 64


@dataclass
class Item:
    id: int
    name: str
    path: Path
    ocr: bool
    doan: bool
    state: str = "cho"
    note: str = ""


class Jobs:
    def __init__(self) -> None:
        self._cv = threading.Condition()
        self._items: list[Item] = []
        self._queue: deque[Item] = deque()
        self._seq = 0
        self._thread: threading.Thread | None = None
        self._current: Item | None = None
        self._todo: list[int] | None = None  # Điều chờ nhúng; None = chưa đếm / cần đếm lại
        self._stop = False
        self.embed = {"running": False, "done": 0, "total": 0}
        # nâng cấp dữ liệu: mỗi lần mở app đúng một lượt (cờ _migrate_tried; submit và wake không đặt lại, khác _todo)
        self.migrate = {"running": False, "done": 0, "total": 0, "error": "", "failed": 0}  # failed: văn bản chưa nâng cấp
        self._migrate_todo: list[int] | None = None  # doc_id chốt một lần lúc bắt đầu lượt
        self._migrate_tried = False
        self._migrate_bad: dict[int, str] = {}  # doc_id lỗi → lý do; còn sót thì không ghi parse_rev
        self._migrate_ok = 0  # văn bản đã nâng cấp xong (kể cả không đổi)
        self._migrate_streak = 0  # số văn bản lỗi liên tiếp
        self._migrate_retried = False  # đã qua lượt thử lại cuối lượt (hoặc bỏ lượt vì khoá giữ lâu)

    # ---- giao diện cho app ----

    def submit(self, paths: list[Path], *, ocr: bool, doan: bool) -> dict:
        """paths: file hoặc thư mục. Trả {"queued": n, "skipped": m} (m: file đuôi không hỗ trợ trong thư mục)."""
        from soiluat.importer import list_files  # nạp chậm: kéo theo trích chữ

        queued = skipped = 0
        with self._cv:
            for p in paths:
                if p.is_dir():
                    files, skip = list_files(p)
                    skipped += len(skip)
                else:
                    files = [p]
                for f in files:
                    self._seq += 1
                    it = Item(self._seq, f.name, f, ocr, doan)
                    if f.suffix.lower() not in SUFFIXES:
                        it.state, it.note = "bo_qua", f"đuôi {f.suffix or '(không có)'} không hỗ trợ"
                    else:
                        self._queue.append(it)
                        queued += 1
                    self._items.append(it)
            self._trim()
            self._todo = None
            self._ensure_thread()
            self._cv.notify_all()
        return {"queued": queued, "skipped": skipped}

    def wake(self) -> None:
        """Đổi chế độ tìm / vừa có việc mới: đếm lại Điều chưa nhúng."""
        with self._cv:
            self._todo = None
            self._ensure_thread()
            self._cv.notify_all()

    def clear(self) -> None:
        with self._cv:
            self._items = [i for i in self._items if i.state in BUSY]

    def stop(self) -> None:
        with self._cv:
            self._stop = True
            self._cv.notify_all()
        t = self._thread
        if t is not None and t is not threading.current_thread():
            t.join(timeout=10)

    def snapshot(self, conn=None) -> dict:
        with self._cv:
            items = list(self._items)
            cur = self._current
        pages = None
        if cur is not None and conn is not None:
            row = conn.execute(
                "SELECT pages_done, pages_total FROM import_jobs WHERE status = 'running' ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if row and row[1]:
                pages = [row[0] or 0, row[1]]
        out = []
        for i in items:
            d = {"id": i.id, "name": i.name, "state": i.state, "label": LABELS[i.state], "note": i.note,
                 "path": str(i.path)}
            if i is cur and pages:
                d["pages"] = pages
            out.append(d)
        n_busy = sum(1 for i in items if i.state in BUSY)
        return {
            "items": out,
            "total": len(items),
            "done": len(items) - n_busy,
            "active": n_busy > 0 or self.embed["running"] or self.migrate["running"],
            "embed": dict(self.embed),
            "migrate": dict(self.migrate),
        }

    # ---- luồng nền ----

    def _trim(self) -> None:
        extra = len(self._items) - KEEP
        if extra > 0:
            keep: list[Item] = []
            for i in self._items:
                if extra > 0 and i.state not in BUSY:
                    extra -= 1
                    continue
                keep.append(i)
            self._items = keep

    def _ensure_thread(self) -> None:
        if self._thread is None or not self._thread.is_alive():
            self._stop = False
            self._thread = threading.Thread(target=self._run, name="soiluat-jobs", daemon=True)
            self._thread.start()

    def _run(self) -> None:
        from soiluat.db import connect, init_schema
        from soiluat.importer import import_one

        conn = connect(db_path())  # kết nối riêng của luồng này
        init_schema(conn)
        root = data_dir()
        try:
            while not self._stop:
                with self._cv:
                    item = self._queue.popleft() if self._queue else None
                if item is not None:
                    self._import(conn, root, item, import_one)
                    continue
                if self._migrate_chunk(conn) or self._embed_chunk(conn):
                    continue
                with self._cv:
                    if not self._queue and not self._stop:
                        self._cv.wait(timeout=60)
        finally:
            conn.close()

    def _import(self, conn, root: Path, item: Item, import_one) -> None:
        item.state = "dang_nap"
        self._current = item
        try:
            item.state, item.note = import_one(conn, item.path, root, ocr=item.ocr, doan=item.doan)
        except Exception as e:  # noqa: BLE001 — một file hỏng không dừng cả hàng đợi
            item.state, item.note = "loi", f"{type(e).__name__}: {e}"
        finally:
            self._current = None
            self._todo = None  # có Điều mới: đếm lại phần cần nhúng

    def _migrate_chunk(self, conn) -> bool:
        """Nâng cấp dữ liệu một lần, mỗi lần một văn bản (file mới nạp xen vào được). True nếu đã làm gì đó."""
        if self._migrate_tried:
            return False
        try:
            return self._migrate_step(conn)
        except sqlite3.Error as e:  # khoá ghi quá 5 s lúc đếm văn bản hay ghi cờ: báo và dừng lượt, luồng không chết im
            conn.rollback()
            self.migrate.update(running=False, error=f"{type(e).__name__}: {e}", failed=self.migrate["total"] - self._migrate_ok)
            self._migrate_tried = True
            return False

    def _migrate_step(self, conn) -> bool:
        from soiluat.db import backup_db
        from soiluat.rebuild import rebuild_if_changed

        if self._migrate_todo is None:  # đầu lượt của lần mở app này
            if conn.execute("SELECT 1 FROM app_meta WHERE key = 'parse_rev' AND value = ?", (PARSE_REV,)).fetchone():
                self._migrate_tried = True
                return False
            self._migrate_todo = [r[0] for r in conn.execute("SELECT id FROM documents ORDER BY id")]
            self.migrate.update(running=bool(self._migrate_todo), done=0, total=len(self._migrate_todo), error="", failed=0)
            # mỗi lần tăng PARSE_REV có bản sao lưu riêng (lần sau không đè, cũng không bị bỏ vì bản cũ còn đó)
            bak = data_dir() / "backup" / f"soiluat-truoc-parse{PARSE_REV}.db"
            if self._migrate_todo and not bak.exists():  # backup_db ghi qua .tmp nên tên chính có nghĩa là bản đủ
                try:
                    backup_db(db_path(), bak)
                except Exception as e:  # noqa: BLE001 — không sao lưu được thì không dựng lại
                    if not bak.exists():  # trừ khi bản chạy kia (cổng khác, cùng kho) đã sao lưu xong
                        self.migrate.update(running=False, failed=len(self._migrate_todo),
                                            error=f"Không sao lưu được ({type(e).__name__}: {e})")
                        self._migrate_tried = True
                        return False
        if self._migrate_todo:
            doc_id = self._migrate_todo.pop(0)
            first_pass = not self._migrate_retried
            try:
                rebuild_if_changed(conn, doc_id)
                self._migrate_bad.pop(doc_id, None)
                self._migrate_ok += 1
                self._migrate_streak = 0
            except Exception as e:  # noqa: BLE001 — văn bản lỗi hoặc bị khoá ghi: bỏ qua và báo, luồng không chết im
                conn.rollback()
                self._migrate_bad[doc_id] = f"Văn bản {doc_id}: {type(e).__name__}: {e}"
                self._migrate_streak += 1
                if self._migrate_streak >= 3:  # khoá giữ lâu: mỗi văn bản chờ 5 s vô ích, bỏ cả lượt, không thử lại
                    self._migrate_todo.clear()
                    self._migrate_retried = True
            self.migrate.update(error=next(reversed(self._migrate_bad.values()), ""), failed=self.migrate["total"] - self._migrate_ok)
            if first_pass:  # lượt thử lại không tính thêm vào x/y
                self.migrate["done"] += 1
            return True
        if self._migrate_bad and not self._migrate_retried:  # khoá thoáng qua đã hết: thử lại các văn bản lỗi một lần
            self._migrate_retried = True
            self._migrate_todo = list(self._migrate_bad)
            self._migrate_streak = 0
            return True
        if not self._migrate_bad:  # duyệt hết mà không sót văn bản nào (kho trống cũng vào đây) mới ghi cờ
            conn.execute("INSERT OR REPLACE INTO app_meta(key, value) VALUES ('parse_rev', ?)", (PARSE_REV,))
            conn.commit()
        self.migrate["running"] = False
        self._migrate_tried = True
        self._todo = None  # Điều dựng lại mất vector: đếm lại phần cần nhúng (chỉ Advance)
        return False

    def _embed_chunk(self, conn) -> bool:
        """Nhúng một khối Điều chưa có vector. True nếu đã làm gì đó (vòng lặp kiểm hàng đợi rồi làm tiếp)."""
        if semantic.get_mode(conn) != "advance" or not semantic.model_installed():
            self.embed = {"running": False, "done": 0, "total": 0}
            return False
        enc = semantic.encoder()
        if enc is None:
            self.embed = {"running": False, "done": 0, "total": 0}
            return False
        if self._todo is None:
            self._todo = semantic.missing_roots(conn)
            self.embed = {"running": bool(self._todo), "done": 0, "total": len(self._todo)}
        if not self._todo:
            self.embed["running"] = False
            return False
        part, self._todo = self._todo[:EMBED_CHUNK], self._todo[EMBED_CHUNK:]
        semantic.embed_roots(conn, enc, part)
        self.embed["done"] += len(part)
        if not self._todo:
            self.embed["running"] = False
        return True


JOBS = Jobs()
