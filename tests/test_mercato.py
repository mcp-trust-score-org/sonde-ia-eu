import json
from pathlib import Path

from sonde.mercato import notification, nouveaux

T = {"entreprise": "Revolut", "date": "2026-11", "quitte": ["Anthropic", "OpenAI"], "pour": "GLM-5.3 (Z.ai, Chine)",
     "en_partie": True, "source": {"media": "IT for Business", "url": "https://ex.fr/r"}}


def test_premier_depot_ne_notifie_rien():
    assert nouveaux(None, {"transferts": [T]}) == []


def test_un_ajout():
    n = notification(nouveaux({"transferts": []}, {"transferts": [T]}))
    assert n["titre"] == "Le mercato de l'IA · Revolut quitte en partie Anthropic et OpenAI"
    assert "IT for Business" in n["texte"] and n["url"] == "/?mercato=1#une"


def test_sans_source_ou_deja_vu():
    sans = {**T, "entreprise": "X", "source": {}}
    assert nouveaux({"transferts": [T]}, {"transferts": [T, sans]}) == []


def test_plusieurs_ajouts_une_seule_notification():
    u = {**T, "entreprise": "Ecosia", "pour": "Qwen"}
    n = notification(nouveaux({"transferts": []}, {"transferts": [T, u]}))
    assert n["titre"].endswith("2 nouveaux transferts") and "Revolut, Ecosia" in n["texte"]


def test_fichier_du_site_valide():
    d = json.loads((Path(__file__).parent.parent / "iris" / "mercato.json").read_text(encoding="utf-8"))
    for x in d["transferts"]:
        assert x["source"]["url"].startswith("https://") and x["entreprise"] and x["pour"] and x["dit"]
