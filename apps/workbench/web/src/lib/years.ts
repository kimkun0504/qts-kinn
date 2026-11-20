import { money } from "./format";

export function concentration(years: { year: string; net_1x: number }[]): string | null {
  const total = years.reduce((a, y) => a + y.net_1x, 0);
  if (years.length < 3 || total <= 0) return null;
  const best = years.reduce((a, y) => (y.net_1x > a.net_1x ? y : a), years[0]);
  const share = best.net_1x / total;
  if (share < 0.4) return null;
  const without = total - best.net_1x;
  return `${best.year} made ${Math.round(100 * share)}% of the net profit; without it the other years made ${money(without)}. A result that rests on one year is weaker than its total suggests.`;
}
