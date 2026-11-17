"""Tests de la veille à la minute, de la météo, des alertes, des avoirs, des attestations et du bulletin."""

import asyncio
import json
from datetime import datetime, timedelta, timezone

import httpx

from sonde.alertes import detecter, envoyer, traiter
from sonde.attestation import attester, en_markdown
from sonde.bulletin import svg, texte
from sonde.horodatage import ecrire_manifeste
from sonde.meteo import calculer, incidents, produire_meteo, statut_minutes
from sonde.mesure import charger_yaml
from sonde.sla import calculer as calculer_avoir, echeance, produire_avoirs
from sonde.veille import lire_veille, veiller

from .test_sonde import RACINE, serveur  # noqa: F401

CONF_V = charger_yaml(RACINE / "config" / "veille.yaml")
MAINTENANT = datetime(2026, 11, 16, 14, 30, tzinfo=timezone.utc)


def _config(ids):
    return {"fournisseurs": [{"id": i, "nom": f"{i.capitalize()} Cloud", "pays": "FR", "base_url": "x", "cle_env": "X"} for i in ids],
            "modeles": []}


def _ligne(f, quand, ok=True, ttft=400.0, erreur=None):
    return {"type": "veille", "horodatage": quand.isoformat(timespec="seconds"), "fournisseur": f, "offre": "payante",
            "point": "Paris", "modele": "llama-3.3-70b", "modele_id": "llama", "succes": ok,
            "statut_http": 200 if ok else 503, "erreur": None if ok else (erreur or "HTTP 503: indisponible"),
            "ttft_ms": ttft if ok else None, "duree_ms": ttft + 50 if ok else None}


def _histoire(minutes=600, fin=MAINTENANT):
    """10 h de veille : a stable, b en panne depuis 12 min, c très lent depuis 10 min, d un peu lent."""
    lignes = []
    for k in range(minutes):
        t = fin - timedelta(minutes=minutes - k)
        recent = k >= minutes - 10
        lignes.append(_ligne("a", t))
        lignes.append(_ligne("b", t, ok=not (k >= minutes - 12)))
        lignes.append(_ligne("c", t, ttft=1000.0 if recent else 400.0))
        lignes.append(_ligne("d", t, ttft=600.0 if recent else 400.0))
    return lignes


def _ecrire(tmp, lignes):
    d = tmp / "data" / "veille"
    d.mkdir(parents=True, exist_ok=True)
    par_jour = {}
    for l in lignes:
        par_jour.setdefault(l["horodatage"][:10], []).append(l)
    for j, ls in par_jour.items():
        with open(d / f"{j}.jsonl", "w", encoding="utf-8") as f:
            for l in ls:
                f.write(json.dumps(l, ensure_ascii=False) + "\n")
    return tmp / "data"


# ------------------------------------------------------------------ veille

def test_veille_contre_faux_fournisseurs(serveur, tmp_path):
    config = charger_yaml(RACINE / "config" / "fournisseurs.yaml")
    config["assistants"] = []
    config["fournisseurs"] = [
        {"id": "rapide", "nom": "Rapide", "base_url": f"{serveur}/rapide/v1", "cle_env": "K1"},
        {"id": "panne", "nom": "Panne", "base_url": f"{serveur}/panne/v1", "cle_env": "K2"},
        {"id": "anonyme", "nom": "Anonyme", "base_url": f"{serveur}/anonyme/v1", "cle_env": "K3",
         "anonyme_si_sans_cle": True, "catalogue_secours": ["gpt-oss-120b"]},
        {"id": "sanscle", "nom": "Sans clé", "base_url": f"{serveur}/rapide/v1", "cle_env": "K4"},
    ]
    env = {"K1": "x", "K2": "x"}
    lignes = asyncio.run(veiller(config, CONF_V, tmp_path, env=env, point="test"))
    par = {l["fournisseur"]: l for l in lignes}
    assert set(par) == {"rapide", "panne", "anonyme"}
    assert par["rapide"]["succes"] and par["rapide"]["ttft_ms"] is not None
    assert not par["panne"]["succes"] and par["panne"]["statut_http"] == 503
    assert par["anonyme"]["succes"] and par["anonyme"]["offre"] == "anonyme" and par["anonyme"]["modele_id"] == "gpt-oss-120b"
    cache = json.loads((tmp_path / "veille" / "cache-modeles.json").read_text())
    assert cache["rapide"]["modele_id"] == "Meta-Llama-3_3-70B-Instruct"
    # Deuxième passage : le cache évite de relire le catalogue, et les lignes s'ajoutent.
    asyncio.run(veiller(config, CONF_V, tmp_path, env=env, point="test"))
    assert len(lire_veille(tmp_path, datetime.now(timezone.utc) - timedelta(hours=1))) == 6


