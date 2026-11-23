"""Les données du site Iris (dossier iris/donnees/), mises à jour à chaque passage de la sonde.

    python -m sonde site

Copie les fichiers publics utiles aux onglets Premium (Ma Météo, Alertes, Indicateurs,
Rapports) et écrit rapports.json : la liste des dossiers de surveillance et des preuves
horodatées réellement présents dans le dépôt. Rien n'est inventé : un fichier absent
est simplement omis.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

FICHIERS = ["meteo.json", "alertes.json", "contrats.json", "statuts.json", "avoirs.json"]


def _lire(chemin: Path):
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def corriger_fins_d_orage(f_alertes: Path, f_meteo: Path) -> int:
    """Les anciennes « fin de l'orage » annonçaient toutes 57 minutes (bug corrigé le 21 novembre 2026) :
    leur texte est réécrit avec la vraie durée, mesurée depuis l'alerte « orage » qui a ouvert la panne."""
    from .alertes import texte_fin
    journal, meteo = _lire(f_alertes), _lire(f_meteo)
    if not isinstance(journal, list):
        return 0
    n = 0
    for a in journal:
        if a.get("type") == "fin_orage" and a.get("horodatage"):
            nouveau = texte_fin(a, journal, meteo)
            if nouveau != a.get("texte"):
                a["texte"], n = nouveau, n + 1
    f_alertes.write_text(json.dumps(journal, ensure_ascii=False, indent=1), encoding="utf-8")
    return n


def produire(racine: Path, maintenant: datetime | None = None) -> dict:
    maintenant = maintenant or datetime.now(timezone.utc)
    sortie = racine / "iris" / "donnees"
    sortie.mkdir(parents=True, exist_ok=True)
    copies = []
    for nom in FICHIERS:
        source = racine / "public" / nom
        if source.exists():
            shutil.copyfile(source, sortie / nom)
            copies.append(nom)
    corriger_fins_d_orage(sortie / "alertes.json", sortie / "meteo.json")
    from .semaine import produire as produire_semaine   # la météo de la semaine (Iris Plus)
    if produire_semaine(racine, sortie, maintenant):
        copies.append("semaine.json")
    from .pilotage import produire as produire_pilotage   # le tableau de pilotage (iris/pilotage.html)
    produire_pilotage(racine, sortie, maintenant)
    copies.append("pilotage.json")

    dossiers = []
    for f in sorted((racine / "dossiers").glob("*.json")):
        d = _lire(f) or {}
        four = d.get("fournisseur") or {}
        if not four.get("id"):
            continue
        dossiers.append({
            "fournisseur": four["id"], "nom": four.get("nom"), "genere_le": d.get("genere_le"),
            "periode": d.get("periode"), "fichier": f"dossiers/{f.stem}.md",
            "verdict_reseau": (d.get("reseau") or {}).get("verdict"),
        })

    preuves = []
    for f in sorted((racine / "preuves").glob("*.json"), reverse=True):
        d = _lire(f) or {}
        preuves.append({"jour": f.stem, "genere_le": d.get("genere_le"), "fichiers": len(d.get("fichiers") or {}),
                        "methode": d.get("methode"), "fichier": f"preuves/{f.name}",
                        "horodatage": f"preuves/{f.name}.ots" if (f.parent / f"{f.name}.ots").exists() else None})

    rapports = {"genere_le": maintenant.isoformat(timespec="seconds"),
                "depot": "https://github.com/mcp-trust-score-org/sonde-ia-eu",
                "dossiers": dossiers, "preuves": preuves}
    (sortie / "rapports.json").write_text(json.dumps(rapports, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"copies": copies, "dossiers": len(dossiers), "preuves": len(preuves)}
