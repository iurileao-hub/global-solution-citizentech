# Teste de usabilidade r3: Dra. Fernanda (advogada do sindicato dos trabalhadores rurais, RS)

Sessão tmux: `u3-advogada`. Data: 05/11/2026.

## Tarefas

| # | Tarefa | Concluiu | Entradas digitadas | Onde travou | O que encontrou |
|---|--------|----------|--------------------|-------------|-----------------|
| 1 | O que a lei exige antes de fechar | sim | 2 (`1`, `1`) + D6 por curiosidade | Não travou. A resposta D1 apareceu depois de uma entrada que **não fui eu que digitei** (ver observações) | D1: manifestação do Conselho, que considera justificativa da Secretaria, diagnóstico do impacto e manifestação da comunidade. Fonte: LDB art. 28, parágrafo único, incluído pela Lei 12.960/2014 |
| 2 | EMEF Durval Máximo, Muniz Freire/ES | sim | 3 (Enter, `3`, `EMEF Durval Máximo`) | Entradas alheias bagunçaram o fluxo (o meu `3` foi lido como nome de escola) | **56 alunos em 2025** (pré-escola 18, anos iniciais 18, anos finais 20); INEP 32049501; 39 usam transporte; 56 moram na zona rural |
| 3 | E.M. São José, Carlos Chagas/MG | sim | 1 (`Escola Municipal São José Carlos Chagas`) | Não travou | INEP 31151220, rural, em comunidade quilombola; 82 alunos em 2025; série 2019 a 2025 |
| 4 | Como pedir os números à prefeitura | sim | 1 (`C1`) | Não travou | LAI: identificação sem motivo, SIC, 20 dias prorrogáveis para 30, recurso em 10 dias (arts. 10, 11 e 15) |
| 5 | Pergunta que o programa não sabe | sim | 1 (mandado de segurança e prazo decadencial) | n/a | "Não encontrei, na base deste assistente, uma orientação confiável para essa pergunta. Prefiro dizer isso a inventar uma resposta." e lista os 4 assuntos |
| 6 | Quantas escolas do campo fecharam no RS | parcial (na 2ª tentativa) | 2 | A 1ª pergunta ("...no Rio Grande do Sul?") foi entendida como **o município de Rio Grande/RS**: 22 em atividade, 5 extintas 2019-2025, 1 paralisada | Com "no estado do RS": **1.677 em atividade em 2025; 669 extintas de 2019 a 2025; 643 paralisadas em 2025, das quais 458 há 5 anos ou mais** |

## Perguntas da Parte 1 testadas

| Pergunta | Para onde foi | Serviu? |
|----------|---------------|---------|
| "A manifestação do órgão normativo (Conselho Municipal ou Estadual de Educação) é vinculante ou meramente opinativa?" | C3 (papel do Conselho, exemplo de Santa Cruz do Sul) | **Parcial.** C3 não responde. A resposta certa estava no C6, oferecido como link: "A lei nacional não diz se um parecer contrário impede o fechamento: isso depende das regras do seu estado ou município" (com o exemplo do PR). Bom conteúdo, roteamento errado |
| "A Resolução CNE/CEB 2/2008 continua em vigor?" (e, reformulada, "Resolução 2/2008 do CNE ainda vale?") | "Não encontrei..." nas duas | **Não.** E o próprio programa cita essa resolução no D3, então a base sabe dela |
| "Existe jurisprudência do TJRS ou do STJ anulando fechamento de escola do campo por falta de consulta à comunidade?" | "Não encontrei..." | **Não.** O C5 (caso de Muniz Freire) chega perto, mas só achei navegando a partir do C4 |

Também testei, como extra: "O sindicato dos trabalhadores rurais tem legitimidade para propor ação civil pública contra o fechamento?" Resposta: "Não encontrei...". O C4 só cita MP e Defensoria.

## Notas (voz da Dra. Fernanda)

