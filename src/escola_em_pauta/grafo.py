"""Malha viária do OpenStreetMap como grafo.

Fonte: Overpass API, vias highway in (trunk, primary, secondary, tertiary,
unclassified, residential, service, track, road) num retângulo ao redor da
escola (v1: por território; v2: raio de ~30 km sob demanda, com cache).
Em Muniz Freire/ES: 4.411 vias, ~70% com tag surface (compacted, unpaved...).

Estrutura: lista de adjacência, dict[no_id, list[tuple[vizinho_id, minutos]]].
O custo de cada aresta é TEMPO, com velocidade por tipo de via e superfície
(estrada de terra mais lenta). Essa é a correção que o roteador público (OSRM)
não faz, e o motivo de calcularmos a rota nós mesmos.
"""
