import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MAT_DIALOG_DATA, MatDialog, MatDialogRef } from '@angular/material/dialog';

import { MonthlyIndicatorToken } from '../../../models/monthly-indicator-token.model';
import { MonthlyReportDispatch } from '../../../models/monthly-report.model';
import { TokenListDialog } from './token-list-dialog';

describe('TokenListDialog', () => {
  let fixture: ComponentFixture<TokenListDialog>;
  const dialogSpy = { open: vi.fn() };

  const token = (month: number): MonthlyIndicatorToken => ({
    id: `t${month}`,
    token: `tok${month}`,
    startup_id: 's1',
    month,
    year: 2026,
    created_at: '',
  });

  async function render(
    tokens: MonthlyIndicatorToken[],
    dispatches: MonthlyReportDispatch[] | null = [],
  ): Promise<HTMLElement> {
    await TestBed.configureTestingModule({
      imports: [TokenListDialog],
      providers: [
        provideNoopAnimations(),
        { provide: MatDialogRef, useValue: { close: vi.fn() } },
        { provide: MatDialog, useValue: dialogSpy },
        { provide: MAT_DIALOG_DATA, useValue: { tokens, dispatches, executives: [] } },
      ],
    })
      // The component imports MatDialogModule, which brings its own MatDialog
      // provider; overrideProvider is what actually wins over it.
      .overrideProvider(MatDialog, { useValue: dialogSpy })
      .compileComponents();

    fixture = TestBed.createComponent(TokenListDialog);
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  }

  afterEach(() => {
    TestBed.resetTestingModule();
    dialogSpy.open.mockClear();
  });

  const dispatch = (
    month: number,
    kind: 'initial' | 'reminder',
    outcome: { sent?: boolean; error?: string } = { sent: true },
  ): MonthlyReportDispatch => ({
    id: `d${month}${kind}`,
    startup_id: 's1',
    executive_id: 'e1',
    recipient_email: 'ana@payface.com',
    month,
    year: 2026,
    kind,
    error: outcome.error ?? null,
    attempted_at: `2026-0${month + 1}-05T12:00:00Z`,
    sent_at: outcome.sent ? `2026-0${month + 1}-05T12:00:04Z` : null,
  });

  const rowsOf = (element: HTMLElement) =>
    Array.from(element.querySelectorAll('tr[mat-row], tr.mat-mdc-row'));

  it('should show the automatic e-mails of each period, failures in text', async () => {
    const element = await render(
      [token(6), token(7)],
      [dispatch(7, 'initial'), dispatch(7, 'reminder', { error: 'SMTPRecipientsRefused' })],
    );
    const rows = rowsOf(element);

    expect(rows[0].textContent).toContain('Nenhum');
    expect(rows[1].textContent).toContain('Envio em 05/08 para ana@payface.com');
    expect(rows[1].textContent).toContain('Lembrete: tentativa em 05/08');
    expect(rows[1].textContent).toContain('Falhou');
    expect(rows[1].textContent).toContain('SMTPRecipientsRefused');
  });

  // The job could not record the outcome: the mail may have left. Saying so is
  // what keeps the operator from sending a duplicate.
  it('should say in text when a send is unconfirmed', async () => {
    const element = await render([token(7)], [dispatch(7, 'initial', {})]);
    const row = rowsOf(element)[0];

    expect(row.textContent).toContain('Envio: tentativa em 05/08');
    expect(row.textContent).toContain('Não confirmado');
    expect(row.textContent).toContain('pode ter saído');
    expect(row.textContent).not.toContain('Envio em');
  });

  // "Nenhum" would tell the operator nothing went out, and they would resend
  // by hand what the job already sent.
  it('should say the history is unavailable instead of showing none', async () => {
    const element = await render([token(7)], null);

    expect(element.querySelector('[role="status"]')?.textContent).toContain(
      'Não foi possível carregar o histórico',
    );
    expect(rowsOf(element)[0].textContent).toContain('Indisponível');
    expect(rowsOf(element)[0].textContent).not.toContain('Nenhum');
  });

  it('should name every row action by its period', async () => {
    const element = await render([token(6), token(7)]);

    // Three identical unnamed buttons are indistinguishable to assistive tech
    // and to an agent; the name has to carry the row's identity.
    expect(element.querySelector('[aria-label="Abrir link de Jun/2026"]')).toBeTruthy();
    expect(element.querySelector('[aria-label="Abrir link de Jul/2026"]')).toBeTruthy();
  });

  it('should describe the table for assistive tech', async () => {
    const element = await render([token(7)]);

    expect(element.querySelector('caption')?.textContent).toContain('Links de relatório');
    const headers = Array.from(element.querySelectorAll('th'));
    expect(headers.length).toBeGreaterThan(0);
    expect(headers.every((header) => header.getAttribute('scope') === 'col')).toBe(true);
  });

  it('should open the link panel for the chosen period', async () => {
    const element = await render([token(7)]);

    element.querySelector<HTMLButtonElement>('[aria-label="Abrir link de Jul/2026"]')?.click();

    expect(dialogSpy.open).toHaveBeenCalledOnce();
    expect(dialogSpy.open.mock.calls[0][1].data.token.month).toBe(7);
  });

  it('should state the empty case', async () => {
    const element = await render([]);

    expect(element.textContent).toContain('Nenhum link gerado ainda.');
    expect(element.querySelector('table')).toBeNull();
  });
});
