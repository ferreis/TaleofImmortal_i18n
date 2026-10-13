using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
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
        // Separa SOMENTE limites de linha e tags de formatação (capturadas).
        // Sem tradução por substring: nomes de NPCs e parâmetros são preservados.
        private static readonly Regex FragmentBoundaries = new Regex(
            @"(\r\n|\r|\n|<[^>]*>)", RegexOptions.CultureInvariant,
            TimeSpan.FromMilliseconds(75));
        private static readonly Regex EnglishSkillName = new Regex(
            @"^[A-Z][A-Za-z-]+(?:'s|’s) [A-Z][\w'-]+(?: [A-Z][\w'-]+){0,4} (?:Firebolt|Groundfire|Thundercall|Palm|Sword|Spear|Fist|Technique|Técnica|Blade|Manual|Celerity Palm)(?: -\d+)?$",
            RegexOptions.CultureInvariant, TimeSpan.FromMilliseconds(75));
        private static readonly HashSet<string> EnglishRegions =
            new HashSet<string>(StringComparer.Ordinal)
            { "Yong Ning", "Hua Feng", "Mu Xian", "Yun Mo", "Chi You" };


        internal static int TextCount { get { return byText.Count; } }
        internal static int ProtectedNameCount { get { return protectedNames.Count; } }
        internal static int PatternCount { get { return patternRules.Count; } }
        internal static int LoadedFileCount { get; private set; }

        internal static string I18nDirectory { get; private set; }
        private static HashSet<string> translatedValues =
            new HashSet<string>(StringComparer.Ordinal);
        internal static bool IsProtectedName(string text)
        {
            return !string.IsNullOrEmpty(text) && protectedNames.Contains(text);
        }
        internal static bool IsKnownTranslation(string text)
        {
            return !string.IsNullOrEmpty(text) && translatedValues.Contains(text);
        }

        private sealed class CatalogFile
        {
            internal string Path;
            internal Dictionary<string, object> Document;
            internal string Kind;
            internal string Id;
        }

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
            I18nDirectory = root;
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

            ModLog.Info("Lendo traduções de: " + folder);
            // Each JSON identifies itself. File names are not used for classification,
            // including protected names, game catalogs and fallback dictionaries.
            string[] paths = Directory.GetFiles(folder, "*.json", SearchOption.AllDirectories);
            var documents = new List<CatalogFile>();
            var ids = new HashSet<string>(StringComparer.Ordinal);

            foreach (string file in paths)
            {
                try
                {
                    Dictionary<string, object> document =
                        JsonTextParser.ParseObject(File.ReadAllText(file, Encoding.UTF8));
                    string kind, identifier;
                    IdentifyModule(document, file, out kind, out identifier);
                    if (!ids.Add(identifier))
                        ModLog.Warning("O identificador de módulo '" + identifier +
                            "' foi encontrado mais de uma vez. Verifique os arquivos.");
                    documents.Add(new CatalogFile
                    {
                        Path = file,
                        Document = document,
                        Kind = kind,
                        Id = identifier
                    });
                }
                catch (Exception error)
                {
                    ModLog.Warning("Ignorando " + Path.GetFileName(file) + ": " + error);
                }
            }

            documents.Sort(delegate(CatalogFile a, CatalogFile b)
            {
                int order = KindPriority(a.Kind).CompareTo(KindPriority(b.Kind));
                if (order != 0) return order;
                order = StringComparer.Ordinal.Compare(a.Id, b.Id);
                return order == 0 ? StringComparer.Ordinal.Compare(a.Path, b.Path) : order;
            });

            int loaded = 0;
            foreach (CatalogFile file in documents)
            {
                try
                {
                    Dictionary<string, object> document = file.Document;
                    if (file.Kind == "names")
                    {
                        List<object> entries = ReadArray(document, "names", true);
                        foreach (object entry in entries)
                        {
                            string name = entry as string;
                            if (!string.IsNullOrWhiteSpace(name)) names.Add(name);
                        }
                    }
                    else if (document.ContainsKey("translations") ||
                             document.ContainsKey("keys") ||
                             document.ContainsKey("patterns"))
                    {
                        LoadMap(ReadStringMap(document, "translations", false), texts, file.Path);
                        LoadMap(ReadStringMap(document, "keys", false), keys, file.Path);
                        LoadPatterns(ReadArray(document, "patterns", false), patterns, file.Path);
                    }
                    else
                    {
                        // Legacy plain-map JSON files are still supported.
                        if (document.ContainsKey("module"))
                            throw new FormatException(
                                "Pacote com module exige translations, keys ou patterns.");
                        LoadMap(ConvertMap(document), texts, file.Path);
                    }
                    loaded++;
                }
                catch (Exception error)
                {
                    ModLog.Warning("Ignorando " + Path.GetFileName(file.Path) + ": " + error);
                }
            }

            byText = texts;
            translatedValues = new HashSet<string>(texts.Values, StringComparer.Ordinal);
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
            translatedValues = new HashSet<string>(StringComparer.Ordinal);
            I18nDirectory = null;
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

            // Atributos de região e títulos completos de skills que já estão
            // em inglês não devem passar por traduções comunitárias imprecisas.
            if (EnglishRegions.Contains(original) || IsEnglishSkillName(original))
                return original;

            string result;
            if (byText.TryGetValue(original, out result))
                return result;

            // Se não houver correspondência para o bloco todo, traduzir apenas
            // linhas/trechos completos entre tags; nunca fazer Replace global.
            result = TranslateSeparatedSegments(original);
            if (result != null)
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

        private static bool IsEnglishSkillName(string text)
        {
            if (text.Length > 180) return false;
            try { return EnglishSkillName.IsMatch(text); }
            catch (RegexMatchTimeoutException) { return false; }
        }

        private static string TranslateSeparatedSegments(string source)
        {
            if (source.Length > 16000 ||
                (source.IndexOf('<') < 0 && source.IndexOf('\n') < 0 &&
                 source.IndexOf('\r') < 0))
                return null;

            try
            {
                string[] parts = FragmentBoundaries.Split(source);
                if (parts.Length == 1) return null;
                int updated = 0;
                for (int i = 0; i < parts.Length; i++)
                {
                    string value = parts[i];
                    if (string.IsNullOrWhiteSpace(value) || value[0] == '<' ||
                        value == "\n" || value == "\r" || value == "\r\n" ||
                        protectedNames.Contains(value) || EnglishRegions.Contains(value) ||
                        IsEnglishSkillName(value))
                        continue;
                    string translated;
                    if (byText.TryGetValue(value, out translated) &&
                        !string.IsNullOrEmpty(translated) &&
                        translated != value)
                    {
                        parts[i] = translated;
                        updated++;
                    }
                }
                return updated > 0 ? string.Concat(parts) : null;
            }
            catch (RegexMatchTimeoutException)
            {
                return null;
            }
        }

        private static Dictionary<string, string> ConvertMap(Dictionary<string, object> objectMap)
        {
            var result = new Dictionary<string, string>(StringComparer.Ordinal);
            foreach (KeyValuePair<string, object> entry in objectMap)
            {
                string text = entry.Value as string;
                if (text != null)
                    result.Add(entry.Key, text);
            }
            return result;
        }

        private static Dictionary<string, string> ReadStringMap(
            Dictionary<string, object> container, string property, bool required)
        {
            object value;
            if (!container.TryGetValue(property, out value))
            {
                if (required) throw new FormatException("Falta campo " + property + ".");
                return null;
            }

            var map = value as Dictionary<string, object>;
            if (map == null)
                throw new FormatException("O campo " + property + " deve ser objeto JSON.");
            return ConvertMap(map);
        }

        private static List<object> ReadArray(
            Dictionary<string, object> container, string property, bool required)
        {
            object value;
            if (!container.TryGetValue(property, out value))
            {
                if (required) throw new FormatException("Falta campo " + property + ".");
                return null;
            }
            var array = value as List<object>;
            if (array == null)
                throw new FormatException("O campo " + property + " deve ser array JSON.");
            return array;
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

        private static void LoadPatterns(List<object> entries, List<PatternRule> destination, string file)
        {
            if (entries == null) return;

            foreach (object item in entries)
            {
                var entry = item as Dictionary<string, object>;
                if (entry == null) continue;

                object patternToken, replacementToken;
                if (!entry.TryGetValue("pattern", out patternToken) ||
                    !entry.TryGetValue("replacement", out replacementToken))
                    continue;

                string pattern = patternToken as string;
                string replacement = replacementToken as string;
                if (string.IsNullOrWhiteSpace(pattern) || replacement == null) continue;

                try
                {
                    destination.Add(new PatternRule
                    {
                        Regex = new Regex(pattern, RegexOptions.CultureInvariant,
                            TimeSpan.FromMilliseconds(100)),
                        Replacement = replacement
                    });
                }
                catch (ArgumentException error)
                {
                    ModLog.Warning("Regex inválida em " + Path.GetFileName(file) + ": " + error);
                }
            }
        }

        private static int KindPriority(string kind)
        {
            switch (kind)
            {
                case "names": return -1;
                case "game": return 0;
                case "mod": return 1;
                case "fallback": return 2;
                default: return 1;
            }
        }

        private static void IdentifyModule(
            Dictionary<string, object> document, string file,
            out string kind, out string identifier)
        {
            object moduleToken;
            if (!document.TryGetValue("module", out moduleToken))
            {
                // Compatibility with old v1 catalogs that lack metadata.
                string name = Path.GetFileName(file);
                kind = name.Equals("protected-names.json", StringComparison.OrdinalIgnoreCase)
                    ? "names"
                    : name.Equals("game.json", StringComparison.OrdinalIgnoreCase)
                        ? "game"
                        : name.Equals("zzz-auto.json", StringComparison.OrdinalIgnoreCase)
                            ? "fallback" : "mod";
                identifier = "legacy:" + name;
                return;
            }

            var module = moduleToken as Dictionary<string, object>;
            if (module == null)
                throw new FormatException("module deve ser um objeto JSON.");

            object kindValue, idValue;
            kind = module.TryGetValue("kind", out kindValue) ? kindValue as string : null;
            identifier = module.TryGetValue("id", out idValue) ? idValue as string : null;

            if (kind != "game" && kind != "mod" && kind != "fallback" && kind != "names")
                throw new FormatException("module.kind deve ser game, mod, fallback ou names.");
            if (string.IsNullOrWhiteSpace(identifier))
                throw new FormatException("module.id deve conter um identificador estável.");
            if (kind == "mod" && !module.ContainsKey("name"))
                ModLog.Warning("Módulo '" + identifier + "' não contém module.name.");
        }

        private static string ReadLanguage(string root)
        {
            string configPath = Path.Combine(root, "config.json");
            if (!File.Exists(configPath)) return DefaultLanguage;

            try
            {
                var config = JsonTextParser.ParseObject(File.ReadAllText(configPath, Encoding.UTF8));
                object token;
                string language = config.TryGetValue("language", out token) ? token as string : null;
                if (!string.IsNullOrEmpty(language) &&
                    Regex.IsMatch(language, @"^[A-Za-z]{2,3}-[A-Za-z0-9]{2,12}$"))
                    return language;
            }
            catch (Exception error)
            {
                ModLog.Warning("Configuração de idioma inválida: " + error.ToString());
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
