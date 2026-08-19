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
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  }

  afterEach(() => {
    TestBed.resetTestingModule();
    vi.restoreAllMocks();
  });

  it('splits recipients into reachable and blocked by phone validity', async () => {
    const element = await render([
      executive({ name: 'Ana Costa' }),
      executive({ id: 'e2', name: 'Bruno Lima', phone: 'ramal 22' }),
    ]);

    expect(element.querySelector('[aria-label="Enviar por WhatsApp para Ana Costa"]')).toBeTruthy();
    expect(element.querySelector('[aria-label="Enviar por WhatsApp para Bruno Lima"]')).toBeNull();
    expect(element.textContent).toContain('Sem telefone válido');
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
    expect(element.textContent).not.toContain('Sem telefone válido');
  });

  // NOTE: copyLink's clipboard-failure branch (RFC-001 §6) is implemented in the
  // component but not unit-tested here — the Angular Vitest/jsdom builder does
  // not expose a mockable navigator.clipboard to the component under test, so a
  // rejection cannot be staged reliably. The link is always visible as text, so
  // the copy path is a convenience, and its success path is exercised through
  // the dialog spec.
});
