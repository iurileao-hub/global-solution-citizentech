# Teste de usabilidade simulado: persona "conselheira" (Patrícia)

Data: 05/11/2026. Programa: `src/sistema.py` rodado em tmux 110x60, sem leitura de código, dados ou documentação.
Perguntas às cegas da Parte 1: `docs/usabilidade/conselheira-perguntas.json`.

Persona: Patrícia, 45 anos, professora aposentada, conselheira do Conselho Municipal de Educação (ES). A Secretaria pediu ao Conselho o fechamento de duas escolas rurais com uma justificativa de duas páginas e sem números.

## As 5 tarefas

Contagem de entradas: cada linha enviada ao programa (opção de menu, código, texto ou Enter para voltar).

| # | Tarefa | Concluiu | Entradas | Onde travou | O que encontrou |
|---|--------|----------|----------|-------------|-----------------|
| 1 | O que a lei exige antes de fechar escola do campo | Sim | 3 (`1`, `1`, `D1`) | Não travou | D1: manifestação do órgão normativo (Conselho), considerando justificativa da Secretaria, diagnóstico do impacto e manifestação da comunidade escolar. Fonte: LDB art. 28, parágrafo único (Lei 12.960/2014), com link do Planalto |
| 2 | Achar EMEF Durval Máximo (Muniz Freire/ES) e nº de alunos | Sim | 3 (Enter, `3`, `Durval Máximo`) | Não travou; achou direto, mesmo com acento | **56 alunos em 2025** (pré-escola 18; anos iniciais 18; anos finais 20). INEP 32049501, 39 usam transporte, série 2019 a 2025. Distância "ainda não foi calculada" |
| 3 | Achar Escola Municipal São José de Carlos Chagas (MG) | Sim | 5 (Enter, `3`, `Escola Municipal São José`, `Carlos Chagas`, `MG`) | Leve: "Encontrei 546 escolas", mas o próprio programa pediu município e UF | INEP 31151220, rural, em comunidade quilombola, 82 alunos em 2025. Ofereceu D5 (regras para quilombola) |
| 4 | Como pedir os números à prefeitura | Sim | 1 (`C1`, a partir da ficha da escola) | Não travou | C1: Lei de Acesso à Informação, SIC, prazo de 20 dias + 10, recurso em 10 dias |
| 5 | Pergunta que o programa não sabe | Sim (com ressalva) | 6 (Enter, `2`, pergunta sobre prazo regimental; Enter, `2`, pergunta sobre custo por aluno) | Na 1ª tentativa ele não disse que não sabia: respondeu outro assunto | Prazo regimental do CME: devolveu "Qual é o papel do Conselho de Educação?" (não fala de prazo). Custo por aluno em Muniz Freire: "Não encontrei, na base deste assistente, uma orientação confiável para essa pergunta. Prefiro dizer isso a inventar uma resposta." e listou os assuntos que conhece |

## 3 perguntas da Parte 1 feitas ao programa

| Pergunta (como digitei) | Resposta que veio | Serviu? |
|---|---|---|
| "O Conselho Municipal de Educação pode recusar o pedido de fechamento das escolas?" | "Qual é o papel do Conselho de Educação?" (precisa se manifestar; exemplo de Santa Cruz do Sul/RS) | **Parcialmente.** Diz que o Conselho precisa se manifestar e mostra o rito de outro município, mas não responde "sim ou não, pode recusar", nem se o parecer obriga a Secretaria |
| "Existe um modelo de diagnóstico de impacto que a Secretaria deveria apresentar?" | D6: "Ainda não. A LDB exige o diagnóstico, mas não diz como fazê-lo." e explica o PL 3.091/2024 | **Sim.** Resposta direta, honesta, avisa que o PL não é lei. Serve para a reunião |
| "Quais documentos o Conselho deve exigir da Secretaria antes de opinar sobre o fechamento de uma escola do campo?" | C1: como pedir pela Lei de Acesso à Informação | **Não.** Fala de como um cidadão pede documento, não de quais documentos o Conselho deve exigir. A lista útil (matrícula de 5 anos, mapa de distâncias, diagnóstico, ata da comunidade) só apareceu, por acaso, dentro do exemplo de Santa Cruz do Sul em outra resposta |

## Notas (na voz da Patrícia)

