"""Etapa diária: escolhe um post, prepara a foto e abre a issue de aprovação.

Nunca publica nada. Publicar só acontece em decidir.py, depois do seu /aprovar.
"""
import os
import subprocess

from . import comum, conteudo, enderecos, formato, imagem
from .github_api import GitHub
from .instagram_api import ErroInstagram, Instagram


def checar_token(gh):
    """Confere o token antes de sugerir o post. Devolve um aviso (texto) ou ''."""
    if not os.environ.get("INSTAGRAM_ACCESS_TOKEN"):
        return "> **Aviso:** o segredo `INSTAGRAM_ACCESS_TOKEN` não chegou nesta execução. A aprovação não vai conseguir publicar.\n\n"
    try:
        Instagram().conectar()
        return ""
    except ErroInstagram as e:
        gh.alertar("Instagram: problema com o token de acesso",
                   f"A verificação diária encontrou um problema:\n\n> {e}\n\n"
                   "Veja a seção *Renovar o token* no README da pasta `instagram-automation`.")
        return f"> **Aviso:** {e}\n\n"


def sha_atual():
    if os.environ.get("AUTOMACAO_SEM_GIT"):
        return "main"
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=comum.PASTA_REPOSITORIO,
                       capture_output=True, text=True)
    return r.stdout.strip() or "main"


def preparar(gh=None, checar=True):
    gh = gh or GitHub()
    if comum.esta_pausado():
        comum.resumo("Automação pausada (INSTAGRAM_PAUSADO = sim). Nada foi preparado.")
        return None
    gh.garantir_etiquetas()

    pendentes = gh.issues_abertas(comum.ETQ_AGUARDANDO)
    if pendentes:
        n = pendentes[0]["number"]
        comum.resumo(f"Já existe uma sugestão esperando aprovação (issue #{n}). Não criei outra.")
        return None

    post = conteudo.proximo_post()
    if not post:
        gh.alertar("Instagram: acabaram as sugestões do banco de posts",
                   "Todos os posts do arquivo `conteudo/banco-de-posts.json` já foram publicados. "
                   "Peça ao Claude para criar novos posts a partir dos guias e fotos do site.")
        comum.resumo("Banco de posts esgotado. Abri um aviso.")
        return None

    aviso = checar_token(gh) if checar else ""
    data = comum.agora_sp().strftime("%Y-%m-%d")
    tipo = post.get("tipo", "IMAGEM")
    if tipo == "IMAGEM":
        arquivo = f"{data}-{post['id']}.jpg"
        info = imagem.preparar_foto(post["imagem"], comum.PASTA_FILA / arquivo,
                                    comum.config()["largura_imagem"])
    else:
        arquivo, info = post["video"], {"origem": post["video"]}
    comum.salvar_no_repositorio(f"Instagram: prepara foto para {post['id']}")

    dados = {"post_id": post["id"], "arquivo": arquivo, "tipo": tipo, "data": data}
    url_previa = enderecos.url_bruta(arquivo, sha_atual()) if tipo == "IMAGEM" else post["video"]
    corpo = formato.montar_corpo(post, url_previa, dados, aviso)
    issue = gh.criar_issue(f"Instagram {data}: {post['titulo']}", corpo,
                           [comum.ETQ_INSTAGRAM, comum.ETQ_AGUARDANDO])
    conteudo.registrar(post["id"], issue["number"], conteudo.AGUARDANDO, arquivo=arquivo,
                       origem=info["origem"])
    comum.salvar_no_repositorio(f"Instagram: sugestão #{issue['number']} aguardando aprovação")
    comum.resumo(f"Sugestão criada: issue #{issue['number']} — {post['titulo']}")
    return issue


if __name__ == "__main__":
    preparar()
