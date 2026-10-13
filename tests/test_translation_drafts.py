import json
import tempfile
import unittest
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/prepare_translation_drafts.py"
spec = spec_from_file_location("translation_drafts", SCRIPT)
drafts = module_from_spec(spec)
spec.loader.exec_module(drafts)

class DraftTests(unittest.TestCase):
    def test_keeps_human_translation_and_filters_known(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            known = root / "known"
            known.mkdir()
            (known / "game.json").write_text(json.dumps({
                "module": {"kind": "game", "id": "game:tale-of-immortal"},
                "translations": {"Already done": "Já traduzido"}
            }), encoding="utf-8")
            (known / "protected.json").write_text(json.dumps({
                "module": {"kind": "names", "id": "system:protected-names"},
                "names": ["龙儿"]
            }, ensure_ascii=False), encoding="utf-8")
            source = root / "runtime.json"
            source.write_text(json.dumps({
                "format": "talesofmortal-extraction-v1",
                "entries": [
                    {"text": "New quest", "language": "en-candidate"},
                    {"text": "Already done", "language": "en-candidate"},
                    {"text": "龙儿", "language": "zh-und"},
                ],
            }, ensure_ascii=False), encoding="utf-8")
            out = root / "drafts"
            drafts.prepare([source], known, out)
            target = out / "capture_runtime-unattributed.json"
            obj = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(obj["translations"], {"New quest": ""})

            obj["translations"]["New quest"] = "Nova missão"
            target.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
            drafts.prepare([source], known, out)
            merged = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(merged["translations"]["New quest"], "Nova missão")

    def test_groups_offline_per_mod(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            known = root / "known"
            known.mkdir()
            source = root / "offline.json"
            source.write_text(json.dumps({
                "format": "talesofmortal-extraction-v1",
                "catalogs": [
                    {"module": {"kind": "mod", "id": "steam:123", "name": "Test mod"},
                     "entries": [{"text": "Martial art", "language": "en-candidate"}]},
                    {"module": {"kind": "game", "id": "game:tale-of-immortal",
                                "name": "Tale of Immortal"},
                     "entries": [{"text": "功法", "language": "zh-und"}]},
                ],
            }, ensure_ascii=False), encoding="utf-8")
            out = root / "drafts"
            result = drafts.prepare([source], known, out)
            self.assertEqual(len(result["files"]), 2)
            self.assertEqual((out / "steam_123.json").exists(), True)
            self.assertEqual((out / "game_tale-of-immortal.json").exists(), True)

if __name__ == "__main__":
    unittest.main()
