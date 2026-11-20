import { useState } from "react";
import { niceTicks } from "../../lib/series";
import { fitted, useWidth } from "../../lib/useWidth";

export interface Series {
  name: string;
  short?: string;
  values: number[];
  color: string;
  dash?: string;
}

interface LineChartProps {
  title: string;
  labels: string[];
  series: Series[];
  format: (value: number) => string;
  band?: { low: number[]; high: number[]; color: string };
  height?: number;
  /** Show every x label (few points) instead of one per year (dates). */
  everyLabel?: boolean;
  labelAt?: (i: number) => boolean;
  tickText?: (i: number) => string;
  width?: number;
  marks?: { i: number; label: string }[];
  caption?: string;
}

const BASE_PAD = { left: 74, right: 136, top: 12, bottom: 32 };

/** Lines on one shared axis, with direct end labels, a legend and a hover readout. */
export function LineChart({ title, labels, series, format, band, height: designed = 260, everyLabel = false, labelAt, tickText, marks = [], caption, width: reference = 780 }: LineChartProps) {
  const [hover, setHover] = useState<number | null>(null);
  const [box, measured] = useWidth<HTMLDivElement>();
  const { width: W, height } = fitted(measured, reference, designed);
  const n = labels.length;
  if (n < 2) return <p className="m-0 px-4 py-6 text-ink-2">Not enough points for a chart.</p>;
  const longest = Math.max(0, ...series.map((s) => `${s.short ?? s.name} ${format(s.values[n - 1])}`.length));
  const all = series.flatMap((s) => s.values).concat(band ? [...band.low, ...band.high] : [], [0]);
  const low = Math.min(...all);
  const high = Math.max(...all);
  const ticks = niceTicks(low, high);
  const compact = W < 520;
  const left = Math.max(compact ? 44 : BASE_PAD.left, Math.round(Math.max(...ticks.map((v) => format(v).length)) * 7.4 + 14));
  const PAD = compact ? { ...BASE_PAD, left, right: 12 } : { ...BASE_PAD, left, right: Math.max(BASE_PAD.right, Math.round(longest * 7.6 + 14)) };
  const span = high - low || 1;
  const x = (i: number) => PAD.left + ((W - PAD.left - PAD.right) * i) / (n - 1);
  const y = (v: number) => PAD.top + (height - PAD.top - PAD.bottom) * (1 - (v - low) / span);
  const path = (values: number[]) => values.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");

  const xLabels: { i: number; text: string }[] = [];
  if (labelAt) labels.forEach((text, i) => labelAt(i) && xLabels.push({ i, text: tickText ? tickText(i) : text }));
  else if (everyLabel) labels.forEach((text, i) => xLabels.push({ i, text }));
  else {
    const years = new Set(labels.map((l) => l.slice(0, 4)));
    const every = years.size <= 12 ? 1 : 2;
    let seen = 0;
    let last = "";
    labels.forEach((label, i) => {
      const year = label.slice(0, 4);
      if (year !== last) {
        // A first year of only a few sessions would sit on top of the next label.
        const room = !xLabels.length || x(i) - x(xLabels[xLabels.length - 1].i) >= 44;
        if (seen % every === 0 && room) xLabels.push({ i, text: year });
        seen += 1;
        last = year;
      }
    });
  }

  const spaced: typeof xLabels = [];
  for (const label of xLabels) {
    const before = spaced[spaced.length - 1];
    if (!before || x(label.i) - x(before.i) >= (before.text.length + label.text.length) * 3.6 + 14) spaced.push(label);
  }

  const ends = (compact ? [] : series)
    .map((s) => ({ y: y(s.values[n - 1]), text: `${s.short ?? s.name} ${format(s.values[n - 1])}` }))
    .sort((a, b) => a.y - b.y);
  let previous = -99;
  for (const end of ends) {
    end.y = Math.max(end.y, previous + 16);
    previous = end.y;
  }

  return (
    <figure className="m-0 px-3 pt-3 pb-2">
      <figcaption className="flex flex-wrap gap-x-5 gap-y-1 px-1 pb-1 text-[13px] text-ink-2">
        {series.map((s) => (
          <span key={s.name} className="inline-flex items-center gap-1.5">
            <svg aria-hidden="true" width="18" height="4">
              <line x1="0" x2="18" y1="2" y2="2" stroke={s.color} strokeWidth="2" strokeDasharray={s.dash} />
            </svg>
            {s.name}
          </span>
        ))}
      </figcaption>
      <div ref={box} className="relative">
        <svg
          viewBox={`0 0 ${W} ${height}`}
          role="img"
          aria-label={title}
          className="block h-auto w-full text-[13px]"
          onMouseLeave={() => setHover(null)}
          onMouseMove={(event) => {
            const box = event.currentTarget.getBoundingClientRect();
            const px = ((event.clientX - box.left) / box.width) * W;
            setHover(Math.max(0, Math.min(n - 1, Math.round(((px - PAD.left) / (W - PAD.left - PAD.right)) * (n - 1)))));
          }}
        >
          {ticks.map((v) => (
            <g key={v}>
              <line x1={PAD.left} x2={W - PAD.right} y1={y(v)} y2={y(v)} stroke="var(--chart-grid)" />
              <text x={PAD.left - 8} y={y(v) + 4} textAnchor="end" fill="var(--ink-2)">
                {format(v)}
              </text>
            </g>
          ))}
          <line x1={PAD.left} x2={W - PAD.right} y1={y(0)} y2={y(0)} stroke="var(--chart-axis)" />
          {spaced.map(({ i, text }) => (
            <text key={i} x={x(i)} y={height - 10} textAnchor="middle" fill="var(--ink-2)">
              {text}
            </text>
          ))}
          {band && (
            <polygon
              points={[...band.high.map((v, i) => `${x(i)},${y(v)}`), ...band.low.map((v, i) => `${x(i)},${y(v)}`).reverse()].join(" ")}
              fill={band.color}
              opacity="0.16"
            />
          )}
          {series.map((s) => (
            <path key={s.name} d={path(s.values)} fill="none" stroke={s.color} strokeWidth="2" strokeDasharray={s.dash} strokeLinecap="round" />
          ))}
          {ends.map((end) => (
            <text key={end.text} x={W - PAD.right + 8} y={end.y + 4} fill="var(--ink)" fontWeight="600">
              {end.text}
            </text>
          ))}
          {marks.map((m) => (
            <g key={`${m.i}-${m.label}`}>
              <line x1={x(m.i)} x2={x(m.i)} y1={PAD.top} y2={height - PAD.bottom} stroke="var(--ink-3)" strokeDasharray="4 4" />
              <text x={x(m.i) + 5} y={PAD.top + 12} fill="var(--ink-2)">
                {m.label}
              </text>
            </g>
          ))}
          {hover != null && <line x1={x(hover)} x2={x(hover)} y1={PAD.top} y2={height - PAD.bottom} stroke="var(--chart-axis)" />}
        </svg>
        {hover != null && (
          <div className="pointer-events-none absolute top-1 left-16 rounded-md border border-line bg-raised px-2.5 py-1.5 text-[13px] whitespace-nowrap">
            <div className="font-semibold">{labels[hover]}</div>
            {series.map((s) => (
              <div key={s.name}>
                {s.name}: {format(s.values[hover])}
              </div>
            ))}
            {band && (
              <div className="text-ink-2">
                95% interval: {format(band.low[hover])} to {format(band.high[hover])}
              </div>
            )}
          </div>
        )}
      </div>
      {caption && <p className="m-0 px-1 pt-1 text-[13px] text-ink-3">{caption}</p>}
    </figure>
  );
}
