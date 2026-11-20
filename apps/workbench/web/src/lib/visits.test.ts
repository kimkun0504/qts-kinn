import { describe, expect, it } from "vitest";
import { sinceLast } from "./visits";

describe("since the last visit", () => {
  it("counts new runs by agent and kind, and finished Lab runs", () => {
    const runs = [
      { started_at: "2026-11-19T22:00:00Z", agent: "gpt", kind: "event_study" },
      { started_at: "2026-11-19T22:05:00Z", agent: "gpt", kind: "event_study" },
      { started_at: "2026-11-19T22:10:00Z", agent: "gpt", kind: "backtest" },
      { started_at: "2026-11-18T10:00:00Z", agent: "claude", kind: "backtest" },
    ];
    const lab = [
      { created_at: "2026-11-19T23:00:00Z", state: "complete" },
      { created_at: "2026-11-19T23:10:00Z", state: "failed" },
    ];
    expect(sinceLast("2026-11-19T20:00:00Z", runs, lab)).toEqual([
      { label: "gpt: 2 event studies, 1 backtest", count: 3, href: "#/runs" },
      { label: "Lab: 1 run finished", count: 1, href: "#/lab" },
    ]);
    expect(sinceLast(null, runs, lab)).toEqual([]);
  });
});
