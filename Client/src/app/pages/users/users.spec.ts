import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { of, throwError } from 'rxjs';

import { UserResponse } from '../../models/auth.model';
import { AuthService } from '../../services/auth.service';
import { UserInviteService } from '../../services/user-invite.service';
import { Users } from './users';

describe('Users', () => {
  let fixture: ComponentFixture<Users>;

  const usuario = (over: Partial<UserResponse>): UserResponse =>
    ({
      id: 'u1',
      username: 'ana',
      email: 'ana@fundo.com',
      is_active: true,
      created_at: '2026-08-01T12:00:00Z',
      ...over,
    }) as UserResponse;

  const authService = { listUsers: vi.fn() };
  const inviteService = { listActiveInvites: vi.fn() };
  const dialog = { open: vi.fn(() => ({ afterClosed: () => of(undefined) })) };
  const snackBar = { open: vi.fn() };

  beforeEach(() => {
    authService.listUsers = vi.fn(() =>
      of({ items: [usuario({}), usuario({ id: 'u2', username: 'bruno', is_active: false })], total: 2 }),
    );
    dialog.open = vi.fn(() => ({ afterClosed: () => of(undefined) })) as never;
  });

  async function render(): Promise<HTMLElement> {
    await TestBed.configureTestingModule({
      imports: [Users],
      providers: [
        provideNoopAnimations(),
        { provide: AuthService, useValue: authService },
        { provide: UserInviteService, useValue: inviteService },
      ],
    })
      .overrideProvider(MatDialog, { useValue: dialog })
      .overrideProvider(MatSnackBar, { useValue: snackBar })
      .compileComponents();

    fixture = TestBed.createComponent(Users);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  }

  afterEach(() => {
    TestBed.resetTestingModule();
    vi.clearAllMocks();
  });

  it('lists the users in a real table', async () => {
    const element = await render();

    expect(element.querySelector('table')).toBeTruthy();
    expect(element.textContent).toContain('ana');
    expect(element.textContent).toContain('bruno');
  });

  it('sorts inactive users first when ordering by status ascending', async () => {
    await render();
    const component = fixture.componentInstance;

    component.sort.set({ active: 'is_active', direction: 'asc' });

    // Boolean becomes a number so the order is defined, not accidental.
    expect(component.sortedUsers().map((u) => u.username)).toEqual(['bruno', 'ana']);
  });

  it('surfaces a load failure instead of an empty page', async () => {
    authService.listUsers = vi.fn(() =>
      throwError(() => ({ error: { detail: 'sem permissão' } })),
    );
    await render();

    expect(snackBar.open).toHaveBeenCalledWith('sem permissão', 'Fechar', expect.anything());
  });

  it('reloads the list after the edit dialog reports a change', async () => {
    await render();
    dialog.open = vi.fn(() => ({ afterClosed: () => of(true) })) as never;

    fixture.componentInstance.openEditDialog(usuario({}));

    expect(authService.listUsers).toHaveBeenCalledTimes(2);
  });

  it('opens the invite list only after the invites arrive', async () => {
    const convites = [{ id: 'i1', email: 'novo@fundo.com', token: 't', expires_at: '' }];
    inviteService.listActiveInvites = vi.fn(() => of({ items: convites, total: 1 }));
    await render();

    fixture.componentInstance.openInviteListDialog();

    expect(dialog.open).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({ data: { invites: convites } }),
    );
  });

  it('reports a failure fetching invites and opens nothing', async () => {
    inviteService.listActiveInvites = vi.fn(() =>
      throwError(() => ({ error: {} })),
    );
    await render();

    fixture.componentInstance.openInviteListDialog();

    expect(dialog.open).not.toHaveBeenCalled();
    expect(snackBar.open).toHaveBeenCalledWith(
      'Erro ao carregar convites ativos',
      'Fechar',
      expect.anything(),
    );
  });
});
