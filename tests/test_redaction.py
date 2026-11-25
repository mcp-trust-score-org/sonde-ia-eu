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


def _reseau(articles_llm=None, modele_en_panne=None, service_sature=None):
    appels = {"llm": [], "auth": [], "urls": []}

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
            if service_sature and service_sature in u:
                return httpx.Response(429, headers={"retry-after": "20"})
            appels["urls"].append(u)
            if corps["model"] == modele_en_panne:
                return httpx.Response(503)
            appels["llm"].append(corps)
            appels["auth"].append(req.headers.get("authorization"))
            consigne = corps["messages"][1]["content"]
            if "Le Détour" in consigne:
                rep = {"liens": [{"url": "https://next.ink/1", "categorie": "Réseau", "pourquoi": "Pour comprendre un maillon invisible."},
                                 {"url": "https://restofworld.org/a", "categorie": "Réseau", "pourquoi": "Le câble vu d'ailleurs."}]}
            elif "Tous connectés" in consigne and "Réponds : {\"sujet\"" in consigne:
                rep = {"sujet": "Grand Theft Auto VI", "technologie": "les serveurs du jeu saturent",
                       "preuve": "des millions de joueurs ont tenté de se connecter en même temps aux serveurs du jeu",
                       "et_vous": "Un jeu téléchargé dépend d'un compte.",
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
    "une_mini": {"fait": "GTA VI sort aujourd'hui.", "consequence": "Les joueurs attendent.", "dependance": "Le jeu dépend d'un compte."},
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
    sans_service_libre = {**CONF, "redacteur": {**CONF["redacteur"], "services": [
        sv for sv in CONF["redacteur"]["services"] if not sv.get("sans_cle")]}}
    res = rediger(sans_service_libre, racine, client=client, env={}, maintenant=VENDREDI, attendre=lambda s: None)
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


def test_groq_avec_sa_cle(tmp_path):
    """Avec le secret GROQ_API_KEY, Groq passe avant OVHcloud, avec une minute d'attente entre deux appels."""
    racine = _racine(tmp_path)
    client, appels = _reseau()
    pauses = []
    res = rediger(CONF, racine, client=client, env={"GROQ_API_KEY": "cle"}, maintenant=LUNDI, attendre=pauses.append)
    assert res["propositions"][0]["auteur"] == "openai/gpt-oss-120b"
    assert appels["auth"][0] == "Bearer cle"
    assert appels["urls"][0] == "https://api.groq.com/openai/v1/chat/completions"
    assert 61 in pauses


def test_429_on_attend_puis_service_suivant(tmp_path):
    """Groq saturé (429) : on attend le délai demandé, on réessaie, puis on passe à OVHcloud."""
    racine = _racine(tmp_path)
    client, appels = _reseau(service_sature="api.groq.com")
    pauses = []
    res = rediger(CONF, racine, client=client, env={"GROQ_API_KEY": "cle"}, maintenant=LUNDI, attendre=pauses.append)
    assert res["propositions"][0]["auteur"] == "Mistral-Small-3.2-24B-Instruct-2506"
    assert 20.0 in pauses                                               # délai « Retry-After » respecté


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


def test_requete_tient_dans_la_limite_de_groq():
    """Offre gratuite de Groq : 8 000 jetons par minute. Charte de la rubrique seule, extraits raccourcis."""
    from sonde.redaction import Redacteur
    envoyes = []

    def repondre(req):
        envoyes.append(json.loads(req.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(ARTICLE_TC, ensure_ascii=False)}}]})
    client = httpx.Client(transport=httpx.MockTransport(repondre))
    charte = (RACINE / "redaction" / "CHARTE.md").read_text(encoding="utf-8")
    r = Redacteur(CONF["redacteur"], charte, client, {"GROQ_API_KEY": "cle"}, attendre=lambda s: None)
    fiche = {"sujet": "GTA VI", "articles_de_presse": [{"url": f"https://exemple.fr/{i}", "texte": "mot " * 1500} for i in range(3)]}
    r.ecrire("Rubrique : Tous connectés. Écris l'article.", fiche, "tous_connectes")
    corps = envoyes[0]
    taille = sum(len(m["content"]) for m in corps["messages"])
    assert taille <= 17000
    systeme = corps["messages"][0]["content"]
    assert "Tous connectés : l'édition grand public" in systeme and "À la une : l'édition pour les entreprises" not in systeme
    assert "Règles communes" in systeme and "Contrôles automatiques" in systeme


