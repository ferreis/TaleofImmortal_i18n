#!/usr/bin/env python3
"""Cria/valida ModExportData.cache para instalar o mod sem usar o Mod Creator.

O formato foi verificado em um mod exportado de Tale of Immortal:
{"projectData": <ModProject.cache>, "items": {...}, "modNamespace": "..."}.
O arquivo é cifrado com o mecanismo de ModExportData do jogo.

Somente gera um novo cache se ainda não existir. Nunca sobrescreve metadados
exportados pelo editor e nunca descarta conteúdo ModData não exportado.
"""
import argparse
import json
import os
from pathlib import Path

if __package__:
    from .toi_crypto import MAGIC, MOD_KEY, decode_mod_file
else:
    from toi_crypto import MAGIC, MOD_KEY, decode_mod_file


def read_json(path):
    obj = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(obj, dict):
        raise ValueError("Metadata inválida: objeto JSON esperado em " + str(path))
    return obj


def encode_export_cache(value):
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return MAGIC + bytes((b + MOD_KEY[i % len(MOD_KEY)]) & 255
                         for i, b in enumerate(payload))


def parse_export_cache(contents):
    decoded = decode_mod_file(contents)
    document = json.loads(decoded.decode("utf-8-sig"))
    if not isinstance(document, dict):
        raise ValueError("ModExportData.cache: objeto JSON esperado.")
    return document


def export_document(project_file, data_file):
    project = read_json(project_file)
    data = read_json(data_file)
    mod_id = project.get("soleID")
    namespace = data.get("modNamespace")
    if not isinstance(mod_id, str) or not mod_id:
        raise ValueError("ModProject.cache não possui soleID válido.")
    if not isinstance(namespace, str) or not namespace:
        raise ValueError("ModData.cache não possui modNamespace válido.")
    if namespace != "MOD_" + mod_id:
        raise ValueError("Identidades diferentes entre soleID e modNamespace.")

    # Este projeto só tem código/ModAssets. Se o Mod Creator ganhar dados
    # próprios de NPCs, não podemos reconstruir as tabelas por adivinhação.
    for section, value in data.items():
        if section in ("modNamespace", "excelMID"):
            continue
        if isinstance(value, dict):
            entries = value.get("items", [])
            if entries:
                raise ValueError("ModData.cache contém dados no campo " + section +
                                 ". Faça exportação pelo editor para preservar esses dados.")

    return {"projectData": project, "items": {}, "modNamespace": namespace}


def prepare(source_dir, output_path):
    source_dir = Path(source_dir)
    target = Path(output_path)
    expected = export_document(source_dir / "ModProject.cache",
                               source_dir / "ModData.cache")
    if target.is_symlink():
        raise ValueError("ModExportData.cache é link simbólico: operação recusada.")
    if target.exists():
        try:
            current = parse_export_cache(target.read_bytes())
        except (UnicodeError, ValueError) as exc:
            raise ValueError("Cache de exportação existente ilegível. "
                             "Não será sobrescrito: " + str(exc))
        if (current.get("projectData", {}).get("soleID") !=
                expected["projectData"]["soleID"] or
                current.get("modNamespace") != expected["modNamespace"]):
            raise ValueError("Cache existente pertence a outro mod. "
                             "Não será sobrescrito: " + str(target))
        return False

    target.parent.mkdir(parents=True, exist_ok=True)
    encoded = encode_export_cache(expected)
    temp = target.with_name(target.name + ".tmp-" + str(os.getpid()))
    try:
        with temp.open("xb") as fp:
            fp.write(encoded)
        if target.exists():
            raise FileExistsError("Outro processo criou o cache simultaneamente.")
        temp.replace(target)
    finally:
        if temp.exists():
            temp.unlink()
    if parse_export_cache(target.read_bytes())["modNamespace"] != expected["modNamespace"]:
        raise ValueError("Cache gerado não passou na validação.")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    default_dir = Path(__file__).resolve().parents[1] / "ModProject_DQKLF9/ModProject"
    parser.add_argument("--source", type=Path, default=default_dir)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        created = prepare(args.source, args.output)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    print(("Cache nativo criado: " if created else "Cache nativo preservado: ") +
          str(args.output))


if __name__ == "__main__":
    main()
