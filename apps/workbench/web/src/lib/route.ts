import { useCallback, useEffect, useState } from "react";

export type Page = "home" | "strategies" | "strategy" | "stock" | "screener" | "studies" | "lab" | "runs" | "paper" | "compare" | "parameters" | "trials" | "data" | "guide";
export interface Route {
  page: Page;
  /** The strategy on a strategy page; the algorithm in the Lab. */
  name?: string;
  /** The tab on a strategy page; the run in the Lab. */
  tab?: string;
}

const PAGES: Page[] = ["home", "strategies", "strategy", "stock", "screener", "studies", "lab", "runs", "paper", "compare", "parameters", "trials", "data", "guide"];

export function parse(hash: string): Route {
  const [page, name, tab] = hash.replace(/^#\/?/, "").split("/").map(decodeURIComponent);
  if (!PAGES.includes(page as Page)) return { page: "home" };
  if (page === "strategy") return name ? { page: "strategy", name, tab: tab || "results" } : { page: "strategies" };
  if (page === "lab") return { page: "lab", name: name || undefined, tab: tab || undefined };
  if (page === "paper") return { page: "paper", name: name || undefined };
  if (page === "runs") return { page: "runs", name: name || undefined };
  if (page === "compare") return { page: "compare", name: name || undefined };
  if (page === "guide") return { page: "guide", name: name || undefined };
  if (page === "screener") return { page: "screener", name: name && name !== "latest" ? name : undefined, tab: tab || undefined };
  if (page === "stock") return { page: "stock", name: name ? name.toUpperCase() : undefined, tab: tab || undefined };
  return { page: page as Page };
}

export function href(route: Route): string {
  return `#/${[route.page, route.name, route.tab].filter(Boolean).map((part) => encodeURIComponent(part as string)).join("/")}`;
}

/** The page in the address bar's hash, so a reload or a shared link lands in the same place. */
export function useRoute(): [Route, (route: Route, options?: { scroll?: boolean }) => void] {
  const [route, setRoute] = useState<Route>(() => parse(window.location.hash));
  useEffect(() => {
    const onChange = () => setRoute(parse(window.location.hash));
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  const go = useCallback((next: Route, options?: { scroll?: boolean }) => {
    window.location.hash = href(next);
    if (options?.scroll !== false) window.scrollTo(0, 0);
  }, []);
  return [route, go];
}
