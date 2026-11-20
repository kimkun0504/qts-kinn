import { describe, expect, it } from "vitest";
import type { CostLeg } from "../lib/api";
import { legLabel } from "./CostsPage";

const leg = (fill: CostLeg["fill"]): CostLeg => ({ side: "buy", fill, shares: 100, value: 2000, commission: 0.35, fees: 0.1, slippage: 2 });

describe("trading costs", () => {
  it("names each leg by what it does and how it fills", () => {
    expect(legLabel(leg("auction"), false, true)).toBe("Buy at the open");
    expect(legLabel(leg("auction"), false, false)).toBe("Sell at the close");
    expect(legLabel(leg("marketable"), true, true)).toBe("Sell short marketable");
    expect(legLabel(leg("auction"), true, false)).toBe("Buy back at the close");
  });
});
