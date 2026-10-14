# Compilação do projeto DQKLF9

A identidade do projeto é `DQKLF9` (`soleID`) e o namespace de ModCode é `MOD_DQKLF9`. O `ModData.cache` enviado originalmente tinha `Mod_i18N`; corrigimos somente esse campo para coincidir com a DLL e com `MOD_DQKLF9.ModMain`. Os demais metadados originais foram preservados.

Os arquivos reais `ModProject.cache` e `ModData.cache` estão versionados em `ModProject_DQKLF9/ModProject/`. Não é necessário recriar o projeto no editor.

## Build offline (Ubuntu/Pop!_OS)

Na branch `Dev`, execute:

```bash
git pull origin Dev
bash scripts/build.sh
```

O script usa `mcs` do pacote `mono-devel` e compila em .NET Framework 4.7.2 **sem Unity, Tale of Immortal, MelonLoader ou Steam instalados**.

DLL resultante:

```text
ModProject_DQKLF9/ModProject/ModCode/ModMain/bin/Release/MOD_DQKLF9.dll
```

O script também copia a DLL e os JSON de `mod/i18n` para as seguintes pastas:

```text
ModProject_DQKLF9/ModProject/i18n/             # arquivos-fonte do mod criado
ModProject_DQKLF9/debug/Mod_DQKLF9/
  ├── ModProject.cache
  ├── ModData.cache
  ├── ModCode/dll/MOD_DQKLF9.dll
  └── i18n/pt-BR/*.json
dist/TalesOfMortal_i18N/
  ├── ModCode/dll/MOD_DQKLF9.dll
  └── i18n/pt-BR/*.json
```

Os JSON continuam editáveis, sem recompilar a DLL. O script só prepara arquivos locais. A pasta `dist` é um **staging** com DLL, JSON e os dois arquivos `.cache`. Ainda não equivale, por si só, a um pacote exportado e instalado pelo Mod Creator: podem existir metadados e etapas adicionais geradas pelo jogo.

## Instalação inicial e atualizações, com um único comando

**Não é necessário criar ou importar o mod manualmente pelo Mod Creator.**
Feche completamente o Tale of Immortal, entre na branch `Dev` e execute:

```bash
git pull origin Dev
bash scripts/install-local.sh
```

O instalador agora executa automaticamente:

1. Compila `MOD_DQKLF9.dll`, usando o Mono.
2. Cria `<JOGO>/ModExportData/Mod_DQKLF9/` se essa pasta não existir.
3. Cria o **`ModExportData.cache` nativo cifrado**, com `projectData`,
   `items` e `modNamespace`, a partir dos metadados versionados
   `ModProject.cache` e `ModData.cache`. Não renomeia simplesmente um
   cache de projeto.
4. Copia a DLL para `ModCode/dll/` e as traduções para `ModAssets/i18n/`.
5. Se o mod já estiver instalado, preserva o cache que o jogo tiver criado,
   valida o ID do mod e faz backup da DLL antes de substituí-la se mudar.
6. Verifica os arquivos obrigatórios antes de informar sucesso.

Não altera os arquivos dos outros mods nem reinstala o jogo. Se a Steam
estiver em outra biblioteca, informe o caminho do jogo:

```bash
bash scripts/install-local.sh "/caminho/steamapps/common/TOI"
```

Estrutura instalada:

```text
TOI/
└── ModExportData/
    └── Mod_DQKLF9/
        ├── ModExportData.cache
        ├── ModProject.cache
        ├── ModData.cache
        ├── ModCode/
        │   └── dll/MOD_DQKLF9.dll
        └── ModAssets/
            └── i18n/
                ├── config.json
                └── pt-BR/*.json
```

**Na primeira instalação, ainda poderá ser preciso ativar o mod em
`Mods > Mods locais` dentro do jogo.** O script instala os arquivos no
formato do jogo, mas não altera sua lista de mods ativados nem suas
configurações de usuário.

O arquivo `ModExportData.cache` é cifrado com o formato nativo de
ModExportData identificado em um mod público já exportado; os testes
verificam codificação, metadados e instalação inicial num diretório
temporário. **A detecção e ativação no seu Tale of Immortal ainda devem ser
confirmadas dentro do jogo.**

Teste local do instalador sem iniciar o jogo:

```bash
bash scripts/test_install_local.sh
```

Após iniciar o jogo, consulte:

```bash
bash scripts/check-xunity.sh
cat "$HOME/.steam/debian-installation/steamapps/common/TOI/TalesOfMortal_i18N.log"
```

## Projeto fonte e exportação manual opcional

O projeto do Mod Creator continua disponível em
`ModProject_DQKLF9/ModProject`, com o mesmo ID `DQKLF9`. Ele pode
ser aberto no editor para modificar recursos nativos. **A exportação
manual não é necessária** para a instalação inicial do tradutor com o
novo `install-local.sh`.

O adaptador de código precisa permanecer com o nome
`MOD_DQKLF9.dll` e com a classe de entrada `MOD_DQKLF9.ModMain`,
com métodos `Init()` e `Destroy()`. Não o instale como mod
MelonLoader independente.

