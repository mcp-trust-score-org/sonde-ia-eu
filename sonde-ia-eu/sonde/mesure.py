"""Mesure des API d'IA européennes : un appel en streaming par (fournisseur, modèle, tâche).

Chaque appel produit une ligne JSON ajoutée à data/AAAA-MM.jsonl.
Un échec est une mesure comme une autre : il est enregistré, jamais retenté.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import httpx
import yaml

from .verifications import verifier

RACINE = Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------------- config

def charger_yaml(chemin: Path) -> dict:
    with open(chemin, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _cle_comparaison(texte: str) -> str:
    return re.sub(r"[\s._/:]+", "-", texte.lower())


def resoudre_modele(modele: dict, fournisseur_id: str, catalogue: list[str]) -> str | None:
    """Trouve l'identifiant d'un modèle logique dans le catalogue d'un fournisseur."""
    exact = (modele.get("exact") or {}).get(fournisseur_id)
    if exact:
        return exact if (not catalogue or exact in catalogue) else None
    for motif in modele.get("motifs", []):
        m = _cle_comparaison(motif)
        candidats = [mid for mid in catalogue if m in _cle_comparaison(mid)]
        if candidats:
            # Le plus court = en général la version de base, sans suffixe exotique.
            return sorted(candidats, key=len)[0]
    return None


# --------------------------------------------------------------------------- mesure

@dataclass
class Mesure:
    horodatage: str
    execution: str
    fournisseur: str
    modele: str
    modele_id: str | None
    tache: str
    categorie: str
    succes: bool = False
    statut_http: int | None = None
    erreur: str | None = None
    ttft_ms: float | None = None          # délai avant le premier mot
    duree_ms: float | None = None         # durée totale de la réponse
    jetons_entree: int | None = None
    jetons_sortie: int | None = None
    jetons_estimes: bool = False          # True si le fournisseur n'a pas renvoyé l'usage
    jetons_par_s: float | None = None
    cout_eur: float | None = None
    qualite_ok: bool | None = None
    extrait: str = field(default="")


def _maintenant() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


async def lire_catalogue(client: httpx.AsyncClient, base_url: str, cle: str) -> tuple[list[str], str | None]:
    try:
        r = await client.get(f"{base_url}/models", headers={"Authorization": f"Bearer {cle}"})
        r.raise_for_status()
        donnees = r.json()
        ids = [m["id"] for m in donnees.get("data", []) if "id" in m]
        return ids, None
    except Exception as e:  # le catalogue indisponible est lui-même une information
        return [], " ".join(f"{type(e).__name__}: {e}".split())[:300]


async def appeler(
    client: httpx.AsyncClient,
    base_url: str,
    cle: str,
    modele_id: str,
    prompt: str,
    reglages: dict,
    avec_usage: bool = True,
) -> dict:
    """Un appel en streaming. Renvoie les temps, le texte, l'usage et le statut."""
    corps = {
        "model": modele_id,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "max_tokens": reglages["max_tokens"],
        "temperature": reglages["temperature"],
    }
    if avec_usage:
        corps["stream_options"] = {"include_usage": True}

    resultat = {"statut": None, "texte": "", "usage": None, "ttft": None, "duree": None, "erreur": None}
    t0 = time.perf_counter()
    async with client.stream(
        "POST",
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {cle}", "Content-Type": "application/json"},
        json=corps,
    ) as r:
        resultat["statut"] = r.status_code
        if r.status_code >= 400:
            corps_erreur = (await r.aread()).decode("utf-8", "replace")
            resultat["erreur"] = f"HTTP {r.status_code}: {corps_erreur[:300]}"
            return resultat
        morceaux: list[str] = []
        async for ligne in r.aiter_lines():
            if not ligne.startswith("data:"):
                continue
            charge = ligne[5:].strip()
            if charge == "[DONE]":
                break
            try:
                evt = json.loads(charge)
            except json.JSONDecodeError:
                continue
            if evt.get("usage"):
                resultat["usage"] = evt["usage"]
            for choix in evt.get("choices") or []:
                delta = (choix.get("delta") or {})
                texte = delta.get("content") or ""
                # Les modèles de raisonnement envoient parfois d'abord leur réflexion :
                # on la compte pour le premier jeton, pas dans la réponse.
                reflexion = delta.get("reasoning_content") or delta.get("reasoning") or ""
                if (texte or reflexion) and resultat["ttft"] is None:
                    resultat["ttft"] = (time.perf_counter() - t0) * 1000
                if texte:
                    morceaux.append(texte)
        resultat["texte"] = "".join(morceaux)
    resultat["duree"] = (time.perf_counter() - t0) * 1000
    return resultat


def _cout(prix: dict, fournisseur: str, modele: str, entree: int | None, sortie: int | None) -> float | None:
    p = (prix or {}).get(fournisseur, {}).get(modele)
    if not p or entree is None or sortie is None:
        return None
    if p.get("entree") is None or p.get("sortie") is None:
        return None
    return round((entree * p["entree"] + sortie * p["sortie"]) / 1_000_000, 8)


