# -*- mode: python ; coding: utf-8 -*-
"""SoiLuat.exe — MỘT app: tìm, nạp file, OCR, nhúng vector (Advance).
Tesseract (tesseract/) và mô hình (models/) đặt cạnh SoiLuat.exe bởi build.ps1.
Chạy: pyinstaller pack/SoiLuat.spec"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path(SPECPATH).parent
datas = collect_data_files("soiluat")
# seed từ điển (db.init_schema nạp lúc mở kho); thêm tường minh phòng khi collect bỏ sót
seed = ROOT / "src" / "soiluat" / "synonyms_seed.csv"
if seed.exists() and not any(Path(s).name == seed.name for s, _ in datas):
    datas.append((str(seed), "soiluat"))
# static/ (JS, CSS, phông): thiếu thư mục thì StaticFiles ném lỗi lúc mở app
for f in (ROOT / "src" / "soiluat" / "static").rglob("*"):
    rel = f.parent.relative_to(ROOT / "src")
    if f.is_file() and not any(Path(s) == f for s, _ in datas):
        datas.append((str(f), str(rel)))
hidden = collect_submodules("soiluat") + [
    "onnxruntime",
    "tokenizers",
    "numpy",
    "pytesseract",
    "PIL",
    "soiluat.convert",
    # win32com: đổi .doc/.rtf qua Word COM (tuỳ chọn, cần pywin32 trên máy build)
    "win32com",
    "win32com.client",
    "pythoncom",
    "pywintypes",
    "uvicorn.logging",
    "uvicorn.lifespan.on",
    "uvicorn.lifespan.off",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.loops.auto",
    "multipart",
]

a = Analysis(
    [str(ROOT / "pack" / "run_search.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Advance (semantic.py) cần onnxruntime + tokenizers + numpy; bỏ phần onnxruntime không dùng khi chỉ chạy suy luận
    excludes=["cv2", "torch", "onnx", "llama_cpp", "sympy", "huggingface_hub",
              "onnxruntime.transformers", "onnxruntime.quantization", "onnxruntime.tools",
              # numpy kéo theo thư viện tuỳ chọn có trên máy build (+~400 MB) mà app không import
              "pandas", "scipy", "matplotlib", "pyarrow", "numba", "llvmlite", "botocore", "boto3",
              "IPython", "tkinter", "sklearn"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SoiLuat",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="SoiLuat",
)
