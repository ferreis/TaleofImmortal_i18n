using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;

namespace TalesOfMortalI18N
{
    // O Harmony e as classes do jogo são resolvidos quando o mod inicia.
    // O compilador só precisa do .NET Framework.
    internal sealed class ReflectionPatcher
    {
        private const BindingFlags AllMethods =
            BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static;

        private readonly string id;
        private object harmony;
        private Type harmonyMethodType;
        private MethodInfo harmonyPatchMethod;
        private MethodInfo unpatchSelfMethod;

        internal ReflectionPatcher(string harmonyId)
        {
            id = harmonyId;
        }

        internal int Install()
        {
            Type harmonyType = FindType("HarmonyLib.Harmony");
            harmonyMethodType = FindType("HarmonyLib.HarmonyMethod");

            if (harmonyType == null || harmonyMethodType == null)
            {
                ModLog.Error("Harmony não está carregado. Este ModCode precisa do MelonLoader do jogo.");
                return 0;
            }

            harmony = Activator.CreateInstance(harmonyType, id);
            harmonyPatchMethod = harmonyType.GetMethods(AllMethods).FirstOrDefault(m =>
            {
                ParameterInfo[] parameters = m.GetParameters();
                return m.Name == "Patch" && parameters.Length >= 3 &&
                    parameters[0].ParameterType == typeof(MethodBase);
            });
            unpatchSelfMethod = harmonyType.GetMethod("UnpatchSelf", AllMethods, null, Type.EmptyTypes, null);

            if (harmonyPatchMethod == null)
            {
                ModLog.Error("Método Harmony.Patch não encontrado na versão instalada.");
                return 0;
            }

            var patched = new HashSet<MethodBase>();
            int installed = 0;

            Type gameTool = FindType("GameTool");
            installed += Patch(patched, ExactMethod(gameTool, "LS", typeof(string)),
                null, "AfterGameToolLs", "GameTool.LS(string)");
            installed += Patch(patched, ExactMethod(gameTool, "LS", typeof(string), typeof(int)),
                null, "AfterGameToolLsWithBackground", "GameTool.LS(string, int)");

            Type localText = FindType("ConfLocalTextEx");
            MethodInfo textMethod = localText == null ? null :
                localText.GetMethods(AllMethods).FirstOrDefault(m =>
                {
                    ParameterInfo[] parameters = m.GetParameters();
                    return m.Name == "text" && m.ReturnType == typeof(string) &&
                        parameters.Length == 1 && parameters[0].ParameterType.Name == "ConfLocalTextItem";
                });
            installed += Patch(patched, textMethod, null, "AfterLocalText", "ConfLocalTextEx.text");

            installed += Patch(patched, TextSetter("UnityEngine.UI.Text"),
                "BeforeSetText", null, "UnityEngine.UI.Text.text");
            installed += Patch(patched, TextSetter("TMPro.TMP_Text"),
                "BeforeSetText", null, "TMPro.TMP_Text.text");
            installed += Patch(patched, TextSetter("TMPro.TextMeshProUGUI"),
                "BeforeSetText", null, "TMPro.TextMeshProUGUI.text");
            installed += Patch(patched, TextSetter("TMPro.TextMeshPro"),
                "BeforeSetText", null, "TMPro.TextMeshPro.text");

            return installed;
        }

        internal void Unpatch()
        {
            if (harmony == null) return;
            try
            {
                if (unpatchSelfMethod != null)
                    unpatchSelfMethod.Invoke(harmony, null);
                else
                    ModLog.Warning("UnpatchSelf não disponível na versão do Harmony.");
            }
            catch (Exception error)
            {
                ModLog.Warning("Erro ao remover hooks: " + error.Message);
            }
            harmony = null;
        }

