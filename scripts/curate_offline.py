#!/usr/bin/env python3
"""Separa textos localizáveis dos dados técnicos de uma extração offline.

Lê LocalText.json (en/ch/tc/key) e opções chinesas de ModAssets/Config.json.
Não transforma dados arbitrários, scripts, documentação ou nomes de NPC em
traduções. A saída fica fora de i18n para revisão humana.
"""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

LOCALIZED = re.compile(r"^\\$\\[(\\d+)\\]\\.(en|ch|tc|key)$")
CHINESE = re.compile(r"[\\u3400-\\u9fff\\uf900-\\ufaff]")
FIELD = {"en": "english", "ch": "simplified", "tc": "traditional", "key": "key"}


def curate(doc):
    result = {}
    selected = 0
    for catalog in doc.get("catalogs", []):
        mod = catalog["module"]
        mid = mod["id"]
        for entry in catalog.get("entries", []):
            accepted = False
            for loc in entry.get("locations", []):
                path, context = loc.get("file", ""), loc.get("context", "")
                match = LOCALIZED.fullmatch(context)
                if (match and path.endswith("/ModExcel/LocalText.json") and
                        not path.startswith("Mod/modFQA/")):
                    group = result.setdefault(mid, {"module": mod, "rows": {},
                                                     "configLabels": {}})
                    row_key = (path, int(match.group(1)))
                    row = group["rows"].setdefault(row_key, {
                        "sourceFile": path, "row": row_key[1]})
                    row[FIELD[match.group(2)]] = entry["text"]
                    accepted = True
                elif (path.endswith("/ModAssets/Config.json") and
                      context == "$.<key>" and CHINESE.search(entry["text"])):
                    group = result.setdefault(mid, {"module": mod, "rows": {},
                                                     "configLabels": {}})
                    group["configLabels"][entry["text"]] = ""
                    accepted = True
            if accepted:
                selected += 1

    catalogs = []
    total_rows = 0
    config_count = 0
    for mid, data in sorted(result.items()):
        rows = sorted(data["rows"].values(), key=lambda x:
                      (x["sourceFile"], x["row"]))
        total_rows += len(rows)
        config_count += len(data["configLabels"])
        catalogs.append({
            "module": data["module"], "rows": rows,
            "configLabels": dict(sorted(data["configLabels"].items())),
        })
    return {
        "format": "talesofmortal-curated-v1",
        "notice": "Candidatos somente. Não incluir diretamente em traduções.",
        "stats": {
            "input_unique": doc.get("stats", {}).get("entries_unique"),
            "selected_entries": selected,
            "localization_rows": total_rows,
            "config_labels": config_count,
        },
        "catalogs": catalogs,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path, help="offline.json")
    ap.add_argument("--output", type=Path, default=Path("dist/extracted/offline_curado.json"))
    args = ap.parse_args()
    with args.input.open(encoding="utf-8") as file:
        parsed = json.load(file)
    if parsed.get("format") != "talesofmortal-extraction-v1":
        ap.error("Formato do offline.json inválido.")
    curated = curate(parsed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(curated, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps(curated["stats"], ensure_ascii=False, indent=2))
    print("Arquivo de revisão:", args.output)


if __name__ == "__main__":
    main()
