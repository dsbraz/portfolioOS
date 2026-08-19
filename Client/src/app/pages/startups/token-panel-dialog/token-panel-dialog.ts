import { Component, computed, inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { DialogHeader } from '../../../components/dialog-header/dialog-header';
import { Executive } from '../../../models/executive.model';
import { MonthlyIndicatorToken } from '../../../models/monthly-indicator-token.model';
import { MONTH_LABELS } from '../../../models/monthly-indicator.model';
import {
  buildIndicatorRequestMessage,
  buildWhatsAppLink,
  formatBrazilianPhone,
} from '../../../models/whatsapp';

export interface TokenPanelDialogData {
  token: MonthlyIndicatorToken;
  executives: Executive[];
}

/** One executive, resolved for sending — or blocked, with the reason visible. */
interface Recipient {
  name: string;
  role: string | null;
  formattedPhone: string | null;
  whatsappUrl: string | null;
  message: string;
}

@Component({
  selector: 'app-token-panel-dialog',
  imports: [
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatSnackBarModule,
    DialogHeader,
  ],
  templateUrl: './token-panel-dialog.html',
  styleUrl: './token-panel-dialog.scss',
})
export class TokenPanelDialog {
  readonly data = inject<TokenPanelDialogData>(MAT_DIALOG_DATA);
  private readonly snackBar = inject(MatSnackBar);

  readonly period = `${MONTH_LABELS[this.data.token.month]}/${this.data.token.year}`;
  readonly formUrl = `${window.location.origin}/monthly-indicator/${this.data.token.token}`;

  /**
   * Every executive appears, including the ones that cannot be reached. Hiding
   * them would make "there is nobody to send to" indistinguishable from "the
   * phone is missing from the record", which is the actionable case.
   */
  readonly recipients = computed<Recipient[]>(() =>
    this.data.executives.map((executive) => {
      const message = buildIndicatorRequestMessage(executive.name, this.period, this.formUrl);
      return {
        name: executive.name,
        role: executive.role,
        formattedPhone: formatBrazilianPhone(executive.phone),
        whatsappUrl: buildWhatsAppLink(executive.phone, message),
        message,
      };
    }),
  );

  readonly reachable = computed(() => this.recipients().filter((r) => r.whatsappUrl !== null));
  readonly blocked = computed(() => this.recipients().filter((r) => r.whatsappUrl === null));

  copyLink(): void {
    navigator.clipboard.writeText(this.formUrl).then(() => {
      this.snackBar.open('Link copiado!', 'Fechar', { duration: 2000 });
    });
  }
}
