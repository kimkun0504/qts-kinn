import { useState } from "react";
import { niceTicks } from "../../lib/series";

interface BarChartProps {
  title: string;
  labels: string[];
  values: (number | null)[];
  format: (value: number) => string;
  marked?: number[];
  height?: number;
  width?: number;
}

const PAD = { left: 64, right: 16, top: 14, bottom: 30 };

export function BarChart({ title, labels, values, format, marked = [], height = 220, width: W = 780 }: BarChartProps) {
  const [hover, setHover] = useState<number | null>(null);
  const finite = values.filter((v): v is number => v != null && Number.isFinite(v));
  if (!finite.length) return <p className="m-0 py-6 text-ink-2">Nothing to show.</p>;
  const low = Math.min(0, ...finite);
  const high = Math.max(0, ...finite);
  const ticks = niceTicks(low, high, 4);
  const lo = Math.min(low, ticks[0]);
  const hi = Math.max(high, ticks[ticks.length - 1]);
  const y = (v: number) => PAD.top + (height - PAD.top - PAD.bottom) * (1 - (v - lo) / (hi - lo || 1));
  const step = (W - PAD.left - PAD.right) / values.length;
  const width = Math.max(4, step * 0.64);
  return (
    <div className="relative">
      <svg viewBox={`0 0 ${W} ${height}`} role="img" aria-label={title} className="block h-auto w-full text-[12px]" onMouseLeave={() => setHover(null)}>
        {ticks.map((v) => (
          <g key={v}>
            <line x1={PAD.left} x2={W - PAD.right} y1={y(v)} y2={y(v)} stroke={v === 0 ? "var(--chart-axis)" : "var(--chart-grid)"} />
            <text x={PAD.left - 8} y={y(v) + 4} textAnchor="end" fill="var(--ink-2)">
              {format(v)}
            </text>
          </g>
        ))}
        {values.map((v, i) => {
          const x = PAD.left + step * i + (step - width) / 2;
          const top = v == null ? y(0) : y(Math.max(0, v));
          const bottom = v == null ? y(0) : y(Math.min(0, v));
          return (
            <g key={labels[i]} onMouseEnter={() => setHover(i)}>
              <rect x={PAD.left + step * i} y={PAD.top} width={step} height={height - PAD.top - PAD.bottom} fill="transparent" />
              {v != null && <rect x={x} y={top} width={width} height={Math.max(1, bottom - top)} rx="2" fill={v >= 0 ? "var(--gain)" : "var(--loss)"} opacity={marked.length && !marked.includes(i) ? 0.55 : 1} />}
              <text x={x + width / 2} y={height - 10} textAnchor="middle" fill={marked.includes(i) ? "var(--ink)" : "var(--ink-2)"} fontWeight={marked.includes(i) ? 600 : 400}>
                {labels[i]}
              </text>
            </g>
          );
        })}
      </svg>
      {hover != null && values[hover] != null && (
        <div className="pointer-events-none absolute top-1 right-2 rounded-md border border-line bg-raised px-2.5 py-1 text-[13px]">
          {labels[hover]}: {format(values[hover] as number)}
        </div>
      )}
    </div>
  );
}
