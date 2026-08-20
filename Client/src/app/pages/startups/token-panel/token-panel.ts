import { Component, computed, inject, input } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { Executive } from '../../../models/executive.model';
import { MonthlyIndicatorToken } from '../../../models/monthly-indicator-token.model';
import { MONTH_LABELS, MONTH_LABELS_FULL } from '../../../models/monthly-indicator.model';
import {
  buildIndicatorRequestSubject,
  buildMailtoLink,
  normalizeContactEmail,
} from '../../../models/email';
import {
  buildIndicatorRequestMessage,
  buildWhatsAppLink,
  formatPhone,
} from '../../../models/whatsapp';

/** One executive, resolved for sending — or blocked, with the reason visible. */
interface Recipient {
  name: string;
  role: string | null;
  formattedPhone: string | null;
  email: string | null;
  whatsappUrl: string | null;
  mailtoUrl: string | null;
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
  /** Names the startup in the e-mail subject. */
  readonly startupName = input<string>('');

  private readonly snackBar = inject(MatSnackBar);

  readonly period = computed(() => `${MONTH_LABELS[this.token().month]}/${this.token().year}`);
  // The fund's message names the month in full ("julho/2026"); the title and the
  // copy control keep the compact form.
  private readonly messagePeriod = computed(
    () => `${MONTH_LABELS_FULL[this.token().month]}/${this.token().year}`,
  );
  readonly formUrl = computed(
    () => `${window.location.origin}/monthly-indicator/${this.token().token}`,
  );

  /**
   * Every executive appears, including the ones that cannot be reached. Hiding
   * them would make "there is nobody to send to" indistinguishable from "the
   * contact is missing from the record", which is the actionable case.
   *
   * Two channels, same message: WhatsApp is the fund's habit and comes first;
   * e-mail is the fallback that keeps an executive reachable when the phone is
   * missing or unusable. Both hand the composed message to the operator's own
   * client, which is where the send is confirmed.
   */
  readonly recipients = computed<Recipient[]>(() => {
    const messagePeriod = this.messagePeriod();
    const url = this.formUrl();
    const subject = buildIndicatorRequestSubject(this.startupName(), messagePeriod);
    return this.executives().map((executive) => {
      const message = buildIndicatorRequestMessage(executive.name, messagePeriod, url);
      return {
        name: executive.name,
        role: executive.role,
        formattedPhone: formatPhone(executive.phone),
        email: normalizeContactEmail(executive.email),
        whatsappUrl: buildWhatsAppLink(executive.phone, message),
        mailtoUrl: buildMailtoLink(executive.email, subject, message),
        message,
      };
    });
  });

  /** Reachable by at least one channel; blocked only when neither resolves. */
  readonly reachable = computed(() =>
    this.recipients().filter((r) => r.whatsappUrl !== null || r.mailtoUrl !== null),
  );
  readonly blocked = computed(() =>
    this.recipients().filter((r) => r.whatsappUrl === null && r.mailtoUrl === null),
  );

  /**
   * Whether the WhatsApp guidance applies at all. That send lands on WhatsApp's
   * own page offering the desktop app or WhatsApp Web, which is worth
   * explaining — but only where a WhatsApp button exists. Otherwise the hint
   * sends the reader hunting for an affordance the panel never rendered.
   */
  readonly hasWhatsAppChannel = computed(() =>
    this.reachable().some((r) => r.whatsappUrl !== null),
  );

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
