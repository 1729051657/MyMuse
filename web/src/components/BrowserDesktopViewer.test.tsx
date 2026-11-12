import { act } from "react";
import { create, type ReactTestRenderer } from "react-test-renderer";
import { afterEach, expect, it, vi } from "vitest";
import { api } from "../api";
import { setLocaleSetting } from "../i18n";
import BrowserDesktopViewer from "./BrowserDesktopViewer";

(globalThis as Record<string, unknown>).IS_REACT_ACT_ENVIRONMENT = true;
const store = vi.hoisted(() => ({ state: { holds: [{ thread: "main", tool: "browser" }] }, toast: vi.fn() }));
vi.mock("../store", () => ({ useStore: () => store }));
const protocol = vi.hoisted(() => ({ paste: vi.fn(), key: vi.fn() }));
vi.mock("@novnc/novnc", () => ({ default: class extends EventTarget {
  clipboardPasteFrom = protocol.paste;
  sendKey = protocol.key;
  disconnect = vi.fn();
  focus = vi.fn();
} }));
vi.mock("./Sheet", () => ({ Sheet: ({ open, children, footer }: { open: boolean; children: import("react").ReactNode; footer: import("react").ReactNode }) => open ? <section>{children}{footer}</section> : null }));
let view: ReactTestRenderer | undefined;
afterEach(() => {
  act(() => view?.unmount());
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

it("keeps the remote connection when live chat state changes the toast callback", async () => {
  vi.stubGlobal("window", { location: { protocol: "http:", host: "example.org" } });
  vi.stubGlobal("localStorage", { getItem: () => null, setItem: () => undefined });
  vi.stubGlobal("document", { documentElement: { lang: "en" } });
  setLocaleSetting("en");
  const sockets: { close: ReturnType<typeof vi.fn> }[] = [];
  vi.stubGlobal("WebSocket", class {
    close = vi.fn();
    constructor() { sockets.push(this); }
  });
  vi.spyOn(api, "browserControl").mockResolvedValue({ url: "about:blank", title: "" });
  const props = { thread: "main", workspace: "/workspace", onClose: vi.fn() };
  await act(async () => {
    view = create(<BrowserDesktopViewer {...props} />, { createNodeMock: () => ({}) });
  });
  expect(sockets).toHaveLength(1);
  store.toast = vi.fn();
  store.state = { ...store.state, holds: [...store.state.holds] };
  await act(async () => { view!.update(<BrowserDesktopViewer {...props} />); });
  expect(api.browserControl).toHaveBeenCalledTimes(1);
  expect(sockets).toHaveLength(1);
  expect(sockets[0].close).not.toHaveBeenCalled();
});

it("writes Unicode through the account clipboard before sending the paste keys", async () => {
  vi.stubGlobal("window", { location: { protocol: "http:", host: "example.org" } });
  vi.stubGlobal("localStorage", { getItem: () => null, setItem: () => undefined });
  vi.stubGlobal("document", { documentElement: { lang: "en" } });
  setLocaleSetting("en");
  let ready!: (event: { data: string }) => void;
  vi.stubGlobal("WebSocket", class {
    close = vi.fn();
    set onmessage(handler: (event: { data: string }) => void) { ready = handler; }
  });
  vi.spyOn(api, "browserControl").mockResolvedValue({ url: "about:blank", title: "" });
  vi.spyOn(api, "browserClipboard").mockResolvedValue({ text: "old clipboard" });
  vi.spyOn(api, "setBrowserClipboard").mockResolvedValue({ ok: true });
  await act(async () => { view = create(<BrowserDesktopViewer thread="main" workspace="/workspace" onClose={vi.fn()} />, { createNodeMock: () => ({}) }); });
  act(() => ready({ data: JSON.stringify({ kind: "ready" }) }));
  const button = (label: string) => view!.root.findAllByType("button").find((node) => node.children.includes(label))!;
  await act(async () => { button("Clipboard / Chinese input").props.onClick(); });
  act(() => view!.root.findByType("textarea").props.onChange({ target: { value: "中文登录验收" } }));
  await act(async () => { button("Paste into cloud browser").props.onClick(); });
  expect(api.setBrowserClipboard).toHaveBeenCalledWith("中文登录验收");
  expect(protocol.paste).not.toHaveBeenCalled();
  const pasteOrder = vi.mocked(api.setBrowserClipboard).mock.invocationCallOrder;
  expect(pasteOrder[pasteOrder.length - 1]).toBeLessThan(protocol.key.mock.invocationCallOrder[0]);
});
