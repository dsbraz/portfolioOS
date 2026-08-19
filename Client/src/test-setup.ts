/**
 * Global setup for the unit suite.
 *
 * jsdom ships a `matchMedia` without the legacy `addListener`/`removeListener`
 * pair. Angular CDK's `BreakpointObserver` — which every Material dialog and
 * table pulls in — still calls them, so a subscription that fires after the
 * test finished throws `mql.addListener is not a function` as an *uncaught*
 * exception: the tests all report green while the run exits non-zero.
 *
 * It surfaced only in CI, where the timing differs enough for the late
 * subscription to land after teardown. A full stub removes the timing
 * dependence instead of hiding it.
 */
const listenersLegados = new WeakMap<MediaQueryList, Set<(e: MediaQueryListEvent) => void>>();

function criarMediaQueryList(query: string): MediaQueryList {
  const ouvintes = new Set<(e: MediaQueryListEvent) => void>();

  const mql = {
    matches: false,
    media: query,
    onchange: null,
    // Legacy pair, the one the CDK reaches for.
    addListener: (ouvinte: (e: MediaQueryListEvent) => void) => void ouvintes.add(ouvinte),
    removeListener: (ouvinte: (e: MediaQueryListEvent) => void) =>
      void ouvintes.delete(ouvinte),
    // Modern pair, for anything that already migrated.
    addEventListener: (_tipo: string, ouvinte: EventListenerOrEventListenerObject) =>
      void ouvintes.add(ouvinte as (e: MediaQueryListEvent) => void),
    removeEventListener: (_tipo: string, ouvinte: EventListenerOrEventListenerObject) =>
      void ouvintes.delete(ouvinte as (e: MediaQueryListEvent) => void),
    dispatchEvent: () => false,
  } as unknown as MediaQueryList;

  listenersLegados.set(mql, ouvintes);
  return mql;
}

Object.defineProperty(window, 'matchMedia', {
  writable: true,
  configurable: true,
  value: (query: string) => criarMediaQueryList(query),
});
