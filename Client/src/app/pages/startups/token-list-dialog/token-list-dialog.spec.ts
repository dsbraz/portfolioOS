import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MAT_DIALOG_DATA, MatDialog, MatDialogRef } from '@angular/material/dialog';

import { MonthlyIndicatorToken } from '../../../models/monthly-indicator-token.model';
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

  async function render(tokens: MonthlyIndicatorToken[]): Promise<HTMLElement> {
    await TestBed.configureTestingModule({
      imports: [TokenListDialog],
      providers: [
        provideNoopAnimations(),
        { provide: MatDialogRef, useValue: { close: vi.fn() } },
        { provide: MatDialog, useValue: dialogSpy },
        { provide: MAT_DIALOG_DATA, useValue: { tokens, executives: [] } },
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
