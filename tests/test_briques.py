import asyncio
import json
from pathlib import Path

import pytest

from sonde import chemin as chemin_mod
from sonde.chemin import classer_operateur, intermediaires_depuis_entetes, tracer, verdict
from sonde.dossier import construire, en_markdown
from sonde.empreinte import comparer, executer_empreintes, juger, similarite, suivi
from sonde.horodatage import ancrer, ecrire_manifeste, verifier_manifeste
from sonde.mesure import charger_yaml
from sonde.rapport_public import brouillon

from . import faux_serveur
from .test_sonde import RACINE, serveur  # noqa: F401  (fixture partagée)


# ------------------------------------------------------------------ chemin réseau

def test_classement_des_operateurs():
    assert classer_operateur("CLOUDFLARENET - Cloudflare, Inc.") == ("Cloudflare", "US")
    assert classer_operateur("OVH SAS") == ("OVHcloud", "FR")
    assert classer_operateur("Inconnu SARL") == (None, None)


def test_intermediaires_detectes_dans_les_entetes():
    assert intermediaires_depuis_entetes({"CF-RAY": "x", "Server": "cloudflare"}) == ["Cloudflare"]
    assert intermediaires_depuis_entetes({"Via": "1.1 abc.cloudfront.net (CloudFront)"}) == ["Amazon CloudFront"]
    assert intermediaires_depuis_entetes({"server": "nginx"}) == []


def test_verdicts():
    ue = [{"ip": "1", "pays_operateur": "FR", "pays_ip": "FR", "operateur": "OVHcloud"}]
    us = [{"ip": "2", "pays_operateur": "US", "pays_ip": "NL", "operateur": "Cloudflare"}]
    assert verdict(ue, [])[0] == "ue_observe"
    assert verdict(us, [])[0] == "intermediaire_non_ue"
    assert verdict(ue, ["Cloudflare"])[0] == "intermediaire_non_ue"
    assert verdict([], [])[0] == "indetermine"


def test_trace_bout_en_bout(serveur, monkeypatch):  # noqa: F811
    monkeypatch.setattr(chemin_mod, "RIPESTAT", f"{serveur}/ripe/data")
    ips = {"127.0.0.1": None}
    monkeypatch.setattr(chemin_mod, "resoudre", lambda hote: ["51.0.0.1"] if "ue" in ips else ["104.16.0.1"])
    config = {"fournisseurs": [{"id": "cdn", "base_url": f"{serveur}/cdn/v1"}]}
    lignes = asyncio.run(tracer(config, point_de_mesure="test"))
    l = lignes[0]
    assert l["ips"][0]["operateur"] == "Cloudflare" and l["ips"][0]["pays_ip"] == "US"
    assert l["intermediaires"] == ["Cloudflare"]
    assert l["verdict"] == "intermediaire_non_ue"
    ips["ue"] = True
    config = {"fournisseurs": [{"id": "rapide", "base_url": f"{serveur}/rapide/v1"}]}
    l = asyncio.run(tracer(config))[0]
    assert l["verdict"] == "ue_observe" and l["ips"][0]["operateur"] == "OVHcloud"


# ------------------------------------------------------------------ empreinte

REG = {"seuil_absolu": 0.55, "marge_mad": 4, "confirmations": 2, "historique_min": 3, "max_tokens": 80, "temperature": 0}


def test_similarite_et_comparaison():
    assert similarite("Bonjour à tous", "bonjour a tous") == 1.0
    assert similarite("abc", "xyz") < 0.2
    assert comparer({"a": "un texte", "b": "deux"}, {"a": "un texte", "c": "x"}) == 1.0


def test_jugement_par_historique_et_confirmation():
    assert juger([0.95, 0.96, 0.94], 0.95, REG) == (False, "")
    assert juger([0.95, 0.96, 0.94], 0.80, REG)[0]          # sous la variation normale
    assert juger([], 0.40, REG)[0]                           # sous le seuil absolu
    prec = [{"similarite_reference": x, "anormale": False} for x in (0.95, 0.96, 0.94)]
    s1 = suivi(prec, 0.5, REG)
    assert s1["anormale"] and not s1["alerte"]               # une seule anomalie : pas encore d'alerte
    s2 = suivi(prec + [{"similarite_reference": 0.5, **s1}], 0.5, REG)
    assert s2["alerte"]                                      # confirmée


def test_empreinte_detecte_un_changement_silencieux(serveur):  # noqa: F811
    config = charger_yaml(RACINE / "config" / "fournisseurs.yaml")
    config["fournisseurs"] = [{"id": "rapide", "nom": "r", "base_url": f"{serveur}/rapide/v1", "cle_env": "K"}]
    conf = charger_yaml(RACINE / "config" / "empreinte.yaml")
    conf["sondes"] = conf["sondes"][:3]
    env, toutes = {"K": "x"}, []

    def tour():
        lignes = asyncio.run(executer_empreintes(config, conf, list(toutes), env))
        toutes.extend(lignes)
        return {l["modele"]: l for l in lignes}

    faux_serveur.ETAT["derive"] = False
    t1 = tour()
    assert all(l["est_reference"] for l in t1.values())
    for _ in range(3):
        t = tour()
        assert all(l["similarite_reference"] == 1.0 and not l["alerte"] for l in t.values())
    faux_serveur.ETAT["derive"] = True
    t = tour()
    assert all(l["anormale"] and not l["alerte"] for l in t.values())
    t = tour()
    assert all(l["alerte"] for l in t.values())
    faux_serveur.ETAT["derive"] = False


