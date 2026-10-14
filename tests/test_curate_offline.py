import unittest
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec

script = Path(__file__).resolve().parents[1] / "scripts/curate_offline.py"
spec = spec_from_file_location("curate_offline", script)
mod = module_from_spec(spec)
spec.loader.exec_module(mod)

class CurateOfflineTests(unittest.TestCase):
    def test_extracts_language_columns_and_config_fields(self):
        sample = {
            "stats": {"entries_unique": 8},
            "catalogs": [
                {"module": {"id": "steam:2814722600", "kind": "mod", "name": "SectAdmin"},
                 "entries": [
                    {"text": "Recruit", "locations": [
                        {"file": "2814722600/ModExcel/LocalText.json", "context": "$[4].en"}]},
                    {"text": "招募", "locations": [
                        {"file": "2814722600/ModExcel/LocalText.json", "context": "$[4].ch"}]},
                    {"text": "招募", "locations": [
                        {"file": "2814722600/ModExcel/LocalText.json", "context": "$[4].tc"}]},
                    {"text": "schoolAdmin_recruit", "locations": [
                        {"file": "2814722600/ModExcel/LocalText.json", "context": "$[4].key"}]},
                ]},
                {"module": {"id": "steam:2864011606", "kind": "mod", "name": "Test"},
                 "entries": [
                    {"text": "怀孕时长", "locations": [
                        {"file": "2864011606/ModAssets/Config.json", "context": "$.<key>"}]},
                    {"text": "g.mod.GetModPathRoot()", "locations": [
                        {"file": "2864011606/ModAssets/help.txt", "context": "line:1"}]},
                ]}
            ]
        }
        out = mod.curate(sample)
        self.assertEqual(out["stats"]["localization_rows"], 1)
        self.assertEqual(out["stats"]["config_labels"], 1)
        self.assertEqual(out["stats"]["selected_entries"], 5)
        a = next(c for c in out["catalogs"] if c["module"]["id"] == "steam:2814722600")
        self.assertEqual(a["rows"][0]["key"], "schoolAdmin_recruit")
        self.assertEqual(a["rows"][0]["simplified"], "招募")
        b = next(c for c in out["catalogs"] if c["module"]["id"] == "steam:2864011606")
        self.assertIn("怀孕时长", b["configLabels"])

if __name__ == "__main__":
    unittest.main()
