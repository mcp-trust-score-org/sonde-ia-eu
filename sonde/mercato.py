"""Le mercato de l'IA (iris/mercato.json) : prévenir les lecteurs quand un transfert est ajouté.

Appelé par .github/workflows/mercato.yml après un dépôt qui modifie iris/mercato.json :
    python -m sonde.mercato ANCIEN.json NOUVEAU.json   → écrit la notification (JSON) ou rien.
La notification constate un fait sourcé, sans avis (CHARTE, « Le mercato de l'IA »).
"""
from __future__ import annotations

import json
import sys


def _cle(x: dict) -> tuple:
    return (str(x.get("entreprise", "")).strip().lower(), str(x.get("date", "")), str(x.get("pour", "")).strip().lower())


def nouveaux(ancien: dict | None, nouveau: dict) -> list[dict]:
    """Les transferts du nouveau fichier absents de l'ancien. Pas d'ancien fichier (premier dépôt) : rien,
    pour ne pas envoyer d'un coup tout le tableau de départ."""
    if not ancien:
        return []
    vus = {_cle(x) for x in ancien.get("transferts") or []}
    return [x for x in nouveau.get("transferts") or [] if _cle(x) not in vus and x.get("source", {}).get("url")]


def notification(ajouts: list[dict]) -> dict | None:
    if not ajouts:
        return None
    if len(ajouts) == 1:
        x = ajouts[0]
        source = x.get("source", {}).get("media")
        officiel = "OFFICIEL · " if x.get("annonce") == "entreprise" else ""
        if not x.get("quitte"):          # une signature : on ne sait pas ce que l'entreprise utilisait avant
            return {"titre": f"Le mercato de l'IA · {officiel}{x['entreprise']} signe avec {x.get('pour')}",
                    "texte": f"{x.get('comment') or ''}. Source : {source}.".lstrip(". "),
                    "url": "/?mercato=1#une", "sujet": "articles"}
        quitte = " et ".join(x["quitte"])
        partie = " en partie" if x.get("en_partie") else ""
        return {"titre": f"Le mercato de l'IA · {officiel}{x['entreprise']} quitte{partie} {quitte}",
                "texte": f"Pour {x.get('pour')}. Source : {source}.",
                "url": "/?mercato=1#une", "sujet": "articles"}
    noms = ", ".join(dict.fromkeys(x["entreprise"] for x in ajouts))
    return {"titre": f"Le mercato de l'IA · {len(ajouts)} nouveaux transferts",
            "texte": f"{noms}. Qui quitte qui, chaque transfert avec sa source.",
            "url": "/?mercato=1#une", "sujet": "articles"}


def _lire(chemin: str) -> dict | None:
    try:
        with open(chemin, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


if __name__ == "__main__":
    n = notification(nouveaux(_lire(sys.argv[1]), _lire(sys.argv[2]) or {}))
    if n:
        print(json.dumps(n, ensure_ascii=False))