def test_services_satures_on_abandonne_vite_et_on_le_dit(tmp_path):
    """Tous les services répondent 429 : chaque service est déclaré saturé après 2 refus, on n'insiste pas,
    et le fichier du jour explique ce qui s'est passé (journal du rédacteur)."""
    racine = _racine(tmp_path)
    client, _ = _reseau(service_sature="chat/completions")
    pauses = []
    res = rediger(CONF, racine, client=client, env={"GROQ_API_KEY": "cle"}, maintenant=LUNDI, attendre=pauses.append)
    assert sum(pauses) < 300                                            # quelques minutes au pire, pas un quart d'heure
    assert all(p["auteur"] == "fiche" for p in res["propositions"])
    assert {j["service"] for j in res["journal_redacteur"]} == {"Groq", "OVHcloud (anonyme)"}
    md = (racine / "redaction" / "propositions" / "2026-11-23.md").read_text()
    assert "Journal du rédacteur" in md and "429" in md


def test_une_erreur_n_empeche_pas_le_fichier(tmp_path, monkeypatch):
    """Une erreur imprévue en cours de route : le fichier du jour est quand même écrit, avec l'erreur."""
    import sonde.redaction as r
    racine = _racine(tmp_path)
    client, _ = _reseau()
    monkeypatch.setattr(r, "_tous_connectes", lambda *a, **k: 1 / 0)
    res = rediger(CONF, racine, client=client, env={"GROQ_API_KEY": "cle"}, maintenant=LUNDI, attendre=lambda s: None)
    assert res["statut"] == "erreur" and "ZeroDivisionError" in res["erreur"]
    assert [p["rubrique"] for p in res["propositions"]] == ["une", "une"]   # ce qui était prêt est gardé
    assert "Erreur pendant la rédaction" in (racine / "redaction" / "propositions" / "2026-11-23.md").read_text()


def test_reponse_vide_on_reessaie_sans_mode_json():
    """Une réponse vide : on note le détail et on réessaie sans le mode JSON imposé."""
    from sonde.redaction import Redacteur
    vus = []

    def repondre(req):
        corps = json.loads(req.content)
        vus.append("response_format" in corps)
        if "response_format" in corps:
            return httpx.Response(200, json={"choices": [{"message": {"content": ""}, "finish_reason": "stop"}]})
        return httpx.Response(200, json={"choices": [{"message": {"content": "```json\n" + json.dumps(ARTICLE_UNE) + "\n```"}}]})
    client = httpx.Client(transport=httpx.MockTransport(repondre))
    r = Redacteur(CONF["redacteur"], "charte", client, {"GROQ_API_KEY": "cle"}, attendre=lambda s: None)
    rep = r.ecrire("Écris.", {"x": 1}, "une")
    assert rep["title"] == ARTICLE_UNE["title"] and vus == [True, False]
    assert "réponse vide" in r.journal[0]["resultat"] and r.journal[-1]["resultat"] == "ok"


def test_incident_sur_un_modele_non_mesure():
    from sonde.redaction import modele_non_suivi
    suivis = ["Mistral Small 3.2 (24B)", "Mistral Small 4", "Llama 3.3 70B Instruct", "gpt-oss 120B"]
    assert modele_non_suivi("[Generative API] - [global] - GLM-5.3 timeouts", suivis) == "GLM-5.3 timeouts"
    assert modele_non_suivi("Increased error rate for model DeepSeek v4.1 Flash", suivis).startswith("DeepSeek")
    assert modele_non_suivi("Llama 3.3 70B degraded", suivis) is None
    assert modele_non_suivi("AI Endpoint Incident Notification", suivis) is None


