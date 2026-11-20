import { useRef, useState } from "react";
import { useWidth } from "../../lib/useWidth";
import { niceTicks } from "../../lib/series";

export interface PriceMarker {
  key: string;
  i: number;
  price: number;
  kind: "entry" | "exit";
  good: boolean | null;
}

export interface PriceSeries {
  date: string[];
  open: (number | null)[];
  high: (number | null)[];
  low: (number | null)[];
  close: (number | null)[];
  volume: (number | null)[];
}

export interface Overlay {
  name: string;
  values: (number | null)[];
  color: string;
}

export function movingAverage(values: (number | null)[], length: number): (number | null)[] {
  const out: (number | null)[] = new Array(values.length).fill(null);
  let sum = 0;
  let count = 0;
  for (let i = 0; i < values.length; i += 1) {
    const v = values[i];
    if (v != null) {
      sum += v;
      count += 1;
    }
    const drop = i - length >= 0 ? values[i - length] : null;
    if (i - length >= 0 && drop != null) {
      sum -= drop;
      count -= 1;
    }
    if (i >= length - 1 && count === length) out[i] = sum / length;
  }
  return out;
}

interface PriceChartProps {
  data: PriceSeries;
  overlays?: Overlay[];
  from: number;
  to: number;
  log: boolean;
  markers: PriceMarker[];
  results: number[];
  filings: number[];
  span: [number, number] | null;
  hover: number | null;
  onHover: (i: number | null) => void;
  onZoom: (from: number, to: number) => void;
  onReset: () => void;
  priceText: (value: number) => string;
}

const WIDTH = 960;
const H = 400;
const PAD = { left: 8, right: 70, top: 10 };
const PRICE_BOTTOM = 286;
const VOLUME_TOP = 300;
const VOLUME_BOTTOM = 362;
const CANDLES = 160;
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function logTicks(low: number, high: number): number[] {
  const out: number[] = [];
  for (let e = Math.floor(Math.log10(low)); e <= Math.ceil(Math.log10(high)); e += 1) {
    for (const m of [1, 2, 5]) {
      const v = m * 10 ** e;
      if (v >= low && v <= high) out.push(v);
    }
  }
  return out.length >= 3 ? out : niceTicks(low, high);
}

function timeLabels(dates: string[], from: number, to: number, x: (i: number) => number): { i: number; text: string }[] {
  const years = (Date.parse(dates[to]) - Date.parse(dates[from])) / (365.25 * 864e5);
  const out: { i: number; text: string }[] = [];
  let last = "";
  for (let i = from; i <= to; i += 1) {
    const [y, m] = dates[i].split("-");
    const month = Number(m) - 1;
    const key = years >= 3 ? y : years >= 1 ? `${y}-${Math.floor(month / 3)}` : `${y}-${month}`;
    if (key === last) continue;
    last = key;
    if (i === from) continue;
    const text = years >= 3 ? y : month === 0 ? y : MONTHS[month];
    if (!out.length || x(i) - x(out[out.length - 1].i) >= 56) out.push({ i, text });
  }
  return out;
}

