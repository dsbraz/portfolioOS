import { TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { NEVER, of } from 'rxjs';
import { ActivatedRoute, Router } from '@angular/router';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';

import { StartupDetail } from './startup-detail';
import { StartupService } from '../../../services/startup.service';
import { MonthlyIndicatorService } from '../../../services/monthly-indicator.service';
import { BoardMeetingService } from '../../../services/board-meeting.service';
import { ExecutiveService } from '../../../services/executive.service';
import { MonthlyIndicatorTokenService } from '../../../services/monthly-indicator-token.service';
import { MonthlyIndicator } from '../../../models/monthly-indicator.model';
import { Startup, StartupStatus } from '../../../models/startup.model';
import { participationValue } from '../../../models/participation';

describe('StartupDetail (totalParticipation)', () => {
  let component: StartupDetail;
  // Reference is the latest reported indicator; the list arrives API-sorted desc.
  const REF_YEAR = 2026;

  const baseStartup = (equityStake: number | null): Startup => ({
    id: 's1',
    name: 'Acme',
    site: null,
    logo_url: null,
    status: StartupStatus.HEALTHY,
    sector: 'Fintech',
    investment_date: '2025-01-01',
    equity_stake: equityStake,
    notes: null,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  });

  const indicator = (m: number, y: number, revenue: number | null): MonthlyIndicator =>
    ({
      id: `${y}-${m}`,
      startup_id: 's1',
      month: m,
      year: y,
      total_revenue: revenue,
      recurring_revenue_pct: null,
      gross_margin_pct: null,
      cash_balance: null,
      headcount: null,
      ebitda_burn: null,
      achievements: null,
      challenges: null,
      comments: null,
      created_at: '',
      updated_at: '',
    });

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        { provide: ActivatedRoute, useValue: { snapshot: { paramMap: { get: () => 's1' } } } },
        { provide: Router, useValue: {} },
        { provide: MatDialog, useValue: {} },
        { provide: MatSnackBar, useValue: {} },
        { provide: StartupService, useValue: {} },
        { provide: MonthlyIndicatorService, useValue: {} },
        { provide: BoardMeetingService, useValue: {} },
        { provide: ExecutiveService, useValue: {} },
        { provide: MonthlyIndicatorTokenService, useValue: {} },
      ],
    });
    component = TestBed.createComponent(StartupDetail).componentInstance;
  });

  it('accumulates revenue of the latest indicator year up to its month', () => {
    component.startup.set(baseStartup(5));
    // latestIndicator = first item (April 2026).
    component.indicators.set([
      indicator(4, REF_YEAR, 50000),
      indicator(1, REF_YEAR, 100000),
      indicator(12, REF_YEAR - 1, 999999), // previous year => excluded
    ]);

    // (100000 + 50000) accumulated over 4 months.
    expect(component.totalParticipation).toBe(participationValue(150000, 4, 5));
  });

  it('sums Decimal-as-string revenues without producing NaN', () => {
    // Regression: the API serializes total_revenue as a JSON string.
    component.startup.set(baseStartup(5));
    component.indicators.set([
      indicator(2, REF_YEAR, '50000.00' as any),
      indicator(1, REF_YEAR, '100000.00' as any),
    ]);

    const result = component.totalParticipation;
    expect(Number.isNaN(result as number)).toBe(false);
    expect(result).toBe(participationValue(150000, 2, 5));
  });

  it('treats null revenue within the reference year as zero', () => {
    component.startup.set(baseStartup(5));
    component.indicators.set([indicator(4, REF_YEAR, null), indicator(1, REF_YEAR, 100000)]);

    // Reference month is 4 (latest), accumulated revenue is 100000.
    expect(component.totalParticipation).toBe(participationValue(100000, 4, 5));
  });

  it('returns zero (not null) when equity stake is zero', () => {
    component.startup.set(baseStartup(0));
    component.indicators.set([indicator(1, REF_YEAR, 100000)]);

    expect(component.totalParticipation).toBe(0);
  });

  it('returns null when there is no equity stake', () => {
    component.startup.set(baseStartup(null));
    component.indicators.set([indicator(1, REF_YEAR, 100000)]);

    expect(component.totalParticipation).toBeNull();
  });

  it('returns null when there are no indicators', () => {
    component.startup.set(baseStartup(5));
    component.indicators.set([]);

    expect(component.totalParticipation).toBeNull();
  });
});

