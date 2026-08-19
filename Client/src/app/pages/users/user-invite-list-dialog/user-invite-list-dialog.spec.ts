import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';

import {
  UserInviteListDialog,
  UserInviteListDialogData,
} from './user-invite-list-dialog';

describe('UserInviteListDialog', () => {
  let fixture: ComponentFixture<UserInviteListDialog>;

  const snackBar = { open: vi.fn() };
  let escritoNoClipboard: string | null;

  async function render(data: UserInviteListDialogData): Promise<HTMLElement> {
    escritoNoClipboard = null;
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
      imports: [UserInviteListDialog],
      providers: [provideNoopAnimations(), { provide: MAT_DIALOG_DATA, useValue: data }],
    })
      .overrideProvider(MatSnackBar, { useValue: snackBar })
      .compileComponents();

    fixture = TestBed.createComponent(UserInviteListDialog);
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  }

  afterEach(() => {
    TestBed.resetTestingModule();
    vi.clearAllMocks();
  });

  it('says there is nothing instead of showing an empty table', async () => {
    const element = await render({ invites: [] });

    expect(element.textContent).toContain('Nenhum convite ativo no momento');
    expect(element.querySelector('table')).toBeNull();
  });

  it('names each copy action after its invite, so rows are distinguishable', async () => {
    const element = await render({
      invites: [
        { id: 'i1', email: 'ana@fundo.com', token: 'tok-1', expires_at: '2026-09-01T12:00:00Z' },
        { id: 'i2', email: 'bruno@fundo.com', token: 'tok-2', expires_at: '2026-09-02T12:00:00Z' },
      ] as never,
    });

    const botao = element.querySelector<HTMLButtonElement>(
      '[aria-label="Copiar link do convite de bruno@fundo.com"]',
    );
    expect(botao).toBeTruthy();

    botao!.click();
    await fixture.whenStable();

    // The copied URL is the row's own token — not the first row's.
    expect(escritoNoClipboard).toContain('/user-invites/tok-2');
  });
});
