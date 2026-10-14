> **Atualização de segurança (13/10/2026):** o ajuste automático de fonte foi DESATIVADO por padrão e removido do hook de `UnityEngine.UI.Text.set_text` após um log mostrar exceções IL2CPP repetidas nesse setter. Não o reative no `config.json`: a função precisa ser reimplementada fora do setter, com compatibilidade comprovada dentro do jogo. O tooltip continua sem implementação.

# Fonte adaptativa para traduções longas

A versão experimental previa reduzir automaticamente a fonte quando um
texto traduzido não cabe na área disponível de um componente de interface.

## Como funciona

A implementação usa somente propriedades já fornecidas pela Unity:

- `UnityEngine.UI.Text`: `resizeTextForBestFit`,
  `resizeTextMinSize`, `resizeTextMaxSize`.
- `TMPro.TextMeshProUGUI`: `enableAutoSizing`,
  `fontSizeMin`, `fontSizeMax`, **quando o hook TMP estiver disponível**.

Em vez de definir manualmente uma fonte menor para todos os textos, o mod
habilita a adaptação ao componente. O próprio mecanismo de layout tenta
encaixar o texto no retângulo original, mantendo a fonte normal quando há
espaço.

Ao iniciar, o mod lê `adaptiveText` do `ModAssets/i18n/config.json`:

```json
{
  "adaptiveText": {
    "enabled": true,
    "onlyTranslated": true,
    "minCharacters": 24,
    "minScale": 0.65,
    "minFontSize": 12
  }
}
```

- `enabled`: ativa/desativa o recurso ao iniciar o jogo.
- `onlyTranslated`: quando `true`, não interfere em textos cujo valor não
  foi alterado pelo tradutor.
- `minCharacters`: comprimento mínimo da frase para habilitar o autoajuste.
  Por padrão 24; configurável entre 10 e 200. Para menus menores, pode
  reduzir a 10, ciente de que mais labels serão ajustados.
- `minScale`: fração mínima do tamanho original, por padrão 65%.
- `minFontSize`: tamanho mínimo absoluto, por padrão 12.

Exemplo: em um label de 20 px, a fonte pode ser reduzida até 13 px e não
crescerá acima dos 20 px originais. Se o componente já tiver ajuste próprio,
o mod mantém as configurações originais.

**Segurança:** componentes `UnityEngine.UI.InputField` e
`TMPro.TMP_InputField` são ignorados para evitar problemas com cursor e
seleção. O recurso não altera tamanho de caixas, não traduz textos novos e
não muda os JSON de tradução.

## Testar no jogo

1. Feche o Tale of Immortal.
2. Na branch `Dev`, execute `git pull origin Dev` e
   `bash scripts/install-local.sh`.
3. Abra um menu com uma tradução longa, como descrições de mods e opções da seita.
4. Confirme que as letras diminuem apenas quando necessário, permanecendo
   legíveis. Se uma frase ainda ficar cortada, tente `minCharacters: 10` ou
   `minScale: 0.55` no config instalado e reinicie o jogo.
5. Se houver problemas visuais, defina `enabled: false` e reinicie.

O `AdaptiveTextSmoke` testa as propriedades por meio de componentes simulados
de UI.Text e TextMeshProUGUI, inclusive a exclusão de InputField. O build
offline **não prova** o resultado visual nem a presença dos hooks no jogo.

## Tooltip / texto completo ao passar o mouse

O tooltip é tecnicamente possível, porém **ainda não está implementado nesta
versão**. A interface do jogo utiliza objetos de diferentes sistemas de UI,
e a implementação precisa identificar um alvo de eventos de mouse sem
interferir em botões, menus nem cliques. Também precisa garantir que o texto
original continue acessível mesmo quando a fonte alcança seu tamanho mínimo.

A primeira etapa oferece redução automática de fonte; a etapa seguinte é
validar o hook de eventos de mouse e o overlay do tooltip dentro do jogo.
