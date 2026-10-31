"""Số phiên bản phải khớp ở mọi nơi (từng lệch: pyproject 0.8.0, __init__ 0.7.0)."""
import re
from pathlib import Path

import soiluat

ROOT = Path(__file__).resolve().parents[1]


def test_phien_ban_khop_moi_noi():
    v = soiluat.__version__
    assert re.search(r'^version = "([^"]+)"', (ROOT / "pyproject.toml").read_text(encoding="utf-8"), re.M).group(1) == v
    iss = re.search(r'#define AppVer "([^"]+)"', (ROOT / "pack" / "SoiLuat.iss").read_text(encoding="utf-8")).group(1)
    assert v.startswith(iss + ".") or v == iss
    assert f"Bản **{'.'.join(v.split('.')[:2])}**" in (ROOT / "README.md").read_text(encoding="utf-8")
