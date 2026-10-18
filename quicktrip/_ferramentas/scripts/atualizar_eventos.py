#!/usr/bin/env python3
"""Busca eventos futuros nas cidades da base e grava em quicktrip/dados/eventos.json.

Usa a API do Claude com a ferramenta de busca na web. Cada evento só é aceito se:
  - tem nome, data de início válida e dentro da janela pedida;
  - tem uma URL que apareceu de fato nos resultados de busca daquela cidade.
Isso reduz (mas não elimina) o risco de evento inventado. Confira antes de divulgar.

Uso:
  pip install anthropic
  export ANTHROPIC_API_KEY=sua_chave
  python scripts/atualizar_eventos.py                  # todas as cidades, próximos 60 dias
  python scripts/atualizar_eventos.py --cidades olimpia,barretos --dias 90
"""
import argparse
import datetime as dt
import json
import pathlib
import sys
import time

RAIZ = pathlib.Path(__file__).resolve().parent.parent  # quicktrip/_ferramentas
DADOS_DIR = RAIZ.parent / "dados"
DESTINOS = DADOS_DIR / "destinos.json"
SAIDA_PADRAO = DADOS_DIR / "eventos.json"
MODELO_PADRAO = "claude-sonnet-5-5"
FERRAMENTA_BUSCA = "web_search_20250305"


def montar_prompt(cidade, inicio, fim):
    return (
        f"Pesquise eventos públicos que vão acontecer em {cidade}, SP, entre {inicio.isoformat()} e {fim.isoformat()}: "
        "shows, festas, festivais, feiras, exposições, rodeios, eventos esportivos e culturais.\n"
        "Regras:\n"
        "- Use só informações de páginas que você encontrou na busca. Não invente eventos, datas ou locais.\n"
        "- Ignore eventos de outras cidades com nome parecido.\n"
        "- Responda SOMENTE com um array JSON, sem texto antes ou depois.\n"
        'Cada item deve ter: "nome", "data_inicio" (AAAA-MM-DD), "data_fim" (AAAA-MM-DD ou null), '
        '"local" (texto curto ou null) e "url" (a página onde você viu o evento).\n'
        "Se não achar nenhum evento confirmado com data, responda []."
    )


def extrair_json(texto):
    """Devolve o último array JSON válido encontrado no texto, ou None."""
    decoder = json.JSONDecoder()
    achado = None
    for i, ch in enumerate(texto):
        if ch != "[":
            continue
        try:
            valor, _ = decoder.raw_decode(texto[i:])
        except ValueError:
            continue
        if isinstance(valor, list):
            achado = valor
    return achado


def normalizar_url(url):
    return str(url or "").strip().split("#")[0].rstrip("/")


def urls_dos_resultados(blocos):
    urls = set()
    for bloco in blocos:
        tipo = getattr(bloco, "type", None) or (bloco.get("type") if isinstance(bloco, dict) else None)
        if tipo != "web_search_tool_result":
            continue
        conteudo = getattr(bloco, "content", None)
        if conteudo is None and isinstance(bloco, dict):
            conteudo = bloco.get("content")
        if not isinstance(conteudo, list):
            continue  # erro da busca
        for r in conteudo:
            u = getattr(r, "url", None) or (r.get("url") if isinstance(r, dict) else None)
            if u:
                urls.add(normalizar_url(u))
    return urls


def texto_dos_blocos(blocos):
    partes = []
    for bloco in blocos:
        tipo = getattr(bloco, "type", None) or (bloco.get("type") if isinstance(bloco, dict) else None)
        if tipo == "text":
            partes.append(getattr(bloco, "text", None) or bloco.get("text", ""))
    return "\n".join(partes)


def parse_data(valor):
    try:
        return dt.date.fromisoformat(str(valor))
    except ValueError:
        return None


def validar_eventos(bruto, id_destino, urls_validas, hoje, limite):
    saida = []
    for ev in bruto or []:
        if not isinstance(ev, dict):
            continue
        nome = str(ev.get("nome") or "").strip()
        inicio = parse_data(ev.get("data_inicio"))
        fim = parse_data(ev.get("data_fim")) if ev.get("data_fim") else None
        url = normalizar_url(ev.get("url"))
        if not nome or not inicio or not url.lower().startswith(("http://", "https://")):
            continue
        if url not in urls_validas:
            continue  # URL que não apareceu na busca: descarta
        if fim and fim < inicio:
            fim = None
        if (fim or inicio) < hoje or inicio > limite:
            continue
        local = str(ev.get("local") or "").strip() or None
        saida.append({
            "id_destino": id_destino,
            "nome": nome[:140],
            "data_inicio": inicio.isoformat(),
            "data_fim": fim.isoformat() if fim else None,
            "local": local[:140] if local else None,
            "url": url,
        })
    return saida[:10]


