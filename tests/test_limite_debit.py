"""Une réponse HTTP 429 (limite de débit de notre accès gratuit ou anonyme) n'est jamais une panne."""
import json
from datetime import datetime, timedelta, timezone

from sonde import semaine
from sonde.rapport import lire_lignes
from sonde.veille import lire_veille

T0 = datetime(2026, 11, 21, 10, 0, tzinfo=timezone.utc)


def _ligne(minutes, succes, http):
    return {"type": "veille", "horodatage": (T0 + timedelta(minutes=minutes)).isoformat(), "fournisseur": "ovhcloud",
            "succes": succes, "statut_http": http, "ttft_ms": 900 if succes else None}


def test_429_ecartee_de_la_veille_et_des_mesures(tmp_path):
    (tmp_path / "veille").mkdir()
    lignes = [_ligne(0, True, 200), _ligne(10, False, 429), _ligne(20, False, 429), _ligne(30, True, 200)]
    (tmp_path / "veille" / "2026-11-21.jsonl").write_text("\n".join(json.dumps(l) for l in lignes), encoding="utf-8")
    mesures = [dict(l, type="mesure") for l in lignes]
    (tmp_path / "2026-11.jsonl").write_text("\n".join(json.dumps(l) for l in mesures), encoding="utf-8")
    debut, fin = T0 - timedelta(hours=1), T0 + timedelta(hours=1)
    assert len(lire_veille(tmp_path, debut, fin)) == 2
    assert len(lire_veille(tmp_path, debut, fin, garder_limites=True)) == 4
    assert all(l["statut_http"] != 429 for l in lire_lignes(tmp_path, debut))
    v = semaine.lire_veille(tmp_path / "veille")
    res = semaine.calculer(v, T0 + timedelta(hours=1), jours=2)
    jour = [j for j in res["jours"] if j["date"] == "2026-11-21"][0]
    assert jour["fournisseurs"]["ovhcloud"]["echecs"] == 0
    assert not [c for c in res["coupures"] if c["fournisseur"] == "ovhcloud"]
