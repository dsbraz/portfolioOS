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
 *
 * The listeners go nowhere on purpose: `matches` never changes, so there is
 * nothing to notify. A test that needs to drive a media-query change wants a
 * behavioural fake of its own — `theme.service.spec.ts` has one — not this
 * compatibility shim pretending it can dispatch.
 */
function criarMediaQueryList(query: string): MediaQueryList {
  return {
    matches: false,
    media: query,
    onchange: null,
    // Legacy pair, the one the CDK reaches for.
    addListener: () => undefined,
    removeListener: () => undefined,
    // Modern pair, for anything that already migrated.
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
    dispatchEvent: () => false,
  } as unknown as MediaQueryList;
}

Object.defineProperty(window, 'matchMedia', {
  writable: true,
  configurable: true,
  value: (query: string) => criarMediaQueryList(query),
});
