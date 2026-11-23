import { describe, expect, it } from "vitest";
import { bySector } from "./Analytics";

describe("by sector", () => {
  it("adds up each sector's stocks and sorts by profit", () => {
    const rows = bySector([
      { sector: "Technology", trades: 3, wins: 2, total_net: 0.09, profit: 180 },
      { sector: "Energy", trades: 2, wins: 0, total_net: -0.04, profit: -80 },
      { sector: "Technology", trades: 1, wins: 1, total_net: 0.02, profit: 40 },
      { sector: null, trades: 1, wins: 1, total_net: 0.01, profit: 20 },
    ]);
    expect(rows.map((r) => [r.sector, r.trades, r.stocks, r.wins, r.profit])).toEqual([
      ["Technology", 4, 2, 3, 220],
      ["Unknown", 1, 1, 1, 20],
      ["Energy", 2, 1, 0, -80],
    ]);
    expect(rows[0].net).toBeCloseTo(0.11);
  });
});

describe("against random picks", () => {
  it("says where the run stands among the draws", async () => {
    const { luckVerdict } = await import("./Analytics");
    expect(luckVerdict(1)).toBe("better than almost every draw");
    expect(luckVerdict(0.93)).toBe("better than most draws");
    expect(luckVerdict(0.5)).toBe("within what chance gives");
    expect(luckVerdict(0.02)).toBe("worse than most draws");
  });
});
