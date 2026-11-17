import { describe, expect, it } from "vitest";
import type { Period } from "./api";
import { href, parse } from "./route";
import { byYear, timeline } from "./series";

function period(key: string, months: [string, number][]): Period {
  return { key, label: key, note: null, config: key, run_id: `run-${key}`, stats: null, months, targets: null };
}

describe("a strategy's timeline", () => {
  it("joins periods oldest first and keeps uncovered months as gaps", () => {
    const line = timeline([
      period("holdout", [["2024-01", 300], ["2024-02", -500]]),
      period("search", [["2023-10", 100], ["2023-11", -40]]),
    ]);
    expect(line.months.map((m) => m.key)).toEqual(["2023-10", "2023-11", "2023-12", "2024-01", "2024-02"]);
    expect(line.months.map((m) => m.total)).toEqual([100, 60, 60, 360, -140]);
    expect(line.months[2].value).toBeNull();
    expect(line.gaps).toEqual([[2, 2]]);
    expect(line.starts).toEqual([{ key: "search", label: "search", index: 0 }, { key: "holdout", label: "holdout", index: 3 }]);
    expect(line.deepest).toBe(-500);
  });

  it("totals each year over the months a run covers", () => {
    const years = byYear(timeline([period("search", [["2023-11", 100], ["2023-12", 50], ["2024-01", -30]])]).months);
    expect(years).toEqual([
      { year: 2023, total: 150, months: 2, periods: ["search"] },
      { year: 2024, total: -30, months: 1, periods: ["search"] },
    ]);
  });

  it("is empty when no period has a run", () => {
    expect(timeline([period("holdout", [])]).months).toEqual([]);
  });
});

describe("addresses", () => {
  it("round-trips a strategy tab and falls back to home", () => {
    expect(parse(href({ page: "strategy", name: "earnings_drift", tab: "trades" }))).toEqual({ page: "strategy", name: "earnings_drift", tab: "trades" });
    expect(parse("#/strategy/earnings_drift")).toEqual({ page: "strategy", name: "earnings_drift", tab: "results" });
    expect(parse("#/strategy")).toEqual({ page: "strategies" });
    expect(parse("")).toEqual({ page: "home" });
    expect(parse("#/nowhere")).toEqual({ page: "home" });
  });
});