## Estado verificado e limites funcionais

A DLL não embute traduções. Os JSON são copiados para `ModProject_DQKLF9/ModProject/ModAssets/i18n`, e o código os procura em `ModAssets/i18n` (com compatibilidade para `i18n` na raiz). Este caminho segue a convenção de arquivos adicionais do Mod Creator.

**Não existe tradução automática de textos novos em tempo real** nesta versão. O código apenas traduz textos conhecidos nos JSON ou cobertos pelas 5 regras regex existentes. Um texto ausente continua original.

O pacote `SectAdmin.json` tem zero traduções porque a fonte `SectAdmin_PTBR.txt` do ZIP continha apenas comentários. `SchoolAdmin.json` tem 147 entradas, mas é outra camada. O TXT original possui a entrada `Vingativo(a)=Vingativo(a)`, que mantém a palavra como já aparecia e não comprova que nosso mod a tenha traduzido.

Para testar os dados **sem o jogo**:

```bash
bash scripts/test.sh
```

Para diagnosticar cópias possivelmente ativas do XUnity e conferir o último log:

```bash
bash scripts/check-xunity.sh
```

Ambos os scripts são não destrutivos. Para investigar o mod em execução, envie o log atual do MelonLoader; o sucesso no GitHub Actions comprova apenas build e leitura do dicionário, não o funcionamento dos hooks IL2CPP no jogo.


## Limites

O build sem o jogo foi configurado, mas a execução real ainda precisa de validação no Tale of Immortal. A implementação resolve Harmony e os métodos de Unity via reflexão na execução e registra avisos se algum hook não estiver disponível.

O diretório `ModProject_DQKLF9/ModProject/ModRes` contém arquivos de exemplo gerados pelo Unity e não é necessário para o tradutor JSON; foi preservado para não apagar conteúdo do projeto criado.

## Correção do leitor JSON (outubro/2026)

O primeiro teste dentro do jogo mostrou `textos: 0`, apesar de encontrar a pasta e ler os nomes protegidos. O `DataContractJsonSerializer` lançava uma exceção de invocação no runtime IL2CPP do jogo, fazendo o carregador ignorar os arquivos de tradução.

Agora `src/TalesOfMortal_i18N/JsonTextParser.cs` lê os objetos, arrays e strings JSON por código C# explícito, sem DataContract, Newtonsoft nem reflexão para desserializar. Isso mantém o build independente do jogo.

O GitHub Actions validou os **22 arquivos JSON**, incluindo **3.677 textos**, **1.759 nomes protegidos** e **5 regras regex**. Use `bash scripts/test.sh` para reproduzir esse teste offline. Em seguida, use `bash scripts/install-local.sh` com o jogo fechado para atualizar o mod exportado. A validação final precisa ser feita **no jogo**, verificando o log novo; compilação bem-sucedida não prova que todos os hooks de Unity funcionam.

Os hooks de `TMPro` estavam indisponíveis no log de 13/10/2026; por isso a cobertura de textos da interface continua parcial até inspecionarmos a versão do runtime utilizada pelo jogo.

## Identidade do módulo, sem dependência do nome do JSON

Cada pacote carrega `module.kind`, `module.id` e `module.name`. A origem Workshop é dada por `module.workshopId`, quando houver. Fora da Steam, use um identificador estável, por exemplo:

```json
{
  "module": {
    "kind": "mod",
    "id": "local:meu-mod",
    "name": "Meu mod",
    "namespace": "MOD_MeuMod",
    "assembly": "MeuMod.dll"
  },
  "translations": {
    "Original text": "Texto traduzido"
  },
  "keys": {},
  "patterns": []
}
```

Os campos `namespace` e `assembly` são dados opcionais para catalogação; **não são verificados automaticamente na execução**. Evite inventá-los quando não souber. Também não é feita detecção da presença do mod: todos os JSON são carregados em um dicionário global de traduções.

`translations`: texto literal original → tradução.
`keys`: chave interna do jogo → tradução. Os importados do XUnity não forneciam essas chaves.
`patterns`: expressão regular → texto substituto.

Para verificar o comportamento mesmo com nomes de arquivo trocados, rode `bash scripts/test.sh`. Ele renomeia temporariamente o JSON do jogo, do SectAdmin, do legado e dos nomes protegidos em uma cópia descartável e valida as mesmas 3.677 traduções efetivas e 1.759 nomes.

O pacote identificado por `SchoolAdmin` em `Text.zip` corresponde ao **SectAdmin** (`steam:2814722600`). As 147 entradas foram migradas para `SectAdmin.json`, substituindo o arquivo vazio.

A verificação de qualidade estrutural usa `python3 scripts/audit_catalogs.py` e gera `dist/TalesOfMortal_i18N/catalog-audit.json` com contagem de traduções, IDs, colisões entre mods, marcadores de formato e arquivos vazios. O relatório identifica potenciais problemas, mas não substitui a revisão linguística humana das traduções.
