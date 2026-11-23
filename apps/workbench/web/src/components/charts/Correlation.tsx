import { useState } from "react";
import { num } from "../../lib/format";

function fill(v: number | null): string {
  if (v == null) return "var(--raised)";
  const share = Math.round(Math.min(1, Math.abs(v)) * 85);
  return `color-mix(in srgb, ${v >= 0 ? "var(--series-1)" : "var(--loss)"} ${share}%, var(--surface))`;
}

export function Correlation({ symbols, matrix, names }: { symbols: string[]; matrix: (number | null)[][]; names: Record<string, string> }) {
  const [hover, setHover] = useState<[number, number] | null>(null);
  const cell = 40;
  const shown = hover ? matrix[hover[0]][hover[1]] : null;
  return (
    <div className="flex flex-col gap-2">
      <div className="min-h-5 text-[13px] text-ink-2" aria-live="polite">
        {hover ? (
          <>
            <span className="font-semibold text-ink">{symbols[hover[0]]}</span> ({names[symbols[hover[0]]]}) and <span className="font-semibold text-ink">{symbols[hover[1]]}</span> (
            {names[symbols[hover[1]]]}): <span className="font-semibold text-ink">{shown == null ? "not enough days" : num(shown, 2)}</span>
          </>
        ) : (
          "Point at a square to read it."
        )}
      </div>
      <div className="overflow-x-auto">
        <table className="border-collapse text-[11px] tabular-nums" onMouseLeave={() => setHover(null)}>
          <tbody>
            {symbols.map((row, i) => (
              <tr key={row}>
                <th scope="row" className="pr-2 text-right font-medium whitespace-nowrap text-ink-2">
                  {row}
                </th>
                {symbols.map((column, j) =>
                  j <= i ? (
                    <td
                      key={column}
                      onMouseEnter={() => setHover([i, j])}
                      title={`${row} and ${column}: ${matrix[i][j] == null ? "not enough days" : num(matrix[i][j], 2)}`}
                      style={{ width: cell, minWidth: cell, height: 26, background: fill(matrix[i][j]) }}
                      className={`border border-surface text-center ${matrix[i][j] != null && Math.abs(matrix[i][j] as number) > 0.6 ? "text-on-accent" : "text-ink"} ${hover && hover[0] === i && hover[1] === j ? "outline-2 outline-ink" : ""}`}
                    >
                      {matrix[i][j] == null ? "" : num(matrix[i][j], 2).replace(/^(−?)0\./, "$1.")}
                    </td>
                  ) : (
                    <td key={column} style={{ width: cell, minWidth: cell }} />
                  ),
                )}
              </tr>
            ))}
            <tr>
              <th />
              {symbols.map((s) => (
                <th key={s} scope="col" className="pt-1 font-medium whitespace-nowrap text-ink-2" style={{ writingMode: "vertical-rl", transform: "rotate(180deg)", height: 44 }}>
                  {s}
                </th>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
