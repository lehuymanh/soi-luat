from soiluat.health import health_row, write_csv
from pathlib import Path


def test_health_csv(tmp_path):
    src = Path(__file__).parent / "fixtures" / "nd15.txt"
    dest = tmp_path / "nd15.txt"
    dest.write_bytes(src.read_bytes())
    row = health_row(dest)
    assert row["so_dieu"]
    assert int(row["so_dieu"]) >= 3
    assert int(row["co_cum_phat_tien_tu"]) == 1
    out = tmp_path / "h.csv"
    write_csv([row], out)
    text = out.read_text(encoding="utf-8")
    assert "so_hieu" in text
    assert "_TONG" in text
    assert "ty_le_xu_phat" in text
