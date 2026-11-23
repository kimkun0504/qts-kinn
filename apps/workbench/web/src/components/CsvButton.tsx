import { type CsvColumn, download, toCsv } from "../lib/csv";
import { Button } from "./ui/Button";

export function CsvButton<Row>({ filename, rows, columns, label = "CSV" }: { filename: string; rows: Row[]; columns: CsvColumn<Row>[]; label?: string }) {
  return (
    <Button onClick={() => download(filename, toCsv(rows, columns))} disabled={!rows.length} title={`Download ${rows.length} rows as ${filename}`}>
      {label}
    </Button>
  );
}
