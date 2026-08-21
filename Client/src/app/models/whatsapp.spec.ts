import {
  buildIndicatorRequestMessage,
  buildWhatsAppLink,
  firstName,
  formatPhone,
  normalizeInternationalPhone,
} from './whatsapp';

describe('normalizeInternationalPhone', () => {
  it('should keep any number that carries its country prefix', () => {
    expect(normalizeInternationalPhone('+55 (11) 91234-5678')).toBe('+5511912345678');
    expect(normalizeInternationalPhone('+1 415 555 1234')).toBe('+14155551234');
    expect(normalizeInternationalPhone('+351 912 345 678')).toBe('+351912345678');
    expect(normalizeInternationalPhone('+44 20 7946 0958')).toBe('+442079460958');
  });

  it('should refuse a number without the country prefix instead of guessing one', () => {
    // Regression: a foreign number in local format used to be prefixed with 55,
    // resolving to a plausible Brazilian line belonging to someone else. The
    // link is write access to a period, so a misread number hands that write
    // to a stranger.
    expect(normalizeInternationalPhone('(415) 555-1234')).toBeNull();
    expect(normalizeInternationalPhone('11 91234-5678')).toBeNull();
    expect(normalizeInternationalPhone('912345678')).toBeNull();
  });

  it('should refuse anything that is not a valid E.164 number', () => {
    expect(normalizeInternationalPhone('+55')).toBeNull();
    expect(normalizeInternationalPhone('+1234')).toBeNull();
    expect(normalizeInternationalPhone('ramal 22')).toBeNull();
    expect(normalizeInternationalPhone('')).toBeNull();
    expect(normalizeInternationalPhone(null)).toBeNull();
  });
});

describe('formatPhone', () => {
  it('should present a Brazilian number in the familiar shape', () => {
    expect(formatPhone('+5511912345678')).toBe('+55 (11) 91234-5678');
    expect(formatPhone('+551112345678')).toBe('+55 (11) 1234-5678');
  });

  it('should present a foreign number as stored, without inventing a grouping', () => {
    // Grouping rules differ per country; showing E.164 is honest and unambiguous.
    expect(formatPhone('+14155551234')).toBe('+14155551234');
    expect(formatPhone('+351912345678')).toBe('+351912345678');
  });

  it('should return null when the number does not resolve', () => {
    expect(formatPhone('12345')).toBeNull();
    expect(formatPhone(null)).toBeNull();
  });
});

describe('firstName', () => {
  it('should take only the first name for the greeting', () => {
    expect(firstName('Ana Costa Ribeiro')).toBe('Ana');
    expect(firstName('  Bruno  ')).toBe('Bruno');
  });
});

describe('buildIndicatorRequestMessage', () => {
  it('should follow the fund standard template, naming the startup', () => {
    const message = buildIndicatorRequestMessage(
      'Ana Costa',
      'Payface',
      'Jul/2026',
      'https://app/x',
    );

    expect(message).toBe(
      'Olá Ana. Tudo bem?\n' +
        'Segue o link para atualizações dos dados de Payface referentes a Jul/2026:\n' +
        'https://app/x\n' +
        'Obrigado',
    );
  });

  it('should keep the URL alone on its own line so chat clients linkify it', () => {
    // Glued to a sentence, some clients swallow neighbouring punctuation into
    // the URL or give up on linkifying. A line containing only the URL is the
    // robust form — and the easiest to tap.
    const message = buildIndicatorRequestMessage('Ana', 'Payface', 'Jul/2026', 'https://app/x');

    expect(message.split('\n')).toContain('https://app/x');
  });

  it('should never attach a gendered article to the startup name', () => {
    // A company name has no knowable grammatical gender, so the template uses
    // bare "de {name}" — never "da"/"do".
    const message = buildIndicatorRequestMessage('Ana', 'iuPay', 'Jul/2026', 'https://app/x');

    expect(message).toContain('dados de iuPay referentes');
    expect(message).not.toMatch(/\bd[ao] iuPay\b/);
  });

  it('should fall back to the nameless phrasing when the startup name is absent', () => {
    const message = buildIndicatorRequestMessage('Ana', '  ', 'Jul/2026', 'https://app/x');

    expect(message).toContain('dos dados referentes a Jul/2026:');
    expect(message.split('\n')).toContain('https://app/x');
    expect(message).not.toContain('de  ');
  });
});

describe('buildWhatsAppLink', () => {
  it('should build the official click-to-chat URL with the message encoded', () => {
    // wa.me takes digits only — the "+" is dropped, the country code is not.
    expect(buildWhatsAppLink('+55 (11) 91234-5678', 'Olá Ana')).toBe(
      'https://wa.me/5511912345678?text=Ol%C3%A1%20Ana',
    );
  });

  it('should build the URL for a foreign recipient too', () => {
    expect(buildWhatsAppLink('+1 415 555 1234', 'Hi')).toBe(
      'https://wa.me/14155551234?text=Hi',
    );
  });

  it('should return null when the phone does not resolve, so no send is offered', () => {
    expect(buildWhatsAppLink('(415) 555-1234', 'Olá')).toBeNull();
    expect(buildWhatsAppLink(null, 'Olá')).toBeNull();
  });
});
