using System;
using System.IO;
using System.Collections.Generic;
using TalesOfMortalI18N;

internal static class ExtractorSmoke
{
    internal static void Run()
    {
        RuntimeTextExtractor.Start();
        if (!RuntimeTextExtractor.Enabled)
            throw new Exception("Extrator não ativou pelo config.json.");

        RuntimeTextExtractor.Observe("龙门客栈", "test.ui");
        RuntimeTextExtractor.Observe("English quest objective", "test.ui");
        RuntimeTextExtractor.Observe("龙门客栈", "test.ui");
        RuntimeTextExtractor.Observe("XXXX_IGNORAR", "test.debug");
        RuntimeTextExtractor.Stop();

        string output = Path.Combine(AppDomain.CurrentDomain.BaseDirectory,
            "TalesOfMortal_i18N_Extracted", "runtime.json");
        if (!File.Exists(output))
            throw new Exception("Arquivo de extração não foi salvo: " + output);

        var obj = JsonTextParser.ParseObject(File.ReadAllText(output));
        var entries = obj["entries"] as List<object>;
        if (entries == null)
            throw new Exception("JSON de extração não contém entries.");
        bool chinese = false, english = false;
        foreach (object item in entries)
        {
            var row = item as Dictionary<string, object>;
            if (row == null) continue;
            string source = row["text"] as string;
            if (source == "龙门客栈") chinese = true;
            if (source == "English quest objective") english = true;
        }
        if (!chinese || !english)
            throw new Exception("Extração não capturou ambos idiomas.");
        Console.WriteLine("ExtractorSmoke OK: extração CJK/latina salva em JSON.");
    }
}
