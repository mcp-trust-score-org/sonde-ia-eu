"""Dossier d'incident fournisseur, pour un client : tout ce qu'Iris sait, en un seul document.

    python -m sonde dossier-client --client-fichier clients/cabinet.yaml --fournisseur scaleway --mois 2026-10

Le fichier client (gardé dans un dépôt PRIVÉ, jamais dans le dépôt public de la sonde) :

    nom: Cabinet Exemple
    factures:                    # montant HT de la facture du mois, par fournisseur
      scaleway: {"2026-10": 4800}
    tickets:                     # heures d'ouverture des tickets chez le fournisseur (UTC), si utile
      ovhcloud: ["2026-10-14T09:50"]
    fonction_critique: true      # le service soutient-il une fonction critique (DORA) ?

Le dossier assemble :
  1. la synthèse du mois ;
  2. la chronologie de chaque panne : mesures, alertes envoyées, retours des membres du club,
     ce que le fournisseur a reconnu sur sa page de statut ;
  3. l'attestation minute par minute de la panne principale, avec les empreintes des fichiers ;
  4. une aide à la classification DORA (critères de durée et délais) ;
  5. l'avoir dû et la lettre de réclamation, signée au nom du client.

Le dossier constate des faits techniques. Il ne qualifie pas juridiquement l'événement :
la décision (incident majeur ou non, envoi de la réclamation) appartient au client.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from . import attestation as _attestation
from .sla import bornes_mois, calculer, lettre
from .veille import lire_veille

PARIS = ZoneInfo("Europe/Paris")


def _paris(iso: str | datetime, avec_jour: bool = True) -> str:
    d = datetime.fromisoformat(iso) if isinstance(iso, str) else iso
    d = d.astimezone(PARIS)
    return d.strftime("%d/%m %H:%M") if avec_jour else d.strftime("%H:%M")


MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]


def _mois(m: str) -> str:
    a, n = m.split("-")
    return f"{MOIS[int(n) - 1]} {a}"


def _date(iso: str) -> str:
    a, m, j = iso[:10].split("-")
    return f"{int(j)} {MOIS[int(m) - 1]} {a}"


def _duree(minutes: int) -> str:
    h, m = divmod(int(minutes), 60)
    return f"{h} h {m:02d}" if h else f"{m} min"


def _lire_json(chemin: Path, defaut):
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return defaut


def _chevauche(debut: datetime, fin: datetime, autre_debut: str, autre_fin: str | None, marge_min: int = 15) -> bool:
    m = timedelta(minutes=marge_min)
    a = datetime.fromisoformat(autre_debut)
    b = datetime.fromisoformat(autre_fin) if autre_fin else datetime.now(timezone.utc)
    return a <= fin + m and b >= debut - m


def assembler(dossier_donnees: Path, dossier_public: Path, dossier_preuves: Path, config: dict, contrats: dict,
              client: dict, fournisseur: str, mois: str, maintenant: datetime | None = None) -> dict:
    """Rassemble les faits du mois pour un client et un fournisseur. Renvoie un dictionnaire."""
    maintenant = maintenant or datetime.now(timezone.utc)
    tous = config["fournisseurs"] + config.get("assistants", [])
    f = next((x for x in tous if x["id"] == fournisseur), {"id": fournisseur, "nom": fournisseur})
    contrat = (contrats.get("contrats") or {}).get(fournisseur) or {}
    debut, fin = bornes_mois(mois)
    lignes = [l for l in lire_veille(dossier_donnees, debut, fin) if l["fournisseur"] == fournisseur]
    facture = ((client.get("factures") or {}).get(fournisseur) or {}).get(mois)
    tickets = [datetime.fromisoformat(t).replace(tzinfo=timezone.utc) if "+" not in t and "Z" not in t
               else datetime.fromisoformat(t.replace("Z", "+00:00"))
               for t in (client.get("tickets") or {}).get(fournisseur, [])]
    sla = calculer(fournisseur, lignes, contrat, mois, facture=float(facture) if facture is not None else None,
                   tickets=tickets or None, maintenant=maintenant) if contrat.get("engagement_pct") is not None else None
    if sla is None:
        from .meteo import incidents as _incidents
        pannes = _incidents(lignes)
    else:
        pannes = sla["incidents"]

    alertes = [a for a in _lire_json(dossier_public / "alertes.json", []) if a.get("fournisseur") == fournisseur]
    retours = _lire_json(dossier_public / "retours.json", {}).get("par_alerte", {})
    statut = _lire_json(dossier_public / "statuts.json", {}).get("fournisseurs", {}).get(fournisseur, {})

    chronos = []
    for p in pannes:
        d, fi = datetime.fromisoformat(p["debut"]), datetime.fromisoformat(p["fin"])
        evts = [(d, "Premier échec mesuré" + (f" ({next(iter(p.get('erreurs') or {}), '')})" if p.get("erreurs") else ""), "Sonde Iris")]
        for a in alertes:
            h = datetime.fromisoformat(a["horodatage"])
            if d - timedelta(minutes=15) <= h <= fi + timedelta(minutes=30):
                texte = a.get("titre", "Alerte")
                r = retours.get(a.get("id", ""), {})
                if r:
                    n = r.get("touche", 0) + r.get("pas_touche", 0)
                    texte += f" · {r.get('touche', 0)} membre(s) touché(s) sur {n} réponse(s)"
                evts.append((h, f"Alerte envoyée : {texte}", "Iris"))
        reconnu = None
        if statut.get("type") == "statuspage" and not statut.get("erreur"):
            officiels = [o for o in statut.get("incidents_30j", []) if _chevauche(d, fi, o["debut"], o.get("fin"))]
            for o in officiels:
                evts.append((datetime.fromisoformat(o["debut"]), f"Incident publié par le fournisseur : « {o['titre']} »",
                             "Page de statut officielle"))
            reconnu = bool(officiels)
        evts.append((fi, f"Retour à la normale, après {_duree(p['duree_min'])}", "Sonde Iris"))
        evts.sort(key=lambda e: e[0])
        retard = None
        if reconnu:
            premier = min(datetime.fromisoformat(o["debut"]) for o in statut["incidents_30j"]
                          if _chevauche(d, fi, o["debut"], o.get("fin")))
            retard = max(0, round((premier - d).total_seconds() / 60))
        chronos.append({"panne": p, "evenements": evts, "reconnu": reconnu, "retard_min": retard})

    principale = max(pannes, key=lambda p: p["duree_min"]) if pannes else None
    attestation = None
    if principale:
        d = datetime.fromisoformat(principale["debut"]) - timedelta(minutes=15)
        fi = datetime.fromisoformat(principale["fin"]) + timedelta(minutes=15)
        attestation = _attestation.attester(dossier_donnees, dossier_preuves, config, fournisseur, d, fi, maintenant)

    return {"client": client.get("nom", "[NOM DU CLIENT]"), "fonction_critique": bool(client.get("fonction_critique")),
            "fournisseur": f, "mois": mois, "contrat": contrat, "sla": sla, "pannes": pannes,
            "chronologies": chronos, "principale": principale, "attestation": attestation,
            "genere_le": maintenant}


def en_markdown(d: dict) -> str:
    f, sla, nom = d["fournisseur"], d["sla"], d["fournisseur"].get("nom", d["fournisseur"]["id"])
    mf = _mois(d["mois"])
    L = [f"# Dossier d'incident fournisseur : {nom}, {mf}", "",
         f"Préparé par Iris pour **{d['client']}**, le {_paris(d['genere_le'])} (heure de Paris).", ""]

    # 1. Synthèse
    L += ["## Synthèse", ""]
    if not d["pannes"]:
        L += [f"Aucune panne mesurée chez {nom} en {mf}."]
    else:
        p = d["principale"]
        tete = (f"{len(d['pannes'])} panne(s) mesurée(s) chez {nom} en {mf}, dont la principale le "
                f"{_paris(p['debut'])}, pendant {_duree(p['duree_min'])}.")
        if sla and not sla["engagement_tenu"] and sla.get("avoir_eur"):
            tete += f" Un avoir de **{sla['avoir_eur']:.2f} €** est dû, à réclamer **avant le {_date(sla['echeance'])}**.".replace(".", ",", 1)
        L += [tete, "", "| Indicateur | Valeur |", "| --- | --- |"]
        for c in d["chronologies"]:
            pn = c["panne"]
            r = {True: f"reconnue ({c['retard_min']} min après le début)" if c["retard_min"] is not None else "reconnue",
                 False: "non signalée par le fournisseur", None: "page de statut non lisible automatiquement"}[c["reconnu"]]
            L.append(f"| Panne du {_paris(pn['debut'])} | {_duree(pn['duree_min'])}, {r} |")
        if sla:
            dispo = "—" if sla["disponibilite_pct"] is None else f"{sla['disponibilite_pct']:.3f} %".replace(".", ",")
            L += [f"| Disponibilité mesurée sur le mois | {dispo} pour {str(sla['engagement_pct']).replace('.', ',')} % promis |",
                  f"| Couverture de la mesure | {sla['couverture_pct']} % du mois |".replace(".", ","),
                  f"| Avoir | {sla['avoir_pct']:g} % de la facture" + (f", soit {sla['avoir_eur']:.2f} € |".replace(".", ",") if sla.get("avoir_eur") is not None else " (facture non renseignée) |")]
    L.append("")

    # 2. Chronologie
    if d["chronologies"]:
        L += ["## Chronologie", "", "Heures de Paris.", ""]
        for c in d["chronologies"]:
            L += [f"**Panne du {_paris(c['panne']['debut'])}**", "", "| Heure | Événement | Source |", "| --- | --- | --- |"]
            L += [f"| {_paris(h)} | {t} | {s} |" for h, t, s in c["evenements"]]
            L.append("")

    # 3. Attestation
    if d["attestation"]:
        att = en_markdown_attestation(d["attestation"])
        L += ["## Attestation de mesure", "", att, ""]

    # 4. DORA
    if d["principale"]:
        duree = d["principale"]["duree_min"]
        crit = "Oui" if duree > 120 else "Non"
        L += ["## Aide à la classification DORA", "",
              ("Le client indique que ce service soutient une fonction critique." if d["fonction_critique"]
               else "À confirmer : ce service soutient-il une fonction critique ou importante ?"), "",
              "| Critère de durée | Seuil | Mesuré | Atteint |", "| --- | --- | --- | --- |",
              f"| Indisponibilité d'un service soutenant une fonction critique | plus de 2 heures | {_duree(duree)} | "
              f"{crit if d['fonction_critique'] else crit + ' (si fonction critique)'} |",
              f"| Durée totale de l'incident | plus de 24 heures | {_duree(duree)} | {'Oui' if duree > 1440 else 'Non'} |", "",
              "Si l'incident est classé majeur : notification initiale dans les 4 heures suivant la classification "
              "(au plus tard 24 heures après la détection), rapport intermédiaire sous 72 heures, rapport final sous un mois. "
              "Les autres critères (clients touchés, données, impact économique) relèvent de l'entité.", ""]

    # 5. Avoir et lettre
    if sla and not sla["engagement_tenu"]:
        lt = lettre(sla, nom).replace("[NOM DE VOTRE ENTREPRISE]", d["client"]).replace(d["mois"], mf)
        L += ["## Avoir dû et lettre de réclamation", "",
              f"À envoyer **avant le {_date(sla['echeance'])}** ({sla['jours_restants']} jours restants)."
              + ("" if sla["verifie"] else " Conditions du contrat **à vérifier** avant l'envoi."), "",
              "\n".join("> " + x if x else ">" for x in lt.splitlines()), "",
              "C'est le client qui envoie la lettre à son fournisseur, avec ce dossier en pièce jointe.", ""]
    elif sla:
        L += ["## Avoir", "", f"L'engagement de {str(sla['engagement_pct']).replace('.', ',')} % est tenu ce mois-ci : aucun avoir n'est dû.", ""]

    L += ["## Limites", "",
          "- Mesures réalisées depuis le point de mesure d'Iris ; une panne propre au réseau du client ne s'y voit pas.",
          "- Avoir calculé sur les conditions connues du contrat ; le contrat signé fait foi.",
          "- Ce dossier constate des faits techniques. Il ne qualifie pas juridiquement l'événement.", ""]
    return "\n".join(L)


def en_markdown_attestation(a: dict) -> str:
    """L'attestation, sans son titre de premier niveau, pour l'insérer dans le dossier."""
    lignes = _attestation.en_markdown(a).splitlines()
    return "\n".join(l.replace("## ", "### ", 1) if l.startswith("## ") else l for l in lignes if not l.startswith("# "))


def ecrire(d: dict, sortie: Path) -> Path:
    sortie.mkdir(parents=True, exist_ok=True)
    nom = f"dossier-{d['fournisseur']['id']}-{d['mois']}.md"
    chemin = sortie / nom
    chemin.write_text(en_markdown(d), encoding="utf-8")
    return chemin
