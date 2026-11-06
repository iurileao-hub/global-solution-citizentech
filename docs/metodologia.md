# Metodologia: como escolhemos o problema e como validamos a solução

O tema CitizenTech pede para começar pela vida real. Levamos isso a sério: **o problema foi escolhido por um processo explícito, antes de qualquer decisão de tecnologia**, e a rubrica de avaliação só entra depois, como lista de conferência.

## Premissa

Quem vive na interseção entre cidade, campo e comunidades isoladas costuma ter pouca voz no debate público. Por isso o noticiário, sozinho, mostraria sobretudo os problemas de quem já é ouvido. Buscamos a voz dessas pessoas onde ela fica registrada sem que alguém precise ir até lá.

## Fases

**Fase 0: critérios definidos antes da busca.** Cada problema candidato recebe nota de 1 a 3 em seis critérios:

| Critério | Peso |
|---|---|
| Ponte: o problema aparece em mais de um cenário (cidade, campo, remoto) | ×2 |
| Dado obtível, ou simulável com honestidade, para construir e avaliar um protótipo | ×2 |
| Magnitude: quantas pessoas, com que frequência | ×1 |
| Voz baixa: pouca presença no debate público de quem vive o problema | ×1 |
| Parte do problema é tratável por computação | ×1 |
| Vantagem da equipe: conhecimento do domínio e acesso a quem vive o problema | ×1 |

**Fase 1: divergência.** Cinco buscas, uma por família de fonte:
1. notícias e tendências recentes, incluindo mídia independente e regional;
2. voz indireta: ouvidorias, agências reguladoras, Defensorias, Ministério Público;
3. desigualdades medidas nos dados oficiais (Censo Escolar, ANEEL, PNAD, Censo 2022, Atlas de Desastres, entre outros);
4. estudos qualitativos feitos com as próprias comunidades, com as falas dos participantes;
5. metas dos ODS do tema (2, 3, 4, 9, 10, 11 e 13) em que o Brasil está mais atrasado.

Cada busca registrou os problemas **na linguagem de quem os vive**, sem vocabulário de tecnologia, com fonte, magnitude, cenários e dado disponível.

**Fase 2: convergência.** As queixas foram agrupadas em temas e pontuadas pelos critérios. **A nota serviu de insumo, e a escolha final foi um julgamento declarado da equipe**, que deu prioridade à educação por considerá-la a principal oportunidade de transformação social.

**Fase 2b: recorte.** Os temas finalistas são problemas complexos, que dependem de coordenação entre governos. Para torná-los tratáveis, mapeamos quem decide o quê, quando e com que informação. A regra do recorte: **a solução deve servir a quem já tem poder sobre uma decisão, sem depender da coordenação que falta**, e deve medir o resultado em termos do cidadão afetado.

**Fase 2c: revisão adversarial.** Um segundo modelo de IA recebeu todo o raciocínio com a missão de atacar justamente o que considerávamos mais sólido. A revisão encontrou erros reais (uma leitura incorreta de dado, um critério que favorecia a rubrica, notas generosas) e mudou o recorte. Os achados aceitos estão incorporados nesta versão.

**Fase 3: validação.** Antes de qualquer contato, cada recorte passa por uma **anamnese documental**: normas, relatórios de gestão e decisões judiciais mostram como a decisão é tomada hoje e se o decisor já dispõe da informação. Quando há acesso sem contato a frio, acrescentamos uma conversa com quem decide, com uma pergunta: "o que você olha hoje quando decide?".

**Regra de parada.** Uma rodada de busca só. Se nenhum candidato convencer, voltamos aos critérios com o que houver, sem abrir nova pesquisa.

## Validação da solução

Cada rodada de teste mediu uma coisa diferente e mostrou o limite da anterior. A regra que atravessa todas: **uma medida feita nas mesmas perguntas usadas para ajustar o programa é otimista**, então cada ajuste pede uma rodada nova, com perguntas que ninguém da equipe viu.

**1. Conferência das fontes.** Cada orientação da base foi conferida no texto oficial da norma (Planalto, MEC/CNE, Senado, Câmara, FNDE, INEP), com o trecho literal registrado. A conferência mudou a base em cinco pontos que um texto de memória teria errado. Os dois maiores: o mínimo de compra da agricultura familiar na merenda subiu para 45% em 2026, e a própria página do FNDE ainda dizia 30%; e "paralisada", no Censo Escolar, quer dizer atividades temporariamente suspensas, sem extinção formal.

