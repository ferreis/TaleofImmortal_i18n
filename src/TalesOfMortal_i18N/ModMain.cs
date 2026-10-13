using System;
using System.Reflection;
using HarmonyLib;
using UnityEngine;

namespace TalesOfMortalI18N
{
    // Entrada do ModCode nativo do Tale of Immortal.
    public class ModMain
    {
        private const string HarmonyId = "br.ferreis.talesofmortal.i18n";
        private Harmony harmony;

        public void Init()
        {
            try
            {
                TranslationCatalog.Load();
                harmony = new Harmony(HarmonyId);
                int installed = TranslationPatches.Install(harmony);
                Debug.Log("[Tales of Mortal i18N] Iniciado. Hooks instalados: " + installed + ".");
            }
            catch (Exception error)
            {
                Debug.LogError("[Tales of Mortal i18N] Erro durante inicialização: " + error);
            }
        }

        public void Destroy()
        {
            if (harmony != null)
            {
                try { harmony.UnpatchSelf(); }
                catch (Exception error)
                {
                    Debug.LogWarning("[Tales of Mortal i18N] Erro ao remover hooks: " + error.Message);
                }
                harmony = null;
            }

            TranslationCatalog.Clear();
        }
    }
}
