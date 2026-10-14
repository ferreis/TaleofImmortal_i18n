# Revisão em cinco passagens da localização PT-BR

Executada em 13/10/2026, após as correções do hook de texto e do
glossário. Esta revisão diferencia **erros de integridade** de
**itens linguísticos que precisam de contexto**.

## Cinco verificações independentes

1. **Estrutura de execução:** pares texto/tradução, variáveis `{0}`,
   parâmetros nativos `&...&` e `$s_...$`, sprites e tags Unity.
2. **Glossário:** Raio, Fogo, Água, Madeira, Terra, Sorte,
   Velocidade de movimento, Alcance da habilidade, por fonte identificada.
3. **Nomes próprios:** NPCs protegidos, regiões em inglês e nomes
   completos de técnicas/skills em inglês.
4. **Qualidade textual:** caracteres chineses ainda presentes,
   palavras em inglês não esperadas, sequências corrompidas e
   diferenças de quebras de linha.
5. **Consistência entre módulos:** a mesma chave ou o mesmo texto
   original com traduções divergentes em diferentes catálogos.

## Resultado no GitHub (22 JSON versionados)

O pipeline verificou **3.721 traduções por texto**, **76 traduções
por chave** e a lista de **1.759 nomes protegidos**.

Na primeira execução, foram sinalizadas 155 entradas com caracteres
chineses residuais e 230 diferenças de quebra de linha. As passagens
de estrutura, glossário, nomes próprios e conflitos não detectaram
divergências nesses arquivos. A revisão posterior padronizou nomes de
edifícios em 66 traduções de Cave e mais duas de FixData; as quantidades
remanescentes podem ser vistas no pipeline mais recente.

**Aviso:** o script sinaliza todos os caracteres chineses presentes em
uma tradução, inclusive nomes legítimos de NPCs que devem continuar
protegidos. Diferenças de quebras de linha também podem ser uma
reorganização textual intencional. Nenhum desses alertas significa
automaticamente um erro.

## Catálogo comunitário grande

O ZIP fornecido de `Workshop_2990310797.json` foi examinado
separadamente, com **35.014 traduções por texto e 52.855 chaves**.
As chaves foram comparadas ao conteúdo `localizations` do arquivo
original `2990310797.json` extraído da Workshop.

Foram encontrados **340 alertas candidatos** nesse catálogo:
- 104 diferenças nas variáveis internas `&...&` ou `$s_...$`;
- 20 diferenças nas tags Unity;
- 6 identificadores de sprites divergentes;
- 3 divergências em termos de glossário;
- 207 ocorrências de termos ingleses que exigem revisão de contexto.

Esses alertas são derivados **do snapshot recebido**, antes de executar
novamente o importador corrigido. As 130 sinalizações estruturais podem
incluir mudanças de formatação intencionais; o importador atualizado
adota uma postura conservadora e **rejeita linhas com identificadores
de variável, sprites ou estruturas de tags incompatíveis**.

Também foram encontradas, no texto chinês de origem, 247 entradas
com o termo `移动速度` cuja versão PT-BR usa `Agilidade`, 11
com `技能范围` e `Faixa de habilidade`, duas de `幸运`
traduzidas erroneamente como `Tipo`, e outros usos de `雷属性`
como `relâmpago` no sentido de elemento. A normalização por contexto
foi incorporada ao `scripts/import_workshop_ptbr.py`. Ela preserva
marcadores e aplica a convenção apenas se o original confirmar
o termo. O importador corrige tanto novos registros quanto
entradas existentes ao ser executado novamente.

A base comunitária integral é gerada localmente, não é enviada
automaticamente ao GitHub.

## Comandos para reproduzir sobre os catálogos ATUAIS

```bash
git switch Dev
git pull origin Dev

# Regenera o catálogo comunitário com proteção das variáveis e glossário:
python3 scripts/import_workshop_ptbr.py

# Todas as traduções locais, inclusive o catálogo grande:
python3 scripts/review_five_passes.py \
  --extracted dist/extracted/workshop/2990310797.json

# Aplica no jogo, com Tale of Immortal fechado:
bash scripts/install-local.sh
```

O relatório completo fica em:

```text
dist/TalesOfMortal_i18N/five-pass-review.json
dist/TalesOfMortal_i18N/five-pass-review.csv
```

O `GitHub Actions` executa o mesmo script de revisão para todos os
catálogos **versionados**. O catálogo comunitário só entra na checagem
automatizada local depois de ser importado.

## Conferência adicional (13/10/2026, após as cinco passagens)

Foi executada mais uma verificação independente dos 22 catálogos
versionados e dos arquivos de origem e importação comunitária que o
usuário havia enviado.

A revalidação do GitHub Actions, no commit da correção, passou com
**26 testes**, compilação da DLL, smoke tests e instalação simulada.
Nos catálogos versionados foram analisadas **3.721 traduções por texto,
76 chaves e 1.759 nomes protegidos**, sem colisões nem falhas de
estrutura detectadas. Permanecem **340 alertas de revisão contextual**:
110 textos com caracteres chineses (frequentemente nomes próprios)
e 230 casos de mudanças nas quebras de linha.

A auditoria revelou dois casos de borda que o importador anterior não
cobria:

1. Uma importação antiga poderia preservar traduções diretas para
   **nomes protegidos** ou fontes chinesas **ambíguas**, apesar de essas
   entradas já serem rejeitadas quando recém-importadas. O importador
   agora remove esses registros antigos, preservando os ajustes manuais
   estruturalmente válidos nas demais entradas. Também rejeita uma
   chave de localização associada a originais divergentes.
2. Alguns recursos do jogo representam sprites com aspas escapadas,
   por exemplo `<sprite name=\\"zm_lingshi\\">`; as traduções podem
   conter `<sprite name="zm_lingshi">`. A revisão agora compara
   os **identificadores reais**, e não a forma de escape do texto.
   Também valida separadamente tags Unity de abertura e fechamento.

A inspeção independente do ZIP antigo (antes dessas correções) mostrou
possíveis diferenças estruturais em valores já importados. Isso **não
descreve o resultado após regenerar o JSON local**. Para corrigir
automaticamente entradas rejeitadas, é obrigatório executar novamente
`python3 scripts/import_workshop_ptbr.py` no computador do usuário.
O ZIP comunitário completo não é enviado ao repositório e, portanto,
não integra a revisão automática do GitHub Actions.

## Limites

Cinco passagens automatizadas **não garantem a revisão linguística humana
de todas as frases** nem a tradução de textos nunca extraídos do jogo.
Nomes de NPCs podem permanecer em chinês de propósito, enquanto nomes
de regiões e títulos de habilidades em inglês são preservados conforme
o glossário. A integração final dos hooks e a apresentação de tooltips
exigem teste dentro do jogo.
