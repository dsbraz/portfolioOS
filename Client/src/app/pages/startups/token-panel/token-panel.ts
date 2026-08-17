import { Component, computed, inject, input } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { Executive } from '../../../models/executive.model';
import { MonthlyIndicatorToken } from '../../../models/monthly-indicator-token.model';
import { MONTH_LABELS } from '../../../models/monthly-indicator.model';
import {
  buildIndicatorRequestMessage,
  buildWhatsAppLink,
  formatBrazilianPhone,
} from '../../../models/whatsapp';

/** One executive, resolved for sending — or blocked, with the reason visible. */
interface Recipient {
  name: string;
  role: string | null;
  formattedPhone: string | null;
  whatsappUrl: string | null;
  message: string;
}

/**
 * Presentational panel for a generated reporting link: the URL as text, a copy
 * control, and one WhatsApp send affordance per executive with a valid phone.
 * It renders inline inside the unified add-indicator dialog (link mode) and
 * inside the "Links anteriores" dialog, so it takes its data as inputs and owns
 * no navigation.
 */
@Component({
  selector: 'app-token-panel',
  imports: [MatButtonModule, MatIconModule, MatSnackBarModule],
  templateUrl: './token-panel.html',
  styleUrl: './token-panel.scss',
})
export class TokenPanel {
  readonly token = input.required<MonthlyIndicatorToken>();
  readonly executives = input.required<Executive[]>();

  private readonly snackBar = inject(MatSnackBar);

  readonly period = computed(() => `${MONTH_LABELS[this.token().month]}/${this.token().year}`);
  readonly formUrl = computed(
    () => `${window.location.origin}/monthly-indicator/${this.token().token}`,
  );

  /**
   * Every executive appears, including the ones that cannot be reached. Hiding
   * them would make "there is nobody to send to" indistinguishable from "the
   * phone is missing from the record", which is the actionable case.
   */
  readonly recipients = computed<Recipient[]>(() => {
    const period = this.period();
    const url = this.formUrl();
    return this.executives().map((executive) => {
      const message = buildIndicatorRequestMessage(executive.name, period, url);
      return {
        name: executive.name,
        role: executive.role,
        formattedPhone: formatBrazilianPhone(executive.phone),
        whatsappUrl: buildWhatsAppLink(executive.phone, message),
        message,
      };
    });
  });

  readonly reachable = computed(() => this.recipients().filter((r) => r.whatsappUrl !== null));
  readonly blocked = computed(() => this.recipients().filter((r) => r.whatsappUrl === null));

  copyLink(): void {
    // The link is always visible as text above, so a clipboard failure — common
    // outside a secure context — is a soft failure, not a dead end (RFC-001 §6).
    navigator.clipboard.writeText(this.formUrl()).then(
      () => this.snackBar.open('Link copiado!', 'Fechar', { duration: 2000 }),
      () =>
        this.snackBar.open(
          'Não foi possível copiar. O link está visível acima para copiar manualmente.',
          'Fechar',
          { duration: 4000 },
        ),
    );
  }
}
