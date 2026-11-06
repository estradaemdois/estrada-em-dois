"""Prepara a foto no formato que o Instagram aceita (JPEG, proporção entre 4:5 e 1,91:1)."""
from pathlib import Path

from PIL import Image, ImageOps

from . import comum

PROP_MIN = 4 / 5      # retrato mais "alto" aceito pelo Instagram
PROP_MAX = 1.91       # paisagem mais "larga" aceita pelo Instagram
EXTENSOES = (".png", ".jpg", ".jpeg", ".webp")


def melhor_original(caminho_relativo):
    """Se houver uma versão PNG/JPG maior com o mesmo nome, usa ela (mais qualidade)."""
    original = comum.PASTA_REPOSITORIO / caminho_relativo
    candidatos = [original.with_suffix(ext) for ext in EXTENSOES]
    existentes = [c for c in candidatos if c.exists()]
    if not existentes:
        raise FileNotFoundError(f"Não encontrei a foto {caminho_relativo} no repositório.")
    def largura(c):
        with Image.open(c) as im:
            return im.size[0]
    return max(existentes, key=largura)


def preparar_foto(caminho_relativo, destino, largura=1080):
    origem = melhor_original(caminho_relativo)
    with Image.open(origem) as bruta:
        img = ImageOps.exif_transpose(bruta).convert("RGB")
    w, h = img.size
    prop = w / h
    if prop < PROP_MIN:              # muito alta: corta em cima e embaixo, mantendo o centro
        novo_h = round(w / PROP_MIN)
        topo = (h - novo_h) // 2
        img = img.crop((0, topo, w, topo + novo_h))
    elif prop > PROP_MAX:            # muito larga: corta nas laterais
        novo_w = round(h * PROP_MAX)
        esq = (w - novo_w) // 2
        img = img.crop((esq, 0, esq + novo_w, h))
    if img.size[0] > largura:
        img = img.resize((largura, round(img.size[1] * largura / img.size[0])), Image.LANCZOS)
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    img.save(destino, "JPEG", quality=90, optimize=True, progressive=True)
    return {"origem": str(origem.relative_to(comum.PASTA_REPOSITORIO)), "tamanho": img.size}
