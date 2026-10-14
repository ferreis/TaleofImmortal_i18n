#!/usr/bin/env python3
"""Auditoria estrutural de todos os catálogos externos de tradução."""
import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

PH = re.compile(r"\{\d+(?::[^}]*)?\}")
TAG = re.compile(r"</?(?:b|i|u|color|size)\b[^>]*>", re.I)

def run(directory, output=None):
    data = []
    identities = {}
    translations = defaultdict(list)
    warnings = []
    failures = []

    for path in sorted(directory.rglob("*.json")):
        name = path.name
        try:
            doc = json.loads(path.read_text(encoding="utf-8-sig"))
            if not isinstance(doc, dict):
                raise ValueError("a raiz precisa ser um objeto JSON")
            mod = doc.get("module")
            if not isinstance(mod, dict):
                raise ValueError("module não encontrado")
            kind, modid = mod.get("kind"), mod.get("id")
            if kind not in {"game", "mod", "fallback", "names"} or not isinstance(modid, str) or not modid:
                raise ValueError("module.kind ou module.id inválidos")
            if modid in identities:
                failures.append({"type": "duplicate-module-id", "file": name,
                                 "other": identities[modid], "id": modid})
            identities[modid] = name

            fields = {}
            for field in ("translations", "keys"):
                raw = doc.get(field, {})
                if not isinstance(raw, dict) or not all(isinstance(k, str) and isinstance(v, str)
                                                       for k, v in raw.items()):
                    raise ValueError(field + " deve conter pares de strings")
                fields[field] = raw
            patterns = doc.get("patterns", [])
            if not isinstance(patterns, list):
                raise ValueError("patterns precisa ser uma lista")
            if kind == "names":
                names = doc.get("names")
                if not isinstance(names, list) or not all(isinstance(n, str) for n in names):
                    raise ValueError("names deve conter uma lista de strings")
            else:
                names = []

            for key, value in fields["translations"].items():
                translations[key].append((modid, name, value))
                original = Counter(PH.findall(key))
                target = Counter(PH.findall(value))
                if original != target:
                    warnings.append({"type": "placeholder-mismatch", "file": name,
                                     "source": key[:130], "source_placeholders": dict(original),
                                     "target_placeholders": dict(target)})
                for tag in ("b", "i", "u", "color", "size"):
                    op = re.compile(r"<" + tag + r"(?:\s[^>]*)?>", re.I)
                    cl = re.compile(r"</" + tag + r">", re.I)
                    if op.findall(key) and not op.findall(value):
                        warnings.append({"type": "tag-missing", "file": name,
                                         "tag": tag, "source": key[:110]})
            if not fields["translations"] and not fields["keys"] and not patterns and kind == "mod":
                warnings.append({"type": "empty-mod-catalog", "file": name, "id": modid})

            data.append({"file": name, "module": mod,
                         "translations": len(fields["translations"]), "keys": len(fields["keys"]),
                         "patterns": len(patterns), "protected_names": len(names)})
        except Exception as error:
            failures.append({"type": "invalid-file", "file": name, "error": str(error)})

    collisions = []
    for text, origins in translations.items():
        different = {v for _, _, v in origins}
        if len(different) > 1:
            collisions.append({"original": text[:160],
                               "alternatives": [{"id": mid, "file": file, "translation": value[:160]}
                                                for mid, file, value in origins[:6]]})
    summary = {
        "files": len(data), "translations": sum(x["translations"] for x in data),
        "keys": sum(x["keys"] for x in data),
        "patterns": sum(x["patterns"] for x in data),
        "protected_names": sum(x["protected_names"] for x in data),
        "unique_source_texts": len(translations),
        "collisions": len(collisions),
        "warnings": len(warnings),
        "failures": len(failures)
    }
    report = {"summary": summary, "catalogs": data, "collisions": collisions,
              "warnings": warnings, "failures": failures}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    for error in failures[:10]:
        print("ERRO:", json.dumps(error, ensure_ascii=False))
    for item in warnings[:8]:
        print("REVISAR:", json.dumps(item, ensure_ascii=False))
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")
        print("Relatório completo:", output)
    return 1 if failures else 0

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--folder", type=Path, default=Path(__file__).resolve().parents[1] /
                   "mod/i18n/pt-BR")
    p.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] /
                   "dist/TalesOfMortal_i18N/catalog-audit.json")
    a = p.parse_args()
    raise SystemExit(run(a.folder, a.output))
