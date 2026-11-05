# Teste de usabilidade simulado: persona estudante (Kauã, 16, escola do campo no PA)

Data: 05/11/2026. Terminal tmux 110x60, `/usr/bin/python3 -I src/sistema.py`.
Perguntas às cegas (Parte 1): `estudante-perguntas.json`, escritas antes de abrir o programa.

## Tarefas

| # | Tarefa | Concluiu | Entradas | Onde travou | O que encontrou |
|---|--------|----------|----------|-------------|-----------------|
| 1 | O que a lei exige antes de fechar escola do campo | sim | 2 (`2`, `oq a lei fala pra fechar escola do campo`), mais 3 testes de limite antes (Enter vazio, `oi`, `7`) | não travou | D1: Conselho de Educação precisa se manifestar considerando justificativa da Secretaria, diagnóstico do impacto e manifestação da comunidade escolar (LDB art. 28, par. único) |
| 2 | Achar EMEF Durval Máximo, Muniz Freire/ES | sim | 2 (`3`, `durval maximo`) | não travou; sem acento funcionou | **56 alunos em 2025** (pré-escola 18, anos iniciais 18, anos finais 20); INEP 32049501 |
| 3 | Achar Escola Municipal São José, Carlos Chagas/MG | sim, com tropeço | 5 (`3`, `sao jose carlos chagas`, `sao jose`, `carlos chagas`, `mg`) | 1ª busca com nome + cidade juntos: "Não encontrei essa escola" | INEP 31151220, rural, quilombola, 82 alunos em 2025 |
| 4 | Como pedir os números à prefeitura | sim | 1 (`c1`, a partir da ficha da escola) | não travou; código minúsculo aceito | C1: Lei de Acesso à Informação, pedido no SIC, 20 + 10 dias, recurso em 10 dias |
| 5 | Pergunta que o programa não sabe | sim | 2 (`2`, `qual time vai ganhar o brasileirao mano`); também testei `z9`, `asdfghjkl` e pergunta vazia | não travou | Disse que não tem orientação confiável, "Prefiro dizer isso a inventar uma resposta", e listou os 4 assuntos que conhece. Não inventou nada |

## Perguntas da Parte 1 testadas

| Pergunta (como digitada) | O que o programa fez | Serviu pro Kauã? |
|---|---|---|
| `eu tenho 16 anos posso pedir informação pra prefeitura ou tem q ser meus pais` | Abriu C1 (LAI): "Qualquer pessoa pode pedir... O pedido precisa da identificação de quem pede" | **parcial**. Diz "qualquer pessoa", mas não fala nada de idade; ele continua sem saber se menor de 16 conta, e "identificação" o deixa com dúvida se precisa de CPF ou dos pais |
| `e o barco escolar se fechar a escola vai ter barco pra levar a gente pra outra` | Não encontrou. Reformulando (`transporte de barco`) caiu em T3 (dinheiro do transporte; cita que o Caminho da Escola financia barcos). T1 diz que transporte é direito; T4 só fala de ônibus | **não**. A dúvida dele (se fechar, a prefeitura é obrigada a levar de barco, quanto tempo de viagem) não foi respondida. 4 entradas tentando |
| `os aluno pode fazer alguma coisa pra n fechar a escola` | Respondeu D6 (padrão nacional do diagnóstico / PL 3.091/2024) | **não** pela pergunta livre. Só achou o útil indo pelo menu `1` > `2` > `c2` (C2: alunos fazem parte da comunidade escolar, registrar em ata), mais 3 entradas |

## Notas (voz do Kauã)

- (a) foi fácil achar o q procurava: **3**. "a escola de muniz freire achei de primeira mas a de carlos chagas n achou qnd botei tudo junto e o barco nada"
- (b) entendeu as respostas: **3**. "da pra entender mas tem umas palavra tipo órgão normativo deliberativo prorrogavel microdados q eu tive q ler 2 vez"
- (c) confiaria pra levar numa reunião conferindo com o órgão: **4**. "gostei q tem a lei e o link e q ele fala q n sabe em vez de inventar, isso eu levava sim"

## O que você mudaria (voz do Kauã)

"mano bota coisa de barco pq aqui é tudo rio, o programa so fala de onibus com faixa amarela, n serve pra gente. e fala direto se aluno de menor pode pedir informação sozinho. qnd eu escrevo o nome da escola e a cidade junto tinha q achar. e qnd eu pergunto o q os aluno pode fazer tinha q aparecer a parte da comunidade e n um projeto de lei"

---

## Observações do avaliador (fora da persona)

