import { useEffect, useRef, useState } from "react";
import { lab, type RunListRow } from "../lib/lab";
import { href } from "../lib/route";

const BUSY = 4_000;
const IDLE = 20_000;
const SHOWN = 12_000;

const live = (r: RunListRow) => r.state === "queued" || r.state === "running";

export function finished(before: RunListRow[], now: RunListRow[]): RunListRow[] {
  const was = new Set(before.filter(live).map((r) => r.run_id));
  return now.filter((r) => was.has(r.run_id) && !live(r));
}

export function RunningRuns() {
  const [runs, setRuns] = useState<RunListRow[]>([]);
  const [done, setDone] = useState<RunListRow[]>([]);
  const last = useRef<RunListRow[] | null>(null);
  useEffect(() => {
    let timer = 0;
    let stopped = false;
    const poll = () => {
      lab
        .runs()
        .then((rows) => {
          if (stopped) return;
          if (last.current) {
            const ended = finished(last.current, rows);
            if (ended.length) setDone((current) => [...ended, ...current].slice(0, 3));
          }
          last.current = rows;
          setRuns(rows);
          timer = window.setTimeout(poll, rows.some(live) ? BUSY : IDLE);
        })
        .catch(() => {
          if (!stopped) timer = window.setTimeout(poll, IDLE);
        });
    };
    poll();
    return () => {
      stopped = true;
      window.clearTimeout(timer);
    };
  }, []);
  useEffect(() => {
    if (!done.length) return;
    const timer = window.setTimeout(() => setDone([]), SHOWN);
    return () => window.clearTimeout(timer);
  }, [done]);
  const running = runs.filter(live);
  return (
    <>
      {running.length > 0 && (
        <a
          href={href({ page: "lab", name: running[0].algorithm, tab: running[0].run_id })}
          className="inline-flex min-h-9 items-center gap-2 rounded-md border border-line bg-surface px-3 text-sm font-medium text-ink no-underline hover:bg-raised focus-visible:outline-2 focus-visible:outline-accent"
        >
          <span aria-hidden="true" className="size-2 animate-pulse rounded-full bg-accent" />
          {running.length === 1 ? `Running ${running[0].algorithm}` : `${running.length} Lab runs going`}
        </a>
      )}
      {done.length > 0 && (
        <div role="status" className="fixed right-5 bottom-5 z-40 flex w-[320px] flex-col gap-2">
          {done.map((r) => (
            <div key={r.run_id} className="flex items-start justify-between gap-3 rounded-lg border border-line bg-surface px-4 py-3 text-sm shadow-[0_12px_32px_rgba(15,23,42,0.18)]">
              <div className="min-w-0">
                <div className="font-medium">
                  {r.algorithm} {r.state === "complete" ? "finished" : r.state === "failed" ? "failed" : "stopped"}
                </div>
                {r.headline && <div className="truncate text-[13px] text-ink-2">{r.headline}</div>}
              </div>
              <a href={href({ page: "lab", name: r.algorithm, tab: r.run_id })} className="shrink-0 text-[13px] font-medium text-accent no-underline hover:underline">
                Open
              </a>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
