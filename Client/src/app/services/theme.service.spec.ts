import { TestBed } from '@angular/core/testing';

import { THEME_STORAGE_KEY, ThemeService } from './theme.service';

describe('ThemeService', () => {
  let listeners: ((e: { matches: boolean }) => void)[] = [];
  let systemDark = false;

  /** `matchMedia` falso que guarda o listener, para simular o SO trocando de
   *  tema com a página aberta. */
  const stubMatchMedia = () => {
    window.matchMedia = ((query: string) =>
      ({
        matches: systemDark && query.includes('dark'),
        media: query,
        addEventListener: (_: string, cb: (e: { matches: boolean }) => void) => listeners.push(cb),
        removeEventListener: () => undefined,
      }) as unknown as MediaQueryList) as typeof window.matchMedia;
  };

  const create = () => {
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({});
    return TestBed.inject(ThemeService);
  };

  const emitSystemChange = (dark: boolean) => {
    systemDark = dark;
    listeners.forEach((cb) => cb({ matches: dark }));
  };

  beforeEach(() => {
    listeners = [];
    systemDark = false;
    localStorage.removeItem(THEME_STORAGE_KEY);
    document.documentElement.removeAttribute('data-theme');
    document.documentElement.style.colorScheme = '';
    stubMatchMedia();
  });

  it('should default to following the system', () => {
    const service = create();
    expect(service.theme()).toBe('system');
    expect(service.isDark()).toBe(false);
  });

  it('should resolve to dark when the system prefers dark', () => {
    systemDark = true;
    stubMatchMedia();
    expect(create().isDark()).toBe(true);
  });

  // Regression: the bootstrap script stamps an explicit `data-theme`, which
  // disables the `prefers-color-scheme` branch of the CSS. Without a listener
  // the app never reacted to the OS changing theme while open.
  it('should repaint when the system switches while following it', () => {
    const service = create();
    expect(service.isDark()).toBe(false);

    emitSystemChange(true);

    expect(service.isDark()).toBe(true);
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
  });

  it('should not let a system change override an explicit choice', () => {
    const service = create();
    service.set('light');

    emitSystemChange(true);

    expect(service.isDark()).toBe(false);
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
  });

  it('should cycle system -> light -> dark -> system', () => {
    const service = create();
    expect(service.theme()).toBe('system');
    service.cycle();
    expect(service.theme()).toBe('light');
    service.cycle();
    expect(service.theme()).toBe('dark');
    service.cycle();
    expect(service.theme()).toBe('system');
  });

  it('should persist the choice so it survives a reload', () => {
    create().set('dark');
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('dark');
  });

  // The token layer keys off `[data-theme]`, and `color-scheme` is what makes
  // native controls (scrollbars, date pickers) match. Both must move together.
  it('should drive both data-theme and color-scheme on the root element', () => {
    const service = create();
    service.set('dark');

    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
    expect(document.documentElement.style.colorScheme).toBe('dark');

    service.set('light');

    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
    expect(document.documentElement.style.colorScheme).toBe('light');
  });
});
