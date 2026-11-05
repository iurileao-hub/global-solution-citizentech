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

**5. Terceira rodada.** Para medir o programa corrigido com honestidade, uma nova leva de personas, diferentes das primeiras, escreve perguntas que nem a equipe nem o programa viram. *(Em andamento; o resultado entra aqui.)*

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

As buscas da Fase 1, a anamnese documental da Fase 3, a revisão adversarial, a conferência das fontes da base e o teste de usabilidade simulado foram executados por agentes de IA (modelos Claude, da Anthropic), com instruções e critérios definidos pela equipe. A pontuação, a conferência de fontes e as escolhas passam por revisão humana. O registro detalhado do uso de IA acompanha a entrega.

## Limitações

- Não houve ida a campo. A validação é documental, com no máximo uma conversa com quem decide.
- As cinco buscas da Fase 1 usaram o mesmo modelo e o mesmo roteiro. Um tema que aparece em todas indica relevância sob esse roteiro, sem equivaler a cinco observações independentes.
- Algumas bases oficiais bloqueiam acesso automatizado, e parte dos números veio de fontes secundárias. Esses números são conferidos na fonte primária antes de entrar no relatório.
- Os usuários do teste de usabilidade foram simulados por agentes de IA, com as limitações descritas acima. Em duas sessões, um agente registrou entradas que não digitou, provavelmente de outro agente testando ao mesmo tempo; as tarefas afetadas foram refeitas em sessão isolada.
- As personas, o juiz e o programa foram feitos com a mesma família de modelos de IA. Isso pode deixar as perguntas mais parecidas com o vocabulário da base do que as de pessoas reais.
