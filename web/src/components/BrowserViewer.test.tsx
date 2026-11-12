import { act, type ReactNode } from "react";
import { create, type ReactTestRenderer } from "react-test-renderer";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "../api";
import { setLocaleSetting } from "../i18n";
import type { BrowserEvent, HoldEvent } from "../types";
import { BrowserViewer } from "./BrowserViewer";

(globalThis as Record<string, unknown>).IS_REACT_ACT_ENVIRONMENT = true;

const store = vi.hoisted(() => ({
  state: {
    events: {} as Record<string, BrowserEvent[]>,
    holds: [] as HoldEvent[],
    profile: null,
    status: { state: "idle", thread: "main" },
  },
  toast: vi.fn(),
}));
vi.mock("../store", () => ({ useStore: () => store }));
vi.mock("./Sheet", () => ({
  Sheet: ({ children, title, footer }: { children: ReactNode; title: ReactNode; footer: ReactNode }) => (
    <section role="dialog">{title}{children}{footer}</section>
  ),
}));

const frame: BrowserEvent = {
  id: "old-card", type: "browser", thread: "main", ts: "2026-01-01T00:00:00Z",
  url: "https://example.com", title: "Example", action: "Opened page",
  frame: "old-frame", frames: 1, status: "done", backend: "playwright",
};
const hold: HoldEvent = {
  id: "hold", type: "hold", thread: "main", ts: "2026-01-01T00:00:00Z",
  tool: "browser", status: "on", by: "user", reason: "",
};
const views: ReactTestRenderer[] = [];

beforeEach(() => {
  vi.useFakeTimers();
  vi.stubGlobal("window", {
    addEventListener: () => undefined, removeEventListener: () => undefined,
    setInterval, clearInterval, location: { href: "https://example.org/" },
  });
  vi.stubGlobal("localStorage", { getItem: () => null, setItem: () => undefined });
  vi.stubGlobal("document", { hidden: false, documentElement: { lang: "en" } });
  setLocaleSetting("en");
  store.state.events = {};
  store.state.holds = [];
  store.toast.mockClear();
  vi.spyOn(api, "browserControl").mockResolvedValue({ url: frame.url, title: frame.title });
});

afterEach(() => {
  act(() => views.splice(0).forEach((view) => view.unmount()));
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

function render(eventId?: string) {
  let view!: ReactTestRenderer;
  act(() => { view = create(<BrowserViewer thread="main" eventId={eventId} onClose={vi.fn()} />); });
  views.push(view);
  return view;
}

describe("BrowserViewer", () => {
  it("opens the browser controls before the agent has made a frame", () => {
    store.state.holds = [hold];
    const view = render();
    expect(view.root.findByProps({ role: "dialog" })).toBeDefined();
    expect(view.root.findByProps({ "aria-label": "Open a URL…" })).toBeDefined();
    expect(view.root.findAllByType("img")).toHaveLength(0);
  });

  it("refreshes a finished browser card while the user has control", async () => {
    store.state.events.main = [frame];
    store.state.holds = [hold];
    render(frame.id);
    await act(async () => { await vi.advanceTimersByTimeAsync(1000); });
    expect(api.browserControl).toHaveBeenCalledWith("main", { action: "look" });
  });

  it("follows the current frame when taking over an older card", () => {
    store.state.events.main = [frame, { ...frame, id: "new-card", frame: "new-frame" }];
    store.state.holds = [hold];
    const view = render(frame.id);
    expect(view.root.findByType("img").props.src).toContain("new-frame.jpg");
  });

  it("keeps the entered URL when navigation fails", async () => {
    store.state.events.main = [frame];
    store.state.holds = [hold];
    vi.mocked(api.browserControl).mockRejectedValue(new Error("Page could not load"));
    const view = render(frame.id);
    act(() => view.root.findByProps({ "aria-label": "Open a URL…" }).props.onChange({ target: { value: "https://example.org" } }));
    await act(async () => { view.root.findAllByType("form")[1].props.onSubmit({ preventDefault: () => undefined }); });
    expect(view.root.findByProps({ "aria-label": "Open a URL…" }).props.value).toBe("https://example.org");
    expect(store.toast).toHaveBeenCalledWith("Page could not load");
  });
});
