# Teste de usabilidade simulado: persona "mae-agricultora" (Dona Cida)

Data: 05/11/2026. Programa: `src/sistema.py`, rodado em tmux 110x60 com `/usr/bin/python3 -I`.
Persona: Dona Cida, 38 anos, agricultora em assentamento no interior de MG, estudou até o 5º ano, dois filhos (5 e 9 anos) na escola rural que a prefeitura quer fechar.
Perguntas às cegas (Parte 1): `mae-agricultora-perguntas.json`, escritas antes de abrir o programa.

## Tarefas

| # | Tarefa | Concluiu | Entradas digitadas | Onde travou | O que encontrou |
|---|--------|----------|--------------------|-------------|-----------------|
| 1 | O que a lei exige antes de fechar escola do campo | sim | 2 (`2`, `pode fechar escola do campo? o que a lei fala`) | não travou | Assunto D1: Conselho de Educação precisa se manifestar, considerando justificativa da Secretaria, diagnóstico do impacto e manifestação da comunidade escolar (LDB art. 28, parágrafo único) |
| 2 | EMEF Durval Máximo, Muniz Freire/ES: nº de alunos | sim | 3 (Enter, `3`, `durval maximo`) | não travou | **56 alunos em 2025** (pré-escola 18; 1º ao 5º 18; 6º ao 9º 20). INEP 32049501; 39 usam transporte |
| 3 | Escola Municipal São José, Carlos Chagas/MG | sim, na 2ª tentativa | 7 (Enter, `3`, `escola sao jose carlos chagas` [falhou], Enter, `3`, `sao jose`, `carlos chagas`, `mg`) | Nome com a cidade junto deu "Não encontrei essa escola"; só achou quando digitei só o nome e o programa perguntou município e UF | ESCOLA MUNICIPAL SAO JOSE, Carlos Chagas/MG, INEP 31151220, quilombola, 82 alunos em 2025 |
| 4 | Como pedir os números à prefeitura | sim | 1 (`c1`, oferecido na tela da escola); refeito por texto livre (`como eu peço os numero da escola pra prefeitura`) caiu no mesmo assunto | não travou | Assunto C1: pedido pela Lei de Acesso à Informação no SIC, prazo de 20 dias + 10, recurso em 10 dias, guardar o protocolo, pode pedir pela associação |
| 5 | Pergunta que o programa não sabe | sim | 1 (`a merenda da escola da cidade e boa? meu menino so come comida de casa`) | não travou | Disse que não tem orientação confiável, "Prefiro dizer isso a inventar uma resposta", listou os 4 assuntos que conhece e sugeriu reformular ou consultar escola. Não inventou nada |

## Perguntas da Parte 1 testadas

| Pergunta (como a Dona Cida digitou) | Assunto que o programa abriu | Serviu? |
|---|---|---|
| `a prefeitura pode fechar a escola do assentamento assim sem perguntar pra gente?` | D1, O que a lei exige antes de fechar | **Sim.** A resposta diz que a comunidade tem de se manifestar e que fechar sem isso contraria a lei. Só que ela não diz "não pode" com todas as letras, e as palavras são difíceis |
| `quanto tempo meu filho de 5 ano vai ficar no onibus ate a cidade` | D3, As crianças pequenas podem ser levadas para estudar longe da comunidade? | **Serviu, mas não respondeu o que eu perguntei.** Não deu o tempo (nem disse que não sabe), mas trouxe o que mais me ajuda: criança pequena deve estudar na própria comunidade e o transporte deve ser "do campo para o campo, não para a cidade" |
| `o que eu posso fazer pra escola nao fechar` | D6, Existe um padrão nacional de como fazer o diagnóstico do impacto? | **Não.** Falou de projeto de lei no Senado e na Câmara. Eu queria saber o que fazer |

Extra (não conta nas 3): `onde eu reclamo, no ministerio publico ou na secretaria de educaçao?` abriu C4 (Ministério Público, Defensoria, levar datas, atas e números). Serviu. E `se fechar quem paga o onibus e tem monitor pra cuidar das criança no onibus?` deu "Não encontrei", mesmo existindo o assunto T3 "De onde vem o dinheiro do transporte escolar?".

## Notas (na voz da Dona Cida)

- **(a) Foi fácil achar o que procurava: 4.** "a escola do durval achei de primeira. a sao jose eu escrevi com a cidade e ele disse que nao tinha, quase desisti. depois ele mesmo perguntou a cidade e achou"
- **(b) Entendeu as respostas: 3.** "entendi o principal mas tem palavra de advogado. orgao normativo, manifestacao, nucleada, programa suplementar. LDB eu nao sei o que e. tive que ler duas vez"
- **(c) Confiaria para levar a uma reunião, conferindo com o órgão: 4.** "gostei que ele mostra de onde tirou e fala que nao e do governo. quando nao sabia ele falou que nao sabia, nao inventou. eu levava a lei dos pequeno que tem que estudar na comunidade"

