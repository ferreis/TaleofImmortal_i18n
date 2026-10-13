import json
import tempfile
import unittest
from pathlib import Path
from scripts.import_workshop_ptbr import prepare, normalize_from_source, structural_problem


class WorkshopPtBrImportTests(unittest.TestCase):
    def test_preserves_manual_translations_and_rejects_ambiguous_text(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            original = root / "2990310797.json"
            original.write_text(json.dumps({
                "format": "talesofmortal-workshop-extraction-v1",
                "module": {"id": "steam:2990310797"},
                "localizations": [
                    {"key": "key_one", "ch": "你好", "en": "Olá"},
                    {"key": "key_two", "ch": "你好", "en": "Saudações"},
                    {"key": "key_three", "ch": "欢迎来到宗门", "en": "Bem-vindo à seita"},
                    {"key": "key_four", "ch": "突破到{0}境界", "en": "Avançar para {1}"},
                    {"key": "key_five", "ch": "已经完成", "en": "Concluído"},
                    {"key": "key_six", "ch": "龙儿", "en": "Longe"},
                    {"key": "key_seven", "ch": "宗门公告", "en": "Aviso da seita"},
                    {"key": "key_eight", "ch": "护盾&s_hudun&", "en": "Escudo &s_other&"},
                    {"key": "key_nine", "ch": "获得$s_lingqi$", "en": "Obter $s_four$"},
                    {"key": "key_ten", "ch": "<color=red>获得道具</color>", "en": "Obter item"},
                ],
            }, ensure_ascii=False), encoding="utf-8")
            catalog = root / "catalogs"
            catalog.mkdir()
            (catalog / "game.json").write_text(json.dumps({
                "module": {"id": "game:tale-of-immortal", "kind": "game"},
                "translations": {"已经完成": "Finalizado"},
                "keys": {"key_seven": "Outro valor"}
            }, ensure_ascii=False), encoding="utf-8")
            (catalog / "names.json").write_text(json.dumps({
                "module": {"id": "system:protected-names", "kind": "names"},
                "names": ["龙儿"],
            }, ensure_ascii=False), encoding="utf-8")
            target = catalog / "Workshop_2990310797.json"
            target.write_text(json.dumps({
                "module": {"id": "steam:2990310797", "kind": "mod"},
                "translations": {}, "keys": {}
            }), encoding="utf-8")
            report = prepare(original, catalog, target)
            result = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(result["module"]["kind"], "fallback")
            self.assertEqual(result["translations"],
                             {"欢迎来到宗门": "Bem-vindo à seita", "宗门公告": "Aviso da seita"})
            self.assertEqual(result["keys"]["key_one"], "Olá")
            self.assertEqual(result["keys"]["key_two"], "Saudações")
            self.assertNotIn("key_four", result["keys"])
            self.assertNotIn("key_six", result["keys"])
            self.assertNotIn("key_seven", result["keys"])
            self.assertNotIn("key_eight", result["keys"])
            self.assertNotIn("key_nine", result["keys"])
            self.assertNotIn("key_ten", result["keys"])
            self.assertGreaterEqual(report["internalVariableMismatch"], 2)
            self.assertGreaterEqual(report["richTextMismatch"], 1)
            self.assertEqual(report["skippedAmbiguousChinese"], 1)
            again = prepare(original, catalog, target)
            self.assertEqual(again["addedKeys"], 0)
            self.assertEqual(again["addedChineseTranslations"], 0)

    def test_normalizes_source_grounded_terminology_and_keeps_proper_names(self):
        self.assertEqual(
            normalize_from_source("移动速度降低30%。", "Agilidade -30%"),
            "Velocidade de movimento -30%")
        self.assertEqual(
            normalize_from_source("技能范围&30133_jnfwUp&%", "Faixa de habilidade &30133_jnfwUp&%"),
            "Alcance da habilidade &30133_jnfwUp&%")
        self.assertEqual(normalize_from_source("增加15%幸运", "Tipo +15%"), "Sorte +15%")
        self.assertEqual(normalize_from_source("雷属性伤害", "Dano de Relâmpago"),
                         "Dano de Raio")
        self.assertEqual(normalize_from_source("暮仙第一刀修", "Em Xian No. 1 Cultivador"),
                         "Mu Xian No. 1 Cultivador")
        self.assertEqual(normalize_from_source("敏捷增加", "Agilidade aumenta"),
                         "Agilidade aumenta")
        self.assertEqual(
            structural_problem('<sprite name=\\\"zm_lingshi\\\">：{0}',
                               '<sprite name="zm_lingshi">: {0}'),
            None)
        self.assertEqual(
            structural_problem('<sprite name=\\\"zm_lingshi\\\">',
                               '<sprite name="zm_other">'),
            "spriteMismatch")
        self.assertEqual(
            structural_problem("<color=red>消息</color>",
                               "<color=red>Mensagem"),
            "richTextMismatch")
        self.assertEqual(
            structural_problem("伤害&15112_hdsx%1&", "Dano &15112_other%1&"),
            "internalVariableMismatch")
        self.assertEqual(
            structural_problem("伤害&321_spell|/321_one|x321_two&",
                               "Dano &321_spell|/321_one|x321_two&"),
            None)

    def test_reimport_removes_previously_saved_protected_and_ambiguous_values(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "2990310797.json"
            source.write_text(json.dumps({
                "format": "talesofmortal-workshop-extraction-v1",
                "module": {"id": "steam:2990310797"},
                "localizations": [
                    {"key": "protect", "ch": "龙儿", "en": "Dragon"},
                    {"key": "a", "ch": "你好", "en": "Olá"},
                    {"key": "b", "ch": "你好", "en": "Saudações"},
                    {"key": "dup", "ch": "修炼", "en": "Cultivar"},
                    {"key": "dup", "ch": "检查", "en": "Inspecionar"},
                    {"key": "manual", "ch": "欢迎来到宗门", "en": "Bem-vindo à seita"},
                ],
            }, ensure_ascii=False), encoding="utf-8")
            folder = root / "catalog"
            folder.mkdir()
            (folder / "names.json").write_text(json.dumps({
                "module": {"kind": "names", "id": "names"},
                "names": ["龙儿"]
            }, ensure_ascii=False), encoding="utf-8")
            output = folder / "Workshop_2990310797.json"
            output.write_text(json.dumps({
                "module": {"id": "steam:2990310797", "kind": "fallback"},
                "translations": {"龙儿": "Dragon", "你好": "Oi",
                                 "欢迎来到宗门": "Bem-vindo à seita!"},
                "keys": {"protect": "Dragon", "dup": "Cultivar",
                         "manual": "Seja bem-vindo à seita!"}
            }, ensure_ascii=False), encoding="utf-8")
            result = prepare(source, folder, output)
            current = json.loads(output.read_text(encoding="utf-8"))
            self.assertNotIn("龙儿", current["translations"])
            self.assertNotIn("你好", current["translations"])
            self.assertNotIn("protect", current["keys"])
            self.assertNotIn("dup", current["keys"])
            # Preserve manually improved, structurally valid translations.
            self.assertEqual(current["translations"]["欢迎来到宗门"],
                             "Bem-vindo à seita!")
            self.assertEqual(current["keys"]["manual"],
                             "Seja bem-vindo à seita!")
            self.assertGreaterEqual(result["removedProtectedOrAmbiguousSavedText"], 2)
            self.assertGreaterEqual(result["removedProtectedOrConflictingSavedKeys"], 2)
            self.assertGreaterEqual(result["conflictingSourceKeys"], 2)

    def test_rejects_wrong_workshop_id(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source.json"
            path.write_text(json.dumps({
                "format": "talesofmortal-workshop-extraction-v1",
                "module": {"id": "steam:123"},
                "localizations": [{"key": "k", "ch": "中国", "en": "China"}]
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "2990310797"):
                prepare(path, Path(folder), Path(folder) / "out.json")


if __name__ == "__main__":
    unittest.main()
