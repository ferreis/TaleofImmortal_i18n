using System;
using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

namespace TalesOfMortalI18N
{
    internal static class TranslationPatches
    {
        private static readonly BindingFlags NonPublicStatic =
            BindingFlags.NonPublic | BindingFlags.Static;

        internal static int Install(Harmony harmony)
        {
            int count = 0;
            var installed = new HashSet<MethodBase>();

            count += InstallOne(harmony, installed,
                AccessTools.Method(typeof(GameTool), "LS", new[] { typeof(string) }),
                null, nameof(AfterGameToolLs), "GameTool.LS(string)");

            count += InstallOne(harmony, installed,
                AccessTools.Method(typeof(GameTool), "LS", new[] { typeof(string), typeof(int) }),
                null, nameof(AfterGameToolLsWithBackground), "GameTool.LS(string,int)");

            count += InstallOne(harmony, installed,
                AccessTools.Method(typeof(ConfLocalTextEx), "text", new[] { typeof(ConfLocalTextItem) }),
                null, nameof(AfterLocalText), "ConfLocalTextEx.text");

            count += InstallOne(harmony, installed,
                AccessTools.PropertySetter(typeof(Text), "text"),
                nameof(BeforeSetText), null, "UnityEngine.UI.Text.text");

            count += InstallOne(harmony, installed,
                AccessTools.PropertySetter(typeof(TMP_Text), "text"),
                nameof(BeforeSetText), null, "TMP_Text.text");

            count += InstallOne(harmony, installed,
                AccessTools.PropertySetter(typeof(TextMeshProUGUI), "text"),
                nameof(BeforeSetText), null, "TextMeshProUGUI.text");

            count += InstallOne(harmony, installed,
                AccessTools.PropertySetter(typeof(TextMeshPro), "text"),
                nameof(BeforeSetText), null, "TextMeshPro.text");

            return count;
        }

        private static int InstallOne(
            Harmony harmony,
            HashSet<MethodBase> installed,
            MethodBase target,
            string prefixName,
            string postfixName,
            string label)
        {
            if (target == null)
            {
                Debug.LogWarning("[Tales of Mortal i18N] Hook indisponível: " + label);
                return 0;
            }

            if (installed.Contains(target))
                return 0;

            try
            {
                HarmonyMethod prefix = prefixName == null ? null :
                    new HarmonyMethod(typeof(TranslationPatches).GetMethod(prefixName, NonPublicStatic));
                HarmonyMethod postfix = postfixName == null ? null :
                    new HarmonyMethod(typeof(TranslationPatches).GetMethod(postfixName, NonPublicStatic));

                harmony.Patch(target, prefix, postfix);
                installed.Add(target);
                return 1;
            }
            catch (Exception error)
            {
                Debug.LogWarning("[Tales of Mortal i18N] Falha no hook " + label + ": " + error.Message);
                return 0;
            }
        }

        // Recebe o texto antes que o componente Unity o desenhe.
        private static void BeforeSetText(ref string __0)
        {
            __0 = TranslationCatalog.TranslateText(__0);
        }

        // game tool keys têm preferência sobre o texto final.
        private static void AfterGameToolLs(string __0, ref string __result)
        {
            string translated;
            if (TranslationCatalog.TryKey(__0, out translated))
                __result = GameTool.TextToData(translated, 1);
            else
                __result = TranslationCatalog.TranslateText(__result);
        }

        private static void AfterGameToolLsWithBackground(
            string __0, int __1, ref string __result)
        {
            string translated;
            if (TranslationCatalog.TryKey(__0, out translated))
                __result = GameTool.TextToData(translated, __1);
            else
                __result = TranslationCatalog.TranslateText(__result);
        }

        private static void AfterLocalText(ConfLocalTextItem __0, ref string __result)
        {
            string translated;
            if (__0 != null && TranslationCatalog.TryKey(__0.key, out translated))
                __result = GameTool.TextToData(translated, 1);
            else
                __result = TranslationCatalog.TranslateText(__result);
        }
    }
}
