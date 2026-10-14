# Revisão estrutural dos JSON PT-BR

Resultado de `python3 scripts/audit_catalogs.py`, validado no GitHub Actions em 13/10/2026, após a normalização da identidade de cada módulo.

## Totais

| Métrica | Valor |
|---|---:|
| Arquivos JSON do idioma | 21 |
| Entradas de tradução `translations` | 3.677 |
| `keys` identificadas | 0 |
| `patterns` regex | 5 |
| Nomes protegidos | 1.759 |
| Textos originais distintos | 3.677 |
| Traduções conflitantes entre arquivos | 0 |
| Inconsistências detectadas de placeholders `{0}`, `{1}` etc. | 0 |
| Arquivos estruturalmente inválidos / identidade duplicada | 0 |
| Avisos de catálogo sem traduções | 2 |

## Origem, correções e pendências

O arquivo **`SectAdmin.json`** passou a conter as 147 entradas anteriormente importadas de `SchoolAdmin`, correspondente ao mod **SectAdmin** da Steam Workshop `2814722600`. A fonte separada `SectAdmin_PTBR.txt` não continha pares úteis, apenas comentários.

Os catálogos **`SectQOL.json`** e **`Workshop_2990310797.json`** ainda estão vazios. O último corresponde à antiga tradução PT-BR da Workshop; isso **não significa** que o plugin XUnity faça parte do nosso mod. O registro está vazio e é mantido apenas como origem histórica.

Para os demais mods, os identificadores `steam:ID` foram retirados dos caminhos reais `Text/mods/Workshop_ID...` do arquivo de importação. Alguns nomes legíveis foram confirmados nas páginas do Workshop. Quando não há nome comprovado, usamos `Workshop ID` de forma provisória. Campos `sourceAlias` apenas registram a etiqueta da fonte; não equivalem à identificação de uma DLL instalada.

Todos os catálogos passam a ter `module.id`, `module.kind` e `module.name`. O carregador usa esses campos, não o nome do arquivo, para classificar a origem e definir a prioridade. A precedência de `game`, `mod` e `fallback` está coberta por teste que renomeia arbitrariamente os arquivos antes de carregá-los.

## Limitações desta revisão

Esta foi uma **revisão estrutural automatizada**, não a leitura e correção linguística manual de todas as 3.677 traduções. Regras regex, trechos de marcação do Unity, semântica dos diálogos e escolhas terminológicas ainda merecem análise contextual no jogo. A cobertura de `TMP_Text` em tempo de execução e a tradução instantânea sem reiniciar são assuntos separados.

O relatório completo e atualizado, incluindo todos os módulos e avisos, fica no artefato do GitHub Actions:
`dist/TalesOfMortal_i18N/catalog-audit.json`.
