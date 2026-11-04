"""Escolas receptoras possíveis para os alunos de uma escola.

Critério: escolas públicas ativas que oferecem as MESMAS etapas, as k mais
próximas (pré-filtro em linha reta, depois rota real). Marcar se a receptora é
rural ou urbana (o TCE-ES tratou receptora urbana como irregularidade) e a
ocupação estimada (proxy: matrícula / salas utilizadas, rotulado como estimativa).
Lembrar a Res. CNE/CEB 2/2008, art. 3º: pré-escola e anos iniciais devem ser
oferecidos na própria comunidade.
"""
