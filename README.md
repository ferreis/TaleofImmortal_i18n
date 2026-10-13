# Tales of Mortal i18N

Traduções comunitárias de **Tale of Immortal** (鬼谷八荒) e de seus mods em arquivos JSON externos. Não usa XUnity.AutoTranslator nem fornece tradução automática de novos textos nesta versão.

> **Estado:** carregamento de JSON e aplicação de traduções confirmado no Tale of Immortal em 13/10/2026. Build independente do jogo; cobertura de todos os métodos de interface e atualização sem reiniciar ainda não validada.

## Projeto nativo gerado pelo Tale of Immortal

O editor do jogo criou o projeto em `ModProject_DQKLF9/ModProject`, com identidade `MOD_DQKLF9`.
A DLL precisa se chamar **`MOD_DQKLF9.dll`** e expor **`MOD_DQKLF9.ModMain`**. O adaptador nativo já está integrado ao tradutor, e a compilação é independente da instalação do jogo.

```bash
git switch Dev
git pull origin Dev
bash scripts/build.sh
```

Saída: `ModProject_DQKLF9/ModProject/ModCode/ModMain/bin/Release/MOD_DQKLF9.dll`.
O script prepara também `ModProject_DQKLF9/debug/Mod_DQKLF9/` e `dist/TalesOfMortal_i18N/`, copiando a DLL, os JSON e os dois arquivos `.cache`. Os arquivos originais `ModProject.cache` e `ModData.cache` agora estão versionados e sincronizados; o segundo foi ajustado para `MOD_DQKLF9`. Leia [as instruções atualizadas](docs/BUILD.md).

## Extrator de textos chineses e ingleses

O mod também possui um **extrator de textos originais em tempo de execução**. Ele registra possíveis textos chineses e ingleses que passam pelos hooks de localização/UI do jogo, inclusive textos de mods, antes de traduzi-los. A captura é opcional e está ativada em `mod/i18n/config.json`.

Após atualizar o mod instalado com `bash scripts/install-local.sh`, visite telas e diálogos no jogo. O resultado é salvo periodicamente em `TOI/TalesOfMortal_i18N_Extracted/runtime.json`, **fora** do catálogo de traduções. O arquivo acumula textos únicos, possíveis idiomas, fontes interceptadas e chaves internas, quando disponíveis.

O extrator offline `scripts/extract_offline.py` percorre os formatos textuais legíveis nas pastas do jogo e dos mods, incluindo origens da Steam Workshop. Ele gera `dist/extracted/offline.json`. O script `scripts/prepare_translation_drafts.py` transforma os resultados em rascunhos editáveis por módulo na pasta `dist/drafts`, sem sobrescrever traduções revisadas.

**Limites:** o idioma é identificado por heurística; `en-candidate` pode conter português ou nomes próprios. A captura ao vivo não identifica automaticamente qual DLL gerou cada texto, e não cobre interfaces não interceptadas. O scanner offline lê automaticamente o formato criptografado **excelEncrypt** de ModExcel. Ainda não lê Assembly-CSharp, DLLs, AssetBundles Unity ou outros formatos binários desconhecidos. A extração não traduz textos novos automaticamente.

Após identificar e decodificar o cabeçalho de criptografia nativo de ModExcel, a extração offline passou a recuperar também tabelas `LocalText.json` desse formato, com identificadores internos. **Não é mais necessário fornecer cópias descriptografadas para esse formato específico.**

**Importação da tradução comunitária existente:** o `workshop.zip` de outubro/2026 revelou 54.991 registros do mod `2990310797` com chinês e versões em português. O script `python3 scripts/import_workshop_ptbr.py` converte o JSON já extraído em um catálogo de fallback local com verificações de nomes protegidos, marcadores de variável e ambiguidades. Não sobrescreve traduções anteriores. Consulte [a revisão do ZIP e as instruções](docs/WORKSHOP_ZIP_IMPORT.md).

**Fonte adaptativa em textos longos:** a DLL agora pode reduzir automaticamente
a fonte de traduções extensas em `UnityEngine.UI.Text` e em
`TextMeshProUGUI` quando o hook TMP estiver disponível. Configuração em
`mod/i18n/config.json` → `adaptiveText`; componentes de entrada editável
são preservados. O tooltip ao passar o mouse ainda está em estudo.
Veja [configuração e limitações](docs/UI_AUTO_FIT.md).

Veja [instruções e exemplos completos](docs/EXTRACTOR.md).

## Diagnóstico após importação

A DLL **não implementa tradução automática de frases desconhecidas**. Ela aplica traduções dos JSON aos textos interceptados, e o funcionamento foi confirmado em execução no jogo. Alterações nos JSON exigem reiniciar o jogo nesta versão.

Se você já importou `Mod_DQKLF9` localmente e deseja aplicar a versão mais recente sem exportar novamente, **feche o jogo** e execute:

```bash
git switch Dev
git pull origin Dev
bash scripts/install-local.sh
```

