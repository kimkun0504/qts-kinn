import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { RunRow } from "../lib/api";
import type { RunDetail } from "../lib/lab";
import { Compare, isLab, labRow } from "./Compare";

afterEach(cleanup);

const run = (run_id: string, strategy: string, kind: RunRow["kind"] = "backtest"): RunRow =>
  ({
    run_id,
    strategy,
    family: strategy,
    config: `${strategy}_base`,
    kind,
    agent: "claude",
    branch: "b",
    commit: "c",
    dirty: false,
    scratch: false,
    status: "complete",
    started_at: "2026-11-18T10:00:00Z",
    period: { start: "2010-01-01", end: "2016-12-31" },
    data_build_id: "b1",
    params: {},
    schema_ok: true,
    trades: 10,
    net_1x: 0.01,
    net_2x: 0.005,
    gross: 0.012,
    sharpe: 1,
    total_net: 100,
    t_stat_2x: 2,
    phase: "development",
    targets: null,
    sharpe_2x: 0.8,
    drawdown_2x: -50,
    total_net_2x: 80,
    fill_check_passed: null,
  }) as RunRow;

describe("compare", () => {
  it("offers the finished backtests to pick from when nothing is picked", () => {
    const onToggle = vi.fn();
    render(<Compare ids={[]} runs={[run("r1", "drift"), run("r2", "prints"), run("r3", "study", "event_study")]} onToggle={onToggle} />);
    expect(screen.getByText("Runs to compare, 0 of 4 picked")).toBeTruthy();
    expect(screen.queryByText("study")).toBeNull();
    fireEvent.change(screen.getByLabelText("Find backtests"), { target: { value: "prints" } });
    expect(screen.queryByText("drift")).toBeNull();
    fireEvent.click(screen.getByLabelText("Compare prints_base"));
    expect(onToggle).toHaveBeenCalledWith("r2");
  });
});

describe("comparing Lab runs", () => {
  it("reads a Lab run's summary into the side-by-side row", () => {
    const run = {
      run_id: "r",
      status: { state: "complete" },
      manifest: { algorithm: "two_up", description: "", created_at: "2026-11-19T22:47:56+00:00", code_sha256: "x" },
      summary: {
        trades: 455,
        headline: "",
        lookahead: { passed: true },
        mean_gross: 0.05,
        mean_net: 0.04,
        mean_net_2x: 0.035,
        t_weekly_2x: 3.1,
        book_profit: 35733,
        max_drawdown: -4000,
        period_label: "2010–2017 (search years)",
      },
    } as unknown as RunDetail;
    const row = labRow("lab:r", run);
    expect(row).toMatchObject({ id: "lab:r", source: "Lab", name: "two_up", period: "2010–2017 (search years)", trades: 455, n1: 0.04, n2: 0.035, t: 3.1, total: 35733, dd: -4000 });
    expect(isLab("lab:r")).toBe(true);
    expect(isLab("20261118T011522Z_gpt_x")).toBe(false);
  });
});
