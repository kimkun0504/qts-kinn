import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Board, LedgerPage } from "../lib/api";
import { PaperPage } from "./PaperPage";

afterEach(cleanup);

const page: LedgerPage = {
  schema: "paper-ledger-1",
  name: "after_hours",
  title: "After-hours short",
  strategy: "after_hours",
  side: "short",
  rule: "Sold short after a 15% fall after hours.",
  alternative: "Held to 15:30",
  benchmark: null,
  stake: 2000,
  command: "uv run python tools/owner/paper_after_hours.py",
  schedule: "each morning after 09:35",
  updated: "2026-11-19T21:59:00+00:00",
  evenings: 2,
  last_evening: "2026-11-18",
  summary: { signals: 2, closed: 2, open: 0, waiting: 0, mean: 0.0467, winners: 1, profit: 561, alternative: 0.03, alternative_count: 2, over_benchmark: null, set_aside: 0, set_aside_closed: 0, set_aside_mean: null, borrow_recorded: 1 },
  rows: [
    { day: "2026-11-16", symbol: "RCAT", market_cap: 5.39e8, entry_day: "2026-11-16", entry: 2.88, exit_day: null, exit: 2.55, gross: 0.11, net: 0.111, alternative: 0.18, benchmark: null, status: "closed", set_aside: false, move: -0.19, accepted: "16:06", thin: false, borrow: "yes, 4%" },
    { day: "2026-11-10", symbol: "BV", market_cap: 1.06e9, entry_day: "2026-11-10", entry: 9.55, exit_day: null, exit: 9.73, gross: -0.02, net: -0.021, alternative: -0.04, benchmark: null, status: "closed", set_aside: false, move: -0.17, accepted: "16:15", thin: true, borrow: null },
  ],
  curve: [
    { day: "2026-11-10", symbol: "BV", total: -42 },
    { day: "2026-11-16", symbol: "RCAT", total: 180 },
  ],
  evening_rows: [
    { day: "2026-11-18", filers: 195, looked_at: 15, signals: 0, note: "read in part" },
    { day: "2026-11-11", filers: 0, looked_at: 0, signals: 0, note: "SEC closed" },
  ],
};

const board = { rows: [], others: [], waiting: [], counts: {} } as unknown as Board;

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      const body = url === "/api/ledgers" ? [page] : url === "/api/ledgers/after_hours" ? page : null;
      return { ok: body !== null, status: body ? 200 : 404, json: async () => body } as Response;
    }),
  );
});

describe("the paper page", () => {
  it("shows an event ledger with its numbers, evenings and signals", async () => {
    render(<PaperPage board={board} name="after_hours" onOpen={() => {}} />);
    await waitFor(() => expect(screen.getByText("Sold short after a 15% fall after hours.")).toBeTruthy());
    expect(screen.getByRole("tab", { name: "After-hours short" }).getAttribute("aria-selected")).toBe("true");
    expect(screen.getByText("+4.67%")).toBeTruthy();
    expect(screen.getByText("1 of 2")).toBeTruthy();
    expect(screen.getByText("SEC closed")).toBeTruthy();
    expect(screen.getByText("yes, 4%")).toBeTruthy();
    expect(screen.getByRole("link", { name: "RCAT" }).getAttribute("href")).toBe("#/stock/RCAT");
  });

  it("sorts the signals by a column", async () => {
    render(<PaperPage board={board} name="after_hours" onOpen={() => {}} />);
    await waitFor(() => expect(screen.getByRole("link", { name: "RCAT" })).toBeTruthy());
    const order = () => screen.getAllByRole("link").map((a) => a.textContent);
    expect(order()).toEqual(["RCAT", "BV"]);
    fireEvent.click(screen.getByRole("button", { name: /After costs/ }));
    expect(order()).toEqual(["RCAT", "BV"]);
    fireEvent.click(screen.getByRole("button", { name: /After costs/ }));
    expect(order()).toEqual(["BV", "RCAT"]);
  });
});
