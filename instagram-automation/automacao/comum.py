"""Funções compartilhadas: caminhos, leitura de arquivos, data no fuso de São Paulo."""
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

PASTA_AUTOMACAO = Path(__file__).resolve().parent.parent
PASTA_REPOSITORIO = PASTA_AUTOMACAO.parent
ARQ_CONFIG = PASTA_AUTOMACAO / "config.json"
ARQ_BANCO = PASTA_AUTOMACAO / "conteudo" / "banco-de-posts.json"
ARQ_HISTORICO = PASTA_AUTOMACAO / "historico" / "historico.json"
PASTA_FILA = PASTA_AUTOMACAO / "fila"

# Etiquetas (labels) usadas nas issues de aprovação
ETQ_INSTAGRAM = "instagram"
ETQ_AGUARDANDO = "aguardando-aprovacao"
ETQ_PUBLICADO = "publicado"
ETQ_REJEITADO = "rejeitado"
ETQ_ERRO = "erro-publicacao"
ETQ_ALERTA = "alerta-instagram"


def ler_json(caminho):
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def salvar_json(caminho, dados):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
        f.write("\n")


def config():
    return ler_json(ARQ_CONFIG)


def agora_sp():
    return datetime.now(ZoneInfo(config().get("fuso_horario", "America/Sao_Paulo")))


def variavel_sim(nome):
    """Lê uma variável do repositório (ex.: INSTAGRAM_PAUSADO) e diz se ela vale 'sim'."""
    return os.environ.get(nome, "").strip().lower() in {"sim", "s", "true", "1", "yes"}


def esta_pausado():
    return variavel_sim("INSTAGRAM_PAUSADO")


def modo_teste():
    return variavel_sim("INSTAGRAM_MODO_TESTE")


def resumo(texto):
    """Escreve no resumo da execução do GitHub Actions (aparece na aba Actions)."""
    print(texto)
    arq = os.environ.get("GITHUB_STEP_SUMMARY")
    if arq:
        with open(arq, "a", encoding="utf-8") as f:
            f.write(texto + "\n")


def salvar_no_repositorio(mensagem):
    """Grava no repositório as mudanças da pasta instagram-automation (fila e histórico).

    Só mexe em arquivos dentro de instagram-automation/. Nos testes isso é desligado.
    """
    if os.environ.get("AUTOMACAO_SEM_GIT"):
        return
    def git(*args, check=True):
        return subprocess.run(["git", *args], cwd=PASTA_REPOSITORIO, check=check,
                              capture_output=True, text=True)
    git("config", "user.name", "github-actions[bot]")
    git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    git("add", "instagram-automation")
    if git("diff", "--cached", "--quiet", check=False).returncode == 0:
        return
    git("commit", "-m", mensagem)
    for _ in range(3):
        if git("push", check=False).returncode == 0:
            return
        git("pull", "--rebase", check=False)
    raise RuntimeError("Não consegui gravar as mudanças no repositório (git push falhou).")
