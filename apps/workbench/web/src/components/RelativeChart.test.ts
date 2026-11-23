import { describe, expect, it } from "vitest";
import { aligned, rebase } from "./RelativeChart";

describe("relative performance", () => {
  it("carries the other price forward onto the stock's sessions", () => {
    const other = { symbol: "SPY", name: "SPY", date: ["2023-01-02", "2023-01-04", "2023-01-05"], close: [10, 11, null] };
    expect(aligned(["2023-01-01", "2023-01-03", "2023-01-04", "2023-01-06"], other)).toEqual([null, 10, 11, 11]);
  });

  it("starts every line at zero on the first day all of them have a price", () => {
    const based = rebase([
      [null, 10, 12, 15],
      [5, 5, 4, null],
    ]);
    expect(based?.start).toBe(1);
    expect(based?.values[0]).toEqual([0, 0.19999999999999996, 0.5]);
    expect(based?.values[1]).toEqual([0, -0.19999999999999996, -0.19999999999999996]);
    expect(rebase([[null, null, 3]])).toBeNull();
  });
});
