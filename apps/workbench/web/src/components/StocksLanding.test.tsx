import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ScreenData } from "../lib/api";
import { rowsOf } from "../lib/screen";
import { movers, sectorMonths, StocksLanding, tickersIn } from "./StocksLanding";

afterEach(cleanup);

const columns = ["symbol", "permaticker", "name", "sector", "category", "close", "market_cap", "ret_1d", "ret_1m", "ret_1y", "from_high", "pe"];
const row = (symbol: string, perm: number, sector: string, cap: number, day: number, month: number, category = "Domestic Common Stock") => [
  symbol,
  perm,
  `${symbol} Inc`,
  sector,
  category,
  20,
  cap,
  day,
  month,
  0.1,
  -0.05,
  15,
];
const data: ScreenData = {
  schema: "screen-1",
  on: "2023-11-08",
  first: "2000-01-01",
  last: "2023-11-08",
  columns,
  rows: [
    row("UPPP", 1, "Technology", 5e9, 0.08, 0.05),
    row("DOWN", 2, "Energy", 3e9, -0.06, -0.04),
    row("SMAL", 3, "Energy", 5e8, 0.2, -0.02),
    row("ADRR", 4, "Technology", 9e9, 0.3, 0.1, "ADR Common Stock"),
    row("FLAT", 5, "Technology", 4e9, 0, 0.01),
  ],
};

beforeEach(() => {
  localStorage.clear();
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({ ok: true, status: 200, json: async () => data }) as unknown as Response),
  );
});

describe("the stocks landing", () => {
  it("ranks rises and falls among large US stocks only", () => {
    const rows = rowsOf(data);
    expect(movers(rows, "up").map((r) => r.symbol)).toEqual(["UPPP"]);
    expect(movers(rows, "down").map((r) => r.symbol)).toEqual(["DOWN"]);
  });

  it("takes each sector's median month", () => {
    const sectors = sectorMonths(rowsOf(data));
    expect(sectors.map((s) => [s.label, s.note])).toEqual([
      ["Technology", "median of 2 stocks"],
      ["Energy", "median of 2 stocks"],
    ]);
    expect(sectors[0].value).toBeCloseTo(0.03);
    expect(sectors[1].value).toBeCloseTo(-0.03);
  });

  it("shows the watchlist with the last session's numbers", async () => {
    localStorage.setItem("kinn-watchlist", JSON.stringify([{ ticker: "DOWN", name: "DOWN Inc", permaticker: 2 }]));
    render(<StocksLanding />);
    await waitFor(() => expect(screen.getByText("Watchlist on 8 Nov 2023")).toBeTruthy());
    const table = within(screen.getAllByRole("table")[0]);
    expect(table.getByText("−6.0%")).toBeTruthy();
    expect(table.getByText("$3.0B")).toBeTruthy();
  });

  it("reads tickers from what is pasted", () => {
    expect(tickersIn("aapl, msft;NVDA  brk.b 123 aapl")).toEqual(["AAPL", "MSFT", "NVDA", "BRK.B"]);
  });

  it("adds pasted tickers it can find to the watchlist", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        if (url.startsWith("/api/stocks?q=")) {
          const q = decodeURIComponent(url.split("q=")[1]);
          return new Response(JSON.stringify(q === "UPPP" ? [{ permaticker: 1, ticker: "UPPP", name: "UPPP Inc" }] : []));
        }
        return new Response(JSON.stringify(data));
      }),
    );
    render(<StocksLanding />);
    fireEvent.change(await screen.findByLabelText("Tickers to add"), { target: { value: "uppp, NOPE" } });
    fireEvent.click(screen.getByRole("button", { name: "Add" }));
    await waitFor(() => expect(screen.getByRole("status").textContent).toBe("1 added; not found: NOPE"));
    expect(JSON.parse(localStorage.getItem("kinn-watchlist") ?? "[]")).toEqual([{ ticker: "UPPP", name: "UPPP Inc", permaticker: 1 }]);
  });
});
