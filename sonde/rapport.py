"""Agrège les mesures en un classement par modèle et par fournisseur."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median


def lire_lignes(dossier: Path, depuis: datetime) -> list[dict]:
    lignes = []
    for fichier in sorted(dossier.glob("*.jsonl")):
        with open(fichier, encoding="utf-8") as f:
            for brut in f:
                brut = brut.strip()
                if not brut:
                    continue
                l = json.loads(brut)
                if datetime.fromisoformat(l["horodatage"]) >= depuis:
                    lignes.append(l)
    return lignes


def centile(valeurs: list[float], p: float) -> float | None:
    if not valeurs:
        return None
    v = sorted(valeurs)
    k = (len(v) - 1) * p
    bas, haut = math.floor(k), math.ceil(k)
    return v[int(k)] if bas == haut else v[bas] + (v[haut] - v[bas]) * (k - bas)


def _arrondi(x, n=0):
    return None if x is None else round(x, n) if n else round(x)


def agreger(lignes: list[dict]) -> dict:
    groupes: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for l in lignes:
        if l.get("type") == "mesure":
            nom = l["fournisseur"]
            if l.get("offre", "payante") != "payante":
                nom += f" ({l['offre']})"   # une offre gratuite n'est pas comparable à une offre payante
            groupes[(l["modele"], nom)].append(l)

    resultats = []
    for (modele, fournisseur), ms in sorted(groupes.items()):
        ok = [m for m in ms if m["succes"]]
        ttft = [m["ttft_ms"] for m in ok if m.get("ttft_ms") is not None]
        duree = [m["duree_ms"] for m in ok if m.get("duree_ms") is not None]
        debit = [m["jetons_par_s"] for m in ok if m.get("jetons_par_s")]
        qualite = [m["qualite_ok"] for m in ok if m.get("qualite_ok") is not None]
        couts = [m["cout_eur"] for m in ok if m.get("cout_eur") is not None]
        erreurs = defaultdict(int)
        for m in ms:
            if not m["succes"]:
                erreurs[(m.get("erreur") or "inconnue")[:60]] += 1
        resultats.append({
            "modele": modele,
            "fournisseur": fournisseur,
            "appels": len(ms),
            "disponibilite_pct": round(100 * len(ok) / len(ms), 1),
            "ttft_p50_ms": _arrondi(centile(ttft, 0.5)),
            "ttft_p95_ms": _arrondi(centile(ttft, 0.95)),
            "duree_p50_ms": _arrondi(centile(duree, 0.5)),
            "jetons_par_s_median": _arrondi(median(debit), 1) if debit else None,
            "qualite_pct": round(100 * sum(qualite) / len(qualite), 1) if qualite else None,
            "cout_moyen_eur_par_1000_taches": round(1000 * sum(couts) / len(couts), 4) if couts else None,
            "principales_erreurs": dict(sorted(erreurs.items(), key=lambda x: -x[1])[:3]),
        })

    # Changements de catalogue : modèles ajoutés ou retirés entre deux relevés.
    catalogues: dict[str, list[dict]] = defaultdict(list)
    for l in lignes:
        if l.get("type") == "catalogue" and not l.get("erreur") and l.get("modeles"):
            catalogues[l["fournisseur"]].append(l)
    changements = []
    for fournisseur, releves in catalogues.items():
        releves.sort(key=lambda r: r["horodatage"])
        for avant, apres in zip(releves, releves[1:]):
            a, b = set(avant["modeles"]), set(apres["modeles"])
            if a != b:
                changements.append({
                    "fournisseur": fournisseur, "horodatage": apres["horodatage"],
                    "ajoutes": sorted(b - a), "retires": sorted(a - b),
                })

    absents = sorted({(l["fournisseur"], l["modele"]) for l in lignes if l.get("type") == "absent"})
    incidents: dict[str, dict] = {}
    for l in lignes:
        if l.get("type") == "catalogue":
            i = incidents.setdefault(l["fournisseur"], {"releves": 0, "echecs": 0, "derniere_erreur": None})
            i["releves"] += 1
            if l.get("erreur") and not l.get("secours"):
                i["echecs"] += 1
                i["derniere_erreur"] = l["erreur"][:120]
    incidents = {f: i for f, i in incidents.items() if i["echecs"]}
    return {"resultats": resultats, "changements_catalogue": changements,
            "absents": [list(x) for x in absents], "incidents_catalogue": incidents}


def historique_horaire(lignes: list[dict]) -> list[dict]:
    """Une ligne par (heure, modèle, fournisseur) : de quoi tracer l'évolution dans le temps."""
    seaux: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for l in lignes:
        if l.get("type") != "mesure":
            continue
        heure = l["horodatage"][:13] + ":00:00+00:00"
        nom = l["fournisseur"]
        if l.get("offre", "payante") != "payante":
            nom += f" ({l['offre']})"
        seaux[(heure, l["modele"], nom)].append(l)
    sortie = []
    for (heure, modele, fournisseur), ms in sorted(seaux.items()):
        ok = [m for m in ms if m["succes"]]
        ttft = [m["ttft_ms"] for m in ok if m.get("ttft_ms") is not None]
        qualite = [m["qualite_ok"] for m in ok if m.get("qualite_ok") is not None]
        sortie.append({
            "heure": heure, "modele": modele, "fournisseur": fournisseur,
            "appels": len(ms), "reussis": len(ok),
            "ttft_median_ms": _arrondi(median(ttft)) if ttft else None,
            "ttft_max_ms": _arrondi(max(ttft)) if ttft else None,
            "qualite_pct": round(100 * sum(qualite) / len(qualite), 1) if qualite else None,
        })
    return sortie


