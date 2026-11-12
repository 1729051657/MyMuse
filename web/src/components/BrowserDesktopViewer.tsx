import RFB from "@novnc/novnc";
import { Check, Clipboard, Download, Expand, Folder, Globe, Hand, Loader2, Maximize2, RefreshCw, Upload } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { api, fileUrl, getToken } from "../api";
import { useT } from "../i18n";
import { useStore } from "../store";
import type { FileInfo } from "../types";
import { Sheet } from "./Sheet";

const CTRL = 0xffe3;
const SHORTCUTS: [string, number[]][] = [
  ["New tab", [CTRL, 0x74]], ["Close tab", [CTRL, 0x77]], ["Address bar", [CTRL, 0x6c]],
  ["Reload page", [CTRL, 0x72]], ["Back", [0xffe9, 0xff51]], ["Forward", [0xffe9, 0xff53]],
  ["Find on page", [CTRL, 0x66]], ["Select all", [CTRL, 0x61]], ["Copy", [CTRL, 0x63]],
  ["Paste", [CTRL, 0x76]], ["Zoom in", [CTRL, 0x2b]], ["Zoom out", [CTRL, 0x2d]],
  ["Reset zoom", [CTRL, 0x30]], ["Escape", [0xff1b]], ["Tab", [0xff09]],
  ["Shift + Tab", [0xffe1, 0xff09]], ["Enter", [0xff0d]],
];

