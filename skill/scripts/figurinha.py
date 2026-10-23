"""
Figurinhas de WhatsApp a partir de qualquer imagem: tira o fundo, encaixa em
512×512 com 16 px de margem e põe o contorno branco de adesivo.

    figurinha.py grade <imagem> <saida.png> [--caixa x,y,largura,altura]
        A imagem com uma grade de coordenadas do original por cima, para escolher
        a caixa. Com --caixa, só aquela região, ampliada e com grade mais fina:
        serve para traçar o --apagar.

    figurinha.py recortar <imagem> <saida-sem-extensao> [opções]
        Gera <saida>.webp (o do WhatsApp, até 100 KB) e <saida>.png.
        --caixa x,y,largura,altura   o retângulo da figura, em pixels do original
        --apagar x1,y1,x2,y2,x3,y3…  polígono, em pixels do original, que sai da
                                     figura de qualquer jeito (pode repetir)
        --contorno N                 largura do contorno branco (padrão 7; 0 tira)
        --previa <arquivo.png>       a figurinha sobre fundo escuro e claro, lado a lado
        --conferencia <arquivo.png>  o recorte no tamanho do original, sobre um
                                     fundo liso que contrasta, com a grade do original

Rode pelo `figurinha.sh`, que prepara o venv e o modelo. O modelo é o BiRefNet
general em ONNX, o mesmo do rembg, chamado direto: sem o rembg e as dependências
dele, o venv cai de ~780 MB para ~220 MB. A versão lite do modelo (224 MB em vez
de 973 MB) foi testada em 23/10/2026 e não serve: comeu o escudo e a espada da
rosquinha gladiadora.
"""

import argparse
import io
import os
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

LADO, MARGEM = 512, 16
LIMITE_WEBP = 100 * 1024
CASA = Path(os.environ.get("FIGURINHAS_HOME", Path.home() / ".cache" / "figurinhas"))


def grade(imagem: str, saida: str, caixa: str | None) -> None:
    img = Image.open(imagem).convert("RGB")
    W, H = img.size
    x0, y0, w, h = (int(v) for v in caixa.split(",")) if caixa else (0, 0, W, H)
    img, passo, zoom = com_grade(img.crop((x0, y0, x0 + w, y0 + h)), x0, y0)
    img.save(saida)
    regiao = f"região {w}×{h} em {x0},{y0}, ampliada {zoom:.1f}×" if caixa else "a imagem inteira"
    print(f"{imagem}: {W}×{H}; {regiao}; grade a cada {passo} px, rotulada a cada {passo * 2}")