# ------------------------------------------------------------------ horodatage

def test_manifeste_verifiable_et_resistant_a_l_ajout(tmp_path):
    d = tmp_path / "data"
    d.mkdir()
    f = d / "2099-01.jsonl"
    f.write_text('{"a": 1}\n{"a": 2}\n', encoding="utf-8")
    m = ecrire_manifeste(d, tmp_path / "preuves")
    with open(f, "a", encoding="utf-8") as h:          # les mesures continuent de s'ajouter
        h.write('{"a": 3}\n')
    assert verifier_manifeste(m, d) == {"2099-01.jsonl": True}
    f.write_text('{"a": 1}\n{"a": 999}\n{"a": 3}\n', encoding="utf-8")   # falsification
    assert verifier_manifeste(m, d) == {"2099-01.jsonl": False}


def test_ancrage_sans_client_ots_ne_plante_pas(tmp_path, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: None)
    p = tmp_path / "m.json"
    p.write_text("{}")
    assert "ots absent" in ancrer(p)


# ------------------------------------------------------------------ dossier et rapport

def _lignes_synthetiques():
    h = "2099-01-01T{:02d}:17:00+00:00"
    lignes = []
    for i in range(6):
        for prov, ok in (("ovhcloud", i != 2 and i != 3), ("scaleway", True)):
            lignes.append({"type": "mesure", "horodatage": h.format(i), "fournisseur": prov, "modele": "gpt-oss-120b",
                           "succes": ok, "ttft_ms": 800.0 if ok else None, "duree_ms": 1500.0 if ok else None,
                           "jetons_par_s": 60.0 if ok else None, "qualite_ok": True if ok else None,
                           "cout_eur": None, "erreur": None if ok else "HTTP 503", "offre": "anonyme" if prov == "ovhcloud" else "payante"})
    lignes.append({"type": "chemin", "horodatage": h.format(1), "fournisseur": "ovhcloud", "point_de_mesure": "test",
                   "ips": [{"ip": "51.0.0.1", "pays_ip": "FR", "operateur": "OVHcloud", "titulaire": "OVH SAS", "pays_operateur": "FR"}],
                   "intermediaires": [], "verdict": "ue_observe", "constats": ["Toutes les entrées réseau observées sont dans l'UE/EEE"]})
    lignes.append({"type": "empreinte", "horodatage": h.format(2), "fournisseur": "ovhcloud", "modele": "gpt-oss-120b",
                   "similarite_reference": 0.4, "alerte": True, "raison": "test", "modele_id_change": False})
    return lignes


def test_dossier_complet():
    d = construire("ovhcloud", _lignes_synthetiques())
    p = d["performance"][0]
    assert p["disponibilite_pct"] == pytest.approx(66.67) and p["plus_longue_serie_echecs_h"] == 2
    assert d["reseau"]["verdict"] == "ue_observe"
    assert d["stabilite"][0]["alertes"]
    assert d["substituabilite"][0]["alternatives_mesurees"][0]["fournisseur"] == "scaleway"
    md = en_markdown(d)
    for titre in ("Correspondance réglementaire", "B_07.01", "## 2. Chemin réseau", "## 4. Substituabilité", "à compléter"):
        assert titre in md


def test_brouillon_du_rapport_public(tmp_path, monkeypatch):
    d = tmp_path / "data"
    d.mkdir()
    (d / "2099-01.jsonl").write_text("\n".join(json.dumps(l) for l in _lignes_synthetiques()), encoding="utf-8")
    import sonde.rapport_public as rp
    monkeypatch.setattr(rp, "datetime", type("D", (), {"now": staticmethod(lambda tz=None: __import__("datetime").datetime(2099, 1, 2, tzinfo=tz))}))
    texte = brouillon(d, tmp_path / "preuves", jours=30)
    assert "[À COMMENTER]" in texte and "gpt-oss-120b" in texte and "Par où passent" in texte


def test_alerte_envoyee_aux_appareils_abonnes():
    """Avec NOTIF_SECRET, une alerte part aussi vers le site (sujet « alertes »)."""
    import json as _json
    import httpx
    from sonde.alertes import envoyer
    recus = []

    def repondre(req):
        recus.append((str(req.url), req.headers.get("authorization"), _json.loads(req.content)))
        return httpx.Response(200, json={"envoyes": 1})

    client = httpx.Client(transport=httpx.MockTransport(repondre))
    alerte = {"titre": "Orage sur OVHcloud", "texte": "Panne. Dossier : `python -m sonde avoirs`.", "niveau": "rouge",
              "type": "orage", "id": "ovhcloud-orage-1"}
    faits = envoyer(alerte, {"NOTIF_SECRET": "s", "SITE_URL": "https://iris.example/"}, client)
    assert faits == ["site"]
    url, auth, corps = recus[0]
    assert url == "https://iris.example/api/notifier" and auth == "Bearer s"
    assert corps["sujet"] == "alertes" and corps["url"] == "/#alertes" and "`" not in corps["texte"]
    assert envoyer(alerte, {}, client) == []          # sans secret : rien n'est envoyé au site
