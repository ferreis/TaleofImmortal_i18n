# Tales of Mortal i18N

Traduções comunitárias de **Tale of Immortal** (鬼谷八荒) e de seus mods em arquivos JSON externos. Não usa XUnity.AutoTranslator, serviços online nem tradução automática em execução.

> **Estado:** implementação inicial, ainda sem DLL validada dentro do jogo. Os pontos de interceptação foram selecionados com base nas APIs conhecidas do Tale of Immortal, mas precisam de validação na instalação real.

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

Cada idioma possui sua pasta, e cada mod pode possuir seu próprio JSON. Os nomes dos arquivos JSON são livres, exceto `protected-names.json`. Não é preciso alterar C# para acrescentar traduções.

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

- Correspondência exata, sensível a maiúsculas e espaços; não traduz por partes nem usa regex.
- A tradução por chave é consultada antes da tradução pelo texto retornado.
- Arquivos são processados em ordem alfabética estável (ignorando maiúsculas). Em caso de duplicação com tradução diferente, o **primeiro** valor é preservado e o conflito é registrado no log.
- Arquivos inválidos são ignorados individualmente e a tradução original permanece intacta quando não houver correspondência.
- Os JSON são carregados no início do mod. Reinicie o jogo para aplicar alterações.

## Integração e instalação

Este projeto usa o formato **ModCode do Mod Creator nativo** do Tale of Immortal. O jogo carrega uma classe pública `ModMain` com os métodos `Init()` e `Destroy()`, e o mod aplica patches Harmony. O próprio jogo já usa MelonLoader para executar ModCode.

1. Abra o criador de mods do Tale of Immortal e crie um mod com código. Configure o **namespace do ModCode** como `TalesOfMortalI18N` (o mesmo namespace do código e nome da assembly do projeto). Esse procedimento gera os metadados e a estrutura exigidos pela versão do jogo. Não substitua esses arquivos por um ZIP que contenha apenas DLL.
2. Compile o projeto em `src/TalesOfMortal_i18N` com as bibliotecas da **sua instalação do jogo** (veja [compilação](docs/BUILD.md)). O namespace configurado no editor deve coincidir com o do código.
3. Adicione a DLL compilada à estrutura ModCode do mod criado e exporte-o pelo Mod Creator.
4. Copie a pasta `i18n` fornecida em `mod/i18n` para a raiz **do mod exportado**. Se a DLL tiver sido movida para outra pasta pelo jogo, o carregador também tenta localizar a pasta do mod abaixo de `Mods/TalesOfMortal_i18N`.
5. Ative o mod e inicie o jogo. O log Unity/MelonLoader apresentará `[Tales of Mortal i18N]` e as quantidades carregadas.

**Não** instale `TalesOfMortal_i18N.dll` isoladamente em `<jogo>/Mods/`: esta versão possui entrada `ModMain` para o ModCode do jogo, não o atributo `MelonInfo` de um mod MelonLoader autônomo.

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

## Contribuições

Adicione um JSON na pasta do idioma correspondente. Preserve placeholders (como `{0}`, `{name}`, tags rich text) e caracteres Unicode. Prefira uma PR na branch `Dev`.

## Referências técnicas

- [TOI ModCode guide](https://github.com/creater0822/TOI_Mods/blob/main/Guides/SummaryModCode.md)
- [TL-Spanish (referência para os hooks do jogo)](https://github.com/ChrisTVH/TL-Spanish)

Este repositório contém implementação própria. Nenhum pacote do jogo nem código de outro mod é distribuído aqui.
