import json
import tempfile
import unittest
from pathlib import Path
from scripts.review_five_passes import audit


class FivePassReviewTests(unittest.TestCase):
    def test_five_passes_detect_independent_defects_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            original = {
                "module": {"kind": "game", "id": "game:tale-of-immortal"},
                "translations": {
                    "伤害&11112_power&": "Dano &11112_evade&",  # pass 1
                    "Lightning": "Relâmpago",                 # pass 2
                    "Obsidian's Signing Firebolt": "Seta de Fogo",  # pass 3
                    "你好": "A tradução é 混合",                # pass 4
                    "你好啊": "Olá",
                },
                "keys": {},
            }
            f = directory / "game.json"
            f.write_text(json.dumps(original, ensure_ascii=False), encoding="utf-8")
            (directory / "fallback.json").write_text(json.dumps({
                "module": {"kind": "fallback", "id": "steam:2990310797"},
                "translations": {"你好啊": "Oi"}, "keys": {}
            }, ensure_ascii=False), encoding="utf-8")
            saved = f.read_bytes()
            results = audit(directory, report=directory.parent / "report.json")
            flags = results["pass_counts"]
            self.assertGreater(flags["1"]["internal-variable-mismatch"], 0)
            self.assertGreater(flags["2"]["glossary-inconsistent"], 0)
            self.assertGreater(flags["3"]["skill-name-changed"], 0)
            self.assertGreater(flags["4"]["chinese-remains"], 0)
            self.assertGreater(flags["5"]["text-collision"], 0)
            self.assertEqual(saved, f.read_bytes())
            self.assertTrue((directory.parent / "report.csv").is_file())

    def test_escaped_unity_sprite_identifiers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "catalog").mkdir()
            (root / "catalog" / "source.json").write_text(json.dumps({
                "module": {"kind": "game", "id": "game:test"},
                "translations": {
                    '<sprite name=\\\"zm_lingshi\\\">': '<sprite name="zm_lingshi">'
                }
            }, ensure_ascii=False), encoding="utf-8")
            result = audit(root / "catalog")
            self.assertNotIn("sprite-mismatch", result["pass_counts"]["1"])

    def test_source_keys_check_matches_source_originals(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "catalog").mkdir()
            (root / "catalog" / "fallback.json").write_text(json.dumps({
                "module": {"kind": "fallback", "id": "steam:2990310797"},
                "translations": {},
                "keys": {"k1": "Dano &11112_evade&"}
            }, ensure_ascii=False), encoding="utf-8")
            source = root / "2990310797.json"
            source.write_text(json.dumps({
                "module": {"id": "steam:2990310797"},
                "localizations": [{"key": "k1", "ch": "伤害&11112_power&"}]
            }, ensure_ascii=False), encoding="utf-8")
            summary = audit(root / "catalog", extracted=source)
            self.assertEqual(summary["pass_counts"]["1"]["internal-variable-mismatch"], 1)


if __name__ == "__main__":
    unittest.main()
