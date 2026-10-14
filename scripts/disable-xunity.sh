#!/usr/bin/env bash
set -euo pipefail

GAME="${1:-$HOME/.steam/debian-installation/steamapps/common/TOI}"
if [[ ! -d "$GAME" ]]; then
  echo "ERRO: pasta do jogo não encontrada: $GAME" >&2
  echo "Uso: bash scripts/disable-xunity.sh '/caminho/para/TOI'" >&2
  exit 1
fi

if pgrep -fi '(^|/)(TOI.exe|guigubahuang.exe)( |$)' >/dev/null; then
  echo "ERRO: feche completamente o jogo antes de desativar o XUnity." >&2
  exit 1
fi

count=0
# Mude somente o plugin de entrada, jamais UserLibs/XUnity.Common.dll
# ou XUnity.ResourceRedirector.dll, pois outras extensões podem usá-los.
if [[ -d "$GAME/Mods" ]]; then
  while IFS= read -r -d '' dll; do
    if [[ ! -e "$dll.disabled" ]]; then
      mv -- "$dll" "$dll.disabled"
      echo "Desativado: $dll"
      count=$((count + 1))
    fi
  done < <(find "$GAME/Mods" -type f -name 'XUnity.AutoTranslator.Plugin.MelonMod.dll' -print0)
fi

if [[ -d "$GAME/BepInEx/plugins" ]]; then
  while IFS= read -r -d '' dll; do
    if [[ ! -e "$dll.disabled" ]]; then
      mv -- "$dll" "$dll.disabled"
      echo "Desativado: $dll"
      count=$((count + 1))
    fi
  done < <(find "$GAME/BepInEx/plugins" -type f \( -name 'XUnity.AutoTranslator.Plugin.BepInEx.dll' -o -name 'XUnity.AutoTranslator.Plugin.BepInEx.IL2CPP.dll' \) -print0)
fi

echo "$count carregador(es) do XUnity desativado(s) nesta instalação."
echo "Nenhum TXT de tradução foi apagado."
echo "Reinicie o jogo e execute bash scripts/check-xunity.sh para conferir."
