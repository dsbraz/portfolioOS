import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

import { Executive } from '../../../models/executive.model';
import { MonthlyIndicatorToken } from '../../../models/monthly-indicator-token.model';
import { TokenPanelDialog } from './token-panel-dialog';

describe('TokenPanelDialog', () => {
  let fixture: ComponentFixture<TokenPanelDialog>;

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
      imports: [TokenPanelDialog],
      providers: [
        provideNoopAnimations(),
        { provide: MatDialogRef, useValue: { close: vi.fn() } },
        { provide: MAT_DIALOG_DATA, useValue: { token, executives } },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(TokenPanelDialog);
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  }

  afterEach(() => {
    TestBed.resetTestingModule();
    vi.restoreAllMocks();
  });

  it('should render the link as text so no step depends on the clipboard', async () => {
    const element = await render([executive({})]);

    const link = element.querySelector('.link-text');
    expect(link?.textContent).toContain('/monthly-indicator/abc123');
  });

  it('should name the copy control by its period', async () => {
    const element = await render([executive({})]);

    const copy = element.querySelector('[aria-label="Copiar link de Jul/2026"]');
    expect(copy).toBeTruthy();
  });

  it('should expose the send as a real wa.me link present before any click', async () => {
    const element = await render([executive({})]);

    const send = element.querySelector<HTMLAnchorElement>(
      '[aria-label="Enviar por WhatsApp para Ana Costa"]',
    );
    expect(send).toBeTruthy();
    expect(send?.tagName).toBe('A');
    expect(send?.getAttribute('href')).toContain('https://wa.me/5511912345678?text=');
    expect(send?.getAttribute('href')).toContain(encodeURIComponent('Olá Ana'));
    expect(send?.getAttribute('rel')).toContain('noopener');
  });

  it('should show the resolved recipient number before the send', async () => {
    const element = await render([executive({})]);

    expect(element.textContent).toContain('+55 (11) 91234-5678');
  });

  it('should offer no send for an unresolvable phone and say why', async () => {
    const element = await render([executive({ name: 'Bruno Lima', phone: 'ramal 22' })]);

    expect(element.querySelector('[aria-label="Enviar por WhatsApp para Bruno Lima"]')).toBeNull();
    expect(element.textContent).toContain('Sem telefone válido');
    expect(element.textContent).toContain('Executivos');
  });

  it('should explain the empty case instead of rendering an unusable panel', async () => {
    const element = await render([]);

    expect(element.textContent).toContain('Nenhum executivo cadastrado');
    expect(element.querySelector('.recipient-list')).toBeNull();
  });

  it('should preview the message that WhatsApp will open with', async () => {
    const element = await render([executive({})]);

    const preview = element.querySelector('.message-preview');
    expect(preview?.textContent).toContain('Olá Ana. Tudo bem?');
    expect(preview?.textContent).toContain('julho/2026');
  });
});
