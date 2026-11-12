import cases from './reporting-message.cases.json';
import { buildReportingChatMessage, buildReportingEmail } from './reporting-message';

// The server's monthly job reads the same file
// (Server/tests/unit/test_reporting_message.py), so the e-mail it sends and the
// one the panel prepares cannot drift apart. The reminder only the job sends.
describe('buildReportingEmail', () => {
  for (const testCase of cases.filter((c) => c.kind === 'initial')) {
    it(`matches the shared case: ${testCase.name}`, () => {
      const message = buildReportingEmail(testCase.input);

      expect(message.subject).toBe(testCase.subject);
      expect(message.body).toBe(testCase.body);
    });
  }
});

describe('buildReportingChatMessage', () => {
  const input = {
    executiveName: '  Ana   Souza ',
    startupName: ' Payface ',
    month: 7,
    year: 2026,
    formUrl: 'https://portfolio.example.com/monthly-indicator/abc',
  };

  it('keeps the short standard text, with the URL on its own line', () => {
    expect(buildReportingChatMessage(input)).toBe(
      'Olá Ana. Tudo bem?\n' +
        'Segue o link para atualizações dos dados de Payface referentes a julho/2026:\n' +
        'https://portfolio.example.com/monthly-indicator/abc\n' +
        'Obrigado',
    );
  });

  it('degrades a blank startup name instead of breaking the sentence', () => {
    expect(buildReportingChatMessage({ ...input, startupName: ' ' })).toContain(
      'atualizações dos dados referentes a julho/2026:',
    );
  });
});
