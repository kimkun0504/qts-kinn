import { describe, expect, it } from "vitest";
import { cleanName, type LabSettings } from "./lab";
import { base, changed, fromSettings, NUMBERS, readTickers, shown, toPatch } from "./labSettings";

const DEFAULTS: LabSettings = {
  period: "search",
  start: null,
  end: null,
  universe: { min_market_cap: 50e6, max_market_cap: null, min_price: 2, min_dollar_volume: 250_000, exclude_blank_checks: false },
  entry: { mode: "signal", top_n: 10, rank_order: "highest" },
  exit: { hold_days: 20, stop_loss: null, take_profit: null },
  book: { position_size: 2000, max_positions: 20 },
};
const spec = (path: string) => NUMBERS.find((s) => s.path === path)!;

describe("settings form", () => {
  it("shows the code's settings over the Lab's, in the form's units", () => {
    const merged = base(DEFAULTS, { universe: { max_market_cap: 300e6 }, exit: { stop_loss: 0.1 } });
    expect(shown(merged, spec("universe.max_market_cap"))).toBe("300");
    expect(shown(merged, spec("exit.stop_loss"))).toBe("10");
    expect(shown(merged, spec("exit.take_profit"))).toBe("none");
    expect(shown(merged, spec("universe.min_dollar_volume"))).toBe("250");
    expect(merged.universe.min_price).toBe(2);
  });

  it("sends only what was typed, scaled back", () => {
    const { patch, errors } = toPatch({ period: "late", numbers: { "universe.min_market_cap": "1,000", "exit.stop_loss": "7.5", "exit.hold_days": "" } });
    expect(errors).toEqual([]);
    expect(patch).toEqual({ period: "late", universe: { min_market_cap: 1e9 }, exit: { stop_loss: 0.075 } });
  });

  it("clears an optional setting with 0 and names a bad field", () => {
    expect(toPatch({ numbers: { "exit.stop_loss": "0" } }).patch).toEqual({ exit: { stop_loss: null } });
    expect(toPatch({ numbers: { "exit.hold_days": "2.5" } }).errors).toEqual(["Hold: a whole number."]);
    expect(toPatch({ numbers: { "exit.hold_days": "x" } }).errors).toEqual(["Hold: not a number."]);
    expect(toPatch({ period: "custom", start: "2015-01-01", numbers: {} }).errors.length).toBe(1);
  });

  it("turns a past run's settings back into a draft", () => {
    const used = base(DEFAULTS, { exit: { hold_days: 5, stop_loss: 0.1 }, period: "early" });
    const draft = fromSettings(used, DEFAULTS);
    expect(draft).toEqual({ period: "early", numbers: { "exit.hold_days": "5", "exit.stop_loss": "10" } });
    expect(toPatch(draft).patch).toEqual({ period: "early", exit: { hold_days: 5, stop_loss: 0.1 } });
  });
});

describe("names", () => {
  it("makes a usable algorithm name", () => {
    expect(cleanName("  My Big Idea! ")).toBe("my_big_idea");
    expect(cleanName("--x")).toBe("x");
  });
});

describe("toSweep", () => {
  it("reads values in the form's units", async () => {
    const { toSweep } = await import("./labSettings");
    expect(toSweep({ numbers: {}, sweep_field: "exit.hold_days", sweep_values: "5, 10 20" })).toEqual({ sweep: { field: "exit.hold_days", values: [5, 10, 20] }, error: null });
    expect(toSweep({ numbers: {}, sweep_field: "exit.stop_loss", sweep_values: "none, 5, 10" }).sweep?.values).toEqual([null, 0.05, 0.1]);
    expect(toSweep({ numbers: {} })).toEqual({ sweep: null, error: null });
  });

  it("refuses what the server would refuse", async () => {
    const { toSweep } = await import("./labSettings");
    expect(toSweep({ numbers: {}, sweep_field: "exit.hold_days", sweep_values: "5" }).error).toMatch(/2 to 12/);
    expect(toSweep({ numbers: {}, sweep_field: "exit.hold_days", sweep_values: "5, 5" }).error).toMatch(/differ/);
    expect(toSweep({ numbers: {}, sweep_field: "exit.hold_days", sweep_values: "5, 2.5" }).error).toMatch(/whole/);
    expect(toSweep({ numbers: {}, sweep_field: "exit.hold_days", sweep_values: "5, 999" }).error).toMatch(/from 1 to 250/);
  });
});

describe("named stocks", () => {
  it("reads tickers however they are typed", () => {
    expect(readTickers("aapl, msft;nvda  brk.b aapl")).toEqual({ tickers: ["AAPL", "BRK.B", "MSFT", "NVDA"], bad: [] });
    expect(readTickers("all")).toEqual({ tickers: [], bad: [] });
    expect(readTickers("AAPL 1X $T").bad).toEqual(["1X", "$T"]);
  });

  it("sends the list, clears it with all, and refuses a bad ticker", () => {
    expect(toPatch({ numbers: {}, tickers: "nvda aapl" }).patch).toEqual({ universe: { tickers: ["AAPL", "NVDA"] } });
    expect(toPatch({ numbers: {}, tickers: "all" }).patch).toEqual({ universe: { tickers: [] } });
    expect(toPatch({ numbers: {}, tickers: "AAPL, 9Z" }).errors).toEqual(["Only these stocks: not a ticker: 9Z."]);
    expect(changed({ numbers: {}, tickers: "AAPL" })).toBe(true);
    expect(changed({ numbers: {}, tickers: "  " })).toBe(false);
  });

  it("brings a past run's stocks back", () => {
    const run = { ...DEFAULTS, universe: { ...DEFAULTS.universe, tickers: ["AAPL", "MSFT"] } };
    expect(fromSettings(run, DEFAULTS).tickers).toBe("AAPL, MSFT");
    expect(fromSettings(DEFAULTS, run).tickers).toBe("all");
    expect(fromSettings(run, run).tickers).toBeUndefined();
  });
});

describe("shorts", () => {
  it("sends the side and the borrow fee in its units", () => {
    expect(toPatch({ side: "short", numbers: { "book.borrow_rate": "5" } }).patch).toEqual({ entry: { side: "short" }, book: { borrow_rate: 0.05 } });
    expect(toPatch({ numbers: { "book.borrow_rate": "120" } }).errors).toEqual(["Borrow fee a year: from 0 to 100."]);
    expect(changed({ side: "short", numbers: {} })).toBe(true);
    expect(toPatch({ mode: "rank", side: "both", numbers: {} }).patch).toEqual({ entry: { mode: "rank", side: "both" } });
  });

  it("brings a past short back and treats an old run as long", () => {
    const short = { ...DEFAULTS, entry: { ...DEFAULTS.entry, side: "short" as const }, book: { ...DEFAULTS.book, borrow_rate: 0.03 } };
    const draft = fromSettings(short, { ...DEFAULTS, book: { ...DEFAULTS.book, borrow_rate: 0.01 } });
    expect(draft.side).toBe("short");
    expect(draft.numbers["book.borrow_rate"]).toBe("3");
    expect(fromSettings(DEFAULTS, { ...DEFAULTS, entry: { ...DEFAULTS.entry, side: "long" } }).side).toBeUndefined();
  });
});
