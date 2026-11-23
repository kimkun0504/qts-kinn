import type { ReactNode } from "react";

/** Inline marks: **bold**, `code` and [text](link). Links are shown as text unless they are
 *  web addresses, since the reports link to files in the repository. */
function inline(text: string, key: string): ReactNode[] {
  const out: ReactNode[] = [];
  const pattern = /(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g;
  let last = 0;
  let n = 0;
  for (const match of text.matchAll(pattern)) {
    if (match.index > last) out.push(text.slice(last, match.index));
    const token = match[0];
    const id = `${key}-${n++}`;
    if (token.startsWith("**")) out.push(<strong key={id}>{inline(token.slice(2, -2), id)}</strong>);
    else if (token.startsWith("`"))
      out.push(
        <code key={id} className="rounded bg-raised px-1 py-px text-[0.92em]">
          {token.slice(1, -1)}
        </code>,
      );
    else {
      const [, label, href] = /\[([^\]]+)\]\(([^)]+)\)/.exec(token) ?? [];
      out.push(
        /^https?:/.test(href) ? (
          <a key={id} href={href} target="_blank" rel="noreferrer" className="text-accent underline">
            {label}
          </a>
        ) : (
          <span key={id}>{inline(label, id)}</span>
        ),
      );
    }
    last = match.index + token.length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

export function slug(heading: string): string {
  return heading
    .toLowerCase()
    .replace(/[`*[\]()]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

export function sections(text: string): { title: string; anchor: string }[] {
  let fenced = false;
  const out: { title: string; anchor: string }[] = [];
  for (const line of text.replace(/\r/g, "").split("\n")) {
    if (line.startsWith("```")) fenced = !fenced;
    else if (!fenced && line.startsWith("## ")) out.push({ title: line.slice(3).replace(/[`*]/g, ""), anchor: slug(line.slice(3)) });
  }
  return out;
}

const cells = (line: string) =>
  line
    .trim()
    .replace(/^\||\|$/g, "")
    .split("|")
    .map((cell) => cell.trim());

/** The reports' markdown as a page: headings, paragraphs, lists, tables, code and quotes.
 *  A small renderer for our own documents, not a general one. */
export function Markdown({ text }: { text: string }) {
  const lines = text.replace(/\r/g, "").split("\n");
  const out: ReactNode[] = [];
  let i = 0;
  const key = () => `b${out.length}`;
  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) {
      i += 1;
    } else if (line.startsWith("```")) {
      const body: string[] = [];
      for (i += 1; i < lines.length && !lines[i].startsWith("```"); i += 1) body.push(lines[i]);
      i += 1;
      out.push(
        <pre key={key()} className="overflow-x-auto rounded-lg bg-raised px-4 py-3 text-[13px] leading-relaxed">
          <code>{body.join("\n")}</code>
        </pre>,
      );
    } else if (/^#{1,4} /.test(line)) {
      const level = line.indexOf(" ");
      const content = inline(line.slice(level + 1), key());
      const style = ["mt-2 text-2xl font-semibold tracking-tight", "mt-6 border-t border-line pt-5 text-xl font-semibold", "mt-3 text-base font-semibold", "mt-2 font-semibold text-ink-2"][level - 1];
      const anchor = slug(line.slice(level + 1));
      out.push(
        level === 1 ? (
          <h2 key={key()} className={`m-0 ${style}`}>
            {content}
          </h2>
        ) : level === 2 ? (
          <h3 key={key()} id={anchor} className={`m-0 scroll-mt-6 ${style}`}>
            {content}
          </h3>
        ) : (
          <h4 key={key()} className={`m-0 ${style}`}>
            {content}
          </h4>
        ),
      );
      i += 1;
    } else if (line.trim().startsWith("|") && i + 1 < lines.length && /^\s*\|?[\s:|-]+\|[\s:|-]*$/.test(lines[i + 1])) {
      const head = cells(line);
      const rows: string[][] = [];
      for (i += 2; i < lines.length && lines[i].trim().startsWith("|"); i += 1) rows.push(cells(lines[i]));
      const id = key();
      out.push(
        <div key={id} className="overflow-x-auto">
          <table className="border-collapse text-sm">
            <thead>
              <tr>
                {head.map((cell, c) => (
                  <th key={c} scope="col" className="border-b border-line px-3 py-2 text-left font-semibold text-ink-2">
                    {inline(cell, `${id}h${c}`)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, r) => (
                <tr key={r}>
                  {row.map((cell, c) => (
                    <td key={c} className="border-b border-line-soft px-3 py-2 align-top">
                      {inline(cell, `${id}r${r}c${c}`)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>,
      );
    } else if (/^\s*([-*]|\d+\.) /.test(line)) {
      const ordered = /^\s*\d+\. /.test(line);
      const items: string[] = [];
      while (i < lines.length && (/^\s*([-*]|\d+\.) /.test(lines[i]) || (/^\s{2,}\S/.test(lines[i]) && items.length))) {
        if (/^\s*([-*]|\d+\.) /.test(lines[i])) items.push(lines[i].replace(/^\s*([-*]|\d+\.) /, ""));
        else items[items.length - 1] += ` ${lines[i].trim()}`;
        i += 1;
      }
      const id = key();
      const body = items.map((item, n) => <li key={n}>{inline(item, `${id}i${n}`)}</li>);
      out.push(
        ordered ? (
          <ol key={id} className="m-0 flex list-decimal flex-col gap-1.5 pl-6">
            {body}
          </ol>
        ) : (
          <ul key={id} className="m-0 flex list-disc flex-col gap-1.5 pl-6">
            {body}
          </ul>
        ),
      );
    } else {
      const body: string[] = [];
      while (i < lines.length && lines[i].trim() && !/^(#{1,4} |```|\s*([-*]|\d+\.) )/.test(lines[i]) && !(lines[i].trim().startsWith("|") && body.length === 0)) {
        body.push(lines[i].replace(/^> ?/, "").trim());
        i += 1;
      }
      if (!body.length) {
        body.push(lines[i]);
        i += 1;
      }
      out.push(
        <p key={key()} className="m-0">
          {inline(body.join(" "), key())}
        </p>,
      );
    }
  }
  return <div className="flex max-w-[86ch] flex-col gap-3.5 leading-relaxed">{out}</div>;
}
