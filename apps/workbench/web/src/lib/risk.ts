export function returns(close: (number | null)[]): (number | null)[] {
  return close.map((c, i) => {
    const before = i > 0 ? close[i - 1] : null;
    return c != null && before != null && before > 0 ? c / before - 1 : null;
  });
}

function pairs(a: (number | null)[], b: (number | null)[], last: number): [number, number][] {
  const out: [number, number][] = [];
  const start = Math.max(0, a.length - last);
  for (let i = start; i < a.length; i += 1) {
    const x = a[i];
    const y = b[i];
    if (x != null && y != null) out.push([x, y]);
  }
  return out;
}

export function beta(stock: (number | null)[], market: (number | null)[], last: number): { beta: number; correlation: number; n: number } | null {
  const both = pairs(stock, market, last);
  if (both.length < 40) return null;
  const n = both.length;
  const mx = both.reduce((s, [x]) => s + x, 0) / n;
  const my = both.reduce((s, [, y]) => s + y, 0) / n;
  let sxy = 0;
  let sxx = 0;
  let syy = 0;
  for (const [x, y] of both) {
    sxy += (x - mx) * (y - my);
    sxx += (x - mx) ** 2;
    syy += (y - my) ** 2;
  }
  if (!syy || !sxx) return null;
  return { beta: sxy / syy, correlation: sxy / Math.sqrt(sxx * syy), n };
}

export function volatility(values: (number | null)[], last: number): number | null {
  const known = values.slice(-last).filter((v): v is number => v != null);
  if (known.length < 40) return null;
  const mean = known.reduce((s, v) => s + v, 0) / known.length;
  const variance = known.reduce((s, v) => s + (v - mean) ** 2, 0) / (known.length - 1);
  return Math.sqrt(variance * 252);
}

export interface Drawdown {
  peak: string;
  trough: string;
  recovered: string | null;
  depth: number;
}

export function drawdowns(dates: string[], close: (number | null)[], count = 5): Drawdown[] {
  const found: Drawdown[] = [];
  let peak = -1;
  let trough = -1;
  for (let i = 0; i < close.length; i += 1) {
    const c = close[i];
    if (c == null) continue;
    if (peak < 0 || c >= (close[peak] as number)) {
      if (trough >= 0 && (close[trough] as number) < (close[peak] as number)) {
        found.push({ peak: dates[peak], trough: dates[trough], recovered: dates[i], depth: (close[trough] as number) / (close[peak] as number) - 1 });
      }
      peak = i;
      trough = -1;
    } else if (trough < 0 || c < (close[trough] as number)) {
      trough = i;
    }
  }
  if (trough >= 0 && peak >= 0) found.push({ peak: dates[peak], trough: dates[trough], recovered: null, depth: (close[trough] as number) / (close[peak] as number) - 1 });
  return found.sort((a, b) => a.depth - b.depth).slice(0, count);
}

export interface Season {
  month: number;
  mean: number | null;
  median: number | null;
  up: number;
  years: number;
}

export function seasons(dates: string[], close: (number | null)[]): Season[] {
  const ends: { key: string; close: number }[] = [];
  for (let i = 0; i < dates.length; i += 1) {
    const c = close[i];
    if (c == null) continue;
    const key = dates[i].slice(0, 7);
    if (ends.length && ends[ends.length - 1].key === key) ends[ends.length - 1].close = c;
    else ends.push({ key, close: c });
  }
  const by: number[][] = Array.from({ length: 12 }, () => []);
  for (let k = 1; k < ends.length; k += 1) {
    by[Number(ends[k].key.slice(5, 7)) - 1].push(ends[k].close / ends[k - 1].close - 1);
  }
  return by.map((values, m) => {
    const sorted = [...values].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return {
      month: m + 1,
      mean: values.length ? values.reduce((s, v) => s + v, 0) / values.length : null,
      median: !sorted.length ? null : sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2,
      up: values.filter((v) => v > 0).length,
      years: values.length,
    };
  });
}
