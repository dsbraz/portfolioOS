import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { ActivatedRoute, ParamMap, Router, convertToParamMap } from '@angular/router';
import { BehaviorSubject, NEVER, Observable, Subject, of, throwError } from 'rxjs';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';

import { Portfolio } from './portfolio';
import { PortfolioSummary } from '../../models/portfolio.model';
import { PortfolioService } from '../../services/portfolio.service';
import { StartupService } from '../../services/startup.service';

// `routerLink` on the startup name builds and serializes an href and subscribes
// to navigation events, so the stub needs more than `navigate`.
const routerStub = () => ({
  navigate: vi.fn().mockResolvedValue(true),
  createUrlTree: vi.fn((commands: unknown[]) => commands),
  serializeUrl: vi.fn((tree: unknown) => (tree as unknown[]).join('/')),
  events: new Subject<unknown>(),
});

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
  const routerSpy = routerStub();
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
    const expected =
      now.getMonth() === 0
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

  it('should compute total participation as the annualized revenue multiple across startups', () => {
    const startups = [
      {
        startup: { id: 'a', name: 'Alpha', status: 'saudavel', equity_stake: 5 },
        total_revenue: 50000,
        cash_balance: null,
        ebitda_burn: null,
        headcount: null,
        accumulated_revenue_ytd: 200000,
      },
      {
        startup: { id: 'b', name: 'Beta', status: 'atencao', equity_stake: null },
        total_revenue: 10000,
        cash_balance: null,
        ebitda_burn: null,
        headcount: null,
        accumulated_revenue_ytd: 80000,
      },
    ];
    portfolioServiceSpy.getSummary.mockReturnValue(of({ ...summaryMock, startups } as any));
    queryParamMap$.next(convertToParamMap({ month: '2', year: '2026' }));
    fixture.detectChanges();

    // selectedMonth = 2 => (200000 / 2) * 12 * 5 * 0.05 = 300000; startup b has no equity => 0
    expect(component.totalParticipation()).toBe(300000);
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

  it('should preserve the table language used by browser-operated skills', () => {
    portfolioServiceSpy.getSummary.mockReturnValue(
      of({
        ...summaryMock,
        startups: [
          {
            startup: { id: 'a', name: 'Alpha', status: 'saudavel', equity_stake: 5 },
            total_revenue: 1000,
            cash_balance: 500,
            ebitda_burn: -100,
            headcount: 8,
            accumulated_revenue_ytd: 3000,
            last_reported_year: 2026,
            last_reported_month: 4,
          },
          {
            startup: { id: 'b', name: 'Beta', status: 'atencao', equity_stake: null },
            total_revenue: null,
            cash_balance: null,
            ebitda_burn: null,
            headcount: null,
            accumulated_revenue_ytd: null,
            last_reported_year: null,
            last_reported_month: null,
          },
        ],
      } as PortfolioSummary),
    );
    queryParamMap$.next(convertToParamMap({ month: '7', year: '2026' }));
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    const headers = [...el.querySelectorAll('th')].map((header) => header.textContent?.trim());
    expect(headers).toEqual(['Startup', 'Status', 'Receita', 'Caixa', 'EBITDA/Burn', 'Headcount']);
    // A pointer-only row is unreachable by keyboard; the name is the real
    // control, and it is a link because the action is a navigation.
    const opener = el.querySelector<HTMLAnchorElement>('.row-opener');
    expect(opener?.tagName).toBe('A');
    expect(opener?.textContent?.trim()).toBeTruthy();

    expect(el.textContent).toContain('Último: Abr/2026');
    expect(el.textContent).toContain('Nunca reportou');
  });
});

