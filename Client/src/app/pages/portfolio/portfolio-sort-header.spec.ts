import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { ActivatedRoute, Router, convertToParamMap } from '@angular/router';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { of } from 'rxjs';

import { Portfolio } from './portfolio';
import { PortfolioSummary } from '../../models/portfolio.model';
import { PortfolioService } from '../../services/portfolio.service';
import { StartupService } from '../../services/startup.service';

// The sorting rules are covered by setting `sort` directly; these tests cover
// the other half: that clicking a real `mat-sort-header` reaches that signal.
describe('Portfolio (sort header wiring)', () => {
  const item = (name: string, revenue: number | null) => ({
    startup: { id: name, name, status: 'saudavel', sector: 'Fintech', equity_stake: null },
    total_revenue: revenue,
    cash_balance: null,
    ebitda_burn: null,
    headcount: null,
    accumulated_revenue_ytd: null,
    last_reported_year: 2026,
    last_reported_month: 7,
  });

  // Deliberately in neither ascending nor descending order for any column.
  const startups = [item('Bravo', 300), item('Alfa', 100), item('Charlie', 200)];

  let fixture: ComponentFixture<Portfolio>;
  let el: HTMLElement;

  const header = (label: string) =>
    [...el.querySelectorAll('th')].find((th) => th.textContent?.includes(label))!;

  const clickHeader = (label: string) => {
    (header(label).querySelector('.mat-sort-header-container') as HTMLElement).click();
    fixture.detectChanges();
  };

  const rowNames = () =>
    [...el.querySelectorAll('tr[mat-row] .startup-name')].map((n) => n.textContent?.trim());

  beforeEach(async () => {
    TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      imports: [Portfolio],
      providers: [
        provideNoopAnimations(),
        {
          provide: ActivatedRoute,
          useValue: { queryParamMap: of(convertToParamMap({ month: '7', year: '2026' })) },
        },
        { provide: Router, useValue: { navigate: vi.fn().mockResolvedValue(true) } },
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
                health: { healthy: startups.length, warning: 0, critical: 0 },
                monthly_report_pct: 100,
                routines_up_to_date_pct: 100,
                startups,
              } as unknown as PortfolioSummary),
          },
        },
        { provide: StartupService, useValue: { create: vi.fn() } },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(Portfolio);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    el = fixture.nativeElement as HTMLElement;
  });

  it('should keep the API order and aria-sort "none" before any header is clicked', () => {
    expect(rowNames()).toEqual(['Bravo', 'Alfa', 'Charlie']);
    expect(header('Startup').getAttribute('aria-sort')).toBe('none');
  });

  it('should sort by name ascending, then descending, as the header is clicked', () => {
    clickHeader('Startup');
    expect(header('Startup').getAttribute('aria-sort')).toBe('ascending');
    expect(rowNames()).toEqual(['Alfa', 'Bravo', 'Charlie']);

    clickHeader('Startup');
    expect(header('Startup').getAttribute('aria-sort')).toBe('descending');
    expect(rowNames()).toEqual(['Charlie', 'Bravo', 'Alfa']);
  });

  it('should move aria-sort to the newly clicked column', () => {
    clickHeader('Startup');
    clickHeader('Receita');

    expect(header('Startup').getAttribute('aria-sort')).toBe('none');
    expect(header('Receita').getAttribute('aria-sort')).toBe('ascending');
    expect(rowNames()).toEqual(['Alfa', 'Charlie', 'Bravo']);
  });
});
