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
                AdaptiveText.Initialize();
                RuntimeTextExtractor.Start();
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
            RuntimeTextExtractor.Stop();
            AdaptiveText.Clear();
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
        private static readonly object Sync = new object();

        internal static void Info(string message)
        {
            Write("INFO", message);
        }

        internal static void Warning(string message)
        {
            Write("AVISO", message);
        }

        internal static void Error(string message)
        {
            Write("ERRO", message);
        }

        private static void Write(string level, string message)
        {
            string line = "[Tales of Mortal i18N] " + level + ": " + message;
            try
            {
                if (level == "ERRO") Console.Error.WriteLine(line);
                else Console.WriteLine(line);
            }
            catch { /* Sem console em alguns hosts IL2CPP */ }

            // Log próprio para diagnosticar o mod independentemente do MelonLoader.
            try
            {
                string path = System.IO.Path.Combine(
                    AppDomain.CurrentDomain.BaseDirectory, "TalesOfMortal_i18N.log");
                lock (Sync)
                {
                    System.IO.File.AppendAllText(
                        path,
                        DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") + " " + line + Environment.NewLine);
                }
            }
            catch { /* Permissões restritas não devem impedir o mod de inicializar */ }
        }
    }
}
