import { Component, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { MAT_DIALOG_DATA, MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';

import { DialogHeader } from '../../../components/dialog-header/dialog-header';
import { Executive } from '../../../models/executive.model';
import { MonthlyIndicatorToken } from '../../../models/monthly-indicator-token.model';
import {
  DISPATCH_KIND_LABELS,
  dispatchStatus,
  MonthlyReportDispatch,
} from '../../../models/monthly-report.model';
import { formatPeriod } from '../../../models/formatters';
import { TokenPanelDialog, TokenPanelDialogData } from '../token-panel-dialog/token-panel-dialog';

export interface TokenListDialogData {
  tokens: MonthlyIndicatorToken[];
  /**
   * Automatic e-mails of these links, sent by the monthly job. `null` when the
   * history could not be loaded — never shown as "none", or the operator would
   * resend by hand what the job already sent.
   */
  dispatches: MonthlyReportDispatch[] | null;
  executives: Executive[];
  startupName: string;
}

@Component({
  selector: 'app-token-list-dialog',
  imports: [
    DatePipe,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatTableModule,
    DialogHeader,
  ],
  template: `
    <app-dialog-header title="Links de Relatório" />
    <mat-dialog-content>
      @if (data.tokens.length === 0) {
        <p class="empty-text">Nenhum link gerado ainda.</p>
      } @else {
        @if (historyUnavailable) {
          <p class="history-warning" role="status">
            <mat-icon aria-hidden="true">warning</mat-icon>
            <span>
              Não foi possível carregar o histórico de envios automáticos. Antes de enviar um
              link à mão, recarregue a página para conferir se o e-mail já saiu.
            </span>
          </p>
        }
        <table mat-table [dataSource]="data.tokens" class="token-table">
          <caption class="visually-hidden">
            Links de relatório já gerados, por período, com os envios automáticos por
            e-mail.
          </caption>
          <!-- The action sits under its period instead of in a column of its own:
               beside the e-mail history, a third column pushed it out of a
               phone-width dialog. -->
          <ng-container matColumnDef="period">
            <th mat-header-cell *matHeaderCellDef scope="col">Período</th>
            <td mat-cell *matCellDef="let t">
              <span class="period-label">{{ formatPeriod(t.month, t.year) }}</span>
              <button
                mat-stroked-button
                type="button"
                [attr.aria-label]="'Abrir link de ' + formatPeriod(t.month, t.year)"
                (click)="openPanel(t)"
              >
                <mat-icon aria-hidden="true">link</mat-icon>
                Abrir
              </button>
            </td>
          </ng-container>
          <ng-container matColumnDef="dispatches">
            <th mat-header-cell *matHeaderCellDef scope="col">Envio automático</th>
            <td mat-cell *matCellDef="let t">
              @let sent = dispatchesFor(t);
              @if (historyUnavailable) {
                <span class="muted">Indisponível</span>
              } @else if (sent.length === 0) {
                <span class="muted">Nenhum</span>
              } @else {
                <ul class="dispatch-list" role="list">
                  @for (d of sent; track d.id) {
                    @switch (status(d)) {
                      @case ('delivered') {
                        <li>
                          {{ kindLabels[d.kind] }} em {{ d.sent_at | date: 'dd/MM' }} para
                          {{ d.recipient_email }}
                        </li>
                      }
                      @case ('failed') {
                        <li>
                          {{ kindLabels[d.kind] }}: tentativa em
                          {{ d.attempted_at | date: 'dd/MM' }} para {{ d.recipient_email }}
                          <span class="pill pill--danger">Falhou</span>
                          <span class="dispatch-detail">{{ d.error }}</span>
                        </li>
                      }
                      @case ('unconfirmed') {
                        <li>
                          {{ kindLabels[d.kind] }}: tentativa em
                          {{ d.attempted_at | date: 'dd/MM' }} para {{ d.recipient_email }}
                          <span class="pill pill--warn">Não confirmado</span>
                          <span class="dispatch-detail">
                            O e-mail pode ter saído. Confirme com o destinatário antes de
                            enviar de novo.
                          </span>
                        </li>
                      }
                    }
                  }
                </ul>
              }
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
    .token-table td {
      vertical-align: top;
      padding-block: var(--space-sm);
    }
    .period-label {
      display: block;
      margin-block-end: var(--space-xs);
    }
    .muted {
      color: var(--color-text-muted);
    }
    .dispatch-list {
      margin: 0;
      padding: var(--space-xs) 0;
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: var(--space-xs);
      font-size: 0.875rem;
      // An address has no break opportunity; at phone width it would run past
      // the dialog's edge.
      overflow-wrap: anywhere;
    }
    .history-warning {
      display: flex;
      align-items: flex-start;
      gap: var(--space-xs);
      margin: 0 0 var(--space-sm);
      font-size: 0.875rem;
    }
    .history-warning mat-icon {
      flex-shrink: 0;
      color: var(--color-warn);
    }
    .dispatch-detail {
      display: block;
      color: var(--color-text-muted);
      font-size: 0.8125rem;
      overflow-wrap: anywhere;
    }
  `,
})
export class TokenListDialog {
  readonly data = inject<TokenListDialogData>(MAT_DIALOG_DATA);
  private readonly dialog = inject(MatDialog);
  readonly formatPeriod = formatPeriod;
  readonly columns = ['period', 'dispatches'];
  readonly kindLabels = DISPATCH_KIND_LABELS;
  readonly status = dispatchStatus;
  readonly historyUnavailable = this.data.dispatches === null;

  /** Grouped once by period; the template looks each row up instead of filtering. */
  private readonly dispatchesByPeriod = (this.data.dispatches ?? []).reduce(
    (byPeriod, d) => {
      const key = `${d.year}-${d.month}`;
      byPeriod.set(key, [...(byPeriod.get(key) ?? []), d]);
      return byPeriod;
    },
    new Map<string, MonthlyReportDispatch[]>(),
  );

  dispatchesFor(token: MonthlyIndicatorToken): MonthlyReportDispatch[] {
    return this.dispatchesByPeriod.get(`${token.year}-${token.month}`) ?? [];
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