def buscar_cidade(client, modelo, cidade, inicio, fim, max_buscas):
    ferramentas = [{
        "type": FERRAMENTA_BUSCA,
        "name": "web_search",
        "max_uses": max_buscas,
        "user_location": {"type": "approximate", "city": cidade, "region": "São Paulo", "country": "BR", "timezone": "America/Sao_Paulo"},
    }]
    mensagens = [{"role": "user", "content": montar_prompt(cidade, inicio, fim)}]
    blocos = []
    for _ in range(4):  # a API pode pausar o turno em buscas longas
        resp = client.messages.create(model=modelo, max_tokens=4000, tools=ferramentas, messages=mensagens)
        blocos.extend(resp.content)
        if getattr(resp, "stop_reason", None) != "pause_turn":
            break
        mensagens.append({"role": "assistant", "content": resp.content})
    return texto_dos_blocos(blocos), urls_dos_resultados(blocos)


def carregar_json(caminho, padrao):
    try:
        return json.loads(pathlib.Path(caminho).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def main(argv=None, client=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dias", type=int, default=60, help="janela de busca a partir de hoje (padrão 60)")
    ap.add_argument("--cidades", default="", help="ids separados por vírgula (padrão: todas)")
    ap.add_argument("--saida", default=str(SAIDA_PADRAO))
    ap.add_argument("--modelo", default=MODELO_PADRAO)
    ap.add_argument("--max-buscas", type=int, default=4, help="buscas na web por cidade")
    ap.add_argument("--pausa", type=float, default=1.0, help="segundos entre cidades")
    args = ap.parse_args(argv)

    if client is None:
        try:
            import anthropic
        except ImportError:
            sys.exit("Instale o SDK: pip install anthropic")
        client = anthropic.Anthropic()  # lê ANTHROPIC_API_KEY do ambiente

    dados = carregar_json(DESTINOS, None)
    if not dados:
        sys.exit(f"Não consegui ler {DESTINOS}")
    cidades = {d["id"]: d["nome"] for d in dados["destinos"]}
    for o in dados["origens"]:
        cidades.setdefault(o["id"], o["nome"])
    if args.cidades:
        pedidas = [c.strip() for c in args.cidades.split(",") if c.strip()]
        faltando = [c for c in pedidas if c not in cidades]
        if faltando:
            sys.exit("Ids desconhecidos: " + ", ".join(faltando))
        cidades = {c: cidades[c] for c in pedidas}

    hoje = dt.date.today()
    limite = hoje + dt.timedelta(days=args.dias)
    anterior = carregar_json(args.saida, {"eventos": []})
    eventos = {c: [e for e in anterior.get("eventos", []) if e.get("id_destino") == c] for c in cidades}

    for id_cidade, nome in cidades.items():
        print(f"{nome}... ", end="", flush=True)
        try:
            texto, urls = buscar_cidade(client, args.modelo, nome, hoje, limite, args.max_buscas)
            bruto = extrair_json(texto)
            if bruto is None:
                print("resposta sem JSON, mantendo eventos anteriores")
                continue
            novos = validar_eventos(bruto, id_cidade, urls, hoje, limite)
            eventos[id_cidade] = novos
            print(f"{len(novos)} evento(s) aceito(s) de {len(bruto)} sugerido(s)")
        except Exception as erro:  # rede, cota, etc.: não derruba as outras cidades
            print(f"falhou ({type(erro).__name__}: {erro}), mantendo eventos anteriores")
        time.sleep(args.pausa)

    # mantém eventos de cidades que não foram consultadas nesta rodada
    todos = [e for c in cidades for e in eventos[c]]
    todos += [e for e in anterior.get("eventos", []) if e.get("id_destino") not in cidades]
    todos.sort(key=lambda e: (e["data_inicio"], e["id_destino"]))
    saida = {"atualizado_em": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "eventos": todos}
    pathlib.Path(args.saida).write_text(json.dumps(saida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Gravado {args.saida} com {len(todos)} evento(s).")


if __name__ == "__main__":
    main()
