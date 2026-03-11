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
