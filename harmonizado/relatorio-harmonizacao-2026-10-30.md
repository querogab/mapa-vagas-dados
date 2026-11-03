# Relatório da harmonização de vagas

> Processado em 2026-10-30, sem chamadas de rede. Os snapshots de origem não foram alterados.

## Contrato do conjunto

- Uma linha por `fonte` + `id_origem`, sem deduplicação semântica entre plataformas.
- Inclusão pelo título em taxonomia comum; anúncios `fora_do_escopo` ficam registrados no CSV com essa marca e não entram nos agregados substantivos.
- Competências são menções em texto disponível, não requisitos obrigatórios. Texto truncado e ausência de descrição são atributos explícitos.
- Gupy conserva tipos efetiva/PJ/temporária e janela de 90 dias antes da coleta (28/06/26 a 26/09/26): são 1.022 registros antes da taxonomia comum. O recorte histórico de 752 aplicava regras anteriores de família/processos e é preservado, não substituído.
- LinkedIn usa o país da busca, não confirmação de elegibilidade ou local de trabalho. RemoteOK conserva país inferido pelo coletor e canal remoto, sem equivaler isso a modalidade/contrato da vaga.

## Contagens

| Fonte | Linhas | Com descrição | Sem descrição | Fora do escopo |
|---|---:|---:|---:|---:|
| gupy | 1022 | 1022 | 0 | 560 |
| linkedin | 1318 | 249 | 1069 | 109 |
| remoteok | 482 | 482 | 0 | 434 |

## Famílias incluídas

| Fonte | Família | Linhas |
|---|---|---:|
| gupy | analise_bi | 178 |
| gupy | ciencia_dados | 43 |
| gupy | engenharia_dados | 76 |
| gupy | governanca_qualidade | 17 |
| gupy | ia | 64 |
| gupy | pesquisa_inteligencia | 84 |
| linkedin | analise_bi | 389 |
| linkedin | ciencia_dados | 405 |
| linkedin | engenharia_dados | 284 |
| linkedin | governanca_qualidade | 26 |
| linkedin | ia | 82 |
| linkedin | pesquisa_inteligencia | 23 |
| remoteok | analise_bi | 22 |
| remoteok | ciencia_dados | 10 |
| remoteok | engenharia_dados | 3 |
| remoteok | governanca_qualidade | 2 |
| remoteok | ia | 11 |

## Senioridade derivada das linhas incluídas

| Fonte | Nível | Linhas |
|---|---|---:|
| gupy | gestao | 8 |
| gupy | junior | 32 |
| gupy | pleno | 90 |
| gupy | senior | 185 |
| linkedin | gestao | 9 |
| linkedin | junior | 18 |
| linkedin | pleno | 45 |
| linkedin | senior | 548 |
| remoteok | gestao | 2 |
| remoteok | junior | 8 |
| remoteok | senior | 7 |

## Artefatos analíticos

A amostra estratificada foi concluída em `amostra-validacao-2026-10-30.md`. Tabelas e SVGs reprodutíveis estão em `figuras/`; comparações de competências usam apenas linhas incluídas com descrição disponível e expõem esse denominador.
