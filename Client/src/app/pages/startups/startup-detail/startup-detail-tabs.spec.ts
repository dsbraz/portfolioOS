import { ComponentFixture, TestBed } from '@angular/core/testing';
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
import { Startup, StartupStatus } from '../../../models/startup.model';

// WAI-ARIA APG tablist: arrow keys move between tabs (wrapping), Home/End jump
// to the ends, and selection follows focus with a roving tabindex.
describe('StartupDetail (tablist keyboard navigation)', () => {
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

  const list = (items: unknown[]) => ({ items, total: items.length });

  let fixture: ComponentFixture<StartupDetail>;
  let el: HTMLElement;

  const tabs = () => [...el.querySelectorAll<HTMLButtonElement>('[role="tab"]')];
  const selectedIndex = () => tabs().findIndex((t) => t.getAttribute('aria-selected') === 'true');

  const press = (index: number, key: string) => {
    const event = new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true });
    tabs()[index].dispatchEvent(event);
    fixture.detectChanges();
    return event;
  };

  const expectOnlySelected = (index: number) => {
    expect(selectedIndex()).toBe(index);
    expect(tabs().map((t) => t.getAttribute('tabindex'))).toEqual(
      tabs().map((_, i) => (i === index ? '0' : '-1')),
    );
    expect(document.activeElement).toBe(tabs()[index]);
  };

  beforeEach(async () => {
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

    fixture = TestBed.createComponent(StartupDetail);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    el = fixture.nativeElement as HTMLElement;
  });

  it('should start on the first tab', () => {
    expect(tabs().length).toBe(3);
    expect(selectedIndex()).toBe(0);
  });

  it('should move selection and focus to the next tab on ArrowRight', () => {
    const event = press(0, 'ArrowRight');

    expect(event.defaultPrevented).toBe(true);
    expectOnlySelected(1);
  });

  it('should wrap from the last tab to the first on ArrowRight', () => {
    press(0, 'End');
    press(2, 'ArrowRight');

    expectOnlySelected(0);
  });

  it('should wrap from the first tab to the last on ArrowLeft', () => {
    press(0, 'ArrowLeft');

    expectOnlySelected(2);
  });

  it('should move to the previous tab on ArrowLeft', () => {
    press(0, 'End');
    press(2, 'ArrowLeft');

    expectOnlySelected(1);
  });

  it('should jump to the last tab on End and back to the first on Home', () => {
    press(0, 'End');
    expectOnlySelected(2);

    press(2, 'Home');
    expectOnlySelected(0);
  });

  it('should show the panel of the tab selected by keyboard', () => {
    press(0, 'ArrowRight');

    const visible = [...el.querySelectorAll('[role="tabpanel"]')].filter(
      (p) => !p.hasAttribute('hidden'),
    );
    expect(visible.map((p) => p.id)).toEqual([tabs()[1].getAttribute('aria-controls')]);
  });

  // Tab must leave the tablist, so unrelated keys cannot be swallowed.
  it('should ignore keys that are not part of the tablist pattern', () => {
    const event = press(0, 'Tab');

    expect(event.defaultPrevented).toBe(false);
    expect(selectedIndex()).toBe(0);
  });
});
