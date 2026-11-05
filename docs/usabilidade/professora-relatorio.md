# Teste de usabilidade simulado: persona "professora" (Joana)

Data: 05/11/2026. Programa: `src/sistema.py`, rodado em tmux 110x60, interação só pela tela.
Persona: Joana, 31 anos, professora temporária dos anos iniciais numa escola rural de Brazlândia (DF).

## Tarefas

| # | Tarefa | Concluiu | Entradas digitadas | Onde travou | O que encontrou |
|---|--------|----------|--------------------|-------------|-----------------|
| 1 | O que a lei exige antes de fechar escola do campo | Sim | 3 (`1`, `1`, `D1`) | Não travou. No 1º acesso a tela demorou a aparecer e repeti o `1` achando que não tinha ido | LDB art. 28, parágrafo único (Lei 12.960/2014): manifestação do órgão normativo (Conselho de Educação), considerando justificativa da Secretaria, diagnóstico do impacto e manifestação da comunidade escolar. Com link do Planalto e data de conferência |
| 2 | EMEF Durval Máximo, Muniz Freire (ES): nº de alunos | Sim | 2 (`3`, `durval maximo`) | Não travou | **56 alunos em 2025** (pré-escola 18; anos iniciais 18; anos finais 20). 39 usam transporte, 56 moram na zona rural. Série 2019–2025. Distância "ainda não foi calculada" |
| 3 | Escola Municipal São José, Carlos Chagas (MG) | Sim | 4 (`3`, `escola municipal sao jose`, `carlos chagas`, `mg`) | "Encontrei 546 escolas com esse nome" assusta, mas o filtro por município/UF resolveu | INEP 31151220, municipal rural, em comunidade quilombola, 82 alunos em 2025 (pré 13; iniciais 69). Ofereceu o link D5 (regras quilombolas) |
| 4 | Como pedir os números à prefeitura | Sim | 3 (`1`, `2`, `C1`) | Não travou. Também se chega pelo link C1 no fim de D1 e da ficha da escola | Lei de Acesso à Informação: SIC, sem justificar motivo, 20 dias + 10, recurso em 10 dias; dica do protocolo e de pedir via associação/conselho escolar |
| 5 | Pergunta que o programa não sabe | Sim | 2 (`2`, pergunta sobre salário de temporário na SEEDF) | — | Disse "Não encontrei, na base deste assistente, uma orientação confiável para essa pergunta. Prefiro dizer isso a inventar uma resposta." e listou os 4 assuntos que conhece. Não inventou nada |

## Perguntas da Parte 1 testadas

| Pergunta (como a Joana digitou) | O que o programa respondeu | Serviu? |
|---|---|---|
| "quanto tempo as criancas pequenas podem ficar no onibus por lei" | Abriu D3 ("As crianças pequenas podem ser levadas para estudar longe da comunidade?"): educação infantil sempre na comunidade, anos iniciais só excepcionalmente nucleados e "do campo para o campo", "menor tempo possível de percurso" (Res. CNE/CEB 2/2008) | **Parcial.** O argumento é ótimo pra reunião (educação infantil não pode sair da comunidade). Mas eu perguntei quanto tempo e ele não disse se existe ou não um limite em minutos |
| "os alunos com deficiencia tem direito a monitor no transporte escolar?" | Abriu T1 ("O transporte escolar é um direito?"): sim, CF art. 208 VII e LDB art. 4º VIII. Fui em T4 (regras do veículo/motorista) e também não fala de deficiência nem de monitor | **Não.** Respondeu outra coisa sem avisar que não sabia a parte da deficiência |
| "eu sou professora temporaria, perco meu contrato se a escola for fechada?" | "Não encontrei, na base deste assistente, uma orientação confiável..." | **Não**, mas foi honesto. Pelo menos não me enganou |

Extra (fora das tarefas): procurei a minha região. `escola classe brazlandia` não achou nada; `brazlandia` achou só "CED 04 DE BRAZLANDIA" e "CEI 03 DE BRAZLANDIA". Tentei digitar o código INEP na pergunta de município e não funcionou (detalhes abaixo).

## Notas (voz da Joana)

- **(a) Foi fácil achar o que procurava: 4/5.** os menus com os assuntos ajudam muito, achei a lei e a LAI rapidinho. perdi ponto porque a minha escola de brazlandia não aparece e quando perguntei de deficiencia ele me mandou pra outra coisa
- **(b) Entendi as respostas: 4/5.** linguagem clara, sem juridiquês, e tem a lei e o artigo do lado. "órgão normativo do sistema de ensino" e "programa suplementar" eu entendo porque sou da área, os pais não iam entender
- **(c) Confiaria pra levar a uma reunião conferindo com o órgão oficial: 4/5.** tem o número da lei, o artigo, o link do planalto e a data que conferiram, isso eu imprimo e levo. só que fala toda hora "prefeitura" e aqui no DF não tem prefeitura, é a SEEDF/GDF, e não tem nada sobre a regra do DF

## O que eu mudaria (voz da Joana)