## O que você mudaria (na voz da Dona Cida)

"quando eu pergunto o que eu posso fazer ele tinha que me falar o que fazer, passo a passo, nao de projeto la no senado. e se eu escrevo o nome da escola com a cidade junto ele tinha que achar, todo mundo fala assim: a sao jose de carlos chagas. e as palavra dificil, troca por palavra de gente. e se eu pergunto duas coisa junto ele fala que nao sabe, mas ele sabe uma delas, entao responde pelo menos essa"

## Observações do avaliador (fora da persona)

1. **Intenção "o que fazer" mal roteada.** `o que eu posso fazer pra escola nao fechar` abriu "Existe um padrão nacional de como fazer o diagnóstico do impacto?" (D6), embora exista a categoria "O que a comunidade pode fazer" (C1, C2, C4…). Provavelmente o casamento de "fazer"/"fechar" puxou o assunto do diagnóstico ("como fazê-lo"). Para esta persona é a pergunta mais importante, e foi a única das três que não serviu.
2. **Pergunta dupla vira "não sei".** `se fechar quem paga o onibus e tem monitor pra cuidar das criança no onibus?` levou a "Não encontrei, na base deste assistente, uma orientação confiável para essa pergunta.", apesar de T3 "De onde vem o dinheiro do transporte escolar?" cobrir metade. A persona junta dúvidas por hábito; o programa poderia responder a parte que conhece ou sugerir T2/T3.
3. **Busca de escola com município no texto falha, e a mensagem culpa a grafia.** `escola sao jose carlos chagas` e `sao jose carlos chagas` deram "Não encontrei essa escola entre as escolas públicas do campo ativas no Censo Escolar mais recente. Confira a grafia ou use o código INEP." A grafia estava certa; o problema é o nome da cidade junto. Também essa linha passa de 110 colunas e quebra no meio da palavra ("Confira a g / rafia"), ao contrário das demais, que têm quebra de linha bem feita. O mesmo acontece em "Não reconheci o número 2. Digite um código como D1, o código INEP de uma escola, ou escreva sua pergunta. (No / menu, as opções vão de 0 a 4.)".
4. **Lista de homônimos pouco útil.** `sao jose` mostrou "Encontrei 546 escolas com esse nome. Para escolher, informe o município e a UF (mostrando as primeiras):" seguido de 8 escolas todas do Acre. Funcionou porque o programa pediu município e UF em seguida, mas a lista em si não ajuda; dava para pular direto para a pergunta do município.
5. **Link sugerido que não bate com a ficha.** Nas fichas de Durval Máximo e São José aparece "[F2] Por que a distância aparece como "pelo menos"?", mas a mesma ficha diz "A distância até as escolas que poderiam receber os alunos ainda não foi calculada para esta escola." Não há distância "pelo menos" na tela; o atalho confunde.
6. **Pergunta específica respondida com resposta genérica.** `os alunos com deficiencia tem direito a monitor no onibus?` abriu T1 "O transporte escolar é um direito?" ("Sim. A Constituição e a LDB colocam o transporte escolar entre os deveres do Estado…"). Não fala de monitor nem de deficiência, mas responde com "Sim." no começo, o que pode ser lido como "sim, tem direito a monitor". Aqui seria melhor o "não encontrei" honesto, ou uma ressalva.
7. **Pergunta de tempo de ônibus sem aviso de limite.** `quanto tempo meu filho de 5 ano vai ficar no onibus ate a cidade` trouxe D3 (bom conteúdo), mas não diz que o programa não sabe calcular o tempo. Para quem perguntou um número, falta uma linha tipo "não sei dizer quanto tempo; o que a regra diz é…".
8. **Vocabulário difícil para escolaridade até o 5º ano:** "órgão normativo do sistema de ensino", "manifestação da comunidade escolar", "escola nucleada", "como programa suplementar", "LDB" (sigla nunca explicada na resposta), "propor ação civil pública", "parágrafo único", "prorrogáveis".
9. **Pontos fortes confirmados:** aviso de "NÃO OFICIAL" claro na abertura e em toda resposta; fonte com data de conferência; recusa honesta em pergunta fora da base (merenda); o prompt "Digite um código para continuar" aceita também pergunta em texto livre, o que evita voltar ao menu; mensagem útil para entrada vazia ("Você não digitou nada. Escreva uma pergunta, um código como D1, ou o nome da escola.").
10. **Nota de método (não é defeito do programa).** A sessão tmux `u-mae` recebeu pelo menos uma entrada que eu não digitei (`os alunos com deficiencia tem direito a monitor…`), provavelmente de outro teste rodando ao mesmo tempo com o mesmo nome de sessão. Tarefas 1 a 4 e a merenda foram conferidas no histórico da tela como digitadas por mim; as perguntas da Parte 1 e os retestes foram feitos numa sessão isolada (`u-mae-cida`). A pergunta do monitor (item 6) eu refiz na sessão isolada e o resultado foi o mesmo.
