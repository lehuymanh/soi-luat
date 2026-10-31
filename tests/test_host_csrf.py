from fastapi.testclient import TestClient


def test_host_and_csrf(tmp_path, monkeypatch):
    monkeypatch.setenv("SOILUAT_DATA", str(tmp_path))
    monkeypatch.delenv("SOILUAT_ALLOW_TEST_HOST", raising=False)
    from soiluat.app import app

    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 400
    ok = client.get("/", headers={"Host": "127.0.0.1:8000"})
    assert ok.status_code == 200
    denied = client.post("/backup", headers={"Host": "127.0.0.1:8000"})
    assert denied.status_code == 403
    token = ok.cookies.get("soiluat_csrf_8000")
    assert token
    good = client.post(
        "/backup",
        headers={"Host": "127.0.0.1:8000"},
        data={"csrf_token": token},
    )
    assert good.status_code == 200
    assert good.json()["ok"] is True
    assert not any(k.lower() == "access-control-allow-origin" for k in ok.headers)


def test_s4_hai_ban_app_cong_khac_nhau_khong_ghi_de_cookie_cua_nhau(tmp_path, monkeypatch):
    """S4, SEC-4, F6: cookie không phân biệt cổng. Hai bản app (cổng 8001, 8002) cùng một trình duyệt: sau khi bản B
    trả lời, POST vào bản A bằng token của A vẫn phải qua (trước đây 403 vì cookie chung bị B ghi đè)."""
    from soiluat import app as appmod

    monkeypatch.setenv("SOILUAT_DATA", str(tmp_path))
    monkeypatch.delenv("SOILUAT_ALLOW_TEST_HOST", raising=False)
    client = TestClient(appmod.app)  # một lọ cookie dùng chung, như trình duyệt
    a, b = {"Host": "127.0.0.1:8001"}, {"Host": "127.0.0.1:8002"}
    monkeypatch.setattr(appmod, "CSRF_TOKEN", "token-ban-a")
    client.get("/", headers=a)
    monkeypatch.setattr(appmod, "CSRF_TOKEN", "token-ban-b")
    client.get("/api/status", headers=b)  # bản B trả lời (thăm dò mỗi giây khi đang nạp file)
    monkeypatch.setattr(appmod, "CSRF_TOKEN", "token-ban-a")  # lại là tiến trình của bản A
    assert client.post("/backup", headers={**a, "X-CSRF-Token": "token-ban-a"}).status_code == 200
    monkeypatch.setattr(appmod, "CSRF_TOKEN", "token-ban-b")
    assert client.post("/backup", headers={**b, "X-CSRF-Token": "token-ban-b"}).status_code == 200


def test_sec2_post_tu_nguon_khac_bi_chan_du_co_cookie_va_token(tmp_path, monkeypatch):
    """SEC-2: trang ở nguồn khác trên cùng máy (cổng khác) đọc được cookie rồi gửi POST đơn giản: có Origin lạ thì 403,
    không đụng tới kho; Origin cùng nguồn (như trình duyệt gửi từ trang của app) và không Origin (curl) vẫn qua."""
    from soiluat import app as appmod

    monkeypatch.setenv("SOILUAT_DATA", str(tmp_path))
    monkeypatch.delenv("SOILUAT_ALLOW_TEST_HOST", raising=False)
    client = TestClient(appmod.app)
    h = {"Host": "127.0.0.1:8000"}
    token = client.get("/", headers=h).cookies.get("soiluat_csrf_8000")
    assert token
    bak = tmp_path / "backup" / "soiluat.db"
    for origin in ("http://localhost:3000", "http://127.0.0.1:3000", "https://evil.example", "null"):
        r = client.post("/backup", headers={**h, "Origin": origin}, data={"csrf_token": token})
        assert r.status_code == 403, origin
        assert not bak.exists(), origin
    assert client.post("/backup", headers={**h, "Origin": "http://127.0.0.1:8000"}, data={"csrf_token": token}).status_code == 200
    assert client.post("/backup", headers=h, data={"csrf_token": token}).status_code == 200
