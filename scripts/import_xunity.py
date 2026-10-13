#!/usr/bin/env python3
"""Importa pares originais XUnity (original=tradução) para um pacote JSON.

Não executa XUnity, não converte regex, nem substitui nomes de NPC.
A ordem dos TXT determina a prioridade: primeiro arquivo vence.
Uma tradução já presente no JSON de destino prevalece sobre qualquer TXT.
"""
import argparse
import json
from pathlib import Path


def split_entry(line):
    """Divide no primeiro '=' que não esteja escapado com barra invertida."""
    escaped = False
    for index, char in enumerate(line):
        if char == "=" and not escaped:
            original = line[:index]
            translated = line[index + 1 :]
            if original and translated:
                return original.replace(r"\=", "="), translated.replace(r"\=", "=")
            return None
        if char == "\\" and not escaped:
            escaped = True
        else:
            escaped = False
    return None


def read_destination(path):
    if not path.exists():
        return {"translations": {}, "keys": {}}

    obj = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(obj, dict):
        raise ValueError("O JSON de destino precisa ser um objeto.")

    if "translations" in obj or "keys" in obj:
        if not isinstance(obj.get("translations", {}), dict):
            raise ValueError("translations deve ser um objeto JSON.")
        return obj

    if not all(isinstance(value, str) for value in obj.values()):
        raise ValueError("O JSON existente não está no formato suportado.")

    return {"translations": obj, "keys": {}}


def main():
    parser = argparse.ArgumentParser(description="Importar TXT XUnity para JSON do Tales of Mortal i18N")
    parser.add_argument("files", nargs="+", type=Path, help="TXTs em ordem de prioridade (maior primeiro)")
    parser.add_argument("-o", "--output", type=Path, required=True, help="JSON de destino")
    args = parser.parse_args()

    imported = {}
    duplicates = 0
    ignored = 0
    for path in args.files:
        with path.open("r", encoding="utf-8-sig") as stream:
            for line in stream:
                value = line.rstrip("\r\n")
                if not value or value.lstrip().startswith(("#", "//")):
                    continue
                entry = split_entry(value)
                if entry is None:
                    ignored += 1
                    continue
                key, translated = entry
                if key not in imported:
                    imported[key] = translated
                elif imported[key] != translated:
                    duplicates += 1

    data = read_destination(args.output)
    previous = data.setdefault("translations", {})
    added = 0
    for key, translated in imported.items():
        if key not in previous:
            previous[key] = translated
            added += 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Adicionadas: {added}; conflitos entre TXT: {duplicates}; linhas ignoradas: {ignored}")
    print("Destino:", args.output)
    print("Traduções já existentes no destino não foram sobrescritas.")


if __name__ == "__main__":
    main()
