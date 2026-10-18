#!/usr/bin/env python3
"""Gera as duas versões da página a partir de src/pagina.html e dos JSON em quicktrip/dados.

  quicktrip/index.html                versão do site: marca e rodapé do Estrada em Dois, mapa real
                                      (Leaflet + OpenStreetMap), lê dados/*.json
  _ferramentas/artefato/escapadas.html  (só com --artefato) versão de arquivo único de demonstração (dados
                                      embutidos, mapa esquemático em SVG)

Uso, a partir de qualquer pasta:  python3 quicktrip/_ferramentas/build.py
"""
import argparse
import json
import pathlib
import re

RAIZ = pathlib.Path(__file__).resolve().parent  # quicktrip/_ferramentas
PAGINA = RAIZ.parent  # quicktrip
DADOS = PAGINA / "dados"

SITE = "https://estradaemdois.com.br"
TITULO_SITE = "QuickTrip | Viagens de fim de semana por Estrada em Dois"
DESCRICAO = (
    "Escolha de onde você sai e até onde topa dirigir. O QuickTrip mostra destinos de fim de semana "
    "dentro do raio, com pontos turísticos, eventos, hospedagem, custo de combustível e rota, "
    "e sorteia um destino para você."
)

# hashes SRI conferidos contra o pacote npm leaflet@1.9.4
LEAFLET = (
    '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" '
    'integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="">\n'
    '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" '
    'integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>'
)

HEAD_SITE = f"""<meta name="description" content="{DESCRICAO}">
<meta name="theme-color" content="#07343c">
<link rel="canonical" href="{SITE}/quicktrip/">
<link rel="icon" href="/favicon.ico" sizes="any"><link rel="icon" type="image/png" sizes="32x32" href="/assets/icon-32.png"><link rel="apple-touch-icon" href="/assets/icon-180.png">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Estrada em Dois">
<meta property="og:title" content="{TITULO_SITE}">
<meta property="og:description" content="{DESCRICAO}">
<meta property="og:url" content="{SITE}/quicktrip/">
<meta property="og:image" content="{SITE}/assets/hero-casal.jpg">
<meta property="og:locale" content="pt_BR">
<meta name="robots" content="index, follow">
{LEAFLET}"""

MARCA_SITE = (
    '<a class="site-logo" href="/" aria-label="Estrada em Dois, página inicial">'
    '<img src="/assets/logo-estrada-em-dois.webp" alt="Estrada em Dois" width="52" height="52"></a>'
)
VOLTAR_SITE = '<a class="voltar" href="/">← Estrada em Dois</a>'
RODAPE_SITE = (
    '<p>QuickTrip é um projeto do <a href="/">Estrada em Dois</a>. '
    '© 2026 Estrada em Dois. Todos os direitos reservados.</p>'
)
NOTA_ARTEFATO = (
    "<p>Esta é a versão de demonstração. O mapa é esquemático e as estrelas aparecem como links para o Google Maps. "
    "A versão do projeto tem mapa real, avaliações e eventos atualizados por script. Os espaços de parceiros são vagas de exemplo.</p>"
)


def ler(nome):
    return json.loads((DADOS / nome).read_text(encoding="utf-8"))


def json_para_script(obj):
    # evita que "</script>" ou "<!--" dentro dos dados feche o bloco de script
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/").replace("<!--", "<\\!--")


def montar_site(modelo):
    corte = modelo.index('<div class="wrap">')
    cabeca, corpo = modelo[:corte], modelo[corte:]
    cabeca = cabeca.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
    cabeca = cabeca.replace("<title>QuickTrip</title>", f"<title>{TITULO_SITE}</title>")
    cabeca = cabeca.replace("<!--EXTRA_HEAD-->", HEAD_SITE)
    corpo = corpo.replace("/*INLINE*/null", "null").replace("<!--NOTA_ARTEFATO-->", "")
    corpo = corpo.replace("<!--MARCA_SITE-->", MARCA_SITE).replace("<!--VOLTAR_SITE-->", VOLTAR_SITE)
    corpo = corpo.replace("<!--RODAPE_SITE-->", RODAPE_SITE)
    return '<!doctype html>\n<html lang="pt-BR">\n<head>\n' + cabeca + "</head>\n<body>\n" + corpo + "</body>\n</html>\n"


def montar_artefato(modelo):
    texto = modelo.replace('<meta charset="utf-8">\n', "")
    texto = texto.replace('<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n', "")
    texto = texto.replace("<!--EXTRA_HEAD-->\n", "")
    dados = {"destinos": ler("destinos.json"), "eventos": ler("eventos.json"), "avaliacoes": ler("avaliacoes.json")}
    texto = texto.replace("/*INLINE*/null", json_para_script(dados))
    texto = re.sub(r"[ \t]*<!--(MARCA_SITE|VOLTAR_SITE|RODAPE_SITE)-->\n?", "", texto)
    return texto.replace("<!--NOTA_ARTEFATO-->", NOTA_ARTEFATO)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--artefato", action="store_true", help="gera também a versão de demonstração de arquivo único")
    args = ap.parse_args()
    modelo = (RAIZ / "src" / "pagina.html").read_text(encoding="utf-8")
    (PAGINA / "index.html").write_text(montar_site(modelo), encoding="utf-8")
    print("Gerado: quicktrip/index.html")
    if args.artefato:
        (RAIZ / "artefato").mkdir(exist_ok=True)
        (RAIZ / "artefato" / "escapadas.html").write_text(montar_artefato(modelo), encoding="utf-8")
        print("Gerado: quicktrip/_ferramentas/artefato/escapadas.html")


if __name__ == "__main__":
    main()
