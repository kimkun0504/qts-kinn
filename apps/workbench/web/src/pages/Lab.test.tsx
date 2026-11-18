import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { LabSettings, RunDetail, StockRow } from "../lib/lab";
import { Lab } from "./Lab";

afterEach(cleanup);

const DEFAULTS: LabSettings = {
  period: "search",
  start: null,
  end: null,
  universe: { min_market_cap: 50e6, max_market_cap: null, min_price: 2, min_dollar_volume: 250_000, exclude_blank_checks: false },
  entry: { mode: "signal", top_n: 10, rank_order: "highest" },
  exit: { hold_days: 20, stop_loss: null, take_profit: null },
  book: { position_size: 2000, max_positions: 20 },
};
const RUN = "20261118T190102Z_two_up_1a2b3c4d";
const CODE = 'def signal(data):\n    return data.returns > 0\n';
const stock = (ticker: string, profit: number): StockRow => ({
  ticker, name: `${ticker} Inc`, sector: "Energy", trades: 2, wins: profit > 0 ? 2 : 0, win_rate: profit > 0 ? 1 : 0, mean_net: profit / 4000,
  total_net: profit / 2000, profit, book_trades: 2, book_profit: profit, mean_over: 0, best: 0.1, worst: -0.1, last_entry: "2015-06-01",
});
const detail: RunDetail = {
  run_id: RUN,
  status: { state: "complete", stage: "Done", progress: 1 },
  manifest: { algorithm: "two_up", description: "", created_at: "2026-11-18T19:01:02+00:00", code_sha256: "a".repeat(64), data_build_id: "b1" },
  summary: {
    trades: 4, headline: "4 trades, +1.00% a trade after costs", lookahead: { passed: false, checked: ["2015-03-02"], detail: "signal(data) changed when the data was cut off" },
    mean_net: 0.01, mean_net_2x: -0.002, fragile: true, win_rate: 0.5, stocks: 2, taken: 4, skipped: 0, book_profit: 80, capital: 40000, exits: { hold: 4 },
    histogram: { edges: [-0.5, 0, 0.5], counts: [1, 3] }, settings: DEFAULTS, trial_number: 1,
  },
};
const routes: Record<string, unknown> = {
  "/api/lab/meta": { fields: [{ name: "close", description: "The close", known: "that day" }], periods: [{ name: "search", start: "2010-01-01", end: "2017-12-31", label: "2010–2017 (search years)" }], defaults: DEFAULTS, last_entry: "2023-10-13", max_hold: 250, max_code: 200000, active_run: null, folder: "/x/lab" },
  "/api/lab/templates": [],
  "/api/lab/algorithms": [{ name: "two_up", description: "Two up days", updated: "2026-11-18T19:00:00Z", runs: 1, trials: 1, last_run: null }],
  "/api/lab/algorithms/two_up": { name: "two_up", code: CODE, description: "", settings_in_code: null },
  "/api/lab/runs?algorithm=two_up": [{ run_id: RUN, algorithm: "two_up", description: "", created_at: "2026-11-18T19:01:02+00:00", state: "complete", stage: "Done", error: null, trial: true, period: "2010–2017", headline: "4 trades" }],
  [`/api/lab/runs/${RUN}`]: detail,
  [`/api/lab/runs/${RUN}/stocks`]: [stock("WIN", 120), stock("LOSE", -40)],
  [`/api/lab/runs/${RUN}/equity`]: { dates: ["2015-01-02", "2015-01-05"], profit: [0, 80], drawdown: [0, 0], spy: [0, 10], positions: [1, 1], capital: 40000 },
};

let calls: { url: string; init?: RequestInit }[] = [];
beforeEach(() => {
  calls = [];
  vi.stubGlobal("fetch", vi.fn(async (url: string, init?: RequestInit) => {
    calls.push({ url, init });
    if (url.includes("/trades?")) return new Response(JSON.stringify({ total: 1, offset: 0, limit: 100, rows: [] }));
    if (url === "/api/lab/session") return new Response(JSON.stringify({ token: "tok" }));
    if (init?.method === "POST") return new Response(JSON.stringify({ run_id: RUN, status: { state: "queued" } }), { status: 202 });
    const found = routes[url];
    return found === undefined ? new Response(JSON.stringify({ error: "no" }), { status: 404 }) : new Response(JSON.stringify(found));
  }));
});

describe("the Lab", () => {
  it("shows the algorithm, its warnings and its best and worst stocks", async () => {
    render(<Lab name="two_up" onOpen={() => undefined} />);
    expect(await screen.findByText("two_up.py")).toBeTruthy();
    expect(await screen.findByText("The code looks ahead")).toBeTruthy();
    expect(screen.getByText("Fragile")).toBeTruthy();
    expect(await screen.findByText("Best stocks")).toBeTruthy();
    expect(screen.getAllByText("WIN").length).toBeGreaterThan(0);
    expect(screen.getAllByText("LOSE").length).toBeGreaterThan(0);
  });

  it("opens a stock's trades from the stocks table", async () => {
    render(<Lab name="two_up" onOpen={() => undefined} />);
    fireEvent.click(await screen.findByRole("tab", { name: /Stocks/ }));
    const panel = (await screen.findByText("Every stock it traded")).closest("section") as HTMLElement;
    fireEvent.click(within(panel).getByText("LOSE"));
    expect(await screen.findByText("Trades in LOSE")).toBeTruthy();
    await waitFor(() => expect(calls.some((c) => c.url.includes("/trades?ticker=LOSE"))).toBe(true));
  });

  it("runs with the token and only the settings that changed", async () => {
    const onOpen = vi.fn();
    render(<Lab name="two_up" onOpen={onOpen} />);
    fireEvent.change(await screen.findByLabelText(/Hold/), { target: { value: "5" } });
    fireEvent.click(screen.getByRole("button", { name: "Run" }));
    await waitFor(() => expect(onOpen).toHaveBeenCalledWith("two_up", RUN));
    const post = calls.find((c) => c.init?.method === "POST");
    expect((post?.init?.headers as Record<string, string>)["X-Kinn-Token"]).toBe("tok");
    expect(JSON.parse(String(post?.init?.body))).toEqual({ algorithm: "two_up", code: CODE, settings: { exit: { hold_days: 5 } } });
  });

  it("refuses a bad setting before running", async () => {
    render(<Lab name="two_up" onOpen={() => undefined} />);
    fireEvent.change(await screen.findByLabelText(/Hold/), { target: { value: "0" } });
    fireEvent.click(screen.getByRole("button", { name: "Run" }));
    expect(await screen.findByText("Hold: from 1 to 250.")).toBeTruthy();
    expect(calls.some((c) => c.init?.method === "POST")).toBe(false);
  });
});
