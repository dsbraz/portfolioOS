import { TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { NEVER, Observable, of, throwError } from 'rxjs';

import { Users } from './users';
import { AuthService } from '../../services/auth.service';
import { UserInviteService } from '../../services/user-invite.service';

// AGENTS.md: every data-backed screen renders loading, content and error.
describe('Users (loading, content and error states)', () => {
  const mount = async (listUsers: () => Observable<unknown>) => {
    TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      imports: [Users],
      providers: [
        provideNoopAnimations(),
        { provide: MatDialog, useValue: { open: vi.fn() } },
        { provide: MatSnackBar, useValue: { open: vi.fn() } },
        { provide: AuthService, useValue: { listUsers } },
        { provide: UserInviteService, useValue: { listActiveInvites: () => of([]) } },
      ],
    }).compileComponents();

    const fixture = TestBed.createComponent(Users);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  };

  // While loading, the page showed an empty table with no status at all.
  it('should announce loading instead of rendering an empty table', async () => {
    const el = await mount(() => NEVER);

    expect(el.querySelector('[aria-busy="true"]')).toBeTruthy();
    expect(el.querySelector('[role="status"]')?.textContent).toContain('Carregando');
    expect(el.querySelector('table')).toBeNull();
  });

  it('should show the empty state once an empty list arrives', async () => {
    const el = await mount(() => of({ items: [], total: 0 }));

    expect(el.querySelector('[aria-busy="true"]')).toBeNull();
    expect(el.textContent).toContain('Nenhum usuário cadastrado');
  });

  it('should say the load failed instead of showing an empty table', async () => {
    const el = await mount(() => throwError(() => ({ error: { detail: 'falhou' } })));

    expect(el.querySelector('table')).toBeNull();
    expect(el.textContent).not.toContain('Nenhum usuário cadastrado');
    expect(el.querySelector('[role="status"]')?.textContent).toContain('Não foi possível');
  });
});

describe('Users (refresh after a change)', () => {
  const user = { id: 'u1', username: 'admin', email: 'a@x.com', is_active: true, created_at: '2026-07-01T14:30:00', updated_at: '' };

  // After the edit dialog closes the list reloads with new objects. Without
  // tracking by id the row — and the edit button focus returns to — is recreated.
  it('should keep the row edit button in the DOM when the list reloads', async () => {
    TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      imports: [Users],
      providers: [
        provideNoopAnimations(),
        { provide: MatDialog, useValue: { open: vi.fn() } },
        { provide: MatSnackBar, useValue: { open: vi.fn() } },
        { provide: AuthService, useValue: { listUsers: () => of({ items: [{ ...user }], total: 1 }) } },
        { provide: UserInviteService, useValue: { listActiveInvites: () => of([]) } },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(Users);
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    const before = el.querySelector('td button');
    expect(before).toBeTruthy();

    fixture.componentInstance.loadUsers();
    fixture.detectChanges();

    expect(el.querySelector('td button')).toBe(before);
  });
});
