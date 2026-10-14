# AGENTS.md

Instruções permanentes para agentes de IA que alteram este repositório.
Escopo: toda a árvore do projeto, especialmente `mod/i18n/pt-BR/`, `scripts/` e `tests/`.
Idioma das traduções: português brasileiro (pt-BR).

## Prioridades de localização

1. **Preserve o nome original em inglês de itens, técnicas, habilidades, artes, manuais e equipamentos.** Não traduza, adapte, reorganize, abrevie nem substitua partes desses nomes. Ex.: `Azure Jade` continua `Azure Jade`; `Wind's Misty Sutra` continua `Wind's Misty Sutra`; `G6 Skill Fruit` continua `G6 Skill Fruit`. O mesmo vale dentro de mensagens, históricos, recompensas, tooltips, lojas e nomes envoltos em tags.
2. **Traduza para pt-BR as descrições e os efeitos** de itens, técnicas e habilidades, inclusive instruções de uso, efeitos de combate, mensagens explicativas e textos de interface. O nome próprio mencionado na descrição permanece em inglês. Ex.: `Do not take Lustrous Yang Elixir!` vira `Não tome Lustrous Yang Elixir!`.
3. **Preserve nomes próprios de NPCs e de cidades/regiões** na grafia adotada pelo jogo: `Yong Ning`, `Hua Feng`, `Mu Xian`, `Yun Mo` etc. Não romanize automaticamente nomes chineses de NPCs e não substitua nomes por palavras comuns em português.
4. Para textos originalmente chineses, use o **nome oficial em inglês, quando confirmado**. Se não for possível identificar com segurança o nome de um item, técnica ou personagem, sinalize para revisão contextual; não invente um nome nem aplique traduções literais a supostos nomes próprios.
5. **Padronize os atributos/elementos, mas somente quando forem atributos e não parte de nomes próprios:** `Wood` / `木属性` = **Madeira**; `Lightning` / `雷属性` = **Raio**; `Fire` / `火属性` = **Fogo**; `Wind` / `风属性` = **Vento**; `Water` / `水属性` = **Água**; `Earth` / `土属性` = **Terra**. Para os atributos use `Qi de Madeira`, `Aptidão com Madeira`, `Velocidade de movimento` e `Alcance da habilidade` conforme `docs/TERMINOLOGY.md`. Não traduza o `Wood` dentro do nome próprio `Wood's ...`.
6. Diferencie **nome do item** de **frase ao redor do item**: `Azure Jade` fica intacto, mas `Insuficiente Azure Jade` pode ser `Azure Jade insuficiente`. `Receita de Sky Grass` traduz `Receita de`, preservando `Sky Grass`. Não force todo texto que contém `Elixir`, `Stone` ou `Fruit` a ficar sem tradução; analise a função da frase.
7. **Não traduza textos técnicos da engine**: nunca altere as chaves de origem de `translations`, os IDs de `keys`, placeholders (ex.: `{0}`, `{call|B|A}`), tokens (ex.: `$s_...$`, `&...&`), identificadores de sprites, atributos das tags Unity/TextMeshPro, códigos de cor, nomes de arquivos, caminhos, referências internas ou chaves de configuração. Preserve as tags e seu balanceamento.
8. Não faça substituições globais por palavras isoladas em diálogos. `wood` pode significar o elemento Madeira ou madeira como material; `Lightning`, `Fire` e `Wind` podem integrar nomes próprios de itens/técnicas. Faça correções por contexto ou somente em rótulos de atributo exatos.
9. Preserve quebras de linha significativas, pontuação técnica, números e unidades. Não descarte informações originais. Evite traduzir textos que já são somente nomes próprios ou identificadores.

## Fluxo de revisão

- Trabalhe na branch `Dev` (salvo orientação expressa diferente), em commits pequenos e descritivos. Não publique na `main` nem faça release sem solicitação.
- Antes de alterar um valor, consulte sua chave original e identifique se o conteúdo é **nome próprio**, **descrição**, **rótulo de atributo**, **mensagem de interface** ou **token técnico**.
- Use `docs/TERMINOLOGY.md` e `scripts/audit_terminology.py` como referências, mantendo um único glossário de elementos. Evite reintroduzir divergências entre auditorias/importadores.
- Valide JSON, equivalência de placeholders/sprites/tags, e rode `python3 scripts/audit_terminology.py`, `python3 scripts/review_five_passes.py` e os testes disponíveis. Confira também as diferenças de nomes protegidos.
- A detecção automática de nomes de itens e técnicas é **conservadora e incompleta**. Não trate heurísticas ou uma auditoria sem erros como comprovação de tradução correta. Registre casos ambíguos, sem corrigi-los às cegas.
- O catálogo comunitário `Workshop_2990310797.json` pode ser gerado localmente e não estar todo versionado. Não afirme que foi revisado integralmente sem ter acesso ao arquivo real.
- Não modifique DLLs, mods de terceiros, arquivos da Steam ou a instalação do jogo como efeito colateral de uma revisão textual.

Em caso de conflito entre regras antigas e estas instruções, prevalece a decisão mais recente do usuário: **nomes de itens e técnicas em inglês; descrições em português brasileiro; elemento Wood traduzido como Madeira quando for atributo**.
