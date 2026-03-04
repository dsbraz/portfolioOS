import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { ActivatedRoute, ParamMap, Router, convertToParamMap } from '@angular/router';
import { BehaviorSubject, of } from 'rxjs';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';

import { Portfolio } from './portfolio';
import { PortfolioService } from '../../services/portfolio.service';
import { StartupService } from '../../services/startup.service';

describe('Portfolio', () => {
  let component: Portfolio;
  let fixture: ComponentFixture<Portfolio>;
  let queryParamMap$: BehaviorSubject<ParamMap>;

  const portfolioServiceSpy = {
    getSummary: vi.fn(),
  };
  const startupServiceSpy = {
    create: vi.fn(),
  };
  const routerSpy = {
    navigate: vi.fn().mockResolvedValue(true),
  };
  const dialogSpy = {
    open: vi.fn(),
  };
  const snackBarSpy = {
    open: vi.fn(),
  };

  const summaryMock = {
    total_startups: 2,
    revenue: 100000,
    revenue_variation_pct: 25,
    revenue_variation_direction: 'up' as const,
    health: { healthy: 1, warning: 1, critical: 0 },
    monthly_report_pct: 50,
    routines_up_to_date_pct: 50,
    startups: [],
  };

  beforeEach(async () => {
    queryParamMap$ = new BehaviorSubject(convertToParamMap({ month: '2', year: '2026' }));
    portfolioServiceSpy.getSummary.mockReturnValue(of(summaryMock));

    await TestBed.configureTestingModule({
      imports: [Portfolio],
      providers: [
        provideNoopAnimations(),
        { provide: PortfolioService, useValue: portfolioServiceSpy },
        { provide: StartupService, useValue: startupServiceSpy },
        { provide: Router, useValue: routerSpy },
        { provide: MatDialog, useValue: dialogSpy },
        { provide: MatSnackBar, useValue: snackBarSpy },
        { provide: ActivatedRoute, useValue: { queryParamMap: queryParamMap$.asObservable() } },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(Portfolio);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should load summary for selected query period', () => {
    expect(portfolioServiceSpy.getSummary).toHaveBeenCalledWith(2, 2026);
    expect(component.selectedMonth()).toBe(2);
    expect(component.selectedYear()).toBe(2026);
  });

  it('should default to previous month when query params are missing', () => {
    routerSpy.navigate.mockClear();
    const now = new Date();
    const expected = now.getMonth() === 0
      ? { month: 12, year: now.getFullYear() - 1 }
      : { month: now.getMonth(), year: now.getFullYear() };

    queryParamMap$.next(convertToParamMap({}));
    fixture.detectChanges();

    expect(routerSpy.navigate).toHaveBeenCalledWith([], {
      relativeTo: TestBed.inject(ActivatedRoute),
      queryParams: expected,
      replaceUrl: true,
    });
  });

  it('should navigate to previous month in same year', () => {
    routerSpy.navigate.mockClear();
    component.selectedMonth.set(3);
    component.selectedYear.set(2026);

    component.goToPreviousMonth();

    expect(routerSpy.navigate).toHaveBeenCalledWith([], {
      relativeTo: TestBed.inject(ActivatedRoute),
      queryParams: { month: 2, year: 2026 },
      replaceUrl: false,
    });
  });

  it('should navigate to previous month and previous year from january', () => {
    routerSpy.navigate.mockClear();
    component.selectedMonth.set(1);
    component.selectedYear.set(2026);

    component.goToPreviousMonth();

    expect(routerSpy.navigate).toHaveBeenCalledWith([], {
      relativeTo: TestBed.inject(ActivatedRoute),
      queryParams: { month: 12, year: 2025 },
      replaceUrl: false,
    });
  });

  it('should navigate to next month when selected month is not current', () => {
    routerSpy.navigate.mockClear();
    component.selectedMonth.set(11);
    component.selectedYear.set(2025);

    component.goToNextMonth();

    expect(routerSpy.navigate).toHaveBeenCalledWith([], {
      relativeTo: TestBed.inject(ActivatedRoute),
      queryParams: { month: 12, year: 2025 },
      replaceUrl: false,
    });
  });

  it('should not navigate to next month when current month is selected', () => {
    routerSpy.navigate.mockClear();
    const now = new Date();
    component.selectedMonth.set(now.getMonth() + 1);
    component.selectedYear.set(now.getFullYear());

    component.goToNextMonth();

    expect(routerSpy.navigate).not.toHaveBeenCalled();
  });

  it('should expose positive revenue trend data for card rendering', () => {
    expect(component.revenueCardTone()).toBe('positive');
    expect(component.revenueTrendIcon()).toBe('trending_up');
    expect(component.revenueVariationLabel()).toContain('+25.0%');
  });

  it('should return "Sem base" label when there is no previous-month base', () => {
    portfolioServiceSpy.getSummary.mockReturnValue(
      of({
        ...summaryMock,
        revenue_variation_pct: null,
        revenue_variation_direction: 'neutral' as const,
      }),
    );
    queryParamMap$.next(convertToParamMap({ month: '2', year: '2026' }));
    fixture.detectChanges();

    expect(component.revenueCardTone()).toBe('neutral');
    expect(component.revenueTrendIcon()).toBe('trending_flat');
    expect(component.revenueVariationLabel()).toBe('Sem base');
  });
});
