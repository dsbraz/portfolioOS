import { Component, inject, OnInit, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { UserResponse } from '../../../models/auth.model';
import { AuthService } from '../../../services/auth.service';

export interface UserFormDialogData {
  user?: UserResponse;
}

@Component({
  selector: 'app-user-form-dialog',
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatDialogModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatSlideToggleModule,
    MatSnackBarModule,
  ],
  templateUrl: './user-form-dialog.html',
  styleUrl: './user-form-dialog.scss',
})
export class UserFormDialog implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly dialogRef = inject(MatDialogRef<UserFormDialog>);
  private readonly snackBar = inject(MatSnackBar);
  readonly data: UserFormDialogData = inject(MAT_DIALOG_DATA);

  readonly isEditMode = !!this.data?.user;

  readonly form = this.fb.nonNullable.group({
    username: ['', [Validators.required, Validators.maxLength(150)]],
    email: ['', [Validators.required, Validators.email]],
    password: ['', this.isEditMode ? [Validators.minLength(8)] : [Validators.required, Validators.minLength(8)]],
    is_active: [true],
  });

  readonly loading = signal(false);
  readonly hidePassword = signal(true);

  ngOnInit(): void {
    if (this.data?.user) {
      const u = this.data.user;
      this.form.patchValue({
        username: u.username,
        email: u.email,
        is_active: u.is_active,
      });
    }
  }

  onSubmit(): void {
    if (this.form.invalid) return;

    this.loading.set(true);

    if (this.isEditMode) {
      const raw = this.form.getRawValue();
      const updates: Record<string, unknown> = {
        username: raw.username,
        email: raw.email,
        is_active: raw.is_active,
      };
      if (raw.password) {
        updates['password'] = raw.password;
      }
      this.authService.updateUser(this.data.user!.id, updates).subscribe({
        next: () => {
          this.snackBar.open('Usuário atualizado', 'Fechar', { duration: 3000 });
          this.dialogRef.close(true);
        },
        error: (err) => {
          this.loading.set(false);
          this.snackBar.open(this.extractError(err, 'Erro ao atualizar usuário'), 'Fechar', { duration: 3000 });
        },
      });
    } else {
      this.authService.createUser(this.form.getRawValue()).subscribe({
        next: () => {
          this.snackBar.open('Usuário criado com sucesso', 'Fechar', { duration: 3000 });
          this.dialogRef.close(true);
        },
        error: (err) => {
          this.loading.set(false);
          this.snackBar.open(this.extractError(err, 'Erro ao criar usuário'), 'Fechar', { duration: 3000 });
        },
      });
    }
  }

  private extractError(err: unknown, fallback: string): string {
    const httpErr = err as { error?: unknown; message?: string };
    let body = httpErr?.error;
    if (typeof body === 'string') {
      try { body = JSON.parse(body); } catch { /* keep as string */ }
    }
    if (body && typeof body === 'object' && 'detail' in (body as object)) {
      const detail = (body as Record<string, unknown>)['detail'];
      if (typeof detail === 'string') return detail;
    }
    if (typeof body === 'string') return body;
    return fallback;
  }
}
