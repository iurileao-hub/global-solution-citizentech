# Uso de inteligência artificial

## O assistente não usa modelo de linguagem

O Assistente Escola em Pauta (`python src/sistema.py`) responde só com regras explícitas e com o texto da base de orientações. Nenhuma resposta é gerada por modelo de linguagem no momento da consulta. Foi uma escolha: o enunciado pede respostas com fonte verificável e sem invenção, e regras podem ser testadas uma a uma.

## Onde a IA foi usada no desenvolvimento

O projeto foi desenvolvido com o **Claude Code** (Anthropic, modelos da família Claude), sob direção e revisão humanas. Usos:

| Etapa | Uso da IA | O que ficou com a equipe |
|---|---|---|
| Escolha do problema | levantamento de queixas em 5 famílias de fontes, agrupamento e pontuação (ver `docs/metodologia.md`) | a escolha entre os finalistas, o recorte e o teto de esforço |
| Base de orientações | rascunho das orientações e verificação de cada norma por um agente que abriu o texto oficial e copiou o trecho literal | aprovação dos temas e dos registros; inclusão da alimentação escolar; decisão de manter os casos indígena/quilombola e o caso de Muniz Freire |
| Código | escrita do código, dos testes e dos scripts | decisões de arquitetura (camadas, pré-cálculo, critério de transporte fluvial) |
| Prompts | os dois modelos de instrução de resposta (A e B) foram escritos como especificação e comparados nas perguntas de teste | escolha do modelo padrão |
| Testes | planejamento das perguntas de teste e dos indicadores | o segundo conjunto de perguntas e o teste de usabilidade, feitos por pessoas que não viram a base |
| Textos | revisão de linguagem do README | revisão final |

## Validação crítica: o que a conferência pegou

Toda afirmação jurídica da base foi conferida no texto oficial, com o trecho literal registrado (`docs/pesquisa/base-fontes-verificadas.md`, mantido fora do repositório público por ser material de trabalho). A conferência mudou a base em pontos que um rascunho de memória teria errado:

- **Alimentação escolar:** o mínimo de compra da agricultura familiar é 45% desde 01/01/2026 (Lei 15.226/2025). A própria página do FNDE ainda dizia 30%.
- **Nucleação dos anos iniciais:** a Resolução CNE/CEB 2/2008 admite, em caráter excepcional, nucleação dentro do campo. O rascunho dizia que a regra era absoluta.
- **Escola "paralisada" no Censo:** o INEP define como atividades temporariamente suspensas, sem extinção formal. Uma leitura anterior, também apoiada por IA, tinha concluído "escola já fechada"; a correção veio da leitura do caderno de conceitos do INEP.
- **Lei de Acesso à Informação:** o pedido exige identificação de quem pede, mas não exige justificativa. O rascunho omitia a identificação, o que importa para quem teme retaliação.
- **PL 3.091/2024:** os prazos de 1 ano e de 90 dias tratam de coisas diferentes, e o projeto não é lei (está parado na Câmara desde maio de 2026).

Erros da IA no código, achados por teste ou por uso:

- Uma afirmação técnica sobre o roteador OSRM ("ignora o tipo de superfície") estava errada e foi corrigida depois de lido o perfil do roteador.
- A busca de escolas descartava "São" como se fosse o verbo "são", e "Escola Municipal São José" devolvia escolas sem "São" no nome. O teste automático passava, porque só conferia que havia uma lista; o teste foi reforçado para exigir a escola certa.
- Um commit entrou com um teste falhando, porque o resultado do teste não foi conferido de fato; o processo passou a exigir que a suíte passe antes do commit.

## O que a IA não decidiu

O problema, o público, os temas, o que entra e o que sai da base, o critério de transporte fluvial, a participação na competição e o uso da ferramenta fora do curso foram decisões da equipe. A IA propôs; as propostas foram aceitas, mudadas ou recusadas por pessoas, e várias recomendações foram recusadas (por exemplo, a de limitar a primeira versão à consulta sem rotas).
