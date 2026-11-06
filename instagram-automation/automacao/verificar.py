"""Verificação do token e da conta, sem publicar nada.

Mostra no resumo da execução (aba Actions) se o token funciona, de que tipo ele é,
qual conta ele acessa e quantas publicações ainda cabem nas últimas 24 horas.
"""
from . import comum
from .github_api import GitHub
from .instagram_api import ErroInstagram, Instagram

TIPOS = {
    "instagram": "Instagram API com login do Instagram (graph.instagram.com)",
    "facebook": "Instagram API com login do Facebook (graph.facebook.com)",
}


def verificar(gh=None, ig=None):
    ig = ig or Instagram()
    comum.resumo("## Verificação da conexão com o Instagram\n")
    comum.resumo(f"- Tipo de token detectado: {TIPOS.get(ig.tipo_do_token(), ig.tipo_do_token())}")
    try:
        info = ig.conectar()
    except ErroInstagram as e:
        comum.resumo(f"- **Falhou:** {e}")
        (gh or GitHub()).alertar("Instagram: problema com o token de acesso",
                                 f"A verificação encontrou um problema:\n\n> {e}\n\n"
                                 "Veja a seção *Renovar o token* no README da pasta `instagram-automation`.")
        return False
    usado, total = ig.limite_de_publicacao()
    comum.resumo(f"- Conta: @{info['usuario']} (ID {info['conta_id']})")
    comum.resumo(f"- Usado pela API: {TIPOS[info['tipo']]}")
    if total:
        comum.resumo(f"- Publicações pela API nas últimas 24 h: {usado} de {total}")
    comum.resumo("- **Tudo certo.** Nenhuma publicação foi feita nesta verificação.")
    return True


if __name__ == "__main__":
    import sys
    sys.exit(0 if verificar() else 1)
