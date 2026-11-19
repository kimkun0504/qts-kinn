import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { type Command, CommandPalette, rank, score } from "./CommandPalette";

afterEach(cleanup);

const commands: Command[] = [
  { id: "p1", group: "Pages", label: "Runs", href: "#/runs" },
  { id: "p2", group: "Pages", label: "Lab", href: "#/lab" },
  { id: "s1", group: "Strategies", label: "Earnings drift", keywords: "earnings_drift", href: "#/strategy/earnings_drift" },
  { id: "r1", group: "Runs", label: "rebound_limit", hint: "base_o0", keywords: "base_o0 run1", href: "#/runs/run1" },
];

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn(async () => ({ ok: true, status: 200, json: async () => [] }) as unknown as Response));
  localStorage.clear();
  window.location.hash = "";
});

describe("scoring", () => {
  it("prefers a prefix, then a word start, then anywhere, then letters in order", () => {
    expect(score("Earnings drift", "earn")).toBe(0);
    expect(score("Earnings drift", "drift")).toBe(1);
    expect(score("Earnings drift", "nings")).toBe(2);
    expect(score("Earnings drift", "edt")).toBe(3);
    expect(score("Earnings drift", "zz")).toBeNull();
  });

  it("shows the watchlist with no query and the screens with one", () => {
    const more: Command[] = [...commands, { id: "w1", group: "Watchlist", label: "AAPL" }, { id: "c1", group: "Screens", label: "Small caps" }];
    expect(rank(more, "").map((c) => c.id)).toEqual(["p1", "p2", "w1"]);
    expect(rank(more, "small").map((c) => c.id)).toEqual(["c1"]);
  });

  it("shows pages with no query and searches every group with one", () => {
    expect(rank(commands, "").map((c) => c.id)).toEqual(["p1", "p2"]);
    expect(rank(commands, "base").map((c) => c.id)).toEqual(["r1"]);
    expect(rank(commands, "drift").map((c) => c.id)).toEqual(["s1"]);
  });
});

describe("the palette", () => {
  it("opens the chosen item with the keyboard", () => {
    const onClose = vi.fn();
    render(<CommandPalette open onClose={onClose} commands={commands} />);
    const input = screen.getByRole("textbox", { name: "Search" });
    fireEvent.change(input, { target: { value: "earn" } });
    expect(screen.getByRole("option", { name: /Earnings drift/ }).getAttribute("aria-selected")).toBe("true");
    fireEvent.keyDown(input, { key: "Enter" });
    expect(onClose).toHaveBeenCalled();
    expect(window.location.hash).toBe("#/strategy/earnings_drift");
  });

  it("closes on Escape", () => {
    const onClose = vi.fn();
    render(<CommandPalette open onClose={onClose} commands={commands} />);
    fireEvent.keyDown(screen.getByRole("textbox", { name: "Search" }), { key: "Escape" });
    expect(onClose).toHaveBeenCalled();
  });
});
