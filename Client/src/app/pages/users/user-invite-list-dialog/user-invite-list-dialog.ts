import { Component, inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { UserInviteResponse } from '../../../models/user-invite.model';

export interface UserInviteListDialogData {
  invites: UserInviteResponse[];
}

@Component({
  selector: 'app-user-invite-list-dialog',
  imports: [
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatTableModule,
    MatSnackBarModule,
  ],
  template: `
    <h2 mat-dialog-title>Links de Convite Ativos</h2>
    <mat-dialog-content>
      @if (data.invites.length === 0) {
        <p class="empty-text">Nenhum convite ativo no momento.</p>
      } @else {
        <table mat-table [dataSource]="data.invites" class="invite-table">
          <ng-container matColumnDef="email">
            <th mat-header-cell *matHeaderCellDef>Email</th>
            <td mat-cell *matCellDef="let invite">{{ invite.email }}</td>
          </ng-container>

          <ng-container matColumnDef="expires_at">
            <th mat-header-cell *matHeaderCellDef>Expira em</th>
            <td mat-cell *matCellDef="let invite">
              {{ formatDate(invite.expires_at) }}
            </td>
          </ng-container>

          <ng-container matColumnDef="actions">
            <th mat-header-cell *matHeaderCellDef></th>
            <td mat-cell *matCellDef="let invite">
              <button mat-icon-button (click)="copyLink(invite.token)">
                <mat-icon>content_copy</mat-icon>
              </button>
            </td>
          </ng-container>

          <tr mat-header-row *matHeaderRowDef="columns"></tr>
          <tr mat-row *matRowDef="let row; columns: columns"></tr>
        </table>
      }
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button mat-dialog-close>Fechar</button>
    </mat-dialog-actions>
  `,
  styles: `
    .empty-text {
      color: var(--mat-sys-on-surface-variant);
      text-align: center;
      padding: 16px 0;
    }

    .invite-table {
      width: 100%;
    }
  `,
})
export class UserInviteListDialog {
  readonly data = inject<UserInviteListDialogData>(MAT_DIALOG_DATA);
  private readonly snackBar = inject(MatSnackBar);
  readonly columns = ['email', 'expires_at', 'actions'];

  copyLink(token: string): void {
    const url = `${window.location.origin}/user-invites/${token}`;
    navigator.clipboard.writeText(url).then(() => {
      this.snackBar.open('Link copiado!', 'Fechar', { duration: 2000 });
    });
  }

  formatDate(dateStr: string): string {
    return new Intl.DateTimeFormat('pt-BR', {
      dateStyle: 'short',
      timeStyle: 'short',
    }).format(new Date(dateStr));
  }
}
