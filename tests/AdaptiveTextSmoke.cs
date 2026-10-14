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
        if (AdaptiveText.Enabled || !AdaptiveText.OnlyTranslated)
            throw new Exception("Ajuste de fonte deve iniciar desativado por segurança IL2CPP.");

        var legacy = new UnityEngine.UI.Text { fontSize = 20 };
        AdaptiveText.TryFit(legacy, "Short", "Tradução longa demais para a área do texto.");
        if (legacy.resizeTextForBestFit || legacy.fontSize != 20)
            throw new Exception("O ajuste desativado não deve alterar a UI.");

        var tmp = new TMPro.TextMeshProUGUI { fontSize = 24f };
        AdaptiveText.TryFit(tmp, "Short", "Tradução longa demais para a área do texto.");
        if (tmp.enableAutoSizing || tmp.fontSize != 24f)
            throw new Exception("O ajuste desativado não deve alterar o TMP.");

        AdaptiveText.Clear();
        Console.WriteLine("AdaptiveTextSmoke OK: UI e TMP preservados com ajuste desativado.");

    }
}
