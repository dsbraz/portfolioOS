/**
 * E-mail as the fallback channel for the monthly-indicator request (PRD-001
 * 6.5). It mirrors the WhatsApp path exactly: the product composes the message
 * and hands it to the operator's own mail client through `mailto:`, which then
 * confirms and sends. Nothing is delivered by the platform, so no credentials,
 * no outbound infrastructure, and no delivery tracking — the same guarantee
 * that keeps every send behind a human confirmation.
 *
 * The recipient is always a registered executive address; there is no
 * free-form entry here either.
 */

import { AbstractControl, ValidationErrors } from '@angular/forms';

/**
 * One "@", no spaces, dotted domain. Deliberately not the full RFC 5322
 * grammar: this refuses an address we cannot compose to, it does not certify
 * deliverability. Mirrors `normalize_contact_email` on the server, which is the
 * authority.
 */
const EMAIL = /^[^@\s]+@[^@\s.]+(\.[^@\s.]+)+$/;

/** Lowercased and trimmed, or `null` when absent or unusable. */
export function normalizeContactEmail(value: string | null | undefined): string | null {
  if (value == null) return null;

  const candidate = value.trim().toLowerCase();
  if (!candidate) return null;

  return EMAIL.test(candidate) ? candidate : null;
}

/** Names the startup and the period so the message is scannable in an inbox. */
export function buildIndicatorRequestSubject(startupName: string, period: string): string {
  return `${startupName} — indicadores de ${period}`;
}

/**
 * `mailto:` with subject and body encoded. Returns `null` when the address does
 * not resolve, so a caller can never offer a send to an unreachable recipient.
 */
export function buildMailtoLink(
  email: string | null | undefined,
  subject: string,
  body: string,
): string | null {
  const normalized = normalizeContactEmail(email);
  if (normalized === null) return null;

  const query = `subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  return `mailto:${normalized}?${query}`;
}

/** Form validator: absence is valid, an unusable address is not. */
export function emailValidator(control: AbstractControl): ValidationErrors | null {
  const value = control.value;
  if (value == null || String(value).trim() === '') return null;
  return normalizeContactEmail(String(value)) === null ? { email: true } : null;
}
