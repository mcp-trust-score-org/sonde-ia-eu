"""Tendances et propositions d'articles (réseau et rédacteur simulés)."""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import httpx

from sonde.croisement import croiser
from sonde.mesure import RACINE, charger_yaml
from sonde.redaction import controler, rediger
from sonde.tendances import produire_tendances

LUNDI = datetime(2026, 11, 23, 3, 41, tzinfo=timezone.utc)
VENDREDI = datetime(2026, 11, 20, 18, 0, tzinfo=timezone.utc)
CONF = charger_yaml(RACINE / "config" / "redaction.yaml")

WIKI = {"items": [{"articles": [
    {"article": "Wikipédia:Accueil_principal", "views": 900000},
    {"article": "Spécial:Recherche", "views": 500000},
    {"article": "Grand_Theft_Auto_VI", "views": 250000},
    {"article": "Labubu", "views": 90000},
]}]}
PRESSE = {"articles": [
    {"url": "https://exemple.fr/gta", "title": "Grand Theft Auto VI : les serveurs saturés le jour de la sortie",
     "seendate": "20261122T100000Z", "domain": "exemple.fr", "language": "French", "sourcecountry": "France"},
    {"url": "https://exemple.fr/gta-bis", "title": "Grand Theft Auto VI : les serveurs saturés le jour de la sortie",
     "seendate": "20261122T110000Z", "domain": "autre.fr", "language": "French", "sourcecountry": "France"},
]}
DETOUR = {"articles": [
    {"url": "https://next.ink/1", "title": "Ce que la panne de Cloudflare dit d'Internet", "seendate": "20261119T100000Z", "domain": "next.ink"},
    {"url": "https://next.ink/2", "title": "Les datacenters et l'eau", "seendate": "20261118T100000Z", "domain": "next.ink"},
    {"url": "https://next.ink/3", "title": "Troisième article Next", "seendate": "20261117T100000Z", "domain": "next.ink"},
    {"url": "https://www.lemonde.fr/pixels/article/1", "title": "Pixels : l'IA au bureau", "seendate": "20261119T100000Z", "domain": "lemonde.fr"},
    {"url": "https://www.lemonde.fr/politique/article/2", "title": "Hors rubrique", "seendate": "20261119T100000Z", "domain": "lemonde.fr"},
    {"url": "https://restofworld.org/a", "title": "The cable that connects a continent", "seendate": "20261119T100000Z", "domain": "restofworld.org"},
]}


def _rss(items):
    corps = "".join(f"<item><title>{t}</title><link>{u}</link><pubDate>{d}</pubDate><description>{r}</description></item>"
                    for t, u, d, r in items)
    return f"<?xml version='1.0'?><rss version='2.0'><channel>{corps}</channel></rss>"


FLUX_GRAND_PUBLIC = _rss([
    ("Grand Theft Auto VI : les serveurs saturés le jour de la sortie", "https://exemple.fr/gta", "Sun, 22 Nov 2026 10:00:00 +0000", "Files d'attente."),
    ("Grand Theft Auto VI : les serveurs saturés le jour de la sortie", "https://exemple.fr/gta-bis", "Sun, 22 Nov 2026 11:00:00 +0000", ""),
    ("Vieille info", "https://exemple.fr/vieux", "Mon, 02 Nov 2026 10:00:00 +0000", ""),
])
FLUX_NEXT = _rss([
    ("Ce que la panne de Cloudflare dit d'Internet", "https://next.ink/1", "Thu, 19 Nov 2026 10:00:00 +0000", ""),
    ("Les datacenters et l'eau", "https://next.ink/2", "Wed, 18 Nov 2026 10:00:00 +0000", ""),
    ("Troisième article Next", "https://next.ink/3", "Tue, 17 Nov 2026 10:00:00 +0000", ""),
])
FLUX_REPORTERRE = _rss([
    ("Les abeilles reviennent en ville", "https://reporterre.net/abeilles", "Thu, 19 Nov 2026 10:00:00 +0000", "Biodiversité."),
    ("Le coût écologique des centres de données", "https://reporterre.net/donnees", "Thu, 19 Nov 2026 10:00:00 +0000", "Électricité et eau."),
])
FLUX_ROW = """<?xml version='1.0'?><feed xmlns='http://www.w3.org/2005/Atom'><entry><title>The cable that connects a continent</title>
<link rel='alternate' href='https://restofworld.org/a'/><updated>2026-11-19T10:00:00Z</updated></entry></feed>"""


