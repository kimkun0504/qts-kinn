import { describe, expect, it } from "vitest";
import { concentration } from "./RunDetail";

describe("a backtest's years", () => {
  it("names a year that carries the result", () => {
    const years = [
      { year: "2007", net_1x: 2056 },
      { year: "2008", net_1x: 12292 },
      { year: "2009", net_1x: 255 },
      { year: "2011", net_1x: -1023 },
    ];
    expect(concentration(years)).toMatch(/^2008 made 91% of the net profit; without it the other years made \+\$1,288\./);
    expect(concentration(years.map((y) => ({ ...y, net_1x: 100 })))).toBeNull();
    expect(concentration(years.slice(0, 2))).toBeNull();
  });
});
