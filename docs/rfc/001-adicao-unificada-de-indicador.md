# RFC-001 — Adição unificada de indicador mensal

- **Tipo:** Design doc de engenharia
- **Status:** Em revisão
- **Autor(es):** Matheus Donangelo
- **Audiência:** Daniel Braz e Mauricio Bueno
- **Revisores:** Daniel Braz
- **Última atualização:** 2026-08-18
- **Fonte funcional:** [PRD-001 — Adição unificada de indicador](../prd/001-adicao-unificada-de-indicador.md)

> O PRD-001 é normativo para comportamento de produto. Esta RFC é normativa
> para a realização técnica. As pendências do PRD (expiração de link,
> procedência, envio em branco) não são resolvidas aqui; o desenho não as
> bloqueia.

## 1. Resumo executivo

**A adição de indicador será unificada no admin: o administrador terá um único
lugar — o diálogo "Adicionar indicador" — para definir se quer gerar um link
para a investida responder ou criar o registro ele mesmo.** O diálogo abre pelo
período (padrão: mês anterior), mostra o contexto do período já carregado na
página (indicador existente? link existente?) e só então oferece o modo. A ação
"Gerar link" sai do cabeçalho da página e o `TokenGenerateDialog` é removido.

A segunda metade da unificação é o contrato: a **zona reportada** (os oito
campos que a investida pode enviar) passa a ter uma única definição de
formulário no frontend — construída por uma factory compartilhada com os mesmos
validadores — consumida pelo diálogo do administrador e pelo formulário
público. `comments` é formalizado como **anotação do fundo**: seção própria nos
formulários do admin e na vista de leitura, ausente por contrato (e por teste)
do fluxo público.

O modo link termina num **painel do link**: a URL visível como texto
selecionável, ação de copiar e **Enviar por WhatsApp** — um `<a href>` real
para o click-to-chat oficial (`wa.me/<número>?text=…`), com o destinatário
escolhido entre os executivos da startup e a mensagem no modelo padrão do
fundo (primeiro nome, mês de referência, link). O painel é desenhado como
**contrato de máquina**: um agente de
IA com a sessão do administrador completa gerar→enviar usando apenas papéis e
nomes acessíveis, sem depender da área de transferência.

**Não há endpoint novo, mudança de schema nem migração.** A API atual já cobre
os dois efeitos; a unificação é de experiência e de contrato de campos, a
escolha de modo é orquestração do cliente sobre rotas existentes, e o envio por
WhatsApp não passa pelo backend — `wa.me` é externo e os executivos já chegam
carregados na página.

## 2. Contexto e escopo

Estado atual e seus defeitos, medidos no código:

- duas entradas em regiões distintas (`page-head-actions` e `sections-bar`),
  sendo que "Gerar link" aparece mesmo com a aba de Reuniões ativa;
- dois formulários com validações divergentes: o público valida limites
  (`MIN_MONEY`/`MAX_MONEY`/`MAX_PCT`, duplicados localmente em
  `report-form.ts`); o diálogo do administrador não valida limites no cliente;
- períodos-padrão divergentes: diálogo abre no mês corrente,
  `getPreviousMonthPeriod()` só existe no fluxo de token;
- `comments` renderizado dentro de "Qualitativos", sem distinção de autoria.

O backend já está correto quanto à zona de anotação: `PublicIndicatorSubmit` e
`PublicIndicatorData` omitem `comments`. Esta RFC transforma esse fato em
contrato testado.

### 2.1 Metas

- um único ponto de entrada, com o modo escolhido depois do período e com
  contexto do período visível antes da escolha;
- validação idêntica da zona reportada nos dois formulários, com uma única
  fonte de limites no frontend;
- anotação do fundo como seção própria na edição e na leitura, e garantida fora
  do fluxo público por teste de contrato;
- período-padrão unificado (mês anterior), com o mesmo validador de período
  futuro nos dois lados;
- painel do link com envio por WhatsApp (`wa.me`), destinatário vindo dos
  executivos já carregados — zero requisições novas;
