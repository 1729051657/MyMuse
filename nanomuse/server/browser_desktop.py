"""The account's Linux browser desktop. Its RFB port stays on loopback."""

from __future__ import annotations

import asyncio
import contextlib
import os
from pathlib import Path

from starlette.websockets import WebSocket

VNC_PORT = 5900


class BrowserDesktop:
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.processes: list[asyncio.subprocess.Process] = []
        self.lock = asyncio.Lock()

    async def start(self) -> None:
        async with self.lock:
            if self.processes and all(p.returncode is None for p in self.processes):
                return
            await self.stop()
            os.environ["DISPLAY"] = ":99"
            os.environ.setdefault("LANG", "C.UTF-8")
            for name, folder in (("Downloads", "downloads"), ("Uploads", "attachments")):
                target = self.workspace / folder
                target.mkdir(parents=True, exist_ok=True)
                link = Path.home() / name
                if not link.exists():
                    link.symlink_to(target, target_is_directory=True)
            self.processes.append(
                await asyncio.create_subprocess_exec(
                    "Xtigervnc",
                    ":99",
                    "-geometry",
                    "1280x800",
                    "-depth",
                    "24",
                    "-SecurityTypes",
                    "None",
                    "-localhost",
                    "yes",
                    "-rfbport",
                    str(VNC_PORT),
                    "-AlwaysShared",
                    "-desktop",
                    "MyMuse Browser",
                    "-nolisten",
                    "tcp",
                    "-ac",
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
            )
            for _ in range(100):
                if self.processes[0].returncode is not None:
                    raise RuntimeError("the cloud browser desktop could not start")
                if Path("/tmp/.X11-unix/X99").exists():
                    break
                await asyncio.sleep(0.05)
            else:
                raise RuntimeError("the cloud browser desktop did not become ready")
            self.processes.append(
                await asyncio.create_subprocess_exec(
                    "openbox",
                    "--sm-disable",
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
            )

    async def stop(self) -> None:
        for proc in reversed(self.processes):
            if proc.returncode is None:
                with contextlib.suppress(ProcessLookupError):
                    proc.terminate()
                try:
                    await asyncio.wait_for(proc.wait(), 3)
                except TimeoutError:
                    proc.kill()
                    await proc.wait()
        self.processes.clear()

    async def read_clipboard(self) -> str:
        proc = await asyncio.create_subprocess_exec(
            "xclip",
            "-selection",
            "clipboard",
            "-out",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        out, _ = await proc.communicate()
        return out.decode("utf-8", errors="replace") if proc.returncode == 0 else ""

    async def write_clipboard(self, text: str) -> None:
        # xclip forks the selection owner. Its inherited output must not hold a pipe open.
        proc = await asyncio.create_subprocess_exec(
            "xclip",
            "-selection",
            "clipboard",
            "-in",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.communicate(text.encode("utf-8"))
        if proc.returncode != 0:
            raise RuntimeError("the cloud clipboard could not be updated")


async def proxy_desktop(ws: WebSocket) -> None:
    reader, writer = await asyncio.open_connection("127.0.0.1", VNC_PORT)
    await ws.send_json({"kind": "ready"})

    async def to_browser() -> None:
        while data := await reader.read(65536):
            await ws.send_bytes(data)

    async def to_desktop() -> None:
        while True:
            writer.write(await ws.receive_bytes())
            await writer.drain()

    tasks = [asyncio.create_task(to_browser()), asyncio.create_task(to_desktop())]
    try:
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    finally:
        for task in tasks:
            task.cancel()
        writer.close()
        await asyncio.gather(*tasks, return_exceptions=True)
        await writer.wait_closed()
        with contextlib.suppress(RuntimeError):
            await ws.close()
