#!/usr/bin/env python3
"""Extrai textos originais de CADA mod da Steam Workshop de Tale of Immortal.

Entrada: steamapps/workshop/content/1468810/<ID_DO_MOD>/
Saída:   dist/extracted/workshop/<ID_DO_MOD>/texts.json
         dist/extracted/workshop/index.json

O script lê recursos textuais, não modifica os mods, não chama tradutores e
não interpreta AssetBundles, DLLs ou tabelas binárias/criptografadas.
"""
import argparse
import json
import os
import re
import csv
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

if __package__:
    from .extract_offline import (
        EXTENSIONS, SKIP_DIRS, iter_source_strings, language, read_content,
    )
else:
    from extract_offline import (
        EXTENSIONS, SKIP_DIRS, iter_source_strings, language, read_content,
    )

APP_ID = "1468810"
MAX_LOCATIONS = 5
LOCALIZATION_FIELDS = ("en", "ch", "tc")
TECH_PREFIXES = ("#", "&", "//", "/*", "--", "http://", "https://", "file://")
TECHNICAL = re.compile(
    r"^(?:[\w.-]+[/\\][\w./\\-]+|[A-Za-z_]\w*\([^\n]*\)|"
    r"(?=.*[_=])[\w=+|#&./\\:%*-]+|[A-Za-z0-9+/_=-]{28,})$"
)
RICH_TAG = re.compile(r"</?[^>]{1,100}>")
ENGLISH = re.compile(r"[A-Za-z]{2,}")
TEXT_FIELD = re.compile(
    r"(?:^|\.)(?:en|english|text|title|desc|description|name|label|"
    r"content|help|tip|tips|info|dialogue|dialog|option|message|"
    r"caption|prompt|notice|hint|subtitle|ch|tc)(?:$|\[)", re.I
)
SKIP_FILES = {"moddata.cache", "modproject.cache", "modexportdata.cache"}
IGNORED_DIRS = SKIP_DIRS | {
    "docs", "documentation", "readme", ".vs", "xunity", "temp", "tmp",
}


def known_strings(folder):
    """Only annotate known translations; never merge them into extracted data."""
    known, protected = set(), set()
    if not folder.is_dir():
        return known, protected
    for path in folder.glob("*.json"):
        try:
            document = json.loads(path.read_text(encoding="utf-8-sig"))
            known.update(document.get("translations", {}).keys())
            known.update(document.get("keys", {}).keys())
            names = document.get("names", [])
            if isinstance(names, list):
                protected.update(value for value in names if isinstance(value, str))
        except (OSError, ValueError, TypeError):
            continue
    return known, protected


def readable_candidate(value, context, protected):
    value = value.strip()
    if len(value) < 2 or len(value) > 8000 or value in protected:
        return None
    lang = language(value)
    if lang is None:
        return None
    plain = RICH_TAG.sub("", value).strip()
    if not plain:
        return None
    if plain.lower().startswith(TECH_PREFIXES):
        return None
    if "\x00" in plain or TECHNICAL.fullmatch(plain):
        return None
    if lang == "en-candidate":
        tokens = ENGLISH.findall(plain)
        # Outside UI fields, a lone ASCII word is usually an identifier.
        if len(tokens) < 2 and not TEXT_FIELD.search(context):
            return None
        # Avoid source-code fragments and file names, even in text fields.
        if re.search(r"(?i)\.(?:dll|exe|json|xml|png|cs|py|lua|js)(?:\b|$)", plain):
            return None
        if re.search(r"\b(?:using\s+\w+;|namespace\s+\w+|public\s+class|return\s+new)\b", plain):
            return None
    return value, lang


def extract_localtext(doc, relative_path):
    """Keep English, simplified, traditional and key tied to a shared row."""
    pending = [(doc, "$")]
    while pending:
        current, position = pending.pop()
        if isinstance(current, list):
            for idx, row in enumerate(current):
                pending.append((row, f"{position}[{idx}]"))
        elif isinstance(current, dict):
            if any(isinstance(current.get(field), str) for field in LOCALIZATION_FIELDS):
                row = {"file": relative_path, "row": position}
                for field in (*LOCALIZATION_FIELDS, "key"):
                    if isinstance(current.get(field), str):
                        row[field] = current[field]
                yield row
                # These are data fields, not a string-to-string translations map.
                for field, value in current.items():
                    if field not in (*LOCALIZATION_FIELDS, "key") and isinstance(value, (dict, list)):
                        pending.append((value, f"{position}.{field}"))
            else:
                for field, value in current.items():
                    if isinstance(value, (dict, list)):
                        pending.append((value, f"{position}.{field}"))


