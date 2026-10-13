#!/usr/bin/env python3
"""Extrai possíveis textos de UI de arquivos textuais do jogo e de mods.

Decodifica ModExcel no formato excelEncrypt do Tale of Immortal.
Não interpreta AssetBundles Unity, Assembly-CSharp, DLLs ou formatos desconhecidos.
"""
import argparse
import csv
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

if __package__:
    from .toi_crypto import decode_mod_file, is_mod_encrypted
else:
    from toi_crypto import decode_mod_file, is_mod_encrypted

EXTENSIONS = {".json", ".jsonc", ".txt", ".csv", ".tsv", ".xml", ".ini",
              ".cfg", ".lang", ".strings", ".yaml", ".yml"}
SKIP_DIRS = {
    ".git", ".github", "__pycache__", "node_modules", "bin", "obj", "logs",
    "melonloader", "cache", "translation", "i18n",
    "talesofmortal_i18n_extracted", "dist", "xunity.autotranslator",
    "modfqa", "userdata", "il2cpp_data", "library",
}
SIMP = set("龙门剑学气灵体发岁无万国经师后阳风广画云东叶书鸟马鱼")
TRAD = set("龍門劍學氣靈體發歲無萬國經師後陽風廣畫雲東葉書鳥馬魚")
CJK = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]")
LATIN = re.compile(r"[A-Za-z]{3,}")

def language(text):
    han = set(CJK.findall(text))
    if han:
        hs, ht = bool(han & SIMP), bool(han & TRAD)
        return ("zh-mixed" if hs and ht else
                "zh-Hans" if hs else
                "zh-Hant" if ht else "zh-und")
    if LATIN.search(text):
        return "en-candidate"  # Também pode ser PT-BR ou pinyin: revisar
    return None

def strings_from_json(value):
    stack = [(value, "$")]
    while stack:
        obj, key = stack.pop()
        if isinstance(obj, str):
            yield obj, key
        elif isinstance(obj, list):
            for index, item in enumerate(obj):
                stack.append((item, key + "[" + str(index) + "]"))
        elif isinstance(obj, dict):
            for k, v in obj.items():
                # Só inclua chaves de objeto que contenham ideogramas;
                # evitar IDs internos, propriedades, números e definições de classe.
                if CJK.search(str(k)):
                    yield str(k), key + ".<key>"
                stack.append((v, key + "." + str(k)[:80]))

