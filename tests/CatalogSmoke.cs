using System;
using TalesOfMortalI18N;

public static class CatalogSmoke
{
    public static int Main()
    {
        TranslationCatalog.Load();
        // Não basta traduzir uma palavra: TODOS os pacotes reais precisam
        // abrir, caso contrário o teste offline pode mascarar o erro do jogo.
        if (TranslationCatalog.TextCount < 3500 ||
            TranslationCatalog.ProtectedNameCount < 1700 ||
            TranslationCatalog.PatternCount < 5 ||
            TranslationCatalog.LoadedFileCount < 19)
        {
            Console.Error.WriteLine("ERRO: o catálogo foi carregado parcialmente: " +
                "textos=" + TranslationCatalog.TextCount +
                ", nomes=" + TranslationCatalog.ProtectedNameCount +
                ", padrões=" + TranslationCatalog.PatternCount +
                ", arquivos=" + TranslationCatalog.LoadedFileCount);
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
