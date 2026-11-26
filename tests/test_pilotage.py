"""Le tableau de pilotage : charte du jour, état des brouillons, passages de la sonde."""

import json
from datetime import date, datetime, timezone

from sonde.pilotage import attendus, redaction, sonde

RYTHME = {"une": {"bilan_le": 0}, "tous_connectes": {"jours": [0, 2, 4, 5], "reflexe_de_la_semaine": 0}, "detour": {"jours": [1, 4]}}


def test_attendus():
    lundi = [a["rubrique"] for a in attendus(date(2026, 12, 7), RYTHME)]       # premier lundi du mois
    assert lundi == ["une", "tous_connectes", "et_si"]
    assert [a["rubrique"] for a in attendus(date(2026, 11, 29), RYTHME)] == ["une", "meteo_semaine"]   # dimanche
    assert attendus(date(2026, 11, 24), RYTHME)[0]["optionnel"]                 # mardi : À chaud seulement s'il y a un incident


def test_etats(tmp_path):
    d = tmp_path / "redaction" / "propositions"
    d.mkdir(parents=True)
    (d / "2026-11-23.json").write_text(json.dumps({"propositions": [
        {"rubrique": "une", "statut": "publie"}, {"rubrique": "tous_connectes", "alertes_charte": ["x"]}]}))
    (d / "2026-11-25.json").write_text(json.dumps({"propositions": [{"rubrique": "tous_connectes"}]}))
    jours = {j["date"]: {l["rubrique"]: l["etat"] for l in j["lignes"]}
             for j in redaction(tmp_path, date(2026, 11, 25), RYTHME, avant=4, apres=1, suivi_depuis="2026-11-23")}
    assert jours["2026-11-22"]["une"] == "avant le lancement"
    assert jours["2026-11-23"] == {"une": "publié", "tous_connectes": "non publié"}   # jour passé, jamais publié
    assert jours["2026-11-24"]["detour"] == "rédaction pas lancée"
    assert jours["2026-11-25"]["tous_connectes"] == "brouillon prêt"
    assert jours["2026-11-26"]["une"] == "à venir"


def test_sonde_interruptions(tmp_path):
    v = tmp_path / "data" / "veille"
    v.mkdir(parents=True)
    lignes = [{"type": "veille", "fournisseur": "mistral", "horodatage": h, "succes": True}
              for h in ("2026-11-22T08:00:00+00:00", "2026-11-22T08:10:00+00:00", "2026-11-22T13:00:00+00:00")]
    (v / "2026-11-22.jsonl").write_text("\n".join(json.dumps(l) for l in lignes))
    (tmp_path / "data" / "2026-11.jsonl").write_text(json.dumps({"type": "mesure", "horodatage": "2026-11-22T12:17:00+00:00", "execution": "a"}))
    s = sonde(tmp_path, datetime(2026, 11, 22, 13, 30, tzinfo=timezone.utc), jours=1)
    assert s["veille"]["etat"] == "ok" and s["mesure"]["etat"] == "ok"
    assert [t["heures"] for t in s["interruptions"]] == [4.8]
    assert s["jours"][-1]["veille"] == 3 and s["jours"][-1]["mesures"] == 1


def test_publies_font_foi(tmp_path):
    """Un article en ligne compte comme publié, même si son brouillon n'a jamais été marqué (dépôt à la main)."""
    d = tmp_path / "redaction" / "propositions"
    d.mkdir(parents=True)
    (d / "2026-11-25.json").write_text(json.dumps({"propositions": [{"rubrique": "tous_connectes"}]}))
    (tmp_path / "iris").mkdir()
    (tmp_path / "iris" / "publies.json").write_text(json.dumps({
        "une": [{"date": "2026-11-26", "title": "Quatre clouds.<br/>Des <mark>puces</mark>."}],
        "tous_connectes": [{"date": "2026-11-25", "title": "Un sur cinq"}],
        "detour": [{"date": "2026-11-24", "url": "https://x"}]}))
    jours = {j["date"]: {l["rubrique"]: l for l in j["lignes"]}
             for j in redaction(tmp_path, date(2026, 11, 26), RYTHME, avant=2, apres=0)}
    assert jours["2026-11-25"]["tous_connectes"]["etat"] == "publié"      # et non « non publié »
    assert jours["2026-11-24"]["detour"]["etat"] == "publié"
    assert jours["2026-11-26"]["une"]["etat"] == "publié"                 # et non « rien (pas d'incident) »
    assert jours["2026-11-26"]["une"]["titre"] == "Quatre clouds. Des puces."


def test_a_chaud_non_publie_nest_pas_un_rate(tmp_path):
    d = tmp_path / "redaction" / "propositions"
    d.mkdir(parents=True)
    (d / "2026-11-24.json").write_text(json.dumps({"propositions": [{"rubrique": "une"}]}))   # mardi : À chaud facultatif
    jours = {j["date"]: {l["rubrique"]: l["etat"] for l in j["lignes"]}
             for j in redaction(tmp_path, date(2026, 11, 26), RYTHME, avant=2, apres=0)}
    assert jours["2026-11-24"]["une"] == "non retenu"
