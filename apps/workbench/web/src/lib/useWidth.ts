import { useCallback, useRef, useState } from "react";

export function useWidth<T extends HTMLElement>(): [(node: T | null) => void, number | null] {
  const [width, setWidth] = useState<number | null>(null);
  const observer = useRef<ResizeObserver | null>(null);
  const ref = useCallback((node: T | null) => {
    observer.current?.disconnect();
    observer.current = null;
    if (!node || typeof ResizeObserver === "undefined") return;
    observer.current = new ResizeObserver(([entry]) => {
      const measured = Math.round(entry.contentRect.width);
      if (measured > 0) setWidth(measured);
    });
    observer.current.observe(node);
  }, []);
  return [ref, width];
}

export function fitted(measured: number | null, reference: number, height: number): { width: number; height: number } {
  if (!measured) return { width: reference, height };
  const scale = Math.min(1.5, Math.max(0.75, measured / reference));
  return { width: measured, height: Math.round(height * scale) };
}
