# Public forms

Use this reference only when the user opens a public invitation or monthly-report
link themselves. These pages do not require the normal authenticated navigation.

## User invitation

`/user-invites/{token}` shows `Convite de acesso` and asks for email, username,
password, and password confirmation before `Concluir cadastro`.

The agent must not fill this form because it contains credentials. Let the user
complete it directly. Resume only after they report completion or the browser
shows a non-sensitive result.

## Monthly report

`/monthly-indicator/{token}` shows the startup and period and may contain existing
values. Fields include revenue, recurring-revenue percentage, gross margin, cash,
headcount, burn/EBITDA, `Destaques do mês`, and `Próximos passos e necessidades`.
It does not expose or change the internal `Comentários` field.

Before `Enviar relatório`, preview the startup, period, and every final field and
obtain explicit confirmation. Submission updates the single indicator for that
startup and period; it does not create version history.

Clearing an existing numeric value in the public form may preserve the old value
because the current update ignores null fields. To intentionally clear a number,
use the authenticated internal indicator editor instead and preview that change.

Never copy, quote, or expose the token. If the link is not already open, ask the
user to open it directly rather than paste it into chat.
