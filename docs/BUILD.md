# Compilação do projeto DQKLF9

A identidade do projeto criada pelo jogo é `MOD_DQKLF9`. **Não modifique esse namespace no editor.**

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
  ├── ModCode/dll/MOD_DQKLF9.dll
  └── i18n/pt-BR/*.json
dist/TalesOfMortal_i18N/
  ├── ModCode/dll/MOD_DQKLF9.dll
  └── i18n/pt-BR/*.json
```

Os JSON continuam editáveis, sem recompilar a DLL. O script só prepara arquivos locais. A pasta `dist` é um **staging**, não um mod completo, pois precisa dos arquivos de metadados que o editor nativo exporta.

## Instalação

O projeto do mod foi adicionado em `ModProject_DQKLF9/ModProject`. Abra-o no editor do Tale of Immortal e faça a exportação normal. Os arquivos `.cache` e os metadados não foram enviados ao GitHub, então a cópia do repositório por si só pode **não conter um projeto importável completo** no editor.

Não renomeie o `MOD_DQKLF9.dll` nem tente carregar como mod MelonLoader independente. O tipo de entrada exportado é `MOD_DQKLF9.ModMain` com métodos `Init()` e `Destroy()`.

Depois de exportar e instalar o mod pelo editor, garanta que a pasta `i18n` fique junto à raiz do mod exportado, ao lado de `ModCode`. Desative o XUnity.AutoTranslator para evitar tradução duplicada.

## Limites

O build sem o jogo foi configurado, mas a execução real ainda precisa de validação no Tale of Immortal. A implementação resolve Harmony e os métodos de Unity via reflexão na execução e registra avisos se algum hook não estiver disponível.

O diretório `ModProject_DQKLF9/ModProject/ModRes` contém arquivos de exemplo gerados pelo Unity e não é necessário para o tradutor JSON; foi preservado para não apagar conteúdo do projeto criado.