def add_entry(entries, original, context, source_path, known, protected,
              max_entries, key=None):
    result = readable_candidate(original, context, protected)
    if result is None:
        return False
    original, lang = result
    entry = entries.get(original)
    if entry is None:
        if len(entries) >= max_entries:
            return False
        entry = {
            "text": original, "language": lang, "translatedInProject": original in known,
            "occurrences": 0, "locations": [], "localizationKeys": [],
        }
        entries[original] = entry
    entry["occurrences"] += 1
    location = {"file": source_path, "context": context[:200]}
    if location not in entry["locations"] and len(entry["locations"]) < MAX_LOCATIONS:
        entry["locations"].append(location)
    if isinstance(key, str) and key and key not in entry["localizationKeys"]:
        if len(entry["localizationKeys"]) < 15:
            entry["localizationKeys"].append(key)
    return True


def extract_mod(mod_id, mod_dir, known, protected, max_file_bytes, max_entries):
    entries = {}
    localizations = []
    skipped = []
    stats = {"files_scanned": 0, "files_skipped": 0,
             "texts_seen": 0, "unique_texts": 0, "already_translated": 0}

    for directory, subdirs, files in os.walk(mod_dir, followlinks=False):
        subdirs[:] = sorted(
            subdir for subdir in subdirs
            if subdir.lower() not in IGNORED_DIRS and
            not (Path(directory) / subdir).is_symlink()
        )
        for filename in sorted(files):
            path = Path(directory) / filename
            if path.is_symlink() or path.suffix.lower() not in EXTENSIONS:
                continue
            if filename.lower() in SKIP_FILES:
                continue
            relative = path.relative_to(mod_dir).as_posix()
            try:
                text = read_content(path, max_file_bytes)
                stats["files_scanned"] += 1

                if path.name.lower() == "localtext.json":
                    document = json.loads(text)
                    for row in extract_localtext(document, relative):
                        # Do not save the internal localization ID as a translated text.
                        localizations.append(row)
                        for field in LOCALIZATION_FIELDS:
                            original = row.get(field)
                            if not isinstance(original, str):
                                continue
                            if add_entry(entries, original, row["row"] + "." + field,
                                         relative, known, protected, max_entries,
                                         key=row.get("key")):
                                stats["texts_seen"] += 1
                else:
                    for original, context in iter_source_strings(path, text):
                        if add_entry(entries, original, context, relative,
                                     known, protected, max_entries):
                            stats["texts_seen"] += 1

            except (OSError, ValueError, UnicodeError, ET.ParseError, csv.Error) as error:
                stats["files_skipped"] += 1
                if len(skipped) < 100:
                    skipped.append({"file": relative, "reason": str(error)[:200]})

    ordered = [entries[key] for key in sorted(entries)]
    stats["unique_texts"] = len(ordered)
    stats["already_translated"] = sum(1 for row in ordered if row["translatedInProject"])
    return {
        "format": "talesofmortal-workshop-extraction-v1",
        "module": {
            "kind": "mod", "id": "steam:" + mod_id,
            "name": "Workshop " + mod_id, "workshopId": mod_id
        },
        "source": "steam-workshop-text-files",
        "note": "Only candidate UI text. Language is heuristic; review names and variables.",
        "stats": stats,
        "entries": ordered,
        "localizations": sorted(localizations, key=lambda row: (row["file"], row["row"])),
        "skipped": skipped,
    }