def com_grade(img: Image.Image, x0: int, y0: int) -> tuple[Image.Image, int, float]:
    """A região (que começa em x0,y0 do original) ampliada e com a grade do original."""
    w, h = img.size
    # Ampliada até ~1000 px no lado maior, para o traço do polígono sair preciso.
    zoom = max(1.0, 1000 / max(w, h))
    img = img.resize((round(w * zoom), round(h * zoom)), Image.LANCZOS)
    passo = next(p for p in (10, 25, 50, 100, 200) if max(w, h) / p <= 15)
    desenho = ImageDraw.Draw(img)
    fonte = ImageFont.load_default(size=max(12, max(img.size) // 70))
    rotulo = dict(fill=(255, 255, 0), font=fonte, stroke_width=2, stroke_fill=(0, 0, 0))
    for x in range(-(-x0 // passo) * passo, x0 + w, passo):
        forte = x % (passo * 2) == 0
        px = round((x - x0) * zoom)
        desenho.line([(px, 0), (px, img.height)], fill=(255, 0, 255) if forte else (0, 255, 255), width=1)
        if forte:
            desenho.text((px + 2, 2), str(x), **rotulo)
    for y in range(-(-y0 // passo) * passo, y0 + h, passo):
        forte = y % (passo * 2) == 0
        py = round((y - y0) * zoom)
        desenho.line([(0, py), (img.width, py)], fill=(255, 0, 255) if forte else (0, 255, 255), width=1)
        if forte:
            desenho.text((2, py + 2), str(y), **rotulo)
    return img, passo, zoom


def mascara(img: Image.Image) -> Image.Image:
    """
    O pré e pós-processamento do BiRefNet no rembg. Uma diferença de propósito: o
    rembg escurece a cor da borda semitransparente; aqui ela fica com a cor original.
    """
    import onnxruntime as ort

    caminho = CASA / "modelos" / "birefnet-general.onnx"
    if not caminho.exists():
        sys.exit(f"Falta o modelo {caminho}: rode pelo figurinha.sh, que o baixa.")
    # Com a arena de memória ligada (o padrão), o pico passou de 23 GB e o processo
    # foi morto por falta de memória; sem ela, fica em ~7,5 GB.
    opcoes = ort.SessionOptions()
    opcoes.enable_cpu_mem_arena = False
    opcoes.enable_mem_pattern = False
    sessao = ort.InferenceSession(str(caminho), opcoes, providers=["CPUExecutionProvider"])
    a = np.array(img.resize((1024, 1024), Image.LANCZOS)).astype(np.float64)
    a = a / max(a.max(), 1e-6)
    a = (a - (0.485, 0.456, 0.406)) / (0.229, 0.224, 0.225)
    entrada = a.transpose(2, 0, 1)[None].astype(np.float32)
    saida = sessao.run(None, {sessao.get_inputs()[0].name: entrada})[0][0, 0]
    p = 0.5 * (1 + np.tanh(saida / 2))  # a sigmoide, sem estourar o exp
    p = (p - p.min()) / (p.max() - p.min())
    return Image.fromarray((p * 255).astype(np.uint8), mode="L").resize(img.size, Image.LANCZOS)


def componentes(cheio: np.ndarray) -> tuple[np.ndarray, list[int]]:
    """
    As partes conexas de uma máscara: o rótulo de cada pixel (0 fora) e a área de
    cada parte (`areas[0]` não conta). Busca em largura com um rótulo por pixel: o
    modelo deixa milhares de pontinhos de ruído, e guardar uma máscara por parte
    estourou a memória.
    """
    h, w = cheio.shape
    fundo = (~cheio).ravel().tolist()
    rotulo = [0] * (h * w)
    areas = [0]
    for inicio in range(h * w):
        if fundo[inicio] or rotulo[inicio]:
            continue
        n = len(areas)
        rotulo[inicio] = n
        fila, area = deque([inicio]), 0
        while fila:
            i = fila.popleft()
            area += 1
            y, x = divmod(i, w)
            for j, ok in ((i - w, y > 0), (i + w, y < h - 1), (i - 1, x > 0), (i + 1, x < w - 1)):
                if ok and not fundo[j] and not rotulo[j]:
                    rotulo[j] = n
                    fila.append(j)
        areas.append(area)
    return np.array(rotulo).reshape(h, w), areas


def tirar_cacos(alfa: np.ndarray) -> int:
    """Apaga as partes soltas com menos de 2% da maior: restos do fundo que o modelo deixou."""
    rotulo, areas = componentes(alfa > 0)
    if len(areas) <= 2:
        return 0
    minimo = 0.02 * max(areas)
    cacos = np.array([a < minimo for a in areas])
    cacos[0] = False
    alfa[cacos[rotulo]] = 0
    return int(cacos.sum())


def recortar(
    imagem: str,
    saida: str,
    caixa: str | None,
    apagar: list[str],
    contorno: int,
    previa: str | None,
    conferencia: str | None,
) -> None:
    poligonos = []
    for p in apagar:
        v = [int(n) for n in p.split(",")]
        if len(v) < 6 or len(v) % 2:
            sys.exit(f"--apagar precisa de pelo menos 3 pontos x,y: {p}")
        poligonos.append(v)
    img = Image.open(imagem).convert("RGB")
    x, y = 0, 0
    if caixa:
        x, y, w, h = (int(v) for v in caixa.split(","))
        img = img.crop((x, y, x + w, y + h))
    figura = img.convert("RGBA")
    alfa = mascara(img)
    # O que o modelo trouxe junto e a caixa não deixa de fora. Vem antes dos
    # cacos: o que o polígono separar da figura sai como caco.
    for v in poligonos:
        ImageDraw.Draw(alfa).polygon([(v[i] - x, v[i + 1] - y) for i in range(0, len(v), 2)], fill=0)
    alfa = np.array(alfa)
    alfa[alfa <= 40] = 0  # o halo semitransparente em volta
    cacos = tirar_cacos(alfa)
    figura.putalpha(Image.fromarray(alfa))
    if conferencia:
        # O recorte no tamanho do original, sobre um fundo liso, com a grade do
        # original: mostra resto pequeno que a prévia de 512 px esconde, já com
        # as coordenadas para o --apagar. O fundo é verde ou azul, o mais
        # distante da cor média da figura: um sapo sumiria no verde. Magenta não,
        # que é a cor das linhas fortes da grade.
        media = np.array(figura)[alfa > 128][:, :3].mean(axis=0) if (alfa > 128).any() else np.zeros(3)
        cores = {"verde": (0, 170, 0), "azul": (0, 60, 220)}
        nome_cor = max(cores, key=lambda c: np.linalg.norm(media - cores[c]))
        liso = Image.new("RGBA", figura.size, (*cores[nome_cor], 255))
        liso.alpha_composite(figura)
        com_grade(liso.convert("RGB"), x, y)[0].save(conferencia)
    if not figura.getchannel("A").getbbox():
        sys.exit("O modelo não achou figura nenhuma: confira a caixa.")
    figura = figura.crop(figura.getchannel("A").getbbox())

    alvo = LADO - 2 * MARGEM - 2 * contorno
    esc = alvo / max(figura.size)
    figura = figura.resize((round(figura.width * esc), round(figura.height * esc)), Image.LANCZOS)
    tela = Image.new("RGBA", (LADO, LADO), (0, 0, 0, 0))
    tela.alpha_composite(figura, ((LADO - figura.width) // 2, (LADO - figura.height) // 2))

    # Furo é a transparência que não chega à borda da tela: o miolo de uma
    # rosquinha, o vão entre o braço e o corpo. Conta os de 20 px ou mais.
    silhueta = tela.getchannel("A").point(lambda v: 255 if v > 128 else 0)
    fora = silhueta.copy()
    ImageDraw.floodfill(fora, (0, 0), 128)
    furo = fora.point(lambda v: 255 if v == 0 else 0)
    furos = sum(a >= 20 for a in componentes(np.array(furo) > 0)[1][1:])
    if contorno:
        # O contorno engorda a silhueta; num furo ele o taparia, então ali fica só um friso.
        borda = silhueta.filter(ImageFilter.MaxFilter(contorno * 2 + 1))
        friso = silhueta.filter(ImageFilter.MaxFilter(5))
        borda = Image.composite(friso, borda, furo).filter(ImageFilter.GaussianBlur(1))
        fundo = Image.new("RGBA", tela.size, (255, 255, 255, 0))
        fundo.putalpha(borda)
        fundo.alpha_composite(tela)
        tela = fundo

    Path(saida).parent.mkdir(parents=True, exist_ok=True)
    tela.save(f"{saida}.png", optimize=True)
    for q in (85, 75, 65, 55, 45):
        buf = io.BytesIO()
        tela.save(buf, "WEBP", quality=q, alpha_quality=100, method=6)
        if buf.tell() <= LIMITE_WEBP:
            break
    Path(f"{saida}.webp").write_bytes(buf.getvalue())

    if previa:
        lado_a_lado = Image.new("RGB", (LADO * 2, LADO))
        for i, cor in enumerate(("#0b141a", "#efeae2")):  # os fundos do WhatsApp, escuro e claro
            quadro = Image.new("RGBA", (LADO, LADO), cor)
            quadro.alpha_composite(tela)
            lado_a_lado.paste(quadro.convert("RGB"), (i * LADO, 0))
        lado_a_lado.save(previa)

    print(f"{saida}.webp: {buf.tell() / 1024:.0f} KB (qualidade {q}){'  ⚠️ acima de 100 KB' if buf.tell() > LIMITE_WEBP else ''}")
    print(f"{saida}.png: {Path(f'{saida}.png').stat().st_size / 1024:.0f} KB")
    print(f"cacos removidos: {cacos}; furos vazados: {furos}")
    if conferencia:
        print(f"conferência: {conferencia} (fundo {nome_cor})")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="comando", required=True)
    g = sub.add_parser("grade")
    g.add_argument("imagem")
    g.add_argument("saida")
    g.add_argument("--caixa")
    r = sub.add_parser("recortar")
    r.add_argument("imagem")
    r.add_argument("saida")
    r.add_argument("--caixa")
    r.add_argument("--apagar", action="append", default=[])
    r.add_argument("--contorno", type=int, default=7)
    r.add_argument("--previa")
    r.add_argument("--conferencia")
    a = p.parse_args()
    if a.comando == "grade":
        grade(a.imagem, a.saida, a.caixa)
    else:
        recortar(a.imagem, a.saida, a.caixa, a.apagar, a.contorno, a.previa, a.conferencia)


if __name__ == "__main__":
    main()
