# Teste de usabilidade simulado: Seu Benedito (avô quilombola)

Persona: Seu Benedito, 67 anos, liderança quilombola no Vale do Ribeira (SP). Dita ao neto de 14 anos, que digita rápido, abreviado e sem acento.
Sessão: tmux 110x60, `python3 -I src/sistema.py`, 05/11/2026. Perguntas da Parte 1 em `avo-quilombola-perguntas.json`.

## Tarefas

| # | Tarefa | Concluiu | Entradas digitadas | Onde travou | O que encontrou |
|---|--------|----------|--------------------|-------------|-----------------|
| 1 | O que a lei exige antes de fechar escola do campo | Sim | 2 (`2`, `o q a lei manda fazer antes de fechar escola do campo`) | Não travou | Assunto D1: o Conselho de Educação precisa se manifestar, considerando justificativa da Secretaria, diagnóstico do impacto e manifestação da comunidade escolar (LDB art. 28, parágrafo único) |
| 2 | EMEF Durval Máximo, Muniz Freire/ES, nº de alunos | Sim | 2 (`3`, `durval maximo`) + 1 Enter para voltar ao menu | Não travou | EMEF DURVAL MAXIMO, Muniz Freire/ES, INEP 32049501. **56 alunos em 2025** (pré-escola 18, anos iniciais 18, anos finais 20); 39 usam transporte |
| 3 | Escola Municipal São José, Carlos Chagas/MG | Sim, na 2ª tentativa | 6 (`3`, `escola sao jose carlos chagas`, `3`, `sao jose`, `carlos chagas`, `mg`) + 2 Enter | 1ª tentativa: o neto escreveu nome e cidade juntos e veio "Não encontrei essa escola". Na 2ª, só "sao jose" deu 546 escolas, e o programa pediu município e UF | ESCOLA MUNICIPAL SAO JOSE, Carlos Chagas/MG, INEP 31151220, "em comunidade quilombola", 82 alunos em 2025; ofereceu o assunto D5 (regras quilombolas) |
| 4 | Como pedir os números à prefeitura | Sim | 1 (`c1`, a partir da ficha da escola) | Não travou | Lei de Acesso à Informação: pedido no SIC, sem precisar dizer o motivo, prazo de 20 + 10 dias, recurso em 10 dias; sugere pedir via associação ou conselho escolar |
| 5 | Pergunta que o programa não sabe | Parcial | 4 (`2`, `qnto custa o onibus escolar por mes pra prefeitura`, `2`, `telefone da defensoria em eldorado sp`) | 1ª pergunta: em vez de dizer que não sabia, respondeu outra coisa ("Quem é responsável pelo transporte escolar?") | 2ª pergunta: admitiu "Não encontrei, na base deste assistente, uma orientação confiável para essa pergunta. Prefiro dizer isso a inventar uma resposta." e listou os assuntos que conhece |

## Perguntas da Parte 1 testadas

| Pergunta (como o neto digitou) | Assunto que veio | Serviu? |
|---|---|---|
| `a prefeitura pode fechar a escola do quilombo sem perguntar pra gente?` | D1, O que a lei exige antes de fechar uma escola do campo | Em parte. Responde que não pode fechar sem manifestação da comunidade e do Conselho, mas trata como escola do campo comum: não menciona as regras quilombolas nem oferece o D5, mesmo com "quilombo" na pergunta |
| `o q e consulta previa e a gente tem direito` | D5, Escola indígena ou quilombola: há regras próprias? | Sim, é a resposta que ele mais queria: tem direito, Convenção 169 e Resolução CNE/CEB 8/2012, educação infantil e anos iniciais no território. Só que não explica o que é a consulta (como deve ser feita, quem é consultado, se tem que ser antes) |
| `quem pode ajudar a gente a nao deixar fechar a escola, defensoria? ministerio publico?` | C4, Se fecharem a escola sem cumprir a lei, a quem recorrer? | Sim. Diz Ministério Público e Defensoria e o que levar. Mas fala de depois que fecharam; ele queria impedir antes. E o Ministério Público Federal, que o D5 cita para quilombo, não aparece aqui |

## Notas (na voz do Seu Benedito)

