import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { RunListRow } from "../lib/lab";
import { ErrorBoundary } from "./ErrorBoundary";
import { finished } from "./RunningRuns";
import { Shortcuts } from "./Shortcuts";

afterEach(cleanup);

const run = (run_id: string, state: RunListRow["state"]): RunListRow => ({
  run_id,
  algorithm: "mine",
  description: "",
  created_at: "",
  state,
  stage: null,
  error: null,
  trial: true,
  period: null,
  headline: null,
});

describe("the shell", () => {
  it("notices runs that were going and have ended", () => {
    const before = [run("a", "running"), run("b", "queued"), run("c", "complete")];
    const now = [run("a", "complete"), run("b", "running"), run("c", "complete"), run("d", "failed")];
    expect(finished(before, now).map((r) => r.run_id)).toEqual(["a"]);
  });

  it("lists the shortcuts and closes on Escape", () => {
    const onClose = vi.fn();
    render(<Shortcuts open onClose={onClose} />);
    expect(screen.getByRole("dialog", { name: "Keyboard shortcuts" })).toBeTruthy();
    expect(screen.getByText("Go to Screener")).toBeTruthy();
    fireEvent.keyDown(window, { key: "Escape" });
    expect(onClose).toHaveBeenCalled();
  });

  it("keeps a page's error inside the page", () => {
    const Broken = () => {
      throw new Error("bad numbers");
    };
    vi.spyOn(console, "error").mockImplementation(() => undefined);
    render(
      <ErrorBoundary>
        <Broken />
      </ErrorBoundary>,
    );
    expect(screen.getByText("This page stopped with an error")).toBeTruthy();
    expect(screen.getByText("bad numbers")).toBeTruthy();
  });
});
