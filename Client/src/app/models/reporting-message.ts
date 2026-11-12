import { MONTH_LABELS_FULL } from './monthly-indicator.model';

export interface ReportingMessageInput {
  executiveName: string;
  startupName: string;
  month: number;
  year: number;
  formUrl: string;
}

export interface ReportingMessage {
  subject: string;
  body: string;
}

const periodOf = (input: ReportingMessageInput) =>
  `${MONTH_LABELS_FULL[input.month]}/${input.year}`;

/**
 * The short chat message the panel puts in WhatsApp — the fund's standard text,
 * already in use before the platform existed.
 */
export function buildReportingChatMessage(input: ReportingMessageInput): string {
  const firstName = input.executiveName.trim().split(/\s+/)[0];
  // Trimmed because the record can carry padding the reader would see.
  const startup = input.startupName?.trim() ?? '';
  // Names the startup, so a contact who answers for several investees can tell
  // the requests apart. Bare "de" and never a gendered article: a company name
  // has no knowable grammatical gender, and "da Payface" is a guess the template
  // must not make. A blank name degrades the sentence instead of breaking it.
  const whose = startup ? `dos dados de ${startup}` : 'dos dados';
  // The URL stands alone on its own line: glued to a sentence, chat clients can
  // swallow neighbouring punctuation into the link or fail to linkify it at all.
  // (WhatsApp also needs a host with a dot, so `localhost` stays plain text in
  // development no matter the formatting.)
  return [
    `Olá ${firstName}. Tudo bem?`,
    `Segue o link para atualizações ${whose} referentes a ${periodOf(input)}:`,
    input.formUrl,
    'Obrigado',
  ].join('\n');
}

/**
 * The e-mail asking for the month's indicators. The reader is a founder or a
 * senior executive: short, courteous, and honest about what the form allows (a
 * partial answer, completed later on the same link).
 *
 * The monthly job sends the same e-mail (`Server/app/domain/reporting_message.py`).
 * Both are pinned to `reporting-message.cases.json`; the job also appends the
 * fund's signature, which a manual e-mail gets from the operator's own client.
 */
export function buildReportingEmail(input: ReportingMessageInput): ReportingMessage {
  const firstName = input.executiveName.trim().split(/\s+/)[0];
  const greeting = firstName ? `Olá, ${firstName}.` : 'Olá.';
  const startup = input.startupName?.trim() ?? '';
  const period = periodOf(input);
  const ofStartup = startup ? ` de ${startup}` : '';
  const topic = `indicadores de ${period}`;
  const subject = startup ? `${startup} — ${topic}` : `I${topic.slice(1)}`;
  const body = [
    greeting,
    `Já está disponível o formulário de indicadores${ofStartup} referentes a ${period}:\n${input.formUrl}`,
    'O preenchimento leva poucos minutos. Se algum número ainda não estiver fechado, ' +
      'envie o que tiver e complete depois pelo mesmo link.',
    'Obrigado pela parceria.',
  ].join('\n\n');
  return { subject, body };
}
