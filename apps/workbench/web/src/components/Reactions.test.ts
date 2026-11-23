import { describe, expect, it } from "vitest";
import { reactions } from "./Reactions";

const dates = Array.from({ length: 40 }, (_, i) => new Date(Date.UTC(2023, 0, 2 + i)).toISOString().slice(0, 10));
const close = dates.map((_, i) => (i < 10 ? 100 : i < 11 ? 110 : 121));

describe("results reactions", () => {
  it("measures from the close before the filing day to the close after it", () => {
    const [r] = reactions(dates, close, [dates[10]]);
    expect(r.before).toBe(9);
    expect(r.after).toBe(11);
    expect(r.move).toBeCloseTo(0.21);
    expect(r.next5).toBe(0);
    expect(r.market).toBeNull();
  });

  it("uses the next session when the filing day did not trade, and skips the ends", () => {
    const gaps = dates.filter((_, i) => i !== 10);
    const prices = close.filter((_, i) => i !== 10);
    const [r] = reactions(gaps, prices, [dates[10], dates[0], "2023-03-28"]);
    expect([r.before, r.after]).toEqual([9, 10]);
    expect(reactions(gaps, prices, [dates[0], "2099-01-01"])).toEqual([]);
  });

  it("sets the market's move beside the stock's", () => {
    const market = dates.map((_, i) => (i < 10 ? 400 : 404));
    const [r] = reactions(dates, close, [dates[10]], market);
    expect(r.market).toBeCloseTo(0.01);
    expect(r.market20).toBe(0);
  });
});
