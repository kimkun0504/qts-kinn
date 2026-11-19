import { describe, expect, it } from "vitest";
import { movingAverage } from "./PriceChart";

describe("movingAverage", () => {
  it("averages the last n values once there are n of them", () => {
    expect(movingAverage([1, 2, 3, 4, 5], 3)).toEqual([null, null, 2, 3, 4]);
  });

  it("waits for a full window after a gap", () => {
    expect(movingAverage([1, null, 3, 4, 5, 6], 2)).toEqual([null, null, null, 3.5, 4.5, 5.5]);
  });
});
