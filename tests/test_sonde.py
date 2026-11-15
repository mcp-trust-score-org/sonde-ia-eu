import asyncio
import json
import socket
import threading
import time
from pathlib import Path

import pytest
import uvicorn

from sonde.mesure import charger_yaml, choisir_taches, executer, resoudre_modele
from sonde.rapport import produire
from sonde.verifications import verifier

from .faux_serveur import BONNES_REPONSES, app

RACINE = Path(__file__).resolve().parent.parent
TACHES = charger_yaml(RACINE / "config" / "taches.yaml")["taches"]


# ------------------------------------------------------------------ vérifications

def test_chaque_bonne_reponse_passe_sa_verification():
    for t in TACHES:
        assert verifier(BONNES_REPONSES[t["id"]], t["verification"]), t["id"]


@pytest.mark.parametrize("tache_id, mauvaise", [
    ("calcul-abonnement", "149"),
    ("raisonnement-ages", "15"),
    ("extraction-json", '{"nom": "Claire Dubois", "ville": "Paris"}'),
    ("classification-client", "facturation"),
    ("format-trois-lignes", "1. Fraise\n2. Cerise\n3. Framboise\n4. Tomate"),
    ("date-jour-semaine", "Lundi"),
    ("code-python", "def pair(n): return n & 1 == 0"),
])
def test_mauvaises_reponses_rejetees(tache_id, mauvaise):
    t = next(t for t in TACHES if t["id"] == tache_id)
    assert not verifier(mauvaise, t["verification"])


def test_nombre_avec_espace_et_virgule():
    assert verifier("Environ 1 234,50 €", {"type": "nombre", "valeur": 1234.5})


# ------------------------------------------------------------------ résolution des modèles

def test_resolution_insensible_aux_separateurs():
    mod = {"id": "llama-3.3-70b", "motifs": ["llama-3.3-70b-instruct"]}
    assert resoudre_modele(mod, "ovh", ["Meta-Llama-3_3-70B-Instruct", "x"]) == "Meta-Llama-3_3-70B-Instruct"
    assert resoudre_modele(mod, "ionos", ["meta-llama/Llama-3.3-70B-Instruct"]) == "meta-llama/Llama-3.3-70B-Instruct"
    assert resoudre_modele(mod, "autre", ["mistral-small-2506"]) is None


def test_resolution_exacte():
    mod = {"id": "m", "motifs": ["zzz"], "exact": {"mistral": "mistral-small-2506"}}
    assert resoudre_modele(mod, "mistral", ["mistral-small-2506"]) == "mistral-small-2506"
    assert resoudre_modele(mod, "mistral", ["autre"]) is None


def test_rotation_couvre_toutes_les_taches():
    vues = set()
    for heure in range(len(TACHES)):
        vues |= {t["id"] for t in choisir_taches(TACHES, 3, heure)}
    assert vues == {t["id"] for t in TACHES}


# ------------------------------------------------------------------ bout en bout

@pytest.fixture(scope="module")
def serveur():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    srv = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    th = threading.Thread(target=srv.run, daemon=True)
    th.start()
    while not srv.started:
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    srv.should_exit = True
    th.join(timeout=5)


