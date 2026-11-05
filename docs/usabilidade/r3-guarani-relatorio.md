# Teste de usabilidade r3: persona `guarani` (Dona Kunhã)

Persona: Dona Kunhã, 34 anos, guarani-kaiowá, aldeia no MS. O guarani é a primeira língua dela, e ela escreve em português curto, sem acento e com verbo no infinitivo. Os três filhos estudam na escola indígena da aldeia, com professora da comunidade que ensina em guarani.

Sessão: `u3-guarani`, 05/11/2026. Todas as entradas foram digitadas como a persona digitaria (sem acento).

## Tarefas

| # | Tarefa | Concluiu | Entradas | Onde travou | O que encontrou |
|---|---|---|---|---|---|
| 1 | O que a lei exige antes de fechar | sim | 3 (`1`, `1`, `D1`) | não travou | [D1]: o Conselho de Educação precisa se manifestar considerando a justificativa da Secretaria, o diagnóstico do impacto e a manifestação da comunidade escolar (LDB art. 28, par. único) |
| 2 | EMEF Durval Máximo (Muniz Freire/ES) | sim | 3 (Enter, `3`, `durval maximo`) | não travou; a busca sem acento funcionou | **56 alunos em 2025** (pré 18, iniciais 18, finais 20); 39 usam transporte; INEP 32049501 |
| 3 | E. M. São José (Carlos Chagas/MG) | sim | 3 (Enter, `3`, `escola sao jose carlos chagas`) | não travou | ESCOLA MUNICIPAL SAO JOSE, INEP 31151220, rural, comunidade quilombola, 82 alunos em 2025 |
| 4 | Como pedir os números à prefeitura | sim | 1 (`C1`, a partir da ficha) | não travou | [C1]: pedido pela LAI no SIC, sem precisar dar o motivo; 20 dias + 10; recurso em 10 dias |
| 5 | Pergunta que o programa não sabe | sim | 1 (`professora da aldeia perder trabalho se escola fechar?`) | não se aplica | Disse que não tinha orientação confiável ("Prefiro dizer isso a inventar uma resposta") e listou os assuntos que conhece. Não inventou nada. Também não disse a quem perguntar. |
| 6 | Quantas escolas do campo fecharam no MS | sim | 1 (`quantas escola fechar no mato grosso do sul`) | não travou | Escolas públicas rurais em MS: **238 em atividade em 2025; 16 extintas de 2019 a 2025; 10 paralisadas em 2025, das quais 4 há 5 anos ou mais** |

## Perguntas da Parte 1 testadas

| Pergunta (como ela digitou) | Resposta | Serviu? |
|---|---|---|
| `prefeitura pode fechar escola da aldeia sem perguntar comunidade?` | Abriu [D1] (regra geral da LDB) com o aviso "não trata de 'aldeia', 'perguntar', 'comunidade'" | **Parcial.** A resposta diz que a comunidade tem que se manifestar, mas não levou à [D5], que é onde está a consulta prévia da Convenção 169 da OIT, justamente o que ela queria saber |
| `escola da cidade ensinar em guarani?` | "Não encontrei... uma orientação confiável" | **Não.** Ela reformulou como `lingua indigena na escola`, que abriu a [D5], mas a [D5] também não fala de língua (o próprio aviso diz "não trata de 'lingua'") |
| `quem defende indigena quando querer fechar escola` | Abriu [C4] (Ministério Público estadual, "promotoria da educação ou da infância", e Defensoria) com o aviso "não trata de 'indigena'" | **Parcial.** Deu caminho, mas o MPF e as organizações indígenas só aparecem na [D5], e a FUNAI não aparece em lugar nenhum |

## Notas (na voz da Dona Kunhã)

- (a) Fácil achar: **4**. "menu bom, numero facil. escrever sem acento funcionar. mas pergunta de aldeia ir para coisa geral."
- (b) Entendeu as respostas: **3**. "frase comprida. palavra 'diagnostico', 'nucleada', 'extinta', 'manifestar' dificil. eu ler duas vez."
- (c) Confiaria para levar à reunião, conferindo com o órgão: **3**. "lei escrita, numero da lei, isso bom para mostrar. mas lingua guarani nao falar nada, e isso mais importante para mim."

## O que eu mudaria (na voz da Dona Kunhã)

"quando eu escrever aldeia ou indigena, mostrar logo parte de indigena, nao parte geral. falar da lingua: escola da cidade ter que ensinar guarani ou nao? falar funai e ministerio publico federal na parte de quem defender. numero de escola fechada, mostrar so escola indigena tambem, nao misturar tudo rural. frase mais curta."

## Observações do avaliador (fora da persona)

