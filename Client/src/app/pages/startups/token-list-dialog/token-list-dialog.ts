import { Component, inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';

import { DialogHeader } from '../../../components/dialog-header/dialog-header';
import { Executive } from '../../../models/executive.model';
import { MonthlyIndicatorToken } from '../../../models/monthly-indicator-token.model';
import { MONTH_LABELS } from '../../../models/monthly-indicator.model';
import { TokenPanelDialog, TokenPanelDialogData } from '../token-panel-dialog/token-panel-dialog';

export interface TokenListDialogData {
  tokens: MonthlyIndicatorToken[];
  executives: Executive[];
  startupName: string;
}

@Component({
  selector: 'app-token-list-dialog',
  imports: [MatDialogModule, MatButtonModule, MatIconModule, MatTableModule, DialogHeader],
  template: `
    <app-dialog-header title="Links de Relatório" />
    <mat-dialog-content>
      @if (data.tokens.length === 0) {
        <p class="empty-text">Nenhum link gerado ainda.</p>
      } @else {
        <table mat-table [dataSource]="data.tokens" class="token-table">
          <caption class="visually-hidden">
            Links de relatório já gerados, por período.
          </caption>
          <ng-container matColumnDef="period">
            <th mat-header-cell *matHeaderCellDef scope="col">Período</th>
            <td mat-cell *matCellDef="let t">{{ periodOf(t) }}</td>
          </ng-container>
          <ng-container matColumnDef="actions">
            <th mat-header-cell *matHeaderCellDef scope="col">
              <span class="visually-hidden">Ações</span>
            </th>
            <td mat-cell *matCellDef="let t">
              <button
                mat-stroked-button
                type="button"
                [attr.aria-label]="'Abrir link de ' + periodOf(t)"
                (click)="openPanel(t)"
              >
                <mat-icon aria-hidden="true">link</mat-icon>
                Abrir
              </button>
            </td>
          </ng-container>
          <tr mat-header-row *matHeaderRowDef="columns"></tr>
          <tr mat-row *matRowDef="let row; columns: columns"></tr>
        </table>
      }
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-stroked-button mat-dialog-close>Fechar</button>
    </mat-dialog-actions>
  `,
  styles: `
    .empty-text {
      color: var(--color-text-muted);
      text-align: center;
      padding: var(--space-md) 0;
    }
    .token-table {
      width: 100%;
    }
  `,
})
export class TokenListDialog {
  readonly data = inject<TokenListDialogData>(MAT_DIALOG_DATA);
  private readonly dialog = inject(MatDialog);
  readonly columns = ['period', 'actions'];

  periodOf(token: MonthlyIndicatorToken): string {
    return `${MONTH_LABELS[token.month]}/${token.year}`;
  }

  /**
   * The link itself lives in the panel, not here: one row action per period with
   * a name that identifies it, instead of N identical copy buttons.
   */
  openPanel(token: MonthlyIndicatorToken): void {
    this.dialog.open(TokenPanelDialog, {
      width: '560px',
      data: {
        token,
        executives: this.data.executives,
        startupName: this.data.startupName,
      } as TokenPanelDialogData,
    });
  }
}
