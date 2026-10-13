using System;
using TalesOfMortalI18N;

public static class CatalogSmoke
{
    public static int Main()
    {
        TranslationCatalog.Load();
        int expectedFiles = System.IO.Directory.GetFiles(
            System.IO.Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "i18n", "pt-BR"),
            "*.json", System.IO.SearchOption.AllDirectories).Length;
        // Não basta traduzir uma palavra: TODOS os pacotes reais precisam
        // abrir, caso contrário o teste offline pode mascarar o erro do jogo.
        if (TranslationCatalog.TextCount < 3500 ||
            TranslationCatalog.ProtectedNameCount < 1700 ||
            TranslationCatalog.PatternCount < 5 ||
            TranslationCatalog.LoadedFileCount != expectedFiles)
        {
            Console.Error.WriteLine("ERRO: o catálogo foi carregado parcialmente: " +
                "textos=" + TranslationCatalog.TextCount +
                ", nomes=" + TranslationCatalog.ProtectedNameCount +
                ", padrões=" + TranslationCatalog.PatternCount +
                ", arquivos=" + TranslationCatalog.LoadedFileCount +
                ", esperados=" + expectedFiles);
            return 1;
        }
        var parsed = JsonTextParser.ParseObject(
            @"{""translations"":{""\u52a0\u8f7d"":""teste"",""a"":""linha\n2""}}");
        var values = (System.Collections.Generic.Dictionary<string, object>)parsed["translations"];
        if ((string)values["加载"] != "teste" || (string)values["a"] != "linha\n2")
        {
            Console.Error.WriteLine("ERRO: interpretação de escapes JSON inválida.");
            return 1;
        }

        AssertTranslation("加载中...", "carregando...");
        AssertTranslation("Vingativo(a)", "Vingativo(a)");
        AssertTranslation("__texto_inexistente_i18n_1234__", "__texto_inexistente_i18n_1234__");
        AssertTranslation("加载中...\n__unknown__", "carregando...\n__unknown__");
        AssertTranslation("<color=red>lightning</color>", "<color=red>Raio</color>");
        AssertTranslation("Obsidian's Signing Firebolt", "Obsidian's Signing Firebolt");
        AssertTranslation("Yong Ning", "Yong Ning");

        // Captured FixData modal: dynamically rendered values, buttons and status.
        AssertTranslation("大鬼修复存档MOD", "Reparo de saves do Bahuang Dagui");
        AssertTranslation("前往大鬼首页", "Página do Dagui");
        AssertTranslation("加入大鬼QQ群", "Grupo QQ");
        AssertTranslation("充电支持大鬼", "Apoiar");
        AssertTranslation("展开修复详情", "Ver detalhes");
        AssertTranslation("存档修复完成，总共修补了166处错误。", "Reparo do save concluído. 166 erros corrigidos.");
        AssertTranslation("本次修复存档耗时43.48秒。", "Tempo do reparo: 43.48 segundos.");
        AssertTranslation("八荒大鬼为你的存档保驾护航！", "Bahuang Dagui ajuda a proteger seus saves!");
        AssertTranslation("删除166个无效月结日志", "166 registros mensais inválidos removidos");
        AssertTranslation("\n删除166个无效月结日志", "166 registros mensais inválidos removidos");
        AssertTranslation("存档修复完成，总共修补了166处错误。\n本次修复存档耗时43.48秒。\n八荒大鬼为你的存档保驾护航！", "Reparo do save concluído. 166 erros corrigidos.\nTempo do reparo: 43.48 segundos.\nBahuang Dagui ajuda a proteger seus saves!");
        AssertTranslation("存档修复完成，总共修补了204处错误。\r\n本次修复存档耗时12.50秒。\r\n八荒大鬼为你的存档保驾护航！", "Reparo do save concluído. 204 erros corrigidos.\nTempo do reparo: 12.50 segundos.\nBahuang Dagui ajuda a proteger seus saves!");
        AssertTranslation("存档修复完成，总共修补了{0}处错误。\n本次修复存档耗时{1}秒。\n八荒大鬼为你的存档保驾护航！", "Reparo do save concluído. {0} erros corrigidos.\nTempo do reparo: {1} segundos.\nBahuang Dagui ajuda a proteger seus saves!");

        ExtractorSmoke.Run();
        AdaptiveTextSmoke.Run();
        Console.WriteLine("CatalogSmoke OK: dicionários reais carregados com sucesso.");
        return 0;
    }

    private static void AssertTranslation(string input, string expected)
    {
        string actual = TranslationCatalog.TranslateText(input);
        if (actual != expected)
        {
            Console.Error.WriteLine("Falhou para " + input +
                ": recebido " + actual + ", esperado " + expected);
            Environment.Exit(1);
        }
    }
}
