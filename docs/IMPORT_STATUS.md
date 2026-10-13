# Estado da importação do acervo PT-BR

Análise do ZIP de traduções fornecido em 13/10/2026:

| Métrica | Quantidade |
| --- | ---: |
| Arquivos TXT no acervo | 23 |
| Mods distintos da Steam Workshop | 17 |
| Entradas únicas por arquivo original | 34.260 |
| Traduções efetivas convertidas | 3.682 |
| Textos e aliases protegidos | 1.759 |
| Regras dinâmicas (expressões regulares) | 5 |
| Entradas `original=original` não incluídas no runtime | 28.820 |
| Conflitos entre camadas de tradução | 0 |

## Estrutura da importação

O conversor `scripts/import_translation_zip.py` escreve o resultado em `mod/i18n/pt-BR/`:
- `game.json`: traduções de `PTBR_Revisado.txt`;
- `SchoolAdmin.json`, `Cave.json`, `FixData.json` etc.: pacotes por mod;
- `Workshop_<id>.json`: pacote por Workshop quando não há nome estável;
- `zzz-auto.json`: traduções automáticas, prioridade mínima;
- `protected-names.json`: lista derivada do antigo `_Substitutions.txt`.

Os cinco padrões de regex são mantidos no campo `patterns` do JSON do FixData.
O `SectAdmin_PTBR.txt` do ZIP estava vazio, por isso não gerou traduções adicionais.

**Situação no GitHub:** o código do importador e o suporte C# para os padrões
foram enviados à branch `Dev`. O acervo completo gerado a partir do ZIP
permanece como pacote de download entregue na conversa de origem e **ainda
precisa ser adicionado a esta branch**. Não confundir o importador publicado
com a importação integral publicada.

## Importar na branch Dev

```bash
python3 scripts/import_translation_zip.py /caminho/Text.zip
git add mod/i18n/pt-BR/
git commit -m "feat: importar acervo completo de traducoes pt-BR"
git push origin Dev
```

A implementação do runtime continua sem validação contra as DLLs específicas
da instalação do jogo. Não publicar release binária antes dessa validação.
