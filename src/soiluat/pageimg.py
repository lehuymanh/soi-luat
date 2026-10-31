"""Ảnh trang gốc cho Search App: PDF render bằng pypdfium2 → PNG (không cần Pillow), file ảnh trả nguyên."""

from __future__ import annotations

import struct
import threading
import zlib
from pathlib import Path

from soiluat.config import data_dir

# pdfium "vốn không an toàn khi nhiều luồng dùng": /page chạy trong threadpool (trình duyệt xin vài trang cùng lúc) và luồng
# OCR cũng vẽ trang. Mọi lời gọi pdfium của app (mở, vẽ, đóng) giữ khoá này; không khoá thì cả app chết (SIGSEGV).
PDFIUM = threading.RLock()

VIEWABLE = {".pdf": "pdf", ".png": "png", ".jpg": "jpg", ".jpeg": "jpg"}
MAX_W = 1100  # px: đủ đọc chữ, PNG vài trăm KB


def stored_path(file_path: str) -> Path:
    """documents.file_path (tương đối data hoặc tuyệt đối, có thể kèm #vbN) → đường dẫn đầy đủ app tìm tệp."""
    p = Path(file_path.split("#vb", 1)[0])
    return p if p.is_absolute() else data_dir() / p


def source_file(file_path: str) -> Path | None:
    """File thật nếu còn."""
    p = stored_path(file_path)
    return p if p.is_file() else None


def can_view(file_path: str | None) -> bool:
    return bool(file_path) and Path(file_path.split("#vb", 1)[0]).suffix.lower() in VIEWABLE


def _png(rgb: bytes, w: int, h: int, stride: int) -> bytes:
    rows = b"".join(b"\0" + rgb[y * stride : y * stride + w * 3] for y in range(h))

    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(rows, 6))
        + chunk(b"IEND", b"")
    )


def render_pdf_page(path: Path, page_no: int) -> bytes | None:
    with PDFIUM:  # cả mở, vẽ, đóng; biến cục bộ của _render giải phóng ngay trong khoá
        return _render(path, page_no)


def _render(path: Path, page_no: int) -> bytes | None:
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(str(path))
    try:
        if not 1 <= page_no <= len(pdf):
            return None
        page = pdf[page_no - 1]
        scale = min(2.5, MAX_W / max(page.get_width(), 1))
        bmp = page.render(scale=scale, rev_byteorder=True)  # RGB, nền trắng
        return _png(bytes(bmp.buffer), bmp.width, bmp.height, bmp.stride)
    finally:
        pdf.close()
