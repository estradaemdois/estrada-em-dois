"""Reage aos seus comentários na issue: /aprovar, /rejeitar ou /outra.

Regras de segurança (todas precisam valer para publicar):
1. O comentário foi feito pela dona do repositório.
2. A issue foi criada pela própria automação e tem a etiqueta "instagram".
3. A issue ainda está aguardando (não foi publicada nem rejeitada antes).
4. A automação não está pausada.
"""
import json
import os

from . import comum, conteudo, enderecos, formato, preparar
from .github_api import GitHub
from .instagram_api import ErroInstagram, Instagram

APROVAR = {"/aprovar", "aprovar", "aprovado", "/aprovado"}
REJEITAR = {"/rejeitar", "rejeitar", "rejeitado", "/rejeitado"}
OUTRA = {"/outra", "outra"}
AUTOR_AUTOMACAO = "github-actions[bot]"


def ler_evento():
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as f:
        return json.load(f)


def interpretar(evento):
    """Devolve (acao, quem, issue) ou (None, ...) se o evento não for um pedido."""
    issue = evento.get("issue") or {}
    if "comment" in evento:
        primeira = (evento["comment"].get("body") or "").strip().splitlines()[:1]
        palavra = primeira[0].strip().lower() if primeira else ""
        quem = evento["comment"]["user"]["login"]
        acao = ("aprovar" if palavra in APROVAR else "rejeitar" if palavra in REJEITAR
                else "outra" if palavra in OUTRA else None)
        return acao, quem, issue
    if evento.get("action") == "closed":
        return "fechada", (evento.get("sender") or {}).get("login", ""), issue
    return None, "", issue


def decidir(evento, gh=None, ig=None, verificar_url=enderecos.acessivel):
    gh = gh or GitHub()
    acao, quem, issue = interpretar(evento)
    if not acao:
        return "ignorado"
    numero = issue["number"]
    etiquetas = {e["name"] for e in issue.get("labels", [])}
    dona = evento["repository"]["owner"]["login"]

    if comum.ETQ_INSTAGRAM not in etiquetas or issue.get("user", {}).get("login") != AUTOR_AUTOMACAO:
        return "ignorado"  # não é uma issue da automação
    if quem.lower() != dona.lower():
        if acao != "fechada":
            gh.comentar(numero, f"@{quem}, só @{dona} pode aprovar ou rejeitar publicações. Nada foi feito.")
        return "sem-permissao"
    if comum.ETQ_PUBLICADO in etiquetas:
        if acao != "fechada":
            gh.comentar(numero, "Esta publicação já foi feita. Não vou publicar de novo.")
        return "ja-publicado"
    if comum.ETQ_REJEITADO in etiquetas and acao != "aprovar":
        return "ja-rejeitado"

    try:
        legenda, hashtags, dados = formato.ler_issue(issue.get("body"))
    except ValueError as e:
        gh.comentar(numero, f"Não consegui continuar: {e}")
        return "erro-leitura"

    if acao in ("rejeitar", "outra", "fechada"):
        conteudo.registrar(dados["post_id"], numero, conteudo.REJEITADO)
        gh.adicionar_etiquetas(numero, [comum.ETQ_REJEITADO])
        gh.remover_etiqueta(numero, comum.ETQ_AGUARDANDO)
        if acao != "fechada":
            gh.comentar(numero, "Ok, descartei esta sugestão. Ela volta para o fim da fila e pode aparecer de novo no futuro.")
            gh.fechar(numero, "not_planned")
        comum.salvar_no_repositorio(f"Instagram: sugestão #{numero} rejeitada")
        if acao == "outra":
            nova = preparar.preparar(gh)
            if nova:
                gh.comentar(numero, f"Nova sugestão: #{nova['number']}")
        return "rejeitado"

    # ---- aprovar ----
    if issue.get("state") != "open":
        gh.comentar(numero, "Esta issue está fechada. Reabra a issue antes de aprovar.")
        return "fechada"
    if comum.esta_pausado():
        gh.comentar(numero, "A automação está pausada (INSTAGRAM_PAUSADO = sim). Nada foi publicado.")
        return "pausado"
    if conteudo.ja_publicado(dados["post_id"]):
        gh.comentar(numero, "Este conteúdo já foi publicado antes (está no histórico). Não vou repetir.")
        return "duplicado"
    texto, problemas = formato.legenda_final(legenda, hashtags)
    if problemas:
        gh.comentar(numero, "Não publiquei porque encontrei: " + "; ".join(problemas) +
                    ". Edite a issue e comente `/aprovar` de novo.")
        return "invalido"

    if comum.modo_teste():
        gh.comentar(numero, "**Modo de teste ligado** (INSTAGRAM_MODO_TESTE = sim): tudo foi conferido, "
                    "mas nada foi enviado ao Instagram.\n\nTexto que seria publicado:\n\n```text\n"
                    + texto + "\n```")
        return "simulado"

    try:
        ig = ig or Instagram()
        ig.conectar()
        url = enderecos.url_para_meta(dados["arquivo"], verificar_url) if dados["tipo"] == "IMAGEM" else None
        resultado = ig.publicar(texto, url_imagem=url,
                                url_video=dados["arquivo"] if dados["tipo"] != "IMAGEM" else None)
    except (ErroInstagram, RuntimeError) as e:
        conteudo.registrar(dados["post_id"], numero, conteudo.ERRO, erro=str(e))
        gh.adicionar_etiquetas(numero, [comum.ETQ_ERRO])
        gh.comentar(numero, f"Não consegui publicar.\n\n> {e}\n\nNada foi para o Instagram. "
                    "Depois de resolver, comente `/aprovar` de novo.")
        comum.salvar_no_repositorio(f"Instagram: erro ao publicar #{numero}")
        return "erro"

    # Marca como publicado ANTES de qualquer outra coisa, para nunca repetir.
    gh.adicionar_etiquetas(numero, [comum.ETQ_PUBLICADO])
    gh.remover_etiqueta(numero, comum.ETQ_AGUARDANDO)
    gh.remover_etiqueta(numero, comum.ETQ_ERRO)
    gh.remover_etiqueta(numero, comum.ETQ_REJEITADO)
    conteudo.registrar(dados["post_id"], numero, conteudo.PUBLICADO,
                       media_id=resultado["media_id"], link=resultado["permalink"],
                       aprovado_por=quem)
    link = resultado["permalink"] or "(a Meta não devolveu o link)"
    gh.comentar(numero, f"Publicado no Instagram: {link}")
    gh.fechar(numero)
    comum.salvar_no_repositorio(f"Instagram: publicado #{numero}")
    return "publicado"


if __name__ == "__main__":
    comum.resumo(f"Resultado: {decidir(ler_evento())}")
