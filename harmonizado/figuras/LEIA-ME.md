# Tabelas e figuras do Mapa de vagas

Geradas em 2026-10-30 por `gerar_figuras.py`, a partir de `vagas-harmonizadas-2026-10-30.csv`.

## Artefatos

- `01-cobertura-e-selecao.svg`: cobertura, inclusão e descrição por fonte.
- `02-composicao-por-familia.svg`: composição percentual somente das vagas incluídas.
- `03-mencoes-de-competencias.svg`: menções literais somente entre vagas incluídas com descrição disponível.
- `04-sql-python-por-familia.svg`: SQL e Python por família em Gupy e LinkedIn, com o agregado em cima; família sem descrição aparece como tal, não como zero.
- `tabela-*.csv`: valores usados nos SVGs.

## Limites

- Fontes não são amostras comparáveis do mercado e não houve deduplicação semântica entre elas.
- LinkedIn não tem descrição em parte relevante das vagas; nenhuma célula sem texto deve ser lida como zero competência.
- RemoteOK identifica um canal remoto, não contrato, país confirmado ou elegibilidade global.
- As famílias decorrem de regras de título; competências são menções literais no texto, não requisitos confirmados.
