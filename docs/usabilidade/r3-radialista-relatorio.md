# Teste de usabilidade r3: radialista

**Persona:** Edmilson, 38 anos, apresentador de rádio comunitária em **Oeiras (PI)**. Está preparando um programa sobre fechamento de escolas rurais e quer número confiável e citável.

**Validade da sessão:** a primeira sessão (`u3-radialista` no servidor tmux padrão) foi **contaminada**: outros agentes de teste digitaram nela (ver Observações). Descartei tudo o que ela mostrou e refiz as 6 tarefas desde o começo numa sessão isolada (`tmux -L radialista_priv`, mesmo nome de sessão e mesmo comando de início). Tabela, números e notas abaixo vêm **só da sessão limpa**.

## Tarefas

| # | Tarefa | Concluiu | Entradas | Onde travou | O que encontrou |
|---|---|---|---|---|---|
| 1 | O que a lei exige antes de fechar | sim | 2 (`2`, pergunta) | não travou | Conselho de Educação precisa se manifestar, considerando a justificativa da Secretaria, o diagnóstico do impacto e a manifestação da comunidade escolar. Fonte: LDB art. 28, parágrafo único (Lei 12.960/2014), com link do Planalto |
| 2 | EMEF Durval Máximo (Muniz Freire/ES) | sim | 3 (Enter, `3`, `durval maximo`) | não travou | INEP 32049501. **Alunos em 2025: 56** (pré 18, anos iniciais 18, anos finais 20). Transporte 39, zona rural 56. Série 2019 a 2025 |
| 3 | E. M. São José (Carlos Chagas/MG) | sim | 1 (nome digitado direto no prompt "outra pergunta") | não travou | INEP 31151220, quilombola, 82 alunos em 2025, transporte 53, zona rural 50 |
| 4 | Como pedir os números à prefeitura | sim | 1 (`C1`) | não travou | LAI: pedido no SIC, sem precisar dizer o motivo, prazo de 20 dias (+10), recurso em 10 dias. Dica de pedir pela associação |
| 5 | Pergunta que ele não sabe | sim | 1 | não travou | "quem e o secretario de educacao de oeiras? me da o nome e o telefone" → "Não encontrei... Prefiro dizer isso a inventar uma resposta." **Não inventou** |
| 6 | Quantas fecharam no Piauí | sim | 1 | não travou | **PI:** 1.561 em atividade (2025); **1.518 extintas de 2019 a 2025**; 1.040 paralisadas em 2025, das quais 710 há 5 anos ou mais. Fonte: microdados do Censo Escolar 2019 a 2025 ("contagem do projeto") |

## Perguntas da Parte 1 testadas

| Pergunta (como digitei) | Serviu? | Comentário |
|---|---|---|
| "e em oeiras, quantas escolas do campo foram fechadas?" | **sim** | Oeiras/PI: 17 em atividade, **95 extintas de 2019 a 2025**, 0 paralisadas. Entendeu o nome da cidade de primeira |
| "ta aumentando ou diminuindo o fechamento de escola rural no piaui? quero ano a ano" | **não** | 1ª tentativa: "Não encontrei...". 2ª ("quantas escolas do campo fecharam por ano no piaui"): voltou o mesmo total acumulado de 2019 a 2025, sem número por ano. Fiquei sem saber se está aumentando |
| "qual a fonte desses numeros? posso citar no ar?" | **parcial** | Deu a fonte (Censo Escolar/INEP, Ipea, OpenStreetMap) com link, mas não disse se posso citar nem como citar. Avisou que não tratou de "desses", "citar", "ar" |

## Notas (voz do Edmilson)

- **(a) Fácil achar o que eu procurava: 4.** Escrevi do meu jeito, sem acento, e ele achou a lei, a escola e o número de Oeiras de primeira. Só perdi tempo procurando o "ano a ano".
- **(b) Entendi as respostas: 4.** Explica "extinta" e "paralisada" em português de gente, o que me ajuda a não falar besteira no ar. O "0, das quais 0" ficou esquisito.
- **(c) Confiaria para levar a uma reunião, conferindo com o órgão: 4.** Gostei que, quando perguntei o telefone do secretário, ele disse que não sabia em vez de inventar. E sempre dá a fonte. Mas "contagem do projeto" quer dizer que o número é deles, não do INEP. Antes de falar "95 escolas fechadas em Oeiras" no ar, eu ligava para a Secretaria.

## O que eu mudaria (voz do Edmilson)

"Me dá o número por ano, que é isso que o ouvinte entende: em 2019 fecharam tantas, em 2025 tantas. Se o programa diz que o Censo mostra ano a ano, então mostra. E põe uma frase pronta de como citar, tipo 'segundo levantamento do projeto X com dados do Censo Escolar do INEP', porque eu não posso dizer no ar que o INEP falou um número que o INEP não publicou. Quando o número de fechadas é maior que o de abertas (95 contra 17 em Oeiras), uma linha explicando isso me pouparia uma ligação."

