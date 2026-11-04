# Escola em Pauta

**Antes de decidir: o impacto de fechar uma escola do campo, medido antes da decisão.**

Global Solution FIAP 2026, tema CitizenTech.

## O problema

A LDB (art. 28, parágrafo único, incluído pela Lei 12.960/2014) exige que o fechamento de escolas do campo, indígenas e quilombolas seja precedido de um **diagnóstico do impacto** e da **manifestação da comunidade escolar**. A lei não define como esse diagnóstico deve ser feito. Na prática, os números (quantas crianças, quanta estrada, para qual escola) costumam aparecer só depois da decisão, no recurso ao Ministério Público ou na auditoria do Tribunal de Contas.

O problema foi escolhido por um processo explícito, antes de qualquer decisão de tecnologia: ver [`docs/metodologia.md`](docs/metodologia.md).

## A solução

Uma **ficha de duas páginas por escola**, gerada só com dados públicos, para a comunidade e o Conselho de Educação lerem o mesmo número antes da assembleia:

- **Frente:** quantas crianças estudam ali, por etapa e ano escolar; quantas usam transporte; a série da matrícula de 2019 a 2025; as escolas que poderiam receber os alunos (rurais ou urbanas, do mesmo município ou não, com as etapas que cada uma oferece); e a estrada por dia de escola a escola, sempre como **piso** ("pelo menos").
- **Verso:** o que nenhum dado mede (a função social da escola), com linhas para a comunidade escrever na assembleia, e a lista do que a lei pede, marcando o que a ficha já cobre e o que depende de pessoas.

A ficha informa. Quem decide é a comunidade escolar e o Conselho.

## Como funciona

```
Censo Escolar (INEP, 2019-2025) ─┐
Escolas geolocalizadas (Ipea)  ──┼─► diagnosticar(codigo_inep) ─► ficha HTML (A4, imprimível)
OpenStreetMap (Geofabrik)      ──┘                              └► site estático com busca
```

| Módulo | O que faz |
|---|---|
| `censo.py` | Lê os zips do INEP sem descompactar e harmoniza a mudança de layout de 2025 (escola, matrícula e docentes em tabelas separadas) |
| `geo.py` | Lê o GeoPackage do Ipea com `sqlite3` e decodifica o ponto (WKB) à mão |
| `grafo.py` | Transforma as vias do OSM em grafo, com custo em minutos de ônibus por tipo de via e superfície |
| `osm_local.py` | Extrai as vias de várias áreas de um recorte regional do OSM (PBF) numa passada só; o Overpass fica como alternativa |
| `rota.py` | Dijkstra com fila de prioridade (`heapq`) |
| `receptoras.py` | Pré-filtro em linha reta e rota real só para as candidatas |
| `tendencia.py` | Mínimos quadrados e backtest contra uma linha de base |
| `checklist.py` | LDB, Decreto 7.352/2010, Res. CNE/CEB 2/2008, PL 3.091/2024 e o modelo de Santa Cruz do Sul/RS |
| `ficha.py`, `site.py` | Texto da ficha (testável), templates Jinja2 e gerador do site |

### Estruturas de dados, escolhidas pelo problema

- **Grafo em lista de adjacência.** A malha viária é um grafo esparso: em Muniz Freire são cerca de 127 mil nós e 256 mil arestas, perto de 2 por nó. Uma matriz de adjacência teria 16 bilhões de células, quase todas vazias.
- **Fila de prioridade (heap binário).** O Dijkstra precisa, a cada passo, do nó aberto com menor tempo acumulado. No heap isso custa O(log n), contra O(n) numa lista. Usamos "remoção preguiçosa", porque o `heapq` não diminui prioridade de um item já na fila.
- **Um Dijkstra para muitos destinos, e o grafo reverso.** O algoritmo calcula o menor caminho para todos os nós que fecha. Basta seguir até fechar todas as candidatas. A volta (de cada candidata até a escola) sai de um único Dijkstra no grafo com as arestas invertidas. São 2 execuções por escola no lugar de 24; um teste garante que o resultado é igual ao do cálculo par a par.
- **Dicionário pelo código INEP**, a chave que une as três bases.

## Resultados

### 1. O cálculo fica abaixo do real, e por isso é piso

Em Muniz Freire (ES), o Tribunal de Contas mediu **52 km por dia** de transporte para os alunos da EMEF Durval Máximo (Decisão 02423/2025-2). Comparação com as escolas urbanas candidatas, de escola a escola, ida e volta:

