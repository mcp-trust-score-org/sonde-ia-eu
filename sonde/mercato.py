"""Le mercato de l'IA (iris/mercato.json) : préparer la notification quand un mouvement est ajouté.
Elle ne part pas toute seule : elle attend le feu vert de la rédaction dans le pilotage (/api/file, « À valider »).

Appelé par .github/workflows/mercato.yml après un dépôt qui modifie iris/mercato.json :
    python -m sonde.mercato ANCIEN.json NOUVEAU.json   → écrit la notification (JSON) ou rien.
    python -m sonde.mercato --point iris/mercato.json   → la notification du point du vendredi (ou rien).
La notification constate un fait sourcé, sans avis (CHARTE, « Le mercato de l'IA »).
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date, timedelta

# Iris Club : les fournisseurs qu'un lecteur peut suivre, et comment les reconnaître dans un mouvement.
FOURNISSEURS_CLUB = {
    "mistral": r"\bmistral\b", "ovhcloud": r"\bovh", "scaleway": r"\bscaleway\b", "ionos": r"\bionos\b",
    "anthropic": r"\banthropic\b|\bclaude\b", "openai": r"\bopenai\b|chatgpt", "google": r"\bgoogle\b|\bgemini\b|\bgemma\b",
    "meta": r"\bmeta\b|\bllama\b",
}


def fournisseurs_de(x: dict) -> list[str]:
    """Les fournisseurs suivis (Iris Club) qu'un mouvement concerne : celui qu'on quitte et celui qu'on rejoint."""
    texte = " ".join(x.get("quitte") or []) + " " + str(x.get("pour") or "")
    return [k for k, motif in FOURNISSEURS_CLUB.items() if re.search(motif, texte, re.I)]


def _cle(x: dict) -> tuple:
    return (str(x.get("entreprise", "")).strip().lower(), str(x.get("date", "")), str(x.get("pour", "")).strip().lower())


def nouveaux(ancien: dict | None, nouveau: dict) -> list[dict]:
    """Les transferts du nouveau fichier absents de l'ancien. Pas d'ancien fichier (premier dépôt) : rien,
    pour ne pas envoyer d'un coup tout le tableau de départ."""
    if not ancien:
        return []
    vus = {_cle(x) for x in ancien.get("transferts") or []}
    return [x for x in nouveau.get("transferts") or [] if _cle(x) not in vus and x.get("source", {}).get("url")]


def court(pour: str) -> str:
    """« Claude (Anthropic, États-Unis) » → « Claude (Anthropic) » (comme sur la carte partageable)."""
    return re.sub(r"\(([^,()]+),[^()]*\)", r"(\1)", str(pour or ""))


def notification(ajouts: list[dict]) -> dict | None:
    """La notification d'un ou plusieurs mouvements, avec la signature d'Iris « C'est signé ». `cle` et `type` servent
    à la file de validation (une même cle n'est jamais proposée deux fois)."""
    if not ajouts:
        return None
    from .cartes import identifiant
    base = {"url": "/?mercato=1#une", "sujet": "articles", "type": "mercato",
            "cle": "mercato-" + "-".join(identifiant(x) for x in ajouts)[:90],
            "fournisseurs": sorted({f for x in ajouts for f in fournisseurs_de(x)})}
    if len(ajouts) == 1:
        x = ajouts[0]
        source = x.get("source", {}).get("media")
        if not x.get("quitte"):          # une signature : on ne sait pas ce que l'entreprise utilisait avant
            return {**base, "titre": f"Le mercato de l'IA · C'est signé · {x['entreprise']} signe avec {court(x.get('pour'))}",
                    "texte": f"{(x.get('comment') or '').rstrip('.')}. Source : {source}.".lstrip(". ")}
        quitte = " et ".join(x["quitte"])
        partie = " en partie" if x.get("en_partie") else ""
        return {**base, "titre": f"Le mercato de l'IA · C'est signé · {x['entreprise']} quitte{partie} {quitte}",
                "texte": f"Pour {court(x.get('pour'))}. Source : {source}."}
    noms = ", ".join(dict.fromkeys(x["entreprise"] for x in ajouts))
    return {**base, "titre": f"Le mercato de l'IA · {len(ajouts)} nouveaux mouvements",
            "texte": f"{noms}. Qui quitte qui, chaque mouvement avec sa source."}


def de_la_semaine(donnees: dict, jour: date) -> list[dict]:
    """Les mouvements des 7 derniers jours (date de la source), du plus récent au plus ancien."""
    debut = (jour - timedelta(days=6)).isoformat()
    return [x for x in donnees.get("transferts") or []
            if debut <= str((x.get("source") or {}).get("date") or "")[:10] <= jour.isoformat()]


def point_du_vendredi(donnees: dict, jour: date) -> dict | None:
    """La notification du point mercato du vendredi. Pas de mouvement dans la semaine : pas de notification."""
    semaine = de_la_semaine(donnees, jour)
    if not semaine:
        return None
    n = jour.isocalendar()[1]
    x = semaine[0]
    coup = f"{x['entreprise']} × {x.get('pour', '').split(' (')[0]}"
    autres = f" et {len(semaine) - 1} autre{'s' if len(semaine) > 2 else ''} mouvement{'s' if len(semaine) > 2 else ''}" if len(semaine) > 1 else ""
    return {"titre": f"Le point mercato · semaine {n}",
            "texte": f"C'est signé : {coup}{autres}. La semaine en 2 min.",
            "url": "/?point=1#une", "sujet": "articles", "type": "point", "cle": f"point-{jour.isocalendar()[0]}-{n}"}


def _lire(chemin: str) -> dict | None:
    try:
        with open(chemin, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


if __name__ == "__main__":
    if sys.argv[1] == "--point":                     # python -m sonde.mercato --point iris/mercato.json
        n = point_du_vendredi(_lire(sys.argv[2]) or {}, date.today())
    else:
        n = notification(nouveaux(_lire(sys.argv[1]), _lire(sys.argv[2]) or {}))
    if n:
        print(json.dumps(n, ensure_ascii=False))