# ------------------------------------------------------------------ météo

def test_meteo_etats_vigilance_et_phrase():
    m = calculer(_config(["a", "b", "c", "d"]), CONF_V, _histoire(), [], MAINTENANT)
    par = {f["id"]: f for f in m["fournisseurs"]}
    assert par["a"]["etat"] == "soleil" and par["a"]["vigilance"] == "vert"
    assert par["b"]["etat"] == "orage" and par["b"]["vigilance"] == "rouge"
    assert par["b"]["panne_en_cours"]["minutes"] == 12
    assert par["c"]["etat"] == "nuage" and par["c"]["vigilance"] == "orange" and "2,5 fois" in par["c"]["raison"]
    assert par["d"]["etat"] == "eclaircie" and par["d"]["vigilance"] == "jaune"
    assert m["phrase"] == "Temps calme sur 1 fournisseur, nuages sur C et D, orage sur B."
    assert par["b"]["disponibilite"]["24h"] == round(100 * 588 / 600, 3)
    chrono = par["b"]["chronologie"]
    assert [p["nature"] for p in chrono].count("prevision") == 3
    assert chrono[-3]["etat"] == "orage"          # prolongée une heure, puis rien d'annoncé
    assert chrono[-1]["etat"] == "inconnu"


def test_evenement_annonce_monte_la_vigilance():
    conf = {**CONF_V, "evenements": [{"fournisseur": "a", "debut": "2026-11-16T15:00:00+00:00",
                                      "fin": "2026-11-16T18:00:00+00:00", "niveau": "jaune", "raison": "Sortie d'un modèle"}]}
    m = calculer(_config(["a"]), conf, _histoire(), [], MAINTENANT)
    a = m["fournisseurs"][0]
    assert a["vigilance"] == "jaune" and a["raison"] == "Sortie d'un modèle"
    assert a["chronologie"][-3]["etat"] == "eclaircie"


def test_repli_sur_la_mesure_horaire():
    mesures = [{"type": "mesure", "horodatage": (MAINTENANT - timedelta(minutes=20)).isoformat(), "execution": "e1",
                "fournisseur": "a", "succes": False, "offre": "gratuite"} for _ in range(6)]
    # Le fournisseur a déjà répondu une fois : les échecs sont donc une vraie panne.
    mesures.insert(0, {"type": "mesure", "horodatage": (MAINTENANT - timedelta(hours=5)).isoformat(),
                       "execution": "e0", "fournisseur": "a", "succes": True, "offre": "gratuite"})
    m = calculer(_config(["a"]), CONF_V, [], mesures, MAINTENANT)
    assert m["fournisseurs"][0]["source"] == "horaire" and m["fournisseurs"][0]["etat"] == "orage"


def test_minutes_et_incidents():
    debut = MAINTENANT - timedelta(minutes=5)
    lignes = [_ligne("a", debut + timedelta(minutes=k), ok=k not in (1, 2)) for k in range(4)]
    assert statut_minutes(lignes, debut, MAINTENANT) == [1, 0, 0, 1, None]
    inc = incidents(lignes, 2)
    assert len(inc) == 1 and inc[0]["duree_min"] == 2 and not inc[0]["en_cours"]


def test_produire_meteo_ecrit_les_fichiers(tmp_path):
    donnees = _ecrire(tmp_path, _histoire(120))
    produire_meteo(donnees, tmp_path / "public", _config(["a", "b"]), CONF_V, MAINTENANT)
    m = json.loads((tmp_path / "public" / "meteo.json").read_text())
    assert {f["id"] for f in m["fournisseurs"]} == {"a", "b"}
    mins = json.loads((tmp_path / "public" / "minutes" / "2026-11-16.json").read_text())
    assert mins["fournisseurs"]["b"].endswith("0" * 12 + "-")   # minute en cours pas encore mesurée


