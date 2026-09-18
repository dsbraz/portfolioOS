import { Component, computed, inject, input } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { Executive } from '../../../models/executive.model';
import { MonthlyIndicatorToken } from '../../../models/monthly-indicator-token.model';
import { formatPeriod } from '../../../models/formatters';
import { MONTH_LABELS_FULL } from '../../../models/monthly-indicator.model';

interface RecipientBase {
  name: string;
  role: string | null;
  message: string;
}

/**
 * One executive and the single channel the link goes out by: WhatsApp when the
 * phone carries its country code, otherwise e-mail. `notice` says why WhatsApp
 * was not used, so the record can be fixed instead of the detour becoming habit.
 */
type ReachableRecipient = RecipientBase &
  (
    | { channel: 'whatsapp'; contact: string; url: string }
    | { channel: 'email'; contact: string; url: string; notice: string }
  );
type BlockedRecipient = RecipientBase & { channel: null; notice: string };
type Recipient = ReachableRecipient | BlockedRecipient;

/**
 * Presentational panel for a generated reporting link: the URL as text, a copy
 * control, and one send link per reachable executive. Both channels only open
 * the operator's own app with the message ready — nothing is sent from here.
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
  /** Names the startup in the message body and in the e-mail subject. */
  readonly startupName = input.required<string>();

  private readonly snackBar = inject(MatSnackBar);

  readonly period = computed(() => formatPeriod(this.token().month, this.token().year));
  /**
   * The name as the message and the subject both use it. Derived once so the
   * two cannot disagree about a blank one, and trimmed because the record can
   * carry padding the reader would see.
   */
  private readonly startup = computed(() => this.startupName()?.trim() ?? '');
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
   */
  readonly recipients = computed<Recipient[]>(() =>
    this.executives().map((executive) => this.toRecipient(executive)),
  );

  readonly reachable = computed(() =>
    this.recipients().filter((r): r is ReachableRecipient => r.channel !== null),
  );
  readonly blocked = computed(() =>
    this.recipients().filter((r): r is BlockedRecipient => r.channel === null),
  );

  /**
   * Whether the WhatsApp guidance applies at all. That send lands on WhatsApp's
   * own page offering the desktop app or WhatsApp Web, which is worth
   * explaining — but only where a WhatsApp button exists. Otherwise the hint
   * sends the reader hunting for an affordance the panel never rendered.
   */
  readonly hasWhatsAppChannel = computed(() =>
    this.reachable().some((r) => r.channel === 'whatsapp'),
  );
  /** Same rule, other channel: guidance follows the affordance, both ways. */
  readonly hasEmailChannel = computed(() =>
    this.reachable().some((r) => r.channel === 'email'),
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

  private toRecipient(executive: Executive): Recipient {
    const phone = executive.phone?.trim();
    const email = executive.email?.trim();
    const firstName = executive.name.trim().split(/\s+/)[0];
    // The fund's standard message, already in use before the platform existed —
    // now naming the startup, so a contact who answers for several investees can
    // tell the requests apart. The name takes bare "de" and never a gendered
    // article: a company name has no knowable grammatical gender, and "da
    // Payface" is a guess the template must not make.
    //
    // The URL stands alone on its own line: glued to a sentence, chat clients
    // can swallow neighbouring punctuation into the link or fail to linkify it
    // at all. (WhatsApp also needs a host with a dot, so `localhost` stays
    // plain text in development no matter the formatting.)
    // A blank name degrades the sentence instead of breaking the panel.
    const startup = this.startup();
    const whose = startup ? `dos dados de ${startup}` : 'dos dados';
    const message = [
      `Olá ${firstName}. Tudo bem?`,
      `Segue o link para atualizações ${whose} referentes a ${this.messagePeriod()}:`,
      this.formUrl(),
      'Obrigado',
    ].join('\n');
    const base = { name: executive.name, role: executive.role, message };

    // Records saved before the country code became mandatory may lack it.
    if (phone?.startsWith('+')) {
      const url = `https://wa.me/${phone.replace(/\D/g, '')}?text=${encodeURIComponent(message)}`;
      return { ...base, channel: 'whatsapp', contact: phone, url };
    }

    const notice = phone ? 'Telefone sem código do país' : 'Sem telefone cadastrado';
    if (!email) {
      return { ...base, channel: null, notice };
    }

    const subject = `${startup} — indicadores de ${this.messagePeriod()}`;
    // The address is encoded too: a "?" or "," in it would otherwise add
    // recipients to the mail. "@" stays literal for mail clients that do not
    // decode it.
    const address = encodeURIComponent(email).replace('%40', '@');
    const url =
      `mailto:${address}?subject=${encodeURIComponent(subject)}` +
      `&body=${encodeURIComponent(message)}`;
    return { ...base, channel: 'email', contact: email, url, notice };
  }
}