def test_bout_en_bout(serveur, tmp_path):
    config = charger_yaml(RACINE / "config" / "fournisseurs.yaml")
    config["fournisseurs"] = [
        {"id": p, "nom": p, "pays": "FR", "base_url": f"{serveur}/{p}/v1", "cle_env": f"CLE_{p.upper()}"}
        for p in ["rapide", "lent", "panne", "strict", "catako", "sanscle"]
    ]
    config["prix"] = {"rapide": {"llama-3.3-70b": {"entree": 1.0, "sortie": 2.0}}}
    env = {f"CLE_{p.upper()}": "x" for p in ["rapide", "lent", "panne", "strict", "catako"]}

    lignes = asyncio.run(executer(config, TACHES, tmp_path / "data", env=env))
    mesures = [l for l in lignes if l["type"] == "mesure"]

    def de(prov, modele="llama-3.3-70b"):
        return [m for m in mesures if m["fournisseur"] == prov and m["modele"] == modele]

    # 2 modèles présents au catalogue × 11 tâches × 4 fournisseurs qui répondent au catalogue
    assert len(mesures) == 2 * len(TACHES) * 4
    assert all(m["succes"] and m["qualite_ok"] for m in de("rapide"))
    assert all(m["cout_eur"] for m in de("rapide"))
    assert all(not m["succes"] and m["statut_http"] == 503 for m in de("panne"))
    # Le fournisseur strict refuse stream_options : la sonde réessaie sans, et estime les jetons.
    assert all(m["succes"] and m["jetons_estimes"] for m in de("strict"))
    lent = de("lent")
    assert min(m["ttft_ms"] for m in lent) >= 290
    assert sum(not m["qualite_ok"] for m in lent) == 1
    # Mistral Small absent partout, catalogue en erreur signalé, fournisseur sans clé ignoré
    assert any(l["type"] == "absent" and l["modele"] == "mistral-small-3.2" for l in lignes)
    assert any(l["type"] == "catalogue" and l["fournisseur"] == "catako" and l["erreur"] for l in lignes)
    assert not any(l.get("fournisseur") == "sanscle" for l in lignes)

    # Le rapport classe un fournisseur sans faute premier (rapide et strict sont à égalité
    # sur la dispo et la qualité, la vitesse les départage) et le fournisseur en panne dernier.
    md = produire(tmp_path / "data", tmp_path / "public", jours=1)
    resume = json.loads((tmp_path / "public" / "resume.json").read_text(encoding="utf-8"))
    llama = [r for r in resume["resultats"] if r["modele"] == "llama-3.3-70b"]
    assert {r["fournisseur"]: r["disponibilite_pct"] for r in llama}["panne"] == 0.0
    # Un catalogue en panne est un incident, pas un "modèle absent".
    assert "catako" in resume["incidents_catalogue"]
    assert not any(f == "catako" for f, _ in resume["absents"])
    section = md.split("## llama-3.3-70b")[1].split("##")[0]
    rangs = [l for l in section.splitlines() if l.startswith("| 1 ") or l.startswith("| 4 ")]
    assert ("rapide" in rangs[0] or "strict" in rangs[0]) and "panne" in rangs[1]
    print(md)


def test_changement_de_catalogue_detecte(tmp_path):
    d = tmp_path / "data"
    d.mkdir()
    lignes = [
        {"type": "catalogue", "horodatage": "2099-01-01T00:00:00+00:00", "fournisseur": "ovh", "modeles": ["a", "b"], "erreur": None},
        {"type": "catalogue", "horodatage": "2099-01-01T01:00:00+00:00", "fournisseur": "ovh", "modeles": ["a", "c"], "erreur": None},
    ]
    (d / "2099-01.jsonl").write_text("\n".join(json.dumps(l) for l in lignes), encoding="utf-8")
    produire(d, tmp_path / "public", jours=1)
    resume = json.loads((tmp_path / "public" / "resume.json").read_text(encoding="utf-8"))
    assert resume["changements_catalogue"] == [
        {"fournisseur": "ovh", "horodatage": "2099-01-01T01:00:00+00:00", "ajoutes": ["c"], "retires": ["b"]}
    ]


def test_mode_anonyme_avec_catalogue_de_secours_et_pause(serveur, tmp_path):
    config = charger_yaml(RACINE / "config" / "fournisseurs.yaml")
    config["fournisseurs"] = [{
        "id": "anonyme", "nom": "anonyme", "pays": "FR", "base_url": f"{serveur}/anonyme/v1",
        "cle_env": "CLE_ABSENTE", "anonyme_si_sans_cle": True, "pause_anonyme_s": 0.2,
        "catalogue_secours": ["gpt-oss-120b"],
    }]
    taches = TACHES[:3]
    debut = time.perf_counter()
    lignes = asyncio.run(executer(config, taches, tmp_path / "data", env={}))
    duree = time.perf_counter() - debut
    mesures = [l for l in lignes if l["type"] == "mesure"]
    assert len(mesures) == 3 and all(m["succes"] and m["offre"] == "anonyme" for m in mesures)
    assert duree >= 0.55   # 3 appels espacés de 0,2 s, pas en parallèle
    cat = next(l for l in lignes if l["type"] == "catalogue")
    assert cat["erreur"] and cat["secours"]

    md = produire(tmp_path / "data", tmp_path / "public", jours=1)
    resume = json.loads((tmp_path / "public" / "resume.json").read_text(encoding="utf-8"))
    assert "anonyme (anonyme)" in md               # l'offre est affichée à côté du fournisseur
    assert resume["incidents_catalogue"] == {}      # un catalogue fermé sans clé n'est pas une panne