- **(a) Foi fácil achar o que eu procurava: 4/5.** O menu de assuntos é claro e achei as duas escolas sem dificuldade, mesmo escrevendo com acento. Perdi ponto porque, quando escrevi a pergunta com as minhas palavras, duas vezes recebi resposta para outra pergunta.
- **(b) Entendi as respostas: 4/5.** Linguagem simples, frases curtas, sempre com a lei citada. Só estranhei a frase "Se preferir não se identificar sozinho" e a explicação sobre distância "pelo menos" numa escola em que a distância nem foi calculada.
- **(c) Confiaria para levar a uma reunião, conferindo com o órgão oficial: 4/5.** Cada resposta traz a lei, o artigo, o link e a data em que foi conferida, e o programa admite quando não sabe. Levaria a ficha das escolas e o artigo 28 da LDB. Não levaria nada sobre "o que o Conselho pode fazer", porque ali a resposta foi genérica.

## O que eu mudaria (na voz da Patrícia)

O programa foi pensado para a família e para a comunidade, e isso se nota: quase tudo fala "você pode pedir", "a comunidade pode participar". Eu estou do outro lado da mesa: sou eu quem precisa dar o parecer. Gostaria de uma parte "Para conselheiros", com uma lista do que exigir da Secretaria antes de votar (números de matrícula, distância e tempo de viagem, para onde vão os alunos, custo, ata de consulta à comunidade), dizendo claramente se o Conselho pode dar parecer contrário ou pedir complementação. E, quando eu fizer uma pergunta que ele não sabe, prefiro que diga "não sei" a me mostrar um assunto parecido como se fosse a resposta.

---

## Observações do avaliador (fora da persona)

1. **Pergunta livre casa com o assunto errado sem avisar (o defeito mais grave).** "Quais documentos o Conselho deve exigir da Secretaria antes de opinar..." devolveu `Assunto: Como pedir à prefeitura o diagnóstico e os números do fechamento?`. "Qual é o prazo regimental para o Conselho Municipal de Educação emitir parecer..." e "O Conselho Municipal de Educação pode recusar o pedido..." devolveram ambas `Assunto: Qual é o papel do Conselho de Educação?`. O programa mostra o título do assunto encontrado, o que ajuda, mas não sinaliza baixa confiança ("o mais próximo que encontrei foi..."). A pergunta sobre prazo deveria ter caído no fallback honesto, como aconteceu com a de custo por aluno.
2. **Falta conteúdo para quem decide (conselheiro).** Não há ficha que responda "o Conselho pode recusar/dar parecer contrário?" nem "quais documentos exigir". A melhor lista de documentos está escondida no exemplo municipal de Santa Cruz do Sul/RS, dentro de "Qual é o papel do Conselho de Educação?". C1 é escrita para cidadão via LAI; para conselheiro, o canal natural é a diligência/requisição do próprio Conselho, que não aparece.
3. **Link F2 incoerente com a ficha.** Nas duas fichas aparece `A distância até as escolas que poderiam receber os alunos ainda não foi calculada para esta escola.` e logo abaixo `[F2] Por que a distância aparece como "pelo menos"?`, mas nenhuma distância "pelo menos" aparece na tela.
4. **Fallback sem códigos, mas pede código.** Depois de `Não encontrei, na base deste assistente, uma orientação confiável...` a tela termina com `Digite um código para continuar, ou Enter para voltar ao menu:`, sem nenhum código listado.
5. **Busca por nome muito ampla.** `Escola Municipal São José` retornou `Encontrei 546 escolas com esse nome.` e a lista começa por `ESC INDIGENA INSTITUTO SAO JOSE, Jordão/AC` (escola estadual/indígena do AC). "Com esse nome" é impreciso: são escolas que contêm "São José". O pedido seguinte de município e UF resolveu bem.
6. **Frase confusa em C1.** `Se preferir não se identificar sozinho, o pedido pode ser feito por uma associação ou pelo conselho escolar.` "Não se identificar sozinho" é ambíguo (parece anonimato, que a LAI não permite, conforme a própria resposta diz linhas acima).
7. **Possível imprecisão jurídica em D6.** `Se virar lei, ele substitui a regra atual da LDB.` Um PL que altera a LDB tende a modificar/complementar o art. 28, não "substituir a LDB"; vale conferir a redação do PL e ajustar o verbo.
8. **Jargão pontual:** "órgão normativo do sistema de ensino" (D1) e "SIC" (C1, explicado) são compreensíveis para a persona, mas não para a família rural, que é o público principal.
9. **Pontos fortes observados:** acento e caixa não atrapalham a busca; toda resposta traz fonte, artigo, link e data de conferência; a ficha recusa estimar distância "sem base"; a escola quilombola puxa automaticamente D5; ao sair com `0` o programa encerra limpo.
