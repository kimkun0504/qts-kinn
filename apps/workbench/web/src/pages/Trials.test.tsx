import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Family } from "../lib/api";
import { Trials } from "./Trials";

afterEach(cleanup);

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response(JSON.stringify([{ name: "mine", description: "a test", updated: "", runs: 3, trials: 5, last_run: null }]))),
  );
});

const family = (name: string, trials: number, deflated: number | null): Family =>
  ({
    family: name,
    runs: 4,
    counted: 3,
    scratch: 1,
    abandoned: 0,
    prior_trials: trials - 3,
    trials,
    by_agent: { claude: 3 },
    overfitting:
      deflated == null
        ? null
        : {
            best_sharpe_annual: 1.2,
            expected_max_sharpe_annual: 0.9,
            deflated_sharpe: deflated,
            probabilistic_sharpe: 0.99,
            pbo: { pbo: 0.2, trials_compared: 3, splits: 70 },
            sharpes: {},
            best_run: "r1",
          },
  }) as unknown as Family;

describe("trials", () => {
  it("lists the families by trials and opens one at a time", async () => {
    render(<Trials families={[family("small", 10, null), family("big", 600, 0.97)]} runs={[]} />);
    const rows = within(screen.getAllByRole("table")[0]).getAllByRole("row");
    expect(rows[1].textContent).toContain("big");
    expect(screen.getByText("610")).toBeTruthy();
    expect(screen.getByText("The best run clears the usual 0.95 bar after charging for the trials.", { exact: false })).toBeTruthy();
    fireEvent.click(within(screen.getAllByRole("table")[0]).getByText("small"));
    expect(screen.getByText(/No finished backtest in this family yet/)).toBeTruthy();
    expect(await screen.findByText("Lab algorithms, 5 trials")).toBeTruthy();
  });
});