- fluxo gerar→enviar operável por agente de navegador usando apenas semântica
  acessível, verificado por teste;
- nenhuma rota nova, nenhum schema alterado, nenhuma migração.

### 2.2 Não-metas

- expiração, revogação ou auditoria de tokens (pendência 1 do PRD);
- registro de procedência ou fila de aprovação (pendência 2);
- exigência de campo mínimo no envio público (pendência 3);
- tabela orientada a períodos pendentes;
- WhatsApp Business API, envio pelo servidor, envio agendado e rastreio de
  entrega — o envio se conclui dentro do WhatsApp de quem opera;
- mudanças visuais no formulário público além do reuso da factory;
- renomear rotas, entidades ou tabelas existentes.

### 2.3 Linguagem compartilhada

| Produto/UI | Nome de domínio | Definição normativa |
|---|---|---|
| indicador mensal | `MonthlyIndicator` | registro único por (startup, mês, ano) |
| link de indicador | `MonthlyIndicatorToken` | capacidade de escrita pública na zona reportada de um único período; não é credencial — é entregue só ao contato cadastrado (decisão de 14/08/2026) |
| zona reportada | reported fields | os 8 campos que a investida pode enviar: receita, % recorrente, margem, caixa, headcount, burn, conquistas, desafios |
| anotação do fundo | `comments` | texto exclusivo do administrador; nunca transita pelo fluxo público |
| entrada única | `AddIndicatorDialog` | diálogo com período, contexto e modo (preencher agora · gerar link) |
| painel do link | link panel | estado pós-geração do modo link: URL visível, copiar e enviar por WhatsApp |
| envio por WhatsApp | WhatsApp share | `<a href>` para o click-to-chat oficial `wa.me`, com mensagem pré-montada |

## 3. Arquitetura

### 3.1 Composição no frontend

```
models/indicator-form.ts        ← NOVO: única fonte do contrato no cliente
  INDICATOR_LIMITS              (espelha _MIN_MONEY/_MAX_MONEY/_MAX_PCT do backend)
  buildReportedIndicatorForm()  (FormGroup da zona reportada, validadores idênticos)
  futurePeriodValidator         (movido do diálogo; passa a ser compartilhado)

models/whatsapp.ts              ← NOVO: funções puras, testáveis sem Angular
  normalizeBrazilianPhone()     (dígitos; 10–11 → prefixa 55; inválido → null)
  formatBrazilianPhone()        (exibição do número normalizado na prévia)
  firstName()                   (primeiro token do nome, para a saudação)
  buildIndicatorRequestMessage() (modelo padrão do fundo: primeiro nome,
                                 mês de referência, link — ver §3.3)
  buildWhatsAppLink()           (wa.me/<dígitos>?text=<mensagem codificada>)

pages/startups/add-indicator-dialog/   ← NOVO: a entrada única + painel do link
pages/startups/indicator-form-dialog/  ← passa a ser SÓ edição e leitura
pages/startups/token-generate-dialog/  ← REMOVIDO
pages/report/report-form.ts            ← consome a factory; perde constantes locais
```

A regra de camadas do projeto permanece: páginas compõem, `models/` guarda o
contrato puro (sem Angular Material, testável isolado), serviços falam com a
API. O que é deliberado aqui: **compartilha-se a factory do FormGroup, não um
componente de template**. Os dois contextos visuais (diálogo denso e página
pública com seções numeradas) são legitimamente diferentes; o que divergia de
forma danosa era a validação, e é ela que passa a ter fonte única.

O `startup-detail` já carrega indicadores e tokens juntos (`loadAll`). O
diálogo recebe esse contexto por `MAT_DIALOG_DATA` e deriva os avisos de
período localmente — nenhuma chamada nova de rede ao abrir.

### 3.2 Estados do diálogo unificado

