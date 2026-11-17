import { pct } from "../../lib/format";

/** Distribution of a return, as thin bars with a zero line. */
export function Histogram({ counts, edges, label }: { counts: number[]; edges: number[]; label: string }) {
  const W = 480;
  const H = 150;
  const n = counts.length;
  const peak = Math.max(...counts, 1);
  const bar = (W - 12) / n;
  const low = edges[0];
  const high = edges[n];
  const zero = 6 + ((0 - low) / (high - low)) * (W - 12);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={label} className="block h-auto w-full max-w-[520px] text-[13px]">
      {counts.map((count, k) => {
        const h = ((H - 26) * count) / peak;
        return (
          <rect key={k} x={6 + k * bar + 1} y={H - 20 - h} width={bar - 2} height={h} rx="2" fill="var(--accent)">
            <title>{`${pct(edges[k])} to ${pct(edges[k + 1])}: ${count} trades`}</title>
          </rect>
        );
      })}
      {zero > 6 && zero < W - 6 && <line x1={zero} x2={zero} y1="0" y2={H - 20} stroke="var(--chart-axis)" />}
      <text x="6" y={H - 5} fill="var(--ink-2)">
        {pct(low, 1)}
      </text>
      <text x={W - 6} y={H - 5} textAnchor="end" fill="var(--ink-2)">
        {pct(high, 1)}
      </text>
    </svg>
  );
}
