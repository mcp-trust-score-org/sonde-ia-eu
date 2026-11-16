"""Dossier de surveillance par fournisseur, aligné sur les besoins DORA et AI Act.

Le dossier rassemble ce qu'une entité financière doit pouvoir montrer sur un prestataire d'IA :
disponibilité et incidents, chemin réseau observé, stabilité du modèle, changements de catalogue,
fournisseurs alternatifs mesurés, et preuves horodatées. Chaque section indique les champs du
registre d'information DORA (règlement d'exécution (UE) 2024/2956) ou les articles qu'elle aide
à documenter. Le dossier fournit des éléments de preuve ; il ne remplace ni l'évaluation de
l'entité, ni un audit, ni un avis juridique.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median

from .rapport import _config_publique, agreger, centile, lire_lignes

AVERTISSEMENT = (
    "Ce dossier rassemble des mesures externes indépendantes. Il aide à documenter la surveillance "
    "d'un prestataire TIC ; il ne constitue ni une évaluation des risques de l'entité, ni un audit, "
    "ni un avis juridique. Les correspondances réglementaires sont indicatives."
)

CORRESPONDANCES = [
    ("Disponibilité, incidents, performance", "DORA art. 28 (surveillance continue des prestataires TIC), art. 30 §2 (niveaux de service)"),
    ("Chemin réseau observé : pays et opérateurs d'entrée", "Registre d'information B_02.02.0130 (pays de fourniture du service) – élément d'observation"),
    ("Intermédiaires techniques identifiés", "Registre B_05.02 (chaîne de sous-traitance TIC) – éléments à confirmer contractuellement"),
    ("Stabilité du modèle, changements de catalogue", "DORA art. 28 ; AI Act art. 26 (surveillance du fonctionnement par le déployeur) ; déclaration des ESA du 31/07/2026 (inventaires des API et composants d'IA tenus à jour)"),
    ("Fournisseurs alternatifs mesurés", "Registre B_07.01.0050, 0110, 0120 (substituabilité, alternatives identifiées) ; DORA art. 28 §8 (stratégie de sortie), art. 29 (risque de concentration)"),
    ("Preuves horodatées", "Traçabilité des éléments de surveillance (piste d'audit)"),
]


def _heure(iso: str) -> str:
    return iso[:13]


def _plus_longue_serie(heures_en_echec: list[str]) -> int:
    """Nombre maximal d'heures consécutives avec au moins un échec."""
    if not heures_en_echec:
        return 0
    ts = sorted({datetime.fromisoformat(h + ":00:00+00:00") for h in heures_en_echec})
    meilleur = courant = 1
    for a, b in zip(ts, ts[1:]):
        courant = courant + 1 if b - a <= timedelta(hours=1) else 1
        meilleur = max(meilleur, courant)
    return meilleur


