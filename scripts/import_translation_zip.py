#!/usr/bin/env python3
import argparse, json, re, zipfile
from collections import OrderedDict
from pathlib import Path

MOD_NAMES = {"GuiUI": "GuiUI", "Fatury": "Fatury", "Cave": "Cave",
             "SchoolAdmin": "SectAdmin", "FixData": "FixData",
             "MOD_MutualIntimate": "MutualIntimate", "MOD_PFAutoBattle": "PFAutoBattle"}

def workshop_module(workshop_id, source_alias):
    """Stable identity even when the translated JSON is renamed."""
    known = {
        "SchoolAdmin": "SectAdmin",
        "GuiUI": "GuiUI",
        "Fatury": "Fatury",
        "Cave": "Cave",
        "FixData": "FixData",
        "MOD_MutualIntimate": "MutualIntimate",
        "MOD_PFAutoBattle": "PFAutoBattle",
    }
    name = known.get(source_alias) if source_alias else None
    if not name:
        name = source_alias or ("Workshop " + workshop_id)
    mod = {
        "kind": "mod",
        "id": "steam:" + workshop_id,
        "name": name,
        "workshopId": workshop_id,
    }
    if source_alias:
        mod["sourceAlias"] = source_alias
    return mod

def split_pair(line):
    slashes = 0
    for i, char in enumerate(line):
        if char == "=" and slashes % 2 == 0:
            return line[:i], line[i + 1:]
        slashes = slashes + 1 if char == "\\" else 0
    return None

def decode(value):
    out = []
    i = 0
    esc = {"n": "\n", "r": "\r", "t": "\t", "=": "=", "\\": "\\", "/": "/"}
    while i < len(value):
        if value[i] != "\\" or i + 1 >= len(value):
            out.append(value[i]); i += 1; continue
        nx = value[i + 1]
        if nx in esc:
            out.append(esc[nx]); i += 2
        elif nx == "u" and re.fullmatch(r"[0-9a-fA-F]{4}", value[i+2:i+6]):
            out.append(chr(int(value[i+2:i+6], 16))); i += 6
        else:
            out.append(value[i]); i += 1
    return "".join(out)

def read_pairs(raw):
    result = OrderedDict()
    for line in raw.decode("utf-8-sig").splitlines():
        if not line.strip() or line.lstrip().startswith(("#", "//")): continue
        split = split_pair(line)
        if not split: continue
        key, value = map(decode, split)
        if key and value and key not in result:
            result[key] = value
    return result

def read_json(path, default):
    if not path.exists(): return default
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict): raise ValueError("JSON inválido: " + str(path))
    return data

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def run(archive, root):
    stats = {"added": 0, "patterns": 0, "skipped": 0}
    with zipfile.ZipFile(archive) as z:
        pairs = {}
        for item in z.infolist():
            if item.filename.startswith("Text/") and item.filename.endswith(".txt") and not item.is_dir():
                if item.file_size > 30_000_000: raise ValueError("TXT muito grande: " + item.filename)
                pairs[item.filename] = read_pairs(z.read(item))

    original = pairs.get("Text/_Substitutions.txt", {})
    protected = OrderedDict()
    for key, value in original.items():
        protected[key] = None
        protected[value] = None
    names_file = root / "protected-names.json"
    for name in read_json(names_file, {"names": []}).get("names", []):
        if isinstance(name, str) and name:
            protected[name] = None
    write_json(names_file, {
        "module": {"kind": "names", "id": "system:protected-names",
                   "name": "Nomes próprios protegidos"},
        "names": list(protected),
    })
    seen = set()
    def add(source, output, module=None):
        data = pairs.get(source)
        if data is None: return
        target = root / output
        obj = read_json(target, {"translations": {}, "keys": {}})
        if "translations" not in obj:
            obj = {"translations": obj, "keys": {}}
        if module is not None:
            existing = obj.get("module")
            if existing and existing.get("id") != module["id"]:
                raise ValueError("Identidade conflitante em " + str(target))
            # Preservar nomes e identificadores revisados em reimportações.
            obj["module"] = dict(module, **(existing or {}))
        translations = obj["translations"]
        if not isinstance(translations, dict): raise ValueError("translations inválido: " + str(target))
        patterns = obj.setdefault("patterns", [])
        if not isinstance(patterns, list): raise ValueError("patterns inválido: " + str(target))
        patterns_seen = {p.get("pattern") for p in patterns if isinstance(p, dict)}
        for key, translated in data.items():
            if key in protected or key == translated:
                stats["skipped"] += 1; continue
            if key.startswith('r:"') and key.endswith('"'):
                pattern = key[3:-1]
                replacement = translated[1:-1] if translated.startswith('"') and translated.endswith('"') else translated
                if pattern not in patterns_seen:
                    patterns.append({"pattern": pattern, "replacement": replacement})
                    patterns_seen.add(pattern)
                    stats["patterns"] += 1
                continue
            if key in seen or key in translations:
                stats["skipped"] += 1; continue
            translations[key] = translated
            seen.add(key)
            stats["added"] += 1
        write_json(target, obj)

    add("Text/PTBR_Revisado.txt", "game.json", {
        "kind": "game", "id": "game:tale-of-immortal",
        "name": "Tale of Immortal"
    })
    for source in sorted(pairs):
        m = re.fullmatch(r"Text/mods/Workshop_(\d+)(?:__([^/]+))?/PTBR.txt", source)
        if not m: continue
        workshop_id, modname = m.groups()
        add(source, MOD_NAMES.get(modname, "Workshop_" + workshop_id) + ".json",
            workshop_module(workshop_id, modname))
    add("Text/_AutoGeneratedTranslations.txt", "zzz-auto.json", {
        "kind": "fallback", "id": "legacy:xunity-auto",
        "name": "Traduções importadas do legado XUnity"
    })
    print(json.dumps(stats, ensure_ascii=False))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("archive", type=Path, help="Arquivo Text.zip")
    ap.add_argument("--output", type=Path,
                    default=Path(__file__).resolve().parents[1] / "mod/i18n/pt-BR")
    args = ap.parse_args()
    if not zipfile.is_zipfile(args.archive): ap.error("Arquivo ZIP inválido")
    run(args.archive, args.output)
