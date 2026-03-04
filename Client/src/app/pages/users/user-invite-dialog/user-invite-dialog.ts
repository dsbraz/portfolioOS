import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { UserInviteService } from '../../../services/user-invite.service';

@Component({
  selector: 'app-user-invite-dialog',
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatSnackBarModule,
  ],
  templateUrl: './user-invite-dialog.html',
  styleUrl: './user-invite-dialog.scss',
})
export class UserInviteDialog {
  private readonly fb = inject(FormBuilder);
  private readonly userInviteService = inject(UserInviteService);
  private readonly snackBar = inject(MatSnackBar);
  private readonly dialogRef = inject(MatDialogRef<UserInviteDialog>);

  readonly loading = signal(false);

  readonly form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
  });

  onSubmit(): void {
    if (this.form.invalid || this.loading()) return;

    this.loading.set(true);
    const data = this.form.getRawValue();
    this.userInviteService.createInvite(data).subscribe({
      next: (invite) => {
        const url = `${window.location.origin}/user-invites/${invite.token}`;
        navigator.clipboard.writeText(url).then(() => {
          this.snackBar.open('Link de convite gerado e copiado!', 'Fechar', {
            duration: 3000,
          });
        });
        this.loading.set(false);
        this.dialogRef.close(true);
      },
      error: (err) => {
        this.loading.set(false);
        this.snackBar.open(err.error?.detail || 'Erro ao gerar convite', 'Fechar', {
          duration: 3000,
        });
      },
    });
  }
}