- colocar o DF direito: aqui não tem prefeitura nem conselho municipal, é Secretaria de Estado de Educação, Conselho de Educação do DF, Coordenação Regional de Ensino de Brazlândia. e deixar eu achar minha escola classe
- quando eu perguntar de aluno com deficiência (monitor, transporte adaptado, AEE na escola nova) ou se não souber, dizer que não sabe, não me responder outra coisa
- falar do tempo de ônibus em número, ou dizer claro "a lei não fixa minutos" pra eu não ficar procurando
- ter alguma coisa sobre os professores e servidores (lotação, contrato temporário) e sobre o PPP e a escola multisseriada, que é o que a gente mais discute na escola
- um botão "resumo pra levar na reunião" juntando lei + números da escola numa folha só

## Observações do avaliador (fora da persona)

1. **Resposta não bate com a pergunta, sem aviso.** Pergunta: "os alunos com deficiencia tem direito a monitor no transporte escolar?" → respondeu "Assunto: O transporte escolar é um direito? [...] Sim. A Constituição e a LDB colocam o transporte escolar entre os deveres do Estado". A palavra-chave "deficiencia"/"monitor" foi ignorada; o casamento foi feito só por "transporte escolar". Seria melhor declarar a parte que não sabe (como faz na pergunta sobre contrato temporário) ou mostrar "achei algo parecido: ...".
2. **Pergunta quantitativa respondida com regra qualitativa.** "quanto tempo ... podem ficar no onibus" → D3, que diz "o transporte deve ter o menor tempo possível de percurso". Não informa se há limite numérico. Faltou um "a norma nacional não fixa tempo máximo em minutos" (se for o caso).
3. **Código INEP não aceito no prompt de município, apesar da instrução.** A tela diz "Ou digite o código INEP (o número da esquerda)." seguido de "Município (Enter para pular):". Digitar `53017846` ali foi tratado como município: "UF, ex.: ES (Enter para pular):" → "Nenhuma das escolas com esse nome fica nesse município/UF." O usuário faz exatamente o que a tela mandou e falha.
4. **Filtro de município inútil quando todas as opções são do mesmo município.** Com `brazlandia`: "Encontrei 2 escolas com esse nome. Para escolher, informe o município e a UF:" e as duas são "Brasília/DF". Pedir município/UF não desempata nada; com 2 resultados, deveria oferecer escolher por número/código direto.
5. **"546 escolas com esse nome" é exagero e confunde.** Para "escola municipal sao jose" a lista inclui "ESC INDIGENA INSTITUTO SAO JOSE" e "ESC SAO JOSE II". Não são "esse nome"; seria mais exato "546 escolas com nome parecido".
6. **Link contraditório na ficha.** Na ficha da EMEF Durval Máximo (e da E. M. São José) a tela diz "A distância até as escolas que poderiam receber os alunos ainda não foi calculada para esta escola" e, logo abaixo, oferece "[F2] Por que a distância aparece como "pelo menos"?" — mas nenhuma distância apareceu.
7. **Prompt fala em "código" quando não há código na tela.** Após "Não encontrei essa escola entre as escolas públicas do campo ativas [...] Confira a grafia ou use o código INEP." vem "Digite um código para continuar, ou Enter para voltar ao menu:". O usuário pode achar que é para digitar o código INEP ali (é o código de assunto, e nenhum foi listado). Mesmo problema após a mensagem de "Não encontrei, na base deste assistente...".
8. **Vocabulário municipal num usuário do DF.** "Como pedir à prefeitura o diagnóstico e os números do fechamento?" e "Escola municipal rural". No DF a rede é distrital (SEEDF) e não há prefeitura; o texto de C1 até diz "prefeitura ou do estado", mas o título não. Para o DF, citar Distrito Federal explicitamente ajudaria.
9. **Linha quebrada no meio da palavra** a 110 colunas: "Confira a g" / "rafia ou use o código INEP." (a mensagem de escola não encontrada não passa pelo mesmo quebrador de linha que as demais respostas).
10. **Cobertura DF:** "escola classe brazlandia" → não encontrado. Pode ser correto (a base é de escolas do campo e a escola classe pode estar classificada como urbana), mas a mensagem não diz isso: só diz "Confira a grafia". Para a persona, o não-achar parece erro de digitação dela.
11. **Pontos fortes observados:** toda resposta jurídica traz lei, artigo, link oficial e data de conferência; o "Não oficial: confira com o órgão responsável" está em todas as telas; a recusa honesta para pergunta fora da base ("Prefiro dizer isso a inventar uma resposta") funcionou nas duas vezes; a ficha da escola marcou "em comunidade quilombola" e ofereceu D5 automaticamente.
12. **Nota de ambiente de teste (não é defeito do programa):** no histórico do tmux apareceu uma entrada `c1` que eu não digitei (logo após `D1`), e numa captura vi a linha "menu, as opções vão de 0 a 4." que não estava no histórico desta sessão. Suspeita de outro agente de teste enviando teclas a um alvo de tmux parecido em paralelo. Para a tarefa 4 refiz o caminho do zero (`1`, `2`, `C1`) para contar só entradas minhas.
