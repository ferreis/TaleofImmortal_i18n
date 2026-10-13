using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Threading;

namespace TalesOfMortalI18N
{
    // Registra textos observados em hooks do jogo. Não traduz, nem modifica os JSON de tradução.
    // Nenhuma referência ao jogo, Unity ou Harmony é necessária durante a compilação.
    internal static class RuntimeTextExtractor
    {
        private sealed class Entry
        {
            internal string Text;
            internal string Language;
            internal int Observations;
            internal readonly HashSet<string> Sources =
                new HashSet<string>(StringComparer.Ordinal);
            internal readonly HashSet<string> Keys =
                new HashSet<string>(StringComparer.Ordinal);
        }

        private static readonly object Gate = new object();
        private static readonly Dictionary<string, Entry> Entries =
            new Dictionary<string, Entry>(StringComparer.Ordinal);
        private static string outputPath;
        private static bool enabled;
        private static bool includeEnglish;
        private static bool includeChinese;
        private static int maxEntries;
        private static int revision;
        private static bool dirty;
        private static Timer timer;

        internal static bool Enabled { get { return enabled; } }

        internal static void Start()
        {
            Stop();
            try
            {
                string gameRoot = AppDomain.CurrentDomain.BaseDirectory;
                string config = Path.Combine(
                    gameRoot, "ModExportData", "Mod_DQKLF9", "ModAssets", "i18n", "config.json");
                if (!File.Exists(config))
                {
                    string known = TranslationCatalog.I18nDirectory;
                    if (!string.IsNullOrEmpty(known))
                        config = Path.Combine(known, "config.json");
                }

                if (!File.Exists(config))
                {
                    ModLog.Warning("Extrator: config.json não encontrado, captura desativada.");
                    return;
                }

                var root = JsonTextParser.ParseObject(File.ReadAllText(config, Encoding.UTF8));
                object settings;
                var extractor = root.TryGetValue("extractor", out settings) ?
                    settings as Dictionary<string, object> : null;

                if (extractor == null || !Flag(extractor, "enabled", false))
                {
                    ModLog.Info("Extrator de textos desativado no config.json.");
                    return;
                }

                includeEnglish = Flag(extractor, "includeEnglish", true);
                includeChinese = Flag(extractor, "includeChinese", true);
                maxEntries = Bound(Int(extractor, "maxEntries", 50000), 100, 200000);
                int seconds = Bound(Int(extractor, "flushSeconds", 30), 10, 300);

                // Diretório FORA de i18n/pt-BR: nunca será interpretado como tradução.
                outputPath = Path.Combine(gameRoot, "TalesOfMortal_i18N_Extracted", "runtime.json");
                Directory.CreateDirectory(Path.GetDirectoryName(outputPath));

                lock (Gate)
                {
                    Entries.Clear();
                    LoadExisting();
                    dirty = false;
                    revision = 0;
                    enabled = true;
                    timer = new Timer(FlushTimer, null, seconds * 1000, seconds * 1000);
                }
                ModLog.Info("Extrator ligado; itens anteriores: " + Entries.Count +
                    "; saída: " + outputPath);
            }
            catch (Exception error)
            {
                enabled = false;
                ModLog.Warning("Extrator desativado por erro: " + error);
            }
        }

        internal static void Stop()
        {
            Timer old;
            lock (Gate)
            {
                enabled = false;
                old = timer;
                timer = null;
            }
            if (old != null) old.Dispose();
            Flush(true);
        }

