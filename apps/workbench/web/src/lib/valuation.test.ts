import { describe, expect, it } from "vitest";
import type { FinancialPeriod } from "./api";
import { quantile, valuation } from "./valuation";

const book = (period: string, filed: string, income: number | null, revenue = 100, equity = 50, fcf: number | null = 5): FinancialPeriod => ({
  period,
  filed,
  revenueusd: revenue,
  gp: null,
  opinc: null,
  netinccmnusd: income,
  epsusd: null,
  ncfo: null,
  capex: null,
  fcf,
  cashnequsd: null,
  debtusd: null,
  equityusd: equity,
  sharesbas: null,
});

describe("valuation", () => {
  const prices = { date: ["2020-01-02", "2020-02-14", "2020-02-18", "2020-05-01", "2022-01-03"], market_value: [1000, 1000, 1200, 900, 800] };
  const trailing = [book("2019-12-31", "2020-02-14", 10), book("2020-03-31", "2020-04-30", -5)];

  it("divides each session's value by the trailing year filed before it", () => {
    const v = valuation(prices, trailing, "pe");
    expect(v.date).toEqual(["2020-02-18", "2020-05-01", "2022-01-03"]);
    expect(v.value).toEqual([120, null, null]);
    expect(valuation(prices, trailing, "ps").value).toEqual([12, 9, null]);
    expect(valuation(prices, trailing, "fcf_yield").value[0]).toBeCloseTo(5 / 1200);
  });

  it("places today among the sessions shown and stops at a pinned day", () => {
    const v = valuation(prices, trailing, "ps", "2020-05-01");
    expect(v.date.at(-1)).toBe("2020-05-01");
    expect(v.now).toBe(9);
    expect(v.rank).toBe(0);
    expect(v.median).toBe(10.5);
    expect(v.since).toBe("2020-02-18");
  });

  it("interpolates quantiles", () => {
    expect(quantile([1, 2, 3, 4], 0.5)).toBe(2.5);
    expect(quantile([], 0.5)).toBeNull();
  });
});
