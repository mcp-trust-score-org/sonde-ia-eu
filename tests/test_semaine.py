"""La météo de la semaine (Iris Plus) : jours et coupures tirés de la veille de la sonde."""

from datetime import datetime, timezone

from sonde.semaine import calculer


def _v(f, h, ok, ttft=200):
    return {"type": "veille", "fournisseur": f, "horodatage": h, "succes": ok, "ttft_ms": ttft if ok else None}


def test_jours_et_coupures():
    lignes = [
        _v("ovhcloud", "2026-11-20T16:51:00+00:00", True),
        _v("ovhcloud", "2026-11-20T17:51:00+00:00", False),
        _v("ovhcloud", "2026-11-20T20:44:00+00:00", True),
        _v("ovhcloud", "2026-11-20T21:51:00+00:00", False),
        _v("ovhcloud", "2026-11-20T22:51:00+00:00", False),
        _v("ovhcloud", "2026-11-21T01:45:00+00:00", True),
        _v("ovhcloud", "2026-11-21T21:45:00+00:00", False),
        _v("mistral", "2026-11-20T10:00:00+00:00", True),
        _v("mistral", "2026-11-19T10:00:00+00:00", True, ttft=200),
        _v("mistral", "2026-11-18T10:00:00+00:00", True, ttft=200),
        _v("mistral", "2026-11-21T10:00:00+00:00", True, ttft=900),
    ]
    r = calculer(lignes, datetime(2026, 11, 22, 8, tzinfo=timezone.utc), jours=7)
    jours = {j["date"]: j for j in r["jours"]}
    assert jours["2026-11-20"]["fournisseurs"]["ovhcloud"]["etat"] == "orage"      # 3 mesures en échec
    assert jours["2026-11-21"]["fournisseurs"]["ovhcloud"]["etat"] == "averse"     # une seule
    assert jours["2026-11-21"]["fournisseurs"]["mistral"]["etat"] == "brouillard"  # plus de 2 fois plus lent
    assert jours["2026-11-17"]["etat"] == "inconnu"                                # aucune mesure
    c = r["coupures"]
    assert [(x["de"], x.get("a")) for x in c] == [("18 h 51", "21 h 44"), ("22 h 51", "2 h 45 le lendemain"), ("22 h 45", None)]
    assert c[-1]["en_cours"] and c[1]["mesures_en_echec"] == 2
