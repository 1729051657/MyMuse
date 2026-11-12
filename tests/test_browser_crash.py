from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from nanomuse.tools.browser import Browser
from nanomuse.tools.browser_backends import PlaywrightBackend


async def test_crashed_page_reopens_the_same_url_with_the_persistent_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    listeners = {}
    old_page = MagicMock()
    old_page.url = "https://example.com/page"
    old_page.is_closed.return_value = False
    old_page.on.side_effect = lambda name, fn: listeners.__setitem__(name, fn)
    old_context = MagicMock()
    old_context.pages = [old_page]
    old_context.close = AsyncMock()
    old_context.route = AsyncMock()

    new_page = MagicMock()
    new_page.url = old_page.url
    new_page.title = AsyncMock(return_value="Example")
    new_page.is_closed.return_value = False
    new_page.goto = AsyncMock()
    new_context = MagicMock()
    new_context.pages = [new_page]
    new_context.route = AsyncMock()
    new_context.close = AsyncMock()

    playwright = MagicMock()
    launch = AsyncMock(side_effect=[old_context, new_context])
    playwright.chromium.launch_persistent_context = launch
    playwright.stop = AsyncMock()
    module = ModuleType("playwright.async_api")
    module.async_playwright = lambda: SimpleNamespace(start=AsyncMock(return_value=playwright))  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "playwright", ModuleType("playwright"))
    monkeypatch.setitem(sys.modules, "playwright.async_api", module)

    backend = PlaywrightBackend(tmp_path / "profile")
    tool = Browser(workspace=tmp_path)
    tool._backend = backend

    async def guard(url: str) -> bool:
        return url.startswith("https://example.com/")

    await backend.set_url_guard(guard)
    await backend.ensure()
    assert "crash" in listeners
    listeners["crash"](old_page)
    assert tool._pick_backend() is backend

    await tool.user_action("look", thread="main")
    assert backend.open
    old_context.close.assert_awaited_once()
    assert len(launch.await_args_list) == 2
    assert all(call.args[0] == str(tmp_path / "profile") for call in launch.await_args_list)
    new_page.goto.assert_awaited_once_with(
        "https://example.com/page", wait_until="domcontentloaded"
    )
    new_context.route.assert_awaited_once()
    await backend.close()