def _reseau(articles_llm=None, modele_en_panne=None):
    appels = {"llm": [], "auth": []}

    def repondre(req: httpx.Request) -> httpx.Response:
        u = str(req.url)
        if "wikimedia.org" in u:
            if "fr.wikipedia.org" in u and "/2026/11/22" in u:
                return httpx.Response(404)   # classement de la veille pas encore publié
            return httpx.Response(200, json=WIKI)
        if "gdeltproject" in u:
            return httpx.Response(200, json=DETOUR if "domain:" in req.url.params["query"] else PRESSE)
        if "francetvinfo.fr/titres.rss" in u:
            return httpx.Response(200, text=FLUX_GRAND_PUBLIC)
        if u == "https://next.ink/feed/":
            return httpx.Response(200, text=FLUX_NEXT)
        if "reporterre.net/spip.php" in u:
            return httpx.Response(200, text=FLUX_REPORTERRE)
        if "restofworld.org/feed" in u:
            return httpx.Response(200, text=FLUX_ROW)
        if u.endswith((".rss", ".xml", "/rss", "/rss/", "/feed/", "/index", ".atom", "/feed/latest")) or "backend" in u:
            return httpx.Response(503)
        if u.startswith("https://exemple.fr/gta"):
            return httpx.Response(200, headers={"content-type": "text/html"}, text=PAGE_GTA)
        if u.startswith("https://next.ink/1"):
            return httpx.Response(200, headers={"content-type": "text/html"}, text=PAGE_GTA)
        if u.startswith("https://next.ink") or "restofworld" in u or "lemonde.fr" in u:
            return httpx.Response(403)
        if "chat/completions" in u:
            corps = json.loads(req.content)
            if corps["model"] == modele_en_panne:
                return httpx.Response(503)
            appels["llm"].append(corps)
            appels["auth"].append(req.headers.get("authorization"))
            consigne = corps["messages"][1]["content"]
            if "Le Détour" in consigne:
                rep = {"liens": [{"url": "https://next.ink/1", "categorie": "Réseau", "pourquoi": "Pour comprendre un maillon invisible."},
                                 {"url": "https://restofworld.org/a", "categorie": "Réseau", "pourquoi": "Le câble vu d'ailleurs."}]}
            elif "Tous connectés" in consigne and "Réponds : {\"sujet\"" in consigne:
                rep = {"sujet": "Grand Theft Auto VI", "et_vous": "Un jeu téléchargé dépend d'un compte.",
                       "urls": ["https://exemple.fr/gta", "https://invente.example/x"]}
            elif "Tous connectés" in consigne:
                rep = (articles_llm or {}).get("tc") or ARTICLE_TC
            else:
                rep = (articles_llm or {}).get("une") or ARTICLE_UNE
            return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(rep, ensure_ascii=False)}}]})
        return httpx.Response(404)
    return httpx.Client(transport=httpx.MockTransport(repondre)), appels


PAGE_GTA = """<html><head><script>var x = "pas du texte";</script></head><body>
<nav><p>Accueil Jeux Tech Culture Accueil Jeux Tech Culture Accueil Jeux Tech Culture Accueil</p></nav>
<article><h1>Les serveurs saturés</h1>
<p>Le jour de la sortie, des millions de joueurs ont tenté de se connecter en même temps aux serveurs du jeu, provoquant de longues files d'attente.</p>
<p>L'éditeur a reconnu des difficultés de connexion pendant plusieurs heures et a présenté ses excuses aux joueurs touchés par le problème.</p>
<p>Même la version vendue en boîte ne contient qu'un code de téléchargement, obligeant chacun à récupérer plus de deux cents gigaoctets de données.</p>
</article><footer><p>Mentions légales et conditions générales d'utilisation du site, tous droits réservés.</p></footer></body></html>"""


ARTICLE_UNE = {
    "tag": "IA", "title": "Un matin comme les autres.<br/>Une IA <mark>14 fois</mark> plus lente.",
    "chapo": "Le modèle a hésité longuement avant chaque réponse.",
    "fait": ["OVHcloud signale un incident sur son service d'IA.", "Un message discret."],
    "consequence": ["La sonde mesure un fort ralentissement.", "Les autres modèles tiennent."],
    "lien": ["On dépend d'un modèle précis.", "Combien de temps avant que quelqu'un s'en aperçoive ?"],
    "une_mini": {"fait": "…", "consequence": "…", "dependance": "…"},
    "sources": [{"label": "OVHcloud : page de statut", "url": "https://stspg.io/vlkf6x66jncd"}],
}
ARTICLE_TC = {
    "sujet": "Grand Theft Auto VI", "categorie": "jeux-video", "tag": "Jeux vidéo",
    "title": "GTA VI sort aujourd'hui.<br/>Est-il vraiment <mark>à vous ?</mark>",
    "chapo": "Le jeu arrive enfin.", "fait": ["Les serveurs saturent.", "Le jour de la sortie."],
    "consequence": ["Tout passe par des serveurs.", "Personne ne les voit."],
    "lien": ["Un jeu téléchargé dépend d'un compte.", "Et le vôtre, il est où ?"],
    "reflexes": ["Activez la double authentification.", "Listez vos jeux sur disque.", "Téléchargez la nuit."],
    "reflexe_de_la_semaine": {"titre": "Activez la double authentification.", "texte": "C'est votre bibliothèque."},
    "sources": [{"label": "Exemple : serveurs saturés", "url": "https://exemple.fr/gta"}],
}


