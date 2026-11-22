"""La série « Et si… ? » d'Iris Plus (réseau et rédacteur simulés)."""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import httpx

from sonde.et_si import a_reverifier, choisir, controler_et_si, jour_du_et_si, preparer
from sonde.mesure import RACINE
from sonde.redaction import PARIS, en_markdown

PREMIER_LUNDI = datetime(2026, 12, 7, 3, 41, tzinfo=timezone.utc)
PAGE = "<html><body><article>" + "".join(
    f"<p>Paragraphe {i} : le modèle tourne sur le téléphone sans connexion, pour de petites tâches seulement.</p>"
    for i in range(12)) + "</article></body></html>"
TEND = {"detour": [{"media": "Next", "titre": "L'IA locale arrive sur les téléphones, même hors ligne",
                    "url": "https://next.ink/ia-locale", "date": "2026-12-03T10:00+00:00"}],
        "presse": [{"media": "franceinfo", "titre": "Une panne géante de satellite", "url": "https://franceinfo.fr/sat",
                    "date": "2026-12-04T10:00+00:00"}]}
ARTICLE = {
    "tag": "Et si… ?", "title": "Et si votre IA marchait même quand Internet tombe ?",
    "chapo": "Fin novembre, un service d'IA est tombé pendant des heures. Et si l'IA tournait sur le téléphone ?",
    "et_si": ["La sonde d'Iris a vu un service d'IA en panne."],
    "existe_deja": ["Des modèles tournent déjà sur le téléphone."],
    "ca_coince": ["Il faut un téléphone récent.", "La batterie se vide vite."],
    "vraie_question": ["Qu'attend-on vraiment d'une IA le jour d'une panne ?", "Que gagne-t-on à tout confier au cloud ?"],
    "geste": "Mettez votre téléphone en mode avion et testez votre assistant.",
    "sources": [{"label": "Next : l'IA locale", "url": "https://next.ink/ia-locale"}],
}


class Redacteur:
    actif, modele = True, "faux-modele"

    def __init__(self, article=None):
        self.article, self.consignes = article or ARTICLE, []

    def ecrire(self, consigne, fiche, rubrique=None):
        self.consignes.append((consigne, fiche, rubrique))
        if "revérification" in consigne:
            return {"change": True, "ce_qui_a_change": ["Un nouveau modèle est sorti."], "faits_a_retirer": [],
                    "sources": [{"label": "Next", "url": "https://next.ink/ia-locale"}]}
        return self.article


def _client():
    return httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(200, text=PAGE,
                                                                                 headers={"content-type": "text/html"})))


def _racine(tmp_path: Path) -> Path:
    (tmp_path / "config").mkdir()
    shutil.copy(RACINE / "config" / "et-si.yaml", tmp_path / "config" / "et-si.yaml")
    (tmp_path / "redaction").mkdir()
    (tmp_path / "iris" / "donnees").mkdir(parents=True)
    (tmp_path / "iris" / "donnees" / "alertes.json").write_text(json.dumps([
        {"fournisseur": "ovhcloud", "type": "orage", "texte": "OVHcloud AI Endpoints est en panne.",
         "horodatage": "2026-11-27T17:51:00+00:00"}]))
    return tmp_path


def test_premier_lundi_du_mois_seulement():
    r = {"jour": 0, "semaine_du_mois": 1}
    assert jour_du_et_si(PREMIER_LUNDI, r)
    assert not jour_du_et_si(PREMIER_LUNDI.replace(day=14), r)      # deuxième lundi
    assert not jour_du_et_si(PREMIER_LUNDI.replace(day=8), r)       # mardi


def test_le_sujet_suit_l_actualite():
    reserve = [{"id": "satellite", "question": "Et si… ?", "mots_cles": ["satellite"]},
               {"id": "edge", "question": "Et si… ?", "mots_cles": ["hors ligne", "ia locale"], "panne_mesuree": True}]
    sujet, acc, alertes = choisir(reserve, {"sujets": {}}, TEND, pannes=[{"fournisseur": "ovhcloud"}])
    assert sujet["id"] == "edge" and acc[0]["url"] == "https://next.ink/ia-locale" and not alertes
    # Un sujet déjà proposé n'est jamais reproposé.
    sujet, _, _ = choisir(reserve, {"sujets": {"edge": {}}}, TEND, pannes=[])
    assert sujet["id"] == "satellite"
    # La rédaction peut imposer le sujet du mois.
    sujet, _, _ = choisir(reserve, {"sujets": {}}, TEND, pannes=[], prochain="satellite")
    assert sujet["id"] == "satellite"
    # Sans accroche, le brouillon le signale.
    _, _, alertes = choisir(reserve, {"sujets": {}}, {}, pannes=[])
    assert "Aucune accroche" in alertes[0]


