"""Veille à la minute : un appel minimal par fournisseur, pour voir les pannes en direct.

    python -m sonde veille            # un passage (pour un planificateur : cron, GitHub Actions)
    python -m sonde veille --boucle   # tourne en continu, un passage au début de chaque minute

Chaque passage ajoute une ligne par fournisseur dans data/veille/AAAA-MM-JJ.jsonl.
Ces fichiers restent sur la machine qui mesure (ils sont gros) ; seuls les résumés
publiés dans public/ partent dans le dépôt. Les manifestes horodatés couvrent aussi
ces fichiers, ce qui permet de prouver plus tard qu'ils n'ont pas été modifiés.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import httpx

from .mesure import appeler, lire_catalogue, resoudre_modele


async def _adresses(hote: str, delai_s: float = 3.0) -> list[str]:
    """Adresses IP vers lesquelles pointe l'API à cet instant (sert à repérer la région / l'entrée réseau).

    Une résolution qui échoue ou traîne n'empêche jamais la mesure : on renvoie simplement [].
    """
    try:
        infos = await asyncio.wait_for(asyncio.get_running_loop().getaddrinfo(hote, 443), delai_s)
    except (OSError, asyncio.TimeoutError):
        return []
    vues = []
    for info in infos:
        ip = info[4][0]
        if ip not in vues:
            vues.append(ip)
    return vues[:4]


def fichier_veille(dossier: Path, quand: datetime) -> Path:
    return dossier / "veille" / f"{quand:%Y-%m-%d}.jsonl"


def lire_veille(dossier: Path, depuis: datetime, jusqua: datetime | None = None,
                garder_limites: bool = False) -> list[dict]:
    """Lignes de veille entre deux instants (fichiers journaliers).

    Les réponses HTTP 429 (limite de débit de NOTRE accès gratuit ou anonyme) ne sont pas des mesures
    du fournisseur : elles sont écartées, sauf si on veut justement les compter (garder_limites)."""
    jusqua = jusqua or datetime.now(timezone.utc)
    lignes = []
    jour = depuis.date()
    while jour <= jusqua.date():
        f = dossier / "veille" / f"{jour:%Y-%m-%d}.jsonl"
        if f.exists():
            with open(f, encoding="utf-8") as fh:
                for brut in fh:
                    brut = brut.strip()
                    if not brut:
                        continue
                    l = json.loads(brut)
                    if l.get("statut_http") == 429 and not garder_limites:
                        continue
                    h = datetime.fromisoformat(l["horodatage"])
                    if depuis <= h <= jusqua:
                        lignes.append(l)
        jour += timedelta(days=1)
    return lignes


def _cache(dossier: Path) -> Path:
    return dossier / "veille" / "cache-modeles.json"


def _lire_cache(dossier: Path) -> dict:
    try:
        return json.loads(_cache(dossier).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


async def _modele_a_appeler(client, f, cle, config, conf_veille, cache, maintenant) -> tuple[str | None, str | None, str | None]:
    """(id logique, id chez le fournisseur, erreur de catalogue). Mis en cache une heure."""
    entree = cache.get(f["id"])
    valable = timedelta(minutes=conf_veille["reglages"].get("catalogue_valable_min", 60))
    if entree and datetime.fromisoformat(entree["verifie_le"]) > maintenant - valable:
        return entree["modele"], entree["modele_id"], None
    catalogue, erreur = await lire_catalogue(client, f["base_url"], cle)
    if erreur and f.get("catalogue_secours"):
        catalogue, erreur = list(f["catalogue_secours"]), None
    if erreur:
        # Catalogue injoignable : on garde l'ancien choix s'il existe (la panne se verra à l'appel).
        if entree:
            return entree["modele"], entree["modele_id"], None
        return None, None, erreur
    par_id = {m["id"]: m for m in config["modeles"]}
    preferes = conf_veille.get("modeles_preferes", {}).get(f["id"]) or list(par_id)
    for logique in preferes:
        mod = par_id.get(logique)
        if not mod:
            continue
        mid = resoudre_modele(mod, f["id"], catalogue)
        if mid:
            cache[f["id"]] = {"modele": logique, "modele_id": mid, "verifie_le": maintenant.isoformat(timespec="seconds")}
            return logique, mid, None
    return None, None, "aucun modèle suivi au catalogue"


async def _veiller_un(client, f, cle, offre, config, conf_veille, cache, maintenant, point) -> dict:
    ligne = {
        "type": "veille", "horodatage": maintenant.isoformat(timespec="seconds"),
        "fournisseur": f["id"], "offre": offre, "point": point,
        "modele": None, "modele_id": None, "succes": False, "statut_http": None,
        "erreur": None, "ttft_ms": None, "duree_ms": None,
    }
    logique, mid, err = await _modele_a_appeler(client, f, cle, config, conf_veille, cache, maintenant)
    ligne["modele"], ligne["modele_id"] = logique, mid
    if not mid:
        ligne["erreur"] = f"catalogue : {err}"
        return ligne
    r = conf_veille["reglages"]
    reglages = {"max_tokens": r.get("max_tokens", 5), "temperature": r.get("temperature", 0)}
    try:
        res = await appeler(client, f["base_url"], cle, mid, r.get("prompt", "Réponds seulement : OK"), reglages, avec_usage=False)
    except httpx.TimeoutException:
        ligne["erreur"] = "délai dépassé"
        return ligne
    except httpx.HTTPError as e:
        ligne["erreur"] = " ".join(f"{type(e).__name__}: {e}".split())[:200]
        return ligne
    ligne["statut_http"] = res["statut"]
    if res["erreur"]:
        ligne["erreur"] = " ".join(res["erreur"].split())[:200]
        if res["statut"] in (401, 403):
            cache.pop(f["id"], None)
        return ligne
    # Les modèles qui « réfléchissent » (gpt-oss…) consomment nos 5 jetons en réflexion
    # avant d'écrire la réponse : le texte reste vide, mais le modèle a bien répondu.
    # Le premier jeton reçu (réflexion comprise) suffit à prouver que le service marche.
    if not res["texte"] and res["ttft"] is None:
        ligne["erreur"] = "réponse vide"
        return ligne
    ligne["succes"] = True
    ligne["ttft_ms"] = round(res["ttft"], 1) if res["ttft"] is not None else None
    ligne["duree_ms"] = round(res["duree"], 1) if res["duree"] is not None else None
    return ligne


async def _frapper_porte(client, f, maintenant, point) -> dict:
    """Mesure « porte d'entrée », sans clé : on demande le catalogue de l'API sans s'identifier.

    Un service debout répond tout de suite « accès refusé » (401 ou 403) : c'est le signe
    qu'il fonctionne. Une erreur serveur (500, 502, 503…), un délai dépassé ou une connexion
    impossible signalent une panne de toute l'API. Cette mesure ne voit pas un modèle lent
    ou en difficulté derrière la porte : elle repère les grosses pannes, gratuitement.
    """
    ligne = {
        "type": "veille", "horodatage": maintenant.isoformat(timespec="seconds"),
        "fournisseur": f["id"], "offre": "porte", "point": point,
        "modele": None, "modele_id": None, "succes": False, "statut_http": None,
        "erreur": None, "ttft_ms": None, "duree_ms": None,
    }
    t0 = time.perf_counter()
    try:
        r = await client.get(f.get("porte_url") or f"{f['base_url'].rstrip('/')}/models")
    except httpx.TimeoutException:
        ligne["erreur"] = "délai dépassé"
        return ligne
    except httpx.HTTPError as e:
        ligne["erreur"] = " ".join(f"{type(e).__name__}: {e}".split())[:200]
        return ligne
    duree = round((time.perf_counter() - t0) * 1000, 1)
    ligne["statut_http"] = r.status_code
    # 400, 401 et 403 : la porte répond « requête refusée » ; le service est donc debout.
    if r.status_code < 300 or r.status_code in (400, 401, 403):
        ligne["succes"] = True
        # Temps de réponse de la porte : sert de référence pour repérer un ralentissement.
        ligne["ttft_ms"] = ligne["duree_ms"] = duree
    elif r.status_code == 404:
        ligne["erreur"] = "adresse de l'API introuvable (vérifier base_url)"
    else:
        ligne["erreur"] = f"erreur {r.status_code} à l'entrée de l'API"
    return ligne


async def veiller(config: dict, conf_veille: dict, dossier: Path, env: dict | None = None,
                  point: str = "local", fournisseurs_filtre: list[str] | None = None,
                  maintenant: datetime | None = None) -> list[dict]:
    """Un passage : une ligne par fournisseur suivi."""
    env = env if env is not None else os.environ
    maintenant = maintenant or datetime.now(timezone.utc).replace(microsecond=0)
    r = conf_veille["reglages"]
    delais = httpx.Timeout(r.get("delai_total_s", 30), connect=r.get("delai_connexion_s", 10))
    cache = _lire_cache(dossier)
    travaux = []
    async with httpx.AsyncClient(timeout=delais) as client:
        for f in config["fournisseurs"] + config.get("assistants", []):
            if fournisseurs_filtre and f["id"] not in fournisseurs_filtre:
                continue
            if f.get("categorie") == "assistant":
                # Assistants des salariés (Copilot, ChatGPT…) : mesure de la porte d'entrée seulement.
                travaux.append(_frapper_porte(client, f, maintenant, point))
                continue
            cle = env.get(f["cle_env"])
            if cle:
                offre = f.get("offre", "payante")
            elif f.get("anonyme_si_sans_cle"):
                offre = "anonyme"
            elif f.get("porte_si_sans_cle"):
                travaux.append(_frapper_porte(client, f, maintenant, point))
                continue
            else:
                continue
            travaux.append(_veiller_un(client, f, cle, offre, config, conf_veille, cache, maintenant, point))
        lignes = list(await asyncio.gather(*travaux))
        # Région / entrée réseau : l'adresse IP de l'API au moment de la mesure.
        # Croisée avec le chemin réseau quotidien (python -m sonde chemin), elle dit par quel
        # opérateur et quel pays la requête est entrée. Elle ne dit pas où tourne le modèle.
        par_id = {f["id"]: f for f in config["fournisseurs"] + config.get("assistants", [])}
        hotes = {}
        for l in lignes:
            f = par_id.get(l["fournisseur"])
            if f:
                url = f.get("porte_url") if l.get("offre") == "porte" and f.get("porte_url") else f["base_url"]
                hote = urlparse(url).hostname
                if hote:
                    hotes[l["fournisseur"]] = hote
        resolus = dict(zip(hotes, await asyncio.gather(*(_adresses(h) for h in hotes.values()))))
        for l in lignes:
            l["hote"] = hotes.get(l["fournisseur"])
            l["ip"] = resolus.get(l["fournisseur"], [])
    sortie = fichier_veille(dossier, maintenant)
    sortie.parent.mkdir(parents=True, exist_ok=True)
    with open(sortie, "a", encoding="utf-8") as fh:
        for l in lignes:
            fh.write(json.dumps(l, ensure_ascii=False) + "\n")
    _cache(dossier).write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    return lignes


def boucle(config: dict, conf_veille: dict, dossier: Path, point: str, apres_passage=None) -> None:
    """Un passage au début de chaque minute, sans fin. `apres_passage(lignes)` est appelé après chacun."""
    while True:
        attente = 60 - (time.time() % 60)
        time.sleep(attente)
        try:
            lignes = asyncio.run(veiller(config, conf_veille, dossier, point=point))
            etats = " · ".join(f"{l['fournisseur']} {'ok' if l['succes'] else 'ÉCHEC'}" for l in lignes)
            print(f"{datetime.now(timezone.utc):%H:%M} {etats}", flush=True)
            if apres_passage:
                apres_passage(lignes)
        except Exception as e:  # la boucle ne doit jamais s'arrêter sur une erreur
            print(f"{datetime.now(timezone.utc):%H:%M} erreur de passage : {e}", flush=True)
