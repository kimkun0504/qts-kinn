import { describe, expect, it } from "vitest";
import { diffLines, flatten, hunks } from "./diff";

describe("diffLines", () => {
  it("keeps common lines and marks the changes", () => {
    const out = diffLines("a\nb\nc", "a\nx\nc");
    expect(out.map((l) => `${l.kind[0]}${l.text}`)).toEqual(["sa", "rb", "ax", "sc"]);
    expect(out[2].right).toBe(2);
  });

  it("cuts long unchanged stretches into hunks", () => {
    const before = Array.from({ length: 20 }, (_, i) => `line ${i}`).join("\n");
    const after = before.replace("line 10", "changed");
    const shown = hunks(diffLines(before, after), 2);
    expect(shown.filter((l) => l === null)).toHaveLength(0);
    expect(shown.map((l) => l?.text)).toEqual(["line 8", "line 9", "line 10", "changed", "line 11", "line 12"]);
  });
});

describe("flatten", () => {
  it("names nested settings by their path", () => {
    expect(flatten({ exit: { hold_days: 15, stop_loss: null }, period: "search" })).toEqual({ "exit.hold_days": "15", "exit.stop_loss": "null", period: '"search"' });
  });
});