**2. Testes da equipe.** Vinte perguntas escritas pela equipe, com a resposta esperada definida antes de rodar. A primeira rodada acertou 75%. Os cinco erros mostraram problemas típicos de busca (radicais que colidem, como "quilombola" e "quilômetros"; uma palavra solta decidindo a resposta; nome de escola lido como pergunta), e as regras corrigidas levaram o acerto a 100%. Esse número foi tratado como suspeito desde o início, porque as regras foram ajustadas nas mesmas perguntas que o mediam.

**3. Uso interativo e ambiente de quem corrige.** Usar o programa como uma pessoa usaria achou quatro defeitos que a avaliação automática não pegava. O pior: "são" era descartado como verbo dentro de "São José". O programa também foi testado num clone limpo do repositório, com Python 3.10 e sem nenhum pacote instalado.

**4. Teste de usabilidade simulado.** Cinco agentes de IA receberam, cada um, uma persona de quem enfrenta o fechamento de uma escola: uma agricultora assentada com pouca escolaridade, uma liderança quilombola que dita ao neto, uma conselheira municipal de educação, uma professora de escola rural e um estudante ribeirinho que escreve como no celular. Cada agente:
- escreveu 10 perguntas **antes de ver o programa**, no jeito de escrever da persona;
- usou o programa num terminal real, cumprindo 5 tarefas, e registrou onde travou e quantas tentativas fez;
- deu notas de 1 a 5 para facilidade, entendimento e confiança.

As 50 perguntas formaram um conjunto novo. **Um juiz separado**, que leu a base mas não viu as respostas do programa, definiu a resposta esperada de cada uma. Só depois o programa foi medido.

| Medida nas 50 perguntas às cegas | Antes dos ajustes | Depois dos ajustes |
|---|---|---|
| Acerto | 68% | 88% |
| Erros calados (resposta errada sem nenhum aviso) | 16 | 3 |

O resultado "antes" é o honesto. Os 68% mostraram que o filtro criado nos testes da equipe tinha ficado rigoroso demais para perguntas longas e naturais: 10 "não sei" quando a base tinha a resposta. Também houve 6 respostas erradas dadas com segurança, o pior tipo de erro, porque a pessoa sai acreditando nele. A correção principal foi uma faixa intermediária: o assistente responde e **diz quais palavras da pergunta a orientação não cobre**. O resultado "depois" já é otimista, pelo mesmo motivo da rodada 2.

Os agentes também acharam defeitos de tela que se repetiam entre as personas (nome da escola junto com a cidade, convite para digitar um código quando nenhum aparecia, palavras técnicas sem explicação) e quatro assuntos que a base não cobria. Os assuntos viraram orientações novas, conferidas no texto oficial: barco escolar, o que o Conselho deve exigir, aluno com deficiência no transporte e adolescente pedindo informação.

Depois das orientações novas, um erro de registro apareceu: o 92% anotado para o conjunto às cegas tinha sido medido antes de três delas entrarem na base. Rodado de novo, o mesmo código dava 86% com o gabarito antigo. A diferença vinha do gabarito: as orientações novas respondiam melhor perguntas rotuladas antes delas. Daí saiu uma regra para as rodadas seguintes. **O resultado "antes" fica congelado com o rótulo original. Para medir o estado atual, um juiz novo, que lê a base mas não vê as respostas, rotula de novo**, e cada pergunta mudada guarda o rótulo anterior. Corrigir o gabarito à mão, vendo as respostas do programa, seria corrigir a prova olhando a do aluno. Com o gabarito do segundo juiz (13 rótulos mudaram), a versão acertou 92%.

**5. Terceira rodada.** Para medir o programa corrigido com honestidade, seis personas novas, escolhidas para cobrir quem as primeiras deixavam de fora, escreveram 60 perguntas que nem a equipe nem o programa tinham visto:
- um secretário municipal de educação que quer fechar escolas, o lado oposto ao das primeiras personas e um teste de neutralidade;
- uma mãe guarani-kaiowá, com o português como segunda língua;
- um motorista de transporte escolar;
- uma avó que dita as perguntas no celular (o texto chega como o reconhecimento de voz escreve, com "fexar");
- um radialista comunitário que precisa de números citáveis;
- uma advogada de sindicato rural, que confere a precisão jurídica.

Um juiz novo rotulou as 60 perguntas sem ver as respostas, e o programa foi medido **antes de qualquer ajuste**.

