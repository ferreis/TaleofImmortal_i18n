#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GAME="${1:-$HOME/.steam/debian-installation/steamapps/common/TOI}"

if [[ ! -d "$GAME" ]]; then
  echo "ERRO: pasta do jogo inexistente: $GAME" >&2
  echo "Uso: bash scripts/install-local.sh '/caminho/para/TOI'" >&2
  exit 1
fi

if pgrep -fi '(^|/)(TOI.exe|guigubahuang.exe)( |$)' >/dev/null; then
  echo "ERRO: feche completamente o Tale of Immortal antes da instalação." >&2
  exit 1
fi

LOCAL_MOD="$GAME/ModExportData/Mod_DQKLF9"
if [[ ! -d "$LOCAL_MOD" ]]; then
  echo "ERRO: não encontrei o mod importado em $LOCAL_MOD" >&2
  echo "Faça a importação local pelo menu do jogo uma vez e execute novamente." >&2
  exit 1
fi

if [[ ! -f "$LOCAL_MOD/ModExportData.cache" ]]; then
  echo "ERRO: diretório não tem ModExportData.cache, não é uma instalação local confirmada." >&2
  exit 1
fi

bash "$ROOT/scripts/build.sh"
OUTPUT="$ROOT/ModProject_DQKLF9/ModProject/ModCode/ModMain/bin/Release/MOD_DQKLF9.dll"
TARGET="$LOCAL_MOD/ModCode/dll/MOD_DQKLF9.dll"
ASSETS="$LOCAL_MOD/ModAssets/i18n"
STAMP="$(date +%Y%m%d-%H%M%S)"
if [[ -f "$TARGET" ]]; then
  cp -p "$TARGET" "$TARGET.backup-$STAMP"
  echo "Backup da DLL anterior: $TARGET.backup-$STAMP"
fi

mkdir -p "$(dirname "$TARGET")" "$ASSETS"
cp "$OUTPUT" "$TARGET"
cp -a "$ROOT/mod/i18n/." "$ASSETS/"

echo
echo "Instalação atualizada: $LOCAL_MOD"
echo "DLL: $TARGET"
echo "Traduções: $ASSETS"
echo "Abra o jogo com DQKLF9 ativado e verifique:"
echo "  $GAME/TalesOfMortal_i18N.log"
echo "O instalador não modifica o XUnity."
