import {
  buildIndicatorRequestMessage,
  buildWhatsAppLink,
  firstName,
  formatBrazilianPhone,
  normalizeBrazilianPhone,
} from './whatsapp';

describe('normalizeBrazilianPhone', () => {
  it('should add the country code to a local number', () => {
    expect(normalizeBrazilianPhone('(11) 91234-5678')).toBe('5511912345678');
    expect(normalizeBrazilianPhone('11 1234-5678')).toBe('551112345678');
  });

  it('should keep a number that already carries the country code', () => {
    expect(normalizeBrazilianPhone('+55 (11) 91234-5678')).toBe('5511912345678');
  });

  it('should refuse anything that is not a Brazilian number', () => {
    // Refusing beats guessing: the send is offered only for a number we resolved.
    expect(normalizeBrazilianPhone('12345')).toBeNull();
    expect(normalizeBrazilianPhone('+1 415 555 0100')).toBeNull();
    expect(normalizeBrazilianPhone('ramal 22')).toBeNull();
    expect(normalizeBrazilianPhone('')).toBeNull();
    expect(normalizeBrazilianPhone(null)).toBeNull();
  });
});

describe('formatBrazilianPhone', () => {
  it('should present the resolved recipient number', () => {
    expect(formatBrazilianPhone('11912345678')).toBe('+55 (11) 91234-5678');
    expect(formatBrazilianPhone('1112345678')).toBe('+55 (11) 1234-5678');
  });

  it('should return null when the number does not resolve', () => {
    expect(formatBrazilianPhone('12345')).toBeNull();
  });
});

describe('firstName', () => {
  it('should take only the first name for the greeting', () => {
    expect(firstName('Ana Costa Ribeiro')).toBe('Ana');
    expect(firstName('  Bruno  ')).toBe('Bruno');
  });
});

describe('buildIndicatorRequestMessage', () => {
  it('should follow the fund standard template', () => {
    const message = buildIndicatorRequestMessage('Ana Costa', 'Jul/2026', 'https://app/x');

    expect(message).toBe(
      'Olá Ana. Tudo bem?\n' +
        'Segue o link para atualizações dos dados referentes a Jul/2026: https://app/x\n' +
        'Obrigado',
    );
  });
});

describe('buildWhatsAppLink', () => {
  it('should build the official click-to-chat URL with the message encoded', () => {
    const url = buildWhatsAppLink('(11) 91234-5678', 'Olá Ana');

    expect(url).toBe('https://wa.me/5511912345678?text=Ol%C3%A1%20Ana');
  });

  it('should return null when the phone does not resolve, so no send is offered', () => {
    expect(buildWhatsAppLink('12345', 'Olá')).toBeNull();
    expect(buildWhatsAppLink(null, 'Olá')).toBeNull();
  });
});