| Medida nas 60 perguntas da terceira rodada | Antes dos ajustes | Depois dos ajustes |
|---|---|---|
| Acerto | 52% | 70% |
| "Não sei" quando a base tinha a resposta | 20 | 6 |
| Respostas erradas dadas com segurança | 3 | 2 |
| Respostas erradas com aviso de que a pergunta não estava toda coberta | 4 | 6 |

A queda de 92% para 52% é a lição principal da validação: **o acerto nas perguntas usadas para ajustar não se transfere para perguntas novas**. A direção do erro, porém, foi a desejada. De 29 perguntas não acertadas, 20 terminaram em "não sei" e só 3 em resposta errada sem aviso; o programa falha calando, não inventando. As causas, por ordem de peso:
- a grafia do reconhecimento de voz ("fexar") derrubou 5 das 10 perguntas da avó;
- perguntas técnicas, com termos que a base não usa ("vinculante", "legitimidade", "jurisprudência", "vigente"), caíram no "não sei" mesmo quando a orientação existia;
- "Rio Grande do Sul" foi lido como o município de Rio Grande, sem aviso, o defeito mais grave da rodada, porque o número sai errado com cara de certo;
- o aviso de cobertura parcial listava palavras de cortesia ("obrigada", "viu") e o próprio tema ("fechar") como se fossem o assunto que faltava.

A advogada apontou afirmações que diziam mais do que a norma, e o secretário apontou que a base fala só com a comunidade, sem caminho para quem tem de cumprir o rito. Um agente conferiu 12 pontos no texto oficial e achou dois erros de verdade: o Conselho Municipal só é o competente se o município tem sistema próprio de ensino (senão é o Estadual), e a ata da reunião com a comunidade não é exigência da lei nacional. Outros pontos eram imprecisões que mudavam o sentido. O "sim, deu certo recorrer" do caso de Muniz Freire se apoiava em liminar e cautelar, que são provisórias, e virou "sim, por enquanto". A orientação sobre a quem recorrer passou a dizer que uma associação de pais também pode propor a ação civil pública.

Os ajustes, em ordem de efeito:
- **Mecânica da busca:**
  - o nome do lugar citado deixou de contar como assunto;
  - "x" e "ch" passaram a ser a mesma letra, nos dois lados da comparação;
  - a sigla ditada letra a letra virou sigla;
  - o nome do estado passou a valer antes do de município;
  - perguntas de contagem ("quantas fecharam", "está aumentando?") passaram a ir para os números.
- **Conteúdo:**
  - as correções da conferência;
  - a orientação indígena separada da quilombola;
  - o caminho do gestor;
  - a série anual de fechamentos e o recorte de escolas indígenas e quilombolas, com aviso de que é um piso.
- **Tela:**
  - menu que aceita frase e número por extenso;
  - município com a sigla do estado junto;
  - links que não se partem ao meio.

Três achados dessa etapa mostram por que cada mudança foi medida antes de ser aceita:
- "Própria" e "Modelo" são nomes de município, e sumiam das perguntas quando o programa passou a apagar o lugar citado. O nome agora só conta como lugar com uma preposição antes ou a sigla do estado depois.
- A primeira contagem de escolas indígenas fechadas deu zero no Brasil inteiro, porque o Censo só marca a localização diferenciada enquanto a escola funciona.
- Uma variante controlada, que tirava "fechar" da conta da cobertura, ganhava 1 pergunta na terceira rodada e perdia 4 nas antigas. Ficou de fora.

Os 70% são otimistas pelo mesmo motivo das rodadas anteriores. Além disso, um terceiro juiz cego refez 17 rótulos depois das orientações novas (as perguntas indígenas, por exemplo, passaram para a orientação indígena). No conjunto às cegas anterior, os mesmos ajustes deixaram o acerto em 88%, contra 92%: as perguntas novas ganharam e as antigas perderam um pouco. Essa troca só aparece porque a medida é feita em dois conjuntos. O número honesto do programa corrigido só viria de uma quarta leva de perguntas, ou, melhor, de pessoas reais.

Uma falha do próprio teste também entrou no registro: os agentes rodavam ao mesmo tempo e alguns gravaram um script auxiliar com o mesmo nome numa pasta compartilhada, então teclas de uma persona chegaram ao terminal de outra. Quem percebeu refez as tarefas num terminal isolado. Sessões separadas não bastaram; cada agente precisa de um terminal próprio e de arquivos com nome único.