describe('Portfolio (loading state)', () => {
  // Regression: without a loading branch the page rendered an empty container,
  // indistinguishable from "no startups registered".
  const mount = async (pending: boolean) => {
    TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      imports: [Portfolio],
      providers: [
        provideNoopAnimations(),
        {
          provide: ActivatedRoute,
          useValue: { queryParamMap: of(convertToParamMap({ month: '7', year: '2026' })) },
        },
        { provide: Router, useValue: routerStub() },
        { provide: MatDialog, useValue: { open: vi.fn() } },
        { provide: MatSnackBar, useValue: { open: vi.fn() } },
        {
          provide: PortfolioService,
          useValue: {
            getSummary: () =>
              pending
                ? NEVER
                : of({
                    total_startups: 0,
                    revenue: 0,
                    revenue_variation_pct: null,
                    revenue_variation_direction: 'neutral',
                    health: { healthy: 0, warning: 0, critical: 0 },
                    monthly_report_pct: 0,
                    routines_up_to_date_pct: 0,
                    startups: [],
                  } as PortfolioSummary),
          },
        },
        { provide: StartupService, useValue: { create: vi.fn() } },
      ],
    }).compileComponents();

    const fixture = TestBed.createComponent(Portfolio);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  };

  it('should announce that it is loading instead of rendering an empty page', async () => {
    const el = await mount(true);
    expect(el.querySelector('[aria-busy="true"]')).toBeTruthy();
    expect(el.querySelector('[role="status"]')?.textContent).toContain('Carregando');
  });

  it('should drop the busy state and show the empty state once loaded', async () => {
    const el = await mount(false);
    expect(el.querySelector('[aria-busy="true"]')).toBeNull();
    expect(el.textContent).toContain('Nenhuma startup cadastrada');
  });
});

describe('Portfolio (sorting)', () => {
  const create = async (startups: unknown[]) => {
    TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      imports: [Portfolio],
      providers: [
        provideNoopAnimations(),
        {
          provide: ActivatedRoute,
          useValue: { queryParamMap: of(convertToParamMap({ month: '7', year: '2026' })) },
        },
        { provide: Router, useValue: routerStub() },
        { provide: MatDialog, useValue: { open: vi.fn() } },
        { provide: MatSnackBar, useValue: { open: vi.fn() } },
        {
          provide: PortfolioService,
          useValue: {
            getSummary: () =>
              of({
                total_startups: startups.length,
                revenue: 0,
                revenue_variation_pct: null,
                revenue_variation_direction: 'neutral',
                health: { healthy: 0, warning: 0, critical: 0 },
                monthly_report_pct: 0,
                routines_up_to_date_pct: 0,
                startups,
              } as unknown as PortfolioSummary),
          },
        },
        { provide: StartupService, useValue: { create: vi.fn() } },
      ],
    }).compileComponents();

    const fixture = TestBed.createComponent(Portfolio);
    fixture.detectChanges();
    return fixture.componentInstance;
  };

  const item = (name: string, status: string, revenue: number | string | null) => ({
    startup: { id: name, name, status, equity_stake: null },
    total_revenue: revenue,
    cash_balance: null,
    ebitda_burn: null,
    headcount: null,
    accumulated_revenue_ytd: null,
  });

  // The API serializes Decimal as a string. Sorting that as text would put
  // "9.00" after "100.00".
  it('should sort revenue numerically even when it arrives as a string', async () => {
    const component = await create([
      item('a', 'saudavel', '9.00'),
      item('b', 'saudavel', '100.00'),
      item('c', 'saudavel', '20.00'),
    ]);
    component.sort.set({ active: 'total_revenue', direction: 'asc' });

    expect(component.sortedStartups().map((i) => i.startup.name)).toEqual(['a', 'c', 'b']);
  });

  // Status is ORDINAL: sorting by label would give "Atenção, Crítico, Saudável",
  // which describes nothing. Ascending puts the healthiest first.
  it('should sort status by severity, not by label', async () => {
    const component = await create([
      item('c', 'critico', 1),
      item('s', 'saudavel', 1),
      item('a', 'atencao', 1),
    ]);
    component.sort.set({ active: 'status', direction: 'asc' });

    expect(component.sortedStartups().map((i) => i.startup.name)).toEqual(['s', 'a', 'c']);
  });

  // Without a pt-BR collator, "Ávila" would land after "Zago".
  it('should sort names ignoring accents', async () => {
    const component = await create([
      item('Zago', 'saudavel', 1),
      item('Ávila', 'saudavel', 1),
      item('Grão Verde', 'saudavel', 1),
    ]);
    component.sort.set({ active: 'name', direction: 'asc' });

    expect(component.sortedStartups().map((i) => i.startup.name)).toEqual([
      'Ávila',
      'Grão Verde',
      'Zago',
    ]);
  });
});

