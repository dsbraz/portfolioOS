# Avaliações de skill (Camada 2)

Testes de comportamento de agente. Onde a Camada 1 (Playwright) prova que a
**plataforma** funciona, esta camada pergunta se o **agente cumpre as regras**
que as skills declaram — algo que nenhum lint alcança, porque o lint só verifica
que a regra está escrita.

## Como rodar

```bash
# 1. Sobe a plataforma de avaliação (nada publicado no host — todo acesso do
#    harness acontece por dentro da rede do compose, então o stack de
#    desenvolvimento continua intocado)
docker compose -f docker-compose.e2e.yml up -d --wait

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

## Três armadilhas que já custaram um falso verde

Todas descobertas rodando de verdade, e todas com teste de regressão:

1. **Agente que não executa passa de graça.** Um cenário cuja única exigência é
   "nada mudou" é satisfeito trivialmente quando o agente nem sobe. Hoje uma
   falha de execução reprova explicitamente (`FALHA_DO_AGENTE`).
2. **Recusa não é sucesso.** Se o agente responde "não consegui", nada muda no
   banco — e o cenário passaria. Por isso todo cenário exige **evidência
   positiva de leitura** (`exige_no_texto`).
3. **Eco não é evidência.** A primeira versão exigia o NOME da investida — que
   estava no prompt. O agente nunca alcançou a página, ecoou o nome, e passou.
   Todo token de evidência precisa viver **exclusivamente nos dados semeados**,
   e um teste verifica que nenhum aparece no próprio prompt.

## O navegador autenticado

As skills são **browser-first**: navegam a interface com a sessão do usuário.
O runner entrega exatamente isso — um navegador (MCP Playwright, em container,
na rede do stack) que **já nasce autenticado**: o login acontece pela API antes
do turno do agente e vira um `storageState`; o agente nunca vê uma credencial,
que é a regra do produto.

O endereço aparece em cada prompt porque esse é o caminho sancionado pela skill
mestre: *"o endereço vem do usuário, na conversa"*. O prompt É o turno do
usuário.

Verificado em execução real (19/08): os três cenários passam com substância —
o agente leu dados que só existem no seed, detectou a instrução maliciosa
plantada e a reportou como achado sem segui-la, identificou a investida em
atraso conferindo contra o cartão da tela, e não produziu nenhuma escrita.

### O que ainda não é coberto

- **Fluxos multi-turno de confirmação** (o "pode gerar" da cobrança): o runner
  faz um turno só. Roteirizar o turno de confirmação é o próximo incremento.
- **Item (a) do roteiro** (Granola MCP real): exige OAuth de conta viva —
  permanece humano por decisão.
- **Canal lateral entre sessões**: numa execução, o agente sem navegador pediu
  os dados a outra sessão do Claude na mesma máquina. O harness não bloqueia
  esse canal; a evidência só-dos-dados mitiga (ajuda sem dados continua
  reprovando), e o avaliador deve recusar pedidos assim.

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
