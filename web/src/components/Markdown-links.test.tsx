import { act } from "react";
import { create, type ReactTestRenderer } from "react-test-renderer";
import { describe, expect, it, vi } from "vitest";
import { Markdown } from "./Markdown";

(globalThis as Record<string, unknown>).IS_REACT_ACT_ENVIRONMENT = true;

describe("workspace links in model replies", () => {
  it.each([
    "deepseek-live-summary.md",
    "/workspace/deepseek-live-summary.md",
    "sandbox:/workspace/deepseek-live-summary.md",
  ])("opens %s with the existing file viewer callback", (href) => {
    const onOpenFile = vi.fn();
    let renderer!: ReactTestRenderer;
    act(() => {
      renderer = create(
        <Markdown
          text={`[Open summary](${href})`}
          files={["deepseek-live-summary.md"]}
          onOpenFile={onOpenFile}
        />,
      );
    });
    const button = renderer.root.findByType("button");
    act(() => button.props.onClick());
    expect(onOpenFile).toHaveBeenCalledWith("deepseek-live-summary.md");
    expect(renderer.root.findAllByType("a")).toHaveLength(0);
    act(() => renderer.unmount());
  });

  it("decodes a workspace path and keeps external links as links", () => {
    const onOpenFile = vi.fn();
    let renderer!: ReactTestRenderer;
    act(() => {
      renderer = create(
        <Markdown
          text="[Summary](sandbox:/workspace/reports/order%20summary.md) [Website](https://example.com)"
          files={["reports/order summary.md"]}
          onOpenFile={onOpenFile}
        />,
      );
    });
    act(() => renderer.root.findByType("button").props.onClick());
    expect(onOpenFile).toHaveBeenCalledWith("reports/order summary.md");
    expect(renderer.root.findByType("a").props.href).toBe("https://example.com");
    act(() => renderer.unmount());
  });

  it("retains Markdown URL filtering for other protocols", () => {
    let renderer!: ReactTestRenderer;
    act(() => {
      renderer = create(
        <Markdown
          text="[Unknown](sandbox:/etc/passwd) [Script](javascript:alert%281%29)"
          files={["deepseek-live-summary.md"]}
          onOpenFile={vi.fn()}
        />,
      );
    });
    expect(renderer.root.findAllByType("button")).toHaveLength(0);
    expect(renderer.root.findAllByType("a").map((a) => a.props.href)).toEqual(["", ""]);
    act(() => renderer.unmount());
  });
});
