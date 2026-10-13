# Compilação e empacotamento

## Compilação simplificada no Ubuntu

Na branch `Dev`, instale o Mono se necessário (`sudo apt install mono-devel mono-xbuild`) e execute na raiz do repositório:

```bash
bash scripts/build.sh
```

O script tenta localizar a instalação do Tale of Immortal em pastas conhecidas da Steam. Caso esteja em outra biblioteca Steam, informe o caminho da pasta raiz do jogo, a que contém `MelonLoader`:

```bash
bash scripts/build.sh "/caminho/da/SteamLibrary/steamapps/common/TOI"
```

O script verifica as DLLs, usa `msbuild` ou `xbuild` e aponta o local da DLL compilada. Não instala mods, não altera o jogo e não substitui o empacotamento nativo descrito abaixo.

Requisitos: código C# compilado para **.NET Framework 4.7.2**, com as bibliotecas do Tale of Immortal e do MelonLoader já geradas na sua instalação (versões anteriores à migração do MelonLoader para .NET 6). O jogo precisa ter sido executado ao menos uma vez para gerar as referências.

O projeto usa `Newtonsoft.Json` incluído nas DLLs da instalação conhecida do jogo. Nenhuma dependência é baixada durante o jogo.

## Linux / Steam Proton

Utilize `msbuild` com o Mono/.NET Framework 4.7.2 reference assemblies disponíveis. Substitua a rota por sua pasta real:

```bash
msbuild src/TalesOfMortal_i18N/TalesOfMortal_i18N.csproj \
  /p:Configuration=Release \
  /p:GameRoot="$HOME/.local/share/Steam/steamapps/common/guigubahuang"
```

Em sistemas com `dotnet msbuild`, também é possível tentar esse comando, desde que o ambiente tenha as referências do Framework 4.7.2. Não confunda o runtime `dotnet` moderno com o framework usado pelo jogo.

O `.csproj` procura:
- `<GameRoot>/MelonLoader/0Harmony.dll`
- `<GameRoot>/MelonLoader/Managed/Assembly-CSharp.dll`
- `<GameRoot>/MelonLoader/Managed/UnityEngine*.dll`
- `<GameRoot>/MelonLoader/Managed/Unity.TextMeshPro.dll`
- `<GameRoot>/MelonLoader/Managed/Newtonsoft.Json.dll`

**Esses caminhos podem variar** conforme a instalação. Confira os arquivos reais antes de compilar. DLLs do jogo não são versionadas aqui.

## Saída

`src/TalesOfMortal_i18N/bin/Release/TalesOfMortalI18N.dll`

O exportador nativo de mods deve ser usado para gerar os demais arquivos de distribuição, como metadados e identificador único (soleID). No Mod Creator, defina `modNamespace` como **`TalesOfMortalI18N`**, exatamente igual ao namespace C# e ao `AssemblyName`. Mantenha `mod/i18n` junto à raiz do mod exportado.

## Limites da primeira versão

O código-fonte está disponível, mas **não foi compilado nem executado contra sua instalação específica**. Antes de lançar uma versão pública, compile com as DLLs reais e verifique pelo log se os hooks foram aplicados. Se um hook não existir na versão do jogo, ele será ignorado com aviso, mantendo os demais.

## Importar as traduções do histórico

Na raiz do repositório, execute `python3 scripts/import_translation_zip.py ~/Downloads/Text.zip`. O importador usa a biblioteca padrão Python, não modifica o arquivo ZIP nem exige XUnity.AutoTranslator.
