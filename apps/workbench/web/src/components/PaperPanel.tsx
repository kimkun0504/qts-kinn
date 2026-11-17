import type { PaperBook, PaperPosition, PaperSnapshot } from "../lib/api";
import { day, dollars, money, pct } from "../lib/format";

const BOOK: Record<string, string> = {
  ten: "10 positions",
  twenty: "20 positions",
  ten_quality: "10, quality test",
  twenty_quality: "20, quality test",
  ten_quality_trend: "10, quality test, 20-day exit",
};
export const bookName = (name: string) => BOOK[name] ?? name.replace(/_/g, " ");

/** What a book has made so far: closed trades plus open positions at the last close. */
export const bookTotal = (book: PaperBook) => book.net + book.unrealised;

/** Tomorrow's orders, in words. */
export function Orders({ paper }: { paper: PaperSnapshot }) {
  const names = (rows: { symbol: string }[]) => (rows.length ? rows.map((r) => r.symbol).join(", ") : "nothing");
  return (
    <div className="flex flex-wrap gap-x-7 gap-y-1.5 rounded-lg bg-raised px-3.5 py-2.5">
      <span>
        <span className="text-[13px] text-ink-3">Buy at the next open</span> <strong>{names(paper.buy_next_open)}</strong>
      </span>
      {paper.sell_next_open.length > 0 && (
        <span>
          <span className="text-[13px] text-ink-3">Sell at the next open</span> <strong>{names(paper.sell_next_open)}</strong>
        </span>
      )}
      <span>
        <span className="text-[13px] text-ink-3">Sell at the next close</span> <strong>{names(paper.sell_next_close)}</strong>
      </span>
    </div>
  );
}

/** Open positions with a bar for the change since entry, nearest their exit first. */
export function Positions({ positions, hold, limit, books = false }: { positions: PaperPosition[]; hold: number | null; limit?: number; books?: boolean }) {
  const sorted = [...positions].sort((a, b) => b.sessions - a.sessions || a.symbol.localeCompare(b.symbol));
  const shown = limit ? sorted.slice(0, limit) : sorted;
  const widest = Math.max(0.3, ...positions.map((p) => Math.abs(p.change ?? 0)));
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="text-left text-[13px] text-ink-3">
            <th scope="col" className="border-b border-line px-3 py-2 font-semibold">Stock</th>
            <th scope="col" className="border-b border-line px-3 py-2 font-semibold">Bought</th>
            <th scope="col" className="border-b border-line px-3 py-2 text-right font-semibold">Since entry</th>
            <th scope="col" className="w-[30%] border-b border-line px-3 py-2">
              <span className="sr-only">Change as a bar</span>
            </th>
            <th scope="col" className="border-b border-line px-3 py-2 text-right font-semibold">Session</th>
            {books && <th scope="col" className="border-b border-line px-3 py-2 font-semibold">Books</th>}
          </tr>
        </thead>
        <tbody>
          {shown.map((p) => {
            const change = p.change ?? 0;
            const width = Math.min(Math.abs(change) / widest, 1) * 50;
            return (
              <tr key={`${p.symbol}-${p.signal_day}`}>
                <td className="border-b border-line-soft px-3 py-2 font-semibold">{p.symbol}</td>
                <td className="border-b border-line-soft px-3 py-2 whitespace-nowrap text-ink-2">{day(p.entry_day, true)}</td>
                <td className={`border-b border-line-soft px-3 py-2 text-right whitespace-nowrap ${p.change == null ? "text-ink-3" : change < 0 ? "text-neg" : "text-pos"}`}>{pct(p.change, 1)}</td>
                <td className="border-b border-line-soft px-3 py-2">
                  <div aria-hidden="true" className="relative h-2.5">
                    <div className="absolute -inset-y-1 left-1/2 w-px bg-line" />
                    <div className={`absolute inset-y-0 rounded-sm ${change < 0 ? "bg-loss" : "bg-gain"}`} style={{ left: `${change < 0 ? 50 - width : 50}%`, width: `${width}%` }} />
                  </div>
                </td>
                <td className="border-b border-line-soft px-3 py-2 text-right whitespace-nowrap text-ink-2">
                  {p.sessions}
                  {hold ? ` of ${hold}` : ""}
                </td>
                {books && <td className="border-b border-line-soft px-3 py-2 text-[13px] text-ink-2">{p.books.length ? p.books.map(bookName).join("; ") : "followed only"}</td>}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/** The books side by side: what each holds and what it has made. */
export function Books({ books }: { books: PaperBook[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="text-left text-[13px] text-ink-3">
            <th scope="col" className="border-b border-line px-3 py-2 font-semibold">Book</th>
            <th scope="col" className="border-b border-line px-3 py-2 text-right font-semibold">Open</th>
            <th scope="col" className="border-b border-line px-3 py-2 text-right font-semibold">Open positions</th>
            <th scope="col" className="border-b border-line px-3 py-2 text-right font-semibold">Closed trades</th>
            <th scope="col" className="border-b border-line px-3 py-2 text-right font-semibold">A trade</th>
            <th scope="col" className="border-b border-line px-3 py-2 text-right font-semibold">Closed profit</th>
            <th scope="col" className="border-b border-line px-3 py-2 text-right font-semibold">Total</th>
          </tr>
        </thead>
        <tbody>
          {books.map((book) => {
            const total = bookTotal(book);
            const tone = (v: number) => (v < 0 ? "text-neg" : v > 0 ? "text-pos" : "");
            return (
              <tr key={book.name}>
                <td className="border-b border-line-soft px-3 py-2.5">
                  <div className="font-semibold">{bookName(book.name)}</div>
                  {book.account != null && book.slots != null && <div className="text-[13px] text-ink-3">{dollars(book.account / book.slots)} each</div>}
                </td>
                <td className="border-b border-line-soft px-3 py-2.5 text-right">{book.open}</td>
                <td className={`border-b border-line-soft px-3 py-2.5 text-right ${tone(book.unrealised)}`}>{book.open ? money(book.unrealised) : "–"}</td>
                <td className="border-b border-line-soft px-3 py-2.5 text-right">{book.trades}</td>
                <td className={`border-b border-line-soft px-3 py-2.5 text-right ${tone(book.mean ?? 0)}`}>{pct(book.mean)}</td>
                <td className={`border-b border-line-soft px-3 py-2.5 text-right ${tone(book.net)}`}>{book.trades ? money(book.net) : "–"}</td>
                <td className={`border-b border-line-soft px-3 py-2.5 text-right font-semibold ${tone(total)}`}>{book.open || book.trades ? money(total) : "–"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