def read_content(path, max_bytes):
    if path.stat().st_size > max_bytes:
        raise ValueError("Arquivo acima do limite configurado")
    raw = path.read_bytes()
    was_encrypted = is_mod_encrypted(raw)
    if was_encrypted:
        raw = decode_mod_file(raw)
    if b"\x00" in raw and not (raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff")):
        raise ValueError("Arquivo binário (NUL)")
    # UTF-16 sem BOM interpreta arquivos ASCII comuns como falsos
    # ideogramas chineses. Só aceitar UTF-16 com assinatura de bytes.
    encodings = ("utf-8-sig",) if was_encrypted else (
        ("utf-16",) if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else
        ("utf-8-sig", "gb18030", "big5")
    )
    for enc in encodings:
        try:
            text = raw.decode(enc)
            if "\ufffd" in text:
                continue
            return text
        except (UnicodeDecodeError, LookupError):
            pass
    raise ValueError("Codificação textual desconhecida")

def iter_source_strings(path, text):
    suffix = path.suffix.lower()
    if suffix in {".json", ".jsonc"}:
        # JSONC só pode ser lido se também for JSON padrão.
        obj = json.loads(text)
        yield from strings_from_json(obj)
    elif suffix in {".csv", ".tsv"}:
        import io
        for row_no, row in enumerate(csv.reader(io.StringIO(text),
                            delimiter="\t" if suffix == ".tsv" else ","), start=1):
            for col, field in enumerate(row):
                yield field, "row:%d:column:%d" % (row_no, col)
    elif suffix == ".xml":
        tree = ET.fromstring(text)
        for el in tree.iter():
            if el.text:
                yield el.text, "xml:" + str(el.tag)
            for k, v in el.attrib.items():
                yield v, "xml:" + str(el.tag) + "@" + k
    else:
        for num, line in enumerate(text.splitlines(), start=1):
            line = line.strip()
            if not line or line.startswith(("#", "//", ";")):
                continue
            if "=" in line and suffix in {".ini", ".cfg", ".lang", ".strings"}:
                left, right = line.split("=", 1)
                yield left.strip(), "line:%d:key" % num
                yield right.strip(), "line:%d:value" % num
            else:
                yield line, "line:%d" % num

def module_for(path, root):
    parts = path.parts
    # Steam Workshop paths use .../workshop/content/1468810/<id>/...
    for i, item in enumerate(parts):
        if item.lower() == "workshop" and len(parts) > i + 3:
            if parts[i + 1] == "content" and parts[i + 2] == "1468810":
                mod_id = parts[i + 3]
                if mod_id.isdigit():
                    return {"kind": "mod", "id": "steam:" + mod_id,
                            "name": "Workshop " + mod_id,
                            "workshopId": mod_id}
        if item == "ModExportData" and len(parts) > i + 1:
            mod_dir = parts[i + 1]
            if mod_dir.startswith("Mod_"):
                return {"kind": "mod", "id": "local:" + mod_dir[4:],
                        "name": mod_dir}
    if root.name.lower() == "1468810" and path.relative_to(root).parts:
        mod_id = path.relative_to(root).parts[0]
        if mod_id.isdigit():
            return {"kind": "mod", "id": "steam:" + mod_id,
                    "name": "Workshop " + mod_id, "workshopId": mod_id}
    return {"kind": "game", "id": "game:tale-of-immortal", "name": "Tale of Immortal"}

def scan(roots, output, max_bytes=30_000_000, max_entries=120000,
         include_english=True, include_chinese=True):
    catalogs = defaultdict(dict)
    modules = {}
    skipped = []
    statistics = {"files_scanned": 0, "files_skipped": 0, "strings_observed": 0}
    unique_total = 0

    for root in roots:
        root = root.expanduser().resolve()
        if not root.is_dir():
            raise ValueError("Diretório inexistente: " + str(root))
        for directory, dirs, filenames in __import__("os").walk(root):
            dirs[:] = sorted(d for d in dirs if d.lower() not in SKIP_DIRS)
            for filename in sorted(filenames):
                path = Path(directory) / filename
                if path.suffix.lower() not in EXTENSIONS:
                    continue
                if filename.endswith("（打开查看说明）.txt"):
                    continue
                try:
                    text = read_content(path, max_bytes)
                    module = module_for(path, root)
                    mod_id = module["id"]
                    modules[mod_id] = module
                    statistics["files_scanned"] += 1
                    for original, context in iter_source_strings(path, text):
                        original = original.strip()
                        if not 2 <= len(original) <= 8000:
                            continue
                        kind = language(original)
                        if kind is None or (kind == "en-candidate" and not include_english) or \
                           (kind.startswith("zh") and not include_chinese):
                            continue
                        statistics["strings_observed"] += 1
                        data = catalogs[mod_id]
                        if original not in data:
                            if unique_total >= max_entries:
                                continue
                            unique_total += 1
                            data[original] = {
                                "text": original, "language": kind, "occurrences": 0,
                                "locations": [],
                            }
                        row = data[original]
                        row["occurrences"] += 1
                        if len(row["locations"]) < 5:
                            # Source path is stored relative to the selected root, never absolute.
                            row["locations"].append({
                                "file": str(path.relative_to(root)),
                                "context": context[:150]
                            })
                except (OSError, ValueError, ET.ParseError, csv.Error) as exc:
                    statistics["files_skipped"] += 1
                    if len(skipped) < 100:
                        skipped.append({"file": str(path.relative_to(root)), "reason": str(exc)[:200]})

    packages = []
    for mod_id in sorted(catalogs):
        values = catalogs[mod_id]
        packages.append({
            "module": modules[mod_id],
            "entries": [values[k] for k in sorted(values)],
        })
    statistics["entries_unique"] = sum(len(c["entries"]) for c in packages)
    result = {
        "format": "talesofmortal-extraction-v1",
        "mode": "offline-text-resources",
        "limitations": "Only visible text resources; no Unity AssetBundles, DLL string tables or encrypted archives.",
        "languageWarning": "English and Chinese writing systems are heuristic candidates.",
        "stats": statistics,
        "skipped": skipped,
        "catalogs": packages,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return statistics

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", action="append", type=Path, required=True,
                   help="Pasta do jogo, ModExportData ou Steam Workshop 1468810; repetível")
    p.add_argument("--output", type=Path, default=Path("dist/extracted/offline.json"))
    p.add_argument("--max-file-bytes", type=int, default=30_000_000)
    p.add_argument("--max-entries", type=int, default=120000)
    p.add_argument("--no-english", action="store_true")
    p.add_argument("--no-chinese", action="store_true")
    args = p.parse_args()
    try:
        stats = scan(args.root, args.output, args.max_file_bytes, args.max_entries,
                     not args.no_english, not args.no_chinese)
    except (ValueError, OSError) as err:
        p.error(str(err))
    print(json.dumps(stats, ensure_ascii=False))
    print("Extração salva em: " + str(args.output))

if __name__ == "__main__":
    main()
