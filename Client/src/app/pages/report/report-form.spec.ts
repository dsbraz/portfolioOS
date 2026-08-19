import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ActivatedRoute, convertToParamMap } from '@angular/router';

import ReportForm from './report-form';

describe('ReportForm', () => {
  let component: ReportForm;
  let fixture: ComponentFixture<ReportForm>;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ReportForm],
      providers: [
        provideNoopAnimations(),
        provideHttpClient(),
        provideHttpClientTesting(),
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              paramMap: convertToParamMap({ token: 'test-token' }),
            },
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ReportForm);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
    fixture.detectChanges();

    const req = httpMock.expectOne('/api/monthly-indicator/test-token');
    req.flush({
      startup_name: 'Test Startup',
      startup_logo_url: null,
      month: 1,
      year: 2026,
      existing_indicator: null,
    });
  });

  afterEach(() => httpMock.verify());

  it('should have a valid form when all fields are empty (all optional)', () => {
    expect(component.form.valid).toBe(true);
  });

  it('should be invalid when recurring_revenue_pct is negative', () => {
    component.form.controls.recurring_revenue_pct.setValue(-1);
    expect(component.form.controls.recurring_revenue_pct.hasError('min')).toBe(true);
    expect(component.form.valid).toBe(false);
  });

  it('should be invalid when gross_margin_pct is negative', () => {
    component.form.controls.gross_margin_pct.setValue(-0.01);
    expect(component.form.controls.gross_margin_pct.hasError('min')).toBe(true);
    expect(component.form.valid).toBe(false);
  });

  it('should be invalid when headcount is negative', () => {
    component.form.controls.headcount.setValue(-1);
    expect(component.form.controls.headcount.hasError('min')).toBe(true);
    expect(component.form.valid).toBe(false);
  });

  it('should be invalid when headcount is not an integer', () => {
    component.form.controls.headcount.setValue(1.5);
    expect(component.form.controls.headcount.hasError('integer')).toBe(true);
    expect(component.form.valid).toBe(false);
  });

  it('should be invalid when total_revenue exceeds max', () => {
    component.form.controls.total_revenue.setValue(9_999_999_999_999_999);
    expect(component.form.controls.total_revenue.hasError('max')).toBe(true);
    expect(component.form.valid).toBe(false);
  });

  it('should be valid when monetary fields are negative (e.g. burn)', () => {
    component.form.controls.ebitda_burn.setValue(-500000);
    expect(component.form.controls.ebitda_burn.valid).toBe(true);
    expect(component.form.valid).toBe(true);
  });

  it('should be valid when headcount is zero', () => {
    component.form.controls.headcount.setValue(0);
    expect(component.form.controls.headcount.valid).toBe(true);
    expect(component.form.valid).toBe(true);
  });

  it('should be valid with all fields filled within limits', () => {
    component.form.patchValue({
      total_revenue: 500000,
      cash_balance: 1000000,
      ebitda_burn: -20000,
      recurring_revenue_pct: 75,
      gross_margin_pct: 60,
      headcount: 10,
      achievements: 'Lancamento do produto',
      challenges: 'Escalar vendas',
    });
    expect(component.form.valid).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Page flow: load by token, prefill, submit, and the three visible states.
// This is the one form a founder fills with nobody from the fund nearby, so
// every state has to speak for itself.
// ---------------------------------------------------------------------------

describe('ReportForm page flow', () => {
  let fixture: ComponentFixture<ReportForm>;
  let component: ReportForm;
  let httpMock: HttpTestingController;

  const contexto = {
    startup_name: 'Vertah',
    startup_logo_url: null,
    month: 7,
    year: 2026,
    existing_indicator: null,
  };

  async function render(): Promise<void> {
    await TestBed.configureTestingModule({
      imports: [ReportForm],
      providers: [
        provideNoopAnimations(),
        provideHttpClient(),
        provideHttpClientTesting(),
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: convertToParamMap({ token: 'tok-1' }) } },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ReportForm);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
  }

  afterEach(() => {
    // Reset FIRST: a verify() that throws must not leave the TestBed
    // instantiated, or every later test dies on configureTestingModule.
    try {
      httpMock.verify();
    } finally {
      TestBed.resetTestingModule();
    }
  });

  it('announces loading until the context arrives', async () => {
    await render();

    expect(component.loading()).toBe(true);
    // The loading state is a spinner; its accessible name is the announcement.
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[aria-label="Carregando"]'),
    ).toBeTruthy();

    httpMock.expectOne('/api/monthly-indicator/tok-1').flush(contexto);
    fixture.detectChanges();

    expect(component.loading()).toBe(false);
    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('Vertah');
  });

  it('shows a dead-link message instead of an empty page', async () => {
    await render();
    httpMock
      .expectOne('/api/monthly-indicator/tok-1')
      .flush({ detail: 'nope' }, { status: 404, statusText: 'Not Found' });
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('Link invalido ou expirado');
    expect(el.querySelector('form')).toBeNull();
  });

  it('prefills the reportable zone from a previous submission', async () => {
    await render();
    httpMock.expectOne('/api/monthly-indicator/tok-1').flush({
      ...contexto,
      existing_indicator: {
        total_revenue: 150000,
        cash_balance: null,
        ebitda_burn: -80000,
        recurring_revenue_pct: 82,
        gross_margin_pct: null,
        headcount: 24,
        achievements: 'Fechamos o contrato X',
        challenges: null,
      },
    });
    fixture.detectChanges();

    const raw = component.form.getRawValue();
    expect(raw.total_revenue).toBe(150000);
    expect(raw.headcount).toBe(24);
    expect(raw.achievements).toBe('Fechamos o contrato X');
    // Null text becomes empty string so the textarea does not print "null".
    expect(raw.challenges).toBe('');
  });

  it('submits and lands on the confirmation state', async () => {
    await render();
    httpMock.expectOne('/api/monthly-indicator/tok-1').flush(contexto);
    fixture.detectChanges();
    component.form.patchValue({ total_revenue: 1000 });

    component.onSubmit();
    const req = httpMock.expectOne('/api/monthly-indicator/tok-1');
    expect(req.request.method).toBe('POST');
    expect(req.request.body.total_revenue).toBe(1000);
    req.flush(null);
    fixture.detectChanges();

    expect(component.submitted()).toBe(true);
    expect(component.submitting()).toBe(false);
    expect((fixture.nativeElement as HTMLElement).querySelector('form')).toBeNull();
  });

  it('reveals the offending field instead of silently refusing an invalid submit', async () => {
    await render();
    httpMock.expectOne('/api/monthly-indicator/tok-1').flush(contexto);
    fixture.detectChanges();
    component.form.patchValue({ headcount: 2.5 });

    component.onSubmit();
    fixture.detectChanges();

    // No POST goes out, and the error is on screen, not just in form state.
    httpMock.expectNone(
      (r) => r.method === 'POST' && r.url === '/api/monthly-indicator/tok-1',
    );
    expect(component.form.controls.headcount.touched).toBe(true);
    expect((fixture.nativeElement as HTMLElement).textContent).toContain(
      'Informe um numero inteiro',
    );
  });

  it('recovers from a failed submit and keeps what was typed', async () => {
    await render();
    httpMock.expectOne('/api/monthly-indicator/tok-1').flush(contexto);
    fixture.detectChanges();
    component.form.patchValue({ total_revenue: 1000 });

    component.onSubmit();
    httpMock
      .expectOne((r) => r.method === 'POST')
      .flush({ detail: 'Fora dos limites'.repeat(1) }, { status: 400, statusText: 'Bad' });
    fixture.detectChanges();

    // Not submitted, not stuck: the founder can fix and resend.
    expect(component.submitted()).toBe(false);
    expect(component.submitting()).toBe(false);
    expect(component.form.getRawValue().total_revenue).toBe(1000);
  });

  it('ignores a second click while a submit is in flight', async () => {
    await render();
    httpMock.expectOne('/api/monthly-indicator/tok-1').flush(contexto);
    fixture.detectChanges();

    component.onSubmit();
    component.onSubmit();

    // Exactly one POST: the guard, not luck.
    httpMock.expectOne((r) => r.method === 'POST').flush(null);
  });
});
