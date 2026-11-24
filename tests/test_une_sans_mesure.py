"""Un événement que la sonde n'a pas mesuré et que la presse n'a pas repris ne devient pas un « À chaud »."""
from datetime import datetime, timedelta, timezone

from sonde.redaction import candidats_une, fiche_une

M = datetime(2026, 11, 24, 7, 0, tzinfo=timezone.utc)


def _evt(eid, nb_medias=0):
    return {"id": eid, "titre": "Cloudflare : Workers API – Delayed Responses", "type": "incident_amont",
            "debut": (M - timedelta(hours=16)).isoformat(), "fournisseurs": ["mistral"],
            "presse": {"nb_medias": nb_medias} if nb_medias else None}


def test_non_mesure_sans_presse_ecarte():
    actus = {"evenements": [_evt("seul"), _evt("repris", nb_medias=3)]}
    ids = [c["id"] for c in candidats_une(actus, {"impacts": []}, M, set())]
    assert "seul" not in ids
    assert "repris" in ids


def test_fiche_sans_mesure_interdit_rien_vu():
    c = {"evenement": _evt("repris", 3), "impacts": []}
    texte = fiche_une(c)["mesures_de_la_sonde"]
    assert texte.startswith("AUCUNE mesure") and "n'a rien vu" in texte