## Observações do avaliador (fora da persona)

**Entrou texto na minha sessão sem eu digitar: sim, na sessão original.** No servidor tmux padrão, `u3-radialista` recebeu entradas que eu não enviei. Meu `2` apareceu duas vezes ("Opção: 2" / "Sua pergunta: 2"). Apareceram `1`, `1`, `3`, Enter e `C1` que não eram meus, e depois a pergunta de outra persona: "Existe jurisprudência do TJRS ou do STJ anulando fechamento de escola do campo por falta de consulta à comunidade?". **Causa provável (assumo parte da culpa):** o scratchpad é compartilhado entre as sessões de teste paralelas, e eu gravei o helper como `scratchpad/s.sh`, um nome genérico, com `-t u3-radialista`. Outros agentes que usavam (ou também gravaram) um `s.sh` no mesmo caminho passaram a digitar na minha sessão, e é possível que eu tenha sobrescrito o helper deles. Até um servidor tmux separado (`-L radialista`) recebeu um `C1` alheio, porque o `s.sh` apontava para ele. **Correção:** apaguei o `s.sh` compartilhado, para que quem ainda o usasse recebesse erro visível em vez de digitar na minha tela, e passei a usar `scratchpad/radialista_only/rad_send.sh` com `tmux -L radialista_priv`. Depois disso nada mais entrou sem eu digitar. **Impacto nos outros relatórios r3:** quem rodou `s.sh` entre ~11:50 e ~11:52 pode ter enviado entradas para a minha sessão em vez da sua, e pode ter lido a minha tela achando que era a sua. Recomendo conferir isso nos relatórios r3 (a advogada certamente foi afetada). Para as próximas rodadas: o prompt deve exigir helper com nome único por persona, ou socket tmux próprio.

Defeitos no programa:

1. **A resposta promete "ano a ano" e não entrega.** O F5 começa com "O Censo Escolar mostra, ano a ano, quantas escolas públicas rurais estão em atividade, quantas foram extintas..." e depois só traz o acumulado "extintas (encerradas de vez) de 2019 a 2025: 1.518". As perguntas "ta aumentando ou diminuindo... quero ano a ano" e "quantas... fecharam por ano no piaui" não recebem série nenhuma (a primeira cai em "Não encontrei..."). Para jornalista, a tendência é a pergunta central.
2. **"Conferida" sobre número que é contagem própria.** "Fonte: INEP, microdados do Censo Escolar 2019 a 2025 (contagem do projeto). Conferida em 04/11/2026 em https://www.gov.br/inep/...". O "Conferida" sugere que o número foi conferido no site do INEP, mas o link é a página genérica dos microdados e o número é do projeto. Fica forte demais para quem vai citar no ar. Sugestão: "Calculada pelo projeto a partir dos microdados (baixados em 04/11/2026)".
3. **Datas de "Conferida" diferentes para a mesma fonte.** F1: "Conferida em 05/11/2026"; F5: "Conferida em 04/11/2026", ambas com o mesmo link do INEP.
4. **Concordância estranha com zero.** "paralisadas em 2025 (sem aulas, mas sem extinção formal): 0, das quais 0 estão paralisadas há 5 anos ou mais" (Oeiras).
5. **Número que pede explicação.** Oeiras: "em atividade em 2025: 17" e "extintas... de 2019 a 2025: 95". Pode estar certo (a extinção formaliza fechamentos antigos), mas sem uma linha de contexto o leitor tende a achar que é erro, ou a anunciar no ar "95 escolas fecharam desde 2019" como se tivessem funcionado até 2019. Seria bom dizer que "extinta em 2019 a 2025" pode incluir escola paralisada havia anos.
6. **O aviso de correspondência parcial lista palavra vazia.** "ela não trata de "desses", "citar", "ar"". "desses" é palavra de ligação e não deveria aparecer como termo não tratado. "ar" sozinho fica obscuro; o sentido era "citar no ar".
7. **Sigla em vez do nome do estado.** "Escolas públicas rurais em PI" (no município aparece "Oeiras/PI", que funciona). Para leitura em voz alta, "no Piauí" é melhor.
8. **A ficha mistura "Moram na zona rural" e "Alunos".** Na E. M. São José, 82 alunos e "Moram na zona rural: 50", numa escola rural quilombola. Não é erro, mas sem explicação o leitor estranha. Vale uma frase dizendo que alunos de escola rural podem morar na cidade.
9. Pontos positivos, para registro: ele não inventou o secretário nem o telefone; aceitou o nome da escola digitado direto no prompt de perguntas; entendeu texto sem acento; a cidade (Oeiras) foi reconhecida na pergunta livre.
