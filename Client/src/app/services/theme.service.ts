import { DOCUMENT, Injectable, computed, inject, signal } from '@angular/core';

/** O que o usuário escolheu. `system` delega ao sistema operacional. */
export type ThemePreference = 'system' | 'light' | 'dark';
/** O tema que de fato está pintado. */
export type ResolvedTheme = 'light' | 'dark';

/** Compartilhado com o script de bootstrap do `index.html`, que aplica o tema
 *  antes do primeiro paint. Mude os dois juntos. */
export const THEME_STORAGE_KEY = 'portfolio-theme';

const SYSTEM_DARK_QUERY = '(prefers-color-scheme: dark)';

/**
 * Preferência de tema.
 *
 * Escreve `[data-theme]` e `color-scheme` no elemento raiz: o primeiro dirige a
 * camada de tokens BRQ, o segundo faz os controles nativos (scrollbar, pickers)
 * acompanharem.
 *
 * O padrão é `system` e ele é REATIVO: um listener de `matchMedia` repinta
 * quando o sistema operacional troca de tema com a página aberta. Sem esse
 * listener, o `data-theme` carimbado no bootstrap desliga o ramo
 * `@media (prefers-color-scheme: dark)` do CSS e a troca ao vivo não acontece.
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

  /** Percorre sistema -> claro -> escuro -> sistema. */
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
      // Só repinta quando a escolha é delegar ao sistema; uma escolha explícita
      // não deve ser sobrescrita porque o SO mudou.
      if (this.preference() === 'system') this.apply(this.resolved());
    });
  }

  private readStored(): ThemePreference | null {
    try {
      const stored = this.document.defaultView?.localStorage.getItem(THEME_STORAGE_KEY);
      return stored === 'light' || stored === 'dark' || stored === 'system' ? stored : null;
    } catch {
      // Storage pode estar indisponível (modo privado, cookies bloqueados).
      return null;
    }
  }

  private persist(preference: ThemePreference): void {
    try {
      this.document.defaultView?.localStorage.setItem(THEME_STORAGE_KEY, preference);
    } catch {
      // A preferência simplesmente não sobrevive à sessão.
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
