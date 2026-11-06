"""Endereços públicos das mídias.

O GitHub Pages não roda código, mas serve arquivos. A foto preparada fica em
instagram-automation/fila/ e, por isso, ganha um endereço público que a Meta
consegue baixar na hora de publicar.
"""
import os
import urllib.request

from . import comum


def caminho_repo(arquivo):
    return f"{comum.config()['pasta_fila']}/{arquivo}"


def url_bruta(arquivo, ref="main"):
    repo = os.environ.get("GITHUB_REPOSITORY", "estradaemdois/estrada-em-dois")
    return f"https://raw.githubusercontent.com/{repo}/{ref}/{caminho_repo(arquivo)}"


def url_site(arquivo):
    return f"{comum.config()['url_site'].rstrip('/')}/{caminho_repo(arquivo)}"


def acessivel(url):
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200
    except Exception:
        return False


def url_para_meta(arquivo, verificar=acessivel):
    """Prefere o endereço do próprio site; se ainda não estiver no ar, usa o do GitHub."""
    for url in (url_site(arquivo), url_bruta(arquivo)):
        if verificar(url):
            return url
    raise RuntimeError(f"A mídia {arquivo} ainda não está acessível publicamente. "
                       "Espere alguns minutos e comente /aprovar de novo.")
