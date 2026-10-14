using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Text;

namespace TalesOfMortalI18N
{
    // Ajuste de fonte com reflexão: compila sem DLLs do Unity.
    // Respeita os controles InputField/TMP_InputField e não altera texto.
    internal static class AdaptiveText
    {
        private const BindingFlags Properties = BindingFlags.Public | BindingFlags.Instance;
        private static ConditionalWeakTable<object, State> adjusted =
            new ConditionalWeakTable<object, State>();
        private static readonly object Gate = new object();
        private static readonly HashSet<string> failed = new HashSet<string>();

        internal static bool Enabled { get; private set; }
        internal static bool OnlyTranslated { get; private set; }
        internal static int MinimumCharacters { get; private set; }
        internal static int MinimumFontSize { get; private set; }
        internal static double MinimumScale { get; private set; }

        private sealed class State
        {
            internal bool HasApplied;
        }

        internal static void Initialize()
        {
            Clear();
            Enabled = true;
            OnlyTranslated = true;
            MinimumCharacters = 24;
            MinimumFontSize = 12;
            MinimumScale = 0.65;
            try
            {
                string folder = TranslationCatalog.I18nDirectory;
                string path = string.IsNullOrEmpty(folder) ? null :
                    Path.Combine(folder, "config.json");
                if (path != null && File.Exists(path))
                {
                    var root = JsonTextParser.ParseObject(File.ReadAllText(path, Encoding.UTF8));
                    object settings;
                    var options = root.TryGetValue("adaptiveText", out settings) ?
                        settings as Dictionary<string, object> : null;
                    if (options != null)
                    {
                        Enabled = ReadBoolean(options, "enabled", Enabled);
                        OnlyTranslated = ReadBoolean(options, "onlyTranslated", OnlyTranslated);
                        MinimumCharacters = (int)Math.Max(10, Math.Min(200,
                            ReadNumber(options, "minCharacters", MinimumCharacters)));
                        MinimumFontSize = (int)Math.Max(8, Math.Min(36,
                            ReadNumber(options, "minFontSize", MinimumFontSize)));
                        MinimumScale = Math.Max(0.4, Math.Min(0.95,
                            ReadNumber(options, "minScale", MinimumScale)));
                    }
                }
                ModLog.Info("Fonte adaptativa " + (Enabled ? "ativada" : "desativada") +
                    "; mínimo " + MinimumFontSize + "px, escala " + MinimumScale +
                    ", caracteres " + MinimumCharacters + ".");
            }
            catch (Exception error)
            {
                Enabled = false;
                ModLog.Warning("Fonte adaptativa desativada: " + error.Message);
            }
        }

        internal static void Clear()
        {
            adjusted = new ConditionalWeakTable<object, State>();
            lock (Gate) failed.Clear();
            Enabled = false;
        }

        internal static void TryFit(object textComponent, string original, string result)
        {
            if (!Enabled || textComponent == null || string.IsNullOrEmpty(result) ||
                result.Length < MinimumCharacters ||
                (OnlyTranslated && string.Equals(original, result, StringComparison.Ordinal)))
                return;

            Type type = textComponent.GetType();
            bool legacy = IsTypeOrAncestor(type, "UnityEngine.UI.Text");
            bool tmp = IsTypeOrAncestor(type, "TMPro.TextMeshProUGUI");
            if (!legacy && !tmp) return;

            State state = adjusted.GetValue(textComponent, key => new State());
            if (state.HasApplied) return;

            try
            {
                // Editáveis têm seleção e cursor: não alterar suas dimensões de texto.
                string inputType = legacy ? "UnityEngine.UI.InputField" : "TMPro.TMP_InputField";
                Type input = FindType(inputType);
                if (input != null)
                {
                    MethodInfo parent = type.GetMethod("GetComponentInParent", Properties,
                        null, new Type[] { typeof(Type) }, null);
                    if (parent != null && parent.Invoke(textComponent, new object[] { input }) != null)
                        return;
                }

                PropertyInfo font = type.GetProperty("fontSize", Properties);
                PropertyInfo toggle = type.GetProperty(
                    legacy ? "resizeTextForBestFit" : "enableAutoSizing", Properties);
                PropertyInfo min = type.GetProperty(
                    legacy ? "resizeTextMinSize" : "fontSizeMin", Properties);
                PropertyInfo max = type.GetProperty(
                    legacy ? "resizeTextMaxSize" : "fontSizeMax", Properties);
                if (font == null || toggle == null || min == null || max == null ||
                    !toggle.CanWrite || !min.CanWrite || !max.CanWrite)
                    return;
                if (Convert.ToBoolean(toggle.GetValue(textComponent, null)))
                {
                    state.HasApplied = true; // Respeitar configuração original da UI.
                    return;
                }

                double size = Convert.ToDouble(font.GetValue(textComponent, null));
                if (size <= 0) return;
                double smallest = Math.Max(MinimumFontSize, size * MinimumScale);
                if (smallest >= size) return;

                // As propriedades são int em Unity UI.Text e float em TextMeshPro.
                if (legacy)
                {
                    max.SetValue(textComponent, (int)Math.Ceiling(size), null);
                    min.SetValue(textComponent, (int)Math.Ceiling(smallest), null);
                }
                else
                {
                    max.SetValue(textComponent, Convert.ToSingle(size), null);
                    min.SetValue(textComponent, Convert.ToSingle(smallest), null);
                }
                toggle.SetValue(textComponent, true, null);
                state.HasApplied = true;
            }
            catch (Exception error)
            {
                // Não interromper a UI do jogo caso um mod tenha um componente
                // de texto incompatível com estas propriedades.
                lock (Gate)
                {
                    string key = type.FullName ?? type.Name;
                    if (failed.Add(key))
                        ModLog.Warning("Fonte adaptativa indisponível em " + key +
                            ": " + error.Message);
                }
            }
        }

        private static bool IsTypeOrAncestor(Type type, string fullName)
        {
            while (type != null)
            {
                if (type.FullName == fullName) return true;
                type = type.BaseType;
            }
            return false;
        }

        private static Type FindType(string fullName)
        {
            foreach (Assembly assembly in AppDomain.CurrentDomain.GetAssemblies())
            {
                Type match = assembly.GetType(fullName, false);
                if (match != null) return match;
            }
            return null;
        }

        private static bool ReadBoolean(Dictionary<string, object> obj, string key, bool fallback)
        {
            object value;
            return obj.TryGetValue(key, out value) && value is bool ? (bool)value : fallback;
        }

        private static double ReadNumber(Dictionary<string, object> obj, string key, double fallback)
        {
            object value;
            return obj.TryGetValue(key, out value) && value is double ? (double)value : fallback;
        }
    }
}
