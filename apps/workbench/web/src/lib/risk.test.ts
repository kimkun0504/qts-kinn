import { describe, expect, it } from "vitest";
import { beta, drawdowns, returns, seasons, volatility } from "./risk";

describe("risk", () => {
  it("measures beta and correlation on the days both moved", () => {
    const market = Array.from({ length: 100 }, (_, i) => (i === 0 ? null : 0.01 * Math.sin(i)));
    const stock = market.map((m) => (m == null ? null : 2 * m + 0.0001));
    const found = beta(stock, market, 252);
    expect(found?.beta).toBeCloseTo(2);
    expect(found?.correlation).toBeCloseTo(1);
    expect(beta(stock.slice(0, 20), market.slice(0, 20), 252)).toBeNull();
  });

  it("annualises the daily spread", () => {
    const values = Array.from({ length: 60 }, (_, i) => (i % 2 ? 0.01 : -0.01));
    expect(volatility(values, 252)).toBeCloseTo(0.01 * Math.sqrt(252) * Math.sqrt(60 / 59), 4);
    expect(returns([10, 11, null, 12])).toEqual([null, 0.10000000000000009, null, null]);
  });

  it("finds the deepest falls from a high, with the day each recovered", () => {
    const dates = ["d0", "d1", "d2", "d3", "d4", "d5", "d6", "d7"];
    const close = [100, 80, 90, 110, 99, 120, 60, 70];
    expect(drawdowns(dates, close)).toEqual([
      { peak: "d5", trough: "d6", recovered: null, depth: -0.5 },
      { peak: "d0", trough: "d1", recovered: "d3", depth: -0.19999999999999996 },
      { peak: "d3", trough: "d4", recovered: "d5", depth: -0.09999999999999998 },
    ]);
  });

  it("averages each calendar month from month-end closes", () => {
    const dates = ["2020-01-31", "2020-02-14", "2020-02-28", "2020-03-31", "2021-01-29", "2021-02-26"];
    const close = [100, 105, 110, 99, 120, 132];
    const found = seasons(dates, close);
    expect(found[1]).toEqual({ month: 2, mean: expect.closeTo(0.1), median: expect.closeTo(0.1), up: 2, years: 2 });
    expect(found[2].up).toBe(0);
    expect(found[0].years).toBe(1);
  });
});
