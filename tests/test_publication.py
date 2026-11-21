"""Publication d'un brouillon validé sur le site (iris/publies.json)."""

import json
from pathlib import Path

import pytest

from sonde.publication import RefusPublication, publier, retirer
from tests.test_redaction import ARTICLE_TC, ARTICLE_UNE


def _brouillons(tmp_path: Path, propositions: list) -> Path:
    d = tmp_path / "redaction" / "propositions"
    d.mkdir(parents=True)
    (d / "2026-11-22.json").write_text(json.dumps({"date": "2026-11-22", "propositions": propositions}, ensure_ascii=False))
    return tmp_path


UNE = {"rubrique": "une", "tag_interne": "Confirmé", "image": "assets/photos/ia.jpg", "article": ARTICLE_UNE,
       "fiche": {"fournisseurs_concernes": ["OVHcloud"], "debut": "vendredi 20 novembre, 7 h 53",
                 "mesures_de_la_sonde": [{"ce_que_la_sonde_a_vu": "Ralentissement mesuré à 9 h"}]}}


def test_publier_une_et_tous_connectes(tmp_path):
    r = _brouillons(tmp_path, [UNE, {"rubrique": "tous_connectes", "image": "assets/photos/jeux-video.jpg", "article": ARTICLE_TC}])
    publier(r, "À la une", "2026-11-22")
    publier(r, "Tous connectés", "2026-11-22")
    pub = json.loads((r / "iris" / "publies.json").read_text())
    une = pub["une"][0]
    assert une["title"] == ARTICLE_UNE["title"] and une["impact"]["level"] == "red"
    assert "Confirmé" not in json.dumps(pub, ensure_ascii=False)          # le tag interne n'est jamais publié
    assert pub["tous_connectes"][0]["audience"] == "public" and len(pub["tous_connectes"][0]["reflexes"]) == 3
    props = json.loads((r / "redaction" / "propositions" / "2026-11-22.json").read_text())
    assert props["propositions"][0]["statut"] == "publie"
    publier(r, "une", "2026-11-22")                                       # republier ne crée pas de doublon
    assert len(json.loads((r / "iris" / "publies.json").read_text())["une"]) == 1


def test_garde_fous(tmp_path):
    a_verifier = {**UNE, "article": {**ARTICLE_UNE, "chapo": "Le service [À VÉRIFIER : nom du modèle] a ralenti."}}
    r = _brouillons(tmp_path, [{"rubrique": "une", "article": {}}, a_verifier,
                               {"rubrique": "detour", "liens": [{"media": "Next", "titre": "T", "url": "https://x"}]}])
    with pytest.raises(RefusPublication, match="pas été rédigé"):
        publier(r, "une", "2026-11-22", numero=1)
    with pytest.raises(RefusPublication, match="À VÉRIFIER"):
        publier(r, "une", "2026-11-22", numero=2)
    assert publier(r, "une", "2026-11-22", numero=2, forcer=True)["rubrique"] == "une"
    with pytest.raises(RefusPublication, match="pourquoi le lire"):
        publier(r, "detour", "2026-11-22")
    with pytest.raises(RefusPublication, match="Pas de brouillons"):
        publier(r, "une", "2026-11-30")


def test_retirer_le_dernier(tmp_path):
    r = _brouillons(tmp_path, [UNE])
    publier(r, "une", "2026-11-22")
    assert retirer(r, "dernier-une") == 1
    assert json.loads((r / "iris" / "publies.json").read_text())["une"] == []
