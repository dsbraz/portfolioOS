import { Component, inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';

import { DialogHeader } from '../../../components/dialog-header/dialog-header';
import { Executive } from '../../../models/executive.model';
import { MonthlyIndicatorToken } from '../../../models/monthly-indicator-token.model';
import { MONTH_LABELS } from '../../../models/monthly-indicator.model';
import { TokenPanel } from '../token-panel/token-panel';

export interface TokenPanelDialogData {
  token: MonthlyIndicatorToken;
  executives: Executive[];
}

/**
 * Dialog wrapper around the reusable link panel, used from "Links anteriores"
 * to open an existing period's link. The unified add-indicator dialog renders
 * the same `app-token-panel` inline instead of opening this.
 */
@Component({
  selector: 'app-token-panel-dialog',
  imports: [MatDialogModule, MatButtonModule, DialogHeader, TokenPanel],
  template: `
    <app-dialog-header
      [title]="'Link de indicador — ' + period"
      description="O link abre o formulário de reporte deste período. Quem o recebe consegue preencher os dados da startup."
    />
    <mat-dialog-content>
      <app-token-panel [token]="data.token" [executives]="data.executives" />
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-stroked-button mat-dialog-close>Fechar</button>
    </mat-dialog-actions>
  `,
})
export class TokenPanelDialog {
  readonly data = inject<TokenPanelDialogData>(MAT_DIALOG_DATA);
  readonly period = `${MONTH_LABELS[this.data.token.month]}/${this.data.token.year}`;
}
