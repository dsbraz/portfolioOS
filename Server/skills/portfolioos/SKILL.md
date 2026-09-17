---
name: portfolioos
description: Operates portfolioOS in an authenticated browser to inspect or change startups, indicators, meetings, deals, users, and reporting links. Use for any portfolioOS task. Use também para portfólio e investidas, indicadores mensais, reunião de conselho, transcrição ou conversa do Granola, preparação de agenda ou call, dealflow e estágios, monitoramento, executivos, usuários, convites, link de relatório mensal, cobrança de quem não reportou o mês, e apresentação, deck ou slides do portfólio para comitê e reunião de sócios.
---

# Operate portfolioOS

Route each request through the workflow guides bundled below:

1. Read the first guide in the published index. It is the required base workflow;
   apply its safety, record resolution, preview, confirmation, and verification
   rules to every task.
2. Match the user's request against the descriptions in the index and read each
   relevant specialized guide together with the base guide.
3. Do not ask the user to choose a workflow or memorize its name.

A guide is self-contained in its own folder. When it links to a file under its
`references/` directory, read that file completely before acting on it.

Use only the files bundled in this package. If a required file cannot be read,
stop and explain that the installed package is incomplete.

## Published workflows

- [`operar-portfolioos`](skills/operar-portfolioos/GUIDE.md): Consulta e administra o portfolioOS pelo navegador, incluindo startups, indicadores, reuniões, executivos, dealflow, usuários, convites e links. Use para qualquer tarefa na plataforma.
- [`cobrar-indicadores`](skills/cobrar-indicadores/GUIDE.md): Encontra as startups sem indicador no período no portfolioOS, gera os links de reporte após confirmação e monta a fila de cobrança por WhatsApp, com e-mail como alternativa. Use para cobrar, lembrar ou perguntar quem não reportou o mês.
- [`granola-reuniao`](skills/granola-reuniao/GUIDE.md): Obtém uma conversa do Granola pelo MCP conectado ou por um link compartilhado e a transforma em um registro de reunião no portfolioOS, com prévia. Use para registrar, salvar ou lançar uma reunião com uma investida.
- [`preparar-agenda`](skills/preparar-agenda/GUIDE.md): Prepara conversas com uma startup usando reuniões e indicadores do portfolioOS. Use para agenda, call, 1:1 ou para decidir o que acompanhar ou cobrar da investida.
- [`apresentacao-portfolio`](skills/apresentacao-portfolio/GUIDE.md): Monta a apresentação do portfólio na identidade BRQ a partir dos dados do portfolioOS, gerando o spec e construindo o .pptx pela skill brq-pptx. Use para deck, apresentação, slides ou material de comitê e de reunião de sócios sobre o portfólio.
