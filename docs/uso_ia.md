# Uso de inteligência artificial

## O assistente não usa modelo de linguagem

O Assistente Escola em Pauta (`python src/sistema.py`) responde só com regras explícitas e com o texto da base de orientações. Nenhuma resposta é gerada por modelo de linguagem no momento da consulta. Foi uma escolha: o enunciado pede respostas com fonte verificável e sem invenção, e regras podem ser testadas uma a uma.

## Onde a IA foi usada no desenvolvimento

O projeto foi desenvolvido com o **Claude Code** (Anthropic, modelos da família Claude), sob direção e revisão humanas. Na revisão de usabilidade do simulador entrou também o **Codex CLI** (OpenAI), como segundo revisor independente. Usos:

| Etapa | Uso da IA | O que ficou com a equipe |
|---|---|---|
| Escolha do problema | levantamento de queixas em 5 famílias de fontes, agrupamento e pontuação (ver `docs/metodologia.md`) | a escolha entre os finalistas, o recorte e o teto de esforço |
| Base de orientações | rascunho das orientações e verificação de cada norma por um agente que abriu o texto oficial e copiou o trecho literal | aprovação dos temas e dos registros; inclusão da alimentação escolar; decisão de manter os casos indígena/quilombola e o caso de Muniz Freire |
| Código | escrita do código, dos testes e dos scripts, inclusive a reescrita do núcleo em TypeScript para a versão web e o contrato que a prende ao terminal | decisões de arquitetura (camadas, pré-cálculo, critério de transporte fluvial, linguagem da versão web, publicação) |
| Revisão adversarial | um segundo modelo recebeu a escolha do problema e, depois, a versão web, com a missão de atacar o que considerávamos mais sólido | quais achados aceitar; os aceitos estão em `docs/metodologia.md` e nas correções do site |
| Simulador de plano | proposta do desenho, parecer adversarial medido nos dados, código, contrato e revisão antes de publicar | a regra de destino (sem preferência pelo município, com indicação da prefeitura) e a decisão de manter o critério da ficha |
| Usabilidade do simulador | dois revisores (Claude e Codex) analisaram a página em separado, sem ver um a opinião do outro; o redesenho foi atacado de novo pelos dois | o pedido de uma página mais fácil de entender; quais achados aceitar |
| Teste do site | três agentes com papéis (agricultora no celular, conselheira que imprime, auditor de dados) testaram o site publicado | a triagem dos achados e as decisões de critério, como arredondar o piso para baixo |
| Prompts | os dois modelos de instrução de resposta (A e B) foram escritos como especificação e comparados nas perguntas de teste | escolha do modelo padrão |
| Testes | planejamento das perguntas de teste e dos indicadores | o segundo conjunto de perguntas e o teste de usabilidade, feitos por pessoas que não viram a base |
| Textos | revisão de linguagem do README | revisão final |

## Validação crítica: o que a conferência pegou

Toda afirmação jurídica da base foi conferida no texto oficial, com o trecho literal registrado (`docs/pesquisa/base-fontes-verificadas.md`, mantido fora do repositório público por ser material de trabalho). A conferência mudou a base em pontos que um rascunho de memória teria errado:

- **Alimentação escolar:** o mínimo de compra da agricultura familiar é 45% desde 01/01/2026 (Lei 15.226/2025). A própria página do FNDE ainda dizia 30%.
- **Nucleação dos anos iniciais:** a Resolução CNE/CEB 2/2008 admite, em caráter excepcional, nucleação dentro do campo. O rascunho dizia que a regra era absoluta.
- **Escola "paralisada" no Censo:** o INEP define como atividades temporariamente suspensas, sem extinção formal. Uma leitura anterior, também apoiada por IA, tinha concluído "escola já fechada"; a correção veio da leitura do caderno de conceitos do INEP.
- **Lei de Acesso à Informação:** o pedido exige identificação de quem pede, mas não exige justificativa. O rascunho omitia a identificação, o que importa para quem teme retaliação.
- **PL 3.091/2024:** os prazos de 1 ano e de 90 dias tratam de coisas diferentes, e o projeto não é lei (está parado na Câmara desde maio de 2026).

Erros da IA no código, achados por teste ou por uso:

