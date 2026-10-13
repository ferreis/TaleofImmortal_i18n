#!/usr/bin/env bash
set -euo pipefail

GAME="${1:-$HOME/.steam/debian-installation/steamapps/common/TOI}"
if [[ ! -d "$GAME" ]]; then
  echo "Pasta do jogo não localizada: $GAME" >&2
  echo "Execute: bash scripts/check-xunity.sh '/caminho/steamapps/common/TOI'" >&2
  exit 1
fi

echo "=== Arquivos de entrada do XUnity potencialmente ativos ==="
find "$GAME/Mods" "$GAME/Plugins" "$GAME/BepInEx/plugins" \
  -maxdepth 6 -type f \( -iname '*XUnity*Translator*.dll*' -o -iname '*AutoTranslator*.dll*' \) -print 2>/dev/null || true
echo
echo "=== Último log do MelonLoader ==="
if [[ -d "$GAME/MelonLoader/Logs" ]]; then
  latest="$(find "$GAME/MelonLoader/Logs" -maxdepth 1 -type f \( -iname '*.log' -o -iname '*.txt' \) -printf '%T@ %p\n' | sort -rn | head -1 | cut -d' ' -f2-)"
  if [[ -n "$latest" ]]; then
    echo "Arquivo: $latest"
    grep -iE 'XUnity|AutoTranslator|Tales of Mortal i18N|MOD_DQKLF9|Harmony|Hook indisponível' "$latest" | tail -n 100 || true
  else
    echo "Nenhum log encontrado."
  fi
else
  echo "MelonLoader/Logs não encontrado."
fi
echo "Arquivos intactos. Este script não altera o jogo."
