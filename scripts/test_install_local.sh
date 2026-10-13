#!/usr/bin/env bash
# Integração real: instalação inicial e atualização, sem jogo/Steam instalados.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
GAME="$WORK/Steam Library/TOI"
mkdir -p "$GAME"

bash "$ROOT/scripts/install-local.sh" "$GAME"
TARGET="$GAME/ModExportData/Mod_DQKLF9"
CACHE="$TARGET/ModExportData.cache"
DLL="$TARGET/ModCode/dll/MOD_DQKLF9.dll"
[[ -s "$CACHE" && -s "$DLL" && -s "$TARGET/ModAssets/i18n/pt-BR/game.json" ]]
python3 - "$CACHE" "$ROOT" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[2])
from scripts.prepare_export_cache import parse_export_cache
from scripts.toi_crypto import MAGIC
raw = Path(sys.argv[1]).read_bytes()
assert raw.startswith(MAGIC), "ModExportData.cache precisa do formato cifrado nativo"
data = parse_export_cache(raw)
assert data["projectData"]["soleID"] == "DQKLF9", data
assert data["modNamespace"] == "MOD_DQKLF9", data
assert data["items"] == {}, data
print("OK: cache nativo válido para DQKLF9")
PY

CACHE_SHA="$(sha256sum "$CACHE" | cut -d' ' -f1)"
bash "$ROOT/scripts/install-local.sh" "$GAME"
[[ "$CACHE_SHA" == "$(sha256sum "$CACHE" | cut -d' ' -f1)" ]]
[[ -s "$DLL" && -s "$TARGET/ModAssets/i18n/config.json" ]]

echo "InstallLocalSmoke OK: instalação inicial e atualização preservando o cache."