describe('Portfolio (report state in the status column)', () => {
  const item = (name: string, lastYear: number | null, lastMonth: number | null) => ({
    startup: { id: name, name, status: 'saudavel', equity_stake: null },
    total_revenue: null,
    cash_balance: null,
    ebitda_burn: null,
    headcount: null,
    accumulated_revenue_ytd: null,
    last_reported_year: lastYear,
    last_reported_month: lastMonth,
  });

  const mount = async () => {
    TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      imports: [Portfolio],
      providers: [
        provideNoopAnimations(),
        {
          provide: ActivatedRoute,
          useValue: { queryParamMap: of(convertToParamMap({ month: '7', year: '2026' })) },
        },
        { provide: Router, useValue: routerStub() },
        { provide: MatDialog, useValue: { open: vi.fn() } },
        { provide: MatSnackBar, useValue: { open: vi.fn() } },
        {
          provide: PortfolioService,
          useValue: {
            getSummary: () =>
              of({
                total_startups: 0,
                revenue: 0,
                revenue_variation_pct: null,
                revenue_variation_direction: 'neutral',
                health: { healthy: 0, warning: 0, critical: 0 },
                monthly_report_pct: 0,
                routines_up_to_date_pct: 0,
                startups: [],
              } as unknown as PortfolioSummary),
          },
        },
        { provide: StartupService, useValue: { create: vi.fn() } },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(Portfolio);
    fixture.detectChanges();
    return fixture.componentInstance;
  };

  // Reported in the period: the whole row ALREADY is its report, and repeating
  // the date would be noise in a table where only outliers deserve ink.
  it('should stay silent when the startup reported in the selected period', async () => {
    const component = await mount();
    expect(component.reportLabel(item('a', 2026, 7) as never)).toBeNull();
  });

  it('should name the last reported period when the month is missing', async () => {
    const component = await mount();
    expect(component.reportLabel(item('a', 2026, 4) as never)).toBe('Último: Abr/2026');
  });

  it('should say so when the startup never reported', async () => {
    const component = await mount();
    expect(component.reportLabel(item('a', null, null) as never)).toBe('Nunca reportou');
  });

  // Regression: inferring "reported" from null fields is a heuristic — a report
  // submitted blank would fall into it and show up as missing.
  it('should treat a blank report as reported', async () => {
    const component = await mount();
    const blank = { ...item('a', 2026, 7), total_revenue: null, headcount: null };
    expect(component.reportLabel(blank as never)).toBeNull();
  });
});

describe('Portfolio (refresh when the period changes)', () => {
  const summary = (name: string): PortfolioSummary =>
    ({
      total_startups: 1,
      revenue: 0,
      revenue_variation_pct: null,
      revenue_variation_direction: 'neutral',
      health: { healthy: 1, warning: 0, critical: 0 },
      monthly_report_pct: 0,
      routines_up_to_date_pct: 0,
      startups: [
        {
          startup: { id: 'a', name, status: 'saudavel', equity_stake: null },
          total_revenue: 1000,
          cash_balance: null,
          ebitda_burn: null,
          headcount: null,
          accumulated_revenue_ytd: null,
          last_reported_month: 7,
          last_reported_year: 2026,
        },
      ],
    }) as unknown as PortfolioSummary;

  let getSummary: (month: number, year: number) => Observable<PortfolioSummary>;

  const mount = async () => {
    getSummary = () => of(summary('Alpha'));
    TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      imports: [Portfolio],
      providers: [
        provideNoopAnimations(),
        {
          provide: ActivatedRoute,
          useValue: { queryParamMap: of(convertToParamMap({ month: '7', year: '2026' })) },
        },
        { provide: Router, useValue: routerStub() },
        { provide: MatDialog, useValue: { open: vi.fn() } },
        { provide: MatSnackBar, useValue: { open: vi.fn() } },
        {
          provide: PortfolioService,
          useValue: { getSummary: (month: number, year: number) => getSummary(month, year) },
        },
        { provide: StartupService, useValue: { create: vi.fn() } },
      ],
    }).compileComponents();

    const fixture = TestBed.createComponent(Portfolio);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    return fixture;
  };

  const reloadPeriod = (fixture: ComponentFixture<Portfolio>, month: number) => {
    fixture.componentInstance.selectedMonth.set(month);
    fixture.componentInstance.loadSummary();
    fixture.detectChanges();
  };

  // Regression: a refresh swapped the content for a spinner, which reset the
  // table's sort header while the rows stayed sorted.
  it('should keep the rows and the sort header when the same period refreshes', async () => {
    const fixture = await mount();
    const el = fixture.nativeElement as HTMLElement;
    const row = el.querySelector('tr.mat-mdc-row');
    const nameHeader = el.querySelector('th .mat-sort-header-container') as HTMLElement;
    nameHeader.click();
    fixture.detectChanges();
    const sort = nameHeader.closest('th')!.getAttribute('aria-sort');
    expect(sort).toBe('ascending');

    getSummary = () => NEVER;
    fixture.componentInstance.loadSummary();
    fixture.detectChanges();

    expect(el.querySelector('[aria-busy="true"]')).toBeTruthy();
    expect(el.querySelector('tr.mat-mdc-row')).toBe(row);
    expect(el.querySelector('th[aria-sort="ascending"]')).toBeTruthy();
  });

  // Another period's numbers must never show under the new period's label.
  it('should show loading, not the previous period, while another period loads', async () => {
    const fixture = await mount();
    const el = fixture.nativeElement as HTMLElement;

    getSummary = () => NEVER;
    reloadPeriod(fixture, 6);

    expect(el.textContent).not.toContain('Alpha');
    expect(el.querySelector('[role="status"]')?.textContent).toContain('Carregando');
  });

  it('should keep valid data when refreshing the same period fails', async () => {
    const fixture = await mount();
    const el = fixture.nativeElement as HTMLElement;

    getSummary = () => throwError(() => ({ error: { detail: 'falhou' } }));
    fixture.componentInstance.loadSummary();
    fixture.detectChanges();

    expect(el.textContent).toContain('Alpha');
  });

  it('should show the failure when another period fails to load', async () => {
    const fixture = await mount();
    const el = fixture.nativeElement as HTMLElement;

    getSummary = () => throwError(() => ({ error: { detail: 'falhou' } }));
    reloadPeriod(fixture, 6);

    expect(el.textContent).not.toContain('Alpha');
    expect(el.querySelector('[role="status"]')?.textContent).toContain('Não foi possível');
  });

  // Clicking "previous month" twice: the older request must not land last and
  // leave its numbers under the newer period's label.
  it('should ignore a response for a period that is no longer selected', async () => {
    const fixture = await mount();
    const el = fixture.nativeElement as HTMLElement;
    const june = new Subject<PortfolioSummary>();
    const may = new Subject<PortfolioSummary>();
    getSummary = (month) => (month === 6 ? june : may);

    reloadPeriod(fixture, 6);
    reloadPeriod(fixture, 5);
    june.next(summary('Junho'));
    fixture.detectChanges();

    expect(el.textContent).not.toContain('Junho');
    may.next(summary('Maio'));
    fixture.detectChanges();
    expect(el.textContent).toContain('Maio');
  });
});
