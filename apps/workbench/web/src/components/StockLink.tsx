import { href } from "../lib/route";

export function StockLink({ symbol, strong = true }: { symbol: string; strong?: boolean }) {
  return (
    <a
      href={href({ page: "stock", name: symbol })}
      onClick={(event) => event.stopPropagation()}
      className={`text-ink no-underline decoration-ink-3 underline-offset-2 hover:underline focus-visible:outline-2 focus-visible:outline-accent ${strong ? "font-semibold" : ""}`}
    >
      {symbol}
    </a>
  );
}