Para localizar DLLs antigas de XUnity ainda carregáveis e ler os logs:

```bash
bash scripts/check-xunity.sh
```

O novo build inclui `ModAssets/i18n`, o diretório apropriado para dados adicionais exportáveis. O leitor também reconhece `i18n` na raiz para compatibilidade. O teste offline `bash scripts/test.sh` valida a leitura de traduções dos JSON; não prova o funcionamento dos hooks de Unity no jogo.

O identificador `SchoolAdmin` no ZIP é um alias do **SectAdmin**, Workshop `2814722600`. As 147 traduções foram consolidadas em `SectAdmin.json`; o arquivo vazio antigo foi substituído. A fonte separada `SectAdmin_PTBR.txt` contém apenas comentários. A palavra `Vingativo(a)` aparecia no TXT como `Vingativo(a)=Vingativo(a)`, sem transformação.

## Identificação dos módulos por metadados

**O nome do arquivo JSON não determina a origem da tradução.** Cada catálogo inclui:

```json
{
  "module": {
    "kind": "mod",
    "id": "steam:2814722600",
    "name": "SectAdmin",
    "workshopId": "2814722600",
    "sourceAlias": "SchoolAdmin"
  },
  "translations": {
    "Admin": "Chamar administrador"
  },
  "keys": {},
  "patterns": []
}
```

- `module.kind`: `game`, `mod`, `fallback` ou `names`.
- `module.id`: identificador estável, único e obrigatório. Pode ser `steam:ID` para mods Workshop ou `local:meu-mod` para mods fora da Steam.
- `module.name`: nome legível. Não precisa ser o nome da DLL.
- `module.workshopId`: opcional, apenas para mods da Workshop.
- `module.sourceAlias`: nome do pacote encontrado na importação; não comprova namespace nem DLL real.
- `module.namespace` ou `module.assembly`: identificadores opcionais para informar o namespace e nome da DLL **quando forem conhecidos**, sem precisar da Steam.

Os arquivos `SectAdmin.json`, `game.json`, `zzz-auto.json` e `protected-names.json` podem ser renomeados sem alterar a classificação, desde que o campo `module` seja preservado. Arquivos antigos sem `module` continuam usando a regra de compatibilidade por nome.

`translations` traduz pelo texto original, `keys` traduz por chave de localização do jogo (por exemplo, argumento de `GameTool.LS`) e `patterns` aceita regex. Como o XUnity gerou pares de **textos**, os `keys` do acervo importado continuam vazios. São sensíveis a maiúsculas/minúsculas.

A origem identificada serve para organizar, auditar e estabelecer prioridade (`names`, `game`, `mod`, `fallback`). **Ela ainda não restringe uma tradução apenas à DLL do mod correspondente**: o hook global de UI conhece o texto, não necessariamente qual mod o produziu. Textos originais iguais podem conflitar. O script `python3 scripts/audit_catalogs.py` identifica essas colisões e problemas de placeholders.

## Como as traduções ficam organizadas

```text
TalesOfMortal_i18N/                 <- pasta do mod exportado pelo criador do jogo
├── ModCode/                         <- DLL e estrutura do Mod Creator
└── i18n/
    ├── config.json                  <- idioma ativo
    └── pt-BR/
        ├── game.json                <- textos do jogo
        ├── SectAdmin.json           <- textos do SectAdmin
        ├── SectQOL.json             <- textos do SectQOL
        └── protected-names.json     <- nomes que não devem ser modificados
```

Cada idioma possui sua pasta, e cada mod pode possuir seu próprio JSON. Com `module` presente, até o JSON de nomes protegidos pode ser renomeado. Não é preciso alterar C# para acrescentar traduções.

## Formatos de JSON

O formato simples traduz o texto original exato:

```json
{
  "Recruit Disciple": "Recrutar Discípulo",
  "Sect Management": "Gerenciamento da Seita"
}
```

Também são aceitos objetos separados por origem, para casos em que o jogo expõe uma chave de localização:

```json
{
  "translations": {
    "Recruit Disciple": "Recrutar Discípulo"
  },
  "keys": {
    "ui_example_key": "Exemplo de tradução por chave"
  }
}
```

O arquivo `protected-names.json` possui o formato `{"names":["龙儿","龍兒"]}` e bloqueia traduções de nomes **exatamente iguais** ao texto protegido. Ele não reconhece automaticamente NPCs novos nem garante proteção de nomes inseridos dentro de frases maiores.

O idioma é escolhido em `i18n/config.json`, por exemplo: `{"language":"pt-BR"}`. Na ausência do arquivo, usa `pt-BR`.

## Regras de correspondência

- Correspondência exata, sensível a maiúsculas e espaços, para `translations` e `keys`. Regras opcionais `patterns` permitem expressões regulares com limite de tempo de 100 ms por operação.
- A tradução por chave é consultada antes da tradução pelo texto retornado.
- Precedência definida pelo `module.kind`: nomes protegidos, jogo, mods e legado/fallback. Mods são ordenados por `module.id`, sem depender do nome do arquivo. Em caso de conflito, o **primeiro** valor é preservado e registrado no log.
- Arquivos inválidos são ignorados individualmente e a tradução original permanece intacta quando não houver correspondência.
- Os JSON são carregados no início do mod. Reinicie o jogo para aplicar alterações.

