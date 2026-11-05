# Teste de usabilidade r3: motorista (Seu Valdir)

Persona: Seu Valdir, 49 anos, motorista terceirizado de ônibus escolar no sertão da Bahia, 15 anos de rota em estrada de chão. Escreve pouco, às vezes tudo em maiúsculas, com erros.

Data: 05/11/2026. Sessão tmux: `u3-motorista`.

> **Aviso sobre a validade da sessão.** Nos primeiros minutos entraram na minha tela coisas que eu não digitei (ver a seção do avaliador). A causa foi um script auxiliar meu, com nome genérico (`s.sh`), na pasta temporária que os outros testadores também usam: os scripts se sobrescreveram e por um tempo eu mandei comandos para a sessão de outro testador, e ele para a minha. Depois troquei para um script com nome único e **refiz as tarefas 2, 3, 4, 5 e 6 na minha própria sessão**. Os números abaixo vêm da sessão limpa. A tarefa 1 tinha sido feita antes da troca; o texto bate exatamente com o D1 que apareceu depois na sessão limpa.

## Tarefas

| # | Tarefa | Concluiu | Entradas digitadas | Onde travou | O que encontrou |
|---|--------|----------|--------------------|-------------|-----------------|
| 1 | O que a lei exige antes de fechar | sim | 2 (`2`, `O QUE PRECISA PRA FECHAR ESCOLA DA ROÇA`) | não travou; "roça" foi entendido | D1: o Conselho de Educação tem de se manifestar e considerar justificativa da Secretaria, diagnóstico do impacto e manifestação da comunidade (LDB art. 28, parágrafo único) |
| 2 | EMEF Durval Máximo (Muniz Freire/ES) | sim | 2 (`3`, `DURVAL MAXIMO`) | não travou | **56 alunos em 2025** (pré-escola 18, anos iniciais 18, anos finais 20); 39 usam transporte público; INEP 32049501 |
| 3 | E. M. São José (Carlos Chagas/MG) | sim, na 4ª tentativa | 4 (`ESCOLA SAO JOSE`, `CARLOS CHAGAS MG`, `MG`, `ESCOLA SAO JOSE CARLOS CHAGAS`) | `ESCOLA SAO JOSE` trouxe 546 escolas; no campo "Município" escrevi `CARLOS CHAGAS MG`, ele pediu a UF de novo, eu pus `MG` e ele respondeu que nenhuma escola fica "nesse município/UF" | INEP 31151220, rural, comunidade quilombola, 82 alunos em 2025 |
| 4 | Como pedir os números à prefeitura | sim | 2 (`2`, `COMO PEDIR OS NUMERO PRA PREFEITURA`) | não travou | C1: Lei de Acesso à Informação, SIC da prefeitura, 20 dias (+10), recurso em 10 dias, guardar o protocolo |
| 5 | Pergunta que ele não sabe | sim | 1 (`meu contrato e terceirizado se fechar a escola eu perco o serviço?`), mais 3 outras que também caíram no "não sei" | — | Avisou "não trata de 'terceirizado', 'perco', 'servico'" e mostrou mesmo assim uma resposta sobre o Conselho de Educação. Nas perguntas de combustível, ônibus velho e estrada ruim disse "Não encontrei... Prefiro dizer isso a inventar" |
| 6 | Quantas escolas do campo fecharam na BA | sim | 1 (`QUANTAS ESCOLA DO CAMPO FECHOU NA BAHIA`) | não travou | Escolas públicas rurais na BA: **7.474 em atividade em 2025; 3.637 extintas de 2019 a 2025; 2.167 paralisadas em 2025, das quais 1.313 há 5 anos ou mais** |

## Perguntas da Parte 1 testadas

