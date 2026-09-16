import { DOCUMENT, Injectable, computed, inject, signal } from '@angular/core';

/** What the user chose. `system` defers to the operating system. */
export type ThemePreference = 'system' | 'light' | 'dark';
/** The theme actually painted. */
export type ResolvedTheme = 'light' | 'dark';

/** Shared with the bootstrap script in `index.html`, which applies the theme
 *  before first paint. Change both together. */
export const THEME_STORAGE_KEY = 'portfolio-theme';

const SYSTEM_DARK_QUERY = '(prefers-color-scheme: dark)';

/**
 * Theme preference.
 *
 * Writes `[data-theme]` and `color-scheme` on the root element: the former drives
 * the BRQ token layer, the latter makes native controls (scrollbar, pickers)
 * follow along.
 *
 * The default is `system` and it is REACTIVE: a `matchMedia` listener repaints
 * when the operating system switches theme while the page is open. Without that
 * listener, the `data-theme` stamped at bootstrap disables the CSS
 * `@media (prefers-color-scheme: dark)` branch and the live switch never happens.
 */
@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly document = inject(DOCUMENT);

  private readonly preference = signal<ThemePreference>(this.readStored() ?? 'system');
  private readonly systemDark = signal(this.prefersDark());

  readonly theme = this.preference.asReadonly();
  readonly resolved = computed<ResolvedTheme>(() => {
    const pref = this.preference();
    if (pref !== 'system') return pref;
    return this.systemDark() ? 'dark' : 'light';
  });
  readonly isDark = computed(() => this.resolved() === 'dark');

  constructor() {
    this.watchSystem();
    this.apply(this.resolved());
  }

  /** Cycles system -> light -> dark -> system. */
  cycle(): void {
    const ordem: ThemePreference[] = ['system', 'light', 'dark'];
    const proximo = ordem[(ordem.indexOf(this.preference()) + 1) % ordem.length];
    this.set(proximo);
  }

  set(preference: ThemePreference): void {
    this.preference.set(preference);
    this.persist(preference);
    this.apply(this.resolved());
  }

  private watchSystem(): void {
    const mq = this.document.defaultView?.matchMedia?.(SYSTEM_DARK_QUERY);
    mq?.addEventListener?.('change', (event) => {
      this.systemDark.set(event.matches);
      // Only repaint when the choice is to defer to the system; an explicit choice
      // must not be overridden because the OS changed.
      if (this.preference() === 'system') this.apply(this.resolved());
    });
  }

  private readStored(): ThemePreference | null {
    try {
      const stored = this.document.defaultView?.localStorage.getItem(THEME_STORAGE_KEY);
      return stored === 'light' || stored === 'dark' || stored === 'system' ? stored : null;
    } catch {
      // Storage may be unavailable (private mode, blocked cookies).
      return null;
    }
  }

  private persist(preference: ThemePreference): void {
    try {
      this.document.defaultView?.localStorage.setItem(THEME_STORAGE_KEY, preference);
    } catch {
      // The preference simply does not survive the session.
    }
  }

  private prefersDark(): boolean {
    return this.document.defaultView?.matchMedia?.(SYSTEM_DARK_QUERY).matches ?? false;
  }

  private apply(theme: ResolvedTheme): void {
    const root = this.document.documentElement;
    root.setAttribute('data-theme', theme);
    root.style.colorScheme = theme;
  }
}
