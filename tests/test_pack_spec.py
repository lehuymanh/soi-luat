from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_single_spec_bundles_ocr_and_semantic_libs():
    text = (ROOT / "pack" / "SoiLuat.spec").read_text(encoding="utf-8")
    for name in ("pytesseract", "PIL", "onnxruntime", "tokenizers", "win32com"):
        assert f'"{name}"' in text
    assert '"pytesseract", "PIL"' not in text.split("excludes")[1]  # không còn loại khỏi gói
    assert "run_search.py" in text
    assert '"static"' in text  # static/ phải vào gói, thiếu thì app không mở được
    assert not (ROOT / "pack" / "SoiLuatImporter.spec").exists()


def test_bind_localhost_only():
    from soiluat.config import HOST, PORT

    assert HOST == "127.0.0.1"
    assert PORT == 8000
