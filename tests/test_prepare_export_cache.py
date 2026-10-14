import json
import tempfile
import unittest
from pathlib import Path

from scripts.prepare_export_cache import (
    encode_export_cache, export_document, parse_export_cache, prepare,
)
from scripts.toi_crypto import MAGIC, decode_mod_file


class NativeModInstallerCacheTests(unittest.TestCase):
    def write_metadata(self, base):
        base.mkdir(parents=True, exist_ok=True)
        project = {"soleID": "DQKLF9", "createTicks": 639274613758756709,
                   "name": "Tales of Mortal i18N", "author": "Ferreis",
                   "exportVer": 1, "excelEncrypt": True}
        data = {"roleCreateFeature": {"items": [], "groupName": []},
                "fortuitousEvent": {"items": [], "groupName": [],
                                   "cdGroup": {"value": -457102405}},
                "excelMID": -1624146157, "modNamespace": "MOD_DQKLF9"}
        (base / "ModProject.cache").write_text(json.dumps(project), encoding="utf-8")
        (base / "ModData.cache").write_text(json.dumps(data), encoding="utf-8")
        return project

    def test_generates_real_encrypted_export_cache_and_preserves_existing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "metadata"
            project = self.write_metadata(source)
            output = root / "game/ModExportData/Mod_DQKLF9/ModExportData.cache"
            self.assertTrue(prepare(source, output))
            raw = output.read_bytes()
            self.assertTrue(raw.startswith(MAGIC))
            decoded = json.loads(decode_mod_file(raw).decode("utf-8"))
            self.assertEqual(decoded["projectData"], project)
            self.assertEqual(decoded["modNamespace"], "MOD_DQKLF9")
            self.assertEqual(decoded["items"], {})
            self.assertFalse(prepare(source, output))
            self.assertEqual(raw, output.read_bytes())

    def test_keeps_game_generated_cache_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "metadata"
            self.write_metadata(source)
            output = root / "export.cache"
            doc = export_document(source / "ModProject.cache",
                                  source / "ModData.cache")
            doc["items"] = {"LocalText": [{"ch": "测试", "key": "existing"}]}
            raw = encode_export_cache(doc)
            output.write_bytes(raw)
            self.assertFalse(prepare(source, output))
            self.assertEqual(output.read_bytes(), raw)

    def test_refuses_different_mod_and_invalid_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "metadata"
            self.write_metadata(source)
            output = root / "export.cache"
            bad = export_document(source / "ModProject.cache",
                                  source / "ModData.cache")
            bad["projectData"]["soleID"] = "OTHER"
            original = encode_export_cache(bad)
            output.write_bytes(original)
            with self.assertRaisesRegex(ValueError, "outro mod"):
                prepare(source, output)
            self.assertEqual(output.read_bytes(), original)
            output.unlink()
            data_file = source / "ModData.cache"
            bad_data = json.loads(data_file.read_text())
            bad_data["roleCreateFeature"]["items"] = [{"id": 1}]
            data_file.write_text(json.dumps(bad_data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Faça exportação"):
                prepare(source, output)
            self.assertFalse(output.exists())

    def test_detects_corrupt_cache_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "metadata"
            self.write_metadata(source)
            output = root / "export.cache"
            output.write_bytes(b"\x00\xffcorrupt")
            with self.assertRaisesRegex(ValueError, "ilegível"):
                prepare(source, output)
            self.assertEqual(output.read_bytes(), b"\x00\xffcorrupt")


if __name__ == "__main__":
    unittest.main()
