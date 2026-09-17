import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MatSnackBar } from '@angular/material/snack-bar';
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

  it('splits recipients into reachable and blocked by contact', async () => {
    const element = await render([
      executive({ name: 'Ana Costa' }),
      executive({ id: 'e2', name: 'Bruno Lima', phone: 'ramal 22' }),
    ]);

    expect(element.querySelector('[aria-label="Enviar por WhatsApp para Ana Costa"]')).toBeTruthy();
    expect(element.querySelector('[aria-label="Enviar por WhatsApp para Bruno Lima"]')).toBeNull();
    expect(element.textContent).toContain('Sem canal de envio');
  });

  it('builds the WhatsApp link with the fund message encoded', async () => {
    const element = await render([executive({ name: 'Ana Costa Ribeiro' })]);

    const href = element
      .querySelector('[aria-label="Enviar por WhatsApp para Ana Costa Ribeiro"]')
      ?.getAttribute('href');
    const message =
      'Olá Ana. Tudo bem?\n' +
      `Segue o link para atualizações dos dados referentes a julho/2026: ${window.location.origin}/monthly-indicator/abc123\n` +
      'Obrigado';
    expect(href).toBe(`https://wa.me/5511912345678?text=${encodeURIComponent(message)}`);
  });

  // One channel per executive: WhatsApp when it resolves, e-mail only otherwise.
  it('offers only WhatsApp when both channels resolve', async () => {
    const element = await render([executive({ name: 'Ana Costa', email: 'ana@vertah.com.br' })]);

    const actions = [...element.querySelectorAll('a[aria-label^="Enviar por"]')].map((a) =>
      a.getAttribute('aria-label'),
    );
    expect(actions).toEqual(['Enviar por WhatsApp para Ana Costa']);
  });

  it('falls back to e-mail when there is no phone, and says why', async () => {
    const element = await render([
      executive({ name: 'Marina Alencar', phone: null, email: 'marina@vertah.com.br' }),
    ]);

    const mail = element.querySelector<HTMLAnchorElement>(
      '[aria-label="Enviar por e-mail para Marina Alencar"]',
    );
    expect(mail?.getAttribute('href')).toContain(
      `mailto:marina@vertah.com.br?subject=${encodeURIComponent('Vertah — indicadores de julho/2026')}`,
    );
    expect(element.textContent).toContain('Sem telefone cadastrado');
    expect(element.textContent).not.toContain('Sem canal de envio');
  });

  // Records saved before the country code became mandatory must not vanish.
  it('names a legacy phone without country code as the reason for e-mail', async () => {
    const element = await render([
      executive({ name: 'Marina Alencar', phone: '11912345678', email: 'marina@vertah.com.br' }),
    ]);

    expect(element.querySelector('[aria-label^="Enviar por WhatsApp"]')).toBeNull();
    expect(element.querySelector('[aria-label="Enviar por e-mail para Marina Alencar"]')).toBeTruthy();
    expect(element.textContent).toContain('Telefone sem código do país');
  });

  it('encodes the address so it cannot add recipients to the mail', async () => {
    const element = await render([
      executive({ name: 'Marina Alencar', phone: null, email: 'x?bcc=eu@fora.com' }),
    ]);

    const href = element.querySelector('[aria-label^="Enviar por e-mail"]')?.getAttribute('href');
    expect(href).toMatch(/^mailto:x%3Fbcc%3Deu@fora\.com\?subject=/);
  });

  it('blocks only when neither channel resolves', async () => {
    const element = await render([executive({ name: 'Bruno Lima', phone: '11912345678' })]);

    expect(element.querySelector('[aria-label^="Enviar por"]')).toBeNull();
    expect(element.textContent).toContain('Sem canal de envio');
    expect(element.textContent).toContain('Telefone sem código do país');
  });

  it('reaches a foreign executive whose number carries its country code', async () => {
    const element = await render([
      executive({ id: 'e3', name: 'John Miller', phone: '+14155551234' }),
    ]);

    const send = element.querySelector<HTMLAnchorElement>(
      '[aria-label="Enviar por WhatsApp para John Miller"]',
    );
    expect(send?.getAttribute('href')).toContain('https://wa.me/14155551234?text=');
    expect(element.textContent).toContain('+14155551234');
  });

  // Outside a secure context the clipboard rejects; the link stays visible as text.
  it('reports a clipboard failure and points at the visible link', async () => {
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText: () => Promise.reject(new Error('denied')) },
      configurable: true,
    });
    const element = await render([executive({})]);
    const open = vi.spyOn(fixture.debugElement.injector.get(MatSnackBar), 'open');

    element.querySelector<HTMLButtonElement>('[aria-label^="Copiar link de"]')?.click();
    await fixture.whenStable();

    expect(open).toHaveBeenCalledWith(
      'Não foi possível copiar. O link está visível acima para copiar manualmente.',
      'Fechar',
      expect.anything(),
    );
  });
});
