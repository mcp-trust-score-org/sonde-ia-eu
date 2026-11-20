"""Actualités (sources simulées, sans réseau) et croisement avec des mesures réelles."""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import httpx

from sonde.actualites import produire_actualites
from sonde.croisement import croiser
from sonde.mesure import RACINE, charger_yaml

MAINTENANT = datetime(2026, 11, 20, 18, 0, tzinfo=timezone.utc)

CLOUDFLARE = {"incidents": [
    {"id": "abc", "name": "Elevated errors on API Gateway", "created_at": "2026-11-20T09:00:00Z",
     "resolved_at": "2026-11-20T10:00:00Z", "impact": "major", "shortlink": "https://stspg.io/abc", "components": []},
    {"id": "vieux", "name": "Ancien incident", "created_at": "2026-10-01T09:00:00Z", "resolved_at": None,
     "impact": "minor", "components": []},
]}
GITHUB = {"incidents": [
    {"id": "gh1", "name": "Incident with Actions", "created_at": "2026-11-20T12:00:00Z",
     "resolved_at": "2026-11-20T13:00:00Z", "impact": "minor", "components": [{"name": "Actions"}]},
    {"id": "gh2", "name": "Incident with Pages", "created_at": "2026-11-20T12:00:00Z", "components": [{"name": "Pages"}]},
]}
METEOALARM = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:cap="urn:oasis:names:tc:emergency:cap:1.2">
  <entry><title>Orange wind warning</title><link href="https://meteoalarm.org/x"/>
    <cap:areaDesc>Nord</cap:areaDesc><cap:event>Vent violent</cap:event><cap:severity>Severe</cap:severity>
    <cap:onset>2026-11-20T15:00:00+00:00</cap:onset><cap:expires>2026-11-21T03:00:00+00:00</cap:expires></entry>
  <entry><title>Yellow rain</title>
    <cap:areaDesc>Paris</cap:areaDesc><cap:event>Pluie</cap:event><cap:severity>Moderate</cap:severity>
    <cap:onset>2026-11-20T15:00:00+00:00</cap:onset><cap:expires>2026-11-21T03:00:00+00:00</cap:expires></entry>
  <entry><title>Red storm elsewhere</title>
    <cap:areaDesc>Finistere</cap:areaDesc><cap:event>Tempete</cap:event><cap:severity>Extreme</cap:severity>
    <cap:onset>2026-11-20T15:00:00+00:00</cap:onset><cap:expires>2026-11-21T03:00:00+00:00</cap:expires></entry>
</feed>"""
CERT = b"""<?xml version="1.0"?><rss version="2.0"><channel>
  <item><title>Vulnerabilite dans Cloudflare WARP</title><link>https://cert.cyber.gouv.fr/avis/1</link>
    <pubDate>Thu, 20 Nov 2026 08:00:00 +0000</pubDate><description>...</description></item>
  <item><title>Multiples vulnerabilites dans un autre produit</title><link>https://cert.cyber.gouv.fr/avis/2</link>
    <pubDate>Thu, 20 Nov 2026 08:00:00 +0000</pubDate></item>
