"""Coordenadas das escolas.

Fonte principal: Ipea/geobr, schools_2023.gpkg (212 mil escolas, mesmo código
INEP em code_school; coluna empty_geo=1 quando não há coordenada).
https://www.ipea.gov.br/geobr/data_gpkg/schools/2023/schools_2023.gpkg
GeoPackage é SQLite: lê com sqlite3 da biblioteca padrão, sem geopandas.
A geometria é um blob "GeoPackage binary" (cabeçalho + WKB de ponto).

Cobertura de escolas rurais públicas em funcionamento com coordenada:
DF 96%, SP 96%, GO 92%, AM 61%, BA 60%.
Plano B: geocodificar pelo endereço (coluna address), marcando a precisão
na ficha. Nunca inventar coordenada.
"""
