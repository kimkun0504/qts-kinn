import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { RunNote } from "./RunNote";

afterEach(cleanup);

describe("a note on a run", () => {
  it("is written, saved through the Lab and shown", async () => {
    const calls: { url: string; method?: string; body?: string }[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        calls.push({ url, method: init?.method, body: init?.body as string | undefined });
        const payload = url.endsWith("/session") ? { token: "t" } : { run_id: "r1", note: JSON.parse(init?.body as string).note.trim() };
        return new Response(JSON.stringify(payload));
      }),
    );
    const onSaved = vi.fn();
    render(<RunNote runId="r1" note="" onSaved={onSaved} />);
    fireEvent.click(screen.getByRole("button", { name: "Add a note to this run" }));
    fireEvent.change(screen.getByLabelText("Note on this run"), { target: { value: "Shorter hold after the sweep " } });
    fireEvent.click(screen.getByRole("button", { name: "Save the note" }));
    await waitFor(() => expect(screen.getByText("Shorter hold after the sweep")).toBeTruthy());
    const put = calls.find((c) => c.method === "PUT");
    expect(put?.url).toBe("/api/lab/runs/r1/note");
    expect(onSaved).toHaveBeenCalledWith("Shorter hold after the sweep");
    expect(screen.getByRole("button", { name: "Edit the note" })).toBeTruthy();
  });

  it("shows the Lab's refusal and keeps the draft", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) =>
        url.endsWith("/session") ? new Response(JSON.stringify({ token: "t" })) : new Response(JSON.stringify({ error: "Keep a note under 2,000 characters." }), { status: 400 }),
      ),
    );
    render(<RunNote runId="r1" note="old" />);
    fireEvent.click(screen.getByRole("button", { name: "Edit the note" }));
    fireEvent.click(screen.getByRole("button", { name: "Save the note" }));
    await waitFor(() => expect(screen.getByRole("alert").textContent).toBe("Keep a note under 2,000 characters."));
    expect((screen.getByLabelText("Note on this run") as HTMLTextAreaElement).value).toBe("old");
  });
});
