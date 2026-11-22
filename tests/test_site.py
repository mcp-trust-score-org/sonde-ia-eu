"""Données du site (iris/donnees) et durée réelle des fins d'orage."""

import json
from pathlib import Path

from sonde.alertes import duree_depuis_orage
from sonde.site import produire

JOURNAL = [
    {"fournisseur": "ovhcloud", "type": "fin_orage", "horodatage": "2026-11-21T16:26:00+00:00", "texte": "… après 57 minutes de panne."},
    {"fournisseur": "ovhcloud", "type": "orage", "horodatage": "2026-11-21T15:27:00+00:00", "texte": "Orage."},
    {"fournisseur": "ovhcloud", "type": "fin_orage", "horodatage": "2026-11-21T08:48:00+00:00", "texte": "… après 57 minutes de panne."},
    {"fournisseur": "ovhcloud", "type": "orage", "horodatage": "2026-11-21T07:10:00+00:00", "texte": "Orage."},
]
METEO = {"genere_le": "2026-11-21T21:45:00+00:00", "fournisseurs": [{"id": "ovhcloud", "nom": "OVHcloud AI Endpoints", "incidents_30j": [{"duree_min": 57}]}]}


def test_duree_depuis_l_orage_qui_a_ouvert_la_panne():
    assert duree_depuis_orage(JOURNAL[0], JOURNAL) == 59
    assert duree_depuis_orage(JOURNAL[2], JOURNAL) == 98


def test_site_copie_et_corrige(tmp_path: Path):
    (tmp_path / "public").mkdir()
    (tmp_path / "public" / "alertes.json").write_text(json.dumps(JOURNAL))
    (tmp_path / "public" / "meteo.json").write_text(json.dumps(METEO))
    (tmp_path / "dossiers").mkdir()
    (tmp_path / "dossiers" / "ovhcloud.json").write_text(json.dumps({"fournisseur": {"id": "ovhcloud", "nom": "OVHcloud"}, "genere_le": "2026-11-21"}))
    (tmp_path / "preuves").mkdir()
    (tmp_path / "preuves" / "2026-11-21.json").write_text(json.dumps({"fichiers": {"a": {}, "b": {}}}))
    (tmp_path / "preuves" / "2026-11-21.json.ots").write_text("x")
    res = produire(tmp_path)
    assert res["copies"] == ["meteo.json", "alertes.json"] and res["dossiers"] == 1 and res["preuves"] == 1
    textes = [a["texte"] for a in json.loads((tmp_path / "iris" / "donnees" / "alertes.json").read_text())]
    assert "environ 59 minutes" in textes[0] and "environ 98 minutes" in textes[2] and "57" not in textes[0]
    assert "python -m sonde" not in " ".join(textes)
    r = json.loads((tmp_path / "iris" / "donnees" / "rapports.json").read_text())
    assert r["dossiers"][0]["fichier"] == "dossiers/ovhcloud.md" and r["preuves"][0]["horodatage"] == "preuves/2026-11-21.json.ots"
    assert json.loads((tmp_path / "public" / "alertes.json").read_text())[0]["texte"].endswith("57 minutes de panne.")   # l'original n'est pas touché


def test_les_commandes_rapport_et_site_cohabitent(tmp_path):
    """Régression : un `from .site import produire` dans main() masquait `produire` du rapport
    et faisait échouer `python -m sonde rapport` (donc la mesure horaire et les relevés quotidiens)."""
    import subprocess, sys
    from sonde.mesure import RACINE
    r = subprocess.run([sys.executable, "-m", "sonde", "rapport", "--jours", "1", "--sortie", str(tmp_path)],
                       cwd=RACINE, capture_output=True, text=True)
    assert "UnboundLocalError" not in r.stderr, r.stderr
