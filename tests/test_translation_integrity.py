#!/usr/bin/env python3
"""Regressões para números e nomes em catálogos do Tale of Immortal.

Executado pela etapa de unittest da CI; não depende do jogo nem de Mono.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "mod/i18n/pt-BR"
TAG = re.compile(r"<[^<>]*>")
SECONDS = re.compile(r"(?<![\w])([+-]?\d+(?:[.,]\d+)?)s\b")
NUMERIC_ONLY = re.compile(r"\s*[+-]?\d+(?:[./]\d+)*\s*")


def values_with_seconds(text):
    # Atributos HTML/Unity contêm números que não fazem parte dos efeitos.
    plain = TAG.sub("", text)
    return [item.replace(",", ".") for item in SECONDS.findall(plain)]


class TranslationIntegrityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogs = {}
        for name in ("game.json", "zzz-auto.json"):
            data = json.loads((ROOT / name).read_text(encoding="utf-8"))
            cls.catalogs[name] = data["translations"]

    def test_rich_text_tags_are_unchanged(self):
        for filename, catalog in self.catalogs.items():
            for original, translated in catalog.items():
                with self.subTest(file=filename, text=original[:70]):
                    self.assertEqual(TAG.findall(original), TAG.findall(translated))

    def test_numeric_only_labels_are_unchanged(self):
        # Em particular, 2/31 não pode virar 31/02.
        for filename, catalog in self.catalogs.items():
            for original, translated in catalog.items():
                if NUMERIC_ONLY.fullmatch(original):
                    with self.subTest(file=filename, original=original):
                        self.assertEqual(original, translated)

    def test_second_values_are_never_translated(self):
        # Ex.: -1.36s, +11.99s, 2.06s não são frases e não devem
        # virar palavras, horários ou números diferentes.
        for filename, catalog in self.catalogs.items():
            for original, translated in catalog.items():
                original_seconds = values_with_seconds(original)
                if original_seconds:
                    with self.subTest(file=filename, text=original[:80]):
                        self.assertEqual(
                            original_seconds, values_with_seconds(translated)
                        )

    def test_known_proper_names_and_stats(self):
        game = self.catalogs["game.json"]
        fallback = self.catalogs["zzz-auto.json"]
        self.assertEqual(game["FengJi Cidade"], "FengJi Cidade")
        self.assertEqual(fallback["QiLin Cidade"], "QiLin Cidade")
        self.assertEqual(fallback["Deng Ziyin"], "Deng Ziyin")
        self.assertEqual(fallback["Shaper's Blooming Mover"], "Shaper's Blooming Mover")
        self.assertIn("RES. Crítica", game["CRIT RES: +44"])
        self.assertIn("RES. Crítica", fallback["CRIT RES: 680"])


if __name__ == "__main__":
    unittest.main()
