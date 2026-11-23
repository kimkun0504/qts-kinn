import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { DataCatalog } from "../lib/api";
import { DataPage } from "./DataPage";

afterEach(cleanup);

const catalog: DataCatalog = {
  schema: "data-catalog-1",
  build: { id: "b1", created_at: "2026-11-16T02:21:45+00:00", data_version: "data-6", bars_id: "bars1", sharadar_snapshot: "2026-11-09", panel: { panel_rows: 26_415_679, splits: { listed: 9873, date_moved: 142 } } },
  builds: [{ id: "b1", created_at: "2026-11-16T02:21:45+00:00", data_version: "data-6", bars_id: "bars1", current: true }],
  calendar: { first: "2003-09-10", last: "2023-11-08", sessions: 5077 },
  companies: { total: 19496, delisted: 12941, categories: [["Domestic Common Stock", 13106]], sectors: [["Technology", 3438]] },
  tables: [{ name: "panel", path: "panel/*.parquet", files: 21, rows: 26_415_679, bytes: 1.1e9, note: "One row per company and session" }],
  bars: [{ name: "minute bars", path: "bars/bars1/minute", files: 21, years: ["2003", "2023"] }],
  inputs: [{ name: "form4", built: true, input_id: "fe7c", version: "form4-1", rows: 3_589_677, first: "2006-01-03", last: "2023-09-29", built_at: "2026-11-17T03:31:33+00:00" }],
  seal: { holdout_start: "2023-11-09", reads: 2407, last: "2026-11-17T21:46:46+00:00" },
};

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn(async () => ({ ok: true, status: 200, json: async () => catalog }) as unknown as Response));
});

describe("the data page", () => {
  it("shows the build, its tables, the inputs and the seal", async () => {
    render(<DataPage />);
    await waitFor(() => expect(screen.getAllByText("b1").length).toBeGreaterThan(0));
    expect(screen.getByText("5,077")).toBeTruthy();
    expect(screen.getAllByText("26.4M")).toHaveLength(2);
    expect(screen.getByText("1.1 GB")).toBeTruthy();
    expect(screen.getByText("2003 to 2023, 21 yearly files")).toBeTruthy();
    expect(screen.getByText("3 Jan 2006 to 29 Sep 2023")).toBeTruthy();
    expect(screen.getByText("moved to the day prices show it")).toBeTruthy();
    expect(screen.getByText(/2,407 owner reads logged/)).toBeTruthy();
  });
});
