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

## Manage monthly-report links

On a startup page, `Gerar link` opens `Gerar link de indicador` for a month and
year; confirming with `Gerar` opens the panel `Link de indicador — {Mmm/AAAA}`.
The panel shows the link as text under `Link do formulário`, a `Copiar link de
{Mmm/AAAA}` control, and one `Enviar para {name} no WhatsApp` link per executive
with a valid registered phone. An executive whose phone does not resolve appears
as `Sem telefone válido` and gets no send control.

`Mais ações` → `Links anteriores` lists existing periods; `Abrir link de
{Mmm/AAAA}` opens the same panel. A startup and period have one token; generating
it again returns that token.

Preview the startup and period before `Gerar`. The interface cannot expire,
revoke, or delete a reporting link, and the recipient always comes from the
registered executive phone — there is no free-form number entry.
