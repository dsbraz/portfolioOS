import { Component, inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { ReportToken } from '../../../models/report-token.model';
import { MONTH_LABELS } from '../../../models/monthly-indicator.model';

export interface ReportTokenListDialogData {
  tokens: ReportToken[];
}

@Component({
  selector: 'app-report-token-list-dialog',
  imports: [
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatTableModule,
    MatTooltipModule,
    MatSnackBarModule,
  ],
  template: `
    <h2 mat-dialog-title>Links de Relatorio</h2>
    <mat-dialog-content>
      @if (data.tokens.length === 0) {
        <p class="empty-text">Nenhum link gerado ainda.</p>
      } @else {
        <table mat-table [dataSource]="data.tokens" class="token-table">
          <ng-container matColumnDef="period">
            <th mat-header-cell *matHeaderCellDef>Periodo</th>
            <td mat-cell *matCellDef="let t">{{ monthLabels[t.month] }}/{{ t.year }}</td>
          </ng-container>
          <ng-container matColumnDef="actions">
            <th mat-header-cell *matHeaderCellDef></th>
            <td mat-cell *matCellDef="let t">
              <button mat-icon-button matTooltip="Copiar link" (click)="copyLink(t)">
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
    .token-table {
      width: 100%;
    }
  `,
})
export class ReportTokenListDialog {
  readonly data = inject<ReportTokenListDialogData>(MAT_DIALOG_DATA);
  private readonly snackBar = inject(MatSnackBar);
  readonly monthLabels = MONTH_LABELS;
  readonly columns = ['period', 'actions'];

  copyLink(token: ReportToken): void {
    const url = `${window.location.origin}/report/${token.token}`;
    navigator.clipboard.writeText(url).then(() => {
      this.snackBar.open('Link copiado!', 'Fechar', { duration: 2000 });
    });
  }
}