# ------------------------------------------------------------------ alertes

def test_alertes_debut_et_fin_d_orage(tmp_path):
    contrats = {"contrats": {"b": {"debut_decompte": "ticket"}}}
    donnees, public = tmp_path / "data", tmp_path / "public"
    public.mkdir()
    envois = []

    def faux_envoi(a, env=None):
        envois.append(a)
        return ["test"]

    calme = calculer(_config(["a", "b"]), CONF_V, [l for l in _histoire() if l["fournisseur"] == "a"] +
                     [_ligne("b", MAINTENANT - timedelta(minutes=k)) for k in range(30)], [], MAINTENANT)
    (public / "meteo.json").write_text(json.dumps(calme))
    assert traiter(donnees, public, contrats, envoi=faux_envoi) == []      # premier passage : rien
    orage = calculer(_config(["a", "b"]), CONF_V, _histoire(), [], MAINTENANT)
    (public / "meteo.json").write_text(json.dumps(orage))
    a = traiter(donnees, public, contrats, envoi=faux_envoi)
    assert [x["type"] for x in a] == ["orage"]
    assert "Itinéraire bis : A fonctionne normalement" in a[0]["texte"] and "ticket" in a[0]["texte"]
    assert traiter(donnees, public, contrats, envoi=faux_envoi) == []      # pas de répétition
    (public / "meteo.json").write_text(json.dumps(calme))
    assert [x["type"] for x in traiter(donnees, public, contrats, envoi=faux_envoi)] == ["fin_orage"]
    journal = json.loads((public / "alertes.json").read_text())
    assert [x["type"] for x in journal] == ["fin_orage", "orage"]
    assert journal[1]["id"].startswith("b-orage-") and journal[0]["id"].startswith("b-fin-orage-")


def test_retours_des_membres(tmp_path):
    from sonde.retours import lire_message, relever, totaliser
    donnees, public = tmp_path / "data", tmp_path / "public"
    public.mkdir()
    (public / "alertes.json").write_text(json.dumps([
        {"id": "ovhcloud-orage-202611161053", "fournisseur": "ovhcloud", "type": "orage"}]))
    flux = "\n".join(json.dumps(e) for e in [
        {"event": "open", "id": "o"},
        {"event": "message", "id": "m1", "time": 1, "message": "touche|ovhcloud-orage-202611161053"},
        {"event": "message", "id": "m2", "time": 2, "message": "touche|ovhcloud-orage-202611161053"},
        {"event": "message", "id": "m3", "time": 3, "message": "pas_touche|ovhcloud-orage-202611161053"},
        {"event": "message", "id": "m4", "time": 4, "message": "n'importe quoi"},
    ])
    vus = []

    def handler(req):
        vus.append(req)
        return httpx.Response(200, text=flux)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    env = {"NTFY_TOPIC": "mon-sujet"}
    assert relever(donnees, env, client) == 3
    assert vus[0].url.path == "/mon-sujet-retours/json" and vus[0].url.params["poll"] == "1"
    assert relever(donnees, env, client) == 0          # ntfy renvoie les mêmes : pas de doublon
    t = totaliser(donnees, public)
    assert t["par_alerte"]["ovhcloud-orage-202611161053"] == {"touche": 2, "pas_touche": 1}
    assert t["par_fournisseur"]["ovhcloud"]["part_touche_pct"] == 67
    assert lire_message("touche|x y") is None and relever(donnees, {}, client) == 0


def test_envoi_ntfy_et_webhook():
    recus = []

    def handler(req):
        recus.append(req)
        return httpx.Response(200)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    alerte = {"titre": "Orage sur OVHcloud", "texte": "Panne en cours, échecs.", "niveau": "rouge",
              "type": "orage", "id": "ovhcloud-orage-202611161053"}
    faits = envoyer(alerte, {"NTFY_TOPIC": "mon-sujet", "ALERTE_WEBHOOK_URL": "https://hooks.exemple/x"}, client)
    assert faits == ["ntfy", "webhook"]
    corps = json.loads(recus[0].content)
    assert corps["topic"] == "mon-sujet" and corps["title"] == "Orage sur OVHcloud" and corps["priority"] == 5
    assert [b["label"] for b in corps["actions"]] == ["Moi aussi", "Pas chez moi"]
    assert corps["actions"][0]["url"] == "https://ntfy.sh/mon-sujet-retours"
    assert corps["actions"][1]["body"] == "pas_touche|ovhcloud-orage-202611161053"
    assert json.loads(recus[1].content)["text"].startswith("*Orage")
    assert envoyer(alerte, {}, client) == []


