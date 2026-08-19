import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';

import { Executive } from '../../../models/executive.model';
import { MonthlyIndicatorToken } from '../../../models/monthly-indicator-token.model';
import { TokenPanel } from './token-panel';

describe('TokenPanel', () => {
  let fixture: ComponentFixture<TokenPanel>;

  const token: MonthlyIndicatorToken = {
    id: 't1',
    token: 'abc123',
    startup_id: 's1',
    month: 7,
    year: 2026,
    created_at: '2026-07-01T00:00:00Z',
  };

  const executive = (over: Partial<Executive>): Executive => ({
    id: 'e1',
    startup_id: 's1',
    name: 'Ana Costa',
    role: 'CEO',
    email: null,
    phone: '+5511912345678',
    linkedin: null,
    created_at: '',
    updated_at: '',
    ...over,
  });

  async function render(executives: Executive[]): Promise<HTMLElement> {
    await TestBed.configureTestingModule({
      imports: [TokenPanel],
      providers: [provideNoopAnimations()],
    }).compileComponents();

    fixture = TestBed.createComponent(TokenPanel);
    fixture.componentRef.setInput('token', token);
    fixture.componentRef.setInput('executives', executives);
    fixture.componentRef.setInput('startupName', 'Vertah');
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  }

  afterEach(() => {
    TestBed.resetTestingModule();
    vi.restoreAllMocks();
  });

  it('splits recipients into reachable and blocked by contact validity', async () => {
    const element = await render([
      executive({ name: 'Ana Costa' }),
      executive({ id: 'e2', name: 'Bruno Lima', phone: 'ramal 22' }),
    ]);

    expect(element.querySelector('[aria-label="Enviar por WhatsApp para Ana Costa"]')).toBeTruthy();
    expect(element.querySelector('[aria-label="Enviar por WhatsApp para Bruno Lima"]')).toBeNull();
    expect(element.textContent).toContain('Sem canal de envio');
  });

  // E-mail is the fallback channel: an executive with no usable phone is still
  // reachable when a registered address exists.
  it('offers e-mail when the phone cannot be used', async () => {
    const element = await render([
      executive({ name: 'Marina Alencar', phone: null, email: 'marina@vertah.com.br' }),
    ]);

    const mail = element.querySelector<HTMLAnchorElement>(
      '[aria-label="Enviar por e-mail para Marina Alencar"]',
    );
    expect(mail?.tagName).toBe('A');
    expect(mail?.getAttribute('href')).toContain('mailto:marina@vertah.com.br?subject=');
    // Reachable by some channel, so it is not an impediment.
    expect(element.textContent).not.toContain('Sem canal de envio');
  });

  it('blocks only when neither channel resolves', async () => {
    const element = await render([
      executive({ name: 'Bruno Lima', phone: 'ramal 22', email: null }),
    ]);

    expect(element.querySelector('[aria-label^="Enviar por WhatsApp"]')).toBeNull();
    expect(element.querySelector('[aria-label^="Enviar por e-mail"]')).toBeNull();
    expect(element.textContent).toContain('Sem canal de envio');
  });

  it('offers both channels when both resolve, with WhatsApp first', async () => {
    const element = await render([
      executive({ name: 'Ana Costa', email: 'ana@vertah.com.br' }),
    ]);

    const actions = [...element.querySelectorAll('a[aria-label^="Enviar por"]')].map((a) =>
      a.getAttribute('aria-label'),
    );
    expect(actions).toEqual([
      'Enviar por WhatsApp para Ana Costa',
      'Enviar por e-mail para Ana Costa',
    ]);
  });

  // The fund's executives are not all in Brazil: a foreign number carrying its
  // country prefix is a normal recipient, not an impediment.
  it('reaches a foreign executive whose number carries its country prefix', async () => {
    const element = await render([
      executive({ id: 'e3', name: 'John Miller', phone: '+14155551234' }),
    ]);

    const send = element.querySelector<HTMLAnchorElement>(
      '[aria-label="Enviar por WhatsApp para John Miller"]',
    );
    expect(send?.getAttribute('href')).toContain('https://wa.me/14155551234?text=');
    // Shown as stored — no invented grouping for a country whose rules we do
    // not encode.
    expect(element.textContent).toContain('+14155551234');
    expect(element.textContent).not.toContain('Sem canal de envio');
  });

  // Clipboard failure is common outside a secure context; the panel promises a
  // soft landing because the link is always visible as text (RFC-001 §6).
  it('reports a clipboard failure and points at the visible link', async () => {
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText: () => Promise.reject(new Error('sem permissão')) },
      configurable: true,
    });
    const snackSpy = vi.fn();
    await render([executive({})]);
    // Reach into the injected snackbar of this fixture.
    const component = fixture.componentInstance as unknown as {
      snackBar: { open: typeof snackSpy };
      copyLink(): void;
    };
    component.snackBar.open = snackSpy;

    component.copyLink();
    await new Promise((resolve) => setTimeout(resolve));

    expect(snackSpy).toHaveBeenCalledWith(
      'Não foi possível copiar. O link está visível acima para copiar manualmente.',
      'Fechar',
      expect.anything(),
    );
  });
});
