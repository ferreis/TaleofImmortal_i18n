# Revisão dos 17 JSON extraídos da Steam Workshop (13/10/2026)

## Resultado da auditoria

Foram examinados **17 arquivos `<ID>.json`** fornecidos pelo usuário e o `index.json`.
O lote apresenta **225 textos únicos por mod** (incluindo repetições entre mods),
**50 linhas completas de localização** (todas do SectAdmin) e **27 arquivos de
origem que não puderam ser interpretados**.

Parte do material extraído não é texto exibido pelo jogo. O modelo padrão do
criador de mods gera repetidamente `g.mod.GetModPathRoot("六位数的随机模组ID");`,
`在代码中获取模组根目录：` e exemplos de sintaxe. Não foram tratados como
traduções de interface.

| ID Steam | Entradas | Linhas LocalText | Arquivos ilegíveis | Resultado |
| --- | ---: | ---: | ---: | --- |
| 2814686803 | 2 | 0 | 0 | somente exemplo do Mod Creator |
| 2814703549 | 3 | 0 | 0 | somente exemplo e opção técnica EditMode |
| **2814722600** | **141** | **50** | **0** | SectAdmin: 50 keys de localização em PT-BR |
| 2816702829 | 2 | 0 | 0 | somente exemplo do Mod Creator |
| 2817294268 | 2 | 0 | 8 | 8 JSON de ModExcel ilegíveis |
| 2822252336 | 2 | 0 | 7 | 7 JSON de ModExcel ilegíveis |
| 2831402551 | 2 | 0 | 0 | somente exemplo do Mod Creator |
| 2831641209 | 2 | 0 | 0 | somente exemplo do Mod Creator |
| **2845764367** | **44** | **0** | **0** | 34 trechos de instruções de configuração traduzidos |
| 2852510475 | 2 | 0 | 0 | somente exemplo do Mod Creator |
| **2864011606** | **8** | **0** | **4** | 6 opções de configuração já estavam traduzidas; 4 JSON ilegíveis |
| 2939760286 | 2 | 0 | 1 | arquivo de parâmetros ilegível |
| 2948478634 | 2 | 0 | 1 | arquivo de aprendizado ilegível |
| 2990310797 | 2 | 0 | 2 | LocalText e RoleLogLocal ilegíveis |
| **2990449768** | **5** | **0** | **1** | 3 notas sobre confecção de talismãs traduzidas |
| 3334313052 | 2 | 0 | 2 | BattleEffect e LocalText ilegíveis |
| 3770748812 | 2 | 0 | 1 | arquivo RuneParameters ilegível |

### Alterações enviadas à Dev

- `mod/i18n/pt-BR/SectAdmin.json`: completadas as **50 keys** disponíveis
  no arquivo `ModExcel/LocalText.json`, preservando `UIFramework` como
  nome próprio e os marcadores variáveis.
- `mod/i18n/pt-BR/Workshop_2845764367.json`: **34** traduções adicionais
  dos trechos explicativos de `ModAssets/配置修改指南.txt`; nomes de arquivos
  e campos técnicos foram preservados.
- `mod/i18n/pt-BR/Workshop_2990449768.json`: arquivo de mod criado com
  **3** traduções das notas de `ModExcel/改动说明.txt`.
- `mod/i18n/pt-BR/Workshop_2864011606.json`: conferidas as 6 configurações
  que já haviam sido traduzidas anteriormente, sem duplicá-las.
- `scripts/extract_workshop_mods.py`: não coleta mais os TXT de exemplo
  do criador de mods por padrão e pode combinar, pelo mesmo ID, arquivos
  de uma cópia **já descriptografada** de um mod.

As traduções de `2845764367` e `2990449768` são **conteúdo documental**.
O dicionário permite substituição se essas frases aparecerem na UI, mas
**não há comprovação de que esses TXT sejam apresentados no jogo**.

### Por que o extrator perdeu conteúdo?

Os caminhos listados como não legíveis incluem arquivos
`ModExcel/LocalText.json`, `DramaDialogue.json`, `DramaOptions.json`
e outras tabelas. A extensão `.json` não garante texto JSON. Alguns arquivos
são binários ou foram exportados com criptografia do jogo. Uma tentativa de
abri-los como UTF-8, Big5 ou GB18030 não equivale a descriptografá-los.

O script agora informa essas falhas. Não pode recuperar textos que nunca
entraram nos JSON fornecidos. Para melhorar a cobertura, o script aceita
recursos **já descriptografados**, sem alterar a pasta original da Workshop:

```bash
python3 scripts/extract_workshop_mods.py \
  --decrypted-mod "2864011606=/caminho/da/copia-descriptografada"
```

O argumento identifica o ID da Steam e a pasta de recursos do respectivo
mod. Ele **não quebra criptografia nem baixa conteúdo externo**.

Existe uma ferramenta comunitária para descriptografar arquivos de mods
([Mod decryption tool, Workshop 3225372871](https://steamcommunity.com/sharedfiles/filedetails/?id=3225372871))
que também declara permitir despejar arquivos JSON do jogo base. Ela exige o
editor e o modo de depuração do Tale of Immortal. Sua compatibilidade com a
versão atual **não foi verificada**; usuários relatam problemas em versões
recentes, portanto não é parte obrigatória do script.

### Próxima validação

A auditoria de estrutura e os testes automatizados verificam os JSON e a
compilação, mas não provam que novos textos documentais apareçam na interface.
Para os mods com tabelas criptografadas, a tradução completa depende de
extrair as tabelas em formato legível ou capturar os diálogos no runtime do
jogo. Não se deve inventar conteúdo para preencher as lacunas.
