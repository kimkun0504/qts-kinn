import { describe, expect, it } from "vitest";
import type { ScreenRow } from "../lib/screen";
import { peersOf } from "./Peers";

const row = (permaticker: number, industry: string, market_cap: number) => ({ permaticker, symbol: `S${permaticker}`, industry, market_cap }) as ScreenRow;

describe("peers", () => {
  it("takes the largest in the industry and keeps the stock itself", () => {
    const rows = [...Array.from({ length: 20 }, (_, i) => row(i, "Banks", 1e9 * (20 - i))), row(99, "Software", 5e12)];
    const top = peersOf(rows, 3, "Banks");
    expect(top.total).toBe(20);
    expect(top.rank).toBe(4);
    expect(top.peers).toHaveLength(15);
    const small = peersOf(rows, 18, "Banks");
    expect(small.rank).toBe(19);
    expect(small.peers.map((r) => r.permaticker).slice(-2)).toEqual([13, 18]);
    expect(peersOf(rows, 3, null)).toEqual({ peers: [], rank: null, total: 0 });
  });
});
