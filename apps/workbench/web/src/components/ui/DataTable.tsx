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
  /** Cut text longer than this many pixels with an ellipsis; the full text shows on hover. */
  max?: number;
  /** The header sorts by this column (the table's owner does the sorting). */
  sortable?: boolean;
}

export interface Sort {
  key: string;
  dir: "asc" | "desc";
}

interface DataTableProps<Row> {
  columns: Column<Row>[];
  rows: Row[];
  rowKey: (row: Row) => string;
  onRowClick?: (row: Row) => void;
  selectedKey?: string | null;
  empty?: string;
  minWidth?: number;
  sort?: Sort;
  onSort?: (key: string) => void;
}

/** The one table component: dense rows, right-aligned numbers, optional row selection. */
export function DataTable<Row>({ columns, rows, rowKey, onRowClick, selectedKey, empty, minWidth, sort, onSort }: DataTableProps<Row>) {
  if (!rows.length) return <p className="m-0 px-4 py-6 text-ink-2">{empty ?? "Nothing to show yet."}</p>;
  return (
    <table className="w-full border-collapse" style={minWidth ? { minWidth } : undefined}>
      <thead>
        <tr>
          {columns.map((column) => {
            const sorted = sort?.key === column.key ? sort.dir : null;
            return (
              <th
                key={column.key}
                scope="col"
                aria-sort={sorted ? (sorted === "asc" ? "ascending" : "descending") : undefined}
                className={`sticky top-0 z-[1] border-b border-line bg-surface px-3 py-2 text-[13px] font-medium whitespace-nowrap text-ink-2 ${
                  column.align === "left" ? "text-left" : "text-right"
                }`}
              >
                {column.sortable && onSort ? (
                  <button
                    type="button"
                    onClick={() => onSort(column.key)}
                    className={`inline-flex cursor-pointer items-center gap-1 font-medium hover:text-ink focus-visible:outline-2 focus-visible:outline-accent ${sorted ? "text-ink" : ""}`}
                  >
                    {column.header}
                    <span aria-hidden="true" className={`text-[10px] ${sorted ? "" : "opacity-0"}`}>
                      {sorted === "asc" ? "▲" : "▼"}
                    </span>
                  </button>
                ) : (
                  column.header
                )}
              </th>
            );
          })}
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
                selected ? "bg-raised font-medium" : ""
              }`}
            >
              {columns.map((column) => {
                const content = column.render(row);
                const negative = column.signed && typeof content === "string" && isNegative(content);
                return (
                  <td
                    key={column.key}
                    className={`border-b border-line-soft px-3 py-2 text-sm whitespace-nowrap ${
                      column.align === "left" ? "text-left" : "text-right"
                    } ${negative ? "text-neg" : column.muted ? "text-ink-2" : ""} ${column.strong ? "font-semibold" : ""}`}
                  >
                    {column.max && typeof content === "string" ? (
                      <span title={content} className="block truncate" style={{ maxWidth: column.max }}>
                        {content}
                      </span>
                    ) : (
                      content
                    )}
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
