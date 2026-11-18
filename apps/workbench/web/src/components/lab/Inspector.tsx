import { type ReactNode, useEffect, useState } from "react";
import type { Field, LabSettings, Meta, Version } from "../../lib/lab";
import { changed, type Draft, NUMBERS, type NumberSpec, shown } from "../../lib/labSettings";
import { History } from "./History";

interface InspectorProps {
  meta: Meta;
  /** The Lab's defaults with the algorithm's SETTINGS over them. */
  base: LabSettings;
  draft: Draft;
  onChange: (draft: Draft) => void;
  /** The algorithm, for its saved versions. */
  name: string;
  historyKey: number;
  onRestore: (code: string, version: Version) => void;
}

// One control width and one row height for every setting, so the column reads as a table.
const control = "h-8 w-full rounded-md border border-line bg-surface text-sm text-ink focus-visible:outline-2 focus-visible:outline-accent";
// Money reads as $50 M: a "$" before the number, the scale after it.
const UNITS: Record<string, { before?: string; after?: string }> = {
  "$M": { before: "$", after: "M" },
  "$K": { before: "$", after: "K" },
  $: { before: "$" },
  "%": { after: "%" },
  sessions: { after: "days" },
};

function Row({ label, htmlFor, children }: { label: string; htmlFor?: string; children: ReactNode }) {
  return (
    <div className="grid min-h-10 grid-cols-[minmax(0,1fr)_156px] items-center gap-3">
      {htmlFor ? (
        <label htmlFor={htmlFor} className="truncate text-[13px] text-ink-2">
          {label}
        </label>
      ) : (
        <span className="truncate text-[13px] text-ink-2">{label}</span>
      )}
      {children}
    </div>
  );
}

function Group({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section aria-label={title} className="border-t border-line-soft px-4 pt-3 pb-2 first:border-t-0">
      <h3 className="m-0 mb-1 text-[13px] font-semibold text-ink">{title}</h3>
      {children}
    </section>
  );
}

/** Two choices filling the control width. */
function Pair<T extends string>({ label, value, options, onChange }: { label: string; value: T; options: [T, string][]; onChange: (value: T) => void }) {
  return (
    <div role="group" aria-label={label} className="grid h-8 grid-cols-2 gap-0.5 rounded-md border border-line bg-surface p-0.5">
      {options.map(([key, text]) => (
        <button
          key={key}
          type="button"
          aria-pressed={key === value}
          onClick={() => onChange(key)}
          className={`cursor-pointer rounded text-[13px] font-medium focus-visible:outline-2 focus-visible:outline-accent ${key === value ? "bg-raised text-ink" : "text-ink-3 hover:text-ink"}`}
        >
          {text}
        </button>
      ))}
    </div>
  );
}

function NumberRow({ spec, base, draft, onChange }: { spec: NumberSpec; base: LabSettings; draft: Draft; onChange: (draft: Draft) => void }) {
  const id = `lab-${spec.path.replace(".", "-")}`;
  const value = draft.numbers[spec.path] ?? "";
  const placeholder = shown(base, spec);
  // No unit beside "none" (no stop, no cap): there is no amount to qualify.
  const unit = spec.unit && (value.trim() || placeholder !== "none") ? UNITS[spec.unit] : {};
  const right = unit.after === "days" ? "pr-12" : unit.after ? "pr-7" : "pr-2.5";
  return (
    <Row label={spec.label} htmlFor={id}>
      <div className="relative">
        {unit.before && <span className="pointer-events-none absolute inset-y-0 left-2.5 flex items-center text-[13px] text-ink-3">{unit.before}</span>}
        <input
          id={id}
          inputMode="decimal"
          autoComplete="off"
          spellCheck={false}
          value={value}
          placeholder={placeholder}
          onChange={(event) => onChange({ ...draft, numbers: { ...draft.numbers, [spec.path]: event.target.value } })}
          className={`${control} pl-6 text-right tabular-nums placeholder:text-ink-3 ${right} ${value.trim() ? "font-semibold" : ""}`}
        />
        {unit.after && <span className="pointer-events-none absolute inset-y-0 right-2.5 flex items-center text-[13px] text-ink-3">{unit.after}</span>}
      </div>
    </Row>
  );
}