        private int Patch(HashSet<MethodBase> patched, MethodBase target,
            string prefixName, string postfixName, string label)
        {
            if (target == null)
            {
                ModLog.Warning("Hook indisponível: " + label);
                return 0;
            }
            if (!patched.Add(target)) return 0;

            try
            {
                MethodInfo prefix = prefixName == null ? null :
                    typeof(ReflectionPatcher).GetMethod(prefixName, BindingFlags.NonPublic | BindingFlags.Static);
                MethodInfo postfix = postfixName == null ? null :
                    typeof(ReflectionPatcher).GetMethod(postfixName, BindingFlags.NonPublic | BindingFlags.Static);

                if ((prefixName != null && prefix == null) || (postfixName != null && postfix == null))
                    throw new MissingMethodException("Método de patch não encontrado.");

                ParameterInfo[] parameters = harmonyPatchMethod.GetParameters();
                object[] args = new object[parameters.Length];
                args[0] = target;
                args[1] = prefix == null ? null : Activator.CreateInstance(harmonyMethodType, prefix);
                args[2] = postfix == null ? null : Activator.CreateInstance(harmonyMethodType, postfix);
                harmonyPatchMethod.Invoke(harmony, args);
                return 1;
            }
            catch (Exception error)
            {
                ModLog.Warning("Falha ao instalar " + label + ": " + error.Message);
                return 0;
            }
        }

        private static MethodInfo TextSetter(string typeName)
        {
            Type type = FindType(typeName);
            if (type == null) return null;
            PropertyInfo property = type.GetProperty("text", AllMethods);
            return property == null ? null : property.GetSetMethod(true);
        }

        private static MethodInfo ExactMethod(Type type, string name, params Type[] args)
        {
            return type == null ? null : type.GetMethod(name, AllMethods, null, args, null);
        }

        private static Type FindType(string fullName)
        {
            foreach (Assembly assembly in AppDomain.CurrentDomain.GetAssemblies())
            {
                Type type = assembly.GetType(fullName, false);
                if (type != null) return type;
            }
            return Type.GetType(fullName, false);
        }

        private static object ReadKey(object item)
        {
            if (item == null) return null;
            Type type = item.GetType();
            FieldInfo field = type.GetField("key", AllMethods);
            if (field != null) return field.GetValue(item);
            PropertyInfo property = type.GetProperty("key", AllMethods);
            return property == null ? null : property.GetValue(item, null);
        }

        private static string FormatText(string text, int background)
        {
            // Preserva o mecanismo do jogo que expande tags e placeholders.
            try
            {
                Type gameTool = FindType("GameTool");
                MethodInfo formatter = ExactMethod(gameTool, "TextToData", typeof(string), typeof(int));
                if (formatter != null)
                    return formatter.Invoke(null, new object[] { text, background }) as string ?? text;
            }
            catch (Exception error)
            {
                ModLog.Warning("Falha ao formatar tradução: " + error.Message);
            }
            return text;
        }

        private static bool textSetterErrorLogged;

        private static void BeforeSetText(ref string __0)
        {
            // Harmony executes this inside Unity's IL2CPP Text setter.
            // NEVER modify font/layout properties here: Unity may be rebuilding
            // the same text component, causing a native NullReferenceException.
            // Only rewrite the string, and fail open if the hook misbehaves.
            string original = __0;
            try
            {
                RuntimeTextExtractor.Observe(original, "ui.text");
                __0 = TranslationCatalog.TranslateText(original);
            }
            catch (Exception error)
            {
                __0 = original;
                if (!textSetterErrorLogged)
                {
                    textSetterErrorLogged = true;
                    ModLog.Warning("Hook de texto falhou; valor original preservado: " +
                        error.GetType().Name + ": " + error.Message);
                }
            }
        }

        private static void AfterGameToolLs(string __0, ref string __result)
        {
            RuntimeTextExtractor.Observe(__result, "GameTool.LS", __0);
            string value;
            __result = TranslationCatalog.TryKey(__0, out value)
                ? FormatText(value, 1)
                : TranslationCatalog.TranslateText(__result);
        }

        private static void AfterGameToolLsWithBackground(string __0, int __1, ref string __result)
        {
            RuntimeTextExtractor.Observe(__result, "GameTool.LS");
            string value;
            __result = TranslationCatalog.TryKey(__0, out value)
                ? FormatText(value, __1)
                : TranslationCatalog.TranslateText(__result);
        }

        private static void AfterLocalText(object __0, ref string __result)
        {
            try
            {
                string key = ReadKey(__0) as string;
                RuntimeTextExtractor.Observe(__result, "ConfLocalTextEx.text", key);
                string value;
                __result = TranslationCatalog.TryKey(key, out value)
                    ? FormatText(value, 1)
                    : TranslationCatalog.TranslateText(__result);
            }
            catch (Exception error)
            {
                ModLog.Warning("Falha ao buscar chave local: " + error.Message);
            }
        }
    }
}