def _racine(tmp_path: Path) -> Path:
    public = tmp_path / "public"
    shutil.copytree(Path(__file__).parent / "donnees" / "croisement", public)
    (tmp_path / "redaction").mkdir()
    shutil.copy(RACINE / "redaction" / "CHARTE.md", tmp_path / "redaction" / "CHARTE.md")
    actus = {"evenements": [{
        "id": "meteo-test", "titre": "Vigilance orange « Vent violent » : Nord", "type": "meteo",
        "fournisseurs": ["ovhcloud"], "debut": "2026-11-20T16:30:00+00:00", "fin": "2026-11-20T18:00:00+00:00",
        "gravite": "orange", "source_auto": "meteoalarm",
        "sources": [{"type": "alerte_officielle", "url": "https://meteoalarm.org/x", "titre": "Meteoalarm · Nord"}]}]}
    (public / "actualites.json").write_text(json.dumps(actus, ensure_ascii=False))
    croiser(public, [public / "actualites.json"], tmp_path / "rapports")
    return tmp_path


def test_tendances(tmp_path):
    client, _ = _reseau()
    res = produire_tendances(CONF, tmp_path, client=client, maintenant=LUNDI, attendre=lambda s: None)
    wiki = [w["sujet"] for w in res["wikipedia"] if w["projet"] == "fr.wikipedia.org"]
    assert wiki == ["Grand Theft Auto VI", "Labubu"]                  # pages techniques écartées
    assert res["wikipedia"][0]["jour"] == "2026-11-21"                 # repli sur l'avant-veille
    assert [p["url"] for p in res["presse"]] == ["https://exemple.fr/gta"]   # doublon et vieille info écartés
    titres = [d["titre"] for d in res["detour"]]
    assert "Le coût écologique des centres de données" in titres          # média généraliste : sujet tech gardé
    assert "Les abeilles reviennent en ville" not in titres              # … le reste écarté
    assert "Troisième article Next" in titres                            # média spécialisé : tout gardé
    assert "The cable that connects a continent" in titres               # flux Atom
    assert res["flux"]["Détour (flux RSS)"]["Numerama"].startswith("erreur")   # un flux en panne est noté
    assert all(e["etat"] == "ok" for e in res["sources"].values())


def test_propositions_du_lundi(tmp_path):
    racine = _racine(tmp_path)
    client, appels = _reseau()
    produire_tendances(CONF, racine, client=client, maintenant=LUNDI, attendre=lambda s: None)
    res = rediger(CONF, racine, client=client, env={"MISTRAL_API_KEY": "x"}, maintenant=LUNDI, attendre=lambda s: None)
    rubriques = [(p["rubrique"], p.get("format")) for p in res["propositions"]]
    # Lundi : le sujet du jour, le bilan de la semaine, et un sujet grand public. Pas de Détour.
    assert rubriques == [("une", "a_chaud"), ("une", "bilan"), ("tous_connectes", "a_chaud")]
    une = res["propositions"][0]
    assert une["tag_interne"] in ("Confirmé", "Probable", "Possible", "Aucune anomalie", "Non mesuré")
    assert une["image"].startswith("assets/photos/")
    assert une["alertes_charte"] == []                                 # l'article simulé respecte la charte
    tc = res["propositions"][2]
    assert tc["image"].endswith("jeux-video.jpg")
    # Les articles ont été lus ; le lien inventé par le rédacteur est écarté.
    lus = tc["fiche"]["articles_de_presse"]
    assert [a["url"] for a in lus] == ["https://exemple.fr/gta"] and lus[0]["etat"] == "lu"
    assert "files d'attente" in lus[0]["texte"] and "Mentions légales" not in lus[0]["texte"] and "Accueil" not in lus[0]["texte"]
    assert tc["alertes_charte"] == []
    # La charte est bien donnée au rédacteur, avec les faits seulement.
    assert "Charte éditoriale d'Iris" in appels["llm"][0]["messages"][0]["content"]
    assert "=== FICHE ===" in appels["llm"][0]["messages"][1]["content"]
    assert (racine / "redaction" / "propositions" / "2026-11-23.md").exists()
    # Le lendemain, le même événement n'est pas reproposé.
    res2 = rediger(CONF, racine, client=client, env={"MISTRAL_API_KEY": "x"}, maintenant=LUNDI.replace(day=24), attendre=lambda s: None)
    ids = [p.get("evenement_id") for p in res2["propositions"] if p["rubrique"] == "une"]
    assert une["evenement_id"] not in ids


