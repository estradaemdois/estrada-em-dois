"""Banco de posts, histórico e escolha do próximo post (sem repetir)."""
from . import comum

PUBLICADO, AGUARDANDO, REJEITADO, ERRO = "publicado", "aguardando", "rejeitado", "erro"


def banco():
    return comum.ler_json(comum.ARQ_BANCO)["posts"]


def historico():
    return comum.ler_json(comum.ARQ_HISTORICO)


def salvar_historico(h):
    comum.salvar_json(comum.ARQ_HISTORICO, h)


def registrar(post_id, issue, status, **extra):
    h = historico()
    agora = comum.agora_sp().isoformat(timespec="seconds")
    for r in h["registros"]:
        if r["issue"] == issue:
            r.update({"status": status, "atualizado_em": agora, **extra})
            break
    else:
        h["registros"].append({"post_id": post_id, "issue": issue, "status": status,
                               "criado_em": agora, "atualizado_em": agora, **extra})
    salvar_historico(h)


def registro_da_issue(issue):
    return next((r for r in historico()["registros"] if r["issue"] == issue), None)


def ja_publicado(post_id):
    return any(r["post_id"] == post_id and r["status"] == PUBLICADO
               for r in historico()["registros"])


def proximo_post():
    """Ordem: primeiro os nunca usados (na ordem do banco); depois os rejeitados há mais tempo.

    Publicados e os que estão aguardando aprovação nunca voltam.
    """
    registros = historico()["registros"]
    bloqueados = {r["post_id"] for r in registros if r["status"] in (PUBLICADO, AGUARDANDO)}
    usados = {r["post_id"] for r in registros}
    disponiveis = [p for p in banco() if p.get("ativo", True) and p["id"] not in bloqueados]
    novos = [p for p in disponiveis if p["id"] not in usados]
    if novos:
        return novos[0]
    def ultima_rejeicao(p):
        datas = [r["atualizado_em"] for r in registros if r["post_id"] == p["id"]]
        return max(datas) if datas else ""
    return min(disponiveis, key=ultima_rejeicao) if disponiveis else None
