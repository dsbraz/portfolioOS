import { Component, inject, OnInit, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTableModule } from '@angular/material/table';

import { UserResponse } from '../../models/auth.model';
import { AuthService } from '../../services/auth.service';
import { UserFormDialog, UserFormDialogData } from './user-form-dialog/user-form-dialog';

@Component({
  selector: 'app-users',
  imports: [
    MatButtonModule,
    MatCardModule,
    MatDialogModule,
    MatIconModule,
    MatSnackBarModule,
    MatTableModule,
  ],
  templateUrl: './users.html',
  styleUrl: './users.scss',
})
export class Users implements OnInit {
  private readonly authService = inject(AuthService);
  private readonly dialog = inject(MatDialog);
  private readonly snackBar = inject(MatSnackBar);

  readonly users = signal<UserResponse[]>([]);
  readonly loading = signal(false);
  readonly displayedColumns = ['username', 'email', 'is_active', 'created_at', 'actions'];

  ngOnInit(): void {
    this.loadUsers();
  }

  loadUsers(): void {
    this.loading.set(true);
    this.authService.listUsers().subscribe({
      next: (data) => {
        this.users.set(data.items);
        this.loading.set(false);
      },
      error: (err) => {
        this.snackBar.open(err.error?.detail || 'Erro ao carregar usuários', 'Fechar', { duration: 3000 });
        this.loading.set(false);
      },
    });
  }

  openCreateDialog(): void {
    const dialogRef = this.dialog.open(UserFormDialog, {
      width: '480px',
      data: {} as UserFormDialogData,
    });

    dialogRef.afterClosed().subscribe((result) => {
      if (result) {
        this.loadUsers();
      }
    });
  }

  openEditDialog(user: UserResponse): void {
    const dialogRef = this.dialog.open(UserFormDialog, {
      width: '480px',
      data: { user } as UserFormDialogData,
    });

    dialogRef.afterClosed().subscribe((result) => {
      if (result) {
        this.loadUsers();
      }
    });
  }

  formatDate(dateStr: string): string {
    return new Intl.DateTimeFormat('pt-BR', {
      dateStyle: 'short',
      timeStyle: 'short',
    }).format(new Date(dateStr));
  }
}
