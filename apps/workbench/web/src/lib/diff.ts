export interface DiffLine {
  kind: "same" | "added" | "removed";
  text: string;
  left: number | null;
  right: number | null;
}

export function diffLines(before: string, after: string): DiffLine[] {
  const a = before.split("\n");
  const b = after.split("\n");
  const n = a.length;
  const m = b.length;
  const lcs: number[][] = Array.from({ length: n + 1 }, () => new Array<number>(m + 1).fill(0));
  for (let i = n - 1; i >= 0; i -= 1) {
    for (let j = m - 1; j >= 0; j -= 1) {
      lcs[i][j] = a[i] === b[j] ? lcs[i + 1][j + 1] + 1 : Math.max(lcs[i + 1][j], lcs[i][j + 1]);
    }
  }
  const out: DiffLine[] = [];
  let i = 0;
  let j = 0;
  while (i < n && j < m) {
    if (a[i] === b[j]) {
      out.push({ kind: "same", text: a[i], left: i + 1, right: j + 1 });
      i += 1;
      j += 1;
    } else if (lcs[i + 1][j] >= lcs[i][j + 1]) {
      out.push({ kind: "removed", text: a[i], left: i + 1, right: null });
      i += 1;
    } else {
      out.push({ kind: "added", text: b[j], left: null, right: j + 1 });
      j += 1;
    }
  }
  while (i < n) out.push({ kind: "removed", text: a[i], left: i + 1, right: null }), (i += 1);
  while (j < m) out.push({ kind: "added", text: b[j], left: null, right: j + 1 }), (j += 1);
  return out;
}

export function hunks(lines: DiffLine[], context = 3): (DiffLine | null)[] {
  const keep = new Array<boolean>(lines.length).fill(false);
  lines.forEach((line, k) => {
    if (line.kind === "same") return;
    for (let x = Math.max(0, k - context); x <= Math.min(lines.length - 1, k + context); x += 1) keep[x] = true;
  });
  const out: (DiffLine | null)[] = [];
  lines.forEach((line, k) => {
    if (keep[k]) out.push(line);
    else if (out.length && out[out.length - 1] !== null) out.push(null);
  });
  if (out.length && out[out.length - 1] === null) out.pop();
  return out;
}

export function flatten(value: unknown, prefix = ""): Record<string, string> {
  if (value === null || typeof value !== "object" || Array.isArray(value)) return { [prefix]: JSON.stringify(value ?? null) };
  return Object.entries(value as Record<string, unknown>).reduce<Record<string, string>>((all, [key, inner]) => ({ ...all, ...flatten(inner, prefix ? `${prefix}.${key}` : key) }), {});
}