```
período (mês/ano, padrão mês anterior)
  └─ contexto do período (derivado dos dados já carregados)
       ├─ "Jul/2026 já possui indicador. Salvar substitui os campos preenchidos."
       └─ "Já existe um link para este período." (modo link devolve o mesmo)
  └─ modo: ◉ Preencher agora   ○ Gerar link para a investida
       ├─ preencher → zona reportada + seção "Anotações do fundo"
       └─ link      → explicação do que a investida verá
                       └─ após gerar: PAINEL DO LINK
                            ├─ URL visível como texto selecionável
                            ├─ Copiar (secundário, tolerante a falha)
                            └─ Enviar por WhatsApp
                                 ├─ destinatário: SÓ executivos com telefone cadastrado
                                 ├─ prévia: nome + número normalizado + mensagem
                                 └─ <a href="wa.me/..."> real, target _blank
  └─ ação primária: "Salvar indicador" | "Gerar link"
```

Regras de implementação:

- o seletor de modo tem **semântica de rádio** (`role="radiogroup"`,
  `aria-checked`), estilizado na família de chips — o modo é exclusivo, então a
  semântica correta é rádio, não `aria-pressed`;
- trocar de modo **esconde, não destrói** os controles do outro modo: o
  FormGroup persiste e o que foi digitado sobrevive à alternância (critério 6.1
  do PRD);
- a troca de conteúdo é anunciada (`aria-live="polite"` no painel do modo) e o
  foco permanece dentro do diálogo;
- o rótulo do botão primário acompanha o modo;
- validação de período futuro é a mesma função nos dois modos.

No modo link, a confirmação chama a rota existente (que é idempotente por
período — devolve o token existente), monta a URL e abre o painel do link. A
cópia para a área de transferência é ação secundária e tolerante a falha — o
link **sempre** está visível como texto, porque clipboard é indisponível fora
de contexto seguro e invisível para agentes.

### 3.3 Envio por WhatsApp e operabilidade por agente

O envio não passa pelo backend. `wa.me` é o click-to-chat oficial do WhatsApp:
abrir `https://wa.me/<dígitos>?text=<mensagem>` no navegador leva à conversa
com a mensagem pré-preenchida, que quem opera revisa e confirma dentro do
próprio WhatsApp. O produto termina ao abrir a URL; entrega não é rastreada.

**Destinatário.** O telefone vem **exclusivamente do cadastro da plataforma**:
os executivos da startup, que já chegam ao diálogo pelo `MAT_DIALOG_DATA` (a
página os carrega em `loadAll`). O painel lista os que têm telefone,
pré-selecionando o primeiro; **não existe entrada de número avulso** — a
mensagem carrega uma capacidade de escrita no período, e número não cadastrado
significa essa escrita entregue sem rastro de quem é. Telefone novo se cadastra no
executivo (aba Executivos), e o painel orienta esse caminho quando nenhum
executivo tem telefone. Antes de abrir o WhatsApp, o painel exibe nome e número
normalizado.

**Normalização** (`normalizeBrazilianPhone`, função pura): remove tudo que não é
dígito; 10–11 dígitos ganham o prefixo 55; 12–13 dígitos começando em 55
passam direto; qualquer outra forma é recusada com orientação — nunca se abre
`wa.me` com número que não normalizou.

**Mensagem** (`buildIndicatorRequestMessage`, função pura): o modelo padrão que
o fundo já usa hoje, parametrizado —

```
Olá {primeiro nome}. Tudo bem?
Segue o link para atualizações dos dados referentes a {mês de referência}: {link}
Obrigado
```