def test_detour_du_vendredi_et_fiche_sans_cle(tmp_path):
    racine = _racine(tmp_path)
    client, appels = _reseau()
    produire_tendances(CONF, racine, client=client, maintenant=VENDREDI, attendre=lambda s: None)
    sans_secours = {**CONF, "redacteur": {k: v for k, v in CONF["redacteur"].items() if k != "secours"}}
    res = rediger(sans_secours, racine, client=client, env={}, maintenant=VENDREDI)
    detour = [p for p in res["propositions"] if p["rubrique"] == "detour"][0]
    medias = [l["media"] for l in detour["liens"]]
    assert medias.count("Next") <= 2                                   # 2 liens par média au plus
    assert any(l.get("mention") == "(en anglais)" for l in detour["liens"])
    une = [p for p in res["propositions"] if p["rubrique"] == "une"][0]
    assert une["auteur"] == "fiche" and une["fiche"]["sources"]        # sans clé : une fiche à rédiger
    assert not appels["llm"]


def test_redacteur_de_secours_sans_cle(tmp_path):
    """Sans clé Mistral : OVHcloud en accès anonyme, sans en-tête d'authentification, avec une pause entre appels."""
    racine = _racine(tmp_path)
    client, appels = _reseau()
    pauses = []
    res = rediger(CONF, racine, client=client, env={}, maintenant=LUNDI, attendre=pauses.append)
    assert res["propositions"][0]["auteur"] == "Mistral-Small-3.2-24B-Instruct-2506"
    assert appels["llm"] and all(c["model"] == "Mistral-Small-3.2-24B-Instruct-2506" for c in appels["llm"])
    assert appels["auth"] == [None] * len(appels["llm"])                # aucune clé envoyée
    assert pauses and set(pauses) == {31}


def test_secours_passe_au_modele_suivant(tmp_path):
    racine = _racine(tmp_path)
    client, appels = _reseau(modele_en_panne="Mistral-Small-3.2-24B-Instruct-2506")
    res = rediger(CONF, racine, client=client, env={}, maintenant=LUNDI, attendre=lambda s: None)
    assert res["propositions"][0]["auteur"] == "gpt-oss-120b"


def test_passage_recopie_signale():
    from sonde.redaction import passages_recopies
    texte = "Le jour de la sortie, des millions de joueurs ont tenté de se connecter en même temps aux serveurs du jeu."
    copie = {**ARTICLE_TC, "fait": ["Le jour de la sortie, des millions de joueurs ont tenté de se connecter en même temps aux serveurs.", "Recul."]}
    assert passages_recopies(copie, [texte])
    assert not passages_recopies(ARTICLE_TC, [texte])


def test_detour_lit_le_debut_des_articles(tmp_path):
    racine = _racine(tmp_path)
    client, appels = _reseau()
    produire_tendances(CONF, racine, client=client, maintenant=VENDREDI, attendre=lambda s: None)
    res = rediger(CONF, racine, client=client, env={"MISTRAL_API_KEY": "x"}, maintenant=VENDREDI, attendre=lambda s: None)
    detour = [p for p in res["propositions"] if p["rubrique"] == "detour"][0]
    envoye = [c for c in appels["llm"] if "Le Détour" in c["messages"][1]["content"]][0]["messages"][1]["content"]
    assert "files d'attente" in envoye                                 # début de l'article lu, donné au rédacteur
    assert any("non lu" in a for a in detour["alertes_charte"])        # les pages protégées sont signalées
    assert detour["liens"][0]["pourquoi"]


def test_controles_de_la_charte():
    mauvais = {**ARTICLE_UNE, "title": "Votre <mark>IA</mark> a <mark>planté</mark> !",
               "lien": ["On dépend d'un modèle.", "Il faut agir."],
               "consequence": ["12 pannes, 34 minutes, 56 clients et 78 euros."], "sources": []}
    alertes = " ".join(controler(mauvais, "une"))
    for attendu in ("un seul élément surligné", "pas de « vous »", "exclamation", "question", "Trop de chiffres", "Aucune source"):
        assert attendu in alertes
    tc = {**ARTICLE_TC, "reflexes": ["un seul"]}
    assert any("3 bons réflexes" in a for a in controler(tc, "tous_connectes"))
    assert controler(ARTICLE_TC, "tous_connectes") == []