1. **Aviso de "não trata de" contradiz a própria resposta.** Para `prefeitura pode fechar escola da aldeia sem perguntar comunidade?`, a tela diz: "ela não trata de 'aldeia', 'perguntar', 'comunidade'". Logo abaixo, o texto da [D1] fala em "escola do campo, indígena ou quilombola" e "manifestação da comunidade escolar". O aviso parece comparar só palavras exatas e acaba desacreditando uma resposta que serve em parte. O mesmo acontece com "não trata de 'indigena', 'querer'" na [C4]. Os verbos no infinitivo ("querer", "perguntar") entram no aviso como se fossem tema da pergunta.
2. **Roteamento para indígenas falha.** "escola da aldeia" + "comunidade" foi para a [D1], e "quem defende indigena" foi para a [C4]. Nenhuma das duas foi para a [D5], que é a única com consulta prévia (OIT 169) e MPF. Só "lingua indigena" chegou à [D5]. Para essa persona, a palavra "aldeia" deveria puxar a [D5].
3. **A [C4] aponta para o órgão errado no caso indígena.** "Ministério Público (a promotoria da educação ou da infância)" é o MP estadual. Para direitos indígenas, a atribuição costuma ser do MPF (CF art. 129, V; a competência para disputa sobre direitos indígenas é da Justiça Federal, art. 109, XI). A própria [D5] diz "procure a Defensoria, o Ministério Público Federal", então as duas respostas ficam inconsistentes para essa persona. A FUNAI não é mencionada em nenhuma resposta vista.
4. **Lacuna: língua de instrução.** "escola da cidade ensinar em guarani?" não teve resposta, e a [D5] avisa "não trata de 'lingua'". A Res. CNE/CEB 5/2012, que a própria [D5] cita, trata do ensino em língua materna, e a CF art. 210 §2º garante às comunidades indígenas o uso das línguas maternas. Esse é o dado central para essa persona.
5. **A [D5] é desbalanceada.** Do texto, a maior parte trata de quilombolas, e para indígenas há só uma frase ("as diretrizes põem a escola no território indígena"). O link de "Conferida em" aponta só para a resolução quilombola (rceb008_12.pdf), não para a 5/2012.
6. **Tarefa 6 sem recorte indígena.** O número do MS ("Escolas públicas rurais em MS") mistura todas as rurais. A ficha da E. M. São José mostra que o sistema sabe identificar "comunidade quilombola", então o recorte indígena e quilombola na contagem estadual parece viável. Também falta dizer que "rural" do Censo não é igual a "escola do campo" no sentido legal, embora a [D2] trate disso.
7. **"Não sei" sem encaminhamento.** Na tarefa 5, a resposta lista os assuntos, mas não diz a quem perguntar (por exemplo, a Secretaria de Educação ou o sindicato de professores, no caso da professora). O rodapé genérico "(Não oficial: confira com o órgão responsável.)" não diz qual órgão.
8. **Palavras difíceis** para quem tem o português como segunda língua: "se manifestar", "diagnóstico do impacto", "extintas", "nucleada", "paralisadas", "coletividade", "ação civil pública". A explicação entre parênteses ajuda, mas as frases são longas.
9. **Quebra de linha no meio da palavra.** No eco da entrada, a tela mostra "professora da aldeia perder tr / abalho" e "ensinar em gu / arani?" porque a linha passa de 110 colunas. O título da [C1] também quebra: "[O que a comun / idade pode fazer]". É só visual.
10. **Tela redesenhada mostrando entrada antiga.** Depois de algumas entradas, a tela é limpa e redesenhada com o histórico, o que às vezes deixa a resposta anterior visível acima da nova. Não chegou a confundir, mas a tela fica longa.

### Algo entrou na sessão sem eu digitar?

**Na minha sessão `u3-guarani`, não.** Conferi o histórico inteiro e todas as entradas registradas foram minhas.

**O contrário aconteceu: um incidente de contaminação causado pelo ambiente de teste.** Meu script auxiliar ficava no scratchpad compartilhado (`.../scratchpad/s.sh`). Logo depois que o criei, outra sessão de teste gravou um `s.sh` com o mesmo nome, apontando para `u3-advogada`. Por isso **4 entradas minhas foram enviadas para a sessão `u3-advogada`**: `D1` (que caiu como "Sua pergunta: D1" depois de ela ter escolhido a opção 2), um Enter, `3` e `durval maximo` (que caiu como "Opção inexistente: 'durval maximo'"). Percebi pelo erro `line 3: 0}: command not found` e pelo conteúdo do arquivo, e passei a usar `scratchpad/guarani_only/g.sh` com a sessão escrita direto no script. **O relatório da persona `advogada` pode conter essas 4 entradas como se fossem dela.** Recomendação para as próximas rodadas: cada persona usa um auxiliar com nome único, ou escreve `-t u3-<id>` direto no comando, sem arquivo compartilhado.