        internal static void Observe(string text, string source, string localizationKey = null)
        {
            if (!enabled || string.IsNullOrWhiteSpace(text) ||
                text.Length > 8000 || text.Length < 2 ||
                TranslationCatalog.IsProtectedName(text) ||
                TranslationCatalog.IsKnownTranslation(text))
                return;

            string language = IdentifyLanguage(text);
            if (language == null) return;
            if (language == "en-candidate" && !includeEnglish) return;
            if (language != "en-candidate" && !includeChinese) return;

            lock (Gate)
            {
                if (!enabled) return;
                Entry entry;
                if (Entries.TryGetValue(text, out entry))
                {
                    // Limita writes e operações quando a mesma tela atualiza por frame.
                    if (entry.Observations < 999999) entry.Observations++;
                    entry.Sources.Add(source);
                    if (!string.IsNullOrEmpty(localizationKey)) entry.Keys.Add(localizationKey);
                    dirty = true;
                    revision++;
                }
                else if (Entries.Count < maxEntries)
                {
                    entry = new Entry
                    {
                        Text = text,
                        Language = language,
                        Observations = 1
                    };
                    entry.Sources.Add(source);
                    if (!string.IsNullOrEmpty(localizationKey)) entry.Keys.Add(localizationKey);
                    Entries.Add(text, entry);
                    dirty = true;
                    revision++;
                }
            }
        }

        private static void FlushTimer(object unused)
        {
            Flush(false);
        }

        internal static void Flush(bool force)
        {
            if (string.IsNullOrEmpty(outputPath)) return;
            try
            {
                string json;
                int snapshotRevision;
                lock (Gate)
                {
                    if (!dirty) return;
                    json = Serialize();
                    snapshotRevision = revision;
                }

                string temp = outputPath + ".tmp";
                File.WriteAllText(temp, json, new UTF8Encoding(false));
                if (!File.Exists(outputPath))
                    File.Move(temp, outputPath);
                else
                {
                    try { File.Replace(temp, outputPath, null); }
                    catch (PlatformNotSupportedException) { File.Copy(temp, outputPath, true); File.Delete(temp); }
                    catch (IOException) { File.Copy(temp, outputPath, true); File.Delete(temp); }
                }
                lock (Gate)
                {
                    // Snapshot pode ficar defasado se uma UI mudou durante a gravação.
                    // Nesse caso a próxima execução de Flush escreverá o conjunto novo.
                    if (revision == snapshotRevision)
                        dirty = false;
                }
            }
            catch (Exception error)
            {
                // Não pode quebrar o jogo por uma falha de escrita em disco.
                ModLog.Warning("Falha ao salvar extração: " + error.Message);
            }
        }

        private static void LoadExisting()
        {
            if (!File.Exists(outputPath)) return;
            try
            {
                var data = JsonTextParser.ParseObject(File.ReadAllText(outputPath, Encoding.UTF8));
                object rows;
                if (!data.TryGetValue("entries", out rows)) return;
                var list = rows as List<object>;
                if (list == null) return;
                foreach (object value in list)
                {
                    if (Entries.Count >= maxEntries) break;
                    var raw = value as Dictionary<string, object>;
                    if (raw == null) continue;
                    object textValue, langValue, countValue, sourcesValue, keysValue;
                    string text = raw.TryGetValue("text", out textValue) ? textValue as string : null;
                    if (string.IsNullOrEmpty(text) || Entries.ContainsKey(text)) continue;
                    var e = new Entry
                    {
                        Text = text,
                        Language = raw.TryGetValue("language", out langValue) ?
                            langValue as string : null,
                        Observations = raw.TryGetValue("observations", out countValue) &&
                            countValue is double ? Bound((int)(double)countValue, 1, 999999) : 1
                    };
                    if (raw.TryGetValue("sources", out sourcesValue))
                    {
                        var arr = sourcesValue as List<object>;
                        if (arr != null)
                            foreach (object item in arr)
                                if (item is string) e.Sources.Add((string)item);
                    }
                    if (raw.TryGetValue("localizationKeys", out keysValue))
                    {
                        var arr = keysValue as List<object>;
                        if (arr != null)
                            foreach (object item in arr)
                                if (item is string) e.Keys.Add((string)item);
                    }
                    Entries.Add(text, e);
                }
            }
            catch (Exception error)
            {
                // Não sobrescrever arquivo parcialmente ilegível sem preservá-lo.
                File.Copy(outputPath, outputPath + ".invalid." +
                    DateTime.Now.ToString("yyyyMMddHHmmss") + ".bak", true);
                ModLog.Warning("Extração anterior inválida. Backup criado: " + error.Message);
            }
        }

