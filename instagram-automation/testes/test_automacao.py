"""Testes da automação. Rodam sem internet, sem token real e sem publicar nada.

A Meta e o GitHub são substituídos por "dublês" que só anotam o que foi pedido.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["AUTOMACAO_SEM_GIT"] = "1"

from automacao import comum, conteudo, decidir, formato, imagem, preparar  # noqa: E402
from automacao.instagram_api import ErroInstagram, Instagram  # noqa: E402

DONA = "estradaemdois"
TOKEN_IG = "IGAAtokenfalso123"
TOKEN_FB = "EAAtokenfalso456"


class GitHubFalso:
    def __init__(self):
        self.issues, self.comentarios, self.alertas = {}, [], []
        self.proximo = 1

    def garantir_etiquetas(self):
        pass

    def issues_abertas(self, etq):
        return [i for i in self.issues.values()
                if i["state"] == "open" and etq in {l["name"] for l in i["labels"]}]

    def criar_issue(self, titulo, corpo, etiquetas):
        n = self.proximo
        self.proximo += 1
        self.issues[n] = {"number": n, "title": titulo, "body": corpo, "state": "open",
                          "user": {"login": "github-actions[bot]"},
                          "labels": [{"name": e} for e in etiquetas]}
        return self.issues[n]

    def comentar(self, n, texto):
        self.comentarios.append((n, texto))

    def adicionar_etiquetas(self, n, etqs):
        for e in etqs:
            if e not in self.nomes(n):
                self.issues[n]["labels"].append({"name": e})

    def remover_etiqueta(self, n, etq):
        self.issues[n]["labels"] = [l for l in self.issues[n]["labels"] if l["name"] != etq]

    def fechar(self, n, motivo="completed"):
        self.issues[n]["state"] = "closed"

    def alertar(self, titulo, texto):
        self.alertas.append(titulo)

    def nomes(self, n):
        return {l["name"] for l in self.issues[n]["labels"]}


class MetaFalsa:
    """Imita a API da Meta e registra cada chamada."""
    def __init__(self, usuario="estradaemdois.oficial", falhar_publicacao=False):
        self.chamadas, self.usuario, self.falhar = [], usuario, falhar_publicacao

    def __call__(self, metodo, url, dados=None):
        self.chamadas.append((metodo, url, dados))
        if "/me/accounts" in url:
            return 200, {"data": [{"name": "Estrada em Dois", "instagram_business_account":
                                   {"id": "999", "username": self.usuario}}]}
        if "/me?" in url:
            return 200, {"user_id": "777", "username": self.usuario}
        if url.endswith("/media") and metodo == "POST":
            return 200, {"id": "container1"}
        if "container1?" in url:
            return 200, {"status_code": "FINISHED"}
        if url.endswith("/media_publish"):
            if self.falhar:
                return 400, {"error": {"code": 9004, "message": "Only photo or video can be accepted"}}
            return 200, {"id": "midia1"}
        if "midia1?" in url:
            return 200, {"permalink": "https://www.instagram.com/p/teste/"}
        return 404, {"error": {"message": "não esperado"}}

    def publicou(self):
        return any(u.endswith("/media_publish") for _, u, _ in self.chamadas)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.hist = self.tmp / "historico.json"
        self.hist.write_text('{"registros": []}')
        self.fila = self.tmp / "fila"
        self.patches = [mock.patch.object(comum, "ARQ_HISTORICO", self.hist),
                        mock.patch.object(comum, "PASTA_FILA", self.fila),
                        mock.patch.dict(os.environ, {"INSTAGRAM_ACCESS_TOKEN": "",
                                                     "INSTAGRAM_PAUSADO": "",
                                                     "INSTAGRAM_MODO_TESTE": ""})]
        for p in self.patches:
            p.start()
        self.gh = GitHubFalso()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        shutil.rmtree(self.tmp)

    def evento(self, n, texto, quem=DONA):
        return {"comment": {"body": texto, "user": {"login": quem}},
                "issue": self.gh.issues[n], "repository": {"owner": {"login": DONA}}}

    def decidir(self, n, texto, quem=DONA, meta=None):
        meta = meta or MetaFalsa()
        ig = Instagram(token=TOKEN_IG, transporte=meta, espera=0)
        r = decidir.decidir(self.evento(n, texto, quem), gh=self.gh, ig=ig,
                            verificar_url=lambda url: True)
        return r, meta


class TestBancoDePosts(unittest.TestCase):
    def test_posts_validos_e_fotos_existem(self):
        ids = set()
        for p in conteudo.banco():
            self.assertNotIn(p["id"], ids, "id repetido")
            ids.add(p["id"])
            texto, problemas = formato.legenda_final(p["legenda"], p["hashtags"])
            self.assertEqual(problemas, [], p["id"])
            self.assertTrue(imagem.melhor_original(p["imagem"]).exists())
            self.assertTrue(p["fonte"].startswith("https://estradaemdois.com.br/"))


class TestImagem(Base):
    def test_foto_vira_jpeg_no_formato_aceito(self):
        from PIL import Image
        for p in conteudo.banco():
            destino = self.fila / f"{p['id']}.jpg"
            imagem.preparar_foto(p["imagem"], destino)
            with Image.open(destino) as img:
                formato_img, tam = img.format, img.size
            self.assertEqual(formato_img, "JPEG")
            self.assertLessEqual(tam[0], 1080)
            prop = tam[0] / tam[1]
            self.assertTrue(0.79 <= prop <= 1.92, f"{p['id']}: proporção {prop:.2f}")
            self.assertLess(destino.stat().st_size, 8 * 1024 * 1024)


class TestFluxo(Base):
    def preparar(self):
        return preparar.preparar(self.gh, checar=False)

    def test_preparar_nao_publica_e_pede_aprovacao(self):
        issue = self.preparar()
        self.assertIn(comum.ETQ_AGUARDANDO, self.gh.nomes(issue["number"]))
        legenda, hashtags, dados = formato.ler_issue(issue["body"])
        self.assertTrue(legenda)
        self.assertTrue((self.fila / dados["arquivo"]).exists())
        self.assertEqual(conteudo.historico()["registros"][0]["status"], "aguardando")

    def test_so_uma_sugestao_pendente_por_vez(self):
        self.preparar()
        self.assertIsNone(self.preparar())
        self.assertEqual(len(self.gh.issues), 1)

    def test_aprovacao_da_dona_publica(self):
        n = self.preparar()["number"]
        r, meta = self.decidir(n, "/aprovar")
        self.assertEqual(r, "publicado")
        self.assertTrue(meta.publicou())
        self.assertIn(comum.ETQ_PUBLICADO, self.gh.nomes(n))
        self.assertEqual(self.gh.issues[n]["state"], "closed")
        reg = conteudo.registro_da_issue(n)
        self.assertEqual(reg["status"], "publicado")
        self.assertEqual(reg["link"], "https://www.instagram.com/p/teste/")

    def test_outra_pessoa_nao_consegue_aprovar(self):
        n = self.preparar()["number"]
        r, meta = self.decidir(n, "/aprovar", quem="visitante")
        self.assertEqual(r, "sem-permissao")
        self.assertFalse(meta.publicou())
        self.assertIn(comum.ETQ_AGUARDANDO, self.gh.nomes(n))

    def test_comentario_comum_nao_faz_nada(self):
        n = self.preparar()["number"]
        r, meta = self.decidir(n, "Que foto linda, aprovo demais!")
        self.assertEqual(r, "ignorado")
        self.assertEqual(meta.chamadas, [])

    def test_issue_que_nao_e_da_automacao_e_ignorada(self):
        n = self.gh.criar_issue("Falsa", "qualquer coisa", ["instagram"])["number"]
        self.gh.issues[n]["user"] = {"login": "visitante"}
        r, meta = self.decidir(n, "/aprovar")
        self.assertEqual(r, "ignorado")
        self.assertFalse(meta.publicou())

    def test_nao_publica_duas_vezes(self):
        n = self.preparar()["number"]
        self.decidir(n, "/aprovar")
        self.gh.issues[n]["state"] = "open"  # mesmo se alguém reabrir
        r, meta = self.decidir(n, "/aprovar")
        self.assertEqual(r, "ja-publicado")
        self.assertFalse(meta.publicou())

    def test_post_publicado_nao_volta_a_ser_sugerido(self):
        n = self.preparar()["number"]
        post1 = conteudo.registro_da_issue(n)["post_id"]
        self.decidir(n, "/aprovar")
        n2 = self.preparar()["number"]
        self.assertNotEqual(conteudo.registro_da_issue(n2)["post_id"], post1)

    def test_rejeitar_nao_publica_e_volta_para_o_fim_da_fila(self):
        n = self.preparar()["number"]
        post1 = conteudo.registro_da_issue(n)["post_id"]
        r, meta = self.decidir(n, "/rejeitar")
        self.assertEqual(r, "rejeitado")
        self.assertFalse(meta.publicou())
        self.assertEqual(self.gh.issues[n]["state"], "closed")
        n2 = self.preparar()["number"]
        self.assertNotEqual(conteudo.registro_da_issue(n2)["post_id"], post1)

    def test_outra_rejeita_e_ja_prepara_nova(self):
        n = self.preparar()["number"]
        r, _ = self.decidir(n, "/outra")
        self.assertEqual(r, "rejeitado")
        self.assertEqual(len(self.gh.issues_abertas(comum.ETQ_AGUARDANDO)), 1)

    def test_pausado_nao_prepara_nem_publica(self):
        n = self.preparar()["number"]
        with mock.patch.dict(os.environ, {"INSTAGRAM_PAUSADO": "sim"}):
            r, meta = self.decidir(n, "/aprovar")
            self.assertEqual(r, "pausado")
            self.assertFalse(meta.publicou())
            self.gh.fechar(n)
            self.assertIsNone(self.preparar())

    def test_modo_teste_nao_envia_nada(self):
        n = self.preparar()["number"]
        with mock.patch.dict(os.environ, {"INSTAGRAM_MODO_TESTE": "sim"}):
            r, meta = self.decidir(n, "/aprovar")
        self.assertEqual(r, "simulado")
        self.assertEqual(meta.chamadas, [])

    def test_legenda_editada_na_issue_e_a_publicada(self):
        n = self.preparar()["number"]
        corpo = self.gh.issues[n]["body"]
        legenda, _, _ = formato.ler_issue(corpo)
        self.gh.issues[n]["body"] = corpo.replace(legenda, "Texto que eu mesma escrevi.")
        _, meta = self.decidir(n, "/aprovar")
        enviado = next(d for m, u, d in meta.chamadas if u.endswith("/media"))
        self.assertTrue(enviado["caption"].startswith("Texto que eu mesma escrevi."))

    def test_hashtags_demais_bloqueiam(self):
        n = self.preparar()["number"]
        corpo = self.gh.issues[n]["body"]
        _, hashtags, _ = formato.ler_issue(corpo)
        self.gh.issues[n]["body"] = corpo.replace(" ".join(hashtags), " ".join(f"#t{i}" for i in range(8)))
        r, meta = self.decidir(n, "/aprovar")
        self.assertEqual(r, "invalido")
        self.assertFalse(meta.publicou())

    def test_erro_da_meta_fica_registrado_e_permite_tentar_de_novo(self):
        n = self.preparar()["number"]
        r, _ = self.decidir(n, "/aprovar", meta=MetaFalsa(falhar_publicacao=True))
        self.assertEqual(r, "erro")
        self.assertIn(comum.ETQ_ERRO, self.gh.nomes(n))
        self.assertEqual(self.gh.issues[n]["state"], "open")
        r, meta = self.decidir(n, "/aprovar")
        self.assertEqual(r, "publicado")

    def test_fechar_a_issue_conta_como_rejeicao(self):
        n = self.preparar()["number"]
        ev = {"action": "closed", "sender": {"login": DONA}, "issue": self.gh.issues[n],
              "repository": {"owner": {"login": DONA}}}
        self.assertEqual(decidir.decidir(ev, gh=self.gh), "rejeitado")


class TestInstagramAPI(unittest.TestCase):
    def test_token_do_login_instagram(self):
        meta = MetaFalsa()
        ig = Instagram(token=TOKEN_IG, transporte=meta, espera=0)
        self.assertEqual(ig.conectar()["conta_id"], "777")
        self.assertIn("graph.instagram.com", meta.chamadas[0][1])

    def test_token_do_login_facebook(self):
        meta = MetaFalsa()
        ig = Instagram(token=TOKEN_FB, transporte=meta, espera=0)
        self.assertEqual(ig.conectar()["conta_id"], "999")
        self.assertIn("graph.facebook.com", meta.chamadas[0][1])

    def test_conta_errada_bloqueia(self):
        ig = Instagram(token=TOKEN_IG, transporte=MetaFalsa(usuario="outra.conta"), espera=0)
        with self.assertRaises(ErroInstagram):
            ig.conectar()

    def test_token_nunca_aparece_em_mensagens_de_erro(self):
        def meta_vazando(metodo, url, dados=None):
            return 400, {"error": {"code": 190, "message": f"token {TOKEN_IG} expirou"}}
        ig = Instagram(token=TOKEN_IG, transporte=meta_vazando, espera=0)
        with self.assertRaises(ErroInstagram) as e:
            ig.conectar()
        self.assertNotIn(TOKEN_IG, str(e.exception))

    def test_token_vai_no_corpo_ao_publicar(self):
        meta = MetaFalsa()
        ig = Instagram(token=TOKEN_IG, transporte=meta, espera=0)
        ig.conectar()
        ig.publicar("legenda", url_imagem="https://estradaemdois.com.br/x.jpg")
        for metodo, url, dados in meta.chamadas:
            if metodo == "POST":
                self.assertNotIn(TOKEN_IG, url)


if __name__ == "__main__":
    unittest.main()