## Integração e instalação

Este projeto usa o formato **ModCode do Mod Creator nativo** do Tale of Immortal. O jogo carrega uma classe pública `ModMain` com os métodos `Init()` e `Destroy()`, e o mod aplica patches Harmony. O próprio jogo usa MelonLoader para executar ModCode. **A compilação utiliza somente Mono/.NET Framework 4.7.2; as APIs do jogo são resolvidas por reflexão na execução.**

1. Abra o projeto existente em `ModProject_DQKLF9/ModProject` no Mod Creator do jogo. Os dois arquivos `.cache` estão incluídos. O namespace foi alinhado para **`MOD_DQKLF9`** (o cache recebido originalmente dizia `Mod_i18N`).
2. Compile sem o jogo instalado usando `bash scripts/build.sh` e Mono (veja [compilação](docs/BUILD.md)). A DLL terá o namespace e nome exigidos pelo editor.
3. Compile `MOD_DQKLF9.dll` com `bash scripts/build.sh`; o projeto nativo já está integrado, então exporte-o pelo Mod Creator.
4. Copie a pasta `i18n` fornecida em `mod/i18n` para a raiz **do mod exportado**. Se a DLL tiver sido movida para outra pasta pelo jogo, o carregador também tenta localizar a pasta do mod abaixo de `Mods/TalesOfMortal_i18N`.
5. Ative o mod e inicie o jogo. O log Unity/MelonLoader apresentará `[Tales of Mortal i18N]` e as quantidades carregadas.

**Não** instale `MOD_DQKLF9.dll` isoladamente em `<jogo>/Mods/`: esta versão possui entrada `ModMain` para o ModCode do jogo, não o atributo `MelonInfo` de um mod MelonLoader autônomo.

## O que esta versão intercepta

- `GameTool.LS(string)` e `GameTool.LS(string, int)`, por chave interna.
- `ConfLocalTextEx.text(ConfLocalTextItem)`, por chave interna.
- Setter de `UnityEngine.UI.Text.text` e setter de `TMPro.TMP_Text.text`, por texto original.

Textos exibidos em sistemas próprios de outros mods (como interfaces que não passam por esses setters), sprites, imagens, nomes gerados e conteúdo carregado diretamente por outros mecanismos podem exigir patches específicos depois. **Não há promessa de cobertura universal nesta primeira versão.**

## Importar traduções TXT antigas

Se você já tem arquivos do XUnity, o conversor opcional transforma pares simples `original=tradução` em JSON, sem usar o XUnity durante o jogo. Os TXT são lidos na ordem indicada (maior prioridade primeiro) e **não sobrescrevem** valores já presentes no JSON.

```bash
python3 scripts/import_xunity.py -o mod/i18n/pt-BR/SectAdmin.json \
  /caminho/SectAdmin_PTBR.txt /caminho/_AutoGeneratedTranslations.txt
```

O importador não interpreta regras de regex nem determina automaticamente se um texto é nome de NPC. Revise os nomes antes de adicioná-los em `protected-names.json`. Faça um backup das traduções existentes antes de uma conversão grande.

## Importação completa do arquivo Text.zip

O ZIP de traduções existentes pode ser importado sem passar pelo XUnity.AutoTranslator:

```bash
python3 scripts/import_translation_zip.py /caminho/Text.zip
```

O importador lê todos os TXT dentro do ZIP, identifica os pacotes da Workshop e os transforma em `mod/i18n/pt-BR/*.json`. Ele converte sequências escapadas do XUnity (`\\n`, `\\=`, `\\u002f`), mantém traduções manuais prioritárias, transforma os padrões `r:"..."` em `patterns` com placeholders nomeados e preserva nomes protegidos. Traduções que repetem o original são omitidas do runtime porque não alteram o texto mostrado.

**A execução do importador é feita antes de compilar ou publicar o mod.** O script não depende do XUnity nem de bibliotecas Python externas. Os arquivos `Text.zip` originais permanecem intactos.

As traduções importadas automaticamente precisam de revisão linguística antes de uma versão pública.

## Contribuições

Adicione um JSON na pasta do idioma correspondente. Preserve placeholders (como `{0}`, `{name}`, tags rich text) e caracteres Unicode. Prefira uma PR na branch `Dev`.

## Referências técnicas

- [TOI ModCode guide](https://github.com/creater0822/TOI_Mods/blob/main/Guides/SummaryModCode.md)
- [TL-Spanish (referência para os hooks do jogo)](https://github.com/ChrisTVH/TL-Spanish)

Este repositório contém implementação própria. Nenhum pacote do jogo nem código de outro mod é distribuído aqui.
