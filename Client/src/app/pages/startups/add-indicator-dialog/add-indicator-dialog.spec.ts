import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { NEVER, Subject, of, throwError } from 'rxjs';

import { MonthlyIndicator } from '../../../models/monthly-indicator.model';
import { MonthlyIndicatorToken } from '../../../models/monthly-indicator-token.model';
import { MonthlyIndicatorService } from '../../../services/monthly-indicator.service';
import { MonthlyIndicatorTokenService } from '../../../services/monthly-indicator-token.service';
import { AddIndicatorDialog, AddIndicatorDialogData } from './add-indicator-dialog';

describe('AddIndicatorDialog', () => {
  let fixture: ComponentFixture<AddIndicatorDialog>;
  let component: AddIndicatorDialog;

  const dialogRef = {
    close: vi.fn(),
    disableClose: false,
    keydownEvents$: new Subject<KeyboardEvent>(),
    backdropClick$: new Subject<MouseEvent>(),
    keydownEvents() {
      return this.keydownEvents$.asObservable();
    },
    backdropClick() {
      return this.backdropClick$.asObservable();
    },
  };
  const indicatorService = { create: vi.fn() };
  const tokenService = { create: vi.fn() };
  const snackBar = { open: vi.fn() };

  function previousMonth(): { month: number; year: number } {
    const now = new Date();
    return now.getMonth() === 0
      ? { month: 12, year: now.getFullYear() - 1 }
      : { month: now.getMonth(), year: now.getFullYear() };
  }

  const token: MonthlyIndicatorToken = {
    id: 't1',
    token: 'tok1',
    startup_id: 's1',
    month: previousMonth().month,
    year: previousMonth().year,
    created_at: '',
  };

  async function render(over: Partial<AddIndicatorDialogData> = {}): Promise<HTMLElement> {
    const data: AddIndicatorDialogData = {
      startupId: 's1',
      indicators: [],
      tokens: [],
      executives: [],
      ...over,
    };
    await TestBed.configureTestingModule({
      imports: [AddIndicatorDialog],
      providers: [
        provideNoopAnimations(),
        { provide: MatDialogRef, useValue: dialogRef },
        { provide: MAT_DIALOG_DATA, useValue: data },
        { provide: MonthlyIndicatorService, useValue: indicatorService },
        { provide: MonthlyIndicatorTokenService, useValue: tokenService },
      ],
    })
      // MatSnackBarModule (imported by the component) provides its own MatSnackBar;
      // overrideProvider wins over that, a plain provider does not.
      .overrideProvider(MatSnackBar, { useValue: snackBar })
      .compileComponents();

    fixture = TestBed.createComponent(AddIndicatorDialog);
    component = fixture.componentInstance;
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  }

  afterEach(() => {
    TestBed.resetTestingModule();
    vi.clearAllMocks();
  });

  it('defaults the period to the previous month', async () => {
    await render();
    expect(component.form.getRawValue().month).toBe(previousMonth().month);
    expect(component.form.getRawValue().year).toBe(previousMonth().year);
  });

  it('offers the two modes with radio semantics, fill selected first', async () => {
    const el = await render();
    expect(el.querySelector('[role="radiogroup"]')).toBeTruthy();
    expect(el.querySelectorAll('mat-radio-button')).toHaveLength(2);
    expect(el.textContent).toContain('Preencher agora');
    expect(el.textContent).toContain('Gerar link para a investida');
    expect(component.mode()).toBe('fill');
  });

  it('keeps what was typed when the mode switches', async () => {
    await render();
    component.form.get('reported.total_revenue')!.setValue(1500);

    component.setMode('link');
    component.setMode('fill');

    // Switching hides the other mode's controls without destroying the form.
    expect(component.form.get('reported.total_revenue')!.value).toBe(1500);
  });

  it('labels the primary button by mode', async () => {
    const el = await render();
    const primary = () => el.querySelector('mat-dialog-actions button[color="primary"]');
    expect(primary()?.textContent?.trim()).toBe('Salvar indicador');

    component.setMode('link');
    fixture.detectChanges();
    expect(primary()?.textContent?.trim()).toBe('Gerar link');
  });

  it('warns when the period already has an indicator or a link', async () => {
    const period = previousMonth();
    const indicator = { month: period.month, year: period.year } as MonthlyIndicator;
    const el = await render({ indicators: [indicator], tokens: [token] });

    expect(el.textContent).toContain('já possui indicador');
    expect(el.textContent).toContain('Já existe um link para este período');
  });

  it('saves the indicator, turning a blank note into absence, then closes', async () => {
    indicatorService.create.mockReturnValue(of({} as MonthlyIndicator));
    await render();
    component.form.get('reported.total_revenue')!.setValue(1000);
    component.form.get('comments')!.setValue('   ');

    component.submit();

    expect(indicatorService.create).toHaveBeenCalledOnce();
    const payload = indicatorService.create.mock.calls[0][1];
    expect(payload.total_revenue).toBe(1000);
    // A blank field must not wipe stored text on the upsert (PRD-001 §6.1/§8).
    expect(payload.comments).toBeNull();
    expect(dialogRef.close).toHaveBeenCalledWith(true);
  });

  it('generates the link and reveals the panel without closing', async () => {
    tokenService.create.mockReturnValue(of(token));
    const el = await render({
      executives: [
        {
          id: 'e1',
          startup_id: 's1',
          name: 'Ana Costa',
          role: 'CEO',
          email: null,
          phone: '(11) 91234-5678',
          linkedin: null,
          created_at: '',
          updated_at: '',
        },
      ],
    });
    component.setMode('link');
    fixture.detectChanges();

    component.submit();
    fixture.detectChanges();

    expect(tokenService.create).toHaveBeenCalledWith('s1', {
      month: previousMonth().month,
      year: previousMonth().year,
    });
    expect(dialogRef.close).not.toHaveBeenCalled();
    // The panel appears inline with the link as text and the send affordance.
    expect(el.querySelector('app-token-panel')).toBeTruthy();
    expect(el.querySelector('[aria-label="Enviar por WhatsApp para Ana Costa"]')).toBeTruthy();
  });

  // Regression: only the "Fechar" button returned `true`. Closing by the header
  // X, Escape or the backdrop returned `undefined`, so the page never reloaded
  // and the link just created was missing from "Links anteriores".
  describe('after a link is generated, every way out signals the change', () => {
    async function renderGenerated(): Promise<HTMLElement> {
      tokenService.create.mockReturnValue(of(token));
      const el = await render();
      component.setMode('link');
      component.submit();
      fixture.detectChanges();
      return el;
    }

    it('closes with true from the header close button', async () => {
      const el = await renderGenerated();
      (el.querySelector('button[aria-label="Fechar diálogo"]') as HTMLButtonElement).click();
      expect(dialogRef.close).toHaveBeenCalledWith(true);
    });

    it('closes with true on Escape', async () => {
      await renderGenerated();
      dialogRef.keydownEvents$.next(new KeyboardEvent('keydown', { key: 'Escape' }));
      expect(dialogRef.close).toHaveBeenCalledWith(true);
    });

    it('closes with true on a backdrop click', async () => {
      await renderGenerated();
      dialogRef.backdropClick$.next(new MouseEvent('click'));
      expect(dialogRef.close).toHaveBeenCalledWith(true);
    });
  });

  // Regression: Escape during an in-flight save closed with `false`; the server
  // still created the record and the page never reloaded to show it.
  it.each([['fill'], ['link']] as const)(
    'reports a change when closed while the %s request is in flight',
    async (mode) => {
      indicatorService.create.mockReturnValue(NEVER);
      tokenService.create.mockReturnValue(NEVER);
      await render();
      component.setMode(mode);
      component.submit();

      dialogRef.keydownEvents$.next(new KeyboardEvent('keydown', { key: 'Escape' }));

      expect(dialogRef.close).toHaveBeenCalledWith(true);
    },
  );

  // Regression: clearing the year to retype it put "null" in the title.
  it('keeps the last valid period in the title while the year is being retyped', async () => {
    await render();
    const label = component.periodLabel();

    component.form.controls.year.setValue(null);
    expect(component.periodLabel()).toBe(label);

    component.form.controls.year.setValue(26);
    expect(component.periodLabel()).toBe(label);
  });

  it('closes without a change signal on Escape before anything was created', async () => {
    await render();
    dialogRef.keydownEvents$.next(new KeyboardEvent('keydown', { key: 'Escape' }));
    expect(dialogRef.close).toHaveBeenCalledWith(false);
  });

  // Regression: the year lost its 2000–2100 range, so `26` reached the API and
  // came back as a 422 whose detail rendered as "[object Object]".
  it.each([['fill'], ['link']] as const)(
    'rejects a year outside 2000–2100 in %s mode without calling the API',
    async (mode) => {
      const el = await render();
      component.setMode(mode);
      component.form.controls.year.setValue(26);
      component.submit();
      fixture.detectChanges();

      expect(component.form.controls.year.hasError('min')).toBe(true);
      expect(indicatorService.create).not.toHaveBeenCalled();
      expect(tokenService.create).not.toHaveBeenCalled();
      expect(el.textContent).toContain('Informe um ano entre 2000 e 2100.');
    },
  );

  it('reports a save error and stays open', async () => {
    indicatorService.create.mockImplementation(() =>
      throwError(() => ({ error: { detail: 'boom' } })),
    );
    await render();

    component.submit();

    expect(snackBar.open).toHaveBeenCalledWith('boom', 'Fechar', expect.anything());
    expect(dialogRef.close).not.toHaveBeenCalled();
  });

  it('separates the fund note from the reportable zone in fill mode', async () => {
    const el = await render();
    expect(el.textContent).toContain('Anotações do fundo');
    expect(el.querySelector('#add-comments')).toBeTruthy();
  });

  // PRD-001 criterion 6.5.7 / item 6: a browser agent completes generate → send
  // using only roles and accessible names, never an implementation selector.
  it('is operable end to end by role and accessible name', async () => {
    tokenService.create.mockReturnValue(of(token));
    const el = await render({
      executives: [
        {
          id: 'e1',
          startup_id: 's1',
          name: 'Ana Costa',
          role: 'CEO',
          email: null,
          phone: '(11) 91234-5678',
          linkedin: null,
          created_at: '',
          updated_at: '',
        },
      ],
    });

    // Pick the link mode by its label, not by index.
    const linkRadio = [...el.querySelectorAll('mat-radio-button')].find((r) =>
      r.textContent?.includes('Gerar link para a investida'),
    );
    linkRadio!.querySelector('input')!.click();
    fixture.detectChanges();

    // Trigger the primary action by its name.
    const generate = [...el.querySelectorAll('mat-dialog-actions button')].find(
      (b) => b.textContent?.trim() === 'Gerar link',
    );
    (generate as HTMLButtonElement).click();
    fixture.detectChanges();

    // The send is a real wa.me link, named for its recipient, present before any
    // click — an agent can read the href instead of clicking.
    const send = el.querySelector<HTMLAnchorElement>(
      '[aria-label="Enviar por WhatsApp para Ana Costa"]',
    );
    expect(send?.tagName).toBe('A');
    expect(send?.getAttribute('href')).toContain('https://wa.me/5511912345678?text=');
  });
});
