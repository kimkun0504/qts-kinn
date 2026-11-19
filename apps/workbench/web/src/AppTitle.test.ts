import { describe, expect, it } from "vitest";
import { pageTitle } from "./App";
import type { Board } from "./lib/api";

describe("the tab title", () => {
  it("names what the page is about", () => {
    const board = { rows: [{ strategy: "earnings_drift", title: "Earnings drift", variant: false }] } as unknown as Board;
    expect(pageTitle({ page: "strategy", name: "earnings_drift" }, board)).toBe("Earnings drift");
    expect(pageTitle({ page: "stock", name: "AAPL" }, null)).toBe("AAPL");
    expect(pageTitle({ page: "lab", name: "momentum_rank" }, null)).toBe("momentum_rank in the Lab");
    expect(pageTitle({ page: "screener" }, null)).toBe("Screener");
    expect(pageTitle({ page: "paper", name: "big_prints" }, null)).toBe("big prints paper ledger");
  });
});
