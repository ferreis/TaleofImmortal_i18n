# Glossário e revisão de tradução PT-BR

## Convenções fixas

A tradução prioriza consistência, legibilidade e segurança das variáveis
dinâmicas do Tale of Immortal. Essas convenções se aplicam aos JSON do jogo,
aos mods e ao fallback comunitário, **quando o contexto confirmar a mesma
estatística ou o mesmo elemento**.

| Conceito | Tradução canônica | Evitar |
| --- | --- | --- |
| Elemento `Lightning` / `雷属性` | **Raio** | Relâmpago, Trovão para o elemento |
| Elemento `Fire` / `火属性` | **Fogo** | Flamejante como nome de elemento |
| Elemento `Water` / `水属性` | **Água** | Aquático como nome de elemento |
| Elemento `Wood` / `木属性` | **Wood** | Madeira, Tábua, Árvore como nome de elemento |
| Elemento `Earth` / `土属性` | **Terra** | Solo como nome de elemento |
| Elemento `Wind` / `风属性` | **Vento** | Variações para o mesmo atributo |
| `Luck` quando representa atributo | **Sorte** | Luck, Fortuna sem critério |
| `Appearance` / `Looks` como atributo visual | **Aparência** | Sorte |
| `Movement Speed` | **Velocidade de movimento** | velocidade de deslocamento/andar |
| `Skill Range` | **Alcance da habilidade** | taxa de habilidade, raio de efeito |
| `Jianmu` como nome do armazém | **Jianmu** | construção, madeira de construção |

**Não confundir:** `Wood` é a grafia fixa do **elemento** e do seu Qi, inclusive em `Wood Qi` e `Aptidão com Wood`. A palavra portuguesa *madeira* permanece válida quando o texto fala do material físico (árvores, móveis, construções), nunca como sinônimo automático do elemento.

`Skill Rate` pode designar cadência, porcentagem,
taxa ou outro parâmetro do mod. **Não é sinônimo seguro de Skill Range**.
`Looking` também não equivale a Sorte; pode indicar "procurando" ou
referir-se a aparência conforme a origem. Essas expressões exigem contexto.

## Nomes que não devem ser traduzidos automaticamente

- **Regiões e cidades:** manter o padrão em inglês do jogo. Exemplos:
  `Yong Ning`, `Hua Feng`, `Mu Xian`, `Yun Mo`.
- **Nomes específicos de habilidades, artes, técnicas e skills:**
  quando o nome original já vem em inglês, mantê-lo em inglês, inclusive
  em títulos de itens, descrições e avisos relacionados.
- **Nomes próprios de NPCs:** preservar a identidade, mesmo que coincidam com palavras comuns. Nomes chineses
  podem ter homônimos; não fazer substituições globais por traduções
  automáticas nem converter um nome sem relação com sua fonte.
- **Variáveis:** preservar `{0}`, `{call|B|A}`, `$s_...$`,
  `&123_nome&`, `<sprite name="...">` e tags Unity exatamente.
  Esses códigos NÃO são prosa e não devem receber tradução.

**Observação:** manter o nome *da skill* em inglês não impede traduzir
suas descrições, efeitos e mensagens. E `Lightning` em uma habilidade
com nome próprio não deve ser substituído automaticamente por `Raio`.

## Nomes oficiais dos Espíritos de Artefato (Artifact Spirits)

O jogo utiliza **nomes próprios em inglês** para os Espíritos de Artefato,
não traduções literais ou fonéticas feitas por tradução automática.

Lista oficial publicada nas [notas da atualização do jogo na Steam,
30/06/2021](https://store.steampowered.com/news/posts/?enddate=1625033517&feed=steam_community_announcements):

Mengyi, Cangya, Jiuchen, Muqing, Ningshuang, Lingge, Yunling, Huofa,
Silver Edge, Xuanti, Bajiao, Jiuzhu, Zhenxin, Sharp Edge, Charon,
Searing Feather, Feiming, Youling, Sharpclaw, Darkfang, Voodoo, Muke,
Brawler e Rainmaker.

**Correções da interface de seleção:** `homens G um` → `Mengyi`,
`Luz UM` → `Muqing`, `hu Ofa` → `Huofa`,
`Colar Y ONU` → `Yunling`, `FeIming` → `Feiming`,
`Jovem` → `Youling`, `Borda de prata` → `Silver Edge` e
`Pena abrasadora` → `Searing Feather`.

Os nomes oficiais foram adicionados a `protected-names.json`.
Também foi corrigida a lista unificada com tags de cores do
`game.json` e a auditoria passou a detectar corrupção dessa lista.

**Cuidado com nomes que se confundem com palavras comuns:** a entrada
isolada `Jovem` foi normalizada porque o próprio texto da lista de
espíritos na extração antiga a usa como alias do espírito `Youling`.
A substituição é por string inteira, **não dentro de outras frases**,
mas uma outra interface que use exatamente a palavra `Jovem` ainda
poderá sofrer colisão. Uma correção por contexto exigirá verificar
a hierarquia da UI no jogo.

## Auditoria de todos os arquivos, inclusive fallback local

```bash
python3 scripts/audit_terminology.py
```

O relatório aparece em `dist/TalesOfMortal_i18N/terminology-audit.json`.
A auditoria verifica cada entrada de `translations`, contabiliza
`keys` e sinaliza marcadores divergentes, possível chinês ainda
não traduzido, inglês residual, alterações em nomes de técnicas,
perda de tags e quebras de linha.

Para **corrigir somente rótulos exatos e nomes ingleses completos**
cobertos pelas regras conservadoras:

```bash
python3 scripts/audit_terminology.py --apply
```

Esse comando não tenta "corrigir" arbitrariamente diálogos. Quando
`Workshop_2990310797.json` já foi gerado pelo importador comunitário,
ele também é incluído na revisão. O `import_workshop_ptbr.py`
passou a descartar traduções nas quais mudam variáveis internas ou
se perdem tags de interface.

A auditoria automatizada **não comprova a correção semântica de todas
as frases**: certas expressões têm sentidos dependentes do contexto
e alguns textos precisam ser vistos na UI real. A revisão humana
deve priorizar os `issues` do relatório.

## Falhas de interface do log de 13/10/2026

O log enviado registra numerosas `NullReferenceException` no
`UnityEngine.UI.Text.set_text`, após o recurso experimental que alterava
a fonte *dentro* desse setter. Isso é um ponto inseguro para mudar
`resizeTextForBestFit`, já que essa propriedade invalida o layout do
próprio texto. A manipulação da fonte foi retirada desse hook;
`adaptiveText.enabled` foi desativado por padrão.

O mesmo log mostra falhas separadas de
`Fatury.ResLateLoadPatch.Postfix` dentro de
`UnityEngine.Resources.Load`. O log por si só não demonstra
que o tradutor causou essa segunda falha.

O **tooltip ao passar o mouse ainda não foi implementado**. Não há
um tooltip funcional a ser ativado no `config.json` nesta versão.
Implementá-lo com segurança requer ligar o texto ao sistema de
eventos/layout usado no runtime IL2CPP e testá-lo dentro do jogo.
