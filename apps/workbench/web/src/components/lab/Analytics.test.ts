import { describe, expect, it } from "vitest";
import type { Equity } from "../../lib/lab";
import { monthReturns } from "./Analytics";

describe("monthReturns", () => {
  it("turns the book's running profit into each month's share of the capital", () => {
    const equity: Equity = {
      dates: ["2015-01-05", "2015-01-30", "2015-02-27", "2015-03-02", "2016-01-04"],
      profit: [0, 400, 200, null, 1200],
      drawdown: [0, 0, -200, -200, 0],
      spy: [0, 0, 0, 0, 0],
      positions: [1, 1, 1, 1, 1],
      capital: 20000,
    };
    const rows = monthReturns(equity);
    expect(rows.map((r) => r.year)).toEqual([2015, 2016]);
    expect(rows[0].months[0]?.value).toBeCloseTo(0.02);
    expect(rows[0].months[1]?.value).toBeCloseTo(-0.01);
    expect(rows[0].months[2]).toBeNull();
    expect(rows[0].total).toBeCloseTo(0.01);
    expect(rows[1].months[0]?.value).toBeCloseTo(0.05);
    expect(rows[0].months[0]?.partial).toBe(true);
  });
});
