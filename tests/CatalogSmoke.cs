using System;
using TalesOfMortalI18N;

public static class CatalogSmoke
{
    public static int Main()
    {
        TranslationCatalog.Load();
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