- Uma afirmação técnica sobre o roteador OSRM ("ignora o tipo de superfície") estava errada e foi corrigida depois de lido o perfil do roteador.
- A busca de escolas descartava "São" como se fosse o verbo "são", e "Escola Municipal São José" devolvia escolas sem "São" no nome. O teste automático passava, porque só conferia que havia uma lista; o teste foi reforçado para exigir a escola certa.
- Um commit entrou com um teste falhando, porque o resultado do teste não foi conferido de fato; o processo passou a exigir que a suíte passe antes do commit.
- O acerto de 92% no conjunto às cegas foi gravado antes de três orientações novas entrarem na base. Rodado de novo, o mesmo código dava 86% com o gabarito antigo. A diferença não era o programa piorar: as orientações novas respondiam melhor perguntas cujo rótulo era anterior a elas. Um segundo juiz, também sem ver as respostas, rotulou de novo as 50 perguntas, e o rótulo original ficou guardado em cada uma.
- Para tirar o nome do lugar da conta da busca, o programa passou a apagar nomes de município da pergunta. "Própria" e "Modelo" são municípios (Propriá, em Sergipe, e Modelo, em Santa Catarina), e sumiam de "escola própria" e "modelo de diagnóstico". O nome agora só conta como lugar depois de "em", "de", "no" ou antes da sigla do estado.
- A primeira contagem de escolas indígenas e quilombolas fechadas deu zero no Brasil inteiro. O Censo só marca a localização diferenciada enquanto a escola funciona; paralisada e extinta vêm em branco. A contagem passou a usar a localização do último ano em atividade e é apresentada como piso ("pelo menos").
- Uma URL de lei foi escrita de memória na base e trocada pela que o agente de fontes de fato abriu, antes do commit.
- Na versão web, o leitor dos traçados seguia um formato provisório, diferente do arquivo que o pré-cálculo de fato gravou. A captura de tela de uma escola de Mato Grosso mostrou o mapa sem estrada, e o leitor foi corrigido.
- A revisão adversarial da versão web achou cinco problemas que bloqueavam a publicação, todos corrigidos antes de publicar: o link "pular para o conteúdo" levava a uma página de erro; 171 fichas diziam "0,0 km" para escolas no mesmo endereço (agora "no mesmo lugar ou quase"); o cartão do link das escolas do Norte saía sem o aviso de transporte por rio; uma escola sem município no Censo aparecia como "null, null"; e o link antigo da ficha não abria sem sinal.
- Ao tirar da tela os códigos das orientações (D1, C5), a primeira versão da troca perdia o texto depois da última citação, e sumia o parágrafo principal das orientações. Os testes passavam, porque conferiam o texto e não a tela; a captura de tela pegou o erro antes da publicação, e um teste novo confere que nenhum trecho se perde.
- Uma mensagem de commit citou 39.852 escolas sem conferir; o número certo é 41.158. A correção ficou registrada no commit seguinte.
- O teste por agentes achou erros de critério no código escrito com IA: a distância de "pelo menos" arredondada para cima; o cartão do link arredondando diferente da ficha; o checklist da lei marcando como pronto o diagnóstico do impacto; uma nota sobre outra escola impressa em todas as fichas; e "sem matrícula" em escolas com alunos fora das etapas regulares. Todos foram reproduzidos e corrigidos.

- No simulador, a IA errou três vezes antes da revisão: dobrou um número do parecer ao "corrigi-lo" (a distância do arquivo já era de ida e volta); afirmou que os dados do simulador já estavam publicados quando o script de publicação os excluía; e escreveu no README que o Norte concentrava os maiores fechamentos em lote, quando três dos cinco maiores são do Nordeste. Os três foram achados ao conferir a fonte e corrigidos antes do commit.
- A revisão do simulador pegou o link do plano errado no rodapé impresso, o plano apagado pelo link "pular para o conteúdo" e a tela que fechava as escolas abertas a cada mudança. Ao corrigir, apareceu um defeito antigo da ficha: o texto só para leitor de tela não tinha estilo, e a letra de cada receptora aparecia repetida na tela ("A. EMEF Alto Monforte"). Nenhum teste nem revisão anterior tinha notado.

- No redesenho do simulador, a IA agrupou as etapas que iam para a mesma escola e juntou uma etapa indicada pela prefeitura com outra que ia para lá pela regra: a etiqueta "indicada pela prefeitura" passou a valer para as duas. O teste da interação achou antes do commit. O pedido aos revisores também dizia que o maior município tinha cerca de 120 escolas do campo; um deles mediu 317 (Santarém/PA).
- Para o deploy do site, que passou a estourar o limite de 10 minutos do GitHub Pages, a IA recomendou um workflow próprio com tempo maior, apoiada na descrição da opção de tempo da action oficial. O código da action corta qualquer valor em 10 minutos, e o deploy falhou de novo. A solução foi reduzir o número de arquivos (os 4.479 municípios do simulador viraram 512 pedaços). A lição ficou registrada: conferir o código, e não só a documentação, antes de recomendar uma configuração.

## O que a IA não decidiu

O problema, o público, os temas, o que entra e o que sai da base, o critério de transporte fluvial, a participação na competição e o uso da ferramenta fora do curso foram decisões da equipe. A IA propôs; as propostas foram aceitas, mudadas ou recusadas por pessoas, e várias recomendações foram recusadas (por exemplo, a de limitar a primeira versão à consulta sem rotas).
