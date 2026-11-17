import { useEffect, useState } from "react";

export type Page = "home" | "strategies" | "strategy" | "studies" | "runs" | "paper" | "compare" | "parameters" | "trials";
export interface Route {
  page: Page;
  /** The strategy on a strategy page. */
  name?: string;
  /** The tab on a strategy page. */
  tab?: string;
}

const PAGES: Page[] = ["home", "strategies", "strategy", "studies", "runs", "paper", "compare", "parameters", "trials"];

export function parse(hash: string): Route {
  const [page, name, tab] = hash.replace(/^#\/?/, "").split("/").map(decodeURIComponent);
  if (!PAGES.includes(page as Page)) return { page: "home" };
  if (page === "strategy") return name ? { page: "strategy", name, tab: tab || "results" } : { page: "strategies" };
  return { page: page as Page };
}

export function href(route: Route): string {
  return `#/${[route.page, route.name, route.tab].filter(Boolean).map((part) => encodeURIComponent(part as string)).join("/")}`;
}

/** The page in the address bar's hash, so a reload or a shared link lands in the same place. */
export function useRoute(): [Route, (route: Route) => void] {
  const [route, setRoute] = useState<Route>(() => parse(window.location.hash));
  useEffect(() => {
    const onChange = () => setRoute(parse(window.location.hash));
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  const go = (next: Route) => {
    window.location.hash = href(next);
    window.scrollTo(0, 0);
  };
  return [route, go];
}
