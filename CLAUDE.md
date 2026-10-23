# CLAUDE.md

Repositório da skill `figurinha`: figurinha de WhatsApp a partir de uma imagem.
Para que serve e como instalar, veja o `README.md`. Para o fluxo que a skill
segue, veja `skill/SKILL.md`.

## Estrutura

- `skill/` → symlink em `~/.claude/skills/figurinha` (`make install`). É a pasta
  da skill: `SKILL.md` e `scripts/`.
- `skill/scripts/figurinha.sh` — a única porta de entrada. Prepara o venv e o
  modelo em `$FIGURINHAS_HOME` (padrão `~/.cache/figurinhas`) e roda o Python
  com teto de memória.
- `skill/scripts/figurinha.py` — o recorte: `grade` e `recortar`.

## Decisões e por quês (23/10/2026)

- **Sem rembg.** O BiRefNet em ONNX é chamado direto, com o mesmo pré e
  pós-processamento do rembg. Com isso o venv cai de ~780 MB para ~220 MB
  (onnxruntime, numpy e pillow) e o modelo vai para `~/.cache/figurinhas`, não
  para `~/.u2net`. O pip roda sem cache: o autor reclamou dos 2 GB de sobra da
  primeira vez. Conferido contra as figurinhas que o rembg gerou para o site da
  Gringa: visualmente iguais, com 0,4% de erro médio. A diferença está só na
  borda semitransparente, que o rembg escurece e aqui mantém a cor original.
- **Modelo `birefnet-general` (973 MB), não o lite (224 MB).** O lite comeu o
  escudo e a espada da rosquinha e deixou um borrão no Mestre. O
  `isnet-general-use` (179 MB), testado ainda pelo rembg, também comeu a espada.
- **Arena de memória do onnxruntime desligada.** Ligada, o processo passou de 23
  GB e o kernel o matou; desligada, o pico fica em ~7,5 GB. O `figurinha.sh` põe
  teto de 12 GB (`systemd-run --scope`, ajustável em `FIGURINHAS_TETO_MEMORIA`),
  para um descontrole não levar a máquina junto.
- **Cacos por busca em largura, com um rótulo por pixel.** O modelo deixa
  milhares de pontinhos de ruído, e guardar uma máscara por parte estourou a
  memória. O scipy faria o mesmo, mas custaria mais ~100 MB.
- **A caixa vai esticada para 1024×1024, como no rembg.** Completar até o
  quadrado, para não deformar, foi testado e piorou as três figurinhas: a
  salsicha trouxe um bloco de fundo, o furo da rosquinha fechou e a luminária
  do Mestre voltou.
- **`--apagar` existe porque a caixa não resolve tudo.** No primeiro teste de
  campo, a salsicha gladiadora (fundo carregado atrás da cabeça) não passou
  em três caixas diferentes. Com três polígonos, passou. O que o `--apagar`
  não faz é devolver uma parte: os dentes do tridente, finos e na frente da
  torcida, o modelo perde em qualquer caixa. Esse caso vai para o autor.
- **O hash do modelo é o do download de 23/10/2026.** Se a release do rembg
  mudar o arquivo, o `figurinha.sh` recusa e apaga: confira e atualize o `SHA`
  de propósito, não para calar o erro.

## Como testar uma mudança

Não há teste automático. Rode o recorte nas duas figurinhas de referência e
compare a prévia com as do site da Gringa (`compare -metric RMSE`, do
ImageMagick):

| Figurinha | Origem (repo `biblia-gringa`, em `site/`) | Caixa | Referência |
|---|---|---|---|
| rosquinha | `assets-source/cenas/its-very-fuck/cena-09-coliseu.jpg` | `70,255,520,430` | `src/assets/figurinhas/rosquinha-gladiadora.png` |
| Mestre | `assets-source/figurinhas/resizement-capa-suno.jpg` | `295,165,570,810` | `src/assets/figurinhas/mestre.png` |

As duas são casos difíceis: a espada fina da rosquinha e o furo dela, que tem de
ficar vazado, e o caco de luminária do Mestre, que tem de sumir.

O terceiro caso não tem referência aprovada: é a salsicha gladiadora, da mesma
cena da rosquinha. Ela serve para testar o `--apagar`. A caixa é `880,100,360,590`,
e os polígonos são estes:

```
--apagar 880,100,1015,100,1005,160,990,260,880,260
--apagar 990,100,1160,100,1160,180,1145,186,1125,150,1105,108,1080,108,1050,125,1036,140,1022,168,1015,185,995,205,990,205
--apagar 1155,100,1240,100,1240,188,1155,188
```

Com eles, o fundo atrás da cabeça some. O tridente continua sem os dentes.

**Mudou o `SKILL.md`?** Faça um teste de campo: um agente novo, sem o contexto
da sessão, recebe o pedido "faz uma figurinha da salsicha gladiadora desta
imagem", lê só o `SKILL.md` e para antes da entrega. Ele relata cada frase que
foi ambígua. Foram dois testes em 23/10/2026. Do primeiro saíram o `--apagar`, o `grade
--caixa` e a seção "Quando falha". Do segundo saíram a `--conferencia` e a
contagem dos furos. No segundo, o agente traçou os polígonos convertendo à mão a
escala da prévia para o original, e só achou os restos pequenos ampliando a
prévia por conta própria.

## Como o trabalho chega na main

Repositório pessoal, num Gitea próprio
(`git@git.kafeltz.com.br:ismael/figurinhas.git`). Não se abre pull request: o
trabalho vai direto para a `main`. Commitar e empurrar só a pedido do autor.
Os commits saem com o e-mail pessoal dele (`shalanga@gmail.com`).