- **(a) Foi fácil achar o que procurava: 3/5.** O menu por assunto é rápido e os códigos ajudam. Mas quando eu pergunto do meu jeito, com termo técnico, ele erra o destino ou diz que não sabe, mesmo quando sabe (Resolução 2/2008, vinculação do parecer). E "Rio Grande do Sul" virar o município de Rio Grande é o tipo de erro que me faria levar número errado para uma assembleia.
- **(b) Entendi as respostas: 5/5.** Texto claro, com artigo e link do Planalto. Para as famílias, o tom está certo.
- **(c) Confiaria para levar a uma reunião, conferindo com o órgão oficial: 3/5.** Indicaria às famílias para a parte de LAI e para a ficha da escola. Para mim, como advogada, é ponto de partida: algumas frases afirmam mais do que a norma diz (listo abaixo) e falta a questão de qual Conselho é competente quando o município não tem sistema próprio de ensino, que é a situação de muitos municípios gaúchos.

## O que eu mudaria (voz da Dra. Fernanda)

1. Que "Rio Grande do Sul", "RS" e "estado do RS" deem sempre o estado. Quando o nome puder ser estado e município, perguntar qual.
2. Que perguntas com termo técnico ("vinculante", "Resolução 2/2008", "legitimidade", "jurisprudência") caiam no assunto que já existe (C6, D3, C4, C5) em vez de "não encontrei".
3. Dizer, no C6/D1, que o órgão normativo é o Conselho Municipal só se o município instituiu sistema próprio de ensino; senão é o Conselho Estadual.
4. No C4, lembrar que associação e sindicato também podem propor ação civil pública (Lei 7.347/1985, art. 5º, V), observados os requisitos. É exatamente o meu caso.
5. No C5, trocar o "Sim" seco por "provisoriamente sim": liminar e cautelar não são decisão final, e informar o número do processo judicial do MP, não só o do TCE.
6. Dizer explicitamente se a Resolução CNE/CEB 2/2008 está vigente e em que data isso foi conferido, como já faz com o PL.

## Observações do avaliador (fora da persona)

### Entradas que NÃO fui eu que digitei (contaminação da sessão)

Sim, entrou muita coisa. No histórico da `u3-advogada` apareceram estas entradas que eu não enviei:
- `o que a lei exige antes de fechar uma escola do campo?` (no prompt de código, logo depois do meu `1`)
- `2`, depois `O QUE PRECISA PRA FECHAR ESCOLA DA ROÇA`
- um Enter avulso, `3`, `DURVAL MAXIMO MUNIZ FREIRE`
- mais tarde, um Enter avulso, `3`, `DURVAL MAXIMO`, `SAO JOSE CARLOS CHAGAS`

**Causa provável (falha minha, autodeclarada):** criei um script auxiliar com nome genérico, `scratchpad/s.sh`, que mandava teclas para `-t u3-advogada`. O scratchpad é **compartilhado** entre as sessões de teste paralelas. Outro testador (pelo estilo em CAIXA ALTA, provavelmente a persona motorista ou a avó) usou ou sobrescreveu um arquivo de mesmo nome, e o meu `s.sh` sumiu no meio do teste. Consequência possível no outro sentido: uma chamada minha (`C4`, perto do fim) pode ter rodado a versão do outro testador e ido parar na sessão DELE. Não conferi, porque a regra proíbe tocar sessão alheia. Recomendação para a próxima rodada: helper com nome único por persona (ex.: `u3_<id>_envia.sh`) ou socket próprio `tmux -L <id>`, como a radialista acabou fazendo. Depois disso troquei para `u3_advogada_envia.sh` e não houve mais contaminação.

Isso não afeta os números lidos: 56 (Durval Máximo), 82 (São José) e os do RS saíram de entradas minhas e conferem com as repetições.

### Defeitos concretos

