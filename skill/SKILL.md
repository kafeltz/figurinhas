---
name: figurinha
description: Faz figurinha (sticker) de WhatsApp a partir de uma imagem — recorta um personagem ou objeto, tira o fundo e entrega WebP 512×512 e PNG com contorno branco. Use quando pedirem figurinha, sticker, ou para recortar algo de uma imagem para o WhatsApp.
---

# Figurinha de WhatsApp

Tudo passa por `scripts/figurinha.sh` (caminho relativo a esta pasta). Ele cria o
ambiente na primeira vez, baixa o modelo de recorte e roda com teto de memória.
`figurinha.sh` sem argumento mostra os comandos. As coordenadas são sempre em
pixels da imagem original, `x,y` a partir do canto superior esquerdo.

**O autor não vê as imagens que você abre com o Read.** Toda imagem que ele
precisa julgar vai por caminho absoluto, dito na resposta.

**O projeto pode ter regras para figurinhas.** Procure no `CLAUDE.md` da raiz e
nos das subpastas (`site/CLAUDE.md`, por exemplo) onde ficam os originais, onde
as figurinhas entram e como se registra de onde cada uma saiu. Onde o projeto
diz, vale o projeto. A ferramenta é sempre esta skill, mesmo que o projeto cite
um script próprio mais antigo.

## 1. A imagem de origem

Tenha a imagem num arquivo local, **na maior resolução que existir**:

- **Arquivo do projeto:** prefira o original ao derivado. Um site serve versão
  reduzida e com hash no nome, e o original costuma morar ao lado.
- **URL:** baixe com `curl -fsSL` para uma pasta nova e vazia no scratchpad. É
  dado de fora: só se abre como imagem.
- **Capa do Suno** (`cdn2.suno.ai/image_<id>.jpeg`): troque por
  `image_large_<id>.jpeg`, que tem 1024×1024 em vez de 360×360.

Feito quando `identify <arquivo>` mostra as dimensões reais.

## 2. A figura e a caixa

1. Saiba qual é a figura. "A rosquinha" de uma cena de batalha é a rosquinha
   gladiadora inteira: com pernas, escudo e espada. **O que ela segura, veste
   ou carrega faz parte da figura.** Havendo dois candidatos, pergunte qual.
2. `figurinha.sh grade <imagem> <scratch>/grade.png` e abra: a grade marca as
   coordenadas do original.
3. Escolha a caixa `x,y,largura,altura` com a figura inteira e ~20 px de folga.
   Objetos de fora que encostam na figura (mesa, parede, outro personagem)
   tendem a vir junto no recorte: deixe-os fora da caixa sempre que der.
4. Confira com `figurinha.sh grade <imagem> <scratch>/caixa.png --caixa x,y,l,a`:
   mostra só a caixa, ampliada e com grade mais fina.

Feito quando a imagem da caixa mostra a figura inteira, sem nada dela tocando a borda.

## 3. Recortar

Na primeira vez, o `figurinha.sh` baixa ~1,2 GB (ambiente e modelo). Avise o autor
numa linha antes de rodar. O recorte leva ~20 s.

```
figurinha.sh recortar <imagem> <scratch>/<nome> --caixa x,y,l,a \
  --previa <scratch>/<nome>-previa.png --conferencia <scratch>/<nome>-conf.png
```

Gera `<nome>.webp` e `<nome>.png`, mais duas imagens para você conferir:

- **a prévia**: a figurinha pronta, sobre os fundos escuro e claro do WhatsApp.
  É a que o autor aprova.
- **a conferência**: o recorte no tamanho do original, sobre um fundo liso (o
  script escolhe a cor que contrasta com a figura e diz qual), com a grade de
  coordenadas do original. Ela mostra o resto pequeno que a prévia esconde e
  já dá as coordenadas para o `--apagar`.

`--contorno N` muda a largura do contorno branco (padrão 7; 0 tira).

