import { TestBed } from '@angular/core/testing';
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
