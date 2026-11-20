import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { MarketsData } from "../lib/api";
import { MarketsPage, startOf } from "./MarketsPage";

afterEach(cleanup);

const dates = Array.from({ length: 300 }, (_, i) => new Date(Date.UTC(2022, 8, 1 + i)).toISOString().slice(0, 10));
const markets: MarketsData = {
  schema: "markets-1",
  on: dates[299],
  first: "2000-01-01",
  last: dates[299],
  groups: [
    {
      title: "US stocks",
      rows: [
        { symbol: "SPY", name: "S&P 500", close: 437.25, day: 0.0007, week: 0.01, month: 0.006, quarter: 0.02, year_to_date: 0.143, year: 0.15, three_years: 0.25 },
        { symbol: "QQQ", name: "Nasdaq 100", close: 372.94, day: 0.0006, month: 0.012 },
        { symbol: "IWM", name: "Russell 2000", close: 169.87, day: -0.0107 },
        { symbol: "DIA", name: "Dow Jones industrials", close: 341.12, day: -0.0012 },
      ],
    },
  ],
  breadth: dates.slice(-80).map((date) => ({ date, advancing: 60, declining: 40, traded: 100 })),
};

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      if (url === "/api/markets") return new Response(JSON.stringify(markets));
      const symbol = decodeURIComponent(url.split("symbols=")[1]);
      return new Response(JSON.stringify({ series: [{ symbol, name: symbol, date: dates, close: dates.map((_, i) => 100 + i) }], missing: [], sealed_from: "2023-11-09" }));
    }),
  );
});

describe("markets", () => {
  it("starts the year-to-date range at the last close of the year before", () => {
    expect(dates[startOf(dates, "ytd")]).toBe("2022-12-31");
    expect(startOf(dates, "month")).toBe(299 - 21);
    expect(startOf(dates.slice(0, 10), "year")).toBe(0);
  });

  it("shows the funds, the day's breadth and charts what is clicked", async () => {
    render(<MarketsPage />);
    expect(await screen.findByText("Russell 2000")).toBeTruthy();
    expect(screen.getByText("US stocks that rose")).toBeTruthy();
    await waitFor(() => expect(screen.getByRole("img", { name: "SPY, QQQ, IWM over the range" })).toBeTruthy());
    fireEvent.click(within(screen.getAllByRole("table")[0]).getByText("Dow Jones industrials"));
    await waitFor(() => expect(screen.getByRole("img", { name: "SPY, QQQ, IWM, DIA over the range" })).toBeTruthy());
  });
});
