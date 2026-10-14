#!/usr/bin/env python3
"""Five independent QA passes over every PT-BR catalog, including local fallback.

Never modifies catalogs. Optional --extracted supplies original Chinese
LocalText for key-level placeholder checks. Reports review candidates, not
certified human translations.
"""
import argparse
import collections
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HAN = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]")
PH = re.compile(r"\{[^{}\r\n]+\}")
VAR = re.compile(r"\$s_[^$\r\n]{1,140}\$|&[A-Za-z0-9_/%+|.?:=-]{1,140}&")
SPRITE = re.compile(r"""<sprite\b[^>]*?\bname=\\?["']([^"\\']+)\\?["']""", re.I)
TAG = re.compile(r"<(/?)(b|i|u|color|size|link|voffset)\b", re.I)
EN = re.compile(r"\b(?:luck|looking|lightning|movement speed|skill range)\b", re.I)
SKILL = re.compile(
    r"^[A-Z][A-Za-z-]+(?:'s|’s) [A-Z][\w'-]+(?: [A-Z][\w'-]+){0,4} "
    r"(?:Firebolt|Groundfire|Thundercall|Palm|Sword|Spear|Fist|"
    r"Technique|Técnica|Blade|Manual|Celerity Palm)(?: -\d+)?$")
REGIONS = {"Yong Ning", "Hua Feng", "Mu Xian", "Yun Mo", "Chi You"}
ARTIFACT_SPIRITS = {
    "Mengyi", "Cangya", "Jiuchen", "Muqing", "Ningshuang", "Lingge",
    "Yunling", "Huofa", "Silver Edge", "Xuanti", "Bajiao", "Jiuzhu",
    "Zhenxin", "Sharp Edge", "Charon", "Searing Feather", "Feiming",
    "Youling", "Sharpclaw", "Darkfang", "Voodoo", "Muke", "Brawler",
    "Rainmaker",
}
ARTIFACT_SOURCE_ALIASES = {
    "Jovem": "Youling",
    "Borda de prata": "Silver Edge",
    "Pena abrasadora": "Searing Feather",
}
ARTIFACT_LIST_NAMES = re.compile(r"<color=[^>]*>([^<>]+)</color>")

CANON = {
    "lightning": "Raio", "Lightning": "Raio", "雷属性": "Raio",
    "火属性": "Fogo", "水属性": "Água", "木属性": "Madeira", "土属性": "Terra",
    "Luck": "Sorte", "luck": "Sorte",
    "移动速度": "Velocidade de movimento",
    "Movement Speed": "Velocidade de movimento", "movement speed": "Velocidade de movimento",
    "Move Speed": "Velocidade de movimento", "Skill Range": "Alcance da habilidade",
    "skill range": "Alcance da habilidade", "技能射程": "Alcance da habilidade",
}
SUSPICIOUS = re.compile(r"parmeasureiRO|\b(?:nullpointer|undefined)\b", re.I)


def originals(path):
    if not path or not Path(path).is_file():
        return {}
    doc = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if doc.get("module", {}).get("id") != "steam:2990310797":
        raise ValueError("--extracted deve ser o JSON extraído de 2990310797.")
    return {r["key"]: r["ch"] for r in doc.get("localizations", [])
            if isinstance(r, dict) and isinstance(r.get("key"), str)
            and isinstance(r.get("ch"), str)}