def test_impact_affirme_sans_mesure_signale():
    """Premier vrai brouillon de Groq : « Mistral impacté 48 minutes » alors que la sonde n'avait rien mesuré."""
    fiche = {"fournisseurs_concernes": ["mistral"], "mesures_de_la_sonde": "aucune mesure de la sonde pendant l'événement"}
    faux = {**ARTICLE_UNE, "title": "Des problèmes chez Cloudflare<br/>Mistral impacté <mark>48 minutes</mark>"}
    assert any("non soutenue par les mesures" in a for a in controler(faux, "une", fiche))
    juste = {**ARTICLE_UNE, "title": "Cloudflare ralentit à Paris.<br/>Mistral passe par lui, la sonde <mark>n'a rien vu.</mark>"}
    assert not any("non soutenue" in a for a in controler(juste, "une", fiche))


def test_controle_titre_perime_et_doublon():
    from datetime import date
    from sonde.redaction import fiche_tous_connectes
    gta = {**ARTICLE_TC, "title": "GTA VI sort ce jeudi.<br/>Sa version <mark>sans disque</mark> inquiète les joueurs."}
    en_ligne = [{"id": None, "titre": "GTA VI sort aujourd'hui.<br/>Est-il vraiment <mark>à vous ?</mark>"}]
    alertes = " ".join(controler(gta, "tous_connectes", contexte={"date": date(2026, 11, 21), "en_ligne": en_ligne}))
    assert "Titre périmé" in alertes and "Doublon" in alertes
    # le même titre, le jeudi de la sortie, est juste
    assert not any("périmé" in a for a in controler(gta, "tous_connectes", contexte={"date": date(2026, 11, 19)}))
    # un sujet déjà en ligne n'est plus proposé au rédacteur
    tend = {"wikipedia": [{"sujet": "Grand Theft Auto VI", "projet": "fr.wikipedia", "rang": 1, "url": "u"},
                          {"sujet": "Hypothèse de Riemann", "projet": "fr.wikipedia", "rang": 2, "url": "v"}]}
    fiche = fiche_tous_connectes(tend, set(), en_ligne=[en_ligne[0]["titre"]])
    assert [t["sujet"] for t in fiche["tendances_wikipedia"]] == ["Hypothèse de Riemann"]
    assert fiche["deja_en_ligne"] == ["GTA VI sort aujourd'hui. Est-il vraiment à vous ?"]


def test_lien_technologique_invente():
    from sonde.coherence import techno_non_sourcee
    from sonde.redaction import _alertes_lecture
    # Le cas du 21 novembre : une affaire politique habillée en « fuite numérique »
    prefet = {**ARTICLE_TC, "title": "Le préfet veut quitter son poste.<br/>Il pointe la <mark>fuite numérique</mark>.",
              "fait": ["Le préfet a été convoqué par le ministre."],
              "consequence": ["Les soupçons reposent sur des échanges électroniques."]}
    lu = [{"url": "https://exemple.fr/p", "etat": "lu",
           "texte": "Le préfet, soupçonné de fuites vers un parti, dénonce une campagne de déstabilisation. "
                    "Pour sauvegarder cet article, connectez-vous. Votre adresse e-mail sert à la newsletter."}]
    assert techno_non_sourcee(prefet, [lu[0]["texte"]]) == ["numérique", "électronique"]
    assert any(a.startswith("Ligne éditoriale : lien technologique non sourcé") for a in _alertes_lecture(lu, prefet))
    # Le cas GTA : le téléchargement est bien dans l'article lu
    gta = {**ARTICLE_TC, "fait": ["La boîte ne contient qu'un code de téléchargement."], "consequence": ["Pas de revente."]}
    assert techno_non_sourcee(gta, ["Dans la boîte, pas de disque mais un code de téléchargement pour la console."]) == []
    assert techno_non_sourcee(gta, []) == []          # rien de lu : rien à comparer


def test_points_a_verifier_du_redacteur_signales():
    art = {**ARTICLE_TC, "a_verifier": ["Confirmer la date du communiqué"]}
    assert any("1 point(s) à vérifier" in a for a in controler(art, "tous_connectes"))