# ------------------------------------------------------------------ avoirs

CONTRAT = {"service": "Generative APIs", "engagement_pct": 99.9, "definition_panne": {"fenetre_min": 1, "seuil_erreur": 1.0},
           "debut_decompte": "panne", "paliers": [{"sous_pct": 99.9, "avoir_pct": 10}, {"sous_pct": 99.0, "avoir_pct": 25}],
           "reclamation": {"delai_jours_apres_fin_mois": 30}, "verifie": False, "source": "test"}


def _mois_avec_panne(minutes_panne, debut_panne=datetime(2026, 10, 8, 9, 0, tzinfo=timezone.utc)):
    lignes, t = [], datetime(2026, 10, 1, tzinfo=timezone.utc)
    fin = datetime(2026, 11, 1, tzinfo=timezone.utc)
    while t < fin:
        panne = debut_panne <= t < debut_panne + timedelta(minutes=minutes_panne)
        lignes.append(_ligne("scaleway", t, ok=not panne))
        t += timedelta(minutes=1)
    return lignes


def test_avoir_selon_le_palier():
    r = calculer_avoir("scaleway", _mois_avec_panne(210), CONTRAT, "2026-10", facture=2400, maintenant=MAINTENANT)
    assert r["fenetres_mesurees"] == 31 * 1440 and r["minutes_en_panne"] == 210
    assert 99.5 < r["disponibilite_pct"] < 99.6 and not r["engagement_tenu"]
    assert r["avoir_pct"] == 10 and r["avoir_eur"] == 240
    assert r["echeance"] == "2026-11-30" and r["jours_restants"] == 14
    assert r["incidents"][0]["duree_min"] == 210


def test_avoir_ne_compte_qu_a_partir_du_ticket():
    c = {**CONTRAT, "debut_decompte": "ticket"}
    lignes = _mois_avec_panne(600)
    sans = calculer_avoir("x", lignes, c, "2026-10", maintenant=MAINTENANT)
    assert sans["minutes_en_panne"] == 0 and sans["minutes_non_decomptees_faute_de_ticket"] == 600
    assert sans["disponibilite_si_ticket_immediat_pct"] < 99
    avec = calculer_avoir("x", lignes, c, "2026-10", tickets=[datetime(2026, 10, 8, 10, 0, tzinfo=timezone.utc)], maintenant=MAINTENANT)
    assert avec["minutes_en_panne"] == 540 and avec["minutes_non_decomptees_faute_de_ticket"] == 60


def test_produire_avoirs_public_sans_montant(tmp_path):
    donnees = _ecrire(tmp_path, _mois_avec_panne(210))
    config = {"fournisseurs": [{"id": "scaleway", "nom": "Scaleway"}]}
    res = produire_avoirs(donnees, tmp_path / "public", tmp_path / "rec", config, {"contrats": {"scaleway": CONTRAT}},
                          "2026-10", {"scaleway": 2400.0}, maintenant=MAINTENANT)
    assert res[0]["avoir_eur"] == 240
    public = json.loads((tmp_path / "public" / "avoirs.json").read_text())
    assert "avoir_eur" not in public["2026-10"][0] and "facture_eur" not in public["2026-10"][0]
    md = (tmp_path / "rec" / "2026-10" / "scaleway.md").read_text()
    assert "240,00 €" in md and "Estimation" in md and "2026-11-30" in md


def test_echeance_fin_de_mois():
    assert echeance("2026-12", CONTRAT).isoformat() == "2027-01-30"


# ------------------------------------------------------------------ attestation

