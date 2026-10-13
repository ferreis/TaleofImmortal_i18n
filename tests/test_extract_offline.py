import json
import tempfile
import unittest
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/extract_offline.py"
spec = spec_from_file_location("extract_offline", MODULE_PATH)
extract = module_from_spec(spec)
spec.loader.exec_module(extract)

class OfflineExtractorTests(unittest.TestCase):
    def test_game_and_workshop_sources(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "steamapps"
            game = root / "common/TOI"
            workshop = root / "workshop/content/1468810/2814722600"
            (game / "config").mkdir(parents=True)
            (workshop / "assets").mkdir(parents=True)

            (game / "config/game.json").write_text(
                json.dumps({"items": ["简体中文", "繁體中文", "Start your adventure"]},
                           ensure_ascii=False), encoding="utf-8")
            (workshop / "assets/ui.xml").write_text(
                "<root><label>Recruit disciple</label><line>招募弟子</line></root>",
                encoding="utf-8")
            result = Path(temp) / "offline.json"
            stats = extract.scan([game, workshop], result)
            doc = json.loads(result.read_text(encoding="utf-8"))
            self.assertEqual(stats["files_scanned"], 2)
            self.assertEqual(len(doc["catalogs"]), 2)
            ids = {row["module"]["id"] for row in doc["catalogs"]}
            self.assertEqual(ids, {"game:tale-of-immortal", "steam:2814722600"})
            self.assertTrue(any("招募弟子" in {e["text"] for e in row["entries"]}
                                for row in doc["catalogs"]))
            self.assertEqual(doc["format"], "talesofmortal-extraction-v1")
            self.assertTrue(all("translations" not in row for row in doc["catalogs"]))

    def test_ignores_binary_and_translation_directories(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "i18n").mkdir()
            (root / "i18n/pt-BR.json").write_text(
                '{"translation":"Texto que não pode ser capturado"}', encoding="utf-8")
            (root / "binary.json").write_bytes(b'hello\x00world')
            (root / "ordinary.txt").write_text("View all sects", encoding="utf-8")
            stats = extract.scan([root], root / "result.json")
            self.assertEqual(stats["files_scanned"], 1)
            self.assertEqual(stats["files_skipped"], 1)
            rows = json.loads((root / "result.json").read_text())["catalogs"]
            self.assertTrue(any(e["text"] == "View all sects"
                                for row in rows for e in row["entries"]))

if __name__ == "__main__":
    unittest.main()