1. **Estado lido como município.** "Quantas escolas do campo fecharam no Rio Grande do Sul?" respondeu "Escolas públicas rurais em Rio Grande/RS, pelo Censo Escolar: em atividade em 2025: 22". O usuário não percebe a troca se não ler com atenção. É o defeito mais grave da sessão.
2. **"em RS"**: "Escolas públicas rurais em RS, pelo Censo Escolar" (o certo é "no RS").
3. **Roteamento perde respostas que existem:**
   - "é vinculante ou meramente opinativa?" foi para C3, mas quem responde é o C6.
   - "A Resolução CNE/CEB 2/2008 continua em vigor?" e "Resolução 2/2008 do CNE ainda vale?" deram "Não encontrei", embora o D3 cite "Resolução CNE/CEB nº 2/2008, arts. 3º e 4º".
   - "jurisprudência ... anulando fechamento" deu "Não encontrei", mas o C5 é exatamente um caso.
4. Mandado de segurança: o "Não encontrei" está correto e honesto. Só que não aponta o C4/C5, que seriam o vizinho útil.

### Afirmações que, para uma advogada, exigiriam ressalva

1. **C6: "o municipal, se a escola é do município, ou o estadual, se é do estado."** Isso só vale se o município tiver instituído sistema próprio de ensino. Se não tiver, a rede municipal integra o sistema estadual e o órgão normativo é o Conselho Estadual (LDB, arts. 11, parágrafo único, e 18). No RS isso é frequente. D1 tem o mesmo ponto: "o órgão que aprova as regras do ensino na cidade ou no estado".
2. **C6: "a opinião da comunidade escolar, registrada em ata"** e "confira se o pedido ... chegou com os três documentos e no prazo". A LDB não exige ata nem fixa prazo. Ata e prazo vêm de normas locais (como a de Santa Cruz do Sul, no C3). Do jeito que está, parece exigência nacional.
3. **C5: "Deu certo recorrer? Sim. ... A medida foi barrada por liminar em ação do Ministério Público e por decisão cautelar do Tribunal".** Liminar e cautelar são provisórias. O "Sim" sem ressalva promete mais do que o caso mostra. A ação judicial do MP aparece sem número e sem juízo, e a única fonte é a decisão do TCE-ES (republicada pelo MPC). O "Confirme: É um caso; cada situação é julgada pelos seus fatos" ajuda, mas não resolve o caráter provisório.
4. **D4: "Sim. O Estatuto da Criança e do Adolescente garante o acesso à escola pública e gratuita próxima de casa".** O texto do art. 53, V, está certo, mas o "Sim" seco pode ser lido como direito de manter aquela escola específica aberta, o que o dispositivo não garante sozinho. Vale um "isso não impede, sozinho, o fechamento, mas é argumento".
5. **D6: "Se virar lei, ele revoga o parágrafo único do art. 28 da LDB ... e põe regras mais detalhadas no lugar."** Isso descreve a redação aprovada pelo Senado, que a Câmara pode alterar. Falta "na redação aprovada pelo Senado". O "aprovado no Senado em maio de 2026" e "na Câmara desde 21/05/2026" não pude conferir como usuária. A data de conferência está informada, e isso é bom.
6. **D3: "A educação infantil deve ser oferecida sempre na própria comunidade rural."** Fiel ao art. 3º da Res. CNE/CEB 2/2008, mas sem dizer que é norma infralegal do CNE e sem data de vigência conferida. É justamente o que a pergunta 3 da Parte 1 queria saber.
7. **F5: "extintas (encerradas de vez, por ato da Secretaria)".** O Censo registra a situação "extinta" informada pela rede. Afirmar que houve "ato da Secretaria" é inferência, e um advogado usaria isso para pedir o ato. Sugiro "que a rede informou como extintas".
8. **C4** omite a legitimidade de associações e sindicatos para a ação civil pública (Lei 7.347/1985, art. 5º, V). Para o público-alvo do sindicato, é omissão relevante.

O C1 (LAI) e o D1 conferem com o texto legal: 20 + 10 dias, recurso em 10 dias, art. 28 parágrafo único com os três elementos.
