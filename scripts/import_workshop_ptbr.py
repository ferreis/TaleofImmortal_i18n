#!/usr/bin/env python3
"""Importa a tradução do Workshop 2990310797 a partir de seu JSON extraído.

O resultado é fallback: traduções revisadas do jogo e de outros mods têm
precedência. Protege nomes, ignora fontes chinesas ambíguas e verifica
marcadores {variavel}. Os arquivos originais da Steam nunca são modificados.
"""
import argparse
import collections
import json
import re
import shutil
from pathlib import Path

try:
    from .audit_terminology import CANONICAL
except ImportError:
    from audit_terminology import CANONICAL

ROOT = Path(__file__).resolve().parents[1]
SOURCE_MOD = "steam:2990310797"
HAN = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]")
PLACEHOLDER = re.compile(r"\{[^{}]+\}")
INTERNAL_VAR = re.compile(r"\$s_[^$\r\n]{1,140}\$|&[A-Za-z0-9_/%+|.?:=-]{1,140}&")
RICH_TAG = re.compile(r"<(color|size|b|i|u|link|sprite)\b", re.I)
SPRITE = re.compile(r'<sprite\s+name="([^"]+)"', re.I)


def structural_problem(source, translated):
    if (collections.Counter(PLACEHOLDER.findall(source)) !=
            collections.Counter(PLACEHOLDER.findall(translated))):
        return "placeholderMismatch"
    if (collections.Counter(INTERNAL_VAR.findall(source)) !=
            collections.Counter(INTERNAL_VAR.findall(translated))):
        return "internalVariableMismatch"
    if collections.Counter(x.lower() for x in RICH_TAG.findall(source)) != (
            collections.Counter(x.lower() for x in RICH_TAG.findall(translated))):
        return "richTextMismatch"
    if collections.Counter(SPRITE.findall(source)) != collections.Counter(
            SPRITE.findall(translated)):
        return "spriteMismatch"
    return None


def existing_catalogs(folder, output):
    texts, keys, protected = set(), set(), set()
    if not folder.is_dir():
        return texts, keys, protected
    for path in folder.glob("*.json"):
        if path.resolve() == output.resolve():
            continue
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        texts.update(data.get("translations", {}).keys())
        keys.update(data.get("keys", {}).keys())
        protected.update(s for s in data.get("names", []) if isinstance(s, str))
    return texts, keys, protected


def prepare(source, catalog_dir, output):
    if source.resolve() == output.resolve():
        raise ValueError("A origem e a saída não podem ser o mesmo arquivo.")
    data = json.loads(source.read_text(encoding="utf-8-sig"))
    if data.get("format") != "talesofmortal-workshop-extraction-v1":
        raise ValueError("Arquivo não é extração da Workshop.")
    if data.get("module", {}).get("id") != SOURCE_MOD:
        raise ValueError("A origem deve ser do mod Steam 2990310797.")
    rows = data.get("localizations", [])
    if not isinstance(rows, list) or not rows:
        raise ValueError("Extração sem registros LocalText.")

    excluded_texts, excluded_keys, names = existing_catalogs(catalog_dir, output)
    previous = {"translations": {}, "keys": {}}
    if output.exists():
        previous = json.loads(output.read_text(encoding="utf-8-sig"))
        if previous.get("module", {}).get("id") != SOURCE_MOD:
            raise ValueError("Destino pertence a outro mod.")
    saved_text = previous.get("translations", {}) or {}
    saved_keys = previous.get("keys", {}) or {}
    if not isinstance(saved_text, dict) or not isinstance(saved_keys, dict):
        raise ValueError("Catálogo destino inválido.")

    available = collections.defaultdict(set)
    keyed = {}
    counts = collections.Counter()
    source_by_key = {}
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get("key"), str):
            source_by_key.setdefault(row["key"], row.get("ch", ""))
    for row in rows:
        counts["sourceRows"] += 1
        if not isinstance(row, dict):
            counts["invalidRows"] += 1
            continue
        key, zh, pt = (row.get(field) for field in ("key", "ch", "en"))
        if not all(isinstance(value, str) for value in (key, zh, pt)):
            counts["invalidRows"] += 1
            continue
        if not key.strip() or not zh.strip() or not pt.strip():
            counts["emptyRows"] += 1
            continue
        if zh in names or key in names:
            counts["protectedNames"] += 1
            continue
        if zh == pt or not HAN.search(zh):
            counts["sameOrNoChinese"] += 1
            continue
        if HAN.search(pt):
            counts["unfinishedPortuguese"] += 1
            continue
        if "\ufffd" in pt or any(ord(c) < 32 and c not in "\r\n\t" for c in pt):
            counts["invalidCharacters"] += 1
            continue
        problem = structural_problem(zh, pt)
        if problem:
            counts[problem] += 1
            continue
        # Corrigir somente rótulos EXATOS, nunca nomes de skills ou texto livre.
        pt = CANONICAL.get(zh, pt)
        counts["acceptedRows"] += 1
        available[zh].add(pt)
        if key in keyed and keyed[key] != pt:
            counts["duplicateKeys"] += 1
            continue
        keyed[key] = pt

    ambiguous = {zh for zh, values in available.items() if len(values) > 1}
    # Não perpetuar traduções estruturalmente perigosas de uma importação
    # anterior. Preserva revisões humanas que já corrigiram as variáveis.
    translations = {}
    for zh, pt in saved_text.items():
        pt = CANONICAL.get(zh, pt)
        if structural_problem(zh, pt):
            counts["removedUnsafeSavedText"] += 1
        else:
            translations[zh] = pt

    keys = {}
    for key, pt in saved_keys.items():
        source = source_by_key.get(key)
        pt = CANONICAL.get(source, pt)
        if isinstance(source, str) and structural_problem(source, pt):
            counts["removedUnsafeSavedKeys"] += 1
        else:
            keys[key] = pt
    for key, pt in sorted(keyed.items()):
        if key not in keys and key not in excluded_keys and key not in names:
            keys[key] = pt
            counts["addedKeys"] += 1
    for zh, values in sorted(available.items()):
        if (zh not in ambiguous and len(zh) >= 2 and zh not in translations
                and zh not in excluded_texts and zh not in names):
            translations[zh] = next(iter(values))
            counts["addedChineseTranslations"] += 1

    result = {
        "module": {
            "kind": "fallback", "id": SOURCE_MOD,
            "name": "Tradução comunitária PT-BR (importação local)",
            "workshopId": "2990310797",
        },
        "translations": translations,
        "keys": keys,
        "sourceNote": (
            "Conteúdo fornecido por um mod de tradução comunitária; "
            "não foi revisado linguisticamente por completo."
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and (saved_text or saved_keys):
        shutil.copy2(output, output.with_suffix(".json.previous.bak"))
    temp = output.with_suffix(".json.tmp")
    try:
        temp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        temp.replace(output)
    finally:
        if temp.exists():
            temp.unlink()

    return {
        **counts,
        "addedKeys": counts["addedKeys"],
        "addedChineseTranslations": counts["addedChineseTranslations"],
        "totalTextTranslations": len(translations),
        "totalKeys": len(keys), "skippedAmbiguousChinese": len(ambiguous),
        "sourceMod": SOURCE_MOD, "destination": str(output)
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path,
                        default=ROOT / "dist/extracted/workshop/2990310797.json")
    parser.add_argument("--catalog-dir", type=Path,
                        default=ROOT / "mod/i18n/pt-BR")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "mod/i18n/pt-BR/Workshop_2990310797.json")
    args = parser.parse_args()
    try:
        result = prepare(args.input, args.catalog_dir, args.output)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
