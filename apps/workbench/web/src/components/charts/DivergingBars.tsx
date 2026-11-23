interface DivergingBarsProps {
  items: { label: string; value: number; note?: string }[];
  format: (value: number) => string;
  onPick?: (label: string) => void;
}

export function DivergingBars({ items, format, onPick }: DivergingBarsProps) {
  const top = Math.max(1e-9, ...items.map((i) => Math.abs(i.value)));
  return (
    <ul className="m-0 flex list-none flex-col gap-1 p-0">
      {items.map((item) => {
        const share = (50 * Math.abs(item.value)) / top;
        const bar = (
          <>
            <span className="truncate text-left text-ink-2" title={item.note ? `${item.label}: ${item.note}` : item.label}>
              {item.label}
            </span>
            <span className="relative h-3">
              <span className="absolute inset-y-0 left-1/2 w-px bg-line" />
              <span
                className={`absolute inset-y-0.5 rounded-sm ${item.value < 0 ? "bg-loss" : "bg-gain"}`}
                style={item.value < 0 ? { right: "50%", width: `${share}%` } : { left: "50%", width: `${share}%` }}
              />
            </span>
            <span className={`text-right tabular-nums ${item.value < 0 ? "text-neg" : ""}`}>{format(item.value)}</span>
          </>
        );
        const grid = "grid w-full grid-cols-[minmax(0,12rem)_minmax(0,1fr)_4.5rem] items-center gap-3 py-0.5 text-sm";
        return (
          <li key={item.label}>
            {onPick ? (
              <button type="button" onClick={() => onPick(item.label)} className={`${grid} cursor-pointer rounded-sm hover:bg-raised focus-visible:outline-2 focus-visible:outline-accent`}>
                {bar}
              </button>
            ) : (
              <div className={grid}>{bar}</div>
            )}
          </li>
        );
      })}
    </ul>
  );
}
