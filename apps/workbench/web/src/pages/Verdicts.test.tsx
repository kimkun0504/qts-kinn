import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { RunsTable } from "../components/RunsTable";
import { BoardTable } from "../components/BoardTable";
import type { Board, BoardRow, FillCheck, RunRow, Targets } from "../lib/api";
import { FillCheckView } from "./FillCheckView";

afterEach(cleanup);
vi.mock("../lib/useRun", () => ({ useRun: () => ({ detail: null, error: null }) }));

const met: Targets = {
  items: [
    { key: "net_per_trade", label: "Net per trade at 2× slippage", value: 0.0156, bar: 0.01, met: true },
    { key: "sharpe", label: "Sharpe at 2× slippage", value: 1.37, bar: 1, met: true },
    { key: "drawdown", label: "Worst drawdown at 2×, share of the account", value: 0.22, bar: 0.5, met: true },
  ],
  fills: "confirmed",
  fills_run: "check-1",
  met: 4,
  of: 4,
  all_met: true,
};

function run(over: Partial<RunRow>): RunRow {
  return {
    run_id: "r1", strategy: "rebound_limit", family: "intraday_rebound", config: "validation_s_l468", kind: "backtest", agent: "claude", branch: "b",
    commit: "6361f27c", dirty: false, scratch: false, status: "complete", started_at: "2026-11-16T01:40:43+00:00", period: { start: "2017-01-03", end: "2023-11-08" },
    data_build_id: "6453bd3ec8", params: {}, schema_ok: true, trades: 3001, net_1x: 0.0166, net_2x: 0.0156, gross: 0.02, sharpe: 1.46, total_net: 31160,
    t_stat_2x: 3.59, phase: "validation", targets: met, sharpe_2x: 1.37, drawdown_2x: -4485, total_net_2x: 29201, fill_check_passed: null, ...over,
  };
}

const candidate = run({});
const failed = run({ run_id: "r2", config: "validation_t_l468", targets: { ...met, met: 2, all_met: false, fills: "not checked", fills_run: null } });
const search = run({ run_id: "r3", config: "s_l468", phase: "development", targets: null });
const check = run({ run_id: "r4", config: "fill_check:fillcheck_s_l468", kind: "fill_check", phase: "full", targets: null, fill_check_passed: true });

function idea(over: Partial<BoardRow>): BoardRow {
  return {
    strategy: "earnings_drift", idea: "Earnings drift", title: "Earnings drift", owner: "claude", horizon: "40 sessions", family: "swing", trials: 150,
    result: "+$11,430 a year in the holdout", summary: null, verdict: "passed_holdout", label: "Passed holdout", group: "works", variant: false, paper: true, ...over,
  };
}

const board: Board = {
  rows: [
    idea({}),
    idea({ strategy: "earnings_drift", idea: "Skip fallen, cash-rich companies", verdict: "testing", label: "In paper test", group: "testing", variant: true, trials: null, paper: false }),
    idea({ strategy: "rebound_limit", idea: "Intraday rebound", verdict: "failed_holdout", label: "Failed holdout", group: "closed", paper: false, trials: 2011, result: "Lost money in the holdout" }),
  ],
  others: [{ strategy: "opening_gap_reclaim", agent: "gpt", runs: 12, status: "parked" }],
  waiting: [],
  counts: { works: 1, testing: 1, closed: 1 },
};

describe("verdicts in the Workbench", () => {
  it("labels every run with its period and judges only validation backtests", () => {
    render(<RunsTable runs={[candidate, failed, search, check]} onOpen={() => {}} />);
    expect(screen.getAllByText("Validation")).toHaveLength(2);
    expect(screen.getByText("Development")).toBeTruthy();
    expect(screen.getByText("4 of 4 targets")).toBeTruthy();
    expect(screen.getByText("2 of 4 targets")).toBeTruthy();
    expect(screen.getByText("Fill check")).toBeTruthy();
    expect(screen.getByText("Passed")).toBeTruthy();
  });

  it("lists every idea with its verdict and filters by where it stands", () => {
    const opened: string[] = [];
    render(<BoardTable board={board} onOpen={(name) => opened.push(name)} />);
    expect(screen.getByText("Passed holdout")).toBeTruthy();
    expect(screen.getByText("Failed holdout")).toBeTruthy();
    expect(screen.getByText("Skip fallen, cash-rich companies")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Parked or closed 1" }));
    expect(screen.queryByText("Passed holdout")).toBeNull();
    expect(screen.getByText("Intraday rebound")).toBeTruthy();
    fireEvent.click(screen.getByText("Intraday rebound"));
    expect(opened).toEqual(["rebound_limit"]);
  });

  it("shows the first rows on Home and the rest on request", () => {
    render(<BoardTable board={board} onOpen={() => {}} limit={2} />);
    expect(screen.queryByText("Intraday rebound")).toBeNull();
    expect(screen.queryByText("12 intraday ideas")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Show all 3" }));
    expect(screen.getByText("Intraday rebound")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Show the first 2" })).toBeTruthy();
  });

  it("draws a fill check with its bars and its groups", () => {
    const group = {
      orders: 3001, covered: 2998, coverage: 0.999, confirmed: 1, confirmed_after_5s: 0.995, in_full_size: 0.984, through_volume_multiple_median: 142, bid_fell_below_limit: 1,
      simulated: { trades: 2998, net_per_trade_1x: 0.0165, net_per_trade_2x: 0.0155, total_net_1x: 31000, total_net_2x: 29140 },
      tick_rule_0s: { trades: 2998, net_per_trade_1x: 0.0165, net_per_trade_2x: 0.0155, total_net_1x: 30800, total_net_2x: 28900, share_of_simulated_net_2x: 0.99 },
      tick_rule_5s: { trades: 2984, net_per_trade_1x: 0.0163, net_per_trade_2x: 0.0153, total_net_1x: 30100, total_net_2x: 28240, share_of_simulated_net_2x: 0.97 },
      tick_rule_30s: { trades: 2900, net_per_trade_1x: 0.0146, net_per_trade_2x: 0.0136, total_net_1x: 26700, total_net_2x: 24825, share_of_simulated_net_2x: 0.85 },
    };
    const empty = { orders: 0, covered: 0, coverage: null };
    const fill: FillCheck = {
      plan: "fillcheck_s_l468", main_delay_seconds: 5, conditions_source: "vendor table", all_traded: group,
      periods: { validation: { run: "r1", all: group, by_cap: { "under $300M": group }, by_rung: { o4: group }, before_2007: empty, from_2007: group,
        unfilled: { touched: { all: { orders: 204, covered: 204, rule_missed_a_fill: 0.02, printed_at_the_limit_only: 0.98, at_the_limit_in_full_size: 0.85 }, by_cap: {} } } } },
      verdict: { passed: true, bars: { coverage_at_least_95pct: true, validation_net_2x_at_least_1pct: true }, coverage: 0.999, validation_net_per_trade_2x: 0.0153, share_of_simulated_net_2x: { validation: 0.97 } },
    };
    render(<FillCheckView check={fill} />);
    expect(screen.getByText("Passed")).toBeTruthy();
    expect(screen.getByText("Tick data for at least 95% of the filled orders")).toBeTruthy();
    expect(screen.getByText("Rung 4% below")).toBeTruthy();
    expect(screen.getByText("Market cap under $300M")).toBeTruthy();
    expect(screen.queryByText("2003 to 2006")).toBeNull();
    expect(screen.getByText("Price touched the limit")).toBeTruthy();
  });
});