def construire(fournisseur: str, lignes: list[dict], dossier_preuves: Path | None = None) -> dict:
    conf = _config_publique()
    infos = next((f for f in conf["fournisseurs"] if f["id"] == fournisseur), {"id": fournisseur, "nom": fournisseur, "pays": ""})
    mesures = [l for l in lignes if l.get("type") == "mesure" and l["fournisseur"] == fournisseur]

    perf = []
    par_modele = defaultdict(list)
    for m in mesures:
        par_modele[m["modele"]].append(m)
    for modele, ms in sorted(par_modele.items()):
        ok = [m for m in ms if m["succes"]]
        ttft = [m["ttft_ms"] for m in ok if m.get("ttft_ms") is not None]
        echecs = [_heure(m["horodatage"]) for m in ms if not m["succes"]]
        perf.append({
            "modele": modele, "appels": len(ms),
            "disponibilite_pct": round(100 * len(ok) / len(ms), 2),
            "ttft_median_ms": round(median(ttft)) if ttft else None,
            "ttft_p95_ms": round(centile(ttft, 0.95)) if ttft else None,
            "heures_avec_echec": len(set(echecs)),
            "plus_longue_serie_echecs_h": _plus_longue_serie(echecs),
            "offres": sorted({m.get("offre", "payante") for m in ms}),
        })

    chemins = sorted([l for l in lignes if l.get("type") == "chemin" and l["fournisseur"] == fournisseur],
                     key=lambda l: l["horodatage"])
    dernier = chemins[-1] if chemins else None
    reseau = None
    if dernier:
        reseau = {
            "dernier_releve": dernier["horodatage"], "point_de_mesure": dernier.get("point_de_mesure", ""),
            "verdict": dernier["verdict"], "constats": dernier["constats"],
            "pays_entree": sorted({i["pays_ip"] for c in chemins for i in c["ips"] if i.get("pays_ip")}),
            "operateurs": sorted({i.get("operateur") or i.get("titulaire") or "?" for c in chemins for i in c["ips"]}),
            "intermediaires": sorted({x for c in chemins for x in c["intermediaires"]}),
            "verdicts_sur_periode": sorted({c["verdict"] for c in chemins}),
            "releves": len(chemins),
        }

    empreintes = sorted([l for l in lignes if l.get("type") == "empreinte" and l["fournisseur"] == fournisseur],
                        key=lambda l: l["horodatage"])
    stabilite = []
    for modele in sorted({e["modele"] for e in empreintes}):
        es = [e for e in empreintes if e["modele"] == modele]
        stabilite.append({
            "modele": modele, "empreintes": len(es),
            "derniere_similarite": es[-1].get("similarite_reference"),
            "alertes": [{"horodatage": e["horodatage"], "raison": e.get("raison", "")} for e in es if e.get("alerte")],
            "changements_identifiant": [e["horodatage"] for e in es if e.get("modele_id_change")],
        })

    resume = agreger(lignes)
    catalogue = [c for c in resume["changements_catalogue"] if c["fournisseur"] == fournisseur]

    alternatives = []
    for p in perf:
        autres = [r for r in resume["resultats"] if r["modele"] == p["modele"]
                  and r["fournisseur"].split(" (")[0] != fournisseur]
        alternatives.append({
            "modele": p["modele"],
            "alternatives_mesurees": [{"fournisseur": r["fournisseur"], "disponibilite_pct": r["disponibilite_pct"],
                                       "ttft_p50_ms": r["ttft_p50_ms"]} for r in autres],
        })

    preuves = []
    if dossier_preuves and dossier_preuves.exists():
        for m in sorted(dossier_preuves.glob("*.json")):
            preuves.append({"manifeste": m.name, "ancrage_ots": (m.parent / (m.name + ".ots")).exists()})

    return {
        "fournisseur": infos, "genere_le": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "periode": {"debut": min((l["horodatage"] for l in lignes), default=None),
                    "fin": max((l["horodatage"] for l in lignes), default=None)},
        "performance": perf, "reseau": reseau, "stabilite": stabilite,
        "changements_catalogue": catalogue, "substituabilite": alternatives,
        "preuves": preuves[-31:], "avertissement": AVERTISSEMENT,
    }


def _ms(x):
    return "–" if x is None else (f"{x} ms" if x < 1000 else f"{x / 1000:.1f} s".replace(".", ","))


