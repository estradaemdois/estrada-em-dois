"""Integração com a API oficial da Meta para publicar no Instagram.

Funciona com os dois tipos de token que a Meta emite:

* "Instagram API com login do Instagram" (token começa com IGAA / IG):
  chamadas em graph.instagram.com.
* "Instagram API com login do Facebook" (token começa com EAA):
  chamadas em graph.facebook.com, achando a conta do Instagram pela Página.

O token nunca é impresso. Qualquer mensagem de erro passa por `_limpar`, que
apaga o token do texto antes de mostrar.
"""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from . import comum


class ErroInstagram(Exception):
    pass


def _transporte_padrao(metodo, url, dados=None):
    corpo = urllib.parse.urlencode(dados).encode() if dados is not None else None
    req = urllib.request.Request(url, data=corpo, method=metodo)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except ValueError:
            return e.code, {}


class Instagram:
    def __init__(self, token=None, transporte=None, versao=None, usuario=None, espera=5):
        self.token = token if token is not None else os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")
        self.transporte = transporte or _transporte_padrao
        cfg = comum.config()
        self.versao = versao or os.environ.get("INSTAGRAM_VERSAO_API") or cfg["versao_api"]
        self.usuario_esperado = (usuario or cfg["usuario_instagram"]).lower()
        self.espera = espera
        self.tipo = None          # "instagram" ou "facebook"
        self.conta_id = None
        self.usuario = None

    # ---------- utilidades ----------
    def _limpar(self, texto):
        texto = str(texto)
        return texto.replace(self.token, "***") if self.token else texto

    def _base(self):
        host = "graph.instagram.com" if self.tipo == "instagram" else "graph.facebook.com"
        return f"https://{host}/{self.versao}"

    def _chamar(self, metodo, caminho, params=None):
        params = dict(params or {})
        params["access_token"] = self.token
        url = f"{self._base()}/{caminho.lstrip('/')}"
        if metodo == "GET":
            status, resposta = self.transporte("GET", url + "?" + urllib.parse.urlencode(params))
        else:
            status, resposta = self.transporte("POST", url, params)
        if status >= 400 or "error" in resposta:
            erro = resposta.get("error", {})
            msg = erro.get("message", f"HTTP {status}")
            codigo = erro.get("code", "")
            raise ErroInstagram(self._limpar(f"A Meta recusou o pedido ({codigo}): {msg}"))
        return resposta

    # ---------- token e conta ----------
    def tipo_do_token(self):
        if not self.token:
            return "ausente"
        if self.token.startswith("IG"):
            return "instagram"
        if self.token.startswith("EAA"):
            return "facebook"
        return "desconhecido"

    def conectar(self):
        """Descobre o tipo de token, valida e encontra o ID da conta do Instagram.

        Tenta, nesta ordem: login do Instagram (graph.instagram.com), Páginas do
        Facebook (me/accounts) e, por fim, as contas do Instagram que o próprio
        token autorizou (debug_token). Esse último caminho funciona com tokens do
        "login unificado", que não trazem permissões de Página.
        """
        tipo = self.tipo_do_token()
        if tipo == "ausente":
            raise ErroInstagram("O segredo INSTAGRAM_ACCESS_TOKEN não está disponível nesta execução.")
        ordem = ["instagram", "facebook"] if tipo != "facebook" else ["facebook", "instagram"]
        detalhes = []
        for t in ordem:
            self.tipo = t
            try:
                if t == "instagram":
                    r = self._chamar("GET", "me", {"fields": "user_id,username"})
                    self.conta_id = str(r.get("user_id") or r.get("id"))
                    self.usuario = r.get("username", "")
                else:
                    self._conectar_pelo_facebook()
                break
            except ErroInstagram as e:
                detalhes.append(str(e))
        else:
            raise ErroInstagram("Não consegui encontrar a conta do Instagram com este token. "
                                "Detalhes: " + " | ".join(detalhes))
        if self.usuario.lower() != self.usuario_esperado:
            raise ErroInstagram(
                f"O token pertence à conta @{self.usuario}, mas a automação espera "
                f"@{self.usuario_esperado}. Nada será publicado.")
        return {"tipo": self.tipo, "usuario": self.usuario, "conta_id": self.conta_id}

    def _conectar_pelo_facebook(self):
        candidatos = []
        id_fixo = os.environ.get("INSTAGRAM_USER_ID", "").strip()
        if id_fixo:
            candidatos.append(id_fixo)
        try:
            r = self._chamar("GET", "me/accounts",
                             {"fields": "name,instagram_business_account{id,username}"})
            for pagina in r.get("data", []):
                conta = pagina.get("instagram_business_account") or {}
                if conta.get("id"):
                    candidatos.append(conta["id"])
        except ErroInstagram:
            pass
        try:
            r = self._chamar("GET", "debug_token", {"input_token": self.token})
            for escopo in (r.get("data") or {}).get("granular_scopes", []):
                if escopo.get("scope", "").startswith("instagram_"):
                    candidatos.extend(escopo.get("target_ids") or [])
        except ErroInstagram:
            pass
        vistos = []
        for cid in dict.fromkeys(str(c) for c in candidatos):
            try:
                usuario = self._chamar("GET", cid, {"fields": "username"}).get("username", "")
            except ErroInstagram:
                continue
            vistos.append(usuario)
            if usuario.lower() == self.usuario_esperado:
                self.conta_id, self.usuario = cid, usuario
                return
        raise ErroInstagram(
            "o token do tipo Facebook foi aceito, mas não dá acesso à conta "
            f"@{self.usuario_esperado} (contas encontradas: {vistos or 'nenhuma'}). "
            "Ao gerar o token, marque a conta do Instagram do Estrada em Dois na janela de autorização")

    def limite_de_publicacao(self):
        try:
            r = self._chamar("GET", f"{self.conta_id}/content_publishing_limit",
                             {"fields": "quota_usage,config"})
            dados = (r.get("data") or [{}])[0]
            return dados.get("quota_usage"), (dados.get("config") or {}).get("quota_total")
        except ErroInstagram:
            return None, None

    # ---------- publicação ----------
    def publicar(self, legenda, url_imagem=None, url_video=None):
        """Publica de verdade. Só é chamado depois da aprovação."""
        if not self.conta_id:
            self.conectar()
        params = {"caption": legenda}
        if url_video:
            params.update({"media_type": "REELS", "video_url": url_video})
        else:
            params["image_url"] = url_imagem
        criacao = self._chamar("POST", f"{self.conta_id}/media", params)["id"]
        self._aguardar_processamento(criacao, video=bool(url_video))
        midia = self._chamar("POST", f"{self.conta_id}/media_publish", {"creation_id": criacao})["id"]
        link = ""
        try:
            link = self._chamar("GET", midia, {"fields": "permalink"}).get("permalink", "")
        except ErroInstagram:
            pass
        return {"media_id": midia, "permalink": link}

    def _aguardar_processamento(self, criacao, video):
        tentativas = 60 if video else 12
        for _ in range(tentativas):
            status = self._chamar("GET", criacao, {"fields": "status_code"}).get("status_code")
            if status in (None, "FINISHED"):
                return
            if status in ("ERROR", "EXPIRED"):
                raise ErroInstagram(f"A Meta não conseguiu processar a mídia (status {status}). "
                                    "Confira se o arquivo está acessível publicamente.")
            time.sleep(self.espera)
        raise ErroInstagram("A Meta demorou demais para processar a mídia. Tente aprovar de novo.")
