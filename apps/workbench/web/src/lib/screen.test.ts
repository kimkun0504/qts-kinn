import { describe, expect, it } from "vitest";
import { decode, EMPTY, encode, matcher, median, parseValue, type ScreenRow } from "./screen";

const row = (over: Partial<ScreenRow>): ScreenRow =>
  ({
    symbol: "AAA",
    permaticker: 1,
    name: "Alpha Inc",
    sector: "Technology",
    industry: "Software",
    category: "Domestic Common Stock",
    exchange: "NASDAQ",
    market_cap: 5e9,
    ret_1y: 0.2,
    pe: 18,
    ...over,
  }) as ScreenRow;

describe("parseValue", () => {
  it("reads money with K, M, B and T", () => {
    expect(parseValue("300M", "money")).toBe(3e8);
    expect(parseValue("$2.5b", "money")).toBe(2.5e9);
    expect(parseValue("1,000", "money")).toBe(1000);
  });

  it("reads percents as fractions, minus signs included", () => {
    expect(parseValue("−20", "percent")).toBeCloseTo(-0.2);
    expect(parseValue("5%", "percent")).toBeCloseTo(0.05);
  });

  it("tells an empty box from a bad one", () => {
    expect(parseValue("  ", "ratio")).toBeNull();
    expect(parseValue("ten", "ratio")).toBeUndefined();
    expect(parseValue("2B", "ratio")).toBeUndefined();
  });
});

describe("matcher", () => {
  it("applies the kind, sector, text and every bound", () => {
    const test = matcher({
      ...EMPTY,
      sector: "Technology",
      text: "alpha",
      conditions: [
        { field: "market_cap", min: "1B", max: "" },
        { field: "pe", min: "", max: "20" },
      ],
    });
    expect(test(row({}))).toBe(true);
    expect(test(row({ pe: 25 }))).toBe(false);
    expect(test(row({ pe: null }))).toBe(false);
    expect(test(row({ market_cap: 5e8 }))).toBe(false);
    expect(test(row({ sector: "Energy" }))).toBe(false);
    expect(test(row({ name: "Beta Corp" }))).toBe(false);
    expect(test(row({ category: "ADR Common Stock" }))).toBe(false);
  });

  it("ignores a filter with a bad or empty value", () => {
    const test = matcher({
      ...EMPTY,
      conditions: [
        { field: "pe", min: "x", max: "" },
        { field: "ret_1y", min: "", max: "" },
      ],
    });
    expect(test(row({ pe: null, ret_1y: null }))).toBe(true);
  });
});

describe("a screen in the address", () => {
  it("survives a round trip", () => {
    const screen = { ...EMPTY, kind: "adr", text: "bank", sector: "Financial Services", conditions: [{ field: "ret_1y" as const, min: "-50", max: "" }] };
    expect(decode(encode(screen))).toEqual(screen);
    expect(encode(EMPTY)).toBe("");
    expect(decode("f=nothing:1:2&kind=bogus")).toEqual(EMPTY);
  });
});

it("finds the median of what is known", () => {
  expect(median([3, null, 1, 2])).toBe(2);
  expect(median([4, 1, 2, 3])).toBe(2.5);
  expect(median([null])).toBeNull();
});
