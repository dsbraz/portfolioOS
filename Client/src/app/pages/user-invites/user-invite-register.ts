import { Component, inject, OnInit, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { PublicUserInviteContext } from '../../models/user-invite.model';
import { UserInviteService } from '../../services/user-invite.service';

const USERNAME_NO_SPACES_PATTERN = /^\S+$/;

@Component({
  selector: 'app-user-invite-register',
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatCardModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
  ],
  templateUrl: './user-invite-register.html',
  styleUrl: './user-invite-register.scss',
})
export default class UserInviteRegister implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);
  private readonly inviteService = inject(UserInviteService);
  private readonly snackBar = inject(MatSnackBar);

  readonly loading = signal(true);
  readonly submitting = signal(false);
  readonly submitted = signal(false);
  readonly error = signal<string | null>(null);
  readonly context = signal<PublicUserInviteContext | null>(null);

  private token = '';

  readonly form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    username: ['', [Validators.required, Validators.maxLength(150), Validators.pattern(USERNAME_NO_SPACES_PATTERN)]],
    password: ['', [Validators.required, Validators.minLength(8)]],
    confirmPassword: ['', [Validators.required, Validators.minLength(8)]],
  });

  ngOnInit(): void {
    this.token = this.route.snapshot.paramMap.get('token') ?? '';
    if (!this.token) {
      this.error.set('Link inválido ou expirado.');
      this.loading.set(false);
      return;
    }

    this.inviteService.getPublicInvite(this.token).subscribe({
      next: (data) => {
        this.context.set(data);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Link inválido ou expirado.');
        this.loading.set(false);
      },
    });
  }

  onSubmit(): void {
    if (this.form.invalid || this.submitting()) return;

    const raw = this.form.getRawValue();
    if (raw.password !== raw.confirmPassword) {
      this.snackBar.open('As senhas não conferem', 'Fechar', { duration: 3000 });
      return;
    }

    this.submitting.set(true);
    this.inviteService
      .consumeInvite(this.token, {
        email: raw.email.trim(),
        username: raw.username,
        password: raw.password,
      })
      .subscribe({
        next: () => {
          this.submitting.set(false);
          this.submitted.set(true);
          setTimeout(() => {
            this.router.navigate(['/login']);
          }, 1500);
        },
        error: (err) => {
          this.submitting.set(false);
          this.snackBar.open(
            err.error?.detail || 'Erro ao concluir cadastro',
            'Fechar',
            { duration: 4000 },
          );
        },
      });
  }

  canSubmit(): boolean {
    const email = this.form.controls.email.value.trim();
    const username = this.form.controls.username.value.trim();
    const password = this.form.controls.password.value;
    const confirmPassword = this.form.controls.confirmPassword.value;

    return (
      email.length > 0 &&
      this.form.controls.email.valid &&
      username.length > 0 &&
      this.form.controls.username.valid &&
      password.length >= 8 &&
      confirmPassword.length >= 8 &&
      password === confirmPassword
    );
  }
}
