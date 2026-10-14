#!/usr/bin/env python3
"""Auditoria e normalização conservadora de traduções Tale of Immortal.

Verifica todos os pares originais/pt-BR, chaves, parâmetros dinâmicos,
marcadores de UI, nomes de habilidades e consistência de terminologia.
Com --apply, altera SOMENTE nomes de skills inglesas completas e termos
originais EXATOS do glossário; demais suspeitas vão para revisão humana.
Pode processar também o fallback grande gerado localmente.
"""
import argparse
import collections
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Português canônico para rótulos de interface EXATOS, não diálogos, regiões
# ou nomes de habilidades. Termos ambíguos como 'Looking' e 'Skill Rate'
# NÃO são corrigidos sem contexto do jogo.
CANONICAL = {
    # Somente rótulos EXATOS de elementos/estatísticas. "Madeira" é o nome
    # canônico do elemento, sem alterar usos comuns de "madeira" (material).
    "lightning": "Raio", "Lightning": "Raio", "雷属性": "Raio",
    "fire": "Fogo", "Fire": "Fogo", "火属性": "Fogo",
    "water": "Água", "Water": "Água", "水属性": "Água",
    "wood": "Madeira", "Wood": "Madeira", "木属性": "Madeira",
    "earth": "Terra", "Earth": "Terra", "土属性": "Terra",
    "wind": "Vento", "Wind": "Vento", "风属性": "Vento",
    "火属性资质": "Aptidão com Fogo",
    "水属性资质": "Aptidão com Água",
    "木属性资质": "Aptidão com Madeira",
    "土属性资质": "Aptidão com Terra",
    "雷属性资质": "Aptidão com Raio",
    "风属性资质": "Aptidão com Vento",
    "Luck": "Sorte", "luck": "Sorte",
    "移动速度": "Velocidade de movimento",
    "Movement Speed": "Velocidade de movimento",
    "movement speed": "Velocidade de movimento",
    "Move Speed": "Velocidade de movimento",
    "Skill Range": "Alcance da habilidade",
    "skill range": "Alcance da habilidade",
    "技能射程": "Alcance da habilidade",
}
# Os nomes ingleses de técnicas/skills permanecem em inglês. Detectar apenas
# nomes completos e relativamente específicos; não reverter frases inteiras.
SKILL_NAME = re.compile(
    r"^(?:[A-Z][A-Za-z-]+(?:'s|’s) "
    r"(?:Aerial|Blooming|Blooded|Cardinal|Clouded|Deep|Diving|Empty|"
    r"Flawed|Forceful|Living|Maple|Misty|Nether|Peaked|Powerful|Rear|"
    r"Signing|Solid|Thundrous|Vesseled|Warring|Wavy|Willful) "
    r"[^\n<>.!?]{2,80}|"
    r"(?:Windseek(?: \(\d+\))?|Dayblaze|Spiritcall))"
    r"(?: -\d+)?$"
)
COLOR_SKILL = re.compile(r"^<color(?:=[^>]+)>([^<>]+)</color>$")


def is_named_skill(text):
    """Identifica nomes completos, inclusive rótulos com uma tag <color>."""
    match = COLOR_SKILL.fullmatch(text)
    return bool(SKILL_NAME.fullmatch(match.group(1) if match else text))


HAN = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]")
CURLY = re.compile(r"\{[^{}\r\n]+\}")
SPECIAL = re.compile(r"\$s_[A-Za-z0-9_]+\$|&[A-Za-z0-9_|]+&")
SPRITES = re.compile(r'<sprite\s+name="([^"]+)"')
OPEN_TAG = re.compile(r"<(color|size|b|i|u|link|voffset|space)\b", re.I)
UNTRANSLATED = re.compile(
    r"\b(?:luck|looking|lightning|movement speed|skill range)\b", re.I
)


def inspect(original, target):
    issues = []
    for marker, regex in (("placeholder", CURLY), ("game-variable", SPECIAL),
                          ("sprite", SPRITES)):
        if collections.Counter(regex.findall(original)) != collections.Counter(
                regex.findall(target)):
            issues.append(marker)
    if original.count("\n") > 0 and original.count("\n") != target.count("\n"):
        issues.append("linebreak-count")
    if HAN.search(target):
        issues.append("chinese-remains")
    if UNTRANSLATED.search(target):
        issues.append("english-term-remains")
    if OPEN_TAG.findall(original) and not OPEN_TAG.findall(target):
        issues.append("rich-tags-lost")
    if is_named_skill(original) and original != target:
        issues.append("translated-skill-name")
    if original in CANONICAL and target != CANONICAL[original]:
        issues.append("glossary-conflict")
    return issues


def audit(folder, apply=False, report=None):
    files = sorted(Path(folder).rglob("*.json"))
    summary = collections.Counter()
    catalog_entries = []
    issue_rows = []
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            raise ValueError("Catálogo inválido: " + str(path))
        kind = (data.get("module") or {}).get("kind")
        translations = data.get("translations", {})
        keys = data.get("keys", {})
        if not isinstance(translations, dict) or not isinstance(keys, dict):
            raise ValueError("translations/keys inválidos: " + str(path))
        changes = 0
        file_issues = collections.Counter()
        for source, value in list(translations.items()):
            if not isinstance(source, str) or not isinstance(value, str):
                raise ValueError("Tradução que não é string: " + str(path))
            summary["pairs"] += 1
            reasons = inspect(source, value)
            for reason in reasons:
                summary[reason] += 1
                file_issues[reason] += 1
            replacement = CANONICAL.get(source)
            if is_named_skill(source):
                replacement = source
            if apply and replacement is not None and value != replacement:
                # Uma normalização nunca modifica a string ORIGINAL da chave.
                translations[source] = replacement
                changes += 1
                summary["corrected"] += 1
            if reasons:
                issue_rows.append({
                    "catalog": path.name, "source": source,
                    "translation": value, "reasons": reasons,
                })
        summary["keys"] += len(keys)
        summary["files"] += 1
        catalog_entries.append({
            "file": path.name, "kind": kind,
            "pairs": len(translations), "keys": len(keys),
            "corrected": changes, "issues": dict(file_issues),
        })
        if apply and changes:
            temp = path.with_suffix(".json.tmp")
            try:
                temp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                                encoding="utf-8")
                temp.replace(path)
            finally:
                if temp.exists():
                    temp.unlink()

    result = {
        "format": "talesofmortal-terminology-audit-v1",
        "glossary": CANONICAL,
        "summary": dict(summary),
        "catalogs": catalog_entries,
        "issues": issue_rows,
        "limitation": "Automatic checks cannot validate context-dependent meanings, proper-name identity or linguistic quality.",
    }
    if report is not None:
        report = Path(report)
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=Path, default=ROOT / "mod/i18n/pt-BR")
    parser.add_argument("--report", type=Path,
                        default=ROOT / "dist/TalesOfMortal_i18N/terminology-audit.json")
    parser.add_argument("--apply", action="store_true",
                        help="Corrige somente entradas exatas do glossário e nomes completos de skills.")
    args = parser.parse_args()
    result = audit(args.folder, args.apply, args.report)
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    print("Relatório:", args.report)


if __name__ == "__main__":
    main()
