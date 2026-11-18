import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CodeEditor, type CodeEditorHandle } from "../components/CodeEditor";
import { RunResults } from "../components/lab/RunResults";
import { SettingsForm } from "../components/lab/SettingsForm";
import { Badge, type Tone } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { type Column, DataTable } from "../components/ui/DataTable";
import { EmptyState } from "../components/ui/EmptyState";
import { Panel } from "../components/ui/Panel";
import { int, shortTime } from "../lib/format";
import {
  type AlgorithmFile,
  type AlgorithmRow,
  cleanName,
  lab,
  LabError,
  type Meta,
  NAME,
  type RunDetail,
  type RunListRow,
  type RunState,
  type Status,
  type Template,
} from "../lib/lab";
import { base as baseSettings, changed, type Draft, EMPTY_DRAFT, fromSettings, toPatch } from "../lib/labSettings";

interface LabProps {
  name?: string;
  runId?: string;
  onOpen: (name?: string, runId?: string) => void;
}

const BLANK = `"""My idea in one line."""

SETTINGS = {"exit": {"hold_days": 20}}


def signal(data):
    # A table of True/False by date and stock: True buys the stock at the next open.
    return data.returns > 0.05
`;

const STATE_TONE: Record<RunState, Tone> = {
  queued: "info",
  running: "info",
  complete: "ok",
  failed: "bad",
  cancelled: "muted",
  interrupted: "warn",
};
const STATE_LABEL: Record<RunState, string> = {
  queued: "Starting",
  running: "Running",
  complete: "Done",
  failed: "Failed",
  cancelled: "Cancelled",
  interrupted: "Stopped",
};
const LIVE: RunState[] = ["queued", "running"];

const input = "min-h-8 rounded-md border border-line bg-surface px-2.5 text-sm text-ink placeholder:text-ink-3 focus-visible:outline-2 focus-visible:outline-accent";

function loadDraft(name: string): Draft {
  try {
    const saved = localStorage.getItem(`kinn-lab-draft:${name}`);
    return saved ? { ...EMPTY_DRAFT, ...JSON.parse(saved) } : EMPTY_DRAFT;
  } catch {
    return EMPTY_DRAFT;
  }
}

function keepDraft(name: string, draft: Draft) {
  try {
    if (changed(draft)) localStorage.setItem(`kinn-lab-draft:${name}`, JSON.stringify(draft));
    else localStorage.removeItem(`kinn-lab-draft:${name}`);
  } catch {
    /* storage unavailable: the draft lasts for this visit */
  }
}

function NewAlgorithm({ templates, taken, onCreate, onCancel }: { templates: Template[]; taken: string[]; onCreate: (name: string, code: string) => void; onCancel: () => void }) {
  const [text, setText] = useState("");
  const [from, setFrom] = useState("");
  const name = cleanName(text);
  const problem = !name ? null : !NAME.test(name) ? "Use letters, digits, - and _." : taken.includes(name) ? "That name is taken." : null;
  return (
    <form
      className="flex flex-col gap-2 rounded-lg border border-line bg-surface p-3"
      onSubmit={(event) => {
        event.preventDefault();
        if (name && !problem) onCreate(name, templates.find((t) => t.name === from)?.code ?? BLANK);
      }}
    >
      <label className="flex flex-col gap-1 text-[13px] text-ink-2">
        Name
        <input autoFocus value={text} onChange={(e) => setText(e.target.value)} placeholder="my_idea" className={input} />
      </label>
      <label className="flex flex-col gap-1 text-[13px] text-ink-2">
        Start from
        <select value={from} onChange={(e) => setFrom(e.target.value)} className={input}>
          <option value="">A blank algorithm</option>
          {templates.map((t) => (
            <option key={t.name} value={t.name}>
              {t.name}: {t.description}
            </option>
          ))}
        </select>
      </label>
      {problem && <span className="text-[13px] text-neg">{problem}</span>}
      {name && !problem && name !== text && <span className="text-[13px] text-ink-3">Saved as {name}</span>}
      <div className="flex gap-2">
        <Button type="submit" variant="primary" disabled={!name || Boolean(problem)}>
          Create
        </Button>
        <Button onClick={onCancel}>Cancel</Button>
      </div>
    </form>
  );
}