describe('StartupDetail (loading and ARIA)', () => {
  const startup: Startup = {
    id: 's1',
    name: 'Acme',
    site: null,
    logo_url: null,
    status: StartupStatus.HEALTHY,
    sector: 'Fintech',
    investment_date: '2025-01-01',
    equity_stake: 5,
    notes: null,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  };

  const page = (items: unknown[]) => ({ items, total: items.length });

  /** `pending` keeps the calls from emitting, which is the loading state. */
  const mount = async (pending = false) => {
    const respond = <T,>(value: T) => (pending ? NEVER : of(value));

    TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      imports: [StartupDetail],
      providers: [
        provideNoopAnimations(),
        { provide: ActivatedRoute, useValue: { snapshot: { paramMap: { get: () => 's1' } } } },
        { provide: Router, useValue: {} },
        { provide: MatDialog, useValue: {} },
        { provide: MatSnackBar, useValue: { open: vi.fn() } },
        { provide: StartupService, useValue: { getById: () => respond(startup) } },
        {
          provide: MonthlyIndicatorService,
          useValue: { list: () => respond(page([indicatorFixture])) },
        },
        { provide: BoardMeetingService, useValue: { list: () => respond(page([])) } },
        { provide: ExecutiveService, useValue: { list: () => respond(page([])) } },
        { provide: MonthlyIndicatorTokenService, useValue: { list: () => respond(page([])) } },
      ],
    }).compileComponents();

    const fixture = TestBed.createComponent(StartupDetail);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  };

  const indicatorFixture: MonthlyIndicator = {
    id: 'i1',
    startup_id: 's1',
    month: 7,
    year: 2026,
    total_revenue: 1000,
    recurring_revenue_pct: null,
    gross_margin_pct: null,
    cash_balance: null,
    headcount: null,
    ebitda_burn: null,
    achievements: null,
    challenges: null,
    comments: null,
    created_at: '',
    updated_at: '',
  };

  // The page used to render NOTHING while loading, and an empty container is
  // indistinguishable from "no data" — for anyone reading the screen and for
  // any agent that scrapes the DOM too early.
  it('should announce that it is loading instead of rendering an empty page', async () => {
    const el = await mount(true);

    expect(el.querySelector('[aria-busy="true"]')).toBeTruthy();
    expect(el.querySelector('[role="status"]')?.textContent).toContain('Carregando');
    expect(el.querySelector('[role="tabpanel"]')).toBeNull();
  });

  it('should drop the busy state once the data arrives', async () => {
    const el = await mount();

    expect(el.querySelector('[aria-busy="true"]')).toBeNull();
    expect(el.querySelector('h1')?.textContent).toContain('Acme');
  });

  // Regression: the tabs declare `aria-controls`, but only the active panel was
  // rendered — two of the three references pointed to non-existent ids.
  it('should point every tab at a panel that exists', async () => {
    const el = await mount();

    const tabs = [...el.querySelectorAll('[role="tab"]')];
    expect(tabs.length).toBe(3);

    for (const tab of tabs) {
      const id = tab.getAttribute('aria-controls');
      expect(id).toBeTruthy();
      expect(el.querySelector(`#${id}`)).toBeTruthy();
    }
  });

  it('should keep only the selected panel visible', async () => {
    const el = await mount();

    const panels = [...el.querySelectorAll('[role="tabpanel"]')];
    expect(panels.length).toBe(3);
    expect(panels.filter(p => !p.hasAttribute('hidden')).length).toBe(1);
  });

  // Three identical `more_vert` buttons per table showed up as unlabeled
  // "button": nothing told apart the row each one belongs to.
  it('should name every row action button with its row', async () => {
    const el = await mount();

    const actions = [...el.querySelectorAll('button[mat-icon-button][aria-haspopup], button[mat-icon-button]')]
      .filter(b => b.closest('td'));
    expect(actions.length).toBeGreaterThan(0);
    for (const button of actions) {
      expect(button.getAttribute('aria-label')).toBeTruthy();
    }
    expect(el.querySelector('td button[mat-icon-button]')?.getAttribute('aria-label'))
      .toBe('Ações do indicador de Jul/2026');
  });
});

describe('StartupDetail (sorting)', () => {
  const create = () => {
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      providers: [
        { provide: ActivatedRoute, useValue: { snapshot: { paramMap: { get: () => 's1' } } } },
        { provide: Router, useValue: {} },
        { provide: MatDialog, useValue: {} },
        { provide: MatSnackBar, useValue: {} },
        { provide: StartupService, useValue: {} },
        { provide: MonthlyIndicatorService, useValue: {} },
        { provide: BoardMeetingService, useValue: {} },
        { provide: ExecutiveService, useValue: {} },
        { provide: MonthlyIndicatorTokenService, useValue: {} },
      ],
    });
    return TestBed.createComponent(StartupDetail).componentInstance;
  };

  const ind = (m: number, y: number, revenue: number | null = null): MonthlyIndicator =>
    ({
      id: `${y}-${m}`, startup_id: 's1', month: m, year: y,
      total_revenue: revenue, recurring_revenue_pct: null, gross_margin_pct: null,
      cash_balance: null, headcount: null, ebitda_burn: null,
      achievements: null, challenges: null, comments: null,
      created_at: '', updated_at: '',
    });

  // "Período" shows `Jul/2026`. Sorted as text, Ago would come before Jul and
  // Dez before Fev — the column must sort by what it IS.
  it('should sort the period column chronologically, not alphabetically', () => {
    const component = create();
    component.indicators.set([ind(7, 2026), ind(8, 2026), ind(12, 2025), ind(2, 2026)]);
    component.indicatorSort.set({ active: 'period', direction: 'asc' });

    expect(component.sortedIndicators().map(i => `${i.month}/${i.year}`))
      .toEqual(['12/2025', '2/2026', '7/2026', '8/2026']);
  });

  it('should keep indicators without revenue last when sorting by revenue', () => {
    const component = create();
    component.indicators.set([ind(1, 2026, null), ind(2, 2026, 500), ind(3, 2026, 100)]);
    component.indicatorSort.set({ active: 'total_revenue', direction: 'desc' });

    expect(component.sortedIndicators().map(i => i.total_revenue)).toEqual([500, 100, null]);
  });

  it('should leave the rows untouched while no column is active', () => {
    const component = create();
    const rows = [ind(2, 2026), ind(1, 2026)];
    component.indicators.set(rows);

    expect(component.sortedIndicators().map(i => i.month)).toEqual([2, 1]);
  });
});
