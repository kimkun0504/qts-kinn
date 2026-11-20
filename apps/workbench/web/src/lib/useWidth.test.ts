import { describe, expect, it } from "vitest";
import { fitted } from "./useWidth";

describe("a chart's size", () => {
  it("draws at the width it has and keeps its shape within limits", () => {
    expect(fitted(null, 780, 260)).toEqual({ width: 780, height: 260 });
    expect(fitted(1170, 780, 260)).toEqual({ width: 1170, height: 390 });
    expect(fitted(2000, 780, 260)).toEqual({ width: 2000, height: 390 });
    expect(fitted(330, 780, 260)).toEqual({ width: 330, height: 195 });
  });
});
