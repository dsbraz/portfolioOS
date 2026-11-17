import { TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { ActivatedRoute, Router, convertToParamMap } from '@angular/router';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { BehaviorSubject, Observable, Subject, of, throwError } from 'rxjs';

import { Portfolio } from './portfolio';
import { PortfolioSummary } from '../../models/portfolio.model';
import { ExitType, Startup, StartupListResponse, StartupStatus } from '../../models/startup.model';
import { PortfolioService } from '../../services/portfolio.service';
import { StartupService } from '../../services/startup.service';

const routerStub = () => ({
  navigate: vi.fn().mockResolvedValue(true),
  createUrlTree: vi.fn((commands: unknown[]) => commands),
  serializeUrl: vi.fn((tree: unknown) => (tree as unknown[]).join('/')),
  events: new Subject<unknown>(),
});

const emptySummary: PortfolioSummary = {
  total_startups: 0,
  revenue: 0,
  revenue_variation_pct: null,
  revenue_variation_direction: 'neutral',
  health: { healthy: 0, warning: 0, critical: 0 },
  monthly_report_pct: 0,
  routines_up_to_date_pct: 0,
  startups: [],
};

const exited: Startup = {
  id: 'x1',
  name: 'Vendida SA',
  site: null,
  logo_url: null,
  status: StartupStatus.HEALTHY,
  sector: 'Fintech',
  investment_date: '2024-01-10',
  equity_stake: 5,
  notes: null,
  exited_on: '2026-03-20',
  exit_type: ExitType.SALE,
  exit_notes: null,
  monthly_report_enabled: false,
  created_at: '',
  updated_at: '',
};

// Exited startups leave the monitoring but must stay reachable: the section
// below the table is the only way back to their history.
describe('Portfolio (exited startups)', () => {
  const period = new BehaviorSubject(convertToParamMap({ month: '7', year: '2026' }));
  beforeEach(() => period.next(convertToParamMap({ month: '7', year: '2026' })));
  const mount = async (list: () => Observable<StartupListResponse>) => {
    const startupService = { create: vi.fn(), list: vi.fn(list) };
    TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      imports: [Portfolio],
      providers: [
        provideNoopAnimations(),
        {
          provide: ActivatedRoute,
          useValue: { queryParamMap: period },
        },
        { provide: Router, useValue: routerStub() },
        { provide: MatDialog, useValue: { open: vi.fn() } },
        { provide: MatSnackBar, useValue: { open: vi.fn() } },
        { provide: PortfolioService, useValue: { getSummary: () => of(emptySummary) } },
        { provide: StartupService, useValue: startupService },
      ],
    }).compileComponents();

    const fixture = TestBed.createComponent(Portfolio);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    return { el: fixture.nativeElement as HTMLElement, startupService, fixture };
  };

  const section = (el: HTMLElement) =>
    el.querySelector<HTMLElement>('section[aria-labelledby="exited-title"]')!;

  it('moves the exited list with the selected month, including the exit month', async () => {
    const { el, fixture } = await mount(() => of({ items: [exited], total: 1 }));
    for (const [month, year, visible] of [[2, 2026, false], [3, 2026, true], [4, 2026, true], [12, 2025, false]] as const) {
      period.next(convertToParamMap({ month: String(month), year: String(year) }));
      fixture.detectChanges();
      await fixture.whenStable();
      expect(section(el).textContent?.includes('Vendida SA')).toBe(visible);
    }
  });

  it('asks only for the exited startups', async () => {
    const { startupService } = await mount(() => of({ items: [], total: 0 }));

    expect(startupService.list).toHaveBeenCalledWith({ tracked: false });
  });

  it('lists each exited startup with a link, the exit date and its type', async () => {
    const { el } = await mount(() => of({ items: [exited], total: 1 }));

    const table = section(el).querySelector('table')!;
    expect(table.querySelector('caption')?.textContent).toContain('deixaram de ser acompanhadas');
    const link = table.querySelector('a')!;
    expect(link.textContent?.trim()).toBe('Vendida SA');
    const cells = [...table.querySelectorAll('td')].map((td) => td.textContent?.trim());
    expect(cells).toEqual(['Vendida SA', '20/03/2026', 'Venda (M&A ou secundária)']);
  });

  it('does not call the portfolio empty when every startup has exited', async () => {
    const { el } = await mount(() => of({ items: [exited], total: 1 }));

    expect(el.textContent).toContain('Nenhuma startup acompanhada neste período');
    expect(el.textContent).not.toContain('Nenhuma startup cadastrada');
  });

  it('does not claim the portfolio is empty while the exited list is unknown', async () => {
    const { el } = await mount(() => throwError(() => new Error('boom')));

    expect(el.textContent).toContain('Nenhuma startup acompanhada neste período');
    expect(el.textContent).not.toContain('Nenhuma startup cadastrada');
  });

  it('describes an empty period without claiming no startups exist', async () => {
    const { el } = await mount(() => of({ items: [], total: 0 }));

    expect(el.textContent).toContain('Nenhuma startup acompanhada neste período');
  });

  it('says so when no startup has exited', async () => {
    const { el } = await mount(() => of({ items: [], total: 0 }));

    expect(section(el).textContent).toContain('Nenhuma startup encerrada.');
    expect(section(el).querySelector('table')).toBeNull();
  });

  it('says so when the list fails, instead of looking empty', async () => {
    const { el } = await mount(() => throwError(() => new Error('boom')));

    expect(section(el).querySelector('[role="status"]')?.textContent).toContain(
      'Não foi possível carregar',
    );
  });
});
