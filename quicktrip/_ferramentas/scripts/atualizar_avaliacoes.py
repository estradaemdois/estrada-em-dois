#!/usr/bin/env python3
"""Busca nota e número de avaliações dos pontos turísticos no Google Maps (Places API) e grava em
quicktrip/dados/avaliacoes.json.

Não usa bibliotecas externas. Precisa de uma chave do Google Maps Platform com a Places API (New) ativa.
A API é cobrada por requisição: confira a tabela de preços atual antes de rodar em toda a base.

Uso:
  export GOOGLE_MAPS_API_KEY=sua_chave
  python scripts/atualizar_avaliacoes.py                    # toda a base
  python scripts/atualizar_avaliacoes.py --cidades olimpia  # só uma cidade
"""
import argparse
import datetime as dt
import json
import math
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

RAIZ = pathlib.Path(__file__).resolve().parent.parent  # quicktrip/_ferramentas
DADOS_DIR = RAIZ.parent / "dados"
DESTINOS = DADOS_DIR / "destinos.json"
SAIDA_PADRAO = DADOS_DIR / "avaliacoes.json"
ENDPOINT = "https://places.googleapis.com/v1/places:searchText"
CAMPOS = "places.id,places.displayName,places.rating,places.userRatingCount,places.googleMapsUri,places.location"
RAIO_BUSCA_M = 20000
DISTANCIA_MAXIMA_KM = 30  # descarta resultado longe da cidade (homônimo em outra região)


def haversine_km(a, b, c, d):
    r = math.pi / 180
    h = math.sin((c - a) * r / 2) ** 2 + math.cos(a * r) * math.cos(c * r) * math.sin((d - b) * r / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


def buscar_lugar(chave, consulta, lat, lon, abrir=urllib.request.urlopen):
    corpo = {
        "textQuery": consulta,
        "languageCode": "pt-BR",
        "regionCode": "BR",
        "maxResultCount": 1,
        "locationBias": {"circle": {"center": {"latitude": lat, "longitude": lon}, "radius": float(RAIO_BUSCA_M)}},
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(corpo).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Goog-Api-Key": chave, "X-Goog-FieldMask": CAMPOS},
        method="POST",
    )
    with abrir(req, timeout=20) as resp:
        dados = json.loads(resp.read().decode("utf-8"))
    return (dados.get("places") or [None])[0]


def converter(lugar, lat, lon):
    """Transforma a resposta da API no formato do site, ou None se não servir."""
    if not lugar or not isinstance(lugar.get("rating"), (int, float)):
        return None
    loc = lugar.get("location") or {}
    if "latitude" in loc and "longitude" in loc:
        if haversine_km(lat, lon, loc["latitude"], loc["longitude"]) > DISTANCIA_MAXIMA_KM:
            return None
    return {
        "rating": round(float(lugar["rating"]), 1),
        "total": int(lugar.get("userRatingCount") or 0),
        "url": lugar.get("googleMapsUri"),
        "place_id": lugar.get("id"),
        "nome_google": (lugar.get("displayName") or {}).get("text"),
    }


def carregar_json(caminho, padrao):
    try:
        return json.loads(pathlib.Path(caminho).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def main(argv=None, abrir=urllib.request.urlopen):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cidades", default="", help="ids separados por vírgula (padrão: todas)")
    ap.add_argument("--saida", default=str(SAIDA_PADRAO))
    ap.add_argument("--pausa", type=float, default=0.2, help="segundos entre requisições")
    args = ap.parse_args(argv)

    chave = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not chave:
        sys.exit("Defina a variável GOOGLE_MAPS_API_KEY.")
    dados = carregar_json(DESTINOS, None)
    if not dados:
        sys.exit(f"Não consegui ler {DESTINOS}")
    destinos = dados["destinos"]
    if args.cidades:
        pedidas = {c.strip() for c in args.cidades.split(",") if c.strip()}
        destinos = [d for d in destinos if d["id"] in pedidas]
        if not destinos:
            sys.exit("Nenhuma cidade encontrada para: " + args.cidades)

    anterior = carregar_json(args.saida, {"lugares": {}})
    lugares = dict(anterior.get("lugares", {}))
    ok = falhas = 0
    for d in destinos:
        for ponto in d["pontos"]:
            chave_lugar = f'{d["id"]}|{ponto}'
            try:
                lugar = buscar_lugar(chave, f'{ponto}, {d["nome"]}, SP, Brasil', d["lat"], d["lon"], abrir)
                info = converter(lugar, d["lat"], d["lon"])
            except (urllib.error.URLError, ValueError, OSError) as erro:
                print(f'  falhou: {d["nome"]} / {ponto} ({erro})')
                falhas += 1
                continue
            if info:
                lugares[chave_lugar] = info
                ok += 1
                print(f'  {d["nome"]} / {ponto}: {info["rating"]} ({info["total"]})')
            else:
                falhas += 1
                print(f'  sem nota confiável: {d["nome"]} / {ponto}')
            time.sleep(args.pausa)

    saida = {"atualizado_em": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "lugares": lugares}
    pathlib.Path(args.saida).write_text(json.dumps(saida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Gravado {args.saida}: {ok} atualizado(s), {falhas} sem dados.")


if __name__ == "__main__":
    main()