1. **"QUANTAS HORAS CRIANÇA PODE FICAR DENTRO DO ONIBUS"**: serviu em parte. A resposta (D3) diz que a norma nacional não fixa o tempo máximo e manda perguntar à Secretaria qual é o limite local. Eu queria um número, mas pelo menos sei a quem perguntar. O aviso do topo diz que a resposta "não trata de 'quantas', 'ficar', 'dentro'", só que ela trata do tempo, e isso me deixou na dúvida se valia.
2. **"se a escola fechar a rota dobra quem paga o combustivel a mais"**: do jeito que escrevi, não serviu ("Não encontrei"). Quando reescrevi `QUEM PAGA O ONIBUS ESCOLAR` veio T2 (município ou estado, conforme a rede do aluno) e T3 (PNATE paga combustível e manutenção). Com isso entendi que quem paga é a prefeitura com ajuda do PNATE. Se o contrato do terceirizado cobre a rota maior, continuei sem saber.
3. **"PREFEITURA PODE MANDAR RODAR COM ONIBUS VELHO? O MEU TEM MAIS DE 20 ANO"**: não serviu ("Não encontrei"). A orientação T4 (vistoria a cada seis meses) existe e responderia em parte, mas só achei pelo menu ou com `ONIBUS VELHO PODE`, e aí ele me deu uma lista de 5 assuntos para escolher.
   - Extra: **"QUAIS DOCUMENTO O MOTORISTA DE ONIBUS ESCOLAR PRECISA TER"** serviu direto (T4: mais de 21 anos, categoria D, curso especializado, no máximo uma infração gravíssima em 12 meses, CTB arts. 136 a 139).

## Notas (na voz do Seu Valdir)

- (a) Foi fácil achar o que procurava: **3**. "A ESCOLA DURVAL ACHEI DE PRIMEIRA. A SAO JOSE DEU TRABALHO, PUS A CIDADE E ELE DISSE QUE NAO TINHA. ONIBUS VELHO ELE NAO ACHOU MAS TINHA LA NO MENU."
- (b) Entendeu as respostas: **4**. "Escreve claro, sem enrolação. Só não entendi aquele aviso que diz que não trata da minha pergunta e responde mesmo assim."
- (c) Confiaria para levar a uma reunião, conferindo com o órgão: **4**. "Tem a lei e o número do artigo em tudo, isso eu levo pra secretaria. Mas do meu contrato e do ônibus velho ele não disse nada, aí não adianta."

## O que você mudaria (Seu Valdir)

"QUANDO EU PERGUNTO DE ONIBUS VELHO TEM QUE MOSTRAR A REGRA DO VEICULO, ELA ESTA LA. NA HORA DE ACHAR ESCOLA DEIXA EU ESCREVER A CIDADE E O ESTADO JUNTO. E POE ALGUMA COISA PRO MOTORISTA, DO CONTRATO, DE QUEM PAGA O DIESEL QUANDO A ROTA AUMENTA E DE QUANTO TEMPO A CRIANÇA AGUENTA NA ESTRADA RUIM DE MAIS. SE NAO SABE, FALA PRA QUEM EU PERGUNTO."

## Observações do avaliador (fora da persona)

**Algo entrou na sessão sem eu digitar? Sim, mas a culpa foi do método do teste, não do programa.** Na primeira parte apareceram na minha tela `Sua pergunta: D1`, `Opção inexistente: 'durval maximo'`, `EMEF Durval Máximo`, `1`, `2` e uma pergunta sobre "fechamento de escola do campo por falta de consulta à comunidade", nada disso digitado por mim. Causa: meu script auxiliar `scratchpad/s.sh` ficava numa pasta temporária usada pelos outros testadores, e algum deles também gravou um `s.sh` ali (depois o arquivo sumiu). Por um tempo os scripts se cruzaram: minhas chamadas mandavam teclas para a sessão de outro testador e capturavam a tela dele, e as dele caíam na `u3-motorista`. Depois que troquei para `scratchpad/motorista_r3/envia_motorista.sh` não entrou mais nada estranho. **As sessões dos outros testadores também podem ter recebido entradas minhas** (`2`, `O QUE PRECISA PRA FECHAR ESCOLA DA ROÇA`, `3`, `DURVAL MAXIMO MUNIZ FREIRE`, `SAO JOSE CARLOS CHAGAS`, `C1`) entre ~11h50 e ~11h52. Recomendação para a próxima rodada: incluir o {{ID}} no nome do script auxiliar, já na instrução.

Defeitos concretos do programa:

