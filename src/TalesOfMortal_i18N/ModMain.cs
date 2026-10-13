using System;

namespace TalesOfMortalI18N
{
    // Entrada para o ModCode do Tale of Immortal.
    // Nenhuma referência a DLLs do jogo é necessária na compilação.
    public class ModMain
    {
        private const string HarmonyId = "br.ferreis.talesofmortal.i18n";
        private ReflectionPatcher patcher;

        public void Init()
        {
            try
            {
                TranslationCatalog.Load();
                patcher = new ReflectionPatcher(HarmonyId);
                int installed = patcher.Install();
                ModLog.Info("Iniciado. Hooks instalados: " + installed + ".");
            }
            catch (Exception error)
            {
                ModLog.Error("Falha ao iniciar: " + error);
            }
        }

        public void Destroy()
        {
            if (patcher != null)
            {
                patcher.Unpatch();
                patcher = null;
            }

            TranslationCatalog.Clear();
        }
    }

    internal static class ModLog
    {
        internal static void Info(string message)
        {
            Console.WriteLine("[Tales of Mortal i18N] " + message);
        }

        internal static void Warning(string message)
        {
            Console.WriteLine("[Tales of Mortal i18N] AVISO: " + message);
        }

        internal static void Error(string message)
        {
            Console.Error.WriteLine("[Tales of Mortal i18N] ERRO: " + message);
        }
    }
}
