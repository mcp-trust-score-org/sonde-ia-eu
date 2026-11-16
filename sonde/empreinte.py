"""Empreinte du modèle : détecter qu'un fournisseur change de modèle sans le dire.

Méthode volontairement simple et explicable (une version statistique plus poussée viendra) :
  - chaque jour, les mêmes sondes, à temperature 0, pour chaque (fournisseur, modèle) ;
  - la première empreinte complète sert de référence ;
  - on mesure la similarité textuelle moyenne entre les réponses du jour et la référence ;
  - même à temperature 0, les réponses varient un peu : on apprend cette variation normale
    sur l'historique (médiane et écart absolu médian, MAD) ;
  - alerte « changement probable » si la similarité tombe sous le seuil absolu, ou sous
    médiane - marge × MAD, pendant plusieurs empreintes consécutives.
"""

from __future__ import annotations

import asyncio
import hashlib
from datetime import datetime, timezone
from difflib import SequenceMatcher
from statistics import median

import httpx

from .mesure import appeler, lire_catalogue, resoudre_modele
from .verifications import normaliser


def similarite(a: str, b: str) -> float:
    a, b = normaliser(a), normaliser(b)
    if not a and not b:
        return 1.0
    return round(SequenceMatcher(None, a, b).ratio(), 4)


def comparer(reponses: dict[str, str], reference: dict[str, str]) -> float | None:
    communs = [k for k in reponses if k in reference and reponses[k] and reference[k]]
    if not communs:
        return None
    return round(sum(similarite(reponses[k], reference[k]) for k in communs) / len(communs), 4)


def juger(historique: list[float], actuelle: float, reglages: dict) -> tuple[bool, str]:
    """Une empreinte est-elle anormale ? (sans tenir compte des confirmations)"""
    if actuelle < reglages["seuil_absolu"]:
        return True, f"similarité {actuelle:.2f} sous le seuil absolu {reglages['seuil_absolu']}"
    if len(historique) >= reglages["historique_min"]:
        med = median(historique)
        mad = median(abs(x - med) for x in historique) or 0.01
        limite = med - reglages["marge_mad"] * mad
        if actuelle < limite:
            return True, f"similarité {actuelle:.2f} sous la variation normale (médiane {med:.2f}, limite {limite:.2f})"
    return False, ""


def suivi(precedentes: list[dict], actuelle: float, reglages: dict) -> dict:
    """Décide de l'alerte à partir des empreintes précédentes du même (fournisseur, modèle)."""
    historique_normal = [p["similarite_reference"] for p in precedentes
                         if p.get("similarite_reference") is not None and not p.get("anormale")]
    anormale, raison = juger(historique_normal, actuelle, reglages)
    serie = 1 if anormale else 0
    if anormale:
        for p in reversed(precedentes):
            if p.get("anormale"):
                serie += 1
            else:
                break
    return {"anormale": anormale, "raison": raison, "serie_anormale": serie,
            "alerte": anormale and serie >= reglages["confirmations"]}


async def prendre_empreinte(client, f, mod, modele_id, cle, sondes, reglages, pause):
    reponses, erreurs = {}, 0
    reg = {"max_tokens": reglages["max_tokens"], "temperature": reglages["temperature"]}
    for s in sondes:
        try:
            res = await appeler(client, f["base_url"], cle, modele_id, s["prompt"], reg)
            if res["statut"] in (400, 422) and "stream_options" in (res["erreur"] or ""):
                res = await appeler(client, f["base_url"], cle, modele_id, s["prompt"], reg, avec_usage=False)
            if res["erreur"] or not res["texte"]:
                erreurs += 1
            else:
                reponses[s["id"]] = res["texte"].strip()
        except httpx.HTTPError:
            erreurs += 1
        if pause:
            await asyncio.sleep(pause)
    return reponses, erreurs


async def executer_empreintes(config: dict, conf_empreinte: dict, precedentes: list[dict],
                              env: dict, fournisseurs_filtre: list[str] | None = None) -> list[dict]:
    """precedentes : lignes de type 'empreinte' déjà enregistrées (toutes dates)."""
    reglages, sondes = conf_empreinte["reglages"], conf_empreinte["sondes"]
    sortie = []
    rc = config["reglages"]
    async with httpx.AsyncClient(timeout=httpx.Timeout(rc["delai_total_s"], connect=rc["delai_connexion_s"])) as client:
        async def un_fournisseur(f):
            cle = env.get(f["cle_env"])
            if cle:
                pause, offre = float(f.get("pause_entre_appels_s", 0)), f.get("offre", "payante")
            elif f.get("anonyme_si_sans_cle"):
                pause, offre = float(f.get("pause_anonyme_s", 31)), "anonyme"
            else:
                return []
            catalogue, err = await lire_catalogue(client, f["base_url"], cle)
            if err and f.get("catalogue_secours"):
                catalogue = list(f["catalogue_secours"])
            elif err:
                return []
            lignes = []
            for mod in config["modeles"]:
                mid = resoudre_modele(mod, f["id"], catalogue)
                if not mid:
                    continue
                reponses, erreurs = await prendre_empreinte(client, f, mod, mid, cle, sondes, reglages, pause)
                anciennes = [p for p in precedentes if p["fournisseur"] == f["id"] and p["modele"] == mod["id"]]
                anciennes.sort(key=lambda p: p["horodatage"])
                reference = next((p for p in anciennes if p.get("est_reference")), None)
                ligne = {
                    "type": "empreinte",
                    "horodatage": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "fournisseur": f["id"], "modele": mod["id"], "modele_id": mid, "offre": offre,
                    "reponses": reponses, "erreurs": erreurs,
                    "hash": hashlib.sha256("\n".join(f"{k}={v}" for k, v in sorted(reponses.items())).encode()).hexdigest(),
                    "est_reference": False, "similarite_reference": None, "similarite_precedente": None,
                    "modele_id_change": False,
                }
                complete = len(reponses) == len(sondes)
                if reference is None:
                    # La première empreinte complète devient la référence.
                    ligne["est_reference"] = complete
                    ligne.update({"anormale": False, "raison": "", "serie_anormale": 0, "alerte": False})
                else:
                    ligne["similarite_reference"] = comparer(reponses, reference["reponses"])
                    ligne["similarite_precedente"] = comparer(reponses, anciennes[-1]["reponses"])
                    ligne["modele_id_change"] = anciennes[-1].get("modele_id") != mid
                    if ligne["similarite_reference"] is None:
                        ligne.update({"anormale": False, "raison": "aucune réponse exploitable", "serie_anormale": 0, "alerte": False})
                    else:
                        ligne.update(suivi(anciennes, ligne["similarite_reference"], reglages))
                lignes.append(ligne)
            return lignes

        for lot in await asyncio.gather(*[un_fournisseur(f) for f in config["fournisseurs"]
                                          if not fournisseurs_filtre or f["id"] in fournisseurs_filtre]):
            sortie.extend(lot)
    return sortie