export default function BrowserDesktopViewer({ thread, workspace, onClose }: { thread: string; workspace: string; onClose: () => void }) {
  const { state, toast } = useStore();
  const toastRef = useRef(toast);
  const t = useT();
  const control = state.holds.some((h) => h.thread === thread && h.tool === "browser");
  const controlRef = useRef(control);
  const root = useRef<HTMLDivElement>(null);
  const screen = useRef<HTMLDivElement>(null);
  const connection = useRef<RFB | null>(null);
  const upload = useRef<HTMLInputElement>(null);
  const [status, setStatus] = useState<"connecting" | "connected" | "disconnected">("connecting");
  const [attempt, setAttempt] = useState(0);
  const [fit, setFit] = useState(true);
  const fitRef = useRef(fit);
  const [busy, setBusy] = useState(false);
  const [panel, setPanel] = useState<"files" | "clipboard" | null>(null);
  const [clipboard, setClipboard] = useState("");
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [lastUpload, setLastUpload] = useState("");

  useEffect(() => { toastRef.current = toast; }, [toast]);

  useEffect(() => {
    let disposed = false;
    let socket: WebSocket | null = null;
    setStatus("connecting");
    void api.browserControl(thread, { action: "look" }).catch((err: Error) => {
      if (!disposed) toastRef.current(err.message);
    });
    const connect = () => {
      if (disposed || !screen.current) return;
      const scheme = window.location.protocol === "https:" ? "wss:" : "ws:";
      socket = new WebSocket(`${scheme}//${window.location.host}/api/browser/desktop/ws`);
      socket.binaryType = "arraybuffer";
      socket.onopen = () => socket?.send(JSON.stringify({ kind: "auth", token: getToken() }));
      socket.onclose = () => { if (!disposed) setStatus("disconnected"); };
      socket.onerror = () => { if (!disposed) setStatus("disconnected"); };
      socket.onmessage = (event) => {
        if (disposed || !screen.current || !socket || typeof event.data !== "string") return;
        const message = JSON.parse(event.data) as { kind?: string };
        if (message.kind !== "ready") return;
        socket.onmessage = null;
        const rfb = new RFB(screen.current, socket, { shared: true });
        connection.current = rfb;
        rfb.viewOnly = !controlRef.current;
        rfb.scaleViewport = fitRef.current;
        rfb.resizeSession = fitRef.current;
        rfb.showDotCursor = true;
        rfb.qualityLevel = 7;
        rfb.compressionLevel = 2;
        rfb.addEventListener("connect", () => { if (!disposed) setStatus("connected"); });
        rfb.addEventListener("disconnect", () => { if (!disposed) setStatus("disconnected"); });
      };
    };
    connect();
    return () => {
      disposed = true;
      connection.current?.disconnect();
      connection.current = null;
      socket?.close();
    };
  }, [attempt, thread]);

  useEffect(() => {
    controlRef.current = control;
    if (connection.current) connection.current.viewOnly = !control;
  }, [control]);
  useEffect(() => {
    fitRef.current = fit;
    if (connection.current) {
      connection.current.scaleViewport = fit;
      connection.current.resizeSession = fit;
    }
  }, [fit]);

  const sendKeys = (keys: number[]) => {
    const rfb = connection.current;
    if (!control || !rfb) return;
    for (const key of keys) rfb.sendKey(key, undefined, true);
    for (const key of [...keys].reverse()) rfb.sendKey(key, undefined, false);
    rfb.focus();
  };

  const takeOver = async () => {
    setBusy(true);
    try { await api.browserControl(thread, { action: "take_over" }); }
    catch (err) { toast((err as Error).message); }
    finally { setBusy(false); }
  };
  const done = async () => {
    setBusy(true);
    try {
      if (control) await api.browserControl(thread, { action: "handed_back" });
      if (document.fullscreenElement === root.current) await document.exitFullscreen();
      onClose();
    } catch (err) { toast((err as Error).message); }
    finally { setBusy(false); }
  };
  const fullscreen = async () => {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await root.current?.requestFullscreen();
    } catch (err) { toast((err as Error).message); }
  };
  const showFiles = async () => {
    setPanel("files");
    try {
      const [downloads, uploads] = await Promise.all([api.files(100, "downloads"), api.files(100, "attachments")]);
      setFiles([...downloads, ...uploads].sort((a, b) => b.modified.localeCompare(a.modified)));
    } catch (err) { toast((err as Error).message); }
  };
  const showClipboard = async () => {
    setBusy(true);
    try {
      setClipboard((await api.browserClipboard()).text);
      setPanel("clipboard");
    }
    catch (err) { toast((err as Error).message); }
    finally { setBusy(false); }
  };
  const paste = async () => {
    setBusy(true);
    try {
      await api.setBrowserClipboard(clipboard);
      setPanel(null);
      sendKeys([CTRL, 0x76]);
    } catch (err) { toast((err as Error).message); }
    finally { setBusy(false); }
  };
  const copy = async () => {
    try { await navigator.clipboard.writeText(clipboard); toast(t("Copied")); }
    catch (err) { toast((err as Error).message); }
  };
  const uploadFiles = async (selected: FileList | null) => {
    if (!selected?.length) return;
    setBusy(true);
    try {
      for (const file of selected) {
        const result = await api.upload(file);
        setLastUpload(`${workspace}/${result.path}`);
      }
      await showFiles();
    } catch (err) { toast((err as Error).message); }
    finally { setBusy(false); if (upload.current) upload.current.value = ""; }
  };
  const button = "inline-flex items-center gap-1.5 rounded-xl bg-surface-2 px-3 py-2 text-[13px] disabled:opacity-40";

  return (
    <div ref={root} role="dialog" aria-modal="true" aria-label={t("Cloud browser")} className="fixed inset-0 z-50 flex flex-col bg-surface text-fg">
      <header className="flex flex-wrap items-center gap-2 border-b border-border px-3 py-2">
        <Globe size={19} className="text-accent" />
        <span className="mr-1 font-semibold">{t("Cloud browser")}</span>
        <span role="status" className="text-[12px] text-muted">{status === "connected" ? (control ? t("You have control") : t("Watching")) : status === "connecting" ? t("Connecting…") : t("Connection lost")}</span>
        <div className="flex-1" />
        <button type="button" className={button} aria-label={t("Reopen browser")} title={t("Reopen browser")} onClick={() => void api.browserControl(thread, { action: "look" }).catch((err: Error) => toast(err.message))}><RefreshCw size={16} /></button>
        <button type="button" className={button} onClick={() => void showFiles()}><Folder size={16} />{t("Files")}</button>
        <button type="button" className={button} disabled={!control || busy} onClick={() => void showClipboard()}><Clipboard size={16} />{t("Clipboard / Chinese input")}</button>
        <select aria-label={t("Browser shortcuts")} value="" disabled={!control || status !== "connected"} onChange={(e) => sendKeys(SHORTCUTS[Number(e.target.value)][1])} className="max-w-36 rounded-xl bg-surface-2 px-2 py-2 text-[13px] disabled:opacity-40">
          <option value="" disabled>{t("Browser shortcuts")}</option>
          {SHORTCUTS.map(([label], index) => <option value={index} key={label}>{t(label)}</option>)}
        </select>
        <button type="button" className={button} aria-pressed={fit} onClick={() => setFit(!fit)}><Expand size={16} />{fit ? t("Fit to window") : t("Actual size")}</button>
        <button type="button" className={button} aria-label={t("Full screen")} onClick={() => void fullscreen()}><Maximize2 size={16} /></button>
        {!control && <button type="button" className={button} disabled={busy} onClick={() => void takeOver()}><Hand size={16} />{t("Take over")}</button>}
        <button type="button" className="inline-flex items-center gap-1.5 rounded-xl bg-accent px-3 py-2 text-[13px] font-medium text-accent-fg disabled:opacity-40" disabled={busy} onClick={() => void done()}>{busy ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />}{control ? t("Done, hand back") : t("Close")}</button>
      </header>
      <div className="relative min-h-0 flex-1 bg-neutral-900">
        <div ref={screen} className="h-full w-full overflow-auto" aria-label={t("Remote browser screen")} />
        {status !== "connected" && <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-surface/95">
          {status === "connecting" ? <Loader2 size={28} className="animate-spin" /> : <><p>{t("The browser connection was interrupted. Your tabs and login profile stay in the cloud.")}</p><button type="button" className={button} onClick={() => setAttempt(attempt + 1)}><RefreshCw size={16} />{t("Reconnect")}</button></>}
        </div>}
      </div>
      <div className="border-t border-border px-3 py-1 text-[12px] text-muted">{t("Use the browser's tabs and address bar directly. Use the clipboard panel for Chinese text. Login data stays in this account's browser profile.")}</div>

      <Sheet open={panel === "clipboard"} title={t("Clipboard / Chinese input")} onClose={() => setPanel(null)} footer={<div className="flex gap-2"><button type="button" className={button} onClick={() => void copy()}>{t("Copy to this device")}</button><button type="button" className={button} disabled={!control || busy} onClick={() => void paste()}>{t("Paste into cloud browser")}</button></div>}>
        <p className="mb-3 text-[13px] text-muted">{t("Click the target field in the cloud browser first. Enter or paste text here, then paste it into that field. To copy from the cloud, select text there and press Ctrl+C before opening this panel.")}</p>
        <textarea aria-label={t("Clipboard text")} value={clipboard} maxLength={65536} onChange={(e) => setClipboard(e.target.value)} rows={8} className="w-full resize-y rounded-2xl bg-surface-2 p-3 text-[14px] outline-none" />
      </Sheet>
      <Sheet open={panel === "files"} title={t("Browser files")} onClose={() => setPanel(null)} footer={<button type="button" className={button} disabled={busy} onClick={() => upload.current?.click()}>{busy ? <Loader2 size={16} className="animate-spin" /> : <Upload size={16} />}{t("Upload to cloud")}</button>}>
        <p className="mb-3 text-[13px] text-muted">{t("Uploaded files appear in Home/Uploads in the cloud file picker. Website downloads appear here and can be saved to this device.")}</p>
        {lastUpload && <p className="mb-3 break-all rounded-xl bg-surface-2 p-3 text-[12px]">{t("Uploaded to {path}", { path: lastUpload })}</p>}
        <div className="space-y-2">{files.length === 0 ? <p className="text-[13px] text-muted">{t("No browser files yet.")}</p> : files.map((file) => <div key={file.path} className="flex items-center gap-3 rounded-xl bg-surface-2 px-3 py-2"><div className="min-w-0 flex-1"><p className="truncate text-[14px]">{file.name}</p><p className="truncate text-[12px] text-muted">{file.path}</p></div><a href={fileUrl(file.path, true)} download={file.name} aria-label={t("Download {name}", { name: file.name })} className="rounded-xl p-2"><Download size={17} /></a></div>)}</div>
      </Sheet>
      <input ref={upload} type="file" multiple className="hidden" aria-label={t("Upload to cloud")} onChange={(e) => void uploadFiles(e.target.files)} />
    </div>
  );
}
