import json
import tempfile
import unittest
from pathlib import Path

from scripts import extract_workshop_mods as workshop


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


class WorkshopExtractorTests(unittest.TestCase):
    def test_one_folder_and_one_json_per_mod(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            steam = base / "steamapps/workshop/content/1468810"
            write_json(steam / "2814722600/ModExcel/LocalText.json", [
                {"key": "schoolAdmin_recruit", "en": "Recruit disciple",
                 "ch": "招募弟子", "tc": "招募弟子"},
                {"key": "schoolAdmin_ok", "en": "Confirm", "ch": "确认", "tc": "確認"}
            ])
            write_json(steam / "2864011606/ModAssets/Config.json", {
                "怀孕时长": "Duration of pregnancy",
                "debug": "#hpMax",
                "programmer_name": "GameTool.GetInstance()",
                "filepath": "bin/ModMain.dll",
            })
            (steam / "2864011606/ModExcel").mkdir(parents=True)
            (steam / "2864011606/ModExcel/broken.json").write_bytes(b"not\x00json")
            (steam / "unknown").mkdir()
            (steam / "123456/ModCode").mkdir(parents=True)
            (steam / "123456/ModCode/DLL.dll").write_bytes(b"ignored binary")

            out = base / "results"
            summary = workshop.run([steam], out, base / "not-installed")
            self.assertEqual(summary["mods_processed"], 3)
            self.assertEqual({x["workshopId"] for x in summary["mods"]},
                             {"2814722600", "2864011606", "123456"})
            self.assertTrue((out / "index.json").is_file())

            admin = json.loads((out / "2814722600/texts.json").read_text(encoding="utf-8"))
            extra = json.loads((out / "2864011606/texts.json").read_text(encoding="utf-8"))
            empty = json.loads((out / "123456/texts.json").read_text(encoding="utf-8"))
            self.assertEqual(admin["module"]["id"], "steam:2814722600")
            self.assertEqual(extra["module"]["id"], "steam:2864011606")
            self.assertEqual(len(admin["localizations"]), 2)
            self.assertEqual(admin["localizations"][0]["key"], "schoolAdmin_recruit")
            originals = {entry["text"]: entry for entry in admin["entries"]}
            self.assertEqual(set(originals), {"Recruit disciple", "招募弟子", "Confirm", "确认", "確認"})
            self.assertIn("schoolAdmin_recruit", originals["招募弟子"]["localizationKeys"])
            self.assertIn("schoolAdmin_ok", originals["Confirm"]["localizationKeys"])

            extras = {entry["text"] for entry in extra["entries"]}
            self.assertIn("怀孕时长", extras)
            self.assertIn("Duration of pregnancy", extras)
            self.assertNotIn("#hpMax", extras)
            self.assertNotIn("bin/ModMain.dll", extras)
            self.assertNotIn("GameTool.GetInstance()", extras)
            self.assertEqual(extra["stats"]["files_skipped"], 1)
            self.assertEqual(empty["stats"]["unique_texts"], 0)

    def test_does_not_overwrite_workshop_and_filters_existing(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            steam = base / "steamapps/workshop/content/1468810"
            mod_file = steam / "111/ModAssets/texts.json"
            write_json(mod_file, {"label": "Recruit disciple", "话术": "招募弟子",
                                  "other": "龙儿"})
            original = mod_file.read_bytes()
            known = base / "i18n/pt-BR"
            write_json(known / "SectAdmin.json", {
                "translations": {"Recruit disciple": "Recrutar discípulo"}
            })
            write_json(known / "protected-names.json", {
                "names": ["龙儿"]
            })
            out = base / "results"
            workshop.run([steam], out, known)
            workshop.run([steam], out, known)
            self.assertEqual(mod_file.read_bytes(), original)
            entries = {
                e["text"]: e for e in
                json.loads((out / "111/texts.json").read_text())["entries"]
            }
            self.assertEqual(entries["Recruit disciple"]["translatedInProject"], True)
            self.assertNotIn("龙儿", entries)

    def test_multiple_workshop_libraries_and_duplicate_id(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            a = base / "lib1/steamapps/workshop/content/1468810"
            b = base / "lib2/steamapps/workshop/content/1468810"
            write_json(a / "321/ModAssets/data.json", {"text": "First mod"})
            write_json(b / "321/ModAssets/data.json", {"text": "Duplicate"})
            write_json(b / "654/ModAssets/data.json", {"text": "Second mod"})
            result = workshop.run([a, b], base / "out")
            self.assertEqual(result["mods_processed"], 2)
            entries = json.loads((base / "out/321/texts.json").read_text())["entries"]
            self.assertIn("First mod", [e["text"] for e in entries])
            self.assertNotIn("Duplicate", [e["text"] for e in entries])

    def test_refuses_writing_inside_workshop(self):
        with tempfile.TemporaryDirectory() as temp:
            steam = Path(temp) / "steamapps/workshop/content/1468810"
            steam.mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, "dentro da Steam Workshop"):
                workshop.run([steam], steam / "extracted")

    def test_language_and_technical_filter(self):
        known = set()
        self.assertIsNone(workshop.readable_candidate("#hpMax", "en", known))
        self.assertIsNone(workshop.readable_candidate("--backend=burst-llvm-11", "en", known))
        self.assertIsNone(workshop.readable_candidate("GameTool.GetInstance()", "en", known))
        self.assertIsNone(workshop.readable_candidate("SomeModelClass", "$.key", known))
        self.assertEqual(workshop.readable_candidate("Save game", "$.button", known)[0], "Save game")
        self.assertEqual(workshop.readable_candidate("保存游戏", "$.title", known)[0], "保存游戏")


if __name__ == "__main__":
    unittest.main()
