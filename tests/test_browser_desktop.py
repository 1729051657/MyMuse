from __future__ import annotations

import asyncio
import socketserver
import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from nanomuse.config import Settings, load_settings
from nanomuse.llm import MockLLM
from nanomuse.server import browser_desktop as desktop_module
from nanomuse.server import create_app
from nanomuse.server.browser_desktop import BrowserDesktop
from nanomuse.server.service import MuseService
from nanomuse.tools.browser_backends import PlaywrightBackend


@pytest.fixture
def desktop_api(settings: Settings):
    settings.server.token = "desktop-test-token"
    settings.browser.enabled = True
    service = MuseService(settings, llm=MockLLM([]))
    with TestClient(create_app(settings, service)) as client:
        client.headers["Authorization"] = "Bearer desktop-test-token"
        yield client, service


def test_desktop_environment_enables_the_visible_shared_browser(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("NANOMUSE_BROWSER_DESKTOP", "1")
    config = tmp_path / "config.toml"
    config.write_text("")
    settings = load_settings(config)
    assert settings.browser.enabled and settings.browser.desktop
    assert not settings.browser.headless
    assert settings.browser.backend == "playwright"


def test_desktop_availability_and_workspace_folder_boundary(desktop_api):
    client, service = desktop_api
    assert client.get("/api/browser/desktop").json()["available"] is False
    assert client.get("/api/browser/desktop/clipboard").status_code == 404
    assert (
        client.get("/api/browser/desktop", headers={"Authorization": "Bearer wrong"}).status_code
        == 401
    )
    workspace = service.workspace()
    (workspace / "downloads").mkdir()
    (workspace / "attachments").mkdir()
    (workspace / "downloads" / "report.txt").write_text("downloaded")
    (workspace / "attachments" / "upload.txt").write_text("uploaded")
    rows = client.get("/api/files?folder=downloads").json()
    assert [row["path"] for row in rows] == ["downloads/report.txt"]
    assert client.get("/api/files?folder=../").status_code == 403
    assert client.get("/api/files?folder=missing").json() == []


def test_desktop_websocket_authentication_precedes_binary_transport(desktop_api, monkeypatch):
    client, service = desktop_api

    class RFBServer(socketserver.BaseRequestHandler):
        def handle(self):
            self.request.sendall(b"RFB 003.008\n")
            while data := self.request.recv(1024):
                self.request.sendall(data)

    with socketserver.TCPServer(("127.0.0.1", 0), RFBServer) as upstream:
        worker = threading.Thread(target=upstream.serve_forever, daemon=True)
        worker.start()
        monkeypatch.setattr(desktop_module, "VNC_PORT", upstream.server_address[1])
        desktop = BrowserDesktop(service.workspace())
        # The Linux processes are an external boundary; the proxy and auth run unchanged.
        desktop.processes = [
            SimpleNamespace(returncode=None, terminate=lambda: None, wait=AsyncMock())
        ]
        service.browser_desktop = desktop
        assert client.get("/api/browser/desktop").json()["available"] is True
        for payload in (
            {"kind": "auth", "token": "wrong"},
            {"kind": "send", "token": "desktop-test-token"},
        ):
            with pytest.raises(WebSocketDisconnect) as closed:
                with client.websocket_connect("/api/browser/desktop/ws") as ws:
                    ws.send_json(payload)
                    ws.receive_json()
            assert closed.value.code == 4401
        with pytest.raises(WebSocketDisconnect) as closed:
            with client.websocket_connect("/api/browser/desktop/ws?token=desktop-test-token") as ws:
                ws.receive_json()
        assert closed.value.code == 4401
        with client.websocket_connect("/api/browser/desktop/ws") as ws:
            ws.send_json({"kind": "auth", "token": "desktop-test-token"})
            assert ws.receive_json() == {"kind": "ready"}
            assert ws.receive_bytes() == b"RFB 003.008\n"
            ws.send_bytes(b"native mouse and keyboard")
            assert ws.receive_bytes() == b"native mouse and keyboard"
        upstream.shutdown()
        worker.join()


async def test_clipboard_sends_utf8_to_the_operating_system(tmp_path: Path, monkeypatch):
    child = SimpleNamespace(returncode=0, communicate=AsyncMock(return_value=(b"", b"")))
    spawn = AsyncMock(return_value=child)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)
    desktop = BrowserDesktop(tmp_path)
    await desktop.write_clipboard("中文粘贴与登录状态")
    assert spawn.await_args.args == ("xclip", "-selection", "clipboard", "-in")
    child.communicate.assert_awaited_once_with("中文粘贴与登录状态".encode())
    child.communicate.return_value = ("从云端复制".encode(), b"")
    assert await desktop.read_clipboard() == "从云端复制"


async def test_desktop_shutdown_lets_chromium_save_its_session(tmp_path: Path) -> None:
    cdp = SimpleNamespace(send=AsyncMock())
    browser = SimpleNamespace(
        is_connected=lambda: True,
        new_browser_cdp_session=AsyncMock(return_value=cdp),
        close=AsyncMock(),
    )
    process = SimpleNamespace(
        returncode=None, terminate=Mock(), kill=Mock(), wait=AsyncMock(return_value=0)
    )
    backend = PlaywrightBackend(tmp_path / "browser-profile", desktop=True)
    backend._desktop_browser = browser
    backend._desktop_process = process

    await backend.close()

    cdp.send.assert_awaited_once_with("Browser.close")
    process.wait.assert_awaited_once()
    process.terminate.assert_not_called()
    process.kill.assert_not_called()
    browser.close.assert_awaited_once()
