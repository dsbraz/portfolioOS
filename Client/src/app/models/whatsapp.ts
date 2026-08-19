/**
 * Click-to-chat helpers for the monthly-indicator request flow (PRD-001 6.5).
 *
 * The recipient always comes from a registered executive phone — there is no
 * free-form number entry anywhere in the product.
 *
 * Every number carries its country prefix (product decision, 2026-08-19). The
 * fund's executives are not all in Brazil, so a number's country cannot be
 * inferred from its length: `(415) 555-1234` is a valid local number in the US
 * and, once a `55` is guessed onto it, also a plausible line in Paraná. Since
 * the indicator link is write access to a period, that guess would hand the
 * write to a stranger. The prefix is what removes the ambiguity, and it is
 * enforced at registration by
 * `Server/app/domain/validators.py:normalize_international_phone`.
 */

import { AbstractControl, ValidationErrors } from '@angular/forms';

/** E.164: "+" then 8–15 digits, country code included. */
const E164 = /^\+\d{8,15}$/;

/** Separators that are presentation only. A leading "00" is NOT one of them. */
const SEPARATORS = /[\s ().\-/]/g;

/** `+55` followed by a two-digit area code and an 8- or 9-digit subscriber. */
const BRAZILIAN_E164 = /^\+55(\d{2})(\d{8,9})$/;

/**
 * Normalizes a registered phone to E.164, or returns `null` when it does not
 * resolve. Absence and refusal collapse into `null` on purpose: both mean "no
 * send can be offered for this recipient".
 */
export function normalizeInternationalPhone(value: string | null | undefined): string | null {
  if (value == null) return null;

  const candidate = value.trim().replace(SEPARATORS, '');
  return E164.test(candidate) ? candidate : null;
}

/**
 * The recipient's number, shown before the send.
 *
 * A Brazilian number gets the shape the fund reads every day; a foreign one is
 * shown exactly as stored, because grouping rules differ per country and an
 * invented grouping would misrepresent the number.
 */
export function formatPhone(value: string | null | undefined): string | null {
  const normalized = normalizeInternationalPhone(value);
  if (normalized === null) return null;

  const brazilian = BRAZILIAN_E164.exec(normalized);
  if (brazilian === null) return normalized;

  const [, areaCode, subscriber] = brazilian;
  const head = subscriber.slice(0, -4);
  const tail = subscriber.slice(-4);
  return `+55 (${areaCode}) ${head}-${tail}`;
}

/**
 * Form validator for the executive's phone: absence is valid, a number without
 * its country prefix is not. Lives beside the normalizer so the rule the form
 * enforces and the rule the send obeys cannot drift apart — and mirrors
 * `normalize_international_phone` on the server, which is the authority.
 */
export function phoneCountryPrefixValidator(
  control: AbstractControl,
): ValidationErrors | null {
  const value = control.value;
  if (value == null || String(value).trim() === '') return null;
  return normalizeInternationalPhone(String(value)) === null
    ? { phoneCountryPrefix: true }
    : null;
}

/** First name only — the fund's template greets people by it. */
export function firstName(fullName: string): string {
  return fullName.trim().split(/\s+/)[0] ?? fullName;
}

/** The fund's standard message, already in use before the platform existed. */
export function buildIndicatorRequestMessage(
  recipientName: string,
  period: string,
  formUrl: string,
): string {
  return [
    `Olá ${firstName(recipientName)}. Tudo bem?`,
    `Segue o link para atualizações dos dados referentes a ${period}: ${formUrl}`,
    'Obrigado',
  ].join('\n');
}

/**
 * Official click-to-chat URL. Returns `null` when the phone is not normalizable,
 * so a caller can never build a send affordance for an unreachable recipient.
 */
export function buildWhatsAppLink(
  phone: string | null | undefined,
  message: string,
): string | null {
  const normalized = normalizeInternationalPhone(phone);
  if (normalized === null) return null;

  // wa.me addresses a number by digits alone; the country code stays.
  return `https://wa.me/${normalized.slice(1)}?text=${encodeURIComponent(message)}`;
}
