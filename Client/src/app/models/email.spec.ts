import {
  buildIndicatorRequestSubject,
  buildMailtoLink,
  emailValidator,
  normalizeContactEmail,
} from './email';
import { FormControl } from '@angular/forms';

describe('normalizeContactEmail', () => {
  it('should trim and lowercase, so one address has one shape', () => {
    expect(normalizeContactEmail('  Ana@Startup.com.BR ')).toBe('ana@startup.com.br');
    expect(normalizeContactEmail('john.miller+fundo@example.co.uk')).toBe(
      'john.miller+fundo@example.co.uk',
    );
  });

  it('should return null for absence or for an address we cannot compose to', () => {
    expect(normalizeContactEmail(null)).toBeNull();
    expect(normalizeContactEmail('')).toBeNull();
    expect(normalizeContactEmail('ana arroba startup')).toBeNull();
    expect(normalizeContactEmail('ana@startup')).toBeNull();
    expect(normalizeContactEmail('@startup.com')).toBeNull();
  });
});

describe('buildIndicatorRequestSubject', () => {
  it('should name the startup and the period, so the inbox is scannable', () => {
    expect(buildIndicatorRequestSubject('Vertah', 'julho/2026')).toBe(
      'Vertah — indicadores de julho/2026',
    );
  });
});

describe('buildMailtoLink', () => {
  it('should build a mailto with subject and body encoded', () => {
    const url = buildMailtoLink('ana@startup.com.br', 'Assunto x', 'Olá Ana.\nSegue o link');

    expect(url).toBe(
      'mailto:ana@startup.com.br?subject=Assunto%20x&body=Ol%C3%A1%20Ana.%0ASegue%20o%20link',
    );
  });

  it('should return null when the address does not resolve, so no send is offered', () => {
    expect(buildMailtoLink('ana arroba startup', 's', 'b')).toBeNull();
    expect(buildMailtoLink(null, 's', 'b')).toBeNull();
  });
});

describe('emailValidator', () => {
  it('should accept absence — an executive may have no e-mail', () => {
    expect(emailValidator(new FormControl(''))).toBeNull();
    expect(emailValidator(new FormControl(null))).toBeNull();
  });

  it('should flag an address the product cannot compose to', () => {
    expect(emailValidator(new FormControl('ana arroba startup'))).toEqual({ email: true });
    expect(emailValidator(new FormControl('ana@startup.com.br'))).toBeNull();
  });
});