def test_attestation_et_preuves(tmp_path):
    debut = datetime(2026, 11, 16, 14, 0, tzinfo=timezone.utc)
    lignes = [_ligne("ovhcloud", debut + timedelta(minutes=k), ok=not (2 <= k < 7)) for k in range(10)]
    donnees = _ecrire(tmp_path, lignes)
    ecrire_manifeste(donnees, tmp_path / "preuves", MAINTENANT)
    config = {"fournisseurs": [{"id": "ovhcloud", "nom": "OVHcloud AI Endpoints"}]}
    a = attester(donnees, tmp_path / "preuves", config, "ovhcloud", debut, debut + timedelta(minutes=10), MAINTENANT)
    assert a["minutes_mesurees"] == 10 and a["minutes_en_echec"] == 5 and a["taux_echec_pct"] == 50
    assert [s["etat"] for s in a["chronologie"]] == ["fonctionne", "en échec", "fonctionne"]
    assert a["pannes"][0]["duree_min"] == 5
    assert a["preuves"]["manifestes"] == ["2026-11-16.json"]
    md = en_markdown(a)
    assert "ATT-ovhcloud-202611161400" in md and "SHA-256" in md


# ------------------------------------------------------------------ bulletin

def test_bulletin():
    m = calculer(_config(["a", "b"]), CONF_V, _histoire(), [], MAINTENANT)
    s = svg(m, "Iris · iris.exemple")
    assert s.startswith("<svg") and "La météo de l&#x27;IA" not in s and "La météo de l'IA" in s
    assert "orage sur B" in s and "Iris · iris.exemple" in s
    t = texte(m, "iris.exemple")
    assert "• B : orage, en panne" in t and "iris.exemple" in t


def test_plusieurs_passages_dans_la_meme_minute():
    t = MAINTENANT - timedelta(minutes=10)
    lignes = [_ligne("a", t + timedelta(minutes=k, seconds=s), ok=False) for k in range(3) for s in (0, 20, 40)]
    inc = incidents(lignes, 2)
    assert len(inc) == 1 and inc[0]["minutes"] == 3 and inc[0]["duree_min"] == 3


def test_veille_espacee_et_limite_de_debit():
    # Un passage toutes les 10 minutes : un seul échec donne un nuage, pas un orage ; deux sur trois, oui.
    lignes = [_ligne("a", MAINTENANT - timedelta(minutes=m)) for m in (55, 45, 35, 25, 15)]
    lignes.append(_ligne("a", MAINTENANT - timedelta(minutes=5), ok=False))
    assert calculer(_config(["a"]), CONF_V, lignes, [], MAINTENANT)["fournisseurs"][0]["etat"] == "nuage"
    lignes[-2] = _ligne("a", MAINTENANT - timedelta(minutes=15), ok=False)
    assert calculer(_config(["a"]), CONF_V, lignes, [], MAINTENANT)["fournisseurs"][0]["etat"] == "orage"
    # Une limite de débit (HTTP 429) de notre offre gratuite n'est pas une panne du fournisseur.
    l429 = [{**_ligne("a", MAINTENANT - timedelta(minutes=m), ok=False), "statut_http": 429} for m in (3, 2, 1)]
    f = calculer(_config(["a"]), CONF_V, lignes[:4] + l429, [], MAINTENANT)["fournisseurs"][0]
    assert f["etat"] == "soleil" and f["limites_de_debit_30j"] == 3


def test_jamais_joint_n_est_pas_un_orage():
    # Aucune réponse réussie depuis le début : problème d'accès, pas panne du fournisseur.
    lignes = [{**_ligne("a", MAINTENANT - timedelta(minutes=m), ok=False), "statut_http": 401, "erreur": "Unauthorized"}
              for m in (25, 15, 5)]
    f = calculer(_config(["a"]), CONF_V, lignes, [], MAINTENANT)["fournisseurs"][0]
    assert f["etat"] == "inconnu" and f["acces_impossible"] and f["vigilance"] == "vert"
    assert f["derniere_erreur"].startswith("HTTP 401") and f["incidents_30j"] == []
    # Dès qu'une réponse a réussi une fois, un échec redevient une vraie mesure.
    lignes.insert(0, _ligne("a", MAINTENANT - timedelta(minutes=35)))
    f = calculer(_config(["a"]), CONF_V, lignes, [], MAINTENANT)["fournisseurs"][0]
    assert f["etat"] == "orage" and not f["acces_impossible"]


