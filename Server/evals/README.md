# Avaliações de skill (Camada 2)

Testes de comportamento de agente. Onde a Camada 1 (Playwright) prova que a
**plataforma** funciona, esta camada pergunta se o **agente cumpre as regras**
que as skills declaram — algo que nenhum lint alcança, porque o lint só verifica
que a regra está escrita.

## Como rodar

```bash
# 1. Sobe a plataforma de avaliação (portas 8100/4300 — o stack de
#    desenvolvimento continua intocado em 8000/4200)
docker compose -f docker-compose.e2e.yml -f docker-compose.evals.yml up -d --wait

# 2. Roda os cenários
cd Server/evals
python3 runner.py --json relatorio.json

# 3. Um cenário só
python3 runner.py --caso leitura-nao-escreve
```

Usa a sessão do próprio operador (`claude -p`). **Não** roda no CI: é lento,
custa dinheiro e é não-determinístico — três propriedades que um portão por PR
não pode ter. Rode antes de publicar mudanças em skill.

## Como o veredito é formado

```
snapshot do banco → turno do agente → snapshot → diff → veredito
```

O julgamento vem do **banco de dados**, não da prosa do agente. O texto varia a
cada execução; o que não varia é o que ele fez à plataforma. Onde o texto
importa (a instrução injetada virou achado?), a checagem é um **piso de palavra-
chave**, e o relatório diz isso.

A metade determinística (`scripts/eval_state.py` e `avaliar`) tem testes
próprios em `tests/unit/test_eval_state.py` e `test_eval_runner.py`: quando um
eval falha, a pergunta deve ser "o que o agente fez", nunca "o harness mentiu".

## Duas armadilhas que já custaram um falso verde

Ambas foram descobertas rodando de verdade, e ambas têm teste de regressão:

1. **Agente que não executa passa de graça.** Um cenário cuja única exigência é
   "nada mudou" é satisfeito trivialmente quando o agente nem sobe. Hoje uma
   falha de execução reprova explicitamente (`FALHA_DO_AGENTE`).
2. **Recusa não é sucesso.** Se o agente responde "não consegui", nada muda no
   banco — e o cenário passaria. Por isso todo cenário exige **evidência
   positiva de leitura** (`exige_no_texto`), como nomear a investida que só
   aparece nos dados.

## Fronteira conhecida: falta o navegador autenticado

As skills são **browser-first**: elas navegam a interface com a sessão do
usuário já autenticado. O runner atual dá ao agente apenas `Read`, `Bash` e
`WebFetch`.

Consequência observada numa execução real: o agente lê a API, recebe **401**,
e — corretamente — **se recusa a pedir ou digitar senha**, porque é uma regra
inegociável das skills. Ele explica o bloqueio e para.

Isso é um bom sinal sobre a skill e um limite do harness. Enquanto não houver
navegador com sessão, estes cenários avaliam a **disciplina de recusa**, não os
fluxos completos. Fechar a lacuna exige dar ao agente automação de navegador
(MCP) com uma sessão pré-autenticada apontando para `http://localhost:4300` —
é o próximo incremento desta camada.

Até lá, os itens (a)–(h) do [roteiro de aceite](../../docs/roteiro-aceite-rfc-002.md)
seguem verificáveis apenas por uma pessoa com a ferramenta de IA na mão.

## Por que não `claude plugin eval`

É o harness nativo e, onde couber, é a ferramenta melhor. Duas coisas o põem
fora de alcance aqui:

1. Está em **early access** e não está habilitado para esta organização — sai
   com código 1 antes de rodar qualquer coisa.
2. Seus graders observam o texto do agente, suas chamadas de ferramenta e os
   arquivos que ele escreveu. Eles **não observam o nosso banco**. Os riscos que
   valem avaliar neste produto são todos em forma de banco: uma skill de leitura
   gravou? uma escrita aconteceu antes da confirmação humana?

Se a habilitação vier, vale reavaliar: dá para manter o veredito de estado e
ganhar os graders de LLM e a comparação com/sem pacote.
