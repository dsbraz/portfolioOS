import { TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { NEVER, Observable, of, throwError } from 'rxjs';

import { Dealflow } from './dealflow';
import { DealService } from '../../services/deal.service';

// AGENTS.md: every data-backed screen renders loading, content and error.
describe('Dealflow (loading, content and error states)', () => {
  const mount = async (list: () => Observable<unknown>) => {
    TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      imports: [Dealflow],
      providers: [
        provideNoopAnimations(),
        { provide: MatDialog, useValue: { open: vi.fn() } },
        { provide: MatSnackBar, useValue: { open: vi.fn() } },
        { provide: DealService, useValue: { list } },
      ],
    }).compileComponents();

    const fixture = TestBed.createComponent(Dealflow);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  };

  it('should announce loading instead of rendering an empty board', async () => {
    const el = await mount(() => NEVER);

    expect(el.querySelector('[aria-busy="true"]')).toBeTruthy();
    expect(el.querySelector('[role="status"]')?.textContent).toContain('Carregando');
    expect(el.querySelector('.kanban-board')).toBeNull();
  });

  it('should render the board once the deals arrive', async () => {
    const el = await mount(() => of({ items: [], total: 0 }));

    expect(el.querySelector('[aria-busy="true"]')).toBeNull();
    expect(el.querySelector('.kanban-board')).toBeTruthy();
  });

  // A failed load showed an empty board — indistinguishable from "no deals".
  it('should say the load failed instead of showing an empty board', async () => {
    const el = await mount(() => throwError(() => ({ error: { detail: 'falhou' } })));

    expect(el.querySelector('.kanban-board')).toBeNull();
    expect(el.querySelector('[role="status"]')?.textContent).toContain('Não foi possível');
  });
});
