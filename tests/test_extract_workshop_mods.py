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
            self.assertEqual({path.name for path in out.glob("*.json")},
                             {"2814722600.json", "2864011606.json", "123456.json", "index.json"})
            self.assertFalse((out / "2814722600").exists())

            admin = json.loads((out / "2814722600.json").read_text(encoding="utf-8"))
            extra = json.loads((out / "2864011606.json").read_text(encoding="utf-8"))
            empty = json.loads((out / "123456.json").read_text(encoding="utf-8"))
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
                json.loads((out / "111.json").read_text())["entries"]
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
            entries = json.loads((base / "out/321.json").read_text())["entries"]
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


    def test_reports_unreadable_files_and_uses_decrypted_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            steam = base / "steamapps/workshop/content/1468810"
            original = steam / "2864011606/ModExcel/LocalText.json"
            original.parent.mkdir(parents=True)
            original.write_bytes(b"\\x00\\x03unreadable-file")
            decrypted = base / "decrypted-2864011606"
            write_json(decrypted / "ModExcel/LocalText.json", [
                {"key": "myMod_dialogue1", "en": "Welcome to the sect",
                 "ch": "欢迎加入宗门", "tc": "歡迎加入宗門"}
            ])
            out = base / "out"
            result = workshop.run([steam], out, base / "known",
                                  decrypted_dirs={"2864011606": decrypted})
            self.assertEqual(result["mods_processed"], 1)
            document = json.loads((out / "2864011606.json").read_text())
            self.assertEqual(document["stats"]["files_skipped"], 1)
            self.assertEqual(len(document["localizations"]), 1)
            self.assertEqual(document["localizations"][0]["key"], "myMod_dialogue1")
            self.assertEqual(document["localizations"][0]["file"],
                             "decrypted/ModExcel/LocalText.json")
            self.assertIn("歡迎加入宗門", {e["text"] for e in document["entries"]})

    def test_skips_mod_creator_template_unless_requested(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            steam = base / "steamapps/workshop/content/1468810"
            mod = steam / "111/ModAssets"
            mod.mkdir(parents=True)
            (mod / "这个目录下的所有文件都会被一起导出（打开查看说明）.txt").write_text(
                "在代码中获取模组根目录：", encoding="utf-8")
            (mod / "dialogues.txt").write_text("Join our sect today",
                                               encoding="utf-8")
            out = base / "out"
            workshop.run([steam], out)
            texts = {entry["text"] for entry in
                     json.loads((out / "111.json").read_text())["entries"]}
            self.assertEqual(texts, {"Join our sect today"})
            workshop.run([steam], out, include_documentation=True)
            texts = {entry["text"] for entry in
                     json.loads((out / "111.json").read_text())["entries"]}
            self.assertIn("在代码中获取模组根目录：", texts)


if __name__ == "__main__":
    unittest.main()
