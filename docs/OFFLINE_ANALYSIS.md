# Auditoria do offline.json recebido em 13/10/2026

A entrada fornecida tinha **34 MB** e foi gerada com a primeira versão do scanner offline.

## Resumo do conteúdo

| Item | Quantidade |
| --- | ---: |
| Arquivos analisados | 855 |
| Arquivos ignorados | 50 |
| Ocorrências de strings | 1.733.573 |
| Strings únicas na extração | 83.584 |
| Catálogos de origem | 18 |
| Entradas marcadas como jogo | 83.206 |
| Linhas identificáveis de localização (SectAdmin) | 50 |
| Campos de configuração em chinês identificados (mod 2864011606) | 6 |

**A classificação de 83.206 strings como `game:tale-of-immortal` não significa que sejam textos de interface do jogo.** A maior parte veio de `Mod/modFQA/配置修改教程`, uma pasta de exemplos e documentação do criador de mods. Também havia arquivos `guigubahuang_Data/il2cpp_data/etc` e configurações do MelonLoader. Tais strings podem ser códigos internos, nomes próprios, parâmetros ou documentação. Não foram adicionadas indiscriminadamente a `game.json`.

Alguns exemplos de falso positivo: `#hpMax`, `&100010_basUp`, `--backend=burst-llvm-11`. Substituir essas strings globalmente pode corromper informações exibidas ou usadas por mods.

## Fontes aproveitadas

### SectAdmin, Steam Workshop 2814722600

Os registros de `2814722600/ModExcel/LocalText.json` contêm colunas `en` (inglês), `ch` (chinês simplificado), `tc` (tradicional) e `key` (identificador interno). Isso permite associar **as diferentes línguas à mesma linha de localização**, identificada pelo índice do registro.

As traduções PT-BR de `translations` já cobriam esses textos do SectAdmin. O novo processamento aproveitou `key` para adicionar **48 entradas à seção `keys`** de `mod/i18n/pt-BR/SectAdmin.json`, sem inventar traduções. `UIFramework` é nome próprio de dependência, não recebe tradução.

### Mod de Workshop 2864011606

Seis campos em chinês de `ModAssets/Config.json` foram traduzidos e publicados em `mod/i18n/pt-BR/Workshop_2864011606.json`:

| Texto original | PT-BR |
| --- | --- |
| 怀孕时长 | Duração da gestação |
| 怀孕机率 | Probabilidade de gravidez |
| 早产机率 | Probabilidade de parto prematuro |
| 是否早产 | Permitir parto prematuro |
| 是否流产 | Permitir aborto espontâneo |
| 流产机率 | Probabilidade de aborto espontâneo |

Esses nomes são **chaves do arquivo de configuração**. A tradução publicada atua quando as mesmas strings forem mostradas na UI; **não altera as chaves nem o esquema do arquivo original do mod**. Essa correspondência de exibição ainda exige confirmação no jogo.

## Causa do ruído e ajustes feitos

O scanner original extraía todas as chaves de objetos JSON, incluindo identificadores de programação. Além disso, tentava decodificar arquivos de texto ASCII como UTF-16 **sem BOM**, produzindo falsas strings chinesas. A nova versão de `scripts/extract_offline.py`:

- somente interpreta UTF-16 com BOM;
- ignora a documentação `modFQA` e diretórios internos conhecidos;
- não extrai indiscriminadamente todas as chaves JSON, mas mantém chaves em chinês;
- ignora os modelos explicativos de `ModAssets`;
- eleva o tamanho máximo padrão de 5 MB para 30 MB, permitindo tentar tabelas textuais maiores.

A extração por arquivos continua limitada a recursos legíveis. Os grandes arquivos `LocalText.json` listados como ignorados poderão exigir `--max-file-bytes` maior, extração a partir de arquivos Unity ou decodificação especializada. A maior parte das traduções reais do jogo não ficou acessível pelo `offline.json` enviado.

## Gerar arquivo legível a partir deste offline.json

```bash
python3 scripts/curate_offline.py offline.json --output dist/extracted/offline_curado.json
```

Esse script alinha linhas `en/ch/tc/key` do `ModExcel/LocalText.json` e separa os rótulos chineses de `ModAssets/Config.json`. Ele **não copia automaticamente** códigos técnicos para os JSON de tradução.

Após atualizar o scanner, rode novamente para obter um arquivo mais limpo:

```bash
python3 scripts/extract_offline.py \
  --root "$HOME/.steam/debian-installation/steamapps/common/TOI" \
  --root "$HOME/.steam/debian-installation/steamapps/workshop/content/1468810" \
  --output dist/extracted/offline.json
```

Para inspecionar arquivos acima de 30 MB, aumente `--max-file-bytes`, atentando para custo de memória e para os limites do parser.

A revisão dos diálogos e da terminologia ainda exige contexto e validação dentro do jogo.
