import json
import tempfile
import unittest
from pathlib import Path
from scripts.audit_terminology import audit, inspect, CANONICAL


class TerminologyAuditTests(unittest.TestCase):
    def test_checks_placeholders_and_formats(self):
        issues = inspect("Ganhe {0} pontos &11_power& <sprite name=\"sword\">",
                         "Ganhe {1} pontos &11_speed& <sprite name=\"axe\">")
        self.assertIn("placeholder", issues)
        self.assertIn("game-variable", issues)
        self.assertIn("sprite", issues)

    def test_preserves_cooldown_seconds(self):
        source = '<sprite name="jinenglengque"><size=100%></voffset>-1.36s'
        good = '<sprite name="jinenglengque"><size=100%></voffset>-1,36s'
        broken = '<sprite name="jinenglengque"><size=100%></voffset>-1. Espirros'
        self.assertNotIn("seconds-value-mismatch", inspect(source, good))
        self.assertIn("seconds-value-mismatch", inspect(source, broken))

    def test_fixes_only_exact_labels_and_skill_names(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "game.json"
            doc = {
                "module": {"kind": "game", "id": "game:tale-of-immortal"},
                "translations": {
                    "lightning": "relâmpago",
                    "Wood": "Madeira",
                    "wood": "tábua",
                    "木属性": "Madeira",
                    "木属性资质": "Aptidão de Madeira",
                    "Wind": "Brisa",
                    "Fire": "Chama",
                    "A wooden table": "Uma mesa de madeira",
                    "Lightning strikes nearby": "Relâmpago atinge perto",
                    "Obsidian's Signing Firebolt": "Seta de fogo de Obsidian",
                    "Azure Jade": "Jade Azul",
                    "<color=#FF630D>G3 Unity Elixir</color>": "<color=#FF630D>Elixir da Unidade G3</color>",
                    "Recebeu <color=#FF630D>Azure Jade</color>.": "Recebeu <color=#FF630D>Jade Azul</color>.",
                    "An elixir can restore your health.": "Um elixir pode restaurar sua vida.",
                    "Hua Feng": "Hua Feng",
                    "Lucky strike": "Golpe de sorte",
                    "Luck": "Luck",
                    "Looking for a merchant": "Em busca de um mercador",
                    "Skill Rate": "Taxa da habilidade",
                },
                "keys": {},
            }
            path.write_text(json.dumps(doc), encoding="utf-8")
            result = audit(folder, apply=True)
            value = json.loads(path.read_text())["translations"]
            self.assertEqual(value["lightning"], "Raio")
            self.assertEqual(value["Wood"], "Madeira")
            self.assertEqual(value["wood"], "Madeira")
            self.assertEqual(value["木属性"], "Madeira")
            self.assertEqual(value["木属性资质"], "Aptidão com Madeira")
            self.assertEqual(value["Wind"], "Vento")
            self.assertEqual(value["Fire"], "Fogo")
            self.assertEqual(value["A wooden table"], "Uma mesa de madeira")
            self.assertEqual(value["Luck"], "Sorte")
            self.assertEqual(value["Obsidian's Signing Firebolt"],
                             "Obsidian's Signing Firebolt")
            self.assertEqual(value["Lightning strikes nearby"], "Relâmpago atinge perto")
            self.assertEqual(value["Hua Feng"], "Hua Feng")
            self.assertEqual(value["Skill Rate"], "Taxa da habilidade")
            self.assertEqual(value["Looking for a merchant"], "Em busca de um mercador")
            self.assertEqual(value["Azure Jade"], "Azure Jade")
            self.assertEqual(value["<color=#FF630D>G3 Unity Elixir</color>"],
                             "<color=#FF630D>G3 Unity Elixir</color>")
            self.assertEqual(value["Recebeu <color=#FF630D>Azure Jade</color>."],
                             "Recebeu <color=#FF630D>Azure Jade</color>.")
            self.assertEqual(value["An elixir can restore your health."],
                             "Um elixir pode restaurar sua vida.")
            self.assertEqual(result["summary"]["corrected"], 10)
            again = audit(folder, apply=True)
            self.assertEqual(again["summary"].get("corrected", 0), 0)


if __name__ == "__main__":
    unittest.main()