def test_veille_porte_d_entree_sans_cle(serveur, tmp_path):
    # Sans clé : on frappe à la porte. « Accès refusé » = service debout ; pas de réponse = panne.
    config = charger_yaml(RACINE / "config" / "fournisseurs.yaml")
    config["assistants"] = []
    config["fournisseurs"] = [
        {"id": "debout", "nom": "Debout", "base_url": f"{serveur}/anonyme/v1", "cle_env": "K1", "porte_si_sans_cle": True},
        {"id": "tombe", "nom": "Tombé", "base_url": "http://127.0.0.1:9/v1", "cle_env": "K2", "porte_si_sans_cle": True},
        {"id": "ignore", "nom": "Ignoré", "base_url": f"{serveur}/rapide/v1", "cle_env": "K3"},
    ]
    lignes = asyncio.run(veiller(config, CONF_V, tmp_path, env={}, point="test"))
    par = {l["fournisseur"]: l for l in lignes}
    assert set(par) == {"debout", "tombe"}
    assert par["debout"]["succes"] and par["debout"]["statut_http"] == 401 and par["debout"]["offre"] == "porte"
    assert par["debout"]["ttft_ms"] is not None and par["debout"]["modele"] is None
    assert not par["tombe"]["succes"] and par["tombe"]["erreur"]


def test_un_seul_echec_ne_fait_jamais_un_orage():
    # Le fournisseur a déjà répondu, puis un seul passage échoue : nuage, pas orage.
    lignes = [_ligne("a", MAINTENANT - timedelta(hours=3)), _ligne("a", MAINTENANT - timedelta(minutes=5), ok=False)]
    assert calculer(_config(["a"]), CONF_V, lignes, [], MAINTENANT)["fournisseurs"][0]["etat"] == "nuage"
    lignes.append(_ligne("a", MAINTENANT - timedelta(minutes=2), ok=False))
    assert calculer(_config(["a"]), CONF_V, lignes, [], MAINTENANT)["fournisseurs"][0]["etat"] == "orage"


def test_pages_de_statut_officielles(tmp_path):
    from sonde.statuts import produire_statuts
    resume = {"components": [{"id": "c1", "name": "AI & Machine Learning || AI Endpoint", "status": "partial_outage"},
                             {"id": "c2", "name": "Compute - Instance", "status": "major_outage"}]}
    incidents = {"incidents": [
        {"id": "i1", "name": "[GLOBAL][AI & Machine Learning] - AI Endpoint incident notification",
         "created_at": "2026-11-16T13:00:00.000Z", "resolved_at": None, "impact": "major",
         "shortlink": "https://stspg.io/x", "components": [{"id": "c1", "name": "AI Endpoint"}]},
        {"id": "i2", "name": "Instances lentes", "created_at": "2026-11-15T10:00:00Z", "resolved_at": "2026-11-15T11:00:00Z",
         "impact": "minor", "components": [{"id": "c2", "name": "Compute - Instance"}]},
        {"id": "i3", "name": "AI Endpoint ancien", "created_at": "2026-09-01T10:00:00Z", "resolved_at": "2026-09-01T11:00:00Z",
         "impact": "minor", "components": []},
    ]}

    def handler(req):
        if req.url.host == "panne.exemple":
            return httpx.Response(503)
        return httpx.Response(200, json=resume if req.url.path.endswith("summary.json") else incidents)

    config = {"fournisseurs": [
        {"id": "ovh", "statut": {"type": "statuspage", "url": "https://st.exemple", "motif": "AI Endpoint"}},
        {"id": "mistral", "statut": {"type": "lien", "url": "https://status.mistral.ai"}},
        {"id": "casse", "statut": {"type": "statuspage", "url": "https://panne.exemple", "motif": "x"}},
        {"id": "sans"},
    ]}
    client = httpx.Client(transport=httpx.MockTransport(handler))
    s = produire_statuts(config, tmp_path, client, MAINTENANT)["fournisseurs"]
    assert set(s) == {"ovh", "mistral", "casse"}
    assert s["ovh"]["etat_officiel"] == "Panne partielle" and s["ovh"]["incident_en_cours"]["lien"] == "https://stspg.io/x"
    assert [i["titre"] for i in s["ovh"]["incidents_30j"]] == ["[GLOBAL][AI & Machine Learning] - AI Endpoint incident notification"]
    assert s["mistral"] == {"type": "lien", "url": "https://status.mistral.ai"}
    assert "illisible" in s["casse"]["erreur"]
    assert json.loads((tmp_path / "statuts.json").read_text())["fournisseurs"]["ovh"]["gravite"] == 3