1. **Resposta não bate com a pergunta (roteamento).** `os aluno pode fazer alguma coisa pra n fechar a escola` abriu "Assunto: Existe um padrão nacional de como fazer o diagnóstico do impacto?" (D6). O conteúdo certo existia em C2/C4.
2. **Lacuna de conteúdo: transporte fluvial.** `e o barco escolar se fechar a escola vai ter barco pra levar a gente pra outra` caiu no fallback mesmo havendo o assunto Transporte escolar. T4 ("Quais são as regras para o veículo e o motorista") cita só o Código de Trânsito: "faixa amarela com a palavra ESCOLAR", "habilitação na categoria D". Não menciona embarcação nem avisa que essas regras não valem para barco. Para escola do campo na Amazônia isso é o caso típico, não a exceção.
3. **Menor de idade não tratado.** C1 diz "Qualquer pessoa pode pedir" e "precisa da identificação de quem pede", sem dizer se adolescente pode pedir sozinho. A pergunta de 16 anos foi roteada para C1 (certo), mas a dúvida central ficou sem resposta.
4. **Busca de escola com nome + município na mesma linha falha.** `sao jose carlos chagas` deu "Não encontrei essa escola entre as escolas públicas do campo ativas no Censo Escolar mais recente. Confira a grafia ou use o código INEP." A grafia estava certa; o que faltou foi separar a cidade. A mensagem induz a pessoa a achar que errou o nome.
5. **Prompt pede "código" quando não há código na tela.** Depois do "Não encontrei essa escola" e depois de pergunta vazia ("Você não digitou nada. Escreva uma pergunta, um código como D1, ou o nome da escola."), vem "Digite um código para continuar, ou Enter para voltar ao menu:". A mensagem manda escrever pergunta/nome e o prompt diz "código". (Na prática o prompt aceita nome de escola e pergunta livre: `sao jose` ali virou busca. Funciona, mas ninguém descobre isso lendo a tela.)
6. **Mensagens sem quebra de linha.** O resto do texto quebra em ~78 colunas, mas estas passam da largura: "Não encontrei essa escola ... Confira a g / rafia ou use o código INEP." (quebrou no meio da palavra a 110 colunas); "Encontrei 546 escolas com esse nome. Para escolher, informe o município e a UF (mostrando as primeiras):"; "Você não digitou nada. Escreva uma pergunta, um código como D1, ou o nome da escola." Num celular/terminal estreito fica pior.
7. **Sugestão incoerente com a ficha.** Nas fichas das duas escolas aparece "A distância até as escolas que poderiam receber os alunos ainda não foi calculada para esta escola" e, logo abaixo, a sugestão "[F2] Por que a distância aparece como "pelo menos"?". A distância não aparece de jeito nenhum. F2 também é sugerido ao fim de T4 (regras do veículo), sem relação.
8. **T3 respondendo pergunta sobre barco.** `transporte de barco` abriu "De onde vem o dinheiro do transporte escolar?". Útil de passagem (cita Caminho da Escola financiando barcos), mas não é o que se perguntou.
9. **Lista de 546 escolas começa pelo AC.** Com `sao jose`, mostra 8 escolas do Acre ("mostrando as primeiras") e pede município/UF. O fluxo de afunilar funcionou bem (`carlos chagas`, `mg` minúsculo aceito), mas "546 escolas com esse nome" inclui nomes que só contêm "SAO JOSE" (ex.: "ESC INDIGENA INSTITUTO SAO JOSE").
10. **Palavras difíceis para 16 anos:** "órgão normativo do sistema de ensino", "manifestação da comunidade escolar", "órgãos deliberativos", "prorrogáveis", "programa suplementar", "SIC" (sigla explicada só por extenso uma vez), "microdados por escola", "Ipea/geobr".
11. **Entrada inválida: bem tratada.** Enter vazio no menu: "Digite o número de uma opção."; `oi` e `7`: "Opção inexistente: 'oi'. Use 0, 1, 2, 3 ou 4."; código inexistente `z9` e `asdfghjkl` caem no fallback honesto. Códigos minúsculos (`c1`, `t1`) e UF minúscula (`mg`) aceitos.
12. **Ctrl+C:** imprime "^C" e "Até logo." e encerra, sem traceback. Observação técnica: o processo termina por sinal (tmux registrou "Pane is dead (signal 2)"), e na sessão tmux padrão a janela fecha na hora, então o "Até logo." nem chega a ser visto. Não é defeito visível ao usuário comum.
13. **Nota de procedimento:** mandei um Ctrl+C acidental logo após a tarefa 1 (erro meu de operação, não do Kauã). O programa saiu limpo; reiniciei a sessão com `remain-on-exit` para poder ler a tela final no teste proposital de Ctrl+C. Nada do teste depende do estado anterior.
