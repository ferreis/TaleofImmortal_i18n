using System;
using TalesOfMortalI18N;

namespace UnityEngine.UI
{
    public class InputField { }

    public class Text
    {
        public int fontSize { get; set; }
        public bool resizeTextForBestFit { get; set; }
        public int resizeTextMinSize { get; set; }
        public int resizeTextMaxSize { get; set; }
        public bool IsInput;
        public object GetComponentInParent(Type type)
        {
            return IsInput && type == typeof(InputField) ? new InputField() : null;
        }
    }
}

namespace TMPro
{
    public class TMP_InputField { }

    public class TextMeshProUGUI
    {
        public float fontSize { get; set; }
        public bool enableAutoSizing { get; set; }
        public float fontSizeMin { get; set; }
        public float fontSizeMax { get; set; }
        public bool IsInput;
        public object GetComponentInParent(Type type)
        {
            return IsInput && type == typeof(TMP_InputField) ? new TMP_InputField() : null;
        }
    }
}

public static class AdaptiveTextSmoke
{
    public static void Run()
    {
        AdaptiveText.Initialize();
        // Após erros reais no setter IL2CPP, o recurso deve permanecer desativado.
        if (AdaptiveText.Enabled || !AdaptiveText.OnlyTranslated)
            throw new Exception("Fonte adaptativa experimental deve estar desativada por segurança.");

        // Os testes de propriedade abaixo exercitam o algoritmo isolado,
        // sem reativá-lo no jogo até termos um hook de layout seguro.
                var regular = new UnityEngine.UI.Text { fontSize = 20 };
        AdaptiveText.TryFit(regular, "short", "short");
        if (regular.resizeTextForBestFit)
            throw new Exception("Não deve modificar textos sem tradução.");

        AdaptiveText.TryFit(regular, "Short", "Traduzido: texto bastante grande para o campo de interface.");
        if (!regular.resizeTextForBestFit || regular.resizeTextMaxSize != 20 ||
            regular.resizeTextMinSize != 13)
            throw new Exception("Auto ajuste Unity UI.Text incorreto.");

        var input = new UnityEngine.UI.Text { fontSize = 18, IsInput = true };
        AdaptiveText.TryFit(input, "Short", "Uma descrição traduzida bastante longa.");
        if (input.resizeTextForBestFit)
            throw new Exception("Campo editável não pode ter auto ajuste.");

        var tmp = new TMPro.TextMeshProUGUI { fontSize = 24f };
        AdaptiveText.TryFit(tmp, "Short", "Uma descrição traduzida grande para a interface.");
        if (!tmp.enableAutoSizing || tmp.fontSizeMax != 24f ||
            Math.Abs(tmp.fontSizeMin - 15.6f) > .01f)
            throw new Exception("Auto ajuste TextMeshPro incorreto.");

        var tmpInput = new TMPro.TextMeshProUGUI { fontSize = 24f, IsInput = true };
        AdaptiveText.TryFit(tmpInput, "Short", "Outra descrição traduzida grande para a interface.");
        if (tmpInput.enableAutoSizing)
            throw new Exception("Campo TMP editável não pode ter auto ajuste.");

        var configured = new UnityEngine.UI.Text
        {
            fontSize = 17, resizeTextForBestFit = true,
            resizeTextMinSize = 11, resizeTextMaxSize = 17
        };
        AdaptiveText.TryFit(configured, "Short", "Tradução que já possui autoajuste.");
        if (configured.resizeTextMinSize != 11)
            throw new Exception("Não deve sobrescrever ajustes existentes.");

        AdaptiveText.Clear();
        Console.WriteLine("AdaptiveTextSmoke OK: fonte adaptativa sem interferir em campos editáveis.");
    }
}
