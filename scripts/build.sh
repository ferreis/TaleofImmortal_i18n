#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT="$ROOT/src/TalesOfMortal_i18N/TalesOfMortal_i18N.csproj"
GAME="${1:-${GAME_ROOT:-}}"

if [[ -z "$GAME" ]]; then
  for candidate in \
    "$HOME/.steam/debian-installation/steamapps/common/TOI" \
    "$HOME/.local/share/Steam/steamapps/common/TOI" \
    "$HOME/.steam/steam/steamapps/common/TOI" \
    "$HOME/.steam/debian-installation/steamapps/common/guigubahuang" \
    "$HOME/.local/share/Steam/steamapps/common/guigubahuang" \
    "$HOME/.steam/debian-installation/steamapps/common/鬼谷八荒" \
    "$HOME/.local/share/Steam/steamapps/common/鬼谷八荒"; do
    if [[ -f "$candidate/MelonLoader/Managed/Assembly-CSharp.dll" ]]; then
      GAME="$candidate"
      break
    fi
  done
fi

if [[ -z "$GAME" || ! -d "$GAME" ]]; then
  echo "ERRO: pasta do jogo não encontrada. Informe o caminho completo:" >&2
  echo "  bash scripts/build.sh '/caminho/para/TOI'" >&2
  exit 1
fi
GAME="$(cd "$GAME" && pwd -P)"

required=(
  "MelonLoader/0Harmony.dll"
  "MelonLoader/Managed/Assembly-CSharp.dll"
  "MelonLoader/Managed/Il2Cppmscorlib.dll"
  "MelonLoader/Managed/Newtonsoft.Json.dll"
  "MelonLoader/Managed/UnityEngine.dll"
  "MelonLoader/Managed/UnityEngine.CoreModule.dll"
  "MelonLoader/Managed/UnityEngine.UI.dll"
  "MelonLoader/Managed/Unity.TextMeshPro.dll"
)
missing=0
for relative in "${required[@]}"; do
  if [[ ! -f "$GAME/$relative" ]]; then
    echo "DLL ausente: $GAME/$relative" >&2
    missing=1
  fi
done
if ((missing)); then
  echo "ERRO: as referências não estão nos caminhos esperados pelo .csproj." >&2
  echo "Confira MelonLoader/Managed e a versão do jogo antes de compilar." >&2
  exit 1
fi

if command -v msbuild >/dev/null 2>&1; then
  compiler=msbuild
elif command -v xbuild >/dev/null 2>&1; then
  compiler=xbuild
else
  echo "ERRO: compilador não encontrado. No Ubuntu: sudo apt install mono-devel mono-xbuild" >&2
  exit 1
fi

echo "Projeto: $PROJECT"
echo "Instalação do jogo: $GAME"
echo "Compilador: $compiler"
# Compatibilidade com versões de Mono xbuild que não suportam a opção 7.3.
"$compiler" "$PROJECT" /p:Configuration=Release "/p:GameRoot=$GAME" /p:LangVersion=7.2 /verbosity:minimal

OUTPUT="$ROOT/src/TalesOfMortal_i18N/bin/Release/TalesOfMortalI18N.dll"
if [[ ! -f "$OUTPUT" ]]; then
  echo "ERRO: compilação não produziu $OUTPUT" >&2
  exit 1
fi
printf '\nDLL compilada: %s\n' "$OUTPUT"
echo "Empacote a DLL como ModCode pelo Mod Creator nativo do jogo."
