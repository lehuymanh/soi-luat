"""Kế hoạch P1, N2: JS/CSS phục vụ từ static/, không cache cũ, token CSRF đọc lại sau khi app khởi động lại."""

from pathlib import Path

from fastapi.testclient import TestClient

from soiluat import app as app_mod
from soiluat.app import app

TEMPLATE = Path(app_mod.__file__).parent / "templates" / "index.html"


def test_static_js_css_no_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("SOILUAT_DATA", str(tmp_path))
    c = TestClient(app)
    js = c.get("/static/app.js")
    assert js.status_code == 200 and "javascript" in js.headers["content-type"]
    assert "no-cache" in js.headers["cache-control"]
    css = c.get("/static/app.css")
    assert css.status_code == 200 and "text/css" in css.headers["content-type"]


def test_static_qua_host_guard(tmp_path, monkeypatch):
    monkeypatch.setenv("SOILUAT_DATA", str(tmp_path))
    monkeypatch.delenv("SOILUAT_ALLOW_TEST_HOST", raising=False)
    assert TestClient(app).get("/static/app.js").status_code == 400  # Host "testserver" bị chặn


def test_trang_chu_dung_static_khong_nhung_token_vao_script(tmp_path, monkeypatch):
    monkeypatch.setenv("SOILUAT_DATA", str(tmp_path))
    assert "tojson" not in TEMPLATE.read_text(encoding="utf-8")
    html = TestClient(app).get("/").text
    assert 'src="/static/app.js' in html and 'href="/static/app.css' in html
    assert "data-csrf=" in html and "data-suffixes=" in html


def test_403_mang_cookie_moi_de_post_gui_lai(tmp_path, monkeypatch):
    """app.js gặp 403 thì đọc lại cookie và gửi lại một lần: 403 phải mang Set-Cookie token mới."""
    monkeypatch.setenv("SOILUAT_DATA", str(tmp_path))
    monkeypatch.delenv("SOILUAT_ALLOW_TEST_HOST", raising=False)
    h = {"Host": "127.0.0.1:8000"}
    c = TestClient(app)
    old = c.get("/", headers=h).cookies.get("soiluat_csrf_8000")
    monkeypatch.setattr(app_mod, "CSRF_TOKEN", "token-sau-khi-khoi-dong-lai")
    r = c.post("/backup", headers={**h, "X-CSRF-Token": old})
    assert r.status_code == 403
    new = r.cookies.get("soiluat_csrf_8000")
    assert new == "token-sau-khi-khoi-dong-lai"
    assert c.post("/backup", headers={**h, "X-CSRF-Token": new}).status_code == 200


def test_phong_nhung_khong_tai_tu_ngoai(tmp_path, monkeypatch):
    """G0: phông Be Vietnam Pro đóng kèm trong static/fonts; không chỗ nào dẫn Google Fonts (nguyên tắc 8)."""
    import re

    monkeypatch.setenv("SOILUAT_DATA", str(tmp_path))
    c = TestClient(app)
    css = c.get("/static/app.css").text
    assert "@font-face" in css and "font-display: swap" in css
    fonts = re.findall(r'url\("(fonts/[^"]+\.woff2)"\)', css)
    assert len(fonts) == 9
    for f in fonts:
        r = c.get("/static/" + f)
        assert r.status_code == 200 and r.headers["content-type"] == "font/woff2", f
    pkg = Path(app_mod.__file__).parent
    assert (pkg / "static" / "fonts" / "OFL.txt").exists()
    for p in [*(pkg / "static").rglob("*"), *(pkg / "templates").rglob("*")]:
        if p.suffix in {".css", ".js", ".html"}:
            t = p.read_text(encoding="utf-8")
            assert "googleapis" not in t and "gstatic" not in t, p


def test_trang_chu_co_khung_moi(tmp_path, monkeypatch):
    monkeypatch.setenv("SOILUAT_DATA", str(tmp_path))
    html = TestClient(app).get("/").text
    for needle in ('class="side"', 'id="btn-import"', 'id="btn-settings"', 'id="composer"', 'id="open-side"', "0 văn bản", "Kho chưa có văn bản"):
        assert needle in html, needle


def test_app_js_doc_dung_cookie_theo_cong_nhu_may_chu():
    """S4: app.py đặt cookie `soiluat_csrf_<cổng>`; app.js phải đọc đúng tên đó theo location.port."""
    js = (Path(app_mod.__file__).parent / "static" / "app.js").read_text(encoding="utf-8")
    assert "soiluat_csrf_${location.port}" in js and "soiluat_csrf=" not in js
