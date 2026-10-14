# Revisão do workshop.zip e importação PT-BR

Análise do arquivo `workshop.zip` recebido em 13/10/2026, produzido pelo
novo `scripts/extract_workshop_mods.py`.

## Resultado real da extração

A extração percorreu **17 mods** do Tale of Immortal. O maior avanço foi
conseguir ler os arquivos `ModExcel` protegidos pelo formato excelEncrypt.

| Origem | Dados úteis |
| --- | --- |
| `2990310797.json` | **54.991 registros** em `ModExcel/LocalText.json`, com a coluna `ch` em chinês, a coluna `en` frequentemente já em português e a coluna `key` com identificação interna |
| `3334313052.json` (PFAutoBattle) | **26** linhas completas EN/CH/TC/key; já incluídas no catálogo PT-BR |
| `2814722600.json` (SectAdmin) | **50** linhas completas de localização; já incluídas no catálogo PT-BR |
| `2822252336.json` | **83** entradas extraídas; acrescentada a tradução em falta `指点` → `Orientar` |
| `2864011606.json` | 6 rótulos de configuração traduzidos anteriormente, mas 3 ModExcel ainda produzem JSON inválido após descriptografia |
| `2948478634.json` | ModExcel/BattleSkillLearn.json ainda não parseável como JSON |

Os mods restantes não apresentaram novos textos de interface legíveis, ou
seus recursos eram vazios/técnicos. Não foram criadas traduções inventadas
para preencher esses arquivos.

## Tradução comunitária 2990310797: como aproveitar

A coluna `en` do mod `2990310797` frequentemente **contém português**,
não inglês. Exemplo: `欢迎来到宗门` poderá ser associado à frase em português
registrada na mesma linha, com a chave interna preservada.

Há ressalvas importantes: o pacote tem traduções incompletas ou misturadas
com inglês, termos inconsistentes, nomes próprios, placeholders danificados
e originais chineses que se repetem com traduções diferentes em outros
contextos. Não seria seguro inserir todas as 54.991 entradas cegamente
no catálogo global.

O script `scripts/import_workshop_ptbr.py` permite aproveitar as entradas
sem publicar integralmente no GitHub a tradução de terceiros.

```bash
cd ~/Documentos/Aplicativos/TaleofImmortal_i18n
git switch Dev
git pull origin Dev

# Usa o 2990310797.json já extraído pelo scanner:
python3 scripts/import_workshop_ptbr.py

# Atualiza DLL e JSON instalados. Feche o jogo antes:
bash scripts/install-local.sh
```

Ele gera `mod/i18n/pt-BR/Workshop_2990310797.json`, usando o mesmo ID
de módulo já reservado no repositório. O JSON gerado usa `module.kind:
"fallback"`, portanto traduções revisadas existentes têm prioridade.

Na análise isolada do ZIP (antes de comparar com os JSON já existentes),
o algoritmo identificou **52.855 registros candidatos**, **35.014 textos
chineses com tradução única** e **52.855 chaves internas**. A quantidade
final importada localmente será menor após excluir textos e chaves já
presentes nos outros catálogos e nomes protegidos.

Foram descartadas linhas vazias, originais iguais à tradução, casos em que
a tradução contém chinês, e frases com marcadores `{variável}` incompatíveis.
Quando uma frase chinesa possui duas ou mais traduções divergentes, não é
adicionada à correspondência por texto literal, mas suas `keys` ainda
podem ser importadas para permitir escolha contextual.

**Esta é uma importação de traduções existentes, não uma revisão ou
retradução humana de cada frase.** Seu uso no runtime ainda precisa de
validação no jogo, sobretudo pelo tamanho do catálogo.

## Como compartilhar a origem ou o resultado

O arquivo de entrada do script é
`dist/extracted/workshop/2990310797.json`.
Os resultados originais são preservados fora da pasta do jogo.
O arquivo final é gerado localmente e pode ser copiado ou versionado
se o usuário verificar os termos e os direitos de redistribuição da
tradução comunitária.

O repositório distribui o **importador** e o tratamento dos JSON;
a base completa de terceiros não é automaticamente enviada ao GitHub.