</channel></rss>"""
GDELT = {
    "ovhcloud": {"articles": [
        {"url": "https://www.lemagit.fr/a1", "title": "Panne chez OVHcloud : des clients privés de services",
         "seendate": "20261120T093000Z", "domain": "lemagit.fr", "language": "French", "sourcecountry": "France"},
        {"url": "https://www.zdnet.fr/a2", "title": "OVHcloud : une panne prive des clients de leurs services",
         "seendate": "20261120T110000Z", "domain": "zdnet.fr", "language": "French", "sourcecountry": "France"},
        {"url": "https://www.zdnet.fr/a2bis", "title": "OVHcloud : la panne prive des clients de services",
         "seendate": "20261120T113000Z", "domain": "zdnet.fr", "language": "French", "sourcecountry": "France"},
        {"url": "https://bourse.example/a3", "title": "Action OVH : le titre chute après la panne",
         "seendate": "20261120T120000Z", "domain": "bourse.example", "language": "French", "sourcecountry": "France"},
        {"url": "https://x.example/a4", "title": "OVHcloud annonce un nouveau datacenter",
         "seendate": "20261120T120000Z", "domain": "x.example", "language": "French", "sourcecountry": "France"},
        {"url": "https://x.example/a5", "title": "Les pannes du cloud en 2026",
         "seendate": "20261120T120000Z", "domain": "x.example", "language": "French", "sourcecountry": "France"},
    ]},
    "cloudflare": {"articles": [
        {"url": "https://www.theregister.com/c1", "title": "Cloudflare outage knocks sites offline",
         "seendate": "20261120T090000Z", "domain": "theregister.com", "language": "English", "sourcecountry": "UK"},
    ]},
}


appels_gdelt: list = []


def _client():
    appels_gdelt.clear()

    def repondre(req: httpx.Request) -> httpx.Response:
        u = str(req.url)
        if "cloudflarestatus" in u:
            return httpx.Response(200, json=CLOUDFLARE)
        if "githubstatus" in u:
            return httpx.Response(200, json=GITHUB)
        if "meteoalarm-legacy-atom-france" in u:
            return httpx.Response(200, content=METEOALARM)
        if "meteoalarm" in u:
            return httpx.Response(503)
        if "cert.cyber.gouv.fr" in u:
            return httpx.Response(200, content=CERT)
        if "gdeltproject" in u:
            appels_gdelt.append(req.url.params["query"])
            if len(appels_gdelt) == 1:   # GDELT refuse souvent le premier appel
                return httpx.Response(429, text="Please limit requests to one every 5 seconds")
            return httpx.Response(200, json={"articles": GDELT["ovhcloud"]["articles"] + GDELT["cloudflare"]["articles"]})
        return httpx.Response(404)
    return httpx.Client(transport=httpx.MockTransport(repondre))


def _racine(tmp_path: Path) -> Path:
    (tmp_path / "dossiers").mkdir()
    (tmp_path / "dossiers" / "mistral.json").write_text(json.dumps({"reseau": {"intermediaires": ["Cloudflare"]}}))
    (tmp_path / "dossiers" / "ovhcloud.json").write_text(json.dumps({"reseau": {"intermediaires": []}}))
    return tmp_path


def test_actualites_sources_simulees(tmp_path):
    conf = charger_yaml(RACINE / "config" / "actualites.yaml")
    res = produire_actualites(conf, _racine(tmp_path), client=_client(), env={}, maintenant=MAINTENANT,
                              attendre=lambda s: None)
    par_id = {e["id"]: e for e in res["evenements"]}

    # Cloudflare : relié à Mistral par le chemin réseau ; l'incident trop ancien est ignoré.
    assert par_id["cloudflare-abc"]["fournisseurs"] == ["mistral"]
    assert "cloudflare-vieux" not in par_id
    # Météo : seule l'alerte orange sur le Nord (site OVHcloud) est gardée.
    meteo = [e for e in res["evenements"] if e["type"] == "meteo"]
    assert len(meteo) == 1 and meteo[0]["fournisseurs"] == ["ovhcloud"] and meteo[0]["gravite"] == "orange"
    # CERT-FR : seule la publication qui cite Cloudflare, rattachée à Mistral.
    cert = [e for e in res["evenements"] if e["source_auto"] == "cert-fr"]
    assert len(cert) == 1 and cert[0]["fournisseurs"] == ["mistral"]
    # GitHub Actions en panne : un angle mort de la sonde, pas un événement.
    assert [a["id"] for a in res["angles_morts_sonde"]] == ["github-gh1"]
    # Une source en erreur n'empêche pas les autres ; Radar sans jeton est ignoré.
    assert res["sources"]["Meteoalarm"]["etat"] == "partiel"   # flux allemand en panne, français lu
    assert res["sources"]["Cloudflare Radar"]["etat"] == "ignorée"
    assert (tmp_path / "public" / "actualites.json").exists()


def test_presse_tri_fin(tmp_path):
    conf = charger_yaml(RACINE / "config" / "actualites.yaml")
    res = produire_actualites(conf, _racine(tmp_path), client=_client(), env={}, maintenant=MAINTENANT,
                              attendre=lambda s: None)
    presse = [e for e in res["evenements"] if e["source_auto"] == "gdelt"]
    ovh = [e for e in presse if e["fournisseurs"] == ["ovhcloud"]]
    # Deux médias, trois articles proches → un seul événement « repris » ; le 2e article de zdnet est un doublon.
    assert len(ovh) == 1
    assert ovh[0]["presse"]["nb_medias"] == 2 and ovh[0]["gravite"] == "repris"
    assert ovh[0]["fiabilite"] == "presse" and ovh[0]["type"] == "incident_fournisseur"
    # La fenêtre commence 6 h avant la première parution (09:30).
    assert ovh[0]["debut"].startswith("2026-11-20T03:30")
    # Cloudflare : acteur en amont, rattaché à Mistral par le chemin réseau ; un seul média → « isolé ».
    cf = [e for e in presse if e["fournisseurs"] == ["mistral"]]
    assert len(cf) == 1 and cf[0]["type"] == "incident_amont" and cf[0]["gravite"] == "isolé"
    # Le tri : bourse écarté, annonce sans incident écartée, titre sans acteur écarté.
    tri = res["tri_presse"]
    assert tri["hors_sujet"] == 1 and tri["sans_incident"] == 1 and tri["sans_acteur"] == 1
    # Un refus pour excès de débit (429) est réessayé ; une seule requête pour tous les acteurs.
    assert res["sources"]["Presse (GDELT)"]["etat"] == "ok"
    assert len(appels_gdelt) == 2 and "Scaleway" in appels_gdelt[0] and "Cloudflare" in appels_gdelt[0]


def test_presse_repli_par_acteur():
    """Si GDELT juge la requête groupée trop complexe (réponse texte), une requête par acteur."""
    from sonde.actualites import lire_gdelt
    conf = charger_yaml(RACINE / "config" / "actualites.yaml")["sources"]["gdelt"]
    vues = []

    def repondre(req):
        q = req.url.params["query"]
        vues.append(q)
        if "Scaleway" in q and "OVHcloud" in q:
            return httpx.Response(200, text="Your query was too complex.")
        if "OVHcloud" in q:
            return httpx.Response(200, json=GDELT["ovhcloud"])
        if "IONOS" in q:
            return httpx.Response(503, text="")
        return httpx.Response(200, content=b"")
    client = httpx.Client(transport=httpx.MockTransport(repondre))
    evts, bilan = lire_gdelt(client, conf, {"mistral": {"cloudflare"}}, MAINTENANT.replace(day=13), MAINTENANT,
                             attendre=lambda s: None)
    assert "refusée" in bilan["requete_groupee"]
    assert [e["fournisseurs"] for e in evts] == [["ovhcloud"]]
    assert bilan["erreurs"] and bilan["erreurs"][0].startswith("ionos")   # 503 après 4 essais


def test_tri_pages_de_statut():
    """Cloudflare : on garde le réseau en Europe et les incidents globaux, on écarte le reste."""
    from sonde.actualites import lire_statuspages
    conf = charger_yaml(RACINE / "config" / "actualites.yaml")["sources"]
    noms = {
        "a": "Network Performance Issues in Paris", "b": "Network Performance Issues in Miami",
        "c": "Elevated number of 5xx and 499 errors", "d": "R2 Downloads Stalling in Japan",
        "e": "Network performance issues in Los Angeles (LAX) and Frankfurt (FRA) datacenters",
        "f": "Turnstile verification failures", "g": "Degraded connectivity between Europe and Asia Pacific",
        "h": "Cache Purging Delays in Milan", "i": "Elevated errors on API Gateway",
    }
    incidents = {"incidents": [{"id": k, "name": v, "created_at": "2026-11-20T09:00:00Z", "impact": "minor",
                                "components": []} for k, v in noms.items()]}
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=incidents)))
    sp = {"statuspages": [p for p in conf["statuspages"] if p["id"] == "cloudflare"]}
    evts, _, ecartes = lire_statuspages(client, sp, {"mistral": {"cloudflare"}}, MAINTENANT.replace(day=13))
    assert sorted(e["id"].split("-")[1] for e in evts) == ["a", "c", "e", "g", "i"]
    assert len(ecartes) == 4 and all(x["raison"] for x in ecartes)


def test_croisement_sur_mesures_reelles(tmp_path):
    """Mesures réelles du 20/11/2026 : OVHcloud lent pendant son incident officiel du matin."""
    exemple = Path(__file__).parent / "donnees" / "croisement"
    public = tmp_path / "public"
    shutil.copytree(exemple, public)
    actus = {"evenements": [{
        "id": "meteo-test", "titre": "Vigilance orange vent : Nord", "type": "meteo",
        "fournisseurs": ["ovhcloud"], "debut": "2026-11-20T16:30:00+00:00", "fin": "2026-11-20T18:00:00+00:00",
    }]}
    (public / "actualites.json").write_text(json.dumps(actus))
    res = croiser(public, [public / "actualites.json"], tmp_path / "rapports")
    niveaux = {(i["evenement"]["id"].split("-")[0], i["evenement"]["fournisseur"]): i["correlation"]["niveau"]
               for i in res["impacts"]}
    # Incident officiel OVHcloud (06:53 → 12:19) + lenteur mesurée à 08:00 : confirmé.
    assert niveaux[("statut", "OVHcloud")] == "confirme"
    # Alerte météo + échecs mesurés à 17:00 et 17:51, sans confirmation officielle : probable.
    assert niveaux[("meteo", "OVHcloud")] == "probable"
    assert (tmp_path / "rapports" / "croisement.md").exists()


def test_croisement_presse_alertes(tmp_path):
    """Un événement presse passe au croisement avec ses alertes de relecture (jamais publié seul)."""
    exemple = Path(__file__).parent / "donnees" / "croisement"
    public = tmp_path / "public"
    shutil.copytree(exemple, public)
    actus = {"evenements": [{
        "id": "presse-ovhcloud-test", "titre": "Presse : Panne chez OVHcloud", "type": "incident_fournisseur",
        "fournisseurs": ["ovhcloud"], "debut": "2026-11-20T03:30:00+00:00", "fin": "2026-11-20T09:30:00+00:00",
        "source_auto": "gdelt", "fiabilite": "presse", "presse": {"nb_medias": 1, "medias": ["lemagit.fr"]},
        "sources": [{"type": "presse", "url": "https://www.lemagit.fr/a1", "titre": "Panne chez OVHcloud"}],
    }]}
    (public / "actualites.json").write_text(json.dumps(actus))
    res = croiser(public, [public / "actualites.json"], tmp_path / "rapports", avec_statuts=False)
    imp = [i for i in res["impacts"] if i["evenement"]["id"] == "presse-ovhcloud-test"][0]
    assert imp["evenement"]["presse"]["nb_medias"] == 1
    assert any("Source presse" in a for a in imp["alertes_relecture"])
    assert any("seul média" in a for a in imp["alertes_relecture"])
    assert imp["statut_editorial"] == "a_relire"


def test_sans_mesure_pas_de_signal_faible(tmp_path):
    """Un événement tombé entre deux relevés n'est jamais classé « possible »."""
    exemple = Path(__file__).parent / "donnees" / "croisement"
    public = tmp_path / "public"
    shutil.copytree(exemple, public)
    actus = {"evenements": [{"id": "trou", "titre": "Incident pendant un trou de mesure", "type": "incident_amont",
                             "fournisseurs": ["mistral"], "debut": "2026-11-20T03:10:00+00:00",
                             "fin": "2026-11-20T03:20:00+00:00"}]}
    (public / "actualites.json").write_text(json.dumps(actus))
    res = croiser(public, [public / "actualites.json"], tmp_path / "rapports", avec_statuts=False)
    assert not [i for i in res["impacts"] if i["evenement"]["id"] == "trou"]
    assert any(n["evenement"] == "Incident pendant un trou de mesure" for n in res["non_couverts"])
