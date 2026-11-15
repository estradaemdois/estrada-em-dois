#!/usr/bin/env python3
"""Gera a página do QuickTrip a partir de src/pagina.html e dos JSON em quicktrip/dados.

  quicktrip/index.html          versão do site: topo, menu, busca e rodapé do Estrada em Dois (copiados da
                                página inicial, com links a partir da raiz), mapa real (Leaflet + OpenStreetMap),
                                lê dados/*.json
  _ferramentas/artefato/        (só com --artefato) prévia de arquivo único: dados e estilos embutidos,
                                mapa esquemático em SVG e fotos locais em fotos/<id>.jpg

Uso, a partir de qualquer pasta:  python3 quicktrip/_ferramentas/build.py [--artefato]
"""
import argparse
import json
import pathlib
import re

RAIZ = pathlib.Path(__file__).resolve().parent  # quicktrip/_ferramentas
PAGINA = RAIZ.parent  # quicktrip
SITE_RAIZ = PAGINA.parent  # raiz do repositório
DADOS = PAGINA / "dados"

SITE = "https://estradaemdois.com.br"
TITULO_SITE = "QuickTrip | Viagens de fim de semana por Estrada em Dois"
DESCRICAO = (
    "Escolha de onde você sai e até onde topa dirigir. O QuickTrip mostra destinos de fim de semana "
    "dentro do raio, com pontos turísticos, eventos, hospedagem, custo de combustível e rota, "
    "e sorteia um destino para você."
)
V = "20261115"

# hashes SRI conferidos contra o pacote npm leaflet@1.9.4
LEAFLET = (
    '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" '
    'integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="">\n'
    '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" '
    'integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>'
)

HEAD_SITE = f"""<meta name="description" content="{DESCRICAO}">
<meta name="theme-color" content="#17302A">
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
<link rel="stylesheet" href="/assets/novo.css?v={V}">
{LEAFLET}"""

NOTA_ARTEFATO = (
    "<p><strong>Prévia:</strong> o mapa aparece em versão esquemática e as fotos vêm embutidas. "
    "No site, o mapa é o real (OpenStreetMap).</p>"
)


def ler(nome):
    return json.loads((DADOS / nome).read_text(encoding="utf-8"))


def json_para_script(obj):
    # evita que "</script>" ou "<!--" dentro dos dados feche o bloco de script
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/").replace("<!--", "<\\!--")


def absolutizar(html):
    """Links relativos da página inicial passam a partir da raiz do site (a página fica em /quicktrip/)."""
    def troca(m):
        attr, url = m.group(1), m.group(2)
        if re.match(r"^(https?:|mailto:|tel:|#|/)", url):
            return m.group(0)
        if url in ("./", ""):
            url = ""
        return f'{attr}="/{url}"'
    return re.sub(r'\b(href|src)="([^"]*)"', troca, html)


def pecas_do_site():
    """Topo (pular, cabeçalho, menu do celular e busca) e rodapé, iguais aos da página inicial."""
    idx = (SITE_RAIZ / "index.html").read_text(encoding="utf-8")
    i = idx.index("<body>") + len("<body>")
    j = idx.index("<main", i)
    topo = absolutizar(idx[i:j].strip())
    topo = topo.replace('href="/quicktrip/">Fim de semana', 'href="/quicktrip/" aria-current="page">Fim de semana')
    a = idx.index('<footer class="nv-rodape">')
    b = idx.index("</footer>", a) + len("</footer>")
    rodape = absolutizar(idx[a:b])
    return topo, rodape


def montar_site(modelo):
    topo, rodape = pecas_do_site()
    t = modelo.replace("<title>QuickTrip</title>", f"<title>{TITULO_SITE}</title>")
    t = t.replace("<!--EXTRA_HEAD-->", HEAD_SITE)
    t = t.replace("<!--TOPO_SITE-->", topo).replace("<!--RODAPE_SITE-->", rodape + f'\n<script src="/assets/site.js?v={V}" defer></script>')
    t = t.replace("/*INLINE*/null", "null").replace("<!--NOTA_ARTEFATO-->", "")
    fim_estilo = t.index("</style>") + len("</style>")
    return '<!doctype html>\n<html lang="pt-BR">\n<head>\n' + t[:fim_estilo] + "\n</head>\n<body>\n" + t[fim_estilo:].lstrip() + "</body>\n</html>\n"


def montar_artefato(modelo):
    topo, rodape = pecas_do_site()
    # imagens do topo/rodapé ficam junto da prévia
    topo = topo.replace('src="/assets/', 'src="img/')
    rodape = rodape.replace('src="/assets/', 'src="img/')
    novo_css = (SITE_RAIZ / "assets" / "novo.css").read_text(encoding="utf-8")
    js_site = (SITE_RAIZ / "assets" / "site.js").read_text(encoding="utf-8")
    texto = modelo.replace('<meta charset="utf-8">\n', "")
    texto = texto.replace('<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n', "")
    texto = texto.replace("<!--EXTRA_HEAD-->\n", "<style>\n" + novo_css + "\n</style>\n")
    dados = {"destinos": ler("destinos.json"), "eventos": ler("eventos.json"), "avaliacoes": ler("avaliacoes.json")}
    texto = texto.replace("/*INLINE*/null", json_para_script(dados)).replace("/*FOTO_LOCAL*/false", "true")
    texto = texto.replace("<!--TOPO_SITE-->", topo).replace("<!--RODAPE_SITE-->", rodape + "\n<script>\n" + js_site + "\n</script>")
    return texto.replace("<!--NOTA_ARTEFATO-->", NOTA_ARTEFATO)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--artefato", action="store_true", help="gera também a prévia de arquivo único")
    args = ap.parse_args()
    modelo = (RAIZ / "src" / "pagina.html").read_text(encoding="utf-8")
    (PAGINA / "index.html").write_text(montar_site(modelo), encoding="utf-8")
    print("Gerado: quicktrip/index.html")
    if args.artefato:
        (RAIZ / "artefato").mkdir(exist_ok=True)
        (RAIZ / "artefato" / "index.html").write_text(montar_artefato(modelo), encoding="utf-8")
        print("Gerado: quicktrip/_ferramentas/artefato/index.html")


if __name__ == "__main__":
    main()
