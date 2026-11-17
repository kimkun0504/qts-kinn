import { isNegative } from "../../lib/format";

export interface StatItem {
  label: string;
  value: string;
  note?: string;
}

/** A row of headline numbers divided by hairlines. */
export function StatStrip({ items }: { items: StatItem[] }) {
  return (
    <section aria-label="Summary" className="flex flex-wrap rounded-lg border border-line bg-surface">
      {items.map((item) => (
        <div key={item.label} className="min-w-[170px] flex-1 border-r border-line px-4 py-3.5 last:border-r-0">
          <div className="text-[13px] text-ink-2">{item.label}</div>
          <div className={`mt-0.5 text-[22px] font-semibold tracking-tight ${isNegative(item.value) ? "text-neg" : ""}`}>
            {item.value}
          </div>
          {item.note && <div className="text-[13px] text-ink-3">{item.note}</div>}
        </div>
      ))}
    </section>
  );
}
