import type { ReactNode } from "react";
import { isNegative } from "../../lib/format";

export interface Column<Row> {
  key: string;
  header: string;
  align?: "left" | "right";
  render: (row: Row) => ReactNode;
  /** Colour negative numbers. Only for cells that render a formatted number string. */
  signed?: boolean;
  muted?: boolean;
  strong?: boolean;
}

interface DataTableProps<Row> {
  columns: Column<Row>[];
  rows: Row[];
  rowKey: (row: Row) => string;
  onRowClick?: (row: Row) => void;
  selectedKey?: string | null;
  empty?: string;
  minWidth?: number;
}

/** The one table component: dense rows, right-aligned numbers, optional row selection. */
export function DataTable<Row>({ columns, rows, rowKey, onRowClick, selectedKey, empty, minWidth }: DataTableProps<Row>) {
  if (!rows.length) return <p className="m-0 px-4 py-6 text-ink-2">{empty ?? "Nothing to show yet."}</p>;
  return (
    <table className="w-full border-collapse" style={minWidth ? { minWidth } : undefined}>
      <thead>
        <tr>
          {columns.map((column) => (
            <th
              key={column.key}
              scope="col"
              className={`border-b border-line px-3 py-2 text-xs font-medium whitespace-nowrap text-ink-2 ${
                column.align === "left" ? "text-left" : "text-right"
              }`}
            >
              {column.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => {
          const key = rowKey(row);
          const selected = selectedKey === key;
          return (
            <tr
              key={key}
              tabIndex={onRowClick ? 0 : undefined}
              aria-selected={onRowClick ? selected : undefined}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              onKeyDown={onRowClick ? (event) => event.key === "Enter" && onRowClick(row) : undefined}
              className={`${onRowClick ? "cursor-pointer hover:bg-raised focus-visible:outline-2 focus-visible:outline-accent" : ""} ${
                selected ? "bg-raised shadow-[inset_2px_0_0_var(--accent)]" : ""
              }`}
            >
              {columns.map((column) => {
                const content = column.render(row);
                const negative = column.signed && typeof content === "string" && isNegative(content);
                return (
                  <td
                    key={column.key}
                    className={`border-b border-line-soft px-3 py-2 whitespace-nowrap ${
                      column.align === "left" ? "text-left" : "text-right"
                    } ${negative ? "text-neg" : column.muted ? "text-ink-2" : ""} ${column.strong ? "font-semibold" : ""}`}
                  >
                    {content}
                  </td>
                );
              })}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
