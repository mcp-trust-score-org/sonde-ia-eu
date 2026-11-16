"""Retours des membres : « Moi aussi, je suis touché » / « Pas chez moi ».

Chaque alerte d'orage ou de vigilance porte deux boutons (dans la notification ntfy et
dans l'appli Iris). Un clic publie un message anonyme sur un second sujet ntfy, le sujet
des retours :

    touche|<identifiant de l'alerte>      ou      pas_touche|<identifiant de l'alerte>

À chaque passage, la sonde relit ce sujet, garde les retours dans data/retours.jsonl
(ntfy.sh n'en conserve que quelques heures) et publie les totaux dans public/retours.json.
Aucune donnée personnelle : ni nom, ni adresse, seulement un clic.

Avec le temps, ces totaux mesurent ce qu'aucune sonde publique ne voit : la part des
membres réellement touchés quand un fournisseur passe à l'orage, y compris ceux qui
utilisent une offre dédiée ou privée.
"""

from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from pathlib import Path

import httpx

CHOIX = ("touche", "pas_touche")
_MOTIF = re.compile(r"^(touche|pas_touche)\|([a-z0-9_-]{3,80})$")


def sujet_retours(env: dict | None = None) -> str | None:
    env = env if env is not None else os.environ
    if env.get("NTFY_RETOURS_TOPIC"):
        return env["NTFY_RETOURS_TOPIC"]
    return f"{env['NTFY_TOPIC']}-retours" if env.get("NTFY_TOPIC") else None


def lire_message(texte: str) -> tuple[str, str] | None:
    m = _MOTIF.match((texte or "").strip())
    return (m.group(1), m.group(2)) if m else None


def relever(dossier_donnees: Path, env: dict | None = None, client: httpx.Client | None = None) -> int:
    """Récupère les nouveaux retours sur ntfy. Renvoie le nombre de retours ajoutés ; ne lève jamais."""
    env = env if env is not None else os.environ
    sujet = sujet_retours(env)
    if not sujet:
        return 0
    serveur = env.get("NTFY_SERVEUR", "https://ntfy.sh").rstrip("/")
    fichier = dossier_donnees / "retours.jsonl"
    deja = set()
    if fichier.exists():
        for l in fichier.read_text(encoding="utf-8").splitlines():
            try:
                deja.add(json.loads(l)["id"])
            except (ValueError, KeyError):
                pass
    propre = client is None
    client = client or httpx.Client(timeout=15)
    nouveaux = []
    try:
        r = client.get(f"{serveur}/{sujet}/json", params={"poll": "1", "since": "all"})
        if r.status_code >= 300:
            return 0
        for ligne in r.text.splitlines():
            try:
                evt = json.loads(ligne)
            except ValueError:
                continue
            if evt.get("event") != "message" or evt.get("id") in deja:
                continue
            lu = lire_message(evt.get("message", ""))
            if not lu:
                continue
            nouveaux.append({"id": evt["id"], "horodatage": evt.get("time"), "choix": lu[0], "alerte": lu[1]})
            deja.add(evt["id"])
    except httpx.HTTPError:
        return 0
    finally:
        if propre:
            client.close()
    if nouveaux:
        dossier_donnees.mkdir(parents=True, exist_ok=True)
        with fichier.open("a", encoding="utf-8") as f:
            for n in nouveaux:
                f.write(json.dumps(n, ensure_ascii=False) + "\n")
    return len(nouveaux)


def totaliser(dossier_donnees: Path, dossier_public: Path) -> dict:
    """Écrit public/retours.json : totaux par alerte et résumé par fournisseur."""
    par_alerte: dict[str, dict[str, int]] = defaultdict(lambda: {c: 0 for c in CHOIX})
    fichier = dossier_donnees / "retours.jsonl"
    if fichier.exists():
        for l in fichier.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(l)
                par_alerte[r["alerte"]][r["choix"]] += 1
            except (ValueError, KeyError):
                pass
    try:
        journal = json.loads((dossier_public / "alertes.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        journal = []
    origine = {a["id"]: (a["fournisseur"], a.get("type")) for a in journal if a.get("id")}
    resume: dict[str, dict] = {}
    for aid, t in par_alerte.items():
        f, type_ = origine.get(aid, (None, None))
        if not f or type_ != "orage":
            continue
        s = resume.setdefault(f, {"orages_avec_retours": 0, "touche": 0, "pas_touche": 0})
        s["orages_avec_retours"] += 1
        s["touche"] += t["touche"]
        s["pas_touche"] += t["pas_touche"]
    for s in resume.values():
        n = s["touche"] + s["pas_touche"]
        s["part_touche_pct"] = round(100 * s["touche"] / n) if n else None
    sortie = {"par_alerte": dict(par_alerte), "par_fournisseur": resume}
    dossier_public.mkdir(parents=True, exist_ok=True)
    (dossier_public / "retours.json").write_text(json.dumps(sortie, ensure_ascii=False, indent=1), encoding="utf-8")
    return sortie
