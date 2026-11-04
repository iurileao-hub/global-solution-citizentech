"""Caminho mais curto (em tempo) entre duas escolas: Dijkstra com fila de prioridade.

A fila de prioridade (heapq) é a estrutura de dados que o problema exige:
a cada passo, expande o nó ainda não visitado com menor tempo acumulado.
Saída: km e minutos de ida e volta, como PISO. Se não houver caminho no grafo,
devolver None e avisar ("rota não encontrada"), nunca uma estimativa inventada.

Validação (docs/discussao/2026-11-04-passos-5-6.md): em Muniz Freire o TCE-ES
mediu 52 km/dia; o OSRM deu 25 a 37 km/dia. Comparar linha reta × OSRM ×
nossa rota × medição de campo, com erro absoluto e relativo.
"""