function Progress({ status, onCancel }: { status: Status; onCancel: () => void }) {
  const share = Math.round(100 * (status.progress ?? 0));
  return (
    <Panel padded>
      <div className="flex flex-wrap items-center gap-4" aria-live="polite">
        <Badge tone="info">{STATE_LABEL[status.state]}</Badge>
        <span className="text-sm">{status.stage ?? "Waiting"}</span>
        <div className="h-1.5 min-w-[160px] flex-1 overflow-hidden rounded-full bg-raised" role="progressbar" aria-valuenow={share} aria-valuemin={0} aria-valuemax={100} aria-label="Run progress">
          <div className="h-full rounded-full bg-accent transition-[width] duration-500" style={{ width: `${Math.max(share, 2)}%` }} />
        </div>
        <span className="w-10 text-right text-[13px] text-ink-2">{share}%</span>
        <Button onClick={onCancel}>Cancel</Button>
      </div>
    </Panel>
  );
}

function Failure({ detail }: { detail: RunDetail }) {
  const [log, setLog] = useState<string | null>(null);
  const status = detail.status;
  const ours = (status.error ?? "").startsWith("The Lab failed");
  return (
    <Panel padded>
      <div role="alert" className="flex flex-col gap-2">
        <Badge tone={STATE_TONE[status.state]}>{STATE_LABEL[status.state]}</Badge>
        {status.error && <pre className="m-0 max-h-[360px] overflow-auto rounded-md bg-raised p-3 text-[13px] leading-relaxed whitespace-pre-wrap">{status.error}</pre>}
        {status.signals_computed && <span className="text-[13px] text-ink-3">It got as far as the signals, so it counts as trial #{status.trial_number}.</span>}
        {ours && log == null && (
          <button type="button" onClick={() => lab.log(detail.run_id).then((found) => setLog(found.log))} className="cursor-pointer self-start text-[13px] font-medium text-accent hover:underline">
            Show the worker's log
          </button>
        )}
        {log != null && <pre className="m-0 max-h-[360px] overflow-auto rounded-md bg-raised p-3 text-[13px] whitespace-pre-wrap">{log || "The log is empty."}</pre>}
      </div>
    </Panel>
  );
}

/** The line of an error that says what went wrong (a traceback ends with it). */
function lastLine(text: string): string {
  const lines = text.split("\n").map((line) => line.trim()).filter(Boolean);
  return lines[lines.length - 1] ?? text;
}

const historyColumns: Column<RunListRow & { number: number | null }>[] = [
  { key: "trial", header: "Trial", align: "left", render: (r) => (r.number ? `#${r.number}` : "–") },
  { key: "created", header: "Started", align: "left", muted: true, render: (r) => shortTime(r.created_at) },
  { key: "period", header: "Period", align: "left", muted: true, render: (r) => r.period ?? "–" },
  { key: "state", header: "State", align: "left", render: (r) => <Badge tone={STATE_TONE[r.state]}>{STATE_LABEL[r.state]}</Badge> },
  { key: "headline", header: "Result", align: "left", max: 420, render: (r) => r.headline ?? (r.error ? lastLine(r.error) : (r.stage ?? "–")) },
];

function FieldReference({ meta, onInsert }: { meta: Meta; onInsert: (text: string) => void }) {
  const [search, setSearch] = useState("");
  const words = search.trim().toLowerCase();
  const rows = meta.fields.filter((f) => !words || f.name.includes(words) || f.description.toLowerCase().includes(words));
  return (
    <div className="flex flex-col">
      <div className="flex flex-wrap items-center gap-3 border-b border-line px-4 py-3">
        <input type="search" aria-label="Find a field" placeholder="Find a field" value={search} onChange={(e) => setSearch(e.target.value)} className={`${input} w-56`} />
        <span className="text-[13px] text-ink-3">Click a name to put it in the code. Tables are dates × stocks unless marked.</span>
      </div>
      <DataTable
        columns={[
          { key: "name", header: "data.", align: "left", render: (f) => <code className="font-semibold text-accent">{f.name}</code> },
          { key: "description", header: "What it is", align: "left", render: (f) => <span className="whitespace-normal">{f.description}</span> },
          { key: "known", header: "Known", align: "left", muted: true, render: (f) => f.known },
        ]}
        rows={rows}
        rowKey={(f) => f.name}
        onRowClick={(f) => onInsert(`data.${f.name}`)}
      />
    </div>
  );
}

/** The Lab: write an algorithm, run it over every stock, and see what it made where. */
export function Lab({ name, runId, onOpen }: LabProps) {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [algorithms, setAlgorithms] = useState<AlgorithmRow[] | null>(null);
  const [file, setFile] = useState<AlgorithmFile | null>(null);
  const [code, setCode] = useState("");
  const [saved, setSaved] = useState("");
  const [draft, setDraft] = useState<Draft>(EMPTY_DRAFT);
  const [runs, setRuns] = useState<RunListRow[]>([]);
  const [detail, setDetail] = useState<RunDetail | null>(null);
  const [status, setStatus] = useState<Status | null>(null);
  const [message, setMessage] = useState<{ tone: "bad" | "ok"; text: string } | null>(null);
  const [creating, setCreating] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [panel, setPanel] = useState<"settings" | "fields" | null>("settings");
  const [busy, setBusy] = useState(false);
  const editor = useRef<CodeEditorHandle>(null);
  const dirty = file != null && code !== saved;

  const refreshList = useCallback(() => lab.algorithms().then(setAlgorithms), []);
  const refreshRuns = useCallback((which: string) => lab.runs(which).then(setRuns), []);

  useEffect(() => {
    Promise.all([lab.meta(), lab.templates(), lab.algorithms()])
      .then(([m, t, a]) => {
        setMeta(m);
        setTemplates(t);
        setAlgorithms(a);
      })
      .catch((e: Error) => setMessage({ tone: "bad", text: `The Lab could not be read: ${e.message} Restart the Workbench server after updating.` }));
  }, []);

  // Open the most recently changed algorithm when none is named.
  useEffect(() => {
    if (!name && algorithms?.length) {
      const latest = [...algorithms].sort((a, b) => b.updated.localeCompare(a.updated))[0];
      onOpen(latest.name, undefined);
    }
  }, [name, algorithms, onOpen]);

  // What is in the editor now, for the moments the page moves on without a click on Save.
  const pending = useRef({ name: file?.name, code, dirty });
  pending.current = { name: file?.name, code, dirty };

  // Load the named algorithm, its draft settings and its runs. Unsaved code of the one before
  // (left with the back button, say) is saved first.
  useEffect(() => {
    if (!name) return;
    const before = pending.current;
    if (before.name && before.name !== name && before.dirty) lab.save(before.name, before.code).catch(() => undefined);
    let live = true;
    setFile(null);
    setConfirmDelete(false);
    lab
      .algorithm(name)
      .then((found) => {
        if (!live) return;
        setFile(found);
        setCode(found.code);
        setSaved(found.code);
        setDraft(loadDraft(name));
      })
      .catch((e: Error) => {
        if (!live) return;
        setMessage({ tone: "bad", text: e.message });
        if (e instanceof LabError && e.status === 404) onOpen(undefined, undefined);
      });
    refreshRuns(name).catch(() => undefined);
    return () => {
      live = false;
    };
  }, [name, refreshRuns, onOpen]);

  // The run on screen: the one in the address, else the latest of this algorithm.
  const shownRun = runId ?? runs[0]?.run_id;
  useEffect(() => {
    if (!shownRun) {
      setDetail(null);
      setStatus(null);
      return;
    }
    let live = true;
    let timer: number | undefined;
    const poll = () =>
      lab
        .run(shownRun)
        .then((found) => {
          if (!live) return;
          setDetail(found);
          setStatus(found.status);
          if (LIVE.includes(found.status.state)) timer = window.setTimeout(tick, 1000);
        })
        .catch(() => live && setDetail(null));
    const tick = () =>
      lab
        .status(shownRun)
        .then((found) => {
          if (!live) return;
          setStatus(found);
          if (LIVE.includes(found.state)) timer = window.setTimeout(tick, 1000);
          else {
            poll();
            if (name) refreshRuns(name);
            refreshList();
          }
        })
        .catch(() => live && (timer = window.setTimeout(tick, 3000)));
    poll();
    return () => {
      live = false;
      window.clearTimeout(timer);
    };
  }, [shownRun, name, refreshRuns, refreshList]);

  useEffect(() => {
    if (name) keepDraft(name, draft);
  }, [name, draft]);

  // Leaving the Lab for another page keeps the work: unsaved code is saved on the way out.
  useEffect(
    () => () => {
      const { name: last, code: text, dirty: unsaved } = pending.current;
      if (last && unsaved) lab.save(last, text).catch(() => undefined);
    },
    [],
  );

  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => {
      if (dirty) event.preventDefault();
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  const save = useCallback(async () => {
    if (!name || !dirty) return true;
    try {
      await lab.save(name, code);
      setSaved(code);
      refreshList();
      return true;
    } catch (e) {
      setMessage({ tone: "bad", text: (e as Error).message });
      return false;
    }
  }, [name, code, dirty, refreshList]);

  const open = async (next: string) => {
    if (next === name) return;
    if (dirty) await save(); // switching keeps the work: it is saved, never dropped
    setMessage(null);
    onOpen(next, undefined);
  };

  const create = async (newName: string, newCode: string) => {
    try {
      if (dirty) await save();
      await lab.save(newName, newCode);
      setCreating(false);
      await refreshList();
      onOpen(newName, undefined);
    } catch (e) {
      setMessage({ tone: "bad", text: (e as Error).message });
    }
  };

  const remove = async () => {
    if (!name) return;
    try {
      await lab.remove(name);
      setConfirmDelete(false);
      const rest = (await lab.algorithms()).filter((a) => a.name !== name);
      setAlgorithms(rest);
      setFile(null);
      onOpen(rest[0]?.name, undefined);
    } catch (e) {
      setMessage({ tone: "bad", text: (e as Error).message });
    }
  };

  const run = useCallback(async () => {
    if (!name || !meta || busy) return;
    const { patch, errors } = toPatch(draft);
    if (errors.length) {
      setPanel("settings");
      setMessage({ tone: "bad", text: errors.join(" ") });
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      const started = await lab.start(name, code, patch);
      setSaved(code);
      setStatus(started.status);
      await refreshRuns(name);
      onOpen(name, started.run_id);
    } catch (e) {
      setMessage({ tone: "bad", text: (e as Error).message });
    } finally {
      setBusy(false);
    }
  }, [name, meta, busy, draft, code, refreshRuns, onOpen]);

  const cancel = async () => {
    if (!shownRun) return;
    try {
      setStatus(await lab.cancel(shownRun));
    } catch (e) {
      setMessage({ tone: "bad", text: (e as Error).message });
    }
  };

  const base = useMemo(() => (meta ? baseSettings(meta.defaults, file?.settings_in_code ?? null) : null), [meta, file]);
  const trials = useMemo(() => {
    const numbered = new Map<string, number>();
    [...runs].reverse().filter((r) => r.trial).forEach((r, i) => numbered.set(r.run_id, i + 1));
    return runs.map((r) => ({ ...r, number: numbered.get(r.run_id) ?? null }));
  }, [runs]);

  if (!meta || !algorithms) {
    return message ? <EmptyState title="The Lab is not available">{message.text}</EmptyState> : <p className="text-ink-2">Loading the Lab…</p>;
  }

  const running = status != null && LIVE.includes(status.state);
  const current = algorithms.find((a) => a.name === name);

  return (
    <div className="grid items-start gap-5 lg:grid-cols-[232px_minmax(0,1fr)]">
      <nav aria-label="Algorithms" className="flex flex-col gap-3 lg:sticky lg:top-5">
        <div className="flex items-center justify-between">
          <h2 className="m-0 text-sm font-semibold">Algorithms</h2>
          {!creating && <Button onClick={() => setCreating(true)}>New</Button>}
        </div>
        {creating && <NewAlgorithm templates={templates} taken={algorithms.map((a) => a.name)} onCreate={create} onCancel={() => setCreating(false)} />}
        <ul className="m-0 flex list-none flex-col gap-0.5 p-0">
          {algorithms.map((a) => (
            <li key={a.name}>
              <button
                type="button"
                aria-current={a.name === name ? "true" : undefined}
                onClick={() => open(a.name)}
                className={`flex w-full cursor-pointer flex-col items-start rounded-lg px-3 py-2 text-left focus-visible:outline-2 focus-visible:outline-accent ${
                  a.name === name ? "bg-surface shadow-[inset_2px_0_0_var(--accent)]" : "hover:bg-surface"
                }`}
              >
                <span className="flex w-full items-baseline justify-between gap-2">
                  <span className="truncate font-medium">{a.name}</span>
                  <span className="shrink-0 text-[13px] text-ink-3" title="Trials: runs that computed signals">
                    {a.trials ? `${a.trials} ${a.trials === 1 ? "trial" : "trials"}` : ""}
                  </span>
                </span>
                {a.description && <span className="line-clamp-2 text-[13px] text-ink-3">{a.description}</span>}
              </button>
            </li>
          ))}
        </ul>
        <p className="m-0 text-[13px] break-all text-ink-3" title={meta.folder}>
          Saved in {meta.folder.split("/").filter(Boolean).slice(-2).join("/")}
        </p>
      </nav>

      <div className="flex min-w-0 flex-col gap-5">
        {message && (
          <div role={message.tone === "bad" ? "alert" : "status"} className={`flex items-start gap-3 rounded-lg border bg-surface px-4 py-3 text-sm ${message.tone === "bad" ? "border-neg" : "border-line"}`}>
            <span className="flex-1 whitespace-pre-wrap">{message.text}</span>
            <button type="button" aria-label="Dismiss" onClick={() => setMessage(null)} className="cursor-pointer text-ink-3 hover:text-ink">
              ×
            </button>
          </div>
        )}

        {!algorithms.length && !creating ? (
          <div className="flex flex-col gap-4">
            <EmptyState title="Write your first algorithm">Start from a blank file or from one of these, then press Run.</EmptyState>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {templates.map((t) => (
                <button key={t.name} type="button" onClick={() => create(t.name, t.code)} className="flex cursor-pointer flex-col gap-1 rounded-lg border border-line bg-surface p-4 text-left hover:border-accent focus-visible:outline-2 focus-visible:outline-accent">
                  <span className="font-semibold">{t.name}</span>
                  <span className="text-[13px] text-ink-2">{t.description}</span>
                </button>
              ))}
              <button type="button" onClick={() => create("my_idea", BLANK)} className="flex cursor-pointer flex-col gap-1 rounded-lg border border-dashed border-line p-4 text-left hover:border-accent focus-visible:outline-2 focus-visible:outline-accent">
                <span className="font-semibold">Blank</span>
                <span className="text-[13px] text-ink-2">A signal() that returns True to buy.</span>
              </button>
            </div>
          </div>
        ) : !file || !base ? (
          name && <p className="text-ink-2">Loading {name}…</p>
        ) : (
          <>
            <section aria-label="Editor" className="min-w-0 rounded-lg border border-line bg-surface">
              <header className="flex flex-wrap items-center gap-3 border-b border-line px-4 py-2.5">
                <h2 className="m-0 font-mono text-[15px] font-semibold">{file.name}.py</h2>
                <span className="text-[13px] text-ink-3">{dirty ? "Unsaved changes" : "Saved"}</span>
                <div className="flex-1" />
                {confirmDelete ? (
                  <span className="flex items-center gap-2 text-[13px]">
                    Delete {file.name}? It moves to the trash folder; its runs stay.
                    <Button onClick={remove} variant="danger">
                      Delete
                    </Button>
                    <Button onClick={() => setConfirmDelete(false)}>Keep</Button>
                  </span>
                ) : (
                  <Button onClick={() => setConfirmDelete(true)}>Delete</Button>
                )}
                <Button onClick={save} disabled={!dirty} title="Save (⌘S)">
                  Save
                </Button>
                <Button onClick={run} disabled={busy || running} title="Run over every stock (⌘↵)" variant="primary" className="min-w-[92px]">
                  {running ? "Running…" : "Run"}
                </Button>
              </header>
              <CodeEditor ref={editor} value={code} onChange={setCode} onSave={save} onRun={run} fields={meta.fields} label={`${file.name}.py`} />
              <div className="flex flex-wrap gap-6 border-t border-line px-4">
                {(
                  [
                    ["settings", "Settings"],
                    ["fields", `Data ${meta.fields.length} fields`],
                  ] as const
                ).map(([key, label]) => (
                  <button
                    key={key}
                    type="button"
                    aria-expanded={panel === key}
                    onClick={() => setPanel(panel === key ? null : key)}
                    className={`-mt-px cursor-pointer border-t-2 pt-2.5 pb-2.5 text-sm font-medium focus-visible:outline-2 focus-visible:outline-accent ${
                      panel === key ? "border-accent text-ink" : "border-transparent text-ink-2 hover:text-ink"
                    }`}
                  >
                    {label}
                    {key === "settings" && changed(draft) ? " (changed)" : ""}
                  </button>
                ))}
              </div>
              {panel === "settings" && (
                <div className="border-t border-line">
                  <SettingsForm meta={meta} base={base} draft={draft} onChange={setDraft} onReset={() => setDraft(EMPTY_DRAFT)} />
                </div>
              )}
              {panel === "fields" && (
                <div className="max-h-[420px] overflow-auto border-t border-line">
                  <FieldReference meta={meta} onInsert={(text) => editor.current?.insert(text)} />
                </div>
              )}
            </section>

            {status && running && <Progress status={status} onCancel={cancel} />}
            {detail && !running && detail.status.state !== "complete" && <Failure detail={detail} />}
            {detail && detail.status.state === "complete" && detail.summary && (
              <RunResults
                key={detail.run_id}
                detail={detail}
                onRestoreCode={(old) => setCode(old)}
                onUseSettings={() => detail.summary?.settings && setDraft(fromSettings(detail.summary.settings, base))}
              />
            )}

            <Panel title="Runs of this algorithm" aside={current ? `${int(current.trials)} ${current.trials === 1 ? "trial" : "trials"} so far: each run that computed signals counts` : undefined}>
              <DataTable columns={historyColumns} rows={trials} rowKey={(r) => r.run_id} selectedKey={shownRun} onRowClick={(r) => onOpen(name, r.run_id)} empty="No runs yet. Press Run." />
            </Panel>
          </>
        )}
      </div>
    </div>
  );
}
