import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { RunRow } from "../lib/api";
import { Compare } from "./Compare";

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
    expect(screen.getByText("Backtests to compare, 0 of 4 picked")).toBeTruthy();
    expect(screen.queryByText("study")).toBeNull();
    fireEvent.change(screen.getByLabelText("Find backtests"), { target: { value: "prints" } });
    expect(screen.queryByText("drift")).toBeNull();
    fireEvent.click(screen.getByLabelText("Compare prints_base"));
    expect(onToggle).toHaveBeenCalledWith(expect.objectContaining({ run_id: "r2" }));
  });
});
