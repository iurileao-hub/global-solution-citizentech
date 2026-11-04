"""Censo Escolar (INEP): matrícula, etapas, transporte, zona de residência e série histórica.

Fonte: microdados por escola (um CSV de ~218 MB por ano, sep=";", latin1),
https://download.inep.gov.br/dados_abertos/microdados_censo_escolar_<ano>.zip
(o servidor tem certificado SSL quebrado: baixar com verificação desligada é
aceitável por ser dado público; registrar o md5 que vem no zip).

Colunas usadas (conferidas no cabeçalho de 2024): CO_ENTIDADE, NO_ENTIDADE,
CO_MUNICIPIO, NO_MUNICIPIO, TP_LOCALIZACAO, TP_LOCALIZACAO_DIFERENCIADA,
TP_SITUACAO_FUNCIONAMENTO (1 ativa, 2 paralisada = JÁ fechada, 3 extinta),
QT_MAT_* por etapa, QT_MAT_ZR_RUR/URB, QT_TRANSP_PUBLICO(_RESP_EST/_MUN),
QT_SALAS_UTILIZADAS, IN_AGUA_POTAVEL, IN_ENERGIA_*, IN_INTERNET.

Cuidado: o layout muda entre anos. Harmonizar 2019-2025 aqui, com teste.
Pré-processar para um arquivo leve (só colunas usadas, só escolas públicas)
em dados/processados/, que também servirá à v2.
"""