def test_assistants_mesures_a_la_porte(serveur, tmp_path):
    # Les assistants (Copilot, ChatGPT…) : toujours la porte d'entrée, même avec une clé, et 400 = debout.
    config = charger_yaml(RACINE / "config" / "fournisseurs.yaml")
    config["fournisseurs"] = []
    config["assistants"] = [
        {"id": "copilot", "nom": "Microsoft 365 Copilot", "nom_court": "Copilot", "categorie": "assistant",
         "porte_url": f"{serveur}/anonyme/v1/models"},
        {"id": "gemini", "nom": "Gemini", "categorie": "assistant", "porte_url": "http://127.0.0.1:9/x"},
    ]
    lignes = asyncio.run(veiller(config, CONF_V, tmp_path, env={"K": "x"}, point="test"))
    par = {l["fournisseur"]: l for l in lignes}
    assert par["copilot"]["succes"] and par["copilot"]["offre"] == "porte" and not par["gemini"]["succes"]
    m = calculer(config, CONF_V, lignes, [], datetime.fromisoformat(lignes[0]["horodatage"]))
    f = {x["id"]: x for x in m["fournisseurs"]}
    assert f["copilot"]["categorie"] == "assistant" and f["copilot"]["nom_court"] == "Copilot"


def test_dossier_client_complet(tmp_path):
    from sonde.dossier_client import assembler, ecrire
    donnees, public, preuves = tmp_path / "data", tmp_path / "public", tmp_path / "preuves"
    (donnees / "veille").mkdir(parents=True); public.mkdir()
    debut_panne, fin_panne = datetime(2026, 10, 14, 9, 42, tzinfo=timezone.utc), datetime(2026, 10, 14, 12, 54, tzinfo=timezone.utc)
    t, fin = datetime(2026, 10, 14, 0, 0, tzinfo=timezone.utc), datetime(2026, 10, 15, 0, 0, tzinfo=timezone.utc)
    lignes = []
    while t < fin:
        lignes.append(_ligne("nuage", t + timedelta(seconds=5), ok=not (debut_panne <= t < fin_panne)))
        t += timedelta(minutes=1)
    (donnees / "veille" / "2026-10-14.jsonl").write_text("\n".join(json.dumps(l) for l in lignes) + "\n")
    (public / "alertes.json").write_text(json.dumps([{"id": "nuage-orage-202610140943", "fournisseur": "nuage", "type": "orage",
                                                      "titre": "Orage sur Nuage", "horodatage": "2026-10-14T09:43:00+00:00"}]))
    (public / "retours.json").write_text(json.dumps({"par_alerte": {"nuage-orage-202610140943": {"touche": 7, "pas_touche": 2}}}))
    (public / "statuts.json").write_text(json.dumps({"fournisseurs": {"nuage": {"type": "statuspage", "incidents_30j": [
        {"titre": "API dégradée", "debut": "2026-10-14T10:35+00:00", "fin": "2026-10-14T12:50+00:00"}]}}}))
    config = {"fournisseurs": [{"id": "nuage", "nom": "Nuage IA"}]}
    contrats = {"contrats": {"nuage": {"service": "API Nuage", "engagement_pct": 99.9, "definition_panne": {"fenetre_min": 1},
                                       "paliers": [{"sous_pct": 99.9, "avoir_pct": 10}], "reclamation": {"delai_jours_apres_fin_mois": 30},
                                       "verifie": True}}}
    client = {"nom": "Cabinet Exemple", "factures": {"nuage": {"2026-10": 4800}}, "fonction_critique": True}
    d = assembler(donnees, public, preuves, config, contrats, client, "nuage", "2026-10",
                  maintenant=datetime(2026, 11, 16, tzinfo=timezone.utc))
    assert d["principale"]["duree_min"] == 192 and d["chronologies"][0]["reconnu"] and d["chronologies"][0]["retard_min"] == 53
    md = ecrire(d, tmp_path / "sortie").read_text()
    for attendu in ("Cabinet Exemple", "480,00 €", "7 membre(s) touché(s) sur 9", "« API dégradée »",
                    "Aide à la classification DORA", "plus de 2 heures | 3 h 12 | Oui", "SHA-256", "reconnue (53 min après le début)"):
        assert attendu in md, attendu
    assert "[NOM DE VOTRE ENTREPRISE]" not in md