def en_markdown(d: dict) -> str:
    f = d["fournisseur"]
    o = [f"# Dossier de surveillance – {f['nom']}", "",
         f"Période : {(d['periode']['debut'] or '–')[:10]} → {(d['periode']['fin'] or '–')[:10]} · généré le {d['genere_le'][:16].replace('T', ' ')} UTC", "",
         f"> {d['avertissement']}", "",
         "## Identification du prestataire", "",
         "| Champ | Valeur | Source |", "|---|---|---|",
         f"| Nom | {f['nom']} | configuration |",
         f"| Pays du siège | {f.get('pays') or 'à compléter'} | déclaratif, à confirmer au registre du commerce |",
         "| Identifiant LEI ou EUID | à compléter | GLEIF / registre du commerce |",
         "| Société mère ultime | à compléter | registre du commerce |", "",
         "## Correspondance réglementaire (indicative)", "",
         "| Section du dossier | Ce qu'elle aide à documenter |", "|---|---|"]
    o += [f"| {a} | {b} |" for a, b in CORRESPONDANCES]

    o += ["", "## 1. Disponibilité et performance", ""]
    if d["performance"]:
        o += ["| Modèle | Appels | Disponibilité | 1er mot médian | 1er mot p95 | Heures avec échec | Plus longue série d'échecs | Offre mesurée |",
              "|---|---|---|---|---|---|---|---|"]
        for p in d["performance"]:
            o.append(f"| {p['modele']} | {p['appels']} | {p['disponibilite_pct']:g} % | {_ms(p['ttft_median_ms'])} | {_ms(p['ttft_p95_ms'])} | "
                     f"{p['heures_avec_echec']} | {p['plus_longue_serie_echecs_h']} h | {', '.join(p['offres'])} |")
        if any(off != "payante" for p in d["performance"] for off in p["offres"]):
            o += ["", "Les mesures en offre gratuite ou anonyme subissent des limites de débit propres à ces offres : elles ne reflètent pas forcément le service contractuel d'un client payant."]
    else:
        o.append("Aucune mesure sur la période.")

    o += ["", "## 2. Chemin réseau observé", ""]
    r = d["reseau"]
    if r:
        libelles = {"ue_observe": "Entrées réseau opérées et localisées dans l'UE/EEE",
                    "intermediaire_non_ue": "Intermédiaire ou opérateur non européen observé",
                    "indetermine": "Indéterminé – à qualifier"}
        o += [f"**Constat au {r['dernier_releve'][:10]} : {libelles.get(r['verdict'], r['verdict'])}**", ""]
        o += [f"- {c}" for c in r["constats"]]
        o += ["", f"- Pays des points d'entrée observés : {', '.join(r['pays_entree']) or '–'}",
              f"- Opérateurs réseau : {', '.join(r['operateurs']) or '–'}",
              f"- Intermédiaires visibles : {', '.join(r['intermediaires']) or 'aucun'}",
              f"- Relevés sur la période : {r['releves']} · constats distincts : {', '.join(r['verdicts_sur_periode'])}",
              "", "Portée : ce relevé montre l'infrastructure par laquelle les requêtes entrent. Il ne prouve pas à lui seul le lieu de traitement du modèle, à confirmer contractuellement (champ B_02.02.0160)."]
    else:
        o.append("Pas encore de relevé.")

    o += ["", "## 3. Stabilité du modèle et catalogue", ""]
    if d["stabilite"]:
        o += ["| Modèle | Empreintes | Similarité avec la référence | Alertes de changement | Changements d'identifiant |", "|---|---|---|---|---|"]
        for s in d["stabilite"]:
            sim = "référence en cours" if s["derniere_similarite"] is None else f"{s['derniere_similarite']:.2f}"
            o.append(f"| {s['modele']} | {s['empreintes']} | {sim} | {len(s['alertes'])} | {len(s['changements_identifiant'])} |")
        for s in d["stabilite"]:
            for a in s["alertes"]:
                o.append(f"- {a['horodatage'][:16].replace('T', ' ')} · {s['modele']} : changement probable ({a['raison']})")
    else:
        o.append("Pas encore d'empreinte.")
    if d["changements_catalogue"]:
        o += ["", "Changements de catalogue :"]
        for c in d["changements_catalogue"]:
            o.append(f"- {c['horodatage'][:10]} : +{len(c['ajoutes'])} / -{len(c['retires'])}"
                     + (f" (retirés : {', '.join(c['retires'][:6])})" if c["retires"] else ""))

    o += ["", "## 4. Substituabilité : alternatives mesurées", ""]
    for a in d["substituabilite"]:
        if a["alternatives_mesurees"]:
            alts = "; ".join(f"{x['fournisseur']} ({x['disponibilite_pct']:g} %, 1er mot {_ms(x['ttft_p50_ms'])})" for x in a["alternatives_mesurees"])
            o.append(f"- {a['modele']} : également servi et mesuré chez {alts}")
        else:
            o.append(f"- {a['modele']} : aucune alternative européenne mesurée à ce jour")

    o += ["", "## 5. Preuves horodatées", ""]
    if d["preuves"]:
        o.append(f"{len(d['preuves'])} manifestes quotidiens sur la période, dont {sum(p['ancrage_ots'] for p in d['preuves'])} ancrés via OpenTimestamps.")
        o.append("Méthode de vérification : voir `sonde/horodatage.py`.")
    else:
        o.append("Pas encore de manifeste.")
    return "\n".join(o) + "\n"


def produire_dossiers(dossier_donnees: Path, dossier_sortie: Path, dossier_preuves: Path, jours: int = 30) -> list[Path]:
    depuis = datetime.now(timezone.utc) - timedelta(days=jours)
    lignes = lire_lignes(dossier_donnees, depuis)
    fournisseurs = sorted({l["fournisseur"] for l in lignes if l.get("type") in ("mesure", "chemin", "empreinte")})
    dossier_sortie.mkdir(parents=True, exist_ok=True)
    ecrits = []
    for f in fournisseurs:
        d = construire(f, lignes, dossier_preuves)
        (dossier_sortie / f"{f}.json").write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        p = dossier_sortie / f"{f}.md"
        p.write_text(en_markdown(d), encoding="utf-8")
        ecrits.append(p)
    return ecrits
