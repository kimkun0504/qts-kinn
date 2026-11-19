import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ScreenData } from "../lib/api";
import { ScreenerPage } from "./ScreenerPage";

afterEach(cleanup);

const columns = [
  "symbol",
  "permaticker",
  "name",
  "sector",
  "industry",
  "category",
  "exchange",
  "close",
  "market_cap",
  "adv20",
  "ret_1d",
  "ret_1m",
  "ret_3m",
  "ret_6m",
  "ret_1y",
  "from_high",
  "vol_60",
  "pe",
  "ps",
  "pb",
  "fcf_yield",
  "revenue",
  "revenue_growth",
  "net_income",
  "filed",
];
const stock = (symbol: string, sector: string, cap: number, ret: number, pe: number | null, category = "Domestic Common Stock") => {
  const row: Record<string, string | number | null> = {
    symbol,
    permaticker: cap,
    name: `${symbol} Corp`,
    sector,
    industry: "Things",
    category,
    exchange: "NYSE",
    close: 10,
    market_cap: cap,
    adv20: 1e7,
    ret_1d: 0.01,
    ret_1m: 0,
    ret_3m: 0,
    ret_6m: 0,
    ret_1y: ret,
    from_high: -0.1,
    vol_60: 0.3,
    pe,
    ps: 2,
    pb: 3,
    fcf_yield: 0.04,
    revenue: 1e9,
    revenue_growth: 0.1,
    net_income: 1e8,
    filed: "2023-10-30",
  };
  return columns.map((c) => row[c]);
};
const data: ScreenData = {
  schema: "screen-1",
  on: "2023-11-08",
  first: "2000-01-01",
  last: "2023-11-08",
  columns,
  rows: [stock("BIG", "Technology", 5e10, 0.4, 30), stock("MID", "Energy", 3e9, -0.2, 8), stock("TINY", "Energy", 2e8, -0.5, null), stock("FORN", "Technology", 4e9, 0.1, 12, "ADR Common Stock")],
};

beforeEach(() => {
  localStorage.clear();
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({ ok: true, status: 200, json: async () => data }) as unknown as Response),
  );
});

describe("the screener", () => {
  it("lists US common stock by market value and narrows with a filter", async () => {
    render(<ScreenerPage onDate={() => undefined} />);
    await waitFor(() => expect(screen.getByText("3 stocks on 8 Nov 2023")).toBeTruthy());
    const symbols = () => screen.getAllByRole("link").map((a) => a.textContent);
    expect(symbols()).toEqual(["BIG", "MID", "TINY"]);
    fireEvent.click(screen.getByRole("button", { name: "Add a filter" }));
    fireEvent.change(screen.getByLabelText("Market value, at least"), { target: { value: "1B" } });
    expect(symbols()).toEqual(["BIG", "MID"]);
    fireEvent.change(screen.getByLabelText("Market value, at most"), { target: { value: "10B" } });
    expect(symbols()).toEqual(["MID"]);
    expect(window.location.hash).toContain("screener/latest/");
  });

  it("starts from a ready screen and saves it under a name", async () => {
    render(<ScreenerPage onDate={() => undefined} />);
    await waitFor(() => expect(screen.getByText("3 stocks on 8 Nov 2023")).toBeTruthy());
    fireEvent.change(screen.getByLabelText("Start from a screen"), { target: { value: "start:4" } });
    expect(screen.getByText("1 stock on 8 Nov 2023")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Save screen" }));
    fireEvent.change(screen.getByLabelText("Name of the screen"), { target: { value: "Value" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(JSON.parse(localStorage.getItem("kinn-screens") ?? "[]")[0].name).toBe("Value");
    expect(screen.getByRole("button", { name: "Delete “Value”" })).toBeTruthy();
  });

  it("picks a sector from the breakdown", async () => {
    render(<ScreenerPage onDate={() => undefined} />);
    await waitFor(() => expect(screen.getByText("3 stocks on 8 Nov 2023")).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: /^Energy/ }));
    expect(screen.getByText("2 stocks on 8 Nov 2023")).toBeTruthy();
    expect(screen.getByText("Industries in Energy")).toBeTruthy();
  });
});
