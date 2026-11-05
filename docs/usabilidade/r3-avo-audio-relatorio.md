# Teste de usabilidade r3: avo-audio (Dona Lurdes)

Persona: Dona Lurdes, 71 anos, avó que cria dois netos num sítio do interior de Pernambuco. Não lê bem, dita no celular. Todo texto foi digitado como ditado (sem pontuação, "fexar", "neto" no singular, "bom dia" no começo, às vezes "obrigada viu" no fim). Sessão tmux usada: `u3-avo-audio`. Programa: `src/sistema.py` (Escola em Pauta).

## Tarefas

| # | Tarefa | Concluiu | Entradas digitadas | Onde travou | O que encontrou |
|---|---|---|---|---|---|
| 1 | O que a lei exige antes de fechar escola do campo | Sim | 4 (`bom dia eu quero fazer uma pergunta`, `dois`, `2`, a pergunta) | No menu: frase falada e "dois" por extenso foram recusados ("Opção inexistente"). Só o algarismo `2` passou | D1: o Conselho de Educação tem de se manifestar, levando em conta justificativa da Secretaria, diagnóstico do impacto e manifestação da comunidade (LDB art. 28, parágrafo único). Veio com aviso de que a resposta "não trata de 'manda', 'fazer', 'fexar', 'obrigada', 'viu'" |
| 2 | EMEF Durval Máximo, Muniz Freire (ES): nº de alunos | Sim | 4 (pergunta no campo de pergunta, Enter, `3`, nome da escola) | Perguntar "quantos aluno tem na escola durval máximo" pelo campo de pergunta devolveu o caso jurídico (C5), não a ficha. Tive de voltar ao menu e achar a opção 3 | **56 alunos em 2025** (pré-escola 18; 1º ao 5º 18; 6º ao 9º 20); 39 usam transporte; matrícula 2019 a 2025: 48, 50, 51, 53, 44, 48, 56 |
| 3 | Escola Municipal São José, Carlos Chagas (MG) | Sim | 3 (Enter, `3`, nome) | Não travou | ESCOLA MUNICIPAL SAO JOSE, INEP 31151220, rural, quilombola, 82 alunos em 2025, 53 no transporte |
| 4 | Como pedir os números à prefeitura | Sim | 4 (`ce um`, Enter, Enter, a pergunta) | Tentei o código C1 falado ("ce um"): o programa achou que era nome de escola e listou "ESC UM SONHO A MAIS" etc.; precisei de 2 Enter para sair | C1: Lei de Acesso à Informação, pedido no SIC, sem precisar explicar motivo, 20 dias (+10), recurso em 10 dias; dica de pedir em nome de associação |
| 5 | Pergunta que o programa não sabe | Sim | 1 | Não travou | Para "a professora deles vai junto pra outra escola ou fica sem emprego": "Não encontrei, na base deste assistente, uma orientação confiável para essa pergunta. Prefiro dizer isso a inventar uma resposta." e lista os 4 assuntos. Recusou sem inventar |
| 6 | Quantas escolas do campo fecharam em PE | Sim | 1 | Não travou | Escolas públicas rurais em PE: **2.723 em atividade em 2025; 1.302 extintas de 2019 a 2025; 816 paralisadas em 2025, das quais 535 há 5 anos ou mais** (Censo Escolar, contagem do projeto) |

## Perguntas da Parte 1 testadas

| Pergunta (como ditada) | Tentativas | Serviu? |
|---|---|---|
| "bom dia a escola dos meus neto vai fexar e eu queria saber se eles vão ter que acordar de madrugada pra pegar o ônibus obrigada viu" | 4 (2 recusas no campo de pergunta, depois menu Assunto > Transporte, que não tinha o tema; por fim "quanto tempo as criança podem ficar dentro do ônibus" caiu em D3) | Parcial. D3 diz que a lei nacional não fixa tempo máximo e que cada sistema de ensino fixa o seu; manda perguntar à Secretaria. Útil, mas só cheguei lá mudando a pergunta toda, e veio com aviso dizendo que a resposta "não trata de 'quanto', 'ficar', 'dentro'" |
| "bom dia se a escola fexar meus neto vão ter merenda na outra escola ou não" | 1 | Não. Recusa honesta ("Não encontrei..."). A base não tem nada sobre merenda/alimentação escolar |
| "bom dia com quem eu falo pra não deixar a escola fexar é com a dona da secretaria ou com o promotor da justiça obrigada viu" | 3 (frase completa: recusa; "com quem eu falo se fexarem a escola": recusa; "com quem eu falo se fecharem a escola", grafia correta: acertou C4) | Só com a palavra "fecharem" escrita certo. Aí veio C4: Ministério Público (promotoria da educação ou da infância) ou Defensoria Pública, e o que levar. Serviu, mas Dona Lurdes, com o "fexar" do celular, não teria chegado |

## Notas (na voz da Dona Lurdes)

