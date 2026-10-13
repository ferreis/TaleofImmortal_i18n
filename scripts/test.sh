#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
if ! command -v mcs >/dev/null || ! command -v mono >/dev/null; then
  echo "Mono necessário para executar o teste: sudo apt install mono-devel" >&2
  exit 1
fi

cp -a "$ROOT/mod/i18n" "$WORK/i18n"
mcs -sdk:4.7.2 -langversion:7.2 -target:exe \
  -r:System.Core -r:System.Runtime.Serialization \
  -out:"$WORK/CatalogSmoke.exe" \
  "$ROOT/src/TalesOfMortal_i18N/ModMain.cs" \
  "$ROOT/src/TalesOfMortal_i18N/TranslationCatalog.cs" \
  "$ROOT/src/TalesOfMortal_i18N/TranslationPatches.cs" \
  "$ROOT/tests/CatalogSmoke.cs"
mono "$WORK/CatalogSmoke.exe"