def steam_library_candidates():
    home = Path.home()
    steam_roots = [
        home / ".steam/debian-installation",
        home / ".steam/steam",
        home / ".local/share/Steam",
        home / ".var/app/com.valvesoftware.Steam/.local/share/Steam",
    ]
    candidates = []
    for steam in steam_roots:
        candidates.append(steam / "steamapps/workshop/content" / APP_ID)
        vdf = steam / "steamapps/libraryfolders.vdf"
        if not vdf.is_file():
            continue
        try:
            # libraryfolders.vdf contains "path" "/path/to/SteamLibrary"
            for library in re.findall(r'"path"\s*"([^"]+)"', vdf.read_text(encoding="utf-8")):
                base = Path(library.replace("\\\\", "\\"))
                candidates.append(base / "steamapps/workshop/content" / APP_ID)
        except (OSError, UnicodeError):
            continue
    return candidates


def discover_workshop_dirs(explicit):
    if explicit:
        candidates = explicit
    else:
        candidates = steam_library_candidates()
    found, seen = [], set()
    for location in candidates:
        path = location.expanduser().resolve()
        if not path.is_dir():
            if explicit:
                raise ValueError("Steam Workshop não encontrada: " + str(path))
            continue
        if path.name != APP_ID:
            raise ValueError("Escolha a pasta .../workshop/content/" + APP_ID +
                             ", recebida: " + str(path))
        if path in seen:
            continue
        seen.add(path)
        found.append(path)
    if not found:
        raise ValueError("Steam Workshop não localizada. Informe --workshop-dir "
                         "'/caminho/steamapps/workshop/content/1468810'")
    return found


def write_json_atomic(target, data):
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(".json.tmp")
    try:
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        os.replace(temp, target)
    finally:
        if temp.exists():
            temp.unlink()


def run(workshop_dirs, output, known_folder=None, max_file_bytes=30_000_000,
        max_entries=50000):
    roots = discover_workshop_dirs(workshop_dirs)
    output = output.expanduser().resolve()
    if any(output == root or root in output.parents for root in roots):
        raise ValueError("A pasta de saída não pode ficar dentro da Steam Workshop.")
    if max_file_bytes <= 0 or max_entries <= 0:
        raise ValueError("Limites --max-file-bytes e --max-entries devem ser positivos.")

    if known_folder is None:
        known_folder = Path(__file__).resolve().parents[1] / "mod/i18n/pt-BR"
    known, protected = known_strings(known_folder)
    seen_ids = set()
    results = []

    for root in roots:
        for mod_dir in sorted(root.iterdir(), key=lambda path: path.name):
            if not mod_dir.is_dir() or mod_dir.is_symlink() or not mod_dir.name.isdecimal():
                continue
            mod_id = mod_dir.name
            if mod_id in seen_ids:
                print(f"[IGNORADO] Steam Workshop duplicada: {mod_id}")
                continue
            seen_ids.add(mod_id)
            data = extract_mod(mod_id, mod_dir, known, protected, max_file_bytes, max_entries)
            path = output / mod_id / "texts.json"
            write_json_atomic(path, data)
            results.append({"workshopId": mod_id, "file": f"{mod_id}/texts.json",
                            "stats": data["stats"]})
            print(f"[{mod_id}] {data['stats']['unique_texts']} textos; "
                  f"{data['stats']['files_skipped']} arquivo(s) ignorado(s) -> {path}")

    summary = {"format": "talesofmortal-workshop-index-v1",
               "appId": APP_ID, "mods_processed": len(results), "mods": results}
    write_json_atomic(output / "index.json", summary)
    print(f"Concluído: {len(results)} mods | {output / 'index.json'}")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workshop-dir", action="append", type=Path,
                        help="Pasta .../steamapps/workshop/content/1468810 (repetível). "
                             "Sem o argumento, procura bibliotecas Steam automaticamente.")
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).resolve().parents[1] /
                        "dist/extracted/workshop")
    parser.add_argument("--known", type=Path,
                        help="Pasta dos JSON traduzidos, usada só para marcar textos conhecidos.")
    parser.add_argument("--max-file-bytes", type=int, default=30_000_000)
    parser.add_argument("--max-entries", type=int, default=50000,
                        help="Máximo de textos únicos por mod.")
    args = parser.parse_args()
    try:
        run(args.workshop_dir, args.output, args.known,
            args.max_file_bytes, args.max_entries)
    except (ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
