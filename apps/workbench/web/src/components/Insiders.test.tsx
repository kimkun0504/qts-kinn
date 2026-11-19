import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { InsiderTrade } from "../lib/api";
import { Insiders, lastYear } from "./Insiders";

afterEach(cleanup);

const trade = (filed: string, side: "buy" | "sell", amount: number, insider = "Doe Jane"): InsiderTrade => ({
  filed,
  symbol: "ABCD",
  side,
  shares: 100,
  amount,
  traded_from: filed,
  traded_to: filed,
  insider,
  role: "CFO",
  accession: `${filed}-${side}-${insider}`,
});
const rows = [trade("2022-06-01", "buy", 50_000), trade("2023-03-01", "buy", 20_000), trade("2023-05-01", "sell", 1_000_000, "Roe Rick"), trade("2023-09-01", "sell", 500_000)];

describe("insider trades", () => {
  it("sums the year before the day the page is about", () => {
    expect(lastYear(rows, "2023-09-29")).toEqual({ buys: 1, bought: 20_000, sells: 2, sold: 1_500_000 });
    expect(lastYear(rows, "2023-01-01")).toEqual({ buys: 1, bought: 50_000, sells: 0, sold: 0 });
  });

  it("lists, filters and points the chart at a trade", () => {
    const onPick = vi.fn();
    render(<Insiders data={{ first: "2006-01-03", last: "2023-09-29", count: 4, rows }} onPick={onPick} />);
    expect(screen.getByText("$1.5M")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Bought 2" }));
    expect(screen.queryByText("Roe Rick")).toBeNull();
    fireEvent.click(screen.getAllByText("Doe Jane")[0]);
    expect(onPick).toHaveBeenCalledWith("2023-03-01");
  });
});