async def mesurer_une(
    client, fournisseur, modele, modele_id, tache, cle, config, execution, semaphore
) -> Mesure:
    m = Mesure(
        horodatage=_maintenant(), execution=execution, fournisseur=fournisseur["id"],
        modele=modele["id"], modele_id=modele_id, tache=tache["id"], categorie=tache.get("categorie", ""),
    )
    reglages = config["reglages"]
    async with semaphore:
        try:
            res = await appeler(client, fournisseur["base_url"], cle, modele_id, tache["prompt"], reglages)
            # Certains fournisseurs refusent `stream_options` : on réessaie une fois sans.
            if res["statut"] in (400, 422) and "stream_options" in (res["erreur"] or ""):
                res = await appeler(client, fournisseur["base_url"], cle, modele_id, tache["prompt"], reglages, avec_usage=False)
        except httpx.TimeoutException:
            m.erreur = "délai dépassé"
            return m
        except httpx.HTTPError as e:
            m.erreur = f"{type(e).__name__}: {e}"[:300]
            return m

    m.statut_http = res["statut"]
    if res["erreur"]:
        m.erreur = res["erreur"]
        return m
    if not res["texte"]:
        m.erreur = "réponse vide"
        return m

    m.succes = True
    m.ttft_ms = round(res["ttft"], 1) if res["ttft"] is not None else None
    m.duree_ms = round(res["duree"], 1)
    usage = res["usage"] or {}
    m.jetons_entree = usage.get("prompt_tokens")
    m.jetons_sortie = usage.get("completion_tokens")
    if m.jetons_sortie is None:
        # Estimation grossière (≈ 4 caractères par jeton), signalée comme telle.
        m.jetons_sortie = max(1, len(res["texte"]) // 4)
        m.jetons_entree = m.jetons_entree or max(1, len(tache["prompt"]) // 4)
        m.jetons_estimes = True
    generation_s = (m.duree_ms - (m.ttft_ms or 0)) / 1000
    if generation_s > 0:
        m.jetons_par_s = round(m.jetons_sortie / generation_s, 1)
    m.cout_eur = _cout(config.get("prix"), fournisseur["id"], modele["id"], m.jetons_entree, m.jetons_sortie)
    m.qualite_ok = verifier(res["texte"], tache["verification"])
    m.extrait = res["texte"][:200]
    return m


def choisir_taches(taches: list[dict], echantillon: int | None, heure: int) -> list[dict]:
    """Rotation : chaque heure teste un sous-ensemble différent, toutes les tâches sont couvertes."""
    if not echantillon or echantillon >= len(taches):
        return taches
    debut = (heure * echantillon) % len(taches)
    return [taches[(debut + i) % len(taches)] for i in range(echantillon)]


async def executer(
    config: dict,
    taches: list[dict],
    dossier_donnees: Path,
    echantillon: int | None = None,
    fournisseurs_filtre: list[str] | None = None,
    env: dict | None = None,
) -> list[dict]:
    env = env if env is not None else os.environ
    execution = uuid.uuid4().hex[:12]
    maintenant = datetime.now(timezone.utc)
    taches_choisies = choisir_taches(taches, echantillon, int(maintenant.timestamp() // 3600))
    reglages = config["reglages"]
    delais = httpx.Timeout(reglages["delai_total_s"], connect=reglages["delai_connexion_s"])

    lignes: list[dict] = []
    async with httpx.AsyncClient(timeout=delais) as client:
        travaux = []
        for f in config["fournisseurs"]:
            if fournisseurs_filtre and f["id"] not in fournisseurs_filtre:
                continue
            cle = env.get(f["cle_env"])
            if not cle:
                print(f"  - {f['nom']} : clé {f['cle_env']} absente, ignoré")
                continue
            catalogue, erreur_cat = await lire_catalogue(client, f["base_url"], cle)
            lignes.append({
                "type": "catalogue", "horodatage": _maintenant(), "execution": execution,
                "fournisseur": f["id"], "nb_modeles": len(catalogue), "modeles": sorted(catalogue),
                "erreur": erreur_cat,
            })
            if erreur_cat:
                # Catalogue illisible = incident du fournisseur, pas "modèle absent".
                continue
            sem = asyncio.Semaphore(reglages["appels_simultanes_par_fournisseur"])
            for mod in config["modeles"]:
                mid = resoudre_modele(mod, f["id"], catalogue)
                if mid is None:
                    lignes.append({
                        "type": "absent", "horodatage": _maintenant(), "execution": execution,
                        "fournisseur": f["id"], "modele": mod["id"],
                    })
                    continue
                for t in taches_choisies:
                    travaux.append(mesurer_une(client, f, mod, mid, t, cle, config, execution, sem))
        mesures = await asyncio.gather(*travaux)

    lignes.extend({"type": "mesure", **asdict(m)} for m in mesures)
    dossier_donnees.mkdir(parents=True, exist_ok=True)
    fichier = dossier_donnees / f"{maintenant:%Y-%m}.jsonl"
    with open(fichier, "a", encoding="utf-8") as f:
        for l in lignes:
            f.write(json.dumps(l, ensure_ascii=False) + "\n")
    return lignes