function Settings({ meta, base, draft, onChange }: Pick<InspectorProps, "meta" | "base" | "draft" | "onChange">) {
  const period = draft.period ?? base.period;
  const mode = draft.mode ?? base.entry.mode;
  const order = draft.rank_order ?? base.entry.rank_order;
  const exclude = draft.exclude_blank_checks ?? base.universe.exclude_blank_checks;
  const spec = (path: string) => NUMBERS.find((s) => s.path === path) as NumberSpec;
  const number = (path: string) => <NumberRow key={path} spec={spec(path)} base={base} draft={draft} onChange={onChange} />;
  const date = (key: "start" | "end", label: string) => (
    <Row label={label} htmlFor={`lab-${key}`}>
      <input
        id={`lab-${key}`}
        type="date"
        min="2005-01-01"
        max={meta.last_entry}
        value={draft[key] ?? ""}
        onChange={(event) => onChange({ ...draft, period: "custom", [key]: event.target.value })}
        className={`${control} px-2 tabular-nums`}
      />
    </Row>
  );
  return (
    <>
      <Group title="Period">
        <div className="py-1">
          <select
            aria-label="Period"
            value={period}
            onChange={(event) => onChange({ ...draft, period: event.target.value === base.period ? undefined : event.target.value })}
            className={`${control} px-2`}
          >
            {meta.periods.map((p) => (
              <option key={p.name} value={p.name}>
                {p.label}
              </option>
            ))}
            <option value="custom">Custom dates</option>
          </select>
        </div>
        {period === "custom" && (
          <>
            {date("start", "First signal")}
            {date("end", "Last entry")}
          </>
        )}
      </Group>
      <Group title="Universe">
        {number("universe.min_market_cap")}
        {number("universe.max_market_cap")}
        {number("universe.min_price")}
        {number("universe.min_dollar_volume")}
        <Row label="Blank checks">
          <Pair
            label="Blank checks"
            value={exclude ? "skip" : "keep"}
            options={[
              ["keep", "Keep"],
              ["skip", "Leave out"],
            ]}
            onChange={(value) => {
              const next = value === "skip";
              onChange({ ...draft, exclude_blank_checks: next === base.universe.exclude_blank_checks ? undefined : next });
            }}
          />
        </Row>
      </Group>
      <Group title="Entry">
        <Row label="Buy">
          <Pair
            label="Entry mode"
            value={mode}
            options={[
              ["signal", "Signals"],
              ["rank", "Top scores"],
            ]}
            onChange={(value) => onChange({ ...draft, mode: value === base.entry.mode ? undefined : value })}
          />
        </Row>
        {mode === "rank" && (
          <>
            {number("entry.top_n")}
            <Row label="Scores first">
              <Pair
                label="Which scores"
                value={order}
                options={[
                  ["highest", "Highest"],
                  ["lowest", "Lowest"],
                ]}
                onChange={(value) => onChange({ ...draft, rank_order: value === base.entry.rank_order ? undefined : value })}
              />
            </Row>
          </>
        )}
      </Group>
      <Group title="Exit">
        {number("exit.hold_days")}
        {number("exit.stop_loss")}
        {number("exit.take_profit")}
      </Group>
      <Group title="Book">
        {number("book.position_size")}
        {number("book.max_positions")}
      </Group>
    </>
  );
}

const STATIC = new Set(["sector", "industry", "exchange", "name"]);
const SERIES = new Set(["spy", "universe_return"]);
const FLAGS = new Set(["earnings", "filing", "eligible"]);
const EXAMPLES: Record<string, string> = {
  close: "data.close > data.close.rolling(50).max().shift(1)",
  open: "data.open / data.close.shift(1) - 1",
  high: "data.close >= data.high * 0.98",
  low: "(data.close - data.low) / (data.high - data.low)",
  adj_close: "data.adj_close.pct_change(20)",
  returns: "data.returns.rolling(5).sum()",
  volume: "data.volume / data.volume.rolling(20).mean().shift(1)",
  dollar_volume: "data.dollar_volume >= 2 * data.adv20",
  transactions: "data.transactions.rolling(20).mean()",
  trade_size: "data.trade_size / data.trade_size.rolling(60).median().shift(1)",
  market_cap: "(data.market_cap >= 50e6) & (data.market_cap < 300e6)",
  adv20: "data.adv20 >= 1e6",
  eligible: "data.close.where(data.eligible)",
  earnings: "data.earnings & (data.returns > 0.05)",
  filing: "data.filing.astype(int).rolling(5).sum() == 0",
  eps: "data.eps / data.eps.shift(252) - 1",
};

function example(f: Field): string {
  if (EXAMPLES[f.name]) return EXAMPLES[f.name];
  if (STATIC.has(f.name)) return `data.${f.name}["AAPL"]`;
  if (SERIES.has(f.name)) return `data.${f.name}.pct_change(20)`;
  if (FLAGS.has(f.name)) return `data.${f.name}.astype(int).rolling(5).sum() > 0`;
  return `data.${f.name} / data.${f.name}.shift(252) - 1`;
}

/** The fields, as a reference. Nothing here writes into the code: a field is copied, or typed
 *  in the editor, where data. offers every name. */