def audit(folder, extracted=None, report=None):
    folder = Path(folder)
    catalog_files = sorted(folder.rglob("*.json"))
    source_keys = originals(extracted)
    files = []
    protected = set()
    for path in catalog_files:
        doc = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(doc, dict):
            raise ValueError("Catálogo não é objeto JSON: " + str(path))
        files.append((path.name, doc))
        protected.update(x for x in doc.get("names", [])
                         if isinstance(x, str))
    counts = {str(i): collections.Counter() for i in range(1, 6)}
    issues = []
    by_text, by_key = collections.defaultdict(list), collections.defaultdict(list)
    pair_count = key_count = 0

    def flag(pas, catalog, key, reason, original, target, severity="review"):
        counts[str(pas)][reason] += 1
        issues.append({"pass": pas, "severity": severity, "catalog": catalog,
                       "key": key, "reason": reason, "original": original,
                       "translation": target})

    for filename, doc in files:
        mod = doc.get("module", {})
        identity = mod.get("id", filename) if isinstance(mod, dict) else filename
        for field in ("translations", "keys"):
            translations = doc.get(field, {})
            if not isinstance(translations, dict):
                flag(1, filename, "", "invalid-map", field, str(type(translations)), "error")
                continue
            for key, target in translations.items():
                if field == "keys":
                    key_count += 1
                    source = source_keys.get(key)
                    by_key[key].append((filename, target, identity))
                else:
                    pair_count += 1
                    source = key
                    by_text[key].append((filename, target, identity))
                if not isinstance(key, str) or not isinstance(target, str):
                    flag(1, filename, str(key), "non-string", str(source), str(target), "error")
                    continue
                if not key or not target:
                    flag(1, filename, key, "empty-value", source or "", target, "error")
                if source is None:
                    continue

                # Pass 1: engine syntax, placeholders, sprites and markup.
                for kind, matcher in (("placeholder", PH), ("internal-variable", VAR),
                                      ("sprite", SPRITE)):
                    if collections.Counter(matcher.findall(source)) != (
                            collections.Counter(matcher.findall(target))):
                        flag(1, filename, key, kind + "-mismatch", source, target, "error")
                if TAG.search(source) and collections.Counter(TAG.findall(source)) != (
                        collections.Counter(TAG.findall(target))):
                    flag(1, filename, key, "unity-tag-mismatch", source, target, "error")

                # Pass 2: canonical labels only; never rewrite sentence fragments.
                if source in CANON and target != CANON[source]:
                    flag(2, filename, key, "glossary-inconsistent", source, target)

                # Pass 3: NPC names, English regions and named abilities.
                if source in protected and source != target:
                    flag(3, filename, key, "protected-name-changed", source, target, "error")
                if source in REGIONS and source != target:
                    flag(3, filename, key, "region-changed", source, target)
                if SKILL.fullmatch(source) and source != target:
                    flag(3, filename, key, "skill-name-changed", source, target)
                if source in ARTIFACT_SPIRITS and source != target:
                    flag(3, filename, key, "artifact-spirit-name-changed", source, target)
                if source in ARTIFACT_SOURCE_ALIASES and (
                        target != ARTIFACT_SOURCE_ALIASES[source]):
                    flag(3, filename, key, "artifact-spirit-alias-changed", source, target)
                if "<color=" in source and "Mengyi" in source and "Muqing" in source:
                    spirit_sources = ARTIFACT_LIST_NAMES.findall(source)
                    expected = [ARTIFACT_SOURCE_ALIASES.get(name, name) for name in spirit_sources]
                    found = ARTIFACT_LIST_NAMES.findall(target)
                    if len(expected) >= 5 and found != expected:
                        flag(3, filename, key, "artifact-spirit-roster-corrupted",
                             " | ".join(expected), " | ".join(found), "error")

                # Pass 4: language, suspicious corruption and line structure.
                if HAN.search(target) and target != source and target not in protected:
                    flag(4, filename, key, "chinese-remains", source, target)
                if EN.search(target) and not(SKILL.fullmatch(source) and source == target):
                    flag(4, filename, key, "english-term-remains", source, target)
                if SUSPICIOUS.search(target):
                    flag(4, filename, key, "corrupted-word", source, target, "error")
                if source.count("\n") != target.count("\n") and "\n" in source:
                    flag(4, filename, key, "line-count-mismatch", source, target)

    # Pass 5: collisions of identical source text/key in different modules.
    for label, matches in (("text", by_text), ("key", by_key)):
        for key, choices in matches.items():
            if len({item[1] for item in choices}) > 1:
                first = choices[0]
                flag(5, first[0], key, label + "-collision", key,
                     " | ".join(list(dict.fromkeys(c[1] for c in choices))[:4]))

    summary = {
        "files": len(files), "translations": pair_count, "keys": key_count,
        "keys_with_known_source": len(source_keys), "protected_names": len(protected),
        "pass_counts": {p: dict(t) for p, t in counts.items()},
        "flagged_issues": len(issues),
        "unsafe_candidates": sum(x["severity"] == "error" for x in issues),
        "notice": "Candidate issues require context; tests do not certify literary quality."
    }
    output = {"format": "talesofmortal-five-pass-review-v1",
              "summary": summary, "issues": issues}
    if report:
        report = Path(report)
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
        with report.with_suffix(".csv").open("w", newline="", encoding="utf-8-sig") as fp:
            writer = csv.DictWriter(fp, fieldnames=[
                "pass", "severity", "catalog", "reason", "key", "original", "translation"])
            writer.writeheader()
            writer.writerows(issues)
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--folder", type=Path, default=ROOT / "mod/i18n/pt-BR")
    p.add_argument("--extracted", type=Path, help="JSON do mod 2990310797, para validar keys")
    p.add_argument("--output", type=Path,
                   default=ROOT / "dist/TalesOfMortal_i18N/five-pass-review.json")
    args = p.parse_args()
    print(json.dumps(audit(args.folder, args.extracted, args.output),
                     indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
