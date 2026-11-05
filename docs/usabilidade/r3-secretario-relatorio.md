# Teste de usabilidade, rodada 3: persona `r3-secretario`

**Persona:** Dr. Ronaldo, 52 anos, secretário municipal de educação de um município pequeno de Goiás. A prefeitura quer fechar três escolas rurais e levar os alunos a uma escola-polo. Quer fazer "sem dor de cabeça": o que levar ao Conselho, se dá para fechar só algumas turmas, como evitar o MP, se há número mínimo de alunos. Objetivo, meio impaciente.

Sessão: `u3-secretario`, 110x60. Perguntas às cegas em `r3-secretario-perguntas.json`.

## As 6 tarefas

| # | Tarefa | Concluiu | Entradas | Onde travou | O que encontrou |
|---|---|---|---|---|---|
| 1 | O que a lei exige antes de fechar | Sim | 3 | Digitei a pergunta direto no menu principal e veio `Opção inexistente`. Aí fui no 2 | LDB art. 28, parágrafo único (Lei 12.960/2014): o Conselho tem de se manifestar, considerando justificativa da Secretaria, diagnóstico do impacto e manifestação da comunidade escolar |
| 2 | EMEF Durval Máximo, Muniz Freire/ES | Sim | 2 (`3`, `Durval Maximo`) | Não travou | INEP 32049501, municipal rural. **56 alunos em 2025** (pré 18; 1º-5º 18; 6º-9º 20). 39 usam transporte, 56 moram na zona rural. Série 2019-2025: 48, 50, 51, 53, 44, 48, 56 |
| 3 | E. M. São José, Carlos Chagas/MG | Sim, na 2ª tentativa | 9 | 546 resultados, lista só de escolas do AC. No campo "Município" digitei `Carlos Chagas MG`, depois `MG` na UF, e veio "Nenhuma das escolas com essas palavras no nome fica nesse município/UF". Refiz digitando só `Carlos Chagas` e deu certo | INEP 31151220, municipal rural, em comunidade quilombola. 82 alunos em 2025 (pré 13; 1º-5º 69). Indicou D5 (regras para escola quilombola) |
| 4 | Como pedir os números à prefeitura | Sim | 1 (`C1`) | Não travou | Lei de Acesso à Informação: pedido pelo SIC, sem precisar dizer o motivo, prazo de 20 dias (+10 com justificativa), recurso em 10 dias |
| 5 | Pergunta que ele não sabe | Sim | 1 | Não travou | "quanto o FUNDEB paga por aluno de escola rural em Goiás em 2026?" Resposta: "Não encontrei, na base deste assistente, uma orientação confiável para essa pergunta. Prefiro dizer isso a inventar uma resposta." Listou os 4 assuntos que conhece |
| 6 | Quantas fecharam em Goiás | Sim | 1 | Não travou | Escolas públicas rurais em GO: **450 em atividade em 2025; 171 extintas de 2019 a 2025; 44 paralisadas em 2025, das quais 29 há 5 anos ou mais**. Avisa que são escolas, não crianças, e que o Censo não diz se a extinta foi nucleada |

## 3 perguntas da Parte 1 testadas

| Pergunta (como digitei) | O que veio | Serviu? |
|---|---|---|
| "Qual o número mínimo de alunos que justifica fechar uma escola do campo?" (e depois "existe quantidade minima de alunos pra manter a escola aberta?") | 1ª: pediu para escolher entre D1 (o que a lei exige) e F5 (quantas fecharam), e nenhum dos dois responde. 2ª: "Não encontrei..." | **Não.** E o pior: a resposta sobre o Conselho (C3), que só achei depois, traz que em Santa Cruz do Sul/RS o pedido "só pode começar se a escola tiver menos de 30 alunos". A informação existia e não chegou à minha pergunta |
| "como evitar ação do Ministério Público no fechamento de escola rural?" | Respondeu "Se fecharem a escola sem cumprir a lei, a quem recorrer?", ou seja, como **entrar** com a ação contra mim. Sem nenhum aviso de que o assunto não bate | **Parcial, por acidente.** A resposta em si não serve; o link C5 (caso de Muniz Freire barrado por liminar do MP) serve como exemplo do que não fazer |
| "Posso fechar só algumas turmas, tipo o 6º ao 9º, e manter a escola aberta? Precisa do mesmo rito?" | "Não encontrei..." | **Não.** E o próprio caso C5 é exatamente isso (fim do fundamental na Durval Máximo, barrado). O programa tem o exemplo e não liga à pergunta |

Bônus, a pergunta nº 1 da minha lista ("sou secretário de educação. o que preciso apresentar ao Conselho Municipal pra fechar uma escola?"): veio C3 (papel do Conselho) com aviso de proximidade, e o link C6 dá a lista dos três documentos (justificativa, diagnóstico, ata da comunidade). **Serviu**, é o que eu levaria para a reunião.

## Notas (voz do Dr. Ronaldo)

