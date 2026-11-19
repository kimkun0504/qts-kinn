import { useEffect, useId, useState } from "react";
import { lab } from "../../lib/lab";
import { int } from "../../lib/format";
import { Button } from "../ui/Button";

const MAX = 2_000;

export function RunNote({ runId, note, onSaved }: { runId: string; note: string; onSaved?: (note: string) => void }) {
  const [text, setText] = useState(note);
  const [draft, setDraft] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const field = useId();
  useEffect(() => setText(note), [note]);
  const save = () => {
    if (draft == null) return;
    setSaving(true);
    setError(null);
    lab
      .saveNote(runId, draft)
      .then((saved) => {
        setText(saved.note);
        setDraft(null);
        onSaved?.(saved.note);
      })
      .catch((failure: Error) => setError(failure.message))
      .finally(() => setSaving(false));
  };
  const link = "cursor-pointer text-[13px] font-medium focus-visible:outline-2 focus-visible:outline-accent";
  if (draft == null)
    return text ? (
      <div className="flex items-start gap-4 rounded-lg border border-line bg-surface px-4 py-3">
        <p className="m-0 max-w-[100ch] flex-1 text-sm whitespace-pre-wrap text-ink">{text}</p>
        <button type="button" onClick={() => setDraft(text)} className={`${link} shrink-0 text-ink-2 hover:text-ink`}>
          Edit the note
        </button>
      </div>
    ) : (
      <button type="button" onClick={() => setDraft("")} className={`${link} self-start text-accent hover:underline`}>
        Add a note to this run
      </button>
    );
  return (
    <form
      className="flex flex-col gap-2 rounded-lg border border-line bg-surface px-4 py-3"
      onSubmit={(event) => {
        event.preventDefault();
        save();
      }}
    >
      <label htmlFor={field} className="text-[13px] font-medium text-ink-2">
        Note on this run
      </label>
      <textarea
        id={field}
        autoFocus
        rows={3}
        maxLength={MAX}
        value={draft}
        placeholder="Why you tried it, and what you made of it"
        onChange={(event) => setDraft(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Escape") setDraft(null);
          if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
            event.preventDefault();
            save();
          }
        }}
        className="w-full resize-y rounded-md border border-line bg-surface px-3 py-2 text-sm text-ink placeholder:text-ink-3 focus:border-accent focus:outline-none"
      />
      {error && (
        <p role="alert" className="m-0 text-[13px] text-neg">
          {error}
        </p>
      )}
      <div className="flex items-center gap-2">
        <Button type="submit" variant="primary" disabled={saving}>
          {saving ? "Saving…" : "Save the note"}
        </Button>
        <Button onClick={() => setDraft(null)}>Cancel</Button>
        <span className="text-[12px] text-ink-3 tabular-nums">
          {int(draft.length)} of {int(MAX)}
        </span>
      </div>
    </form>
  );
}