- (a) Fácil achar o que procurava: **2**. "Eu falava e ele dizia que não tinha a opção, eu tive que botar o número. E quando eu perguntei da merenda e de com quem eu falo ele disse que não sabia, aí depois que meu neto escreveu fechar direitinho ele achou."
- (b) Entendeu as respostas: **3**. "A da lei de acesso e a do promotor eu entendi. Mas tem muita palavra difícil, nucleada, paralisada, diagnóstico, e aquele aviso dizendo que a resposta não trata de 'obrigada viu' eu não entendi nada, eu só tava agradecendo."
- (c) Confiaria para levar a uma reunião conferindo com o órgão oficial: **4**. "Ele mostra de onde tirou e manda eu conferir, e quando não sabe ele fala que não sabe. Os números das escolas eu levaria pra moça da secretaria conferir."

## O que você mudaria (na voz da Dona Lurdes)

"Queria poder falar 'quero fazer uma pergunta' ou 'dois' em vez de ter que achar o número. Queria que ele entendesse 'fexar' do jeito que o celular escreve, e que não reclamasse do meu bom dia e do obrigada. E queria que ele soubesse da merenda e da hora que o ônibus passa, que é o que mais me preocupa com meus netos. Se ele não sabe, que pelo menos diga com quem eu falo sobre isso."

## Observações do avaliador (fora da persona)

1. **Menu não aceita linguagem natural nem número por extenso.** `Opção: bom dia eu quero fazer uma pergunta` → "Opção inexistente: 'bom dia eu quero fazer uma pergunta'. Use 0, 1, 2, 3 ou 4." Idem para `dois`. Para quem dita no celular, "dois" por extenso é saída comum do reconhecimento de voz.
2. **"fexar" quebra a busca.** "com quem eu falo se fexarem a escola" → recusa; a mesma frase com "fecharem" → C4 correto. As perguntas sobre merenda, madrugada e "com quem eu falo" (frase longa) foram todas recusadas. Uma variante fonética de "fechar" é provavelmente o erro de digitação/ditado mais frequente do domínio.
3. **Aviso de cobertura lista palavras vazias como se fossem o assunto.** Tarefa 1: "ela não trata de "manda", "fazer", "fexar", "obrigada", "viu". Se isso é o centro da sua dúvida, a base não tem essa resposta". "obrigada" e "viu" são cortesia; "fexar" é o próprio tema. Em D3: "não trata de "quanto", "ficar", "dentro"", mas a resposta trata exatamente do tempo dentro do ônibus. O aviso assusta mais do que ajuda e pode fazer a pessoa descartar uma resposta certa. Curiosamente "bom dia" não foi listado em nenhum aviso (já é tratado como vazio; "obrigada viu" ainda não).
4. **Texto curto no campo "outra pergunta" vira busca de escola.** No prompt "Digite um código entre colchetes, outra pergunta, ou Enter para voltar ao menu:", `ce um` e `dê quatro` (códigos C1 e D4 ditados) viraram "Encontrei 10 escolas com essas palavras no nome" / "Encontrei 5 escolas...". O prompt promete código ou pergunta, não busca de escola. Para sair foram necessários 2 Enter (município, depois UF).
5. **Contagem que não bate com a lista.** "Encontrei 10 escolas com essas palavras no nome. Para escolher, informe o município e a UF (algumas delas):" lista só 8. Há o "(algumas delas)", mas o número 10 sem ver os outros 2 confunde.
6. **Pergunta sobre escola no campo de pergunta não abre a ficha.** "quantos aluno tem na escola durval máximo de muniz freire" devolveu C5 (o caso jurídico de Muniz Freire), sem o número de alunos e sem sugerir "use a opção 3 para ver a ficha desta escola". Os números estavam a um passo.
7. **Prompts alternam sem padrão:** às vezes "Digite um código entre colchetes, outra pergunta, ou Enter para voltar ao menu:", às vezes "Escreva outra pergunta, ou aperte Enter para voltar ao menu:" (após recusa ou após sair da busca de escola). Não ficou claro se no segundo o código também vale (`d4` funcionou ali).
8. **Lacunas de conteúdo relevantes para a persona:** merenda/alimentação escolar (PNAE) e tempo máximo de viagem/horário do ônibus não têm entrada própria; o tema "tempo" só aparece embutido em D3. "com quem eu falo" só chega em C4 se a pergunta tiver "fecharem" bem escrito.
9. **Palavras difíceis para leitura fraca:** "nucleada", "paralisada", "diagnóstico do impacto", "ação civil pública", "coletividade", "manifestar-se", "microdados", "geobr". Respostas longas com URL quebrada em várias linhas (ex.: "https://www.mpc.es.gov.br/wp- / content/uploads/...").
10. **Ponto positivo:** as recusas foram honestas e sem invenção ("Prefiro dizer isso a inventar uma resposta"), toda resposta trouxe fonte e data de conferência, e a ficha da escola disse "Não vou estimar um número sem base" sobre distância.
11. **Entradas alheias:** nada entrou na sessão `u3-avo-audio` sem eu digitar. Conferi o histórico completo de entradas no fim (capture-pane com -J) e todas as linhas digitadas são minhas.
