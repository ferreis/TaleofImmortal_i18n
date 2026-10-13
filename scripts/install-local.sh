#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GAME="${1:-$HOME/.steam/debian-installation/steamapps/common/TOI}"
GAME="${GAME%/}"

if [[ ! -d "$GAME" ]]; then
  echo "ERRO: pasta do jogo inexistente: $GAME" >&2
  echo "Uso: bash scripts/install-local.sh '/caminho/para/TOI'" >&2
  exit 1
fi

if pgrep -fi '(^|/)(TOI.exe|guigubahuang.exe)( |$)' >/dev/null; then
  echo "ERRO: feche completamente o Tale of Immortal antes da instalação." >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERRO: Python 3 é necessário para criar o cache de exportação nativo." >&2
  exit 1
fi

LOCAL_MOD="$GAME/ModExportData/Mod_DQKLF9"
METADATA="$ROOT/ModProject_DQKLF9/ModProject"
TARGET="$LOCAL_MOD/ModCode/dll/MOD_DQKLF9.dll"
ASSETS="$LOCAL_MOD/ModAssets/i18n"
OUTPUT="$METADATA/ModCode/ModMain/bin/Release/MOD_DQKLF9.dll"

if [[ -L "$GAME/ModExportData" || -L "$LOCAL_MOD" ]]; then
  echo "ERRO: caminho de instalação é um link simbólico; operação recusada." >&2
  exit 1
fi
if [[ -e "$LOCAL_MOD" && ! -d "$LOCAL_MOD" ]]; then
  echo "ERRO: já existe um arquivo onde o diretório do mod seria instalado: $LOCAL_MOD" >&2
  exit 1
fi

if [[ -d "$LOCAL_MOD" ]]; then
  OPERATION="atualizada"
else
  OPERATION="criada"
fi

echo "Compilando o projeto DQKLF9..."
bash "$ROOT/scripts/build.sh"

# Um cache exportado de verdade possui projectData, items e modNamespace e
# é armazenado no formato criptografado nativo. Não é um ModProject.cache
# renomeado. Gerar esse arquivo dispensa a importação manual pelo jogo.
mkdir -p "$LOCAL_MOD"
python3 "$ROOT/scripts/prepare_export_cache.py" \
  --source "$METADATA" \
  --output "$LOCAL_MOD/ModExportData.cache"

# Estes metadados extras são úteis para diagnóstico/edição. Se já existirem,
# não alterar os arquivos criados pelo editor do jogo.
for cache in ModProject.cache ModData.cache; do
  if [[ ! -e "$LOCAL_MOD/$cache" ]]; then
    cp "$METADATA/$cache" "$LOCAL_MOD/$cache"
  fi
done

mkdir -p "$(dirname "$TARGET")" "$ASSETS"

# Backup apenas se a DLL anterior realmente diferir da versão compilada.
if [[ -f "$TARGET" ]] && ! cmp -s "$TARGET" "$OUTPUT"; then
  STAMP="$(date +%Y%m%d-%H%M%S)"
  BACKUP="$TARGET.backup-$STAMP"
  if [[ -e "$BACKUP" ]]; then
    BACKUP="$BACKUP-$$"
  fi
  cp -p "$TARGET" "$BACKUP"
  echo "Backup da DLL anterior: $BACKUP"
fi

cp "$OUTPUT" "$TARGET"
cp -a "$ROOT/mod/i18n/." "$ASSETS/"

if [[ ! -s "$TARGET" || ! -s "$LOCAL_MOD/ModExportData.cache" ||
      ! -f "$ASSETS/config.json" || ! -d "$ASSETS/pt-BR" ]]; then
  echo "ERRO: arquivos obrigatórios não foram instalados corretamente." >&2
  exit 1
fi

echo
echo "Instalação $OPERATION: $LOCAL_MOD"
echo "DLL: $TARGET"
echo "Traduções: $ASSETS"
echo "Cache do jogo: $LOCAL_MOD/ModExportData.cache"
echo "Abra o jogo. Se for a primeira instalação, ative DQKLF9 em Mods > Mods locais."
echo "Log de diagnóstico: $GAME/TalesOfMortal_i18N.log"
echo "O instalador não modifica o XUnity nem outros mods."
