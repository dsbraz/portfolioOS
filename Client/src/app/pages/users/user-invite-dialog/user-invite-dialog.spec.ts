import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MatDialogRef } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { of, throwError } from 'rxjs';

import { UserInviteService } from '../../../services/user-invite.service';
import { UserInviteDialog } from './user-invite-dialog';

describe('UserInviteDialog', () => {
  let fixture: ComponentFixture<UserInviteDialog>;
  let component: UserInviteDialog;

  const inviteService = { createInvite: vi.fn() };
  const dialogRef = { close: vi.fn() };
  const snackBar = { open: vi.fn() };
  let escritoNoClipboard: string | null;

  beforeEach(async () => {
    escritoNoClipboard = null;
    // jsdom has no clipboard; the dialog copies the invite URL on success, so
    // the spec provides one that records what was written.
    Object.defineProperty(navigator, 'clipboard', {
      value: {
        writeText: (texto: string) => {
          escritoNoClipboard = texto;
          return Promise.resolve();
        },
      },
      configurable: true,
    });

    await TestBed.configureTestingModule({
      imports: [UserInviteDialog],
      providers: [
        provideNoopAnimations(),
        { provide: UserInviteService, useValue: inviteService },
        { provide: MatDialogRef, useValue: dialogRef },
      ],
    })
      .overrideProvider(MatSnackBar, { useValue: snackBar })
      .compileComponents();

    fixture = TestBed.createComponent(UserInviteDialog);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  afterEach(() => {
    TestBed.resetTestingModule();
    vi.clearAllMocks();
  });

  it('refuses to submit without a valid e-mail', () => {
    component.form.patchValue({ email: 'não é e-mail' });

    component.onSubmit();

    expect(inviteService.createInvite).not.toHaveBeenCalled();
    expect(dialogRef.close).not.toHaveBeenCalled();
  });

  it('creates the invite, copies its URL and closes reporting the change', async () => {
    inviteService.createInvite = vi.fn(() => of({ token: 'tok-abc' }));
    component.form.patchValue({ email: 'novo@fundo.com' });

    component.onSubmit();
    await fixture.whenStable();

    expect(inviteService.createInvite).toHaveBeenCalledWith({ email: 'novo@fundo.com' });
    // The copied URL carries the token — it is the artifact the admin sends on.
    expect(escritoNoClipboard).toContain('/user-invites/tok-abc');
    expect(dialogRef.close).toHaveBeenCalledWith(true);
  });

  it('stays open on failure so the e-mail can be corrected', () => {
    inviteService.createInvite = vi.fn(() =>
      throwError(() => ({ error: { detail: 'E-mail já convidado' } })),
    );
    component.form.patchValue({ email: 'repetido@fundo.com' });

    component.onSubmit();

    expect(snackBar.open).toHaveBeenCalledWith('E-mail já convidado', 'Fechar', expect.anything());
    expect(dialogRef.close).not.toHaveBeenCalled();
    expect(component.loading()).toBe(false);
  });
});
