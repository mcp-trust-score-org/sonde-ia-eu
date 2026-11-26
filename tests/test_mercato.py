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


def test_signature():
    sig = {**T, "entreprise": "Les Mousquetaires", "quitte": [], "pour": "Claude (Anthropic, États-Unis)",
           "comment": "Via AWS", "source": {"media": "LSA", "url": "https://ex.fr/m"}}
    n = notification(nouveaux({"transferts": []}, {"transferts": [sig]}))
    assert n["titre"] == "Le mercato de l'IA · Les Mousquetaires signe avec Claude (Anthropic, États-Unis)"
    assert n["texte"] == "Via AWS. Source : LSA."


def test_officiel_dans_la_notification():
    sig = {**T, "entreprise": "Groupement Mousquetaires", "quitte": [], "pour": "Claude (Anthropic, États-Unis)",
           "comment": "Via AWS", "annonce": "entreprise", "source": {"media": "LSA", "url": "https://ex.fr/m"}}
    n = notification(nouveaux({"transferts": []}, {"transferts": [sig]}))
    assert n["titre"] == "Le mercato de l'IA · OFFICIEL · Groupement Mousquetaires signe avec Claude (Anthropic, États-Unis)"


def test_annonce_renseignee():
    d = json.loads((Path(__file__).parent.parent / "iris" / "mercato.json").read_text(encoding="utf-8"))
    assert all(x.get("annonce") in ("entreprise", "presse") for x in d["transferts"])


def test_fournisseurs_et_point():
    from datetime import date
    from sonde.mercato import fournisseurs_de, point_du_vendredi
    from sonde.cartes import identifiant
    sig = {"entreprise": "Groupement Mousquetaires", "date": "2026-11", "quitte": [], "pour": "Claude (Anthropic, États-Unis)",
           "source": {"media": "LSA", "date": "2026-11-25", "url": "https://ex.fr/m"}}
    rev = {"entreprise": "Revolut", "date": "2026-11", "quitte": ["Anthropic", "OpenAI"], "pour": "GLM-5.3 (Z.ai, Chine)",
           "source": {"media": "IT for Business", "date": "2026-11-05", "url": "https://ex.fr/r"}}
    assert fournisseurs_de(sig) == ["anthropic"] and fournisseurs_de(rev) == ["anthropic", "openai"]
    n = point_du_vendredi({"transferts": [sig, rev]}, date(2026, 11, 27))
    assert n["titre"] == "Le point mercato · semaine 48"
    assert n["texte"] == "C'est signé : Groupement Mousquetaires × Claude. La semaine en 2 min."
    assert point_du_vendredi({"transferts": [rev]}, date(2026, 11, 27)) is None      # rien cette semaine : rien
    assert identifiant(sig) == "groupement-mousquetaires-2026-11-claude-anthropic-etats-unis"