O primeiro nome é o primeiro token do nome do executivo selecionado ("Ana
Ribeiro" → "Ana"); o mês de referência usa o rótulo por extenso do período do
link ("julho/2026"). As quebras de linha sobrevivem ao `wa.me` via
`encodeURIComponent` (`%0A`) — o teste cobre a codificação. A mensagem é
pré-preenchida, não travada: quem envia ajusta no próprio WhatsApp antes de
confirmar.

**Contrato de máquina.** O fluxo inteiro é operável por um agente de navegador
com a sessão do administrador, na linha da seção *Machine-readable UI* do
AGENTS.md:

- "Enviar por WhatsApp" é um `<a href>` real com a URL completa **presente no
  DOM antes do clique** (`target="_blank" rel="noopener"`) — um agente pode ler
  o `href` em vez de clicar, o que também cobre ambientes sem segunda aba;
- o nome acessível identifica o destinatário: `Enviar por WhatsApp para
  {nome}`;
- o link gerado, o número normalizado e a mensagem são texto no DOM;
  confirmações usam `role="status"`;
- nenhum passo usa diálogo nativo do navegador, CAPTCHA ou clipboard como única
  via;
- o teste do fluxo percorre gerar→enviar **por papéis e nomes acessíveis**, sem
  seletores de implementação — se o teste passa, um agente genérico consegue.

### 3.4 Backend

Nenhuma mudança de comportamento. Esta RFC **reafirma** o contrato vigente e o
protege com testes:

- `MonthlyIndicatorBase`/`Update` (rotas de admin) incluem `comments`;
- `PublicIndicatorSubmit` e `PublicIndicatorData` **não** incluem `comments`;
- criação sobre período existente substitui campo a campo, sem apagar com
  vazio (`CreateMonthlyIndicator`); como `comments` não vem no payload público,
  o reenvio da investida preserva a anotação do fundo — essa propriedade passa
  a ter teste próprio;
- unicidade de token por (startup, período) já é constraint; a criação devolve
  o existente.

## 4. Contrato de campos e validação

| Campo | Tipo | Validação (idêntica nos dois formulários) | Público |
|---|---|---|---|
| `total_revenue` | moeda | `MIN_MONEY..MAX_MONEY` | sim |
| `recurring_revenue_pct` | percentual | `0..MAX_PCT` | sim |
| `gross_margin_pct` | percentual | `0..MAX_PCT` | sim |
| `cash_balance` | moeda | `MIN_MONEY..MAX_MONEY` | sim |
| `headcount` | inteiro | `MIN_HEADCOUNT..MAX_HEADCOUNT` (`0..2_147_483_647`, teto do `Integer` int32 da coluna), inteiro | sim |
| `ebitda_burn` | moeda | `MIN_MONEY..MAX_MONEY` | sim |
| `achievements` | texto longo | livre | sim |
| `challenges` | texto longo | livre | sim |
| `comments` | texto longo | livre | **não — anotação do fundo** |
| `month`/`year` | período | 1–12 / 2000–2100, não futuro | vem do token |

Os limites existem em dois lugares por natureza (Python e TypeScript). O risco
de divergência é mitigado por: (a) uma única fonte **por lado** —
`INDICATOR_LIMITS` no cliente, constantes de `monthly_indicator.py` no servidor
— com comentário cruzado apontando o par; (b) **teste de paridade** no
frontend, que constrói os dois formulários pela factory e afirma que cada campo
rejeita e aceita os mesmos valores-limite; (c) **teste-guarda** no backend
(seção 6) que trava a relação entre os schemas público e interno.

## 5. Contrato HTTP

Decisão explícita: **nenhum endpoint novo**. O modo é orquestração do cliente
sobre rotas que já existem e permanecem inalteradas:

| Rota | Papel na entrada única |
|---|---|
| `POST /api/startups/{id}/monthly-indicators` | modo "preencher agora" |
| `PATCH /api/startups/{id}/monthly-indicators/{iid}` | edição (com anotação) |
| `POST /api/startups/{id}/monthly-indicator-tokens` | modo "gerar link" (idempotente por período) |
| `GET /api/monthly-indicator/{token}` | contexto público — sem `comments` |
| `POST /api/monthly-indicator/{token}` | envio público — sem `comments` |

O envio por WhatsApp não aparece na tabela porque não é uma rota: `wa.me` é
destino externo, e o telefone do destinatário vem dos executivos já carregados
pela página — zero requisições adicionais.

## 6. Testes

**Frontend (novos):**

- diálogo abre com mês anterior; período futuro recusado;
- alternar modo preserva período e campos digitados;
- semântica de rádio do seletor de modo (`role`, `aria-checked`, setas);
- aviso quando o período já possui indicador; aviso e reuso quando já possui
  link;
- rótulo do botão primário por modo;
- **paridade de validação**: para cada campo da zona reportada, o valor-limite
  rejeitado num formulário é rejeitado no outro (ambos construídos pela
  factory);
- "Anotações do fundo" presente na edição e na leitura, ausente no público;
- falha de clipboard informada;
- **normalização de telefone**: tabela de casos — `(11) 99999-9999` → `5511999999999`,
  `5511999999999` → inalterado, `+55 11 99999-9999` → `5511999999999`,
  `999` → recusado;
- **URL do WhatsApp**: `href` contém o número normalizado e a mensagem
  codificada (`encodeURIComponent`) no modelo padrão — primeiro nome, mês de
  referência e link, com as quebras de linha preservadas (`%0A`);
- **primeiro nome**: "Ana Ribeiro" → "Ana"; nome de um token só → usado
  inteiro;
- painel do link expõe a URL como texto; o `href` do envio existe no DOM antes
  do clique;
- startup sem executivo com telefone → orientação para cadastrar na aba
  Executivos; ação de envio ausente do DOM (não desabilitada sem explicação);
- o painel não renderiza campo de número avulso;
- **fluxo de agente**: spec que percorre gerar→enviar exclusivamente por
  `getByRole`/nome acessível — falha se qualquer passo exigir seletor de
  implementação ou clipboard.

**Backend (novos, guarda de contrato):**

- `set(PublicIndicatorSubmit.model_fields) ==
  set(MonthlyIndicatorBase.model_fields) - {comments, month, year}` — se um
  campo novo entrar num lado só, o teste quebra e força a decisão consciente;
- resposta pública não serializa `comments` mesmo quando o indicador o possui;
- reenvio público sobre indicador com anotação preserva a anotação.

**Removidos:** specs do `TokenGenerateDialog` (componente extinto).

## 7. Acessibilidade

Aplicam-se os padrões já documentados no AGENTS.md, com os pontos específicos
desta entrega: radiogroup com navegação por setas; foco retido no diálogo na
troca de modo; `aria-live` polite para o conteúdo do modo; alvos ≥ 24px; anel
de foco para dentro em qualquer container rolável; erros de validação via
`mat-error` associado ao campo.

## 8. Compatibilidade e rollout

Sem migração e sem efeito sobre links já emitidos — eles continuam válidos e
abrem o mesmo formulário público.

Sequência de implementação em quatro incrementos, cada um entregável e testável
sozinho. **Os quatro estão entregues** (Fase 1 do plano de desenvolvimento,
encerrada em 18/08/2026); o status por incremento fica registrado abaixo.

1. **Contrato compartilhado** ✅ — `indicator-form.ts`, factory nos três
   formulários atuais, validação no diálogo do admin, testes de paridade e os
   guardas de backend. Corrige a assimetria de validação sem tocar na UX.
   Fecha com a máscara de moeda unificada nos dois diálogos do administrador.
2. **Entrada única** ✅ — `AddIndicatorDialog` com o painel do link (URL visível
   como texto + copiar), remoção do "Gerar link" do cabeçalho e do
   `TokenGenerateDialog`; `IndicatorFormDialog` reduzido a edição/leitura.
   O `token-generate-dialog` foi de fato removido da árvore.
3. **Envio por WhatsApp** ✅ — `whatsapp.ts` (normalização, mensagem, URL),
   seletor de destinatário no painel (extraído como `token-panel`, reutilizado
   pelo diálogo e pela lista de links) e o spec do fluxo por papéis/nomes que
   sela a operabilidade por agente.
4. **Zonas** ✅ — seção "Anotações do fundo" na edição e na vista de leitura.

## 9. Alternativas consideradas

| Alternativa | Vantagem | Motivo da rejeição |
|---|---|---|
| Manter dois diálogos, compartilhando só o contrato de campos | menor esforço | mantém a dupla atuação que o PRD elimina; o administrador segue escolhendo o caminho antes de ter contexto do período |
| Endpoint novo unificado (`mode` no payload) | contrato único no servidor | a API atual já cobre os dois efeitos; um endpoint novo duplica semântica sem eliminar os antigos |
| Wizard em passos (período → modo → campos) | uma decisão por tela | três telas para uma ação frequente; o diálogo único mostra o contexto do período de imediato |
| Componente de template compartilhado para os campos | zero duplicação visual | acopla dois contextos visuais legítimos; o que divergia de forma danosa era a validação, e a factory resolve isso com muito menos acoplamento |
| Gerar link criando registro vazio no período | um modo só | cria registro fantasma e confunde "pedi para reportar" com "reportado" na tabela e nos KPIs de report |
| WhatsApp Business API para envio pelo servidor | entrega rastreável, sem depender do WhatsApp de quem opera | exige conta Business, template aprovado, opt-in e infraestrutura de webhook — um projeto próprio; `wa.me` entrega o valor com um `<a href>` |
| `navigator.share()` (Web Share API) | folha de compartilhamento nativa, canal à escolha | indisponível em desktop de forma consistente e **opaca para agentes** — não há `href` para ler; o destino deixaria de ser determinístico |
| Manter só o copiar (status quo) | zero esforço | o envio continua fora do produto, sem destinatário sugerido, e o fluxo permanece invisível para automação — exatamente o problema que o PRD ataca |

## 10. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Administrador não encontra "Gerar link" no lugar novo | o modo é visível assim que o diálogo abre; "Links anteriores" permanece no overflow; monitorar o volume de links gerados (métrica do PRD) |
| Sobrescrita silenciosa segue existindo | aviso de contexto no diálogo cobre o caso do admin; o caso do reenvio público é a pendência 2 do PRD, deliberadamente fora |
| Divergência futura de limites entre TypeScript e Python | fonte única por lado, comentário cruzado, teste de paridade no cliente e guarda de schema no servidor |
| Crescimento de complexidade do diálogo | estados enumerados na seção 3.2, um spec por estado; o componente não acumula responsabilidade de edição |
| Número errado recebe o link (capacidade de escrita no período) | destinatário vem exclusivamente do cadastro de executivos — sem número avulso; prévia obrigatória com nome + número normalizado |
| Telefones cadastrados em formato livre | normalização com recusa explícita e orientação para corrigir o cadastro — `wa.me` nunca abre com número que não normalizou; casos cobertos por teste |
| Mudança no contrato do `wa.me` | construção da URL isolada em função pura única, com teste; uma mudança externa é uma edição de um arquivo |

## 11. Verificação e rastreabilidade

| Critério do PRD | Verificação |
|---|---|
| 6.1 — entrada única, contexto e modos | specs do `AddIndicatorDialog` (seção 6) |
| 6.2 — paridade e ausência de `comments` | teste de paridade + guardas de backend |
| 6.3 — zonas na edição | spec do `IndicatorFormDialog` |
| 6.4 — zonas na leitura | spec do read view |
| 6.5 — envio por WhatsApp e operabilidade por agente | specs de normalização e URL + spec do fluxo por papéis/nomes (seção 6) |
| Guardrail de valores fora dos limites | validação simétrica + testes de limite |

## 12. Decisões e aprovações

| Decisão | Status |
|---|---|
| Entrada única no admin, modo dentro do diálogo | fechada no PRD |
| Nenhum endpoint novo | fechada nesta RFC |
| Factory compartilhada em vez de componente compartilhado | fechada nesta RFC |
| Envio via `wa.me` (client-side), sem Business API | fechada no PRD |
| Destinatário exclusivamente do telefone cadastrado (executivos) | fechada no PRD |
| Operabilidade por agente como critério testável | fechada no PRD (jornada 6.5) |
| Aprovação do desenho | pendente — Daniel Braz |
