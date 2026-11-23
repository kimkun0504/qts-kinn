import { describe, expect, it } from "vitest";
import { toCsv } from "./csv";

describe("toCsv", () => {
  it("writes a header and quotes what needs it", () => {
    const rows = [{ name: 'A "big" one', n: 1.5, note: null }, { name: "plain, with comma", n: -2, note: "x" }];
    const text = toCsv(rows, [
      { header: "Name", value: (r) => r.name },
      { header: "N", value: (r) => r.n },
      { header: "Note", value: (r) => r.note },
    ]);
    expect(text).toBe('Name,N,Note\n"A ""big"" one",1.5,\n"plain, with comma",-2,x\n');
  });
});