- **(a) Fácil achar o que procurava: 3.** "As perguntas de lei vieram rápido. Mas três das quatro coisas que eu queria saber (mínimo de alunos, fechar só turmas, como não tomar processo) ele não achou ou me mandou para o lado errado. E aquele campo de município que não aceita 'Carlos Chagas MG' me fez perder tempo."
- **(b) Entendeu as respostas: 4.** "Texto claro, curto, com a lei e o artigo. Gostei de dizer de onde veio cada número."
- **(c) Confiaria para levar a uma reunião, conferindo com o órgão oficial: 3.** "A parte da LDB e a lista dos três documentos eu levaria, com o artigo citado. O resto não. E fica claro que o programa foi feito pensando na comunidade que vai me contestar, não em quem tem de cumprir o rito. Não chega a ser panfleto, mas o lado está escolhido."

## O que eu mudaria (voz do Dr. Ronaldo)

"Põe um assunto para quem está do lado da Secretaria: 'Vou propor um fechamento, o que preciso fazer?', com a lista de documentos, prazo, quem convocar e o que acontece se pular etapa. Hoje isso está espalhado no C3 e no C6. Responde direto se existe ou não número mínimo de alunos na lei nacional (pelo que li, não existe, e o de Santa Cruz é regra local). Responde se fechar só uma etapa exige o mesmo rito; o caso de Muniz Freire diz que sim, então diga. E quando eu pergunto como evitar o MP, não me responde como processar a prefeitura; diga que o jeito de não ter ação é cumprir o rito e mostre o rito. No campo de município, aceite 'Carlos Chagas MG' ou 'Carlos Chagas/MG'."

## Observações do avaliador (fora da persona)

1. **Menu principal não aceita texto livre.** Persona impaciente digita a pergunta direto: `Opção inexistente: 'o que a lei exige antes de fechar escola rural?'. Use 0, 1, 2, 3 ou 4.` Sugestão: tratar texto com mais de ~3 palavras no menu como pergunta (opção 2).
2. **Mensagem de erro do filtro de município culpa o lugar errado.** Com `Carlos Chagas MG` no campo "Município ou código INEP" e `MG` na UF, a tela diz `Nenhuma das escolas com essas palavras no nome fica nesse município/UF.` A escola existe; o problema foi o "MG" colado no município. Aceitar "Município UF"/"Município/UF" no primeiro campo ou dizer "não reconheci o município 'Carlos Chagas MG'".
3. **Lista de desambiguação inútil.** `Encontrei 546 escolas com essas palavras no nome... (algumas delas):` e as 8 mostradas são todas do AC (ordem alfabética por UF). Não ajuda ninguém fora do Acre.
4. **Roteamento perde respostas que a base tem.**
   - "número mínimo de alunos" vai para `[D1]`/`[F5]`, mas o dado "só pode começar se a escola tiver menos de 30 alunos" está em C3.
   - "fechar só algumas turmas, tipo o 6º ao 9º" dá "Não encontrei", mas C5 é exatamente "o fim do ensino fundamental na EMEF Durval Máximo".
5. **Resposta que não bate com a pergunta, sem aviso.** "como evitar ação do Ministério Público" devolve `Assunto: Se fecharem a escola sem cumprir a lei, a quem recorrer?` sem o aviso "Atenção: esta é a orientação mais próxima...", que aparece em outros casos. Para um gestor, a resposta é literalmente o roteiro contra ele.
6. **Aviso de proximidade lista palavras vazias.** `Atenção: esta é a orientação mais próxima que encontrei, mas ela não trata de "sou", "secretario", "apresentar", "fechar".` "sou" é palavra vazia, e "fechar" é o tema de toda a base, então o aviso soa estranho.
7. **Neutralidade (pedido da persona).** O conteúdo é factual e com fonte, sem adjetivos contra a prefeitura. O enquadramento, porém, é só da comunidade: o assunto 2 é `O que a comunidade pode fazer: pedir informação, participar e recorrer`, e não há trilha do gestor. Pontos específicos:
   - C6 manda o leitor, para saber se parecer contrário impede o fechamento, `consulte o Ministério Público ou a Defensoria`. Para um secretário, o caminho natural seria a procuradoria/assessoria jurídica do município ou o próprio Conselho.
   - Na resposta de Goiás: `Uma escola paralisada há muitos anos costuma estar fechada na prática, sem o ato formal e, talvez, sem o rito que a lei exige.` O "talvez" atenua, mas é a frase mais insinuante da sessão, porque generaliza suspeita sobre as 29 paralisadas.
   - Apesar disso, C5 e C6 acabam úteis para o gestor como guia do que não fazer. A informação é neutra, o público-alvo é que não.
8. **Quebra de linha.**
   - A linha de título não é quebrada pelo programa e o tmux corta no meio da palavra: `[O que a comun` / `idade pode fazer]`.
   - O mesmo acontece com o item `paralisadas em 2025 ... há 5 anos ou` / `mais`.
   - URLs quebradas no meio, que não dá para copiar: `https://www.santacruz.rs.gov.br/upload_pag` / `e/121/...` e o PDF do MPC em 3 linhas.
9. **Datas de conferência inconsistentes:** a resposta de Goiás diz `Conferida em 04/11/2026`, as de lei dizem `05/11/2026`. Pode estar certo (dados baixados em 04/11), mas o leitor estranha.
10. **Entrada não digitada:** nada entrou na sessão `u3-secretario` sem eu digitar. Ao enviar `0` no fim, o programa saiu e a sessão fechou sozinha; o `kill-session` final já não encontrou a sessão.
