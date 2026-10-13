# Extrator de textos: Tale of Immortal e mods

O extrator coleta **textos originais**, não traduz automaticamente. Sua finalidade é descobrir strings ainda não presentes no catálogo PT-BR e gerar rascunhos para tradução.

## 1. Captura enquanto o jogo funciona

O extrator em C# já faz parte de `MOD_DQKLF9.dll`. Atualize com o jogo fechado:

```bash
git switch Dev
git pull origin Dev
bash scripts/install-local.sh
```

O `mod/i18n/config.json` ativa a captura por padrão:

```json
{
  "language": "pt-BR",
  "extractor": {
    "enabled": true,
    "includeEnglish": true,
    "includeChinese": true,
    "flushSeconds": 30,
    "maxEntries": 50000
  }
}
```

Entre no jogo e visite os menus, eventos, diálogos e interfaces dos mods que deseja traduzir. Os hooks capturam os textos originais *antes* de o nosso tradutor aplicar as traduções, além de algumas chaves internas de localização.

O arquivo gerado fica em:

```text
~/.steam/debian-installation/steamapps/common/TOI/TalesOfMortal_i18N_Extracted/runtime.json
```

O jogo grava de forma acumulativa a cada 30 segundos e ao destruir o mod (quando esse evento é chamado). Não dependa apenas do fechamento forçado para persistir os últimos textos.

Exemplo ilustrativo de saída:

```json
{
  "format": "talesofmortal-extraction-v1",
  "origin": "runtime-unattributed-game-or-mod",
  "entries": [
    {
      "text": "招募弟子",
      "language": "zh-und",
      "observations": 5,
      "sources": ["ui.text"],
      "localizationKeys": []
    },
    {
      "text": "Recruit Disciple",
      "language": "en-candidate",
      "observations": 2,
      "sources": ["GameTool.LS"],
      "localizationKeys": ["ui.sect.recruit"]
    }
  ]
}
```

Estes são **exemplos de estrutura**, não resultados extraídos do computador do usuário.

Para desligar a coleta, altere `extractor.enabled` para `false` no `config.json` **instalado** e reinicie o jogo. A captura não faz conexões de rede.

## 2. Extração offline de arquivos legíveis

Também existe `scripts/extract_offline.py`. Ele examina fontes textuais como JSON, TXT, CSV, TSV, XML, INI, YAML e LANG. O scanner identifica a origem usando a pasta do mod, incluindo IDs da Steam Workshop quando presentes.

```bash
cd ~/Documentos/Aplicativos/TaleofImmortal_i18n
python3 scripts/extract_offline.py \
  --root "$HOME/.steam/debian-installation/steamapps/common/TOI" \
  --root "$HOME/.steam/debian-installation/steamapps/workshop/content/1468810" \
  --output dist/extracted/offline.json
```

Se o Steam Workshop estiver em outro disco, altere o caminho `--root`. Use um `--root` quantas vezes for necessário. Não precisa rodar como root.

O scanner não reprocessa nossos JSON de tradução, logs, DLLs e executáveis. Usa limite de 5 MB por arquivo e 120 mil entradas únicas por execução, configuráveis por `--max-file-bytes` e `--max-entries`.

**Limite importante:** arquivos Unity AssetBundle, TextAsset empacotado, tabelas criptografadas, DLLs e recursos nativos IL2CPP exigem decodificadores especializados. O scanner offline não consegue extrair esses formatos binários. A captura em tempo de execução complementa essa limitação, mas não garante todos os textos sem visitar as telas nem captura métodos não interceptados, incluindo alguns TMP.


## 2A. Extrair um arquivo `<ID>.json` para cada mod instalado

Para extrair todos os mods da Workshop automaticamente, **sem misturar textos de mods diferentes**, execute na raiz do repositório:

```bash
python3 scripts/extract_workshop_mods.py
```

O script procura a pasta da Workshop nas bibliotecas Steam conhecidas no Linux. Se necessário, informe seu caminho manualmente:

```bash
python3 scripts/extract_workshop_mods.py \
  --workshop-dir "$HOME/.steam/debian-installation/steamapps/workshop/content/1468810"
```

A saída é uma única pasta com **um JSON por ID numérico**:

```text
dist/extracted/workshop/
├── 2814722600.json
├── 2864011606.json
├── 3334313052.json
└── index.json
```

Cada `<ID>.json` contém `module.id` (`steam:ID`), `module.workshopId`, `entries` com texto original e prováveis idiomas, `localizationKeys` e `locations`, além de `localizations` para alinhar as colunas `en`, `ch`, `tc` e `key` dos arquivos `ModExcel/LocalText.json`. O `index.json` resume quais mods foram examinados, incluindo os que não possuem recursos textuais legíveis.

O script preserva a estrutura original de cada mod e **não grava nada dentro da Steam Workshop**. Ele não altera os JSON PT-BR do tradutor. O resultado é material para revisão e não um dicionário de tradução pronto para usar. Arquivos Unity binários, DLLs e conteúdo criptografado permanecem fora do alcance deste extrator.

## 3. Gerar JSON de tradução para revisão

```bash
python3 scripts/prepare_translation_drafts.py \
  "$HOME/.steam/debian-installation/steamapps/common/TOI/TalesOfMortal_i18N_Extracted/runtime.json" \
  dist/extracted/offline.json
```

Os rascunhos vão para `dist/drafts/`, separados por módulo identificado. Exemplo:

```json
{
  "module": {
    "kind": "mod",
    "id": "steam:2814722600",
    "name": "SectAdmin"
  },
  "translations": {
    "Recruit Disciple": "",
    "招募弟子": ""
  },
  "keys": {},
  "reviewNote": "Os valores vazios estão pendentes de tradução."
}
```

Substitua os valores vazios pelos textos PT-BR. O gerador preserva traduções já preenchidas em rascunhos existentes. Ele **não altera nenhum arquivo carregado pelo jogo**. Os textos já traduzidos e nomes próprios conhecidos são filtrados.

Depois da revisão, migre os pares traduzidos para o JSON correto dentro de `mod/i18n/pt-BR`, de preferência para o arquivo cujo `module.id` corresponda ao rascunho. Não copie todos os rascunhos diretamente para essa pasta, pois um `module.id` duplicado é inválido na auditoria.

Para textos capturados durante o jogo, a origem está identificada como `capture:runtime-unattributed`, porque o hook global não sabe com certeza qual mod originou a string. Avalie os textos antes de classificá-los como jogo ou um mod.

## 4. Idiomas e identificação

- `zh-Hans`: indícios de chinês simplificado
- `zh-Hant`: indícios de chinês tradicional
- `zh-und`: caracteres chineses comuns aos dois sistemas, sem distinção confiável
- `zh-mixed`: indícios simultâneos das duas escritas
- `en-candidate`: letras latinas possivelmente em inglês, mas também podem ser português, nomes ou pinyin

As classes são heurísticas. A captura pode incluir nomes próprios, NPCs gerados ou textos que não devem ser traduzidos. Os nomes conhecidos da lista `protected-names.json` são excluídos por correspondência exata; isso **não protege automaticamente todos os nomes gerados**. Revise os rascunhos antes de adicioná-los ao mod.

## 5. Testes

```bash
bash scripts/test.sh
python3 -m unittest discover -s tests -p 'test_*.py'
```

Os testes validam a gravação JSON pelo C#, textos Unicode, origem por diretório, detecção de arquivos binários, geração de rascunhos e preservação das traduções revisadas. Ainda é necessário testar a coleta ao vivo no seu jogo e confirmar os hooks disponíveis.
