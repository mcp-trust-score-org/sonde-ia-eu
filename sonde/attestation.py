"""Attestation de panne : un document neutre et horodaté sur un créneau donné.

    python -m sonde attestation --fournisseur ovhcloud --debut 2026-11-16T14:00 --fin 2026-11-16T16:00

Écrit attestations/ATT-<fournisseur>-<date>.md et .json. L'attestation décrit ce que la
sonde a mesuré, minute par minute, depuis son point de mesure. Elle cite l'empreinte
SHA-256 des fichiers de mesures et les manifestes horodatés qui les couvrent.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median

from .meteo import incidents, statut_minutes
from .veille import lire_veille

AVERTISSEMENT = (
    "Cette attestation décrit les mesures réalisées par la sonde depuis son point de mesure, "
    "avec un appel minimal par minute. Elle constate des faits techniques ; elle ne qualifie pas "
    "juridiquement l'événement et ne remplace pas les journaux du client ni les engagements du contrat."
)


def _segments(cases: list[int | None], debut: datetime) -> list[dict]:
    """Regroupe les minutes consécutives de même statut."""
    out = []
    for i, c in enumerate(cases):
        etat = {1: "fonctionne", 0: "en échec", None: "pas de mesure"}[c]
        if out and out[-1]["etat"] == etat:
            out[-1]["minutes"] += 1
        else:
            out.append({"de": (debut + timedelta(minutes=i)).isoformat(timespec="minutes"), "etat": etat, "minutes": 1})
    for s in out:
        s["a"] = (datetime.fromisoformat(s["de"]) + timedelta(minutes=s["minutes"])).isoformat(timespec="minutes")
    return out


def _manifestes_couvrant(dossier_preuves: Path, noms: list[str]) -> list[str]:
    if not dossier_preuves.exists():
        return []
    trouves = []
    for m in sorted(dossier_preuves.glob("*.json")):
        try:
            fichiers = json.loads(m.read_text(encoding="utf-8")).get("fichiers", {})
        except ValueError:
            continue
        if any(n in fichiers for n in noms):
            ancre = m.with_suffix(m.suffix + ".ots").exists()
            trouves.append(f"{m.name}{' (ancré OpenTimestamps)' if ancre else ''}")
    return trouves


def attester(dossier_donnees: Path, dossier_preuves: Path, config: dict, fournisseur: str,
             debut: datetime, fin: datetime, maintenant: datetime | None = None) -> dict:
    maintenant = maintenant or datetime.now(timezone.utc)
    lignes = [l for l in lire_veille(dossier_donnees, debut, fin) if l["fournisseur"] == fournisseur]
    nom = next((f["nom"] for f in config["fournisseurs"] if f["id"] == fournisseur), fournisseur)
    cases = statut_minutes(lignes, debut, fin)
    mesurees = [c for c in cases if c is not None]
    echecs = sum(1 for c in mesurees if c == 0)
    erreurs: dict[str, int] = {}
    for l in lignes:
        if not l.get("succes"):
            k = (l.get("erreur") or "échec")[:80]
            erreurs[k] = erreurs.get(k, 0) + 1
    ttft = [l["ttft_ms"] for l in lignes if l.get("succes") and l.get("ttft_ms")]
    jours = sorted({datetime.fromisoformat(l["horodatage"]).date() for l in lignes})
    fichiers = []
    for j in jours:
        f = dossier_donnees / "veille" / f"{j:%Y-%m-%d}.jsonl"
        if f.exists():
            fichiers.append({"fichier": f"veille/{f.name}", "sha256": hashlib.sha256(f.read_bytes()).hexdigest()})
    ident = f"ATT-{fournisseur}-{debut:%Y%m%d%H%M}"
    return {
        "identifiant": ident, "emise_le": maintenant.isoformat(timespec="seconds"),
        "fournisseur": fournisseur, "nom": nom,
        "debut": debut.isoformat(timespec="minutes"), "fin": fin.isoformat(timespec="minutes"),
        "point_de_mesure": lignes[-1].get("point") if lignes else None,
        "modele_appele": lignes[-1].get("modele_id") if lignes else None,
        "minutes_du_creneau": len(cases), "minutes_mesurees": len(mesurees), "minutes_en_echec": echecs,
        "taux_echec_pct": round(100 * echecs / len(mesurees), 1) if mesurees else None,
        "erreurs": dict(sorted(erreurs.items(), key=lambda kv: -kv[1])),
        "ttft_median_ms": round(median(ttft)) if ttft else None,
        "pannes": [{k: i[k] for k in ("debut", "fin", "duree_min")} for i in incidents(lignes)],
        "chronologie": _segments(cases, debut),
        "preuves": {"fichiers": fichiers, "manifestes": _manifestes_couvrant(dossier_preuves, [x["fichier"] for x in fichiers])},
        "avertissement": AVERTISSEMENT,
    }


def en_markdown(a: dict) -> str:
    l = [
        f"# Attestation de panne {a['identifiant']}",
        "",
        f"**{a['nom']}**, du {a['debut']} au {a['fin']} (heures UTC). Émise le {a['emise_le']}.",
        "",
        "| | |", "| --- | --- |",
        f"| Point de mesure | {a['point_de_mesure'] or '—'} |",
        f"| Modèle appelé | {a['modele_appele'] or '—'} |",
        f"| Minutes mesurées | {a['minutes_mesurees']} sur {a['minutes_du_creneau']} |",
        f"| Minutes en échec | {a['minutes_en_echec']} ({a['taux_echec_pct']} %) |",
        f"| Délai médian avant le premier mot (appels réussis) | {a['ttft_median_ms'] or '—'} ms |",
        "",
        "## Ce qui a été constaté, minute par minute",
        "",
        "| De | À | État | Minutes |", "| --- | --- | --- | --- |",
    ]
    for s in a["chronologie"]:
        l.append(f"| {s['de']} | {s['a']} | {s['etat']} | {s['minutes']} |")
    l += ["", "## Erreurs relevées", ""]
    l += [f"- {k} : {v} fois" for k, v in a["erreurs"].items()] or ["- aucune"]
    l += ["", "## Preuves", ""]
    for f in a["preuves"]["fichiers"]:
        l.append(f"- `{f['fichier']}` : SHA-256 `{f['sha256']}`")
    if a["preuves"]["manifestes"]:
        l.append("- Manifestes horodatés couvrant ces fichiers : " + ", ".join(a["preuves"]["manifestes"]))
    else:
        l.append("- Manifeste horodaté : pas encore émis (il l'est chaque nuit).")
    l += ["", f"*{a['avertissement']}*", ""]
    return "\n".join(l)


def ecrire(a: dict, dossier: Path) -> Path:
    dossier.mkdir(parents=True, exist_ok=True)
    (dossier / f"{a['identifiant']}.json").write_text(json.dumps(a, ensure_ascii=False, indent=1), encoding="utf-8")
    p = dossier / f"{a['identifiant']}.md"
    p.write_text(en_markdown(a), encoding="utf-8")
    return p