export function PriceChart({ data, overlays = [], from, to, log, markers, results, filings, span, hover, onHover, onZoom, onReset, priceText }: PriceChartProps) {
  const svg = useRef<SVGSVGElement>(null);
  const [drag, setDrag] = useState<{ start: number; end: number } | null>(null);
  const [box, measured] = useWidth<HTMLDivElement>();
  const W = measured ?? WIDTH;
  const n = to - from + 1;
  if (n < 2) return <p className="m-0 py-10 text-center text-ink-2">Not enough prices in this range.</p>;
  const step = (W - PAD.left - PAD.right) / n;
  const x = (i: number) => PAD.left + (i - from + 0.5) * step;
  let low = Infinity;
  let high = -Infinity;
  let peak = 0;
  for (let i = from; i <= to; i += 1) {
    const lo = data.low[i] ?? data.close[i];
    const hi = data.high[i] ?? data.close[i];
    if (lo != null && lo > 0) low = Math.min(low, lo);
    if (hi != null) high = Math.max(high, hi);
    peak = Math.max(peak, data.volume[i] ?? 0);
  }
  for (const m of markers) {
    if (m.i >= from && m.i <= to && m.price > 0) {
      low = Math.min(low, m.price);
      high = Math.max(high, m.price);
    }
  }
  if (!Number.isFinite(low) || !Number.isFinite(high)) return <p className="m-0 py-10 text-center text-ink-2">No prices in this range.</p>;
  if (high <= low) high = low * 1.01 + 0.01;
  const useLog = log && low > 0;
  const margin = useLog ? 0.04 * Math.log(high / low) : 0.05 * (high - low);
  const lo = useLog ? Math.log(low) - margin : low - margin;
  const hi = useLog ? Math.log(high) + margin : high + margin;
  const y = (v: number) => {
    const t = useLog ? Math.log(Math.max(v, 1e-9)) : v;
    return PAD.top + (PRICE_BOTTOM - PAD.top) * (1 - (t - lo) / (hi - lo));
  };
  const ticks = (useLog ? logTicks(Math.exp(lo), Math.exp(hi)) : niceTicks(Math.max(0, lo), hi, 5)).filter((v) => y(v) >= PAD.top - 1 && y(v) <= PRICE_BOTTOM + 1);
  const gap = ticks.length > 1 ? Math.min(...ticks.slice(1).map((v, k) => v - ticks[k])) : 1;
  const digits = gap >= 1 ? 0 : Math.min(6, Math.max(2, 1 - Math.floor(Math.log10(gap))));
  const tickText = (v: number) => `$${v.toFixed(digits)}`;
  const vy = (v: number) => VOLUME_BOTTOM - (VOLUME_BOTTOM - VOLUME_TOP) * (peak ? v / peak : 0);
  const candles = n <= CANDLES;
  const index = (clientX: number) => {
    const box = svg.current?.getBoundingClientRect();
    if (!box) return from;
    const px = ((clientX - box.left) / box.width) * W;
    return Math.max(from, Math.min(to, from + Math.floor((px - PAD.left) / step)));
  };

  let line = "";
  let up = "";
  let down = "";
  const bodies: { i: number; o: number; c: number; h: number; l: number }[] = [];
  for (let i = from; i <= to; i += 1) {
    const c = data.close[i];
    if (c != null) line += `${line ? "L" : "M"}${x(i).toFixed(1)},${y(c).toFixed(1)}`;
    const v = data.volume[i];
    if (v) {
      const prev = data.close[i - 1] ?? c;
      const seg = `M${x(i).toFixed(1)},${VOLUME_BOTTOM}V${vy(v).toFixed(1)}`;
      if (c != null && prev != null && c < prev) down += seg;
      else up += seg;
    }
    if (candles && c != null) {
      const o = data.open[i] ?? c;
      bodies.push({ i, o, c, h: data.high[i] ?? Math.max(o, c), l: data.low[i] ?? Math.min(o, c) });
    }
  }
  const overlayPaths = overlays.map((o) => {
    let d = "";
    let pen = false;
    for (let i = from; i <= to; i += 1) {
      const v = o.values[i];
      if (v == null || (useLog && v <= 0)) {
        pen = false;
        continue;
      }
      d += `${pen ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`;
      pen = true;
    }
    return { name: o.name, color: o.color, d };
  });
  const area = line && !candles ? `${line}L${x(to).toFixed(1)},${PRICE_BOTTOM}L${x(from).toFixed(1)},${PRICE_BOTTOM}Z` : "";
  const labels = timeLabels(data.date, from, to, x);
  const shown = hover != null && hover >= from && hover <= to ? hover : null;
  const barWidth = Math.max(1, step * 0.62);

  return (
    <div ref={box}>
      <svg
        ref={svg}
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label="Daily prices and volume"
        className="block h-auto w-full touch-none text-[12px] select-none"
        onMouseMove={(event) => {
          const i = index(event.clientX);
          onHover(i);
          if (drag) setDrag({ ...drag, end: i });
        }}
        onMouseLeave={() => {
          onHover(null);
          setDrag(null);
        }}
        onMouseDown={(event) => {
          if (event.button === 0) setDrag({ start: index(event.clientX), end: index(event.clientX) });
        }}
        onMouseUp={() => {
          if (drag && Math.abs(drag.end - drag.start) >= 5) onZoom(Math.min(drag.start, drag.end), Math.max(drag.start, drag.end));
          setDrag(null);
        }}
        onDoubleClick={onReset}
      >
        {ticks.map((v) => (
          <g key={v}>
            <line x1={PAD.left} x2={W - PAD.right} y1={y(v)} y2={y(v)} stroke="var(--chart-grid)" />
            <text x={W - PAD.right + 8} y={y(v) + 4} fill="var(--ink-2)">
              {tickText(v)}
            </text>
          </g>
        ))}
        <line x1={PAD.left} x2={W - PAD.right} y1={VOLUME_BOTTOM} y2={VOLUME_BOTTOM} stroke="var(--chart-axis)" />
        {span && span[1] >= from && span[0] <= to && (
          <rect
            x={x(Math.max(span[0], from)) - step / 2}
            y={PAD.top}
            width={Math.max(step, x(Math.min(span[1], to)) - x(Math.max(span[0], from)) + step)}
            height={VOLUME_BOTTOM - PAD.top}
            fill="var(--accent)"
            opacity="0.08"
          />
        )}
        {area && <path d={area} fill="var(--series-1)" opacity="0.07" />}
        {!candles && <path d={line} fill="none" stroke="var(--series-1)" strokeWidth="1.5" strokeLinejoin="round" />}
        {bodies.map((b) => {
          const rising = b.c >= b.o;
          const colour = rising ? "var(--gain)" : "var(--loss)";
          const top = y(Math.max(b.o, b.c));
          return (
            <g key={b.i}>
              <line x1={x(b.i)} x2={x(b.i)} y1={y(b.h)} y2={y(b.l)} stroke={colour} />
              <rect x={x(b.i) - barWidth / 2} y={top} width={barWidth} height={Math.max(1, y(Math.min(b.o, b.c)) - top)} fill={rising ? "var(--surface)" : colour} stroke={colour} />
            </g>
          );
        })}
        {overlayPaths.map((o) => (
          <path key={o.name} d={o.d} fill="none" stroke={o.color} strokeWidth="1.4" strokeDasharray="6 3" opacity="0.9" />
        ))}
        <path d={up} stroke="var(--gain)" strokeWidth={barWidth} opacity="0.45" />
        <path d={down} stroke="var(--loss)" strokeWidth={barWidth} opacity="0.45" />
        {filings
          .filter((i) => i >= from && i <= to)
          .map((i) => (
            <line key={`f${i}`} x1={x(i)} x2={x(i)} y1={PRICE_BOTTOM - 5} y2={PRICE_BOTTOM} stroke="var(--ink-3)" />
          ))}
        {results
          .filter((i) => i >= from && i <= to)
          .map((i) => (
            <path key={`r${i}`} d={`M${x(i)},${PRICE_BOTTOM - 11}l4,4l-4,4l-4,-4z`} fill="var(--series-4)" />
          ))}
        {markers
          .filter((m) => m.i >= from && m.i <= to)
          .map((m) => {
            const colour = m.good == null ? "var(--ink)" : m.good ? "var(--gain)" : "var(--loss)";
            const px = x(m.i);
            const py = y(m.price);
            const d = m.kind === "entry" ? `M${px},${py + 2}l5,9h-10z` : `M${px},${py - 2}l5,-9h-10z`;
            return <path key={m.key} d={d} fill={colour} stroke="var(--surface)" strokeWidth="1" />;
          })}
        {labels.map((l) => (
          <text key={l.i} x={Math.min(W - PAD.right - 16, Math.max(PAD.left + 16, x(l.i)))} y={H - 18} textAnchor="middle" fill="var(--ink-2)">
            {l.text}
          </text>
        ))}
        {shown != null && data.close[shown] != null && (
          <g pointerEvents="none">
            <line x1={x(shown)} x2={x(shown)} y1={PAD.top} y2={VOLUME_BOTTOM} stroke="var(--chart-axis)" strokeDasharray="3 3" />
            <line x1={PAD.left} x2={W - PAD.right} y1={y(data.close[shown] as number)} y2={y(data.close[shown] as number)} stroke="var(--chart-axis)" strokeDasharray="3 3" />
            <rect x={W - PAD.right + 2} y={y(data.close[shown] as number) - 10} width={PAD.right - 2} height={20} rx="3" fill="var(--ink)" />
            <text x={W - PAD.right + 8} y={y(data.close[shown] as number) + 4} fill="var(--surface)" fontWeight="600">
              {priceText(data.close[shown] as number)}
            </text>
          </g>
        )}
        {drag && Math.abs(drag.end - drag.start) >= 1 && (
          <rect
            x={x(Math.min(drag.start, drag.end)) - step / 2}
            y={PAD.top}
            width={Math.abs(x(drag.end) - x(drag.start)) + step}
            height={VOLUME_BOTTOM - PAD.top}
            fill="var(--accent)"
            opacity="0.12"
            pointerEvents="none"
          />
        )}
      </svg>
    </div>
  );
}
