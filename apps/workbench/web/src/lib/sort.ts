import { useState } from "react";
import type { Sort } from "../components/ui/DataTable";

export type SortValue = string | number | boolean | null | undefined;

export function sortRows<Row>(rows: Row[], sort: Sort, value: (row: Row, key: string) => SortValue): Row[] {
  const sign = sort.dir === "asc" ? 1 : -1;
  return [...rows].sort((a, b) => {
    const x = value(a, sort.key);
    const y = value(b, sort.key);
    if (x == null && y == null) return 0;
    if (x == null) return 1;
    if (y == null) return -1;
    if (typeof x === "number" && typeof y === "number") return sign * (x - y);
    return sign * String(x).localeCompare(String(y));
  });
}

export function useSort(initial: Sort): [Sort, (key: string) => void] {
  const [sort, setSort] = useState<Sort>(initial);
  const onSort = (key: string) => setSort((current) => ({ key, dir: current.key === key && current.dir === "desc" ? "asc" : "desc" }));
  return [sort, onSort];
}
