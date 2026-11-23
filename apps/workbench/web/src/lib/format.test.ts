import { interval, isNegative, money, num, pct, plainPct, shortTime } from "./format";

describe("format", () => {
  it("writes signed percentages with a real minus sign", () => {
    expect(pct(0.0052)).toBe("+0.52%");
    expect(pct(-0.0009)).toBe("−0.09%");
    expect(pct(-0.00004, 1)).toBe("+0.0%");
    expect(pct(460.764, 1)).toBe("+46,076%");
    expect(pct(null)).toBe("–");
    expect(isNegative(pct(-0.01))).toBe(true);
    expect(isNegative(pct(0.01))).toBe(false);
  });
  it("formats money, numbers and plain percentages", () => {
    expect(money(34346.2)).toBe("+$34,346");
    expect(money(-20762.7)).toBe("−$20,763");
    expect(num(2.617)).toBe("2.62");
    expect(num(-0.4, 1)).toBe("−0.4");
    expect(plainPct(0.62)).toBe("62%");
    expect(shortTime("2026-11-15T20:41:57+00:00")).toBe("11-15 20:41");
  });
  it("shows an interval only when there is one", () => {
    expect(interval({ n: 10, mean: 0.0056, low: -0.0015, high: 0.0129 })).toBe("+0.56% (−0.15% to +1.29%)");
    expect(interval({ n: 1, mean: 0.01, low: null, high: null })).toBe("+1.00%");
    expect(interval({ n: 0, mean: null, low: null, high: null })).toBe("–");
  });
});

describe("compact numbers and price ticks", () => {
  it("shortens large numbers", async () => {
    const { compact } = await import("./format");
    expect(compact(1_234_567, "$")).toBe("$1.2M");
    expect(compact(699e6, "$")).toBe("$699M");
    expect(compact(-2500)).toBe("−2.5K");
    expect(compact(null)).toBe("–");
  });

  it("writes axis prices with the digits their size needs", async () => {
    const { priceTick } = await import("./format");
    expect(priceTick(0)).toBe("$0");
    expect(priceTick(150)).toBe("$150");
    expect(priceTick(12.5)).toBe("$12.50");
    expect(priceTick(0.05)).toBe("$0.050");
  });
});