**6. Versão web: mesma resposta, conferida na tela.** O assistente foi reescrito em TypeScript para rodar no celular, e uma reescrita pode divergir sem ninguém notar. Três verificações seguram isso:
- **Contrato com o terminal.** O núcleo Python gravou o que responde às 130 perguntas rotuladas das três rodadas, a 12 buscas de escola e à normalização dos nomes das 53.759 escolas (`data/regressao_web.json`). O teste da web exige o mesmo texto, palavra por palavra, e roda a cada envio ao GitHub. Bateu de primeira, porque as diferenças entre as linguagens foram previstas lendo o código; a principal é o arredondamento (o Python leva 12,5 para 12, o JavaScript para 13).
- **Revisão adversarial antes de publicar.** Um segundo modelo recebeu o site com a missão de quebrá-lo e achou cinco problemas que bloqueavam a publicação, todos corrigidos. O mais instrutivo: 171 fichas diziam "0,0 km, 1 min de ônibus" para escolas no mesmo endereço. Era um número tecnicamente certo e enganoso para quem lê, e virou "no mesmo lugar ou quase". A revisão também tentou, sem conseguir, injetar código pela busca e pelo endereço e misturar versões de dados guardadas no celular.
- **Captura de tela de cada mudança visível.** Os testes conferem o texto da resposta, e a tela pode errar mesmo com o texto certo. Duas falhas só apareceram na captura: um mapa sem estrada, porque o leitor seguia um formato provisório dos traçados, e um parágrafo que sumia depois de uma citação. A segunda ganhou um teste automático; a leitura dos traçados ainda é conferida só na tela.

**Próximo passo: validação com usuários reais.** O teste simulado acha defeitos grosseiros, mas não substitui pessoas. Um agente lê a tela inteira, não cansa, sabe usar terminal e escreve melhor que muita gente; o tempo que ele leva numa tarefa não diz nada sobre o tempo de uma pessoa. A validação seguinte deveria:
- ouvir quem vive o problema: famílias e professores de escolas do campo, conselheiros municipais, lideranças quilombolas e indígenas, e quem já atua nesses conflitos (Defensoria, Ministério Público, fóruns de educação do campo);
- usar o canal que essas pessoas usam, provavelmente o celular, e não o terminal;
- colher as perguntas reais delas para ampliar a base, medir o acerto nessas perguntas e cronometrar tarefas;
- seguir os cuidados de pesquisa com pessoas: participação voluntária, explicação do objetivo e nenhum dado que identifique quem participou.

## Controle de vieses

- **Viés de área.** O líder da equipe é médico. Para não puxar tudo para a saúde, a busca foi cega quanto à área, com teto de cerca de um terço de queixas de saúde por família de fonte.
- **Verificação.** Toda afirmação ficou marcada como verificada (fonte aberta e lida) ou não verificada. Os números que sustentam a escolha foram conferidos na fonte primária.
- **Viés de registro.** Séries oficiais podem crescer porque se passou a registrar mais, e não porque o problema piorou. Isso é levado em conta em qualquer modelo.
- **Média que esconde.** Indicadores nacionais bons podem ocultar a situação rural. Sempre que possível, olhamos o recorte territorial.
- **Autoavaliação.** Quem desenhou os critérios também pontuou os temas. Por isso a nota é tratada como insumo, e a revisão adversarial existe para contestá-la.

## Uso de IA

As buscas da Fase 1, a anamnese documental da Fase 3, a revisão adversarial, a conferência das fontes da base e o teste de usabilidade simulado foram executados por agentes de IA (modelos Claude, da Anthropic), com instruções e critérios definidos pela equipe. A pontuação, a conferência de fontes e as escolhas passam por revisão humana. O registro detalhado, com os erros da IA que a conferência pegou, está em [`docs/uso_ia.md`](uso_ia.md).

## Limitações

- Não houve ida a campo. A validação é documental, com no máximo uma conversa com quem decide.
- As cinco buscas da Fase 1 usaram o mesmo modelo e o mesmo roteiro. Um tema que aparece em todas indica relevância sob esse roteiro, sem equivaler a cinco observações independentes.
- Algumas bases oficiais bloqueiam acesso automatizado, e parte dos números veio de fontes secundárias. Esses números são conferidos na fonte primária antes de entrar no relatório.
- Os usuários do teste de usabilidade foram simulados por agentes de IA, com as limitações descritas acima. Em duas sessões da primeira leva e em três da terceira, um agente registrou entradas que não digitou, vindas de outro agente testando ao mesmo tempo; as tarefas afetadas foram refeitas em sessão isolada.
- As personas, o juiz e o programa foram feitos com a mesma família de modelos de IA. Isso pode deixar as perguntas mais parecidas com o vocabulário da base do que as de pessoas reais.