- **(a) Foi fácil achar o que procurava: 4.** "O menino achou quase tudo de primeira. Só a escola de Minas que deu trabalho: escreveu a cidade junto e a máquina disse que não existia. Depois perguntou a cidade separado e aí achou."
- **(b) Entendeu as respostas: 3.** "Entendi o principal, mas tem palavra de gabinete: 'órgão normativo', 'nucleação', 'polos', 'ação civil pública', 'povos tribais'. O neto teve que me explicar. E LDB ninguém me disse o que é."
- **(c) Confiaria para levar a uma reunião, conferindo com o órgão oficial: 4.** "Gostei que diz a lei, o artigo e o dia que conferiu, e que avisa que não é da prefeitura. Isso eu levo e mostro. Só não levaria a parte do ônibus, que perguntei uma coisa e ela respondeu outra."

## O que eu mudaria (voz do Seu Benedito)

"Quando eu falo que é quilombo, a máquina tem que entender logo que é quilombo e me mostrar os direitos da gente, não a regra geral. Queria que explicasse direitinho o que é essa consulta prévia: quem tem que chamar, quando, se a gente pode dizer não. E que dissesse a quem recorrer antes de fechar, não só depois. Se não sabe o preço do ônibus, que diga que não sabe, igual fez com a Defensoria. E menos palavra difícil: fala como se fosse para mim, não para o juiz."

## Observações do avaliador (fora da persona)

1. **Busca de escola com nome + município na mesma linha falha com mensagem enganosa.** Entrada `escola sao jose carlos chagas` retornou: "Não encontrei essa escola entre as escolas públicas do campo ativas no Censo Escolar mais recente. Confira a grafia ou use o código INEP." A escola existe. O usuário é levado a crer que ela não está na base, e a grafia estava correta. Sugestão: tentar separar município do nome, ou, quando não achar, oferecer "Quer informar o município e a UF?".
2. **Pergunta fora da base respondida com assunto vizinho em vez de recusa.** `qnto custa o onibus escolar por mes pra prefeitura` devolveu "Assunto: Quem é responsável pelo transporte escolar?", que não responde custo. O mesmo programa recusa corretamente `telefone da defensoria em eldorado sp`. A recusa honesta depende do vocabulário, não da pergunta.
3. **Pergunta com "quilombo" não aciona as regras quilombolas.** `a prefeitura pode fechar a escola do quilombo sem perguntar pra gente?` caiu no D1 genérico; os "Para continuar" (C1, C2, F1) não incluem o D5. Na ficha da escola quilombola de Carlos Chagas o D5 aparece, então a ligação existe na ficha mas não na pergunta livre.
4. **Link sugerido que não se aplica à ficha.** Nas duas fichas aparece "[F2] Por que a distância aparece como \"pelo menos\"?" logo abaixo de "A distância até as escolas que poderiam receber os alunos ainda não foi calculada para esta escola." Não há distância "pelo menos" na tela.
5. **Mensagem de erro sem quebra de linha, palavra cortada ao meio.** Em 110 colunas: "...Censo Escolar mais recente. Confira a g" / "rafia ou use o código INEP." As demais respostas são quebradas corretamente; essa não.
6. **URL quebrada em duas linhas.** No D5: "https://www.gov.br/mec/pt-br/cne/pdf/resolucoes-do-" / "cne/ceb/2012/rceb008_12.pdf". Quem copia a primeira linha leva um endereço errado.
7. **D5 não define "consulta prévia".** Afirma que ela vale, mas não diz o que é (prévia, livre, informada, de boa-fé, com as instituições representativas), que é exatamente o que a persona perguntou.
8. **Jargão sem explicação:** "órgão normativo do sistema de ensino", "nucleação", "polos quilombolas", "povos indígenas e tribais", "ação civil pública", "ressarce", "LDB" (sigla nunca expandida, só "LDB (Lei 9.394/1996)").
9. **Ficha: números sem contexto.** "Alunos em 2025: 82 ... Moram na zona rural: 50" numa "Escola municipal rural" deixa dúvida sobre os outros 32; e a matrícula salta de 43 (2021) para 81 (2022) sem comentário. Não é erro, mas um leigo vai perguntar.
10. **Tela nunca é limpa:** cada volta ao menu reimprime abaixo do histórico, então a resposta nova fica misturada com as antigas. Para quem lê devagar, é fácil se perder.
11. Pontos positivos: códigos aceitos em minúsculas (`c1`), a busca por nome sem acento funciona (`durval maximo`, `sao jose`), a desambiguação por município/UF é clara, toda resposta traz fonte, artigo e data de conferência, e o aviso "não oficial" está presente sem atrapalhar.
12. Nota de método: um `Ctrl+L` que eu (avaliador) enviei por engano apareceu como "Opção: ^L3" e o programa aceitou como opção 3. Foi erro meu, não da persona; registro só porque mostra que caracteres de controle no início da entrada passam sem atrapalhar.
