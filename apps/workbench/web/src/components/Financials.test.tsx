import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import type { FinancialPeriod, Financials as FinancialsData } from "../lib/api";
import { Financials, periodLabel } from "./Financials";

afterEach(cleanup);

const quarter = (period: string, revenue: number, income: number): FinancialPeriod => ({
  period,
  filed: period.replace(/-\d\d$/, "-28"),
  revenueusd: revenue,
  gp: revenue * 0.4,
  opinc: revenue * 0.2,
  netinccmnusd: income,
  epsusd: income / 1e8,
  ncfo: null,
  capex: null,
  fcf: null,
  cashnequsd: 5e8,
  debtusd: 1e8,
  equityusd: 2e9,
  sharesbas: 1e8,
});

const data: FinancialsData = {
  currency: "USD",
  quarterly: ["2022-03-31", "2022-06-30", "2022-09-30", "2022-12-31", "2023-03-31"].map((p, i) => quarter(p, 1e9 + i * 1e8, i === 0 ? -5e7 : 1e8)),
  trailing: [quarter("2023-03-31", 4.6e9, 3e8)],
};

describe("financials", () => {
  it("labels periods by calendar quarter", () => {
    expect(periodLabel("2023-09-30", "quarterly")).toBe("Q3 2023");
    expect(periodLabel("2023-09-30", "trailing")).toBe("Year to Q3 2023");
    expect(periodLabel("2023-12-31", "quarterly", true)).toBe("Q4 ’23");
  });

  it("lays out each line by period with growth against the same quarter a year before", () => {
    render(<Financials data={data} />);
    const table = () => within(screen.getByRole("table"));
    expect(table().getByText("Q1 2023")).toBeTruthy();
    expect(table().getByText("+40.0%")).toBeTruthy();
    expect(table().getAllByText("40.0%")).toHaveLength(5);
    expect(table().getByText("−$50.0M")).toBeTruthy();
    expect(table().getByText("−$0.50")).toBeTruthy();
    expect(table().getByText("−5.0%")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Trailing year" }));
    expect(table().getByText("Year to Q1 2023")).toBeTruthy();
    expect(table().getByText("$4.6B")).toBeTruthy();
  });

  it("greys periods filed on or after the day the page was opened for", () => {
    render(<Financials data={data} on="2023-01-01" />);
    const table = within(screen.getByRole("table"));
    const late = table.getByText("$1.4B").closest("td");
    const early = table.getByText("$1.0B").closest("td");
    expect(late?.className).toContain("text-ink-2");
    expect(early?.className).not.toContain("text-ink-2");
  });
});
