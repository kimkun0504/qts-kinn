import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { sections, slug } from "../components/Markdown";
import { GuidePage } from "./GuidePage";

afterEach(cleanup);

const text = "# The Lab\n\nIntro.\n\n## Write an algorithm\n\nText.\n\n```\n## not a heading\n```\n\n## Where things are `kept`\n\nMore.\n";

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ name: "LAB.md", text }))));
});

describe("the guide", () => {
  it("lists the sections outside code blocks", () => {
    expect(sections(text)).toEqual([
      { title: "Write an algorithm", anchor: "write-an-algorithm" },
      { title: "Where things are kept", anchor: "where-things-are-kept" },
    ]);
    expect(slug("Results, and **why**")).toBe("results-and-why");
  });

  it("shows a guide with its sections and switches to the shortcuts", async () => {
    const onGuide = vi.fn();
    render(<GuidePage onGuide={onGuide} />);
    expect(await screen.findByRole("link", { name: "Write an algorithm" })).toBeTruthy();
    expect(document.getElementById("where-things-are-kept")).toBeTruthy();
    fireEvent.click(screen.getByRole("tab", { name: "Keyboard shortcuts" }));
    expect(onGuide).toHaveBeenCalledWith("keys");
  });
});
