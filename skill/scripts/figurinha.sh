#!/usr/bin/env bash
# Porta de entrada da skill: prepara o ambiente na primeira vez e roda o
# figurinha.py com um teto de memória.
#
#   figurinha.sh grade <imagem> <saida.png> [--caixa x,y,l,a]
#   figurinha.sh recortar <imagem> <saida-sem-extensao> [--caixa x,y,l,a] [--apagar x1,y1,x2,y2,x3,y3…]
#                        [--contorno N] [--previa p.png] [--conferencia c.png]
#   figurinha.sh espaco      quanto o ambiente ocupa
#   figurinha.sh limpar      apaga o ambiente e o modelo (voltam sozinhos no próximo uso)
#
# Tudo mora em $FIGURINHAS_HOME (padrão ~/.cache/figurinhas): o venv (~220 MB,
# sem cache do pip) e o modelo (~970 MB). Nada vai para ~/.u2net nem ~/.cache/pip.
set -euo pipefail

CASA="${FIGURINHAS_HOME:-$HOME/.cache/figurinhas}"
AQUI="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
PY="$CASA/venv/bin/python"
MODELO="$CASA/modelos/birefnet-general.onnx"
TETO="${FIGURINHAS_TETO_MEMORIA:-12G}"

# O BiRefNet general em ONNX, das releases do rembg. O hash é o do download de
# 23/10/2026, que gerou as figurinhas aprovadas.
URL="https://github.com/danielgatis/rembg/releases/download/v0.0.0/BiRefNet-general-epoch_244.onnx"
SHA="58f621f00f5d756097615970a88a791584600dcf7c45b18a0a6267535a1ebd3c"

preparar() {
  if [[ ! -x "$PY" ]]; then
    echo "→ criando o ambiente em $CASA/venv (~220 MB, só na primeira vez)" >&2
    mkdir -p "$CASA"
    python3 -m venv "$CASA/venv"
    PIP_NO_CACHE_DIR=1 "$CASA/venv/bin/pip" install -q --disable-pip-version-check onnxruntime numpy pillow
  fi
  [[ "${1:-}" == "com-modelo" && ! -f "$MODELO" ]] || return 0
  echo "→ baixando o modelo (~970 MB, só na primeira vez)" >&2
  mkdir -p "$(dirname "$MODELO")"
  curl -fL --progress-bar -o "$MODELO.part" "$URL"
  if [[ "$(sha256sum "$MODELO.part" | cut -d' ' -f1)" != "$SHA" ]]; then
    rm -f "$MODELO.part"
    echo "✗ o modelo baixado não confere com o hash esperado; apaguei" >&2
    exit 1
  fi
  mv "$MODELO.part" "$MODELO"
}

com_teto() {
  # O recorte tem pico de ~7,5 GB; o teto impede que um descontrole leve a máquina junto.
  if command -v systemd-run >/dev/null && systemd-run --user --scope -q true 2>/dev/null; then
    systemd-run --user --scope -q -p MemoryMax="$TETO" -p MemorySwapMax=0 "$@"
  else
    "$@"
  fi
}

case "${1:-}" in
  espaco)
    if [[ -d "$CASA" ]]; then du -h -d1 "$CASA" | sort -h; else echo "nada instalado em $CASA"; fi
    ;;
  limpar)
    if [[ -d "$CASA" ]]; then du -sh "$CASA"; rm -rf "$CASA"; echo "✓ apagado $CASA"; else echo "nada a limpar em $CASA"; fi
    ;;
  grade)
    preparar
    exec "$PY" -I "$AQUI/figurinha.py" "$@"
    ;;
  recortar)
    preparar com-modelo
    com_teto "$PY" -I "$AQUI/figurinha.py" "$@" || {
      s=$?
      [[ $s -eq 137 ]] && echo "✗ morto por passar do teto de memória ($TETO); suba com FIGURINHAS_TETO_MEMORIA" >&2
      exit $s
    }
    ;;
  *)
    sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'
    exit 2
    ;;
esac
