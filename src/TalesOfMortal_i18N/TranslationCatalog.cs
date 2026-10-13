using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Runtime.Serialization;
using System.Runtime.Serialization.Json;
using System.Text;
using System.Text.RegularExpressions;

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
        private static List<PatternRule> patternRules = new List<PatternRule>();

        [DataContract]
        private sealed class TranslationFile
        {
            [DataMember(Name = "translations", EmitDefaultValue = false)]
            public Dictionary<string, string> Translations { get; set; }

            [DataMember(Name = "keys", EmitDefaultValue = false)]
            public Dictionary<string, string> Keys { get; set; }

            [DataMember(Name = "patterns", EmitDefaultValue = false)]
            public List<PatternEntry> Patterns { get; set; }
        }

        [DataContract]
        private sealed class PatternEntry
        {
            [DataMember(Name = "pattern")]
            public string Pattern { get; set; }

            [DataMember(Name = "replacement")]
            public string Replacement { get; set; }
        }

        [DataContract]
        private sealed class NamesFile
        {
            [DataMember(Name = "names")]
            public List<string> Names { get; set; }
        }

        [DataContract]
        private sealed class ConfigFile
        {
            [DataMember(Name = "language")]
            public string Language { get; set; }
        }

        internal static int TextCount { get { return byText.Count; } }
        internal static int ProtectedNameCount { get { return protectedNames.Count; } }
        internal static int PatternCount { get { return patternRules.Count; } }
        internal static int LoadedFileCount { get; private set; }

        private sealed class PatternRule
        {
            internal Regex Regex;
            internal string Replacement;
            internal bool Disabled;
        }

        internal static void Load()
        {
            var texts = new Dictionary<string, string>(StringComparer.Ordinal);
            var keys = new Dictionary<string, string>(StringComparer.Ordinal);
            var names = new HashSet<string>(StringComparer.Ordinal);
            var patterns = new List<PatternRule>();

            string root = FindI18nFolder();
            if (root == null)
            {
                ModLog.Warning("Diretório i18n não encontrado.");
                Clear();
                return;
            }

            string lang = ReadLanguage(root);
            string folder = Path.Combine(root, lang);
            if (!Directory.Exists(folder))
            {
                ModLog.Warning("Idioma sem traduções: " + folder);
                Clear();
                return;
            }

            string[] files = Directory.GetFiles(folder, "*.json", SearchOption.AllDirectories);
            Array.Sort(files, delegate(string a, string b)
            {
                int pa = Priority(a), pb = Priority(b);
                return pa == pb ? StringComparer.OrdinalIgnoreCase.Compare(a, b) : pa.CompareTo(pb);
            });

            int loaded = 0;
            foreach (string file in files)
            {
                try
                {
                    string json = File.ReadAllText(file, Encoding.UTF8);
                    if (Path.GetFileName(file).Equals("protected-names.json", StringComparison.OrdinalIgnoreCase))
                    {
                        NamesFile list = Deserialize<NamesFile>(json);
                        if (list == null || list.Names == null)
                            throw new FormatException("O arquivo precisa de um array names.");
                        foreach (string name in list.Names)
                            if (!string.IsNullOrWhiteSpace(name))
                                names.Add(name);
                    }
                    else
                    {
                        TranslationFile pack = Deserialize<TranslationFile>(json);
                        if (pack == null)
                            throw new FormatException("Objeto JSON inválido.");

                        if (pack.Translations == null && pack.Keys == null && pack.Patterns == null)
                        {
                            // Compatibilidade com JSON simples: { "original": "tradução" }.
                            LoadMap(Deserialize<Dictionary<string, string>>(json), texts, file);
                        }
                        else
                        {
                            LoadMap(pack.Translations, texts, file);
                            LoadMap(pack.Keys, keys, file);
                            LoadPatterns(pack.Patterns, patterns, file);
                        }
                    }
                    loaded++;
                }
                catch (Exception error)
                {
                    ModLog.Warning("Ignorando " + Path.GetFileName(file) + ": " + error.Message);
                }
            }

            byText = texts;
            byKey = keys;
            protectedNames = names;
            patternRules = patterns;
            LoadedFileCount = loaded;

            ModLog.Info("Idioma: " + lang + "; arquivos: " + loaded +
                "; textos: " + texts.Count + "; chaves: " + keys.Count +
                "; nomes protegidos: " + names.Count + "; regex: " + patterns.Count + ".");
        }

        internal static void Clear()
        {
            byText = new Dictionary<string, string>(StringComparer.Ordinal);
            byKey = new Dictionary<string, string>(StringComparer.Ordinal);
            protectedNames = new HashSet<string>(StringComparer.Ordinal);
            patternRules = new List<PatternRule>();
            LoadedFileCount = 0;
        }

        internal static bool TryKey(string key, out string value)
        {
            value = null;
            return !string.IsNullOrEmpty(key) &&
                !protectedNames.Contains(key) && byKey.TryGetValue(key, out value);
        }

        internal static string TranslateText(string original)
        {
            if (string.IsNullOrEmpty(original) || protectedNames.Contains(original))
                return original;

            string result;
            if (byText.TryGetValue(original, out result))
                return result;

            foreach (PatternRule rule in patternRules)
            {
                if (rule.Disabled)
                    continue;

                try
                {
                    if (rule.Regex.IsMatch(original))
                        return rule.Regex.Replace(original, rule.Replacement, 1);
                }
                catch (RegexMatchTimeoutException)
                {
                    rule.Disabled = true;
                    ModLog.Warning("Regex desativada por timeout: " + rule.Regex);
                }
            }
            return original;
        }

        private static T Deserialize<T>(string json)
        {
            var options = new DataContractJsonSerializerSettings
            {
                UseSimpleDictionaryFormat = true,
                MaxItemsInObjectGraph = int.MaxValue
            };
            var serializer = new DataContractJsonSerializer(typeof(T), options);
            using (var stream = new MemoryStream(Encoding.UTF8.GetBytes(json)))
                return (T)serializer.ReadObject(stream);
        }

        private static void LoadMap(Dictionary<string, string> source, Dictionary<string, string> target, string file)
        {
            if (source == null)
                return;

            foreach (KeyValuePair<string, string> item in source)
            {
                if (string.IsNullOrWhiteSpace(item.Key) || string.IsNullOrEmpty(item.Value))
                    continue;

                string existing;
                if (target.TryGetValue(item.Key, out existing))
                {
                    if (existing != item.Value)
                        ModLog.Warning("Tradução conflitante em " + Path.GetFileName(file) +
                            ": " + item.Key + " (mantida a primeira).");
                }
                else
                {
                    target.Add(item.Key, item.Value);
                }
            }
        }

        private static void LoadPatterns(List<PatternEntry> entries, List<PatternRule> destination, string file)
        {
            if (entries == null)
                return;

            foreach (PatternEntry entry in entries)
            {
                if (entry == null || string.IsNullOrWhiteSpace(entry.Pattern) || entry.Replacement == null)
                    continue;
                try
                {
                    destination.Add(new PatternRule
                    {
                        Regex = new Regex(entry.Pattern, RegexOptions.CultureInvariant,
                            TimeSpan.FromMilliseconds(100)),
                        Replacement = entry.Replacement
                    });
                }
                catch (ArgumentException error)
                {
                    ModLog.Warning("Regex inválida em " + Path.GetFileName(file) + ": " + error.Message);
                }
            }
        }

        private static int Priority(string file)
        {
            string name = Path.GetFileName(file);
            if (name.Equals("game.json", StringComparison.OrdinalIgnoreCase)) return 0;
            if (name.Equals("zzz-auto.json", StringComparison.OrdinalIgnoreCase)) return 2;
            return 1;
        }

        private static string ReadLanguage(string root)
        {
            string configPath = Path.Combine(root, "config.json");
            if (!File.Exists(configPath)) return DefaultLanguage;

            try
            {
                ConfigFile config = Deserialize<ConfigFile>(File.ReadAllText(configPath));
                string language = config == null ? null : config.Language;
                if (!string.IsNullOrEmpty(language) &&
                    Regex.IsMatch(language, @"^[A-Za-z]{2,3}-[A-Za-z0-9]{2,12}$"))
                    return language;
            }
            catch (Exception error)
            {
                ModLog.Warning("Configuração de idioma inválida: " + error.Message);
            }
            return DefaultLanguage;
        }

        private static string FindI18nFolder()
        {
            // Normal case: the DLL is kept in ModCode/dll or its build directory.
            string location = null;
            try { location = typeof(ModMain).Assembly.Location; }
            catch (Exception error) { ModLog.Warning("Localização da DLL indisponível: " + error.Message); }

            string current = string.IsNullOrEmpty(location) ? null : Path.GetDirectoryName(location);
            for (int n = 0; n < 8 && !string.IsNullOrEmpty(current); n++)
            {
                string modAssets = Path.Combine(current, "ModAssets", "i18n");
                if (Directory.Exists(modAssets)) return modAssets;

                string candidate = Path.Combine(current, "i18n");
                if (Directory.Exists(candidate)) return candidate;
                DirectoryInfo parent = Directory.GetParent(current);
                current = parent == null ? null : parent.FullName;
            }

            // Some loaders copy assemblies to a managed cache. Search only
            // actual MOD_DQKLF9 installations, never random mod translations.
            string gameRoot = AppDomain.CurrentDomain.BaseDirectory;
            string[] installationRoots =
            {
                Path.Combine(gameRoot, "ModExportData"),
                Path.Combine(gameRoot, "Mods")
            };

            foreach (string installationRoot in installationRoots)
            {
                if (!Directory.Exists(installationRoot)) continue;

                try
                {
                    foreach (string modFolder in Directory.GetDirectories(installationRoot))
                    {
                        string result = FindInstalledPackage(modFolder);
                        if (result != null) return result;

                        // Mod Creator and Workshop open-source projects can
                        // have the playable files inside debug/Mod_DQKLF9.
                        result = FindInstalledPackage(Path.Combine(modFolder, "debug", "Mod_DQKLF9"));
                        if (result != null) return result;
                    }
                }
                catch (IOException error)
                {
                    ModLog.Warning("Erro ao localizar o mod em " + installationRoot + ": " + error.Message);
                }
                catch (UnauthorizedAccessException error)
                {
                    ModLog.Warning("Sem acesso a " + installationRoot + ": " + error.Message);
                }
            }

            string standalone = Path.Combine(gameRoot, FolderName, "i18n");
            return Directory.Exists(standalone) ? standalone : null;
        }

        private static string FindInstalledPackage(string modFolder)
        {
            if (!Directory.Exists(modFolder)) return null;

            string translations = Path.Combine(modFolder, "ModAssets", "i18n");
            if (!Directory.Exists(translations))
                translations = Path.Combine(modFolder, "i18n");
            if (!Directory.Exists(translations)) return null;

            string[] dllCandidates =
            {
                Path.Combine(modFolder, "ModCode", "dll", "MOD_DQKLF9.dll"),
                Path.Combine(modFolder, "ModCode", "MOD_DQKLF9.dll")
            };

            foreach (string dll in dllCandidates)
                if (File.Exists(dll)) return translations;

            return null;
        }

    }
}