| Escola receptora | Linha reta (km) | OSRM, carro (km) | Nossa rota, ônibus (km) |
|---|---|---|---|
| CEEFMTI Bráulio Franco | 18 | 28 | 32 |
| EMEF Lia Therezinha Mercon Rocha | 19 | 30 | 32 |
| EMEF Maria Áurea Barroso | 16 | 29 | 29 |
| EMEF Leovegília Emiliano da Silva | 21 | 37 | 45 |
| EEEFM Arquimimo Mattos | 18 | 25 | 25 |
| EMEF Paulo Fábio Sartore | 20 | 29 | 29 |

Erro relativo contra os 52 km: linha reta de −69% a −60%; OSRM de −52% a −28%; nossa rota de −52% a −14%. **Todos os métodos subestimam**, porque o ônibus de verdade passa de casa em casa. A diferença entre o OSRM e a nossa rota não mostra que uma seja mais precisa; com um caso só, o resultado vale como ordem de grandeza. Reproduzir: `escola-em-pauta validar`.

Na região, **mais de 80% dos quilômetros de estrada mapeados são de chão**.

### 2. Projetar a matrícula pela tendência erra mais do que não projetar

Backtest: ajuste com 2019 a 2022 e previsão de 2023 a 2025, comparado com a linha de base "a matrícula repete o último ano conhecido".

| Escolas rurais ativas | Escolas | Erro médio da reta (alunos) | Erro médio da linha de base | Reta vence em |
|---|---|---|---|---|
| DF | 81 | 32,0 | 26,3 | 42% das escolas |
| SP | 1.095 | 24,4 | 17,7 | 31% |
| ES | 810 | 14,3 | 10,3 | 29% |

Em escola pequena, uma família que se muda pesa 10% da matrícula, e a reta projeta esse ruído. Por isso a ficha **descreve** a série (estável, em queda ou em alta) e não projeta. O resultado também serve à comunidade: uma justificativa de fechamento baseada em "a matrícula vai continuar caindo" usa um método que, medido em quase 2 mil escolas, erra mais do que supor estabilidade.

### 3. O caso real contradiz a intuição

A escola mais próxima da Durval Máximo é **rural e fica em outro município** (EMEF Alto Monforte, Conceição do Castelo, 18 km por dia, com pré-escola e anos iniciais). Uma lista feita só com as escolas urbanas do próprio município não a encontraria.

## Como rodar

Requer Python 3.12 ou mais recente.

```bash
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Dados brutos (públicos) em dados/brutos/:
#   microdados_censo_escolar_<ano>.zip, de 2019 a 2025 (INEP; o de 2025 se chama ..._2025_.zip no servidor)
#   schools_2023.gpkg (Ipea/geobr)
escola-em-pauta dados                  # gera dados/processados/*.parquet
escola-em-pauta ficha 32049501         # ficha de uma escola qualquer do Brasil
escola-em-pauta site                   # site dos territórios de demonstração
escola-em-pauta validar                # tabela de erro de Muniz Freire
```

Malha viária: para o site, ponha em `dados/brutos/osm/` os recortes regionais da Geofabrik (`centro-oeste-latest.osm.pbf`, `sudeste-latest.osm.pbf`); as vias de cada área são extraídas localmente numa passada só. Sem o recorte da região, a malha vem do Overpass, sob demanda, com cache. Publicar o site: `scripts/publicar_pages.sh`.

## Limitações

- **O número é um piso.** O cálculo não conhece onde cada criança mora (dado pessoal, fora de propósito) nem a rota do ônibus (não há base pública).
- **Velocidades de ônibus são parâmetros declarados**, sem medição própria. A única medição de tempo disponível (Pedras Altas/RS, 1h a 1h30 por sentido) depende de escolas sem coordenada na base do Ipea.
- **Escolas sem coordenada** (cerca de 40% das rurais no Norte e no Nordeste) aparecem com aviso e sem distância.
- **Vagas nas receptoras não são publicadas.** Alunos por sala é uma estimativa que soma os turnos.
- **Escola do campo em área urbana**: o Decreto 7.352/2010 define população do campo pelo trabalho no meio rural. Morar na zona rural é usado como indício.

## Fontes e licenças

- Censo Escolar da Educação Básica, INEP (microdados por escola, 2019 a 2025).
- Escolas geolocalizadas, Ipea (pacote `geobr`, base de 2023).
- © colaboradores do OpenStreetMap, dados sob licença ODbL.
- Normas conferidas no texto oficial: LDB art. 28; Decreto 7.352/2010, art. 1º; Res. CNE/CEB 2/2008, art. 3º.

## Uso de IA

O processo de escolha do problema e o uso de IA estão descritos em [`docs/metodologia.md`](docs/metodologia.md). O código foi escrito com assistência de modelos Claude (Anthropic), com revisão e decisões humanas.
