"""La météo de la semaine (Iris Plus) : le temps qu'il a fait, jour par jour, d'après la veille de la sonde.

Écrit iris/donnees/semaine.json (appelé par `python -m sonde site`) :
  - pour chacun des 14 derniers jours (heure de Paris), l'état de chaque fournisseur suivi :
      soleil      toutes les mesures ont réussi ;
      brouillard  réponses nettement plus lentes que d'habitude (plus de 2 fois le temps habituel) ;
      averse      une mesure en échec dans la journée ;
      orage       plusieurs mesures en échec ;
      inconnu     aucune mesure ce jour-là ;
  - les coupures : de la première mesure en échec à la première mesure réussie qui suit.
    La sonde passe environ une fois par heure : une coupure a pu être plus courte que la plage affichée.

Rien n'est déduit au-delà des mesures. Le texte de la lettre (iris/plus.json) est écrit par la rédaction.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")
SUIVIS = ["mistral", "scaleway", "ovhcloud", "ionos"]
NOMS = {"mistral": "Mistral", "scaleway": "Scaleway", "ovhcloud": "OVHcloud", "ionos": "IONOS"}
ORDRE = ["inconnu", "soleil", "brouillard", "averse", "orage"]


def lire_veille(dossier: Path, jours: int = 15) -> list[dict]:
    lignes = []
    for f in sorted(dossier.glob("*.jsonl"))[-jours:]:
        for l in f.read_text(encoding="utf-8").splitlines():
            try:
                d = json.loads(l)
            except ValueError:
                continue
            if d.get("statut_http") == 429:   # limite de débit de notre accès : pas une mesure du fournisseur
                continue
            if d.get("type") == "veille" and d.get("horodatage"):
                lignes.append(d)
    return lignes


def _h(l: dict) -> datetime:
    return datetime.fromisoformat(l["horodatage"])


def calculer(lignes: list[dict], maintenant: datetime, jours: int = 14, suivis: list[str] | None = None) -> dict:
    suivis = suivis or SUIVIS
    par_four = defaultdict(list)
    for l in lignes:
        if l.get("fournisseur") in suivis:
            par_four[l["fournisseur"]].append(l)
    aujourd_hui = maintenant.astimezone(PARIS).date()
    dates = [aujourd_hui - timedelta(days=i) for i in range(jours - 1, -1, -1)]
    table = {d: {} for d in dates}
    coupures = []
    for f in suivis:
        ls = sorted(par_four.get(f, []), key=_h)
        temps = [l["ttft_ms"] for l in ls if l.get("succes") and l.get("ttft_ms")]
        habituel = median(temps) if temps else None
        par_jour = defaultdict(list)
        for l in ls:
            par_jour[_h(l).astimezone(PARIS).date()].append(l)
        for d in dates:
            jl = par_jour.get(d, [])
            echecs = sum(not l.get("succes") for l in jl)
            t = [l["ttft_ms"] for l in jl if l.get("succes") and l.get("ttft_ms")]
            lent = bool(habituel and t and median(t) > 2 * habituel)
            etat = ("inconnu" if not jl else "orage" if echecs >= 2 else "averse" if echecs == 1
                    else "brouillard" if lent else "soleil")
            table[d][f] = {"etat": etat, "mesures": len(jl), "echecs": echecs}
        courant = None
        for l in ls:
            if not l.get("succes"):
                if courant is None:
                    courant = {"fournisseur": f, "nom": NOMS.get(f, f), "debut": l["horodatage"], "mesures_en_echec": 0}
                courant["mesures_en_echec"] += 1
            elif courant:
                courant["fin"] = l["horodatage"]
                coupures.append(courant)
                courant = None
        if courant:
            courant["en_cours"] = True
            coupures.append(courant)
    debut = datetime.combine(dates[0], datetime.min.time(), PARIS)
    coupures = [c for c in coupures if datetime.fromisoformat(c.get("fin") or c["debut"]) >= debut]
    for c in coupures:
        d = datetime.fromisoformat(c["debut"]).astimezone(PARIS)
        c["jour"] = d.date().isoformat()
        c["de"] = d.strftime("%-H h %M")
        if c.get("fin"):
            fin = datetime.fromisoformat(c["fin"]).astimezone(PARIS)
            c["a"] = fin.strftime("%-H h %M") + ("" if fin.date() == d.date() else " le lendemain")
    sortie_jours = []
    for d in dates:
        etats = table[d]
        pire = max((e["etat"] for e in etats.values()), key=ORDRE.index, default="inconnu")
        sortie_jours.append({"date": d.isoformat(), "etat": pire, "fournisseurs": etats})
    return {"genere_le": maintenant.isoformat(timespec="seconds"), "suivis": {f: NOMS.get(f, f) for f in suivis},
            "jours": sortie_jours, "coupures": sorted(coupures, key=lambda c: c["debut"]),
            "methode": "Veille de la sonde Iris, environ une mesure par heure et par fournisseur. Une coupure va de la "
                       "première mesure en échec à la première mesure réussie : elle a pu être plus courte."}


def produire(racine: Path, sortie: Path, maintenant: datetime | None = None) -> dict | None:
    maintenant = maintenant or datetime.now(timezone.utc)
    lignes = lire_veille(racine / "data" / "veille")
    if not lignes:
        return None
    res = calculer(lignes, maintenant)
    (sortie / "semaine.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res
