"""Avoirs : ce que chaque fournisseur doit, selon la définition de panne de son contrat.

    python -m sonde avoirs --mois 2026-10
    python -m sonde avoirs --mois 2026-10 --facture scaleway=2400 ovhcloud=1800
    python -m sonde avoirs --mois 2026-10 --ticket ovhcloud=2026-10-08T09:20

Calcul :
  1. Le mois est découpé en fenêtres (1 minute en général). Une fenêtre est « en panne »
     si la part d'appels en échec atteint le seuil du contrat. Les fenêtres sans mesure
     sont exclues (on ne compte que ce qu'on a vu).
  2. Si le contrat ne compte la panne qu'à partir d'un ticket, seules les fenêtres en panne
     postérieures au ticket de la même panne comptent.
  3. Disponibilité = fenêtres disponibles / fenêtres mesurées.
  4. Avoir = palier atteint × facture du service sur le mois.

Écrit public/avoirs.json (sans aucun montant de facture) et, si des factures sont données,
un dossier de réclamation par fournisseur dans reclamations/AAAA-MM/.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from .meteo import incidents
from .veille import lire_veille


def bornes_mois(mois: str) -> tuple[datetime, datetime]:
    a, m = (int(x) for x in mois.split("-"))
    debut = datetime(a, m, 1, tzinfo=timezone.utc)
    fin = datetime(a + (m == 12), m % 12 + 1, 1, tzinfo=timezone.utc)
    return debut, fin


def echeance(mois: str, contrat: dict) -> date:
    _, fin = bornes_mois(mois)
    jours = (contrat.get("reclamation") or {}).get("delai_jours_apres_fin_mois", 30)
    return (fin - timedelta(days=1)).date() + timedelta(days=jours)


def fenetres(lignes: list[dict], debut: datetime, fin: datetime, taille_min: int, seuil: float) -> list[dict]:
    """Fenêtres mesurées du mois : {debut, appels, echecs, en_panne}."""
    pas = timedelta(minutes=taille_min)
    comptes: dict[datetime, list[int]] = defaultdict(lambda: [0, 0])
    for l in lignes:
        h = datetime.fromisoformat(l["horodatage"])
        if not (debut <= h < fin):
            continue
        k = debut + ((h - debut) // pas) * pas
        comptes[k][0] += 1
        comptes[k][1] += 0 if l.get("succes") else 1
    out = []
    for k in sorted(comptes):
        n, e = comptes[k]
        out.append({"debut": k, "appels": n, "echecs": e, "en_panne": e / n >= seuil})
    return out


def appliquer_tickets(fen: list[dict], tickets: list[datetime] | None, taille_min: int) -> tuple[list[dict], int]:
    """Ne garde en panne que les fenêtres d'une panne postérieures au ticket de cette panne.
    Sans ticket connu : aucune minute ne compte. Renvoie (fenêtres, minutes perdues faute de ticket)."""
    tickets = sorted(tickets or [])
    perdues = 0
    pas = timedelta(minutes=taille_min)
    debut_panne = None
    res = []
    for w in fen:
        if w["en_panne"]:
            if debut_panne is None or w["debut"] - res[-1]["debut"] > pas:
                debut_panne = w["debut"]
            t = next((t for t in tickets if t >= debut_panne - timedelta(minutes=5)), None)
            compte = t is not None and w["debut"] >= t
            if not compte:
                perdues += taille_min
            res.append({**w, "en_panne": compte, "panne_non_decomptee": not compte})
        else:
            debut_panne = None
            res.append(w)
    return res, perdues


def palier(dispo: float | None, contrat: dict) -> float:
    if dispo is None:
        return 0.0
    pct = 0.0
    for p in contrat.get("paliers") or []:
        if dispo < p["sous_pct"]:
            pct = max(pct, float(p["avoir_pct"]))
    return pct


def calculer(fournisseur: str, lignes: list[dict], contrat: dict, mois: str,
             facture: float | None = None, tickets: list[datetime] | None = None,
             maintenant: datetime | None = None) -> dict:
    maintenant = maintenant or datetime.now(timezone.utc)
    debut, fin = bornes_mois(mois)
    d = contrat.get("definition_panne") or {}
    taille, seuil = int(d.get("fenetre_min", 1)), float(d.get("seuil_erreur", 1.0))
    fen = fenetres(lignes, debut, fin, taille, seuil)
    perdues, au_mieux = 0, None
    if contrat.get("debut_decompte") == "ticket":
        pannes_brutes = sum(w["en_panne"] for w in fen)
        au_mieux = None if not fen else round(100 * (1 - pannes_brutes / len(fen)), 4)
        fen, perdues = appliquer_tickets(fen, tickets, taille)
    mesurees = len(fen)
    en_panne = sum(w["en_panne"] for w in fen)
    dispo = round(100 * (1 - en_panne / mesurees), 4) if mesurees else None
    attendues = int((min(fin, maintenant) - debut).total_seconds() // (60 * taille))
    engagement = contrat.get("engagement_pct")
    pct = palier(dispo, contrat) if engagement is not None else 0.0
    ech = echeance(mois, contrat)
    res = {
        "fournisseur": fournisseur, "service": contrat.get("service"), "mois": mois,
        "engagement_pct": engagement, "disponibilite_pct": dispo,
        "disponibilite_si_ticket_immediat_pct": au_mieux,
        "fenetres_mesurees": mesurees, "fenetres_attendues": attendues,
        "couverture_pct": round(100 * mesurees / attendues, 1) if attendues else None,
        "minutes_en_panne": en_panne * taille, "minutes_non_decomptees_faute_de_ticket": perdues,
        "engagement_tenu": (dispo is None or engagement is None or dispo >= engagement),
        "avoir_pct": pct, "echeance": ech.isoformat(),
        "jours_restants": (ech - maintenant.date()).days,
        "verifie": bool(contrat.get("verifie")), "source": contrat.get("source"),
        "debut_decompte": contrat.get("debut_decompte", "panne"),
        "incidents": [{k: i[k] for k in ("debut", "fin", "duree_min", "erreurs")}
                      for i in incidents([l for l in lignes if debut <= datetime.fromisoformat(l["horodatage"]) < fin])],
    }
    if facture is not None:
        res["facture_eur"] = facture
        res["avoir_eur"] = round(facture * pct / 100, 2)
    return res


def lettre(r: dict, nom_fournisseur: str) -> str:
    dispo = f"{r['disponibilite_pct']:.2f}".replace(".", ",")
    eng = f"{r['engagement_pct']}".replace(".", ",")
    montant = f"{r['avoir_eur']:.2f} €".replace(".", ",") if r.get("avoir_eur") else "[MONTANT SELON VOTRE BARÈME]"
    return (
        f"Objet : demande d'avoir – engagement de disponibilité {r['service']} – {r['mois']}\n\n"
        "Bonjour,\n\n"
        f"Conformément à l'engagement de disponibilité mensuelle de {eng} % de {r['service']}, "
        f"nous demandons l'avoir prévu pour le mois de {r['mois']}. Notre disponibilité mesurée est de {dispo} %, "
        f"soit {r['minutes_en_panne']} minutes d'indisponibilité, détaillées et horodatées dans le dossier joint.\n\n"
        f"Nous vous remercions de confirmer l'avoir correspondant, soit {montant}.\n\n"
        "Cordialement,\n[NOM DE VOTRE ENTREPRISE]\n"
    )


def dossier_markdown(r: dict, nom_fournisseur: str) -> str:
    def pc(x):
        return "—" if x is None else f"{x:.3f} %".replace(".", ",")
    lignes = [
        f"# Réclamation d'avoir – {nom_fournisseur} – {r['mois']}",
        "",
        ("> **Estimation** : les conditions de ce contrat ne sont pas encore vérifiées dans `config/contrats.yaml`. "
         "Vérifiez-les avant d'envoyer.") if not r["verifie"] else "> Conditions du contrat vérifiées.",
        "",
        f"**À envoyer avant le {r['echeance']}** ({r['jours_restants']} jours restants).",
        "",
        "| | |", "| --- | --- |",
        f"| Service | {r['service']} |",
        f"| Engagement | {pc(r['engagement_pct'])} |",
        f"| Disponibilité mesurée | {pc(r['disponibilite_pct'])} |",
        f"| Minutes en panne décomptées | {r['minutes_en_panne']} |",
        f"| Couverture de la mesure | {r['couverture_pct']} % des minutes du mois |",
        f"| Palier d'avoir atteint | {r['avoir_pct']:g} % de la facture |",
    ]
    if r.get("facture_eur") is not None:
        lignes.append(f"| Facture du mois | {r['facture_eur']:.2f} € |".replace(".", ","))
        lignes.append(f"| **Avoir dû** | **{r['avoir_eur']:.2f} €** |".replace(".", ","))
    if r["debut_decompte"] == "ticket":
        lignes += ["", f"Chez ce fournisseur, la panne ne compte qu'à partir de l'ouverture d'un ticket. "
                   f"{r['minutes_non_decomptees_faute_de_ticket']} minutes de panne n'ont pas été décomptées faute de ticket. "
                   f"Avec un ticket ouvert dès le début, la disponibilité aurait été de {pc(r['disponibilite_si_ticket_immediat_pct'])}."]
    lignes += ["", "## Les pannes du mois", "", "| Début (UTC) | Fin (UTC) | Durée | Erreurs principales |", "| --- | --- | --- | --- |"]
    for i in r["incidents"]:
        err = ", ".join(f"{k} ({v})" for k, v in i["erreurs"].items())
        lignes.append(f"| {i['debut']} | {i['fin']} | {i['duree_min']} min | {err} |")
    if not r["incidents"]:
        lignes.append("| — | — | — | aucune panne de 2 minutes ou plus |")
    lignes += ["", "## Le courrier, prêt à envoyer", "", "```", lettre(r, nom_fournisseur).rstrip(), "```", "",
               "## Preuves", "",
               "Mesures minute par minute conservées dans `data/veille/`, dont l'empreinte SHA-256 figure dans les "
               "manifestes quotidiens de `preuves/`, ancrés dans la blockchain Bitcoin (OpenTimestamps). "
               "Joindre aussi un extrait de vos propres journaux d'erreurs sur les mêmes créneaux.", "",
               f"Source des conditions : {r['source']}", ""]
    return "\n".join(lignes)


def produire_avoirs(dossier_donnees: Path, dossier_public: Path, dossier_reclamations: Path,
                    config: dict, contrats: dict, mois: str, factures: dict[str, float] | None = None,
                    tickets: dict[str, list[datetime]] | None = None, maintenant: datetime | None = None) -> list[dict]:
    debut, fin = bornes_mois(mois)
    lignes = lire_veille(dossier_donnees, debut, fin - timedelta(seconds=1))
    noms = {f["id"]: f["nom"] for f in config["fournisseurs"] + config.get("assistants", [])}
    resultats = []
    for fid, contrat in (contrats.get("contrats") or {}).items():
        lf = [l for l in lignes if l["fournisseur"] == fid]
        if not lf:
            continue
        r = calculer(fid, lf, contrat, mois, (factures or {}).get(fid), (tickets or {}).get(fid), maintenant)
        resultats.append(r)
        if factures and fid in factures:
            d = dossier_reclamations / mois
            d.mkdir(parents=True, exist_ok=True)
            (d / f"{fid}.md").write_text(dossier_markdown(r, noms.get(fid, fid)), encoding="utf-8")
    # Version publique : aucun montant de facture.
    publics = [{k: v for k, v in r.items() if k not in ("facture_eur", "avoir_eur", "incidents")} for r in resultats]
    dossier_public.mkdir(parents=True, exist_ok=True)
    f = dossier_public / "avoirs.json"
    try:
        tout = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        tout = {}
    tout[mois] = publics
    tout = dict(sorted(tout.items())[-13:])
    f.write_text(json.dumps(tout, ensure_ascii=False, indent=1), encoding="utf-8")
    return resultats


NOMS_COURTS = {"scaleway": "Scaleway", "ovhcloud": "OVHcloud", "mistral": "Mistral", "ionos": "IONOS"}


def publier_contrats(contrats: dict, dossier_public: Path) -> list[dict]:
    """public/contrats.json : les conditions publiques de chaque fournisseur, pour l'appli.

    Rien de propre à un membre : seulement ce que chaque fournisseur publie lui-même.
    """
    sortie = []
    for fid, c in (contrats.get("contrats") or {}).items():
        if c.get("engagement_pct") is None or not c.get("paliers"):
            continue
        jours = (c.get("reclamation") or {}).get("delai_jours_apres_fin_mois")
        sortie.append({
            "id": fid, "nom": c.get("nom") or NOMS_COURTS.get(fid, fid), "service": c.get("service"),
            "engagement_pct": c["engagement_pct"],
            "paliers": sorted(({"sous_pct": p["sous_pct"], "avoir_pct": p["avoir_pct"]} for p in c["paliers"]),
                              key=lambda p: -p["sous_pct"]),
            "plafond_pct": c.get("plafond_pct"),
            "delai": c.get("delai_texte") or (f"dans les {jours} jours après la fin du mois" if jours else None),
            "delai_jours": jours,
            "debut_decompte": c.get("debut_decompte", "panne"),
            "qui_est_couvert": " ".join(str(c.get("qui_est_couvert") or "").split()) or None,
            "verifie": bool(c.get("verifie")), "source": c.get("source"),
            "suivi_par_la_sonde": c.get("suivi_par_la_sonde", True),
            "note_courte": c.get("note_courte"),
        })
    dossier_public.mkdir(parents=True, exist_ok=True)
    (dossier_public / "contrats.json").write_text(json.dumps(sortie, ensure_ascii=False, indent=1), encoding="utf-8")
    return sortie


def mois_precedent(maintenant: datetime | None = None) -> str:
    maintenant = maintenant or datetime.now(timezone.utc)
    premier = maintenant.replace(day=1)
    return f"{(premier - timedelta(days=1)):%Y-%m}"
