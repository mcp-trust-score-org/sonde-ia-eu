import json
from datetime import datetime, timezone

import httpx

from sonde.marches import a_signaler, avis_boamp, avis_ted, collecter, fournisseurs_cites

BOAMP_ATTRIB = {
    "idweb": "26-123456", "objet": "Mise à disposition d'une solution d'intelligence artificielle générative pour les agents",
    "nomacheteur": "Région Exemple", "dateparution": "2026-11-24", "nature_categorise_libelle": "Résultat de marché",
    "donnees": json.dumps({"attribution": {"titulaire": "Mistral AI SAS"}}),
    "url_avis": "https://www.boamp.fr/pages/avis/?q=idweb:26-123456",
}
BOAMP_APPEL = {
    "idweb": "26-654321", "objet": "Accord-cadre : assistant conversationnel (IA) pour l'accueil des usagers",
    "nomacheteur": "Ville Exemple", "dateparution": "2026-11-25", "nature_categorise_libelle": "Avis de marché",
    "datelimitereponse": "2026-12-20T12:00:00+00:00", "donnees": "{}",
}
BOAMP_HORS_SUJET = {
    "idweb": "26-000001", "objet": "Travaux de voirie au lycée Claude Bernard", "nomacheteur": "Région",
    "dateparution": "2026-11-25", "nature_categorise_libelle": "Avis de marché", "donnees": "{}",
}
TED_ATTRIB = {
    "publication-number": "712345-2026", "notice-title": {"eng": "Generative AI platform for public services"},
    "buyer-name": {"deu": ["Stadt Beispiel"]}, "buyer-country": ["DEU"], "notice-type": "can-standard",
    "publication-date": "2026-11-23+01:00", "winner-name": {"deu": ["Aleph Alpha GmbH"]},
    "links": {"html": {"ENG": "https://ted.europa.eu/en/notice/-/detail/712345-2026"}},
}


def test_boamp():
    a = avis_boamp(BOAMP_ATTRIB)
    assert a["type"] == "attribution" and a["fournisseurs"] == ["Mistral AI"] and a["date"] == "2026-11-24"
    b = avis_boamp(BOAMP_APPEL)
    assert b["type"] == "appel_offres" and b["date_limite"] == "2026-12-20" and b["fournisseurs"] == []
    assert avis_boamp(BOAMP_HORS_SUJET) is None          # « Claude » d'un nom de lycée n'est pas Anthropic


def test_ted():
    a = avis_ted(TED_ATTRIB)
    assert a["type"] == "attribution" and a["fournisseurs"] == ["Aleph Alpha"]
    assert a["acheteur"] == "Stadt Beispiel" and a["url"].endswith("712345-2026") and a["date"] == "2026-11-23"


def test_noms_de_personnes():
    assert fournisseurs_cites("Lycée Claude Monet, avenue du Mistral") == []
    assert fournisseurs_cites("accès à Claude Sonnet via Amazon Bedrock") == ["Anthropic", "Amazon (AWS)"]


def test_collecter_et_signaler(tmp_path):
    def repondre(req: httpx.Request):
        if "boamp" in req.url.host:
            return httpx.Response(200, json={"results": [BOAMP_ATTRIB, BOAMP_APPEL, BOAMP_HORS_SUJET]})
        return httpx.Response(503)                         # TED en panne : le reste continue
    client = httpx.Client(transport=httpx.MockTransport(repondre))
    res = collecter(tmp_path, client, datetime(2026, 11, 26, 6, tzinfo=timezone.utc))
    assert res["sources"]["BOAMP"] == {"etat": "ok", "nombre": 2} and res["sources"]["TED"]["etat"] == "erreur"
    liste = a_signaler(tmp_path, set())
    assert [a["id"] for a in liste] == ["boamp:26-123456", "boamp:26-654321"]   # l'attribution d'abord
    assert a_signaler(tmp_path, {"boamp:26-123456", "boamp:26-654321"}) == []   # jamais deux fois


def test_client_par_defaut_sans_reseau(tmp_path, monkeypatch):
    """Le client créé par collecter() doit pouvoir partir : en-têtes en ASCII (bug du 27/11)."""
    from sonde import marches
    assert marches.AGENT.isascii()
    vrai_client = httpx.Client
    def client(**kw):
        return vrai_client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"results": [], "notices": []})), **kw)
    monkeypatch.setattr(marches.httpx, "Client", client)
    res = collecter(tmp_path, maintenant=datetime(2026, 11, 27, 6, tzinfo=timezone.utc))
    assert res["sources"]["BOAMP"]["etat"] == "ok" and (tmp_path / "public" / "marches.json").exists()
