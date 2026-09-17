import { Component, computed, inject, input } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { Executive } from '../../../models/executive.model';
import { MonthlyIndicatorToken } from '../../../models/monthly-indicator-token.model';
import { formatPeriod } from '../../../models/formatters';
import { MONTH_LABELS_FULL } from '../../../models/monthly-indicator.model';

/**
 * One executive and the single channel the link goes out by: WhatsApp when the
 * phone carries its country code, otherwise e-mail. `notice` says why WhatsApp
 * was not used, so the record can be fixed instead of the detour becoming habit.
 */
interface Recipient {
  name: string;
  role: string | null;
  channel: 'whatsapp' | 'email' | null;
  contact: string | null;
  url: string | null;
  notice: string | null;
  message: string;
}

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
  /** Names the startup in the e-mail subject. */
  readonly startupName = input<string>('');

  private readonly snackBar = inject(MatSnackBar);

  readonly period = computed(() => formatPeriod(this.token().month, this.token().year));
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

  readonly reachable = computed(() => this.recipients().filter((r) => r.channel !== null));
  readonly blocked = computed(() => this.recipients().filter((r) => r.channel === null));

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

  private toRecipient({ name, role, phone, email }: Executive): Recipient {
    const firstName = name.trim().split(/\s+/)[0];
    // The fund's standard message, already in use before the platform existed.
    const message = [
      `Olá ${firstName}. Tudo bem?`,
      `Segue o link para atualizações dos dados referentes a ${this.messagePeriod()}: ${this.formUrl()}`,
      'Obrigado',
    ].join('\n');
    const base = { name, role, message };

    // The country code is never guessed: the fund's executives are not all in
    // Brazil. Records saved before the rule may still lack it.
    if (phone?.trim().startsWith('+')) {
      const digits = phone.replace(/\D/g, '');
      const url = `https://wa.me/${digits}?text=${encodeURIComponent(message)}`;
      return { ...base, channel: 'whatsapp', contact: phone, url, notice: null };
    }

    const notice = phone?.trim() ? 'Telefone sem código do país' : 'Sem telefone cadastrado';
    if (!email?.trim()) {
      return { ...base, channel: null, contact: null, url: null, notice };
    }

    const subject = `${this.startupName()} — indicadores de ${this.messagePeriod()}`;
    // The address is encoded too: a "?" or "," in it would otherwise add
    // recipients to the mail. "@" stays literal for mail clients that do not
    // decode it.
    const address = encodeURIComponent(email.trim()).replace('%40', '@');
    const url =
      `mailto:${address}?subject=${encodeURIComponent(subject)}` +
      `&body=${encodeURIComponent(message)}`;
    return { ...base, channel: 'email', contact: email, url, notice };
  }
}
