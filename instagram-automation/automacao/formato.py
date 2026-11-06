"""Monta o texto da issue de aprovação e lê de volta a legenda (inclusive se você editar)."""
import json
import re

from . import comum

LEG_INI, LEG_FIM = "<!-- legenda:inicio -->", "<!-- legenda:fim -->"
HAS_INI, HAS_FIM = "<!-- hashtags:inicio -->", "<!-- hashtags:fim -->"
DADOS = re.compile(r"<!-- dados: (\{.*?\}) -->", re.S)


def bloco(ini, fim, texto):
    return f"{ini}\n```text\n{texto.strip()}\n```\n{fim}"


def montar_corpo(post, url_previa, dados, aviso=""):
    hashtags = " ".join(post["hashtags"])
    fonte = f"\n**Baseado em:** {post['fonte']}" if post.get("fonte") else ""
    previa = (f"![Prévia]({url_previa})" if post.get("tipo", "IMAGEM") == "IMAGEM"
              else f"[Abrir o vídeo]({url_previa})")
    return f"""{aviso}## Prévia

{previa}

**Post:** {post['titulo']}{fonte}

## Legenda

{bloco(LEG_INI, LEG_FIM, post['legenda'])}

## Hashtags

{bloco(HAS_INI, HAS_FIM, hashtags)}

## Como decidir

Responda nesta página com um comentário:

- `/aprovar` — publica agora no Instagram
- `/rejeitar` — descarta esta sugestão
- `/outra` — descarta e prepara outra sugestão na hora

Quer mudar a legenda ou as hashtags? Edite este texto (menu **···** › **Editar**) e depois comente `/aprovar`. O que estiver escrito aqui no momento da aprovação é o que vai para o Instagram.

<!-- dados: {json.dumps(dados, ensure_ascii=False)} -->
"""


def _entre(corpo, ini, fim):
    m = re.search(re.escape(ini) + r"(.*?)" + re.escape(fim), corpo, re.S)
    if not m:
        return None
    texto = m.group(1).strip()
    texto = re.sub(r"^```[a-z]*\s*\n?", "", texto)
    texto = re.sub(r"\n?```\s*$", "", texto)
    return texto.strip().replace("\r\n", "\n")


def ler_issue(corpo):
    corpo = corpo or ""
    legenda = _entre(corpo, LEG_INI, LEG_FIM)
    hashtags = _entre(corpo, HAS_INI, HAS_FIM)
    m = DADOS.search(corpo)
    if legenda is None or hashtags is None or not m:
        raise ValueError("Não consegui ler a legenda/hashtags. As marcações da issue foram apagadas na edição.")
    return legenda, hashtags.split(), json.loads(m.group(1))


def legenda_final(legenda, hashtags):
    """Valida e junta legenda + hashtags. Devolve (texto, lista_de_problemas)."""
    cfg = comum.config()
    problemas = []
    invalidas = [h for h in hashtags if not re.fullmatch(r"#[\wÀ-ÿ]+", h)]
    if invalidas:
        problemas.append(f"hashtags com formato inválido: {' '.join(invalidas)}")
    if len(hashtags) > cfg["max_hashtags"]:
        problemas.append(f"{len(hashtags)} hashtags (o limite configurado é {cfg['max_hashtags']})")
    texto = legenda.strip() + ("\n\n" + " ".join(hashtags) if hashtags else "")
    if len(texto) > cfg["max_caracteres_legenda"]:
        problemas.append(f"legenda com {len(texto)} caracteres (máximo {cfg['max_caracteres_legenda']})")
    if not legenda.strip():
        problemas.append("legenda vazia")
    return texto, problemas
