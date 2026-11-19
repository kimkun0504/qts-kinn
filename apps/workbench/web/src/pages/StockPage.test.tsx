import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { StockPageData } from "../lib/api";
import { StockPage } from "./StockPage";

afterEach(cleanup);

const dates = Array.from({ length: 30 }, (_, i) => `2014-01-${String(i + 1).padStart(2, "0")}`);
const closes = dates.map((_, i) => (i < 15 ? 100 : 50));
const stock: StockPageData = {
  schema: "stock-1",
  query: "ABCD",
  permaticker: 1001,
  ticker: "ABCD",
  name: "ABCD INC",
  exchange: "NASDAQ",
  category: "Domestic Common Stock",
  sector: "Technology",
  industry: "Software",
  first: "2014-01-01",
  last: "2014-01-30",
  delisted: true,
  location: "Texas",
  siccode: "7372",
  symbols: [
    { symbol: "OLDX", from: "2010-01-01", to: "2012-12-31" },
    { symbol: "ABCD", from: "2013-01-01", to: "2014-01-30" },
  ],
  others: [],
  sealed_from: "2023-11-09",
  prices: {
    date: dates,
    open: closes,
    high: closes.map((c) => c * 1.01),
    low: closes.map((c) => c * 0.99),
    close: closes,
    factor: dates.map((_, i) => (i < 15 ? 0.5 : 1)),
    volume: dates.map(() => 1e5),
    market_cap: dates.map(() => 5e8),
    adv20: dates.map(() => 2e6),
    symbol: dates.map(() => "ABCD"),
  },
  events: [{ date: "2014-01-10", codes: "22|91", results: true }],
  trades: [
    {
      source: "lab",
      id: "run1",
      label: "mine",
      detail: "taken by the book",
      kind: "lab",
      symbol: "ABCD",
      signal_day: "2014-01-09",
      entry_day: "2014-01-10",
      entry: 100,
      exit_day: "2014-01-20",
      exit: 52,
      net: 0.04,
      note: "hold",
      side: "long",
    },
    {
      source: "run",
      id: "run2",
      label: "earnings_drift",
      detail: "research",
      kind: "swing",
      symbol: "ABCD",
      signal_day: null,
      entry_day: "2014-01-05",
      entry: 100,
      exit_day: null,
      exit: 104,
      net: -0.01,
      note: "time",
      side: "long",
    },
  ],
};

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => ({ ok: url.startsWith("/api/stock/ABCD"), status: 200, json: async () => stock }) as Response),
  );
  localStorage.clear();
});

describe("the stock page", () => {
  it("shows the company, its split-adjusted facts and every trade", async () => {
    render(<StockPage symbol="ABCD" onOpen={() => {}} />);
    await waitFor(() => expect(screen.getByRole("heading", { name: "ABCD" })).toBeTruthy());
    expect(screen.getByText("ABCD INC")).toBeTruthy();
    expect(screen.getByText("Also traded as OLDX (2010–2012)")).toBeTruthy();
    expect(screen.getByText("+0.0%")).toBeTruthy();
    expect(screen.getByRole("link", { name: "mine" }).getAttribute("href")).toBe("#/lab/mine/run1");
    expect(screen.getByRole("link", { name: "earnings_drift" }).getAttribute("href")).toBe("#/strategy/earnings_drift/runs");
    expect(screen.getByText("Results")).toBeTruthy();
    expect(JSON.parse(localStorage.getItem("kinn-recent-stocks") ?? "[]")[0].ticker).toBe("ABCD");
  });

  it("filters the trades by where they came from", async () => {
    render(<StockPage symbol="ABCD" onOpen={() => {}} />);
    await waitFor(() => expect(screen.getByText("All 2")).toBeTruthy());
    fireEvent.click(screen.getByText("Lab 1"));
    expect(screen.queryByRole("link", { name: "earnings_drift" })).toBeNull();
    expect(screen.getByRole("link", { name: "mine" })).toBeTruthy();
  });

  it("adds the stock to the watchlist and takes it off again", async () => {
    render(<StockPage symbol="ABCD" onOpen={() => {}} />);
    const add = await screen.findByRole("button", { name: "Add to the watchlist" });
    fireEvent.click(add);
    expect(JSON.parse(localStorage.getItem("kinn-watchlist") ?? "[]")).toEqual([{ ticker: "ABCD", name: "ABCD INC", permaticker: 1001 }]);
    fireEvent.click(screen.getByRole("button", { name: "On the watchlist" }));
    expect(JSON.parse(localStorage.getItem("kinn-watchlist") ?? "[]")).toEqual([]);
  });
});
