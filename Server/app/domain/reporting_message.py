"""The e-mails that ask an investee for the monthly indicators.

The reader is a founder or a senior executive: short, courteous, no pressure,
and honest about what the form allows (it accepts a partial answer and takes a
resubmission on the same link).

The initial e-mail exists twice: here, for the monthly job, and in
`Client/src/app/models/reporting-message.ts`, for the panel's manual e-mail.
Both are pinned to `reporting-message.cases.json`, so a wording change on one
side fails a test instead of making the two requests disagree. The reminder only
the job sends. The signature is not part of the contract: a manual e-mail
carries the operator's own.
"""

from dataclasses import dataclass

from app.domain.models.monthly_report_dispatch import DispatchKind

MONTH_NAMES_FULL = {
    1: "janeiro",
    2: "fevereiro",
    3: "março",
    4: "abril",
    5: "maio",
    6: "junho",
    7: "julho",
    8: "agosto",
    9: "setembro",
    10: "outubro",
    11: "novembro",
    12: "dezembro",
}


@dataclass(frozen=True)
class ReportingMessage:
    subject: str
    body: str


def build_reporting_email(
    kind: DispatchKind,
    executive_name: str,
    startup_name: str,
    month: int,
    year: int,
    form_url: str,
    signature: str | None = None,
) -> ReportingMessage:
    names = executive_name.split()
    greeting = f"Olá, {names[0]}." if names else "Olá."
    startup = startup_name.strip()
    period = f"{MONTH_NAMES_FULL[month]}/{year}"
    # Bare "de", never a gendered article: a company name has no knowable
    # grammatical gender. A blank name degrades the sentence instead of breaking.
    of_startup = f" de {startup}" if startup else ""
    topic = f"indicadores de {period}"
    subject = f"{startup} — {topic}" if startup else topic.capitalize()

    # The URL stands alone on its own line so mail clients linkify it whole.
    if kind is DispatchKind.REMINDER:
        subject = f"Lembrete: {startup} — {topic}" if startup else f"Lembrete: {topic}"
        paragraphs = [
            greeting,
            f"Passando para lembrar dos indicadores{of_startup} referentes a {period}, "
            f"que ainda não recebemos. O formulário continua no mesmo link:\n{form_url}",
            "Se ajudar, envie o que já estiver fechado e complete depois. "
            "Se esta mensagem cruzou com o seu envio, por favor desconsidere.",
            "Obrigado.",
        ]
    else:
        paragraphs = [
            greeting,
            f"Já está disponível o formulário de indicadores{of_startup} referentes a "
            f"{period}:\n{form_url}",
            "O preenchimento leva poucos minutos. Se algum número ainda não estiver "
            "fechado, envie o que tiver e complete depois pelo mesmo link.",
            "Obrigado pela parceria.",
        ]

    body = "\n\n".join(paragraphs)
    if signature and signature.strip():
        body = f"{body}\n{signature.strip()}"
    return ReportingMessage(subject=subject, body=body)
