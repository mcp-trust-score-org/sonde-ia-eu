"""Prévenir les abonnés IRIS Plus quand une nouvelle météo de la semaine ou un nouveau « Et si… ? » est en ligne.

Lancé par GitHub (.github/workflows/plus.yml) à chaque dépôt de iris/plus.json : on compare la version
précédente du fichier à la nouvelle, et seuls les éléments nouveaux déclenchent une notification
(sujet « plus » : les appareils des abonnés Iris Plus et Premium qui ont coché l'option dans la cloche).
Une simple correction de texte ne renvoie rien. Variables : NOTIF_SECRET (déjà utilisé pour les articles)
et SITE_URL.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import httpx


def _lire(chemin: Path) -> dict | None:
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def nouveautes(avant: dict | None, apres: dict | None) -> list[dict]:
    """Les notifications à envoyer. Sans version précédente (première installation), rien."""
    if not avant or not apres:
        return []
    sortie = []
    vues = {e.get("id") for e in avant.get("meteo_semaine") or []}
    for e in apres.get("meteo_semaine") or []:
        if e.get("id") and e["id"] not in vues:
            sortie.append({"sujet": "plus", "titre": "Iris Plus · La météo de la semaine",
                           "texte": e.get("titre") or "La météo de la semaine est en ligne.", "url": "/#plus-meteo"})
    vus = {a.get("id") for a in avant.get("et_si") or []}
    for a in apres.get("et_si") or []:
        if a.get("id") and a["id"] not in vus:
            sortie.append({"sujet": "plus", "titre": "Iris Plus · Et si… ?",
                           "texte": a.get("question") or "", "url": f"/#plus-etsi-{a['id']}"})
    return sortie


def notifier_nouveautes(f_avant: Path, f_apres: Path, env: dict | None = None,
                        client: httpx.Client | None = None) -> list[str]:
    env = env if env is not None else os.environ
    a_envoyer = nouveautes(_lire(f_avant), _lire(f_apres))
    secret = env.get("NOTIF_SECRET")
    if not a_envoyer or not secret:
        return []
    site = (env.get("SITE_URL") or "https://sonde-ia-eu-iris.vercel.app").rstrip("/")
    propre = client is None
    client = client or httpx.Client(timeout=20)
    faits = []
    try:
        for n in a_envoyer:
            try:
                r = client.post(f"{site}/api/notifier", headers={"Authorization": f"Bearer {secret}"}, json=n)
                if r.status_code < 300:
                    faits.append(n["titre"])
            except httpx.HTTPError:
                pass
    finally:
        if propre:
            client.close()
    return faits
