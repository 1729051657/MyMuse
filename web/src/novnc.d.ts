declare module "@novnc/novnc" {
  export default class RFB extends EventTarget {
    constructor(target: HTMLElement, channel: WebSocket, options?: { shared?: boolean });
    viewOnly: boolean;
    scaleViewport: boolean;
    resizeSession: boolean;
    showDotCursor: boolean;
    qualityLevel: number;
    compressionLevel: number;
    focus(): void;
    disconnect(): void;
    sendKey(keysym: number, code?: string, down?: boolean): void;
  }
}
