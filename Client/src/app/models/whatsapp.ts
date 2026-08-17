/**
 * Click-to-chat helpers for the monthly-indicator request flow (PRD-001 6.5).
 *
 * The recipient always comes from a registered executive phone — there is no
 * free-form number entry anywhere in the product.
 */

/** Digits of a Brazilian number, country code included: 55 + DDD + 8 or 9 digits. */
const BRAZILIAN_E164_DIGITS = /^55\d{2}9?\d{8}$/;

/**
 * Normalizes a registered phone to the digits `wa.me` expects.
 *
 * A local number (DDD + 8 or 9 digits) gains the +55 country code. Anything that
 * does not resolve to a Brazilian number returns `null` so the caller can refuse
 * the send and point at the executive record, instead of guessing.
 */
export function normalizeBrazilianPhone(value: string | null | undefined): string | null {
  if (value == null) return null;

  const digits = value.replace(/\D/g, '');
  if (digits.length === 0) return null;

  const withCountryCode = digits.length === 10 || digits.length === 11 ? `55${digits}` : digits;
  return BRAZILIAN_E164_DIGITS.test(withCountryCode) ? withCountryCode : null;
}

/** `+55 (11) 91234-5678` — for showing the recipient before the send. */
export function formatBrazilianPhone(value: string | null | undefined): string | null {
  const normalized = normalizeBrazilianPhone(value);
  if (normalized === null) return null;

  const areaCode = normalized.slice(2, 4);
  const subscriber = normalized.slice(4);
  const head = subscriber.slice(0, subscriber.length - 4);
  const tail = subscriber.slice(-4);
  return `+55 (${areaCode}) ${head}-${tail}`;
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
  const normalized = normalizeBrazilianPhone(phone);
  if (normalized === null) return null;

  return `https://wa.me/${normalized}?text=${encodeURIComponent(message)}`;
}
