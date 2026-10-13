#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NATIVE="$ROOT/ModProject_DQKLF9/ModProject/ModCode/ModMain"
SOURCE="$ROOT/src/TalesOfMortal_i18N"
OUTPUT="$NATIVE/bin/Release/MOD_DQKLF9.dll"
DEBUG="$ROOT/ModProject_DQKLF9/debug/Mod_DQKLF9"
DIST="$ROOT/dist/TalesOfMortal_i18N"

# The cached native mod identity must match our exported entry point.
METADATA="$ROOT/ModProject_DQKLF9/ModProject"
if [[ ! -f "$METADATA/ModProject.cache" || ! -f "$METADATA/ModData.cache" ]]; then
  echo "ERRO: metadados do Mod Creator ausentes em $METADATA" >&2
  exit 1
fi
if ! grep -Eq '"soleID"[[:space:]]*:[[:space:]]*"DQKLF9"' "$METADATA/ModProject.cache" ||
   ! grep -Eq '"modNamespace"[[:space:]]*:[[:space:]]*"MOD_DQKLF9"' "$METADATA/ModData.cache"; then
  echo "ERRO: identidades DQKLF9 / MOD_DQKLF9 inconsistentes nos arquivos .cache" >&2
  exit 1
fi

# No Unity, Harmony, Steam or game installation required to build.
if command -v mcs >/dev/null 2>&1; then
  echo "Compilando MOD_DQKLF9.dll offline com Mono..."
  mkdir -p "$NATIVE/bin/Release"
  mcs -sdk:4.7.2 -langversion:7.2 -target:library -optimize+ \
    -r:System.Core \
    -out:"$OUTPUT" \
    "$NATIVE/ModMain.cs" \
    "$NATIVE/Properties/AssemblyInfo.cs" \
    "$SOURCE/ModMain.cs" \
    "$SOURCE/TranslationCatalog.cs" \
    "$SOURCE/JsonTextParser.cs" \
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

# Files under ModAssets are included in the Mod Creator export.
MOD_ASSETS="$ROOT/ModProject_DQKLF9/ModProject/ModAssets/i18n"
mkdir -p "$MOD_ASSETS"
cp -a "$ROOT/mod/i18n/." "$MOD_ASSETS/"

# Prepare native project and debug layout; keep one authoritative copy in mod/i18n.
mkdir -p "$ROOT/ModProject_DQKLF9/ModProject/i18n"
cp -a "$ROOT/mod/i18n/." "$ROOT/ModProject_DQKLF9/ModProject/i18n/"
mkdir -p "$DEBUG/ModCode/dll" "$DEBUG/ModAssets/i18n"
cp "$OUTPUT" "$DEBUG/ModCode/dll/MOD_DQKLF9.dll"
cp -a "$ROOT/mod/i18n/." "$DEBUG/ModAssets/i18n/"
cp "$METADATA/ModProject.cache" "$DEBUG/ModProject.cache"
cp "$METADATA/ModData.cache" "$DEBUG/ModData.cache"

# Portable staging directory (not a substitute for Mod Creator metadata/export).
mkdir -p "$DIST/ModCode/dll" "$DIST/ModAssets/i18n"
cp "$OUTPUT" "$DIST/ModCode/dll/MOD_DQKLF9.dll"
cp -a "$ROOT/mod/i18n/." "$DIST/ModAssets/i18n/"
cp "$METADATA/ModProject.cache" "$DIST/ModProject.cache"
cp "$METADATA/ModData.cache" "$DIST/ModData.cache"

echo
echo "BUILD OK: $OUTPUT"
echo "DEBUG: $DEBUG"
echo "PACOTE STAGING: $DIST"
echo "O projeto fonte está pronto para exportação pelo Mod Creator."