        private static string Serialize()
        {
            var builder = new StringBuilder(Math.Min(Entries.Count * 140, 2000000));
            builder.Append("{\n  \"format\": \"talesofmortal-extraction-v1\",\n");
            builder.Append("  \"origin\": \"runtime-unattributed-game-or-mod\",\n");
            builder.Append("  \"note\": \"Languages are heuristic; mod provenance is not known at this hook.\",\n");
            builder.Append("  \"entries\": [\n");
            bool first = true;
            foreach (Entry entry in Entries.Values)
            {
                if (!first) builder.Append(",\n");
                first = false;
                builder.Append("    {\"text\": ");
                AppendJson(builder, entry.Text);
                builder.Append(", \"language\": ");
                AppendJson(builder, entry.Language ?? "und");
                builder.Append(", \"observations\": ").Append(entry.Observations);
                builder.Append(", \"sources\": [");
                bool sourceFirst = true;
                foreach (string source in entry.Sources)
                {
                    if (!sourceFirst) builder.Append(", ");
                    sourceFirst = false;
                    AppendJson(builder, source);
                }
                builder.Append("], \"localizationKeys\": [");
                bool keyFirst = true;
                foreach (string key in entry.Keys)
                {
                    if (!keyFirst) builder.Append(", ");
                    keyFirst = false;
                    AppendJson(builder, key);
                }
                builder.Append("]}");
            }
            builder.Append("\n  ]\n}\n");
            return builder.ToString();
        }

        internal static void AppendJson(StringBuilder output, string text)
        {
            output.Append('"');
            foreach (char c in text)
            {
                switch (c)
                {
                    case '\\': output.Append("\\\\"); break;
                    case '"': output.Append("\\\""); break;
                    case '\n': output.Append("\\n"); break;
                    case '\r': output.Append("\\r"); break;
                    case '\t': output.Append("\\t"); break;
                    default:
                        if (c < 32) output.Append("\\u").Append(((int)c).ToString("x4"));
                        else output.Append(c);
                        break;
                }
            }
            output.Append('"');
        }

        // A escrita chinesa pode ser ambígua. Letras presentes em ambos sistemas
        // retornam zh-und, nunca uma afirmação incorreta de simplificado/tradicional.
        internal static string IdentifyLanguage(string text)
        {
            bool hasHan = false, simplified = false, traditional = false, latin = false;
            const string simple = "龙门剑学气灵体发岁无万国经师后阳风广画云东叶书鸟马鱼";
            const string trad = "龍門劍學氣靈體發歲無萬國經師後陽風廣畫雲東葉書鳥馬魚";
            foreach (char c in text)
            {
                if ((c >= '\u3400' && c <= '\u9fff') ||
                    (c >= '\uf900' && c <= '\ufaff'))
                {
                    hasHan = true;
                    if (simple.IndexOf(c) >= 0) simplified = true;
                    if (trad.IndexOf(c) >= 0) traditional = true;
                }
                if (c >= 'A' && c <= 'Z' || c >= 'a' && c <= 'z') latin = true;
            }
            if (hasHan)
                return simplified && traditional ? "zh-mixed" :
                    simplified ? "zh-Hans" : traditional ? "zh-Hant" : "zh-und";
            // Latin scripts are merely candidates: can be English, pinyin or PT-BR.
            if (latin && ContainsLetters(text, 3))
                return "en-candidate";
            return null;
        }

        private static bool ContainsLetters(string text, int minimum)
        {
            int count = 0;
            foreach (char c in text)
            {
                if (c >= 'A' && c <= 'Z' || c >= 'a' && c <= 'z')
                    if (++count >= minimum) return true;
            }
            return false;
        }

        private static bool Flag(Dictionary<string, object> values, string key, bool fallback)
        {
            object value;
            return values.TryGetValue(key, out value) && value is bool ? (bool)value : fallback;
        }

        private static int Int(Dictionary<string, object> values, string key, int fallback)
        {
            object value;
            if (!values.TryGetValue(key, out value) || !(value is double)) return fallback;
            return (int)(double)value;
        }

        private static int Bound(int value, int minimum, int maximum)
        {
            return Math.Max(minimum, Math.Min(maximum, value));
        }
    }
}
