import { describe, expect, it } from "vitest";
import type { StudyRow } from "../lib/api";
import { filterStudies } from "./Studies";

const row = (name: string, verdict: string, when: string, trials: number | null, result = ""): StudyRow => ({ strategy: "s", strategy_title: "S", name, when, trials, result, verdict });
const rows = [row("big prints", "lead", "2026-11-17", 49, "quiet up day"), row("closing bids", "failed", "2026-11-18", 12), row("rebound", "passed", "2026-11-10", null)];

describe("filterStudies", () => {
  it("finds by words anywhere and by outcome", () => {
    expect(filterStudies(rows, "quiet", "all", "newest").map((r) => r.name)).toEqual(["big prints"]);
    expect(filterStudies(rows, "", "failed", "newest").map((r) => r.name)).toEqual(["closing bids"]);
  });

  it("orders by date or by trials", () => {
    expect(filterStudies(rows, "", "all", "newest").map((r) => r.name)).toEqual(["closing bids", "big prints", "rebound"]);
    expect(filterStudies(rows, "", "all", "oldest").map((r) => r.name)).toEqual(["rebound", "big prints", "closing bids"]);
    expect(filterStudies(rows, "", "all", "trials").map((r) => r.name)).toEqual(["big prints", "closing bids", "rebound"]);
  });
});
