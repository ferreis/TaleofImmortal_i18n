using TalesOfMortalI18N;

// Entry point expected by Tale of Immortal for the generated mod ID DQKLF9.
// Keep the namespace and assembly name MOD_DQKLF9 in sync.
namespace MOD_DQKLF9
{
    public class ModMain
    {
        private readonly TalesOfMortalI18N.ModMain translator = new TalesOfMortalI18N.ModMain();

        public void Init()
        {
            translator.Init();
        }

        public void Destroy()
        {
            translator.Destroy();
        }
    }
}
