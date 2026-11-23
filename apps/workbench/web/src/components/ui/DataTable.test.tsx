import { fireEvent, render, screen } from "@testing-library/react";
import { DataTable } from "./DataTable";

const rows = [
  { id: "a", name: "base", net: "+0.52%" },
  { id: "b", name: "deep", net: "−0.85%" },
];

describe("DataTable", () => {
  it("colours negative numbers and reports row clicks", () => {
    const clicked: string[] = [];
    render(
      <DataTable
        rows={rows}
        rowKey={(r) => r.id}
        onRowClick={(r) => clicked.push(r.id)}
        selectedKey="a"
        columns={[
          { key: "name", header: "Config", align: "left", render: (r) => r.name },
          { key: "net", header: "Net", signed: true, render: (r) => r.net },
        ]}
      />,
    );
    expect(screen.getByText("−0.85%").className).toContain("text-neg");
    expect(screen.getByText("+0.52%").className).not.toContain("text-neg");
    fireEvent.click(screen.getByText("deep"));
    expect(clicked).toEqual(["b"]);
    expect(screen.getByText("base").closest("tr")?.getAttribute("aria-selected")).toBe("true");
    const first = screen.getByText("base").closest("tr") as HTMLElement;
    first.focus();
    fireEvent.keyDown(first, { key: "ArrowDown" });
    expect(document.activeElement).toBe(screen.getByText("deep").closest("tr"));
    fireEvent.keyDown(document.activeElement as HTMLElement, { key: "Enter" });
    expect(clicked).toEqual(["b", "b"]);
    fireEvent.keyDown(document.activeElement as HTMLElement, { key: "ArrowUp" });
    expect(document.activeElement).toBe(first);
  });
  it("says so when there is nothing to show", () => {
    render(<DataTable rows={[]} rowKey={() => "x"} columns={[]} empty="No runs yet." />);
    expect(screen.getByText("No runs yet.")).toBeTruthy();
  });
});
