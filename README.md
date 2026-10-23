# figurinhas

Skill do Claude Code que faz figurinha de WhatsApp a partir de qualquer imagem:
recorta o personagem, tira o fundo e entrega WebP 512×512 (até 100 KB) e PNG,
com contorno branco de adesivo. Serve a qualquer projeto: é só pedir "faz uma
figurinha da rosquinha desta imagem".

Nasceu no `biblia-gringa` em 23/10/2026, com a rosquinha gladiadora e o Mestre.

## Instalação

```bash
cd ~/projects/figurinhas && make install
```

Isso liga `~/.claude/skills/figurinha` a `skill/`. O ambiente de recorte
(~1,2 GB: um venv Python e o modelo de IA) **não** se instala aqui: ele vem
sozinho na primeira figurinha, para `~/.cache/figurinhas`.

## Comandos

| Comando | O que faz |
|---|---|
| `make install` / `make uninstall` | liga e desliga a skill |
| `make status` | se a skill está ligada, e quanto o ambiente ocupa |
| `make espaco` | quanto o ambiente ocupa |
| `make limpar` | apaga o ambiente (~1,2 GB); ele volta sozinho na próxima figurinha |

## Onde ficam as figurinhas

Se o projeto tiver um lugar próprio para elas, vão para lá (o site da Gringa tem
um álbum). Se não tiver, vão para `~/Pictures/figurinhas/<tema>/`, com um
`recortes.tsv` que guarda de onde cada uma saiu.

## Como funciona

O passo a passo que o Claude segue está em [`skill/SKILL.md`](skill/SKILL.md):
achar a imagem na maior resolução, escolher a caixa da figura sobre uma grade de
coordenadas, recortar, conferir a prévia sobre os fundos escuro e claro do
WhatsApp, e só entregar depois da sua aprovação.
