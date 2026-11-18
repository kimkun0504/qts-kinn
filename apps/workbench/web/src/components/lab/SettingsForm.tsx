import type { LabSettings, Meta } from "../../lib/lab";
import { changed, type Draft, NUMBERS, type NumberSpec, shown } from "../../lib/labSettings";
import { Segmented } from "../ui/Segmented";

interface SettingsFormProps {
  meta: Meta;
  /** The Lab's defaults with the algorithm's SETTINGS over them. */
  base: LabSettings;
  draft: Draft;
  onChange: (draft: Draft) => void;
  onReset: () => void;
}

const input =
  "min-h-8 w-full min-w-0 rounded-md border border-line bg-surface px-2.5 text-sm text-ink placeholder:text-ink-3 focus-visible:outline-2 focus-visible:outline-accent";

function NumberField({ spec, base, draft, onChange }: { spec: NumberSpec; base: LabSettings; draft: Draft; onChange: (draft: Draft) => void }) {
  const id = `lab-${spec.path.replace(".", "-")}`;
  const value = draft.numbers[spec.path] ?? "";
  return (
    <label htmlFor={id} className="flex min-w-0 flex-col gap-1">
      <span className="text-[13px] text-ink-2">
        {spec.label}
        {spec.unit && <span className="text-ink-3"> ({spec.unit})</span>}
      </span>
      <input
        id={id}
        inputMode="decimal"
        autoComplete="off"
        value={value}
        placeholder={shown(base, spec)}
        onChange={(event) => onChange({ ...draft, numbers: { ...draft.numbers, [spec.path]: event.target.value } })}
        className={`${input} ${value.trim() ? "border-accent" : ""}`}
      />
    </label>
  );
}

function Group({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <fieldset className="m-0 flex min-w-0 flex-col gap-3 border-0 p-0">
      <legend className="mb-2 p-0 text-[13px] font-semibold text-ink">{title}</legend>
      {children}
    </fieldset>
  );
}

/** The run's settings. A blank box keeps the value in the algorithm's SETTINGS (or the Lab's
 *  default), shown greyed; a typed value overrides it for this run. */
export function SettingsForm({ meta, base, draft, onChange, onReset }: SettingsFormProps) {
  const period = draft.period ?? base.period;
  const mode = draft.mode ?? base.entry.mode;
  const order = draft.rank_order ?? base.entry.rank_order;
  const exclude = draft.exclude_blank_checks ?? base.universe.exclude_blank_checks;
  const numbers = (section: string) => NUMBERS.filter((spec) => spec.path.startsWith(section));
  const field = (spec: NumberSpec) => <NumberField key={spec.path} spec={spec} base={base} draft={draft} onChange={onChange} />;
  const custom = period === "custom";
  const periodLabel = meta.periods.find((p) => p.name === period);
  return (
    <div className="@container flex flex-col gap-5 p-4">
      <div className="flex flex-wrap items-center gap-3">
        <Segmented
          label="Period"
          value={period}
          onChange={(value) => onChange({ ...draft, period: value === base.period ? undefined : value })}
          options={[...meta.periods.map((p) => ({ value: p.name, label: p.name === "all" ? "All years" : p.label.split(" (")[0] })), { value: "custom", label: "Custom" }]}
        />
        {custom ? (
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <input type="date" aria-label="First signal day" min="2005-01-01" max={meta.last_entry} value={draft.start ?? ""} onChange={(e) => onChange({ ...draft, period: "custom", start: e.target.value })} className={`${input} w-auto`} />
            <span className="text-ink-3">to</span>
            <input type="date" aria-label="Last entry day" min="2005-01-01" max={meta.last_entry} value={draft.end ?? ""} onChange={(e) => onChange({ ...draft, period: "custom", end: e.target.value })} className={`${input} w-auto`} />
          </div>
        ) : (
          periodLabel && <span className="text-[13px] text-ink-3">{periodLabel.label}</span>
        )}
        <div className="flex-1" />
        {changed(draft) && (
          <button type="button" onClick={onReset} className="cursor-pointer text-[13px] font-medium text-accent hover:underline focus-visible:outline-2 focus-visible:outline-accent">
            Clear changes
          </button>
        )}
      </div>
      <div className="grid grid-cols-1 gap-6 @lg:grid-cols-2 @3xl:grid-cols-4">
        <Group title="Universe">
          {numbers("universe").map(field)}
          <label className="flex items-center gap-2 text-sm text-ink-2">
            <input type="checkbox" checked={exclude} onChange={(e) => onChange({ ...draft, exclude_blank_checks: e.target.checked === base.universe.exclude_blank_checks ? undefined : e.target.checked })} className="size-4 accent-[var(--accent)]" />
            Leave out blank checks (SPACs)
          </label>
        </Group>
        <Group title="Entry">
          <Segmented
            label="Entry mode"
            value={mode}
            onChange={(value) => onChange({ ...draft, mode: value === base.entry.mode ? undefined : value })}
            options={[
              { value: "signal", label: "Every signal" },
              { value: "rank", label: "Top scores" },
            ]}
          />
          {mode === "rank" && (
            <>
              {field(NUMBERS.find((s) => s.path === "entry.top_n") as NumberSpec)}
              <Segmented
                label="Which scores"
                value={order}
                onChange={(value) => onChange({ ...draft, rank_order: value === base.entry.rank_order ? undefined : value })}
                options={[
                  { value: "highest", label: "Highest" },
                  { value: "lowest", label: "Lowest" },
                ]}
              />
            </>
          )}
        </Group>
        <Group title="Exit">{numbers("exit").map(field)}</Group>
        <Group title="Book">{numbers("book").map(field)}</Group>
      </div>
    </div>
  );
}
