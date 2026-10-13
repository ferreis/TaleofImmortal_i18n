# Build do Tales of Mortal i18N (Ubuntu/Pop!_OS)

O projeto é compilado como **biblioteca .NET Framework 4.7.2** com o Mono.
**Não precisa ter o jogo instalado, não acessa a pasta da Steam, não utiliza DLLs de Unity, MelonLoader ou Tale of Immortal durante o build.**
O Harmony e os tipos do jogo serão localizados por reflexão quando o mod executar dentro do jogo.

## Compilar

```bash
sudo apt install mono-devel
git switch Dev
git pull origin Dev
bash scripts/build.sh
```

Saída:

```text
src/TalesOfMortal_i18N/bin/Release/TalesOfMortalI18N.dll
```

O script prefere o compilador `mcs`, já fornecido por `mono-devel`, e usa apenas as referências `System.Core` e `System.Runtime.Serialization`. Não precisa de pacotes NuGet.

## Executar dentro do jogo

**Build independente não significa execução independente.** O código compilado é um **ModCode nativo** do Tale of Immortal, que exige o carregador de mods do jogo e Harmony durante a execução.

- Crie um mod do tipo ModCode no Mod Creator, configurando o namespace `TalesOfMortalI18N`.
- Use a DLL gerada no pacote ModCode exportado pelo criador nativo (não copie esta DLL isolada para a pasta `Mods` do MelonLoader).
- Copie os JSON de `mod/i18n` para a pasta `i18n` na raiz do mod exportado.
- Desative XUnity.AutoTranslator para evitar traduções sobrepostas.
- Confira o log com prefixo `[Tales of Mortal i18N]`. O log informa quantos hooks Harmony funcionaram.

A compilação não comprova compatibilidade com cada versão do Tale of Immortal. Hooks como `GameTool.LS` e os setters de UI são resolvidos **em tempo de execução**; caso um deles não esteja disponível, o mod registra um aviso sem exigir essas referências no build.

## Sobre o erro original do Mono

O `xbuild` falhava com `InternalErrorException` ao ler `UnityEngine.dll` exportada pelo jogo. Removemos as referências externas e agora compilamos somente as classes do próprio tradutor e bibliotecas padrão do .NET 4.7.2.

## Traduções

Os JSON localizados em `mod/i18n/pt-BR` são arquivos de dados externos, não são incorporados à DLL. Alterar o conteúdo dos JSON não requer recompilar. Reinicie o jogo depois de modificar traduções.
