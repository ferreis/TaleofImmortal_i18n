#!/usr/bin/env python3
"""Cria rascunhos PT-BR a partir do extrator de jogo e do scanner offline.

É intencional que os rascunhos fiquem em dist/drafts, FORA dos JSON carregados
pelo mod. Cada entrada nova contém valor vazio para revisão/tradução manual.
Rascunhos existentes são mesclados sem sobrescrever traduções já preenchidas.
"""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

def slug(text):
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", text)[:100] or "unknown"

def known_sources(folder):
    existing, protected = set(), set()
    for file in folder.glob("*.json"):
        try:
            obj = json.loads(file.read_text(encoding="utf-8-sig"))
            existing.update(obj.get("translations", {}))
            if isinstance(obj.get("names"), list):
                protected.update(str(v) for v in obj["names"] if isinstance(v, str))
        except (OSError, json.JSONDecodeError):
            continue
    return existing, protected

def load_inputs(paths, existing, protected):
    groups = defaultdict(dict)
    details = {}
    ignored = 0
    for source_file in paths:
        raw = json.loads(source_file.read_text(encoding="utf-8-sig"))
        if raw.get("format") != "talesofmortal-extraction-v1":
            raise ValueError("Formato de extração não reconhecido: " + str(source_file))

        if isinstance(raw.get("catalogs"), list):
            catalogs = raw["catalogs"]
        else:
            catalogs = [{
                "module": {
                    "kind": "mod",
                    "id": "capture:runtime-unattributed",
                    "name": "Textos capturados em jogo - origem incerta"
                },
                "entries": raw.get("entries", []),
            }]
        for package in catalogs:
            mod = package.get("module", {})
            mod_id = mod.get("id")
            if not isinstance(mod_id, str) or not mod_id:
                raise ValueError("Pacote de extração sem module.id")
            meta = details.get(mod_id)
            if meta is None:
                meta = dict(mod)
                if meta.get("kind") not in {"game", "mod", "fallback"}:
                    meta["kind"] = "mod"
                details[mod_id] = meta
            for item in package.get("entries", []):
                if not isinstance(item, dict):
                    continue
                text = item.get("text")
                if not isinstance(text, str) or not text.strip() or text in existing or text in protected:
                    ignored += 1
                    continue
                groups[mod_id][text] = ""
    return groups, details, ignored

def prepare(sources, known, output):
    existing, protected = known_sources(known)
    groups, details, ignored = load_inputs(sources, existing, protected)
    output.mkdir(parents=True, exist_ok=True)
    result = []
    for mod_id, translations in sorted(groups.items()):
        target = output / (slug(mod_id) + ".json")
        saved = {}
        if target.exists():
            previous = json.loads(target.read_text(encoding="utf-8-sig"))
            if previous.get("module", {}).get("id") != mod_id:
                raise ValueError("Rascunho anterior com ID diferente: " + str(target))
            saved = previous.get("translations", {})
            if not isinstance(saved, dict):
                raise ValueError("translations inválido no rascunho " + str(target))
        merged = dict(translations)
        merged.update(saved)  # Traduções humanas sempre têm precedência.
        target.write_text(json.dumps({
            "module": details[mod_id],
            "translations": dict(sorted(merged.items())),
            "keys": {},
            "reviewNote": "Os valores vazios estão pendentes de tradução. Revise nomes de NPCs.",
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        result.append({"file": str(target), "total": len(merged),
                       "translated": sum(bool(v) for v in merged.values())})
    return {"files": result, "ignored_previously_known_or_protected": ignored}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("extractions", nargs="+", type=Path,
                   help="JSON runtime.json ou offline.json (um ou mais)")
    p.add_argument("--known", type=Path,
                   default=Path(__file__).resolve().parents[1] / "mod/i18n/pt-BR")
    p.add_argument("--output", type=Path,
                   default=Path(__file__).resolve().parents[1] / "dist/drafts")
    args = p.parse_args()
    result = prepare(args.extractions, args.known, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
