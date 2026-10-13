#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT="$ROOT/src/TalesOfMortal_i18N"
OUTPUT="$PROJECT/bin/Release/TalesOfMortalI18N.dll"

# Compilação totalmente offline e independente da instalação do jogo.
# A única dependência é o Mono, já instalado no ambiente Ubuntu do projeto.
if command -v mcs >/dev/null 2>&1; then
  mkdir -p "$PROJECT/bin/Release"
  echo "Compilando com Mono mcs (sem DLLs do jogo)..."
  mcs -sdk:4.7.2 -langversion:7.2 -target:library -optimize+ \
    -r:System.Core -r:System.Runtime.Serialization \
    -out:"$OUTPUT" \
    "$PROJECT/ModMain.cs" \
    "$PROJECT/TranslationCatalog.cs" \
    "$PROJECT/TranslationPatches.cs"
elif command -v msbuild >/dev/null 2>&1; then
  echo "Compilando com MSBuild (sem DLLs do jogo)..."
  msbuild "$PROJECT/TalesOfMortal_i18N.csproj" /p:Configuration=Release /verbosity:minimal
elif command -v xbuild >/dev/null 2>&1; then
  echo "Compilando com xbuild (sem DLLs do jogo)..."
  xbuild "$PROJECT/TalesOfMortal_i18N.csproj" /p:Configuration=Release /verbosity:minimal
else
  echo "ERRO: compilador Mono não encontrado. Execute: sudo apt install mono-devel" >&2
  exit 1
fi

if [[ ! -f "$OUTPUT" ]]; then
  echo "ERRO: DLL não encontrada após compilar: $OUTPUT" >&2
  exit 1
fi

echo "Compilação concluída: $OUTPUT"
echo "Não é necessário ter Tale of Immortal instalado para compilar."
echo "O mod ainda exige o runtime do jogo e Harmony para funcionar em execução."
