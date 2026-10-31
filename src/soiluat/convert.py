"""Đổi .doc/.rtf sang .docx tạm: Word COM → LibreOffice → ValueError."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

WD_FORMAT_DOCX = 16
SOFFICE_PATHS = (
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
)


def word_to_docx(src: Path, dst: Path) -> None:
    import pythoncom
    import win32com.client

    pythoncom.CoInitialize()
    word = doc = None
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        word.AutomationSecurity = 3  # msoAutomationSecurityForceDisable; mặc định Low = chạy mọi macro của file .doc/.rtf lạ
        # mật khẩu giả: file có mật khẩu thì báo lỗi ngay thay vì hiện hộp thoại chờ mãi
        doc = word.Documents.Open(
            str(src.resolve()),
            ConfirmConversions=False,
            ReadOnly=True,
            AddToRecentFiles=False,
            PasswordDocument="soiluat-khong-mat-khau",
        )
        try:
            doc.SaveAs2(str(dst.resolve()), FileFormat=WD_FORMAT_DOCX)
        finally:
            doc.Close(False)
            doc = None
    finally:
        if word is not None:
            word.Quit()
        # Word đã thoát nên nhả proxy có thể sinh lỗi RPC first-chance (vô hại, faulthandler có in ra)
        word = None
        pythoncom.CoUninitialize()


def find_soffice() -> str | None:
    found = shutil.which("soffice")
    if found:
        return found
    return next((p for p in SOFFICE_PATHS if Path(p).is_file()), None)


def soffice_to_docx(src: Path, dst: Path) -> None:
    exe = find_soffice()
    if not exe:
        raise FileNotFoundError("không tìm thấy soffice")
    subprocess.run(
        [exe, "--headless", "--convert-to", "docx", "--outdir", str(dst.parent), str(src.resolve())],
        check=True,
        capture_output=True,
        timeout=180,
    )
    out = dst.parent / f"{src.stem}.docx"
    if not out.is_file():
        raise FileNotFoundError("LibreOffice không tạo ra file .docx")
    out.replace(dst)


@contextmanager
def converted_docx(src: Path) -> Iterator[Path]:
    """Đường dẫn .docx tạm của `src`; thư mục tạm bị xoá khi ra khỏi khối with."""
    with tempfile.TemporaryDirectory(prefix="soiluat-conv-") as tmp:
        dst = Path(tmp) / "converted.docx"
        errors: list[str] = []
        for name, fn in (("Microsoft Word", word_to_docx), ("LibreOffice", soffice_to_docx)):
            try:
                fn(src, dst)
                if dst.is_file():
                    break
                errors.append(f"{name}: không tạo ra file")
            except Exception as e:  # thử cách kế tiếp, giữ lý do để báo
                errors.append(f"{name}: {e}")
        else:
            raise ValueError(
                f"Không đọc được file {src.suffix.lower()} ({src.name}). "
                "Cần Microsoft Word (kèm gói pywin32: pip install soiluat[word]) hoặc LibreOffice "
                "để chuyển sang .docx; hoặc mở file trong Word rồi Lưu thành .docx và nạp lại. "
                "Chi tiết: " + "; ".join(errors)
            )
        yield dst