def _fmt(x, suffixe=""):
    return "–" if x is None else f"{x:g}{suffixe}" if isinstance(x, float) else f"{x}{suffixe}"


def en_markdown(resume: dict, jours: int) -> str:
    periode = "dernier jour" if jours == 1 else f"{jours} derniers jours"
    out = [f"# Classement des API d'IA européennes ({periode})", ""]
    par_modele: dict[str, list[dict]] = defaultdict(list)
    for r in resume["resultats"]:
        par_modele[r["modele"]].append(r)
    if not par_modele:
        out.append("Aucune mesure sur la période.")
    for modele, rs in par_modele.items():
        # Tri : disponibilité, puis qualité, puis rapidité.
        rs.sort(key=lambda r: (-r["disponibilite_pct"], -(r["qualite_pct"] or 0), r["duree_p50_ms"] or 1e12))
        out += [f"## {modele}", "",
                "| Rang | Fournisseur | Appels | Dispo | 1er mot (médiane / p95) | Durée médiane | Jetons/s | Qualité FR | Coût / 1000 tâches |",
                "|---|---|---|---|---|---|---|---|---|"]
        for i, r in enumerate(rs, 1):
            out.append(
                f"| {i} | {r['fournisseur']} | {r['appels']} | {_fmt(r['disponibilite_pct'], ' %')} | "
                f"{_fmt(r['ttft_p50_ms'], ' ms')} / {_fmt(r['ttft_p95_ms'], ' ms')} | {_fmt(r['duree_p50_ms'], ' ms')} | "
                f"{_fmt(r['jetons_par_s_median'])} | {_fmt(r['qualite_pct'], ' %')} | {_fmt(r['cout_moyen_eur_par_1000_taches'], ' €')} |"
            )
        erreurs = [(r["fournisseur"], e, n) for r in rs for e, n in r["principales_erreurs"].items()]
        if erreurs:
            out += ["", "Erreurs : " + " ; ".join(f"{f} – {e} ({n})" for f, e, n in erreurs)]
        out.append("")
    if resume["incidents_catalogue"]:
        out += ["## Incidents : API injoignable", ""]
        out += [f"- {f} : {i['echecs']} relevé(s) sur {i['releves']} en échec ({i['derniere_erreur']})"
                for f, i in resume["incidents_catalogue"].items()]
        out.append("")
    if resume["absents"]:
        out += ["## Modèles absents du catalogue", ""]
        out += [f"- {f} ne propose pas {m}" for f, m in resume["absents"]]
        out.append("")
    if resume["changements_catalogue"]:
        out += ["## Changements de catalogue", ""]
        for c in resume["changements_catalogue"]:
            out.append(f"- {c['horodatage']} · {c['fournisseur']} : +{len(c['ajoutes'])} / -{len(c['retires'])}"
                       + (f" (retirés : {', '.join(c['retires'][:5])})" if c["retires"] else ""))
        out.append("")
    return "\n".join(out)


def _config_publique() -> dict:
    """Fournisseurs et modèles déclarés, pour afficher aussi ceux qui ne sont pas encore mesurés."""
    chemin = Path(__file__).resolve().parent.parent / "config" / "fournisseurs.yaml"
    try:
        import yaml
        c = yaml.safe_load(chemin.read_text(encoding="utf-8"))
    except Exception:
        return {"fournisseurs": [], "modeles": []}
    return {
        "fournisseurs": [{"id": f["id"], "nom": f["nom"], "pays": f.get("pays", "")} for f in c.get("fournisseurs", [])],
        "modeles": [{"id": m["id"], "nom": m.get("nom", m["id"])} for m in c.get("modeles", [])],
    }


def produire(dossier_donnees: Path, dossier_public: Path, jours: int = 7, jours_historique: int = 30) -> str:
    maintenant = datetime.now(timezone.utc)
    tout = lire_lignes(dossier_donnees, maintenant - timedelta(days=max(jours, jours_historique)))
    depuis = maintenant - timedelta(days=jours)
    resume = agreger([l for l in tout if datetime.fromisoformat(l["horodatage"]) >= depuis])
    resume["periode_jours"] = jours
    resume["genere_le"] = maintenant.isoformat(timespec="seconds")
    mesures = [l for l in tout if l.get("type") == "mesure"]
    resume["total_mesures"] = len(mesures)
    resume["premiere_mesure"] = min((l["horodatage"] for l in mesures), default=None)
    resume["fournisseurs_mesures"] = sorted({l["fournisseur"] for l in mesures})
    resume.update(_config_publique())
    dossier_public.mkdir(parents=True, exist_ok=True)
    (dossier_public / "historique.json").write_text(
        json.dumps({"genere_le": resume["genere_le"], "points": historique_horaire(tout)}, ensure_ascii=False),
        encoding="utf-8",
    )
    (dossier_public / "resume.json").write_text(json.dumps(resume, ensure_ascii=False, indent=2), encoding="utf-8")
    md = en_markdown(resume, jours)
    (dossier_public / "classement.md").write_text(md, encoding="utf-8")
    return md
