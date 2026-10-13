#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NATIVE="$ROOT/ModProject_DQKLF9/ModProject/ModCode/ModMain"
SOURCE="$ROOT/src/TalesOfMortal_i18N"
OUTPUT="$NATIVE/bin/Release/MOD_DQKLF9.dll"
DEBUG="$ROOT/ModProject_DQKLF9/debug/Mod_DQKLF9"
DIST="$ROOT/dist/TalesOfMortal_i18N"

# No Unity, Harmony, Steam or game installation required to build.
if command -v mcs >/dev/null 2>&1; then
  echo "Compilando MOD_DQKLF9.dll offline com Mono..."
  mkdir -p "$NATIVE/bin/Release"
  mcs -sdk:4.7.2 -langversion:7.2 -target:library -optimize+ \
    -r:System.Core -r:System.Runtime.Serialization \
    -out:"$OUTPUT" \
    "$NATIVE/ModMain.cs" \
    "$NATIVE/Properties/AssemblyInfo.cs" \
    "$SOURCE/ModMain.cs" \
    "$SOURCE/TranslationCatalog.cs" \
    "$SOURCE/TranslationPatches.cs"
elif command -v msbuild >/dev/null 2>&1; then
  msbuild "$NATIVE/ModMain.csproj" /p:Configuration=Release /verbosity:minimal
elif command -v xbuild >/dev/null 2>&1; then
  xbuild "$NATIVE/ModMain.csproj" /p:Configuration=Release /verbosity:minimal
else
  echo "ERRO: compilador Mono não encontrado. Instale mono-devel." >&2
  exit 1
fi

if [[ ! -s "$OUTPUT" ]]; then
  echo "ERRO: não foi gerada a DLL $OUTPUT" >&2
  exit 1
fi

# Prepare native project and debug layout; keep one authoritative copy in mod/i18n.
mkdir -p "$ROOT/ModProject_DQKLF9/ModProject/i18n"
cp -a "$ROOT/mod/i18n/." "$ROOT/ModProject_DQKLF9/ModProject/i18n/"
mkdir -p "$DEBUG/ModCode/dll" "$DEBUG/i18n"
cp "$OUTPUT" "$DEBUG/ModCode/dll/MOD_DQKLF9.dll"
cp -a "$ROOT/mod/i18n/." "$DEBUG/i18n/"

# Portable staging directory (not a substitute for Mod Creator metadata/export).
mkdir -p "$DIST/ModCode/dll" "$DIST/i18n"
cp "$OUTPUT" "$DIST/ModCode/dll/MOD_DQKLF9.dll"
cp -a "$ROOT/mod/i18n/." "$DIST/i18n/"

echo
echo "BUILD OK: $OUTPUT"
echo "DEBUG: $DEBUG"
echo "PACOTE STAGING: $DIST"
echo "O projeto fonte está pronto para exportação pelo Mod Creator."