1. **A busca de escola não aceita município e UF juntos.** Depois de `ESCOLA SAO JOSE` (546 resultados), no campo `Município ou código INEP (Enter para pular):` digitei `CARLOS CHAGAS MG`; ele pediu `UF, ex.: ES (Enter para pular):`, eu pus `MG` e a resposta foi "Nenhuma das escolas com essas palavras no nome fica nesse município/UF." A escola existe (achei depois com `ESCOLA SAO JOSE CARLOS CHAGAS`). Pelo jeito ele usou "CARLOS CHAGAS MG" inteiro como nome de município. Mensagem enganosa: diz que não existe quando o problema é o formato do que eu digitei.
2. **A lista de desambiguação começa pelo Acre, em ordem alfabética de UF.** Com 546 escolas, os 8 exemplos (`ESC SAO JOSE I, Feijó/AC`...) não ajudam ninguém de MG/BA. Não chega a ser erro, mas faz a pessoa achar que a escola dela não está lá.
3. **Pergunta sobre ônibus velho não chega na T4, que já existe.** `PREFEITURA PODE MANDAR RODAR COM ONIBUS VELHO? O MEU TEM MAIS DE 20 ANO` resultou em "Não encontrei, na base deste assistente, uma orientação confiável". O tópico `[T4] Quais são as regras para o veículo e o motorista do transporte escolar?` (inspeção semestral, autorização do órgão de trânsito) é a resposta mais próxima e devia ser oferecido, nem que fosse com o aviso de "mais próxima". Com `ONIBUS VELHO PODE` aparece uma lista de 5 assuntos, com T4 em último.
4. **O aviso de "orientação mais próxima" contradiz a resposta.** Para `QUANTAS HORAS CRIANÇA PODE FICAR DENTRO DO ONIBUS`: "Atenção: esta é a orientação mais próxima que encontrei, mas ela não trata de "quantas", "ficar", "dentro"." Logo abaixo, a resposta trata justamente do tempo ("A norma nacional não fixa o tempo máximo em minutos"). As palavras listadas são vazias ("quantas", "ficar", "dentro"), e isso faz parecer que o aviso é mecânico. O mesmo vale para `"terceirizado", "perco", "servico"`, aqui com "servico" sem cedilha, que não foi o que eu escrevi ("serviço").
5. **Combustível e contrato terceirizado ficam sem resposta, mas o "não sei" não diz a quem perguntar.** "Não encontrei... Você pode escolher um deles no menu, reformular a pergunta..." Para quem é motorista, faltaria uma linha do tipo "sobre contrato de transporte, procure a Secretaria / o Conselho do Fundeb". Do jeito que está, o "não sei" é honesto, mas deixa a pessoa sem caminho.
6. **Título quebrado no meio da palavra.** Linhas de "Assunto:" com mais de 110 colunas são cortadas no meio: `[O que a comun` / `idade pode fazer]`, `há 5 an` / `os ou mais`. O corpo do texto quebra bem; os títulos e os itens de lista, não.
7. **Prompt duplicado.** Depois da lista "Sua pergunta combina com mais de um assunto. Qual deles?" aparece "Digite o código entre colchetes, ou reformule a pergunta." e em seguida a linha `Digite um código entre colchetes, outra pergunta, ou Enter para voltar ao menu:` impressa duas vezes seguidas.
8. **"Escolas do campo" × "escolas públicas rurais".** Perguntei por "escola do campo"; a resposta F muda para "Escolas públicas rurais em BA" sem explicar se é a mesma coisa (há o D2 sugerido, mas a troca de termo passa despercebida).
9. **Afirmação um pouco forte:** "Uma escola paralisada há muitos anos costuma estar fechada na prática, sem o ato formal e, talvez, sem o rito que a lei exige." O "costuma" não tem fonte; a contagem é do Censo, mas a inferência é do projeto. Sugiro marcar como interpretação.
10. **Datas de conferência diferentes:** a resposta dos números diz "Conferida em 04/11/2026" e as demais "05/11/2026". Não é erro, mas chama atenção de quem confere.
11. **Palavras difíceis para a persona:** "nucleada" (explicada entre parênteses, ok), "ressarce", "microdados", "PNATE"/"FNDE" (siglas sem explicação), "registrador de velocidade" (o motorista diria "tacógrafo").

Pontos fortes: achou "roça" como escola do campo; a ficha da escola é clara e diz com todas as letras que a distância não foi calculada ("Não vou estimar um número sem base"); as respostas citam lei e artigo; o "não sei" não inventa.
