# Monitoring, startups, and startup records

Use this reference for `Monitoramento`, startup details, monthly indicators,
board meetings, executives, and monthly-report links.

## Monitor the portfolio

Open `Monitoramento`. Use `Mês anterior` and `Próximo mês` to select a period;
the interface does not advance beyond the current month. Each row opens through
the startup name, which is a link. Read:

- portfolio totals for revenue, estimated participation, monthly reporting, and
  board routines;
- the health distribution;
- each startup's name, status, revenue, cash, EBITDA/burn, headcount, and latest
  reported period.

The table lists only the startups tracked in the selected period. A startup that
exited appears in every month before its exit; in the exit month it appears only
if it already reported that month, and from then on it no longer appears;
exited startups are listed below the table, under `Encerradas`, with exit date
and type, each name a link to the startup page.

`Total da Participação` is an estimate based on annualized revenue times five and
the ownership percentage. Describe it as an estimate, not a recorded valuation.

## Manage startups

Create with `Nova Startup`. On a startup page, use `Editar` or `Mais ações` →
`Excluir startup`.

Fields: `Nome`, `Site`, `URL do Logotipo`, `Status`, `Setor`, `Data do
Investimento`, `% de Participação`, and `Observação`. Name, sector, and investment
date are required. Participation must be between 0 and 100. Status values are
`Saudável`, `Atenção`, and `Crítico`.

For read-only access to fields visible only in `Editar Startup`, open the dialog,
read without changing anything, and close with `Cancelar`.

## Record an exit

When the fund leaves a startup (sale, IPO, buyback, or the company shut down),
record the exit instead of deleting it: the history stays readable and the
startup stops being tracked. On the startup page, `Mais ações` → `Registrar
saída`. Fields: `Data da saída` (required; not in the future, not before the
investment date, not before the last month already reported — the message
names that month), `Tipo de saída` (required) and `Observações` (buyer, amount,
context). Types: `Venda (M&A ou secundária)`, `IPO`, `Recompra pelos
fundadores`, `Baixa (encerrou)` — a write-off is an exit of type `Baixa`.

Once recorded, the page shows `Acompanhamento encerrado` with the date and type,
and the header shows the `Encerrada` pill. `Adicionar indicador` stays, for
the numbers that arrive late: it fills by hand only (no link mode), and only
periods up to the exit month; a later period is refused. Existing indicators,
meetings and executives stay editable. An exited
startup has no reporting link: every link already sent stops working, whatever
its period, a new one cannot be generated, and `Links anteriores` is no longer
offered. Undoing the exit brings the old links back. A startup can exit only
once; to correct an entry, `Mais ações` → `Desfazer saída`, which makes it
tracked again, then record it anew.

Deleting a startup permanently cascades to its monthly indicators, meetings,
executives, and reporting links. It does not remove an independent deal with the
same company name.

## Manage monthly indicators

Open the `Indicadores Mensais` tab. The table shows period, revenue, cash,
EBITDA/burn, and headcount. Open a period with `Ver indicador de {Mmm/AAAA}` to
read all fields:

- month and year;
- monthly revenue and recurring-revenue percentage;
- gross margin, cash balance, headcount, and burn/EBITDA;
- achievements, challenges, and comments.

Use `Adicionar indicador`, or the row action `Ações do indicador de {period}` →
`Editar` or `Excluir`. A future period is invalid. Startup plus month and year is
unique: look for the period first and edit it if present.

The top KPI cards render missing numeric data as zero. Before asserting a real
zero, confirm it in the table or read view, where absence appears as `-` or `Não
informado`.

## Manage board meetings

Open `Reuniões de Conselho`. A row shows date and summary. Open it with
`Ver reunião de {dd/mm/aaaa}` to read `Data`, `Participantes`, `Resumo`,
`Pontos de Atenção`, and `Próximos passos`.

Use `Adicionar reunião`, or `Ações da reunião de {date}` → `Editar` or `Excluir`.
Date is required; other fields are optional. Duplicate dates are allowed, so use
participants and summary to disambiguate. The platform has no native transcript
or recording field.

## Manage executives

Open `Executivos`. The table shows name, role, email, and phone. Open a person
with `Ver executivo {name}` to also read LinkedIn. Use `Adicionar executivo`, or `Ações de {name}` → `Editar` or
`Excluir`. Only name is required. Names and emails are not unique; resolve the
person within the startup and compare role, email, or phone.

**The phone must carry its country prefix** (`+55 11 91234-5678`,
`+1 415 555 1234`). The fund's executives are not all in Brazil, so the platform
never infers a country: a number without `+` is refused when saving. If the
person dictates a local number, ask which country it belongs to instead of
assuming Brazil — an indicator link is write access to a period, and a misread
number would send it to a stranger.

## Manage monthly-report links

Both filling an indicator and generating a link start from `Adicionar
indicador`, which opens `Adicionar indicador — {Mmm/AAAA}`. Pick the period, then
the mode: `Preencher agora` fills the reportable zone plus the fund note, and
`Gerar link para a investida` creates the link. In link mode, `Gerar link` opens
the panel inline: the link as text under `Link do formulário`, a `Copiar link de
{Mmm/AAAA}` control, and one send control per reachable executive:
`Enviar por WhatsApp para {name}` when the phone carries its country code,
otherwise `Enviar por e-mail para {name}` with the reason shown under the name.
Both open the operator's own client with the message ready — the platform never
sends anything. An executive with neither channel appears as
`Sem canal de envio` and gets no send control.

`Mais ações` → `Links anteriores` lists existing periods; `Abrir link de
{Mmm/AAAA}` opens that panel for an existing token. A startup and period have one
token; generating it again returns that token.

The interface cannot expire, revoke, or delete a reporting link, and the
recipient always comes from the registered executive phone — there is no
free-form number entry.