function Fields({ meta }: { meta: Meta }) {
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState<string | null>(null);
  const [copied, setCopied] = useState<string | null>(null);
  useEffect(() => {
    if (!copied) return;
    const timer = window.setTimeout(() => setCopied(null), 2500);
    return () => window.clearTimeout(timer);
  }, [copied]);
  const copy = (text: string) => {
    navigator.clipboard?.writeText(text).catch(() => undefined);
    setCopied(text);
  };
  const words = search.trim().toLowerCase();
  const rows = meta.fields.filter((f) => !words || f.name.includes(words) || f.description.toLowerCase().includes(words));
  return (
    <div className="flex flex-col">
      <div className="sticky top-0 z-[1] border-b border-line-soft bg-surface px-4 py-3">
        <input type="search" aria-label="Find a field" placeholder="Find a field" value={search} onChange={(e) => setSearch(e.target.value)} className={`${control} px-2.5 placeholder:text-ink-3`} />
        <p role="status" className="m-0 mt-2 min-h-[18px] text-[12px] text-ink-3">
          {copied ? `Copied ${copied}` : "Type data. in the code to pick a field."}
        </p>
      </div>
      <ul className="m-0 list-none p-0">
        {rows.map((f) => {
          const expanded = open === f.name;
          const sample = example(f);
          return (
            <li key={f.name} className="border-b border-line-soft">
              <button
                type="button"
                aria-expanded={expanded}
                onClick={() => setOpen(expanded ? null : f.name)}
                className="flex w-full cursor-pointer flex-col gap-0.5 px-4 py-2.5 text-left hover:bg-raised focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-accent"
              >
                <span className="flex items-baseline justify-between gap-3">
                  <code className="font-mono text-[13px] font-semibold text-ink">{f.name}</code>
                  <span className="shrink-0 text-[12px] text-ink-3">{f.known}</span>
                </span>
                <span className="text-[13px] leading-snug text-ink-2">{f.description}</span>
              </button>
              {expanded && (
                <div className="flex flex-col gap-2 px-4 pb-3">
                  <code className="block overflow-x-auto rounded-md bg-raised px-2.5 py-2 font-mono text-[12px] whitespace-pre text-ink">{sample}</code>
                  <div className="flex gap-2">
                    <button type="button" onClick={() => copy(`data.${f.name}`)} className="h-7 cursor-pointer rounded-md border border-line bg-surface px-2.5 text-[12px] font-medium text-ink hover:bg-raised focus-visible:outline-2 focus-visible:outline-accent">
                      Copy data.{f.name}
                    </button>
                    <button type="button" onClick={() => copy(sample)} className="h-7 cursor-pointer rounded-md border border-line bg-surface px-2.5 text-[12px] font-medium text-ink hover:bg-raised focus-visible:outline-2 focus-visible:outline-accent">
                      Copy the example
                    </button>
                  </div>
                </div>
              )}
            </li>
          );
        })}
        {!rows.length && <li className="px-4 py-6 text-[13px] text-ink-2">No field matches.</li>}
      </ul>
    </div>
  );
}

/** The panel beside the editor: the run's settings, and the data the code can use. */
export function Inspector({ meta, base, draft, onChange, name, historyKey, onRestore }: InspectorProps) {
  const [tab, setTab] = useState<"settings" | "data" | "history">("settings");
  return (
    <div className="flex h-full min-h-0 flex-col">
      <div role="tablist" aria-label="Beside the editor" className="flex h-11 shrink-0 items-end gap-5 border-b border-line px-4">
        {(
          [
            ["settings", "Settings"],
            ["data", "Data"],
            ["history", "History"],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            type="button"
            role="tab"
            aria-selected={tab === key}
            onClick={() => setTab(key)}
            className={`-mb-px cursor-pointer border-b-2 pb-2.5 text-[13px] font-semibold focus-visible:outline-2 focus-visible:outline-accent ${tab === key ? "border-ink text-ink" : "border-transparent text-ink-3 hover:text-ink"}`}
          >
            {label}
          </button>
        ))}
        <div className="flex-1" />
        {tab === "settings" && changed(draft) && (
          <button type="button" onClick={() => onChange({ numbers: {} })} className="cursor-pointer pb-2.5 text-[13px] font-medium text-accent hover:underline focus-visible:outline-2 focus-visible:outline-accent">
            Reset
          </button>
        )}
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto">
        {tab === "settings" ? (
          <Settings meta={meta} base={base} draft={draft} onChange={onChange} />
        ) : tab === "data" ? (
          <Fields meta={meta} />
        ) : (
          <History kind="algorithms" name={name} refresh={historyKey} onRestore={onRestore} />
        )}
      </div>
    </div>
  );
}
