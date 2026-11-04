# Metodologia: como escolhemos o problema

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

## Controle de vieses

- **Viés de área.** O líder da equipe é médico. Para não puxar tudo para a saúde, a busca foi cega quanto à área, com teto de cerca de um terço de queixas de saúde por família de fonte.
- **Verificação.** Toda afirmação ficou marcada como verificada (fonte aberta e lida) ou não verificada. Os números que sustentam a escolha foram conferidos na fonte primária.
- **Viés de registro.** Séries oficiais podem crescer porque se passou a registrar mais, e não porque o problema piorou. Isso é levado em conta em qualquer modelo.
- **Média que esconde.** Indicadores nacionais bons podem ocultar a situação rural. Sempre que possível, olhamos o recorte territorial.
- **Autoavaliação.** Quem desenhou os critérios também pontuou os temas. Por isso a nota é tratada como insumo, e a revisão adversarial existe para contestá-la.

## Uso de IA

As buscas da Fase 1, a anamnese documental da Fase 3 e a revisão adversarial foram executadas por agentes de IA (modelos Claude, da Anthropic), com instruções e critérios definidos pela equipe. A pontuação, a conferência de fontes e as escolhas passam por revisão humana. O registro detalhado do uso de IA acompanha a entrega.

## Limitações

- Não houve ida a campo. A validação é documental, com no máximo uma conversa com quem decide.
- As cinco buscas da Fase 1 usaram o mesmo modelo e o mesmo roteiro. Um tema que aparece em todas indica relevância sob esse roteiro, sem equivaler a cinco observações independentes.
- Algumas bases oficiais bloqueiam acesso automatizado, e parte dos números veio de fontes secundárias. Esses números são conferidos na fonte primária antes de entrar no relatório.