def test_brouillon_du_mois_et_etat(tmp_path):
    racine = _racine(tmp_path)
    red = Redacteur()
    props = preparer(red, _client(), racine, TEND, PREMIER_LUNDI.astimezone(PARIS), PREMIER_LUNDI, {"actif": True})
    assert [p["rubrique"] for p in props] == ["et_si"]
    p = props[0]
    assert p["sujet"] == "post-quantique"           # imposé par le programme du 7 décembre
    assert p["fiche"]["pannes_mesurees_par_la_sonde"][0]["fournisseur"] == "ovhcloud"
    assert "AUCUN avis" in red.consignes[0][0] and red.consignes[0][2] == "et_si"
    assert any("pas encore de sources de base" in a for a in p["alertes_charte"])
    etat = json.loads((racine / "redaction" / "et-si.json").read_text())
    assert etat["sujets"]["post-quantique"]["propose_le"] == "2026-12-07"
    md = en_markdown({"date": "2026-12-07", "propositions": props})
    assert "Et si… ? (Iris Plus)" in md and "**La vraie question**" in md and "**Le geste**" in md
    # Un autre jour du mois : rien.
    assert preparer(red, _client(), racine, TEND, PREMIER_LUNDI.replace(day=9), PREMIER_LUNDI, {"actif": True}) == []


def test_controles_sans_avis():
    fiche = {"sources_de_base": [], "accroches": [{"url": "https://next.ink/ia-locale", "etat": "lu"}]}
    assert controler_et_si(ARTICLE, fiche) == []
    avis = {**ARTICLE, "vraie_question": ["Il faut garder une IA sur son téléphone.", "Et vous ?"],
            "sources": [{"label": "Inventé", "url": "https://invente.example"}], "title": "L'IA hors ligne"}
    alertes = " | ".join(controler_et_si(avis, fiche))
    assert "Le titre doit être une question" in alertes
    assert "chaque phrase doit être une question" in alertes
    assert "Point de vue" in alertes and "il faut" in alertes.lower()
    assert "lien inventé" in alertes
    assert "Partie manquante : Le geste" in " | ".join(controler_et_si({**ARTICLE, "geste": ""}, fiche))


def test_reverification_six_mois_apres(tmp_path):
    racine = _racine(tmp_path)
    (racine / "redaction" / "et-si.json").write_text(json.dumps({"sujets": {"edge": {
        "question": "Et si votre IA marchait même quand Internet tombe ?", "propose_le": "2026-06-01",
        "verifie_le": "2026-06-01", "sources": ["https://docs.mistral.ai/models/ministral-3-3b-25-12"], "article": ARTICLE}}}))
    jour = datetime(2026, 12, 9, 3, 41, tzinfo=timezone.utc)
    assert a_reverifier(json.loads((racine / "redaction" / "et-si.json").read_text()), jour, 182) == "edge"
    props = preparer(Redacteur(), _client(), racine, TEND, jour, jour, {"actif": True})
    assert [p["rubrique"] for p in props] == ["et_si_verif"]
    assert props[0]["article"]["ce_qui_a_change"] == ["Un nouveau modèle est sorti."]
    md = en_markdown({"date": "2026-12-09", "propositions": props})
    assert "Ce qui a changé depuis" in md
    # La date de vérification est remise à jour : pas de nouvelle revérification le lendemain.
    etat = json.loads((racine / "redaction" / "et-si.json").read_text())
    assert etat["sujets"]["edge"]["verifie_le"] == "2026-12-09"
    assert preparer(Redacteur(), _client(), racine, TEND, jour.replace(day=10), jour, {"actif": True}) == []