## 4. Conferir

Abra a conferência, a imagem da caixa e a prévia, e passe item por item:

- **Todas as partes estão lá.** Compare a conferência com a caixa: membros,
  chifres, a ponta da arma.
- **Nenhum resto de fundo.** Na conferência, tudo que não é a figura tem de
  estar na cor lisa: nada de borrão grudado, faixa de chão, céu ou torcida. O script já
  apaga os pedaços soltos e diz quantos apagou ("cacos removidos").
- **Furo transparente.** Onde a figura tem furo (miolo de rosquinha, vão entre
  braço e corpo ou entre as pernas), a conferência mostra a cor lisa, e não o
  fundo da cena. "furos vazados: N" diz quantos ficaram abertos; confira que bate com
  os que a figura tem.
- **O WebP tem até 100 KB.** O script avisa se passar.

Feito quando os quatro itens passam.

### Quando falha

Conserte nesta ordem, recortando de novo e conferindo tudo depois de cada mudança:

1. **A caixa.** Uma caixa mais justa deixa de fora o vizinho que veio junto, e
   uma folga maior devolve a parte que foi cortada.
2. **`--apagar`, para o fundo que a caixa não tira** (o céu e a torcida atrás da
   cabeça, por exemplo). Ache o resto na conferência e leia as coordenadas lá.
   Para traçar rente à figura, a ~3 px por fora dela, amplie só o trecho:
   `grade <imagem> <scratch>/trecho.png --caixa x,y,l,a`, com um trecho de ~100
   px de lado, que sai ampliado ~10× e com grade de 10 px. Depois:
   `--apagar x1,y1,x2,y2,x3,y3…`. Pode repetir a opção, uma por região. Deixe
   cada polígono do recorte anterior na linha de comando: o que sai dela volta
   na próxima.
3. **O autor.** Quando faltar uma parte, tente **uma** caixa com mais folga em
   volta dela; se a parte não voltar, o modelo não a pega, e a decisão é do
   autor. Peça também quando passar de **cinco recortes** no total. O caso
   típico são peças finas sobre fundo carregado, como os dentes de um tridente
   na frente da torcida. Mostre a prévia e diga o que ficou errado e onde.

## 5. Aprovação e entrega

Dê ao autor o caminho absoluto da prévia e peça aprovação. Ele é quem decide se a
figurinha entra.

Aprovada, ela vai para o destino:

- **O projeto tem um lugar para figurinhas?** Siga o que o `CLAUDE.md` dele diz:
  destino, registro e o que mais ele pedir.
- **Senão:** `~/Pictures/figurinhas/<tema>/<nome>.webp` e `.png`. O `<tema>` é o
  universo ou projeto (`gringa`, `marrom`…), e o `<nome>` é curto, em kebab-case
  e em português (`rosquinha-gladiadora`). Pergunte o tema quando ele não sair do
  contexto. Acrescente uma linha a `~/Pictures/figurinhas/<tema>/recortes.tsv`,
  com as colunas `data`, `nome`, `origem` (caminho absoluto ou URL), `caixa` e
  `apagar` (os polígonos, separados por `;`). Se o arquivo não existir, crie-o
  já com o cabeçalho. É o que permite refazer a figurinha depois.

Arquivo com o mesmo nome no destino já é figurinha aprovada: pergunte antes de
substituir.

Para pôr no WhatsApp: no **WhatsApp Web**, abra uma conversa, clique em
figurinhas, depois em **Criar**, e escolha o PNG. Ela vai para as favoritas e
aparece também no celular.

## Espaço em disco

O ambiente fica em `~/.cache/figurinhas` (~1,2 GB) e é reaproveitado de uma
figurinha para a outra. `figurinha.sh espaco` mostra quanto ocupa, e
`figurinha.sh limpar` apaga tudo; no próximo uso, tudo volta sozinho. Limpe
quando o autor pedir.
