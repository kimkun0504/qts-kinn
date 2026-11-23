import { int } from "../../lib/format";

interface BarsProps {
  items: [string, number][];
  total: number;
  onPick?: (name: string) => void;
  picked?: string;
}

export function Bars({ items, total, onPick, picked }: BarsProps) {
  const top = Math.max(1, ...items.map(([, n]) => n));
  return (
    <ul className="m-0 flex list-none flex-col gap-1.5 p-0">
      {items.map(([name, n]) => {
        const row = (
          <>
            <span className={`truncate text-left ${picked === name ? "font-semibold text-ink" : "text-ink-2"}`} title={name}>
              {name}
            </span>
            <span className="h-2 rounded-sm bg-raised">
              <span className="block h-2 rounded-sm bg-series-1" style={{ width: `${(100 * n) / top}%` }} />
            </span>
            <span className="text-right tabular-nums" title={`${((100 * n) / total).toFixed(1)}% of all`}>
              {int(n)}
            </span>
          </>
        );
        const grid = "grid w-full grid-cols-[minmax(0,14rem)_minmax(0,1fr)_4.5rem] items-center gap-3 text-sm";
        return (
          <li key={name}>
            {onPick ? (
              <button
                type="button"
                onClick={() => onPick(name)}
                aria-pressed={picked === name}
                className={`${grid} cursor-pointer rounded-sm py-0.5 hover:bg-raised focus-visible:outline-2 focus-visible:outline-accent`}
              >
                {row}
              </button>
            ) : (
              <div className={grid}>{row}</div>
            )}
          </li>
        );
      })}
    </ul>
  );
}
