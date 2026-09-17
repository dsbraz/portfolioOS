import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { of } from 'rxjs';

import { Users } from './users';
import { UserResponse } from '../../models/auth.model';
import { AuthService } from '../../services/auth.service';
import { UserInviteService } from '../../services/user-invite.service';

// The sorting rules live in `models/sorting.ts`; these tests cover that clicking
// a real `mat-sort-header` actually drives the page's `sort` signal.
describe('Users (sort header wiring)', () => {
  const user = (username: string, email: string, isActive: boolean): UserResponse => ({
    id: username,
    username,
    email,
    is_active: isActive,
    created_at: '2026-01-01T10:00:00',
    updated_at: '2026-01-01T10:00:00',
  });

  // Deliberately in neither ascending nor descending order for any column.
  const users = [
    user('bruno', 'c@example.com', true),
    user('ana', 'b@example.com', false),
    user('carla', 'a@example.com', true),
  ];

  let fixture: ComponentFixture<Users>;
  let el: HTMLElement;

  const header = (label: string) =>
    [...el.querySelectorAll('th')].find((th) => th.textContent?.includes(label))!;

  const clickHeader = (label: string) => {
    (header(label).querySelector('.mat-sort-header-container') as HTMLElement).click();
    fixture.detectChanges();
  };

  const rowNames = () =>
    [...el.querySelectorAll('tr[mat-row] .user-name')].map((n) => n.textContent?.trim());

  beforeEach(async () => {
    TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      imports: [Users],
      providers: [
        provideNoopAnimations(),
        { provide: MatDialog, useValue: { open: vi.fn() } },
        { provide: MatSnackBar, useValue: { open: vi.fn() } },
        { provide: AuthService, useValue: { listUsers: () => of({ items: users, total: users.length }) } },
        { provide: UserInviteService, useValue: { listActiveInvites: () => of({ items: [] }) } },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(Users);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    el = fixture.nativeElement as HTMLElement;
  });

  it('should keep the API order and aria-sort "none" before any header is clicked', () => {
    expect(rowNames()).toEqual(['bruno', 'ana', 'carla']);
    expect(header('Usuário').getAttribute('aria-sort')).toBe('none');
  });

  it('should sort by username ascending, then descending, as the header is clicked', () => {
    clickHeader('Usuário');
    expect(header('Usuário').getAttribute('aria-sort')).toBe('ascending');
    expect(rowNames()).toEqual(['ana', 'bruno', 'carla']);

    clickHeader('Usuário');
    expect(header('Usuário').getAttribute('aria-sort')).toBe('descending');
    expect(rowNames()).toEqual(['carla', 'bruno', 'ana']);
  });

  it('should move aria-sort to the newly clicked column', () => {
    clickHeader('Usuário');
    clickHeader('Email');

    expect(header('Usuário').getAttribute('aria-sort')).toBe('none');
    expect(header('Email').getAttribute('aria-sort')).toBe('ascending');
    expect(rowNames()).toEqual(['carla', 'ana', 'bruno']);
  });
});
