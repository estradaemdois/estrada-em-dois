"""Conversa com o GitHub para criar e atualizar as issues de aprovação.

Usa o GITHUB_TOKEN que o próprio GitHub Actions fornece em cada execução
(não é preciso criar nenhum segredo para isso).
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request

from . import comum

CORES = {
    comum.ETQ_INSTAGRAM: ("E1306C", "Publicação do Instagram"),
    comum.ETQ_AGUARDANDO: ("F2B33D", "Esperando a sua aprovação"),
    comum.ETQ_PUBLICADO: ("2DA44E", "Já publicado no Instagram"),
    comum.ETQ_REJEITADO: ("8FA89B", "Descartado"),
    comum.ETQ_ERRO: ("D73A4A", "Falhou ao publicar"),
    comum.ETQ_ALERTA: ("D73A4A", "Aviso da automação"),
}


class GitHub:
    def __init__(self, token=None, repositorio=None):
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self.repositorio = repositorio or os.environ.get("GITHUB_REPOSITORY", "")

    def _req(self, metodo, caminho, dados=None):
        url = f"https://api.github.com/repos/{self.repositorio}/{caminho.lstrip('/')}"
        corpo = json.dumps(dados).encode() if dados is not None else None
        req = urllib.request.Request(url, data=corpo, method=metodo, headers={
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                texto = r.read().decode()
                return json.loads(texto) if texto else {}
        except urllib.error.HTTPError as e:
            if metodo == "DELETE" and e.code == 404:
                return {}
            raise

    def garantir_etiquetas(self):
        existentes = {e["name"] for e in self._req("GET", "labels?per_page=100")}
        for nome, (cor, desc) in CORES.items():
            if nome not in existentes:
                self._req("POST", "labels", {"name": nome, "color": cor, "description": desc})

    def criar_issue(self, titulo, corpo, etiquetas):
        return self._req("POST", "issues", {"title": titulo, "body": corpo, "labels": etiquetas})

    def issues_abertas(self, etiqueta):
        q = urllib.parse.quote(etiqueta)
        return [i for i in self._req("GET", f"issues?state=open&labels={q}&per_page=50")
                if "pull_request" not in i]

    def issue(self, numero):
        return self._req("GET", f"issues/{numero}")

    def comentar(self, numero, texto):
        return self._req("POST", f"issues/{numero}/comments", {"body": texto})

    def adicionar_etiquetas(self, numero, etiquetas):
        return self._req("POST", f"issues/{numero}/labels", {"labels": etiquetas})

    def remover_etiqueta(self, numero, etiqueta):
        return self._req("DELETE", f"issues/{numero}/labels/{urllib.parse.quote(etiqueta)}")

    def fechar(self, numero, motivo="completed"):
        return self._req("PATCH", f"issues/{numero}", {"state": "closed", "state_reason": motivo})

    def alertar(self, titulo, texto):
        """Abre um aviso (uma única issue aberta por título, sem repetir)."""
        for i in self.issues_abertas(comum.ETQ_ALERTA):
            if i["title"] == titulo:
                return i
        return self.criar_issue(titulo, texto, [comum.ETQ_ALERTA])
