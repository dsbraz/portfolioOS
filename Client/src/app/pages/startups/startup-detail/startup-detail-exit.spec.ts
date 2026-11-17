import { TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { ActivatedRoute, Router } from '@angular/router';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { of } from 'rxjs';

import { StartupDetail } from './startup-detail';
import { StartupService } from '../../../services/startup.service';
import { MonthlyIndicatorService } from '../../../services/monthly-indicator.service';
import { BoardMeetingService } from '../../../services/board-meeting.service';
import { ExecutiveService } from '../../../services/executive.service';
import { MonthlyIndicatorTokenService } from '../../../services/monthly-indicator-token.service';
import { ExitType, Startup, StartupStatus } from '../../../models/startup.model';

// An exited startup stops being chased, but its record stays readable.
describe('StartupDetail (exit)', () => {
  const base: Startup = {
    id: 's1',
    name: 'Acme',
    site: null,
    logo_url: null,
    status: StartupStatus.HEALTHY,
    sector: 'Fintech',
    investment_date: '2025-01-01',
    equity_stake: 5,
    notes: null,
    exited_on: null,
    exit_type: null,
    exit_notes: null,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  };
  const list = (items: unknown[]) => ({ items, total: items.length });

  const mount = async (startup: Startup) => {
    TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      imports: [StartupDetail],
      providers: [
        provideNoopAnimations(),
        { provide: ActivatedRoute, useValue: { snapshot: { paramMap: { get: () => 's1' } } } },
        { provide: Router, useValue: {} },
        { provide: MatDialog, useValue: {} },
        { provide: MatSnackBar, useValue: { open: vi.fn() } },
        { provide: StartupService, useValue: { getById: () => of(startup) } },
        { provide: MonthlyIndicatorService, useValue: { list: () => of(list([])) } },
        { provide: BoardMeetingService, useValue: { list: () => of(list([])) } },
        { provide: ExecutiveService, useValue: { list: () => of(list([])) } },
        { provide: MonthlyIndicatorTokenService, useValue: { list: () => of(list([])) } },
      ],
    }).compileComponents();

    const fixture = TestBed.createComponent(StartupDetail);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  };

  const buttonTexts = (el: HTMLElement) =>
    [...el.querySelectorAll('button')].map((b) => b.textContent?.trim() ?? '');

  it('lets a tracked startup keep receiving indicators, with no exit notice', async () => {
    const el = await mount(base);

    expect(el.querySelector('.exit-notice')).toBeNull();
    expect(buttonTexts(el).some((t) => t.includes('Adicionar indicador'))).toBe(true);
  });

  it('announces the exit and stops offering new indicators', async () => {
    const el = await mount({
      ...base,
      exited_on: '2026-03-20',
      exit_type: ExitType.IPO,
      exit_notes: 'Listada na B3',
    });

    const notice = el.querySelector<HTMLElement>('.exit-notice')!;
    expect(notice.getAttribute('aria-labelledby')).toBe('exit-notice-title');
    expect(notice.textContent).toContain('Acompanhamento encerrado');
    expect(notice.textContent).toContain('20/03/2026');
    expect(notice.textContent).toContain('IPO');
    expect(notice.textContent).toContain('Listada na B3');
    expect(el.querySelector('.header-name-row')?.textContent).toContain('Encerrada');
    expect(buttonTexts(el).some((t) => t.includes('Adicionar indicador'))).toBe(false);
  });
});
