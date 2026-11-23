import { describe, expect, it } from "vitest";
import { sortRows } from "./sort";

describe("sortRows", () => {
  const rows = [
    { name: "b", value: 2 },
    { name: "a", value: null },
    { name: "c", value: -1 },
  ];
  const read = (row: (typeof rows)[number], key: string) => (key === "name" ? row.name : row.value);

  it("orders numbers both ways and keeps blanks last", () => {
    expect(sortRows(rows, { key: "value", dir: "desc" }, read).map((r) => r.name)).toEqual(["b", "c", "a"]);
    expect(sortRows(rows, { key: "value", dir: "asc" }, read).map((r) => r.name)).toEqual(["c", "b", "a"]);
  });

  it("orders text", () => {
    expect(sortRows(rows, { key: "name", dir: "asc" }, read).map((r) => r.name)).toEqual(["a", "b", "c"]);
  });
});