def test_ligne_editoriale_avant_le_choix_du_sujet():
    from sonde.coherence import hors_ligne, preuve_trouvee
    from sonde.redaction import fiche_tous_connectes
    # faits divers, justice et politique sont retirés avant que le rédacteur choisisse
    assert hors_ligne("https://www.franceinfo.fr/faits-divers/comment-les-malfaiteurs-s-attaquent_1.html")
    assert hors_ligne("https://www.franceinfo.fr/politique/front-national/le-prefet_2.html")
    assert not hors_ligne("https://www.franceinfo.fr/culture/jeux-video/gta-vi/les-ventes_3.html")
    tend = {"presse": [{"titre": "Deux distributeurs explosés", "media": "franceinfo", "url": "https://x.fr/faits-divers/a.html"},
                       {"titre": "GTA VI sans disque", "media": "franceinfo", "url": "https://x.fr/culture/jeux-video/b.html"}]}
    fiche = fiche_tous_connectes(tend, set())
    assert [p["titre"] for p in fiche["presse_grand_public"]] == ["GTA VI sans disque"] and fiche["ecartes_hors_ligne"] == 1
    # la preuve technologique doit être dans un article lu
    texte = "Avec la sortie de GTA VI, les joueurs n'y trouvent aucun disque, mais un simple code de téléchargement."
    assert preuve_trouvee("aucun disque, mais un code de téléchargement", [texte])
    assert not preuve_trouvee("les fuites reposent sur des échanges électroniques", [texte])


def test_detour_le_panier_passe_en_premier(tmp_path):
    racine = _racine(tmp_path)
    (racine / "redaction").mkdir(exist_ok=True)
    (racine / "redaction" / "panier.yaml").write_text(
        "liens:\n"
        "  - url: https://www.lemondedudroit.fr/decryptages/tribune-ia.html\n"
        "    note: \"Tribune sur l'IA chez les avocats\"\n"
        "  - url: https://exemple.fr/idee\n"
        "    pour: idee\n", encoding="utf-8")
    client, appels = _reseau()
    produire_tendances(CONF, racine, client=client, maintenant=VENDREDI, attendre=lambda s: None)
    rediger(CONF, racine, client=client, env={"MISTRAL_API_KEY": "x"}, maintenant=VENDREDI, attendre=lambda s: None)
    envoye = [c for c in appels["llm"] if "Le Détour" in c["messages"][1]["content"]][0]["messages"][1]["content"]
    assert "lemondedudroit.fr/decryptages/tribune-ia.html" in envoye and "Le Monde du Droit" in envoye
    assert envoye.index("tribune-ia.html") < envoye.index("next.ink") if "next.ink" in envoye else True
    assert "exemple.fr/idee" not in envoye                             # un pense-bête n'est jamais proposé
    import json
    deja = json.loads((racine / "redaction" / "deja-proposes.json").read_text(encoding="utf-8"))
    assert "https://www.lemondedudroit.fr/decryptages/tribune-ia.html" in deja["detour"]   # proposé une fois seulement



def test_essentiel_en_deux_minutes():
    from sonde.redaction import controler_essentiel
    assert controler_essentiel({"fait": "OVHcloud signale un incident.", "consequence": "Les réponses ralentissent."}) == []
    alertes = " ".join(controler_essentiel({"fait": "Il signale un incident.", "consequence": "x" * 150}))
    assert "commence par « Il »" in alertes and "150 caractères" in alertes
    assert controler_essentiel({"fait": "Seul."})[0].startswith("L'essentiel en 2 min : « le fait » et « la conséquence »")


def test_pistes_qui_font_reflechir():
    from datetime import datetime, timezone
    from sonde.redaction import pistes_reflexion
    m = datetime(2026, 11, 25, 7, tzinfo=timezone.utc)
    tend = {"detour": [
        {"titre": "Revolut quitte OpenAI et fait tourner des modèles chinois GLM sur ses propres serveurs",
         "url": "https://ex.fr/revolut", "media": "IT for Business", "date": "2026-11-20", "resume": ""},
        {"titre": "Un nouveau smartphone pliable", "url": "https://ex.fr/pliable", "media": "X", "date": "2026-11-24"},
        {"titre": "Souveraineté : le cloud européen face au Cloud Act", "url": "https://ex.fr/vieux", "media": "Y", "date": "2026-10-01"},
    ]}
    p = pistes_reflexion(tend, m, set())
    assert [x["url"] for x in p] == ["https://ex.fr/revolut"]          # deux thèmes au moins, et de la semaine
    assert {"modèles chinois", "changer de fournisseur"} <= set(p[0]["themes"])
    assert pistes_reflexion(tend, m, {"https://ex.fr/revolut"}) == []   # jamais deux fois la même piste
