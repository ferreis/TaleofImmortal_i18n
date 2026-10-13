using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using Newtonsoft.Json.Linq;
using UnityEngine;

namespace TalesOfMortalI18N
{
    internal static class TranslationCatalog
    {
        private const string DefaultLanguage = "pt-BR";
        private const string FolderName = "TalesOfMortal_i18N";
        private static Dictionary<string, string> byText =
            new Dictionary<string, string>(StringComparer.Ordinal);
        private static Dictionary<string, string> byKey =
            new Dictionary<string, string>(StringComparer.Ordinal);
        private static HashSet<string> protectedNames =
            new HashSet<string>(StringComparer.Ordinal);

        internal static void Load()
        {
            // Prepara um novo snapshot antes de substituir as tabelas globais.
            var loadedText = new Dictionary<string, string>(StringComparer.Ordinal);
            var loadedKeys = new Dictionary<string, string>(StringComparer.Ordinal);
            var loadedNames = new HashSet<string>(StringComparer.Ordinal);
            string root = FindI18nFolder();

            if (root == null)
            {
                Debug.LogWarning("[Tales of Mortal i18N] Pasta i18n não encontrada. Nenhuma tradução será aplicada.");
                Clear();
                return;
            }

            string language = ReadLanguage(root);
            string languagePath = Path.Combine(root, language);
            if (!Directory.Exists(languagePath))
            {
                Debug.LogWarning("[Tales of Mortal i18N] Idioma não encontrado: " + languagePath);
                Clear();
                return;
            }

            string[] files = Directory.GetFiles(languagePath, "*.json", SearchOption.AllDirectories);
            Array.Sort(files, StringComparer.OrdinalIgnoreCase);
            int loadedFiles = 0;

            foreach (string file in files)
            {
                try
                {
                    var data = JObject.Parse(File.ReadAllText(file));
                    if (string.Equals(Path.GetFileName(file), "protected-names.json", StringComparison.OrdinalIgnoreCase))
                    {
                        LoadProtectedNames(data, loadedNames);
                    }
                    else
                    {
                        LoadTranslations(data, file, loadedText, loadedKeys);
                    }
                    loadedFiles++;
                }
                catch (Exception error)
                {
                    Debug.LogWarning("[Tales of Mortal i18N] Ignorando JSON inválido: " + file + " (" + error.Message + ")");
                }
            }

            byText = loadedText;
            byKey = loadedKeys;
            protectedNames = loadedNames;

            Debug.Log("[Tales of Mortal i18N] Idioma: " + language +
                "; arquivos: " + loadedFiles +
                "; textos: " + byText.Count +
                "; chaves: " + byKey.Count +
                "; nomes protegidos: " + protectedNames.Count + ".");
        }

        internal static void Clear()
        {
            byText = new Dictionary<string, string>(StringComparer.Ordinal);
            byKey = new Dictionary<string, string>(StringComparer.Ordinal);
            protectedNames = new HashSet<string>(StringComparer.Ordinal);
        }

        internal static bool TryKey(string key, out string translation)
        {
            translation = null;
            return !string.IsNullOrEmpty(key) &&
                !protectedNames.Contains(key) &&
                byKey.TryGetValue(key, out translation);
        }

        internal static string TranslateText(string original)
        {
            if (string.IsNullOrEmpty(original) || protectedNames.Contains(original))
                return original;

            string translation;
            return byText.TryGetValue(original, out translation) ? translation : original;
        }

        private static void LoadTranslations(
            JObject data,
            string file,
            Dictionary<string, string> texts,
            Dictionary<string, string> keys)
        {
            JToken translations = data["translations"];
            JToken keyed = data["keys"];

            if (translations != null || keyed != null)
            {
                if (translations != null && translations.Type != JTokenType.Object)
                    throw new FormatException("translations deve ser um objeto JSON.");
                if (keyed != null && keyed.Type != JTokenType.Object)
                    throw new FormatException("keys deve ser um objeto JSON.");

                if (translations != null)
                    LoadMap((JObject)translations, texts, file, "texto");
                if (keyed != null)
                    LoadMap((JObject)keyed, keys, file, "chave");
            }
            else
            {
                LoadMap(data, texts, file, "texto");
            }
        }

        private static void LoadMap(
            JObject map,
            Dictionary<string, string> destination,
            string file,
            string kind)
        {
            foreach (JProperty entry in map.Properties())
            {
                if (string.IsNullOrWhiteSpace(entry.Name) ||
                    entry.Value.Type != JTokenType.String)
                    continue;

                string translated = (string)entry.Value;
                if (string.IsNullOrEmpty(translated))
                    continue;

                string previous;
                if (destination.TryGetValue(entry.Name, out previous))
                {
                    if (!string.Equals(previous, translated, StringComparison.Ordinal))
                        Debug.LogWarning("[Tales of Mortal i18N] Conflito de " + kind +
                            " '" + entry.Name + "' em " + Path.GetFileName(file) +
                            ". Mantida primeira tradução.");
                    continue;
                }

                destination.Add(entry.Name, translated);
            }
        }

        private static void LoadProtectedNames(JObject data, HashSet<string> names)
        {
            var items = data["names"] as JArray;
            if (items == null)
                throw new FormatException("protected-names.json exige um array names.");

            foreach (JToken item in items)
            {
                if (item.Type != JTokenType.String)
                    continue;

                string name = (string)item;
                if (!string.IsNullOrWhiteSpace(name))
                    names.Add(name);
            }
        }

        private static string ReadLanguage(string root)
        {
            string config = Path.Combine(root, "config.json");
            if (!File.Exists(config))
                return DefaultLanguage;

            try
            {
                var json = JObject.Parse(File.ReadAllText(config));
                string language = (string)json["language"];
                // Não aceitar separadores ou segmentos de caminho vindos do JSON.
                if (!string.IsNullOrEmpty(language) &&
                    System.Text.RegularExpressions.Regex.IsMatch(
                        language, @"^[A-Za-z]{2,3}-[A-Za-z0-9]{2,12}$"))
                    return language;
            }
            catch (Exception error)
            {
                Debug.LogWarning("[Tales of Mortal i18N] config.json inválido: " + error.Message);
            }

            return DefaultLanguage;
        }

        private static string FindI18nFolder()
        {
            // O ModCode pode ser carregado de uma subpasta do mod.
            string location = Assembly.GetExecutingAssembly().Location;
            string current = string.IsNullOrEmpty(location) ? null : Path.GetDirectoryName(location);

            for (int level = 0; level < 6 && !string.IsNullOrEmpty(current); level++)
            {
                string candidate = Path.Combine(current, "i18n");
                if (Directory.Exists(candidate))
                    return candidate;

                DirectoryInfo parent = Directory.GetParent(current);
                current = parent == null ? null : parent.FullName;
            }

            // Alternativa quando o host carrega a DLL de um cache interno.
            string baseDir = AppDomain.CurrentDomain.BaseDirectory;
            string[] alternatives =
            {
                Path.Combine(baseDir, "Mods", FolderName, "i18n"),
                Path.Combine(baseDir, FolderName, "i18n")
            };
            foreach (string alternative in alternatives)
            {
                if (Directory.Exists(alternative))
                    return alternative;
            }

            return null;
        }
    }
}
