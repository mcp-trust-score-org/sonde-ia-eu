"""Brouillon du rapport public « Les fournisseurs d'IA européens à l'épreuve de DORA ».

Le générateur ne fait que des constats chiffrés tirés des mesures. Les passages marqués
[À COMMENTER] sont à écrire par une personne : l'interprétation, le ton et les
recommandations ne s'automatisent pas. Rien n'est publié sans relecture.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from .dossier import construire
from .rapport import _config_publique, lire_lignes


def brouillon(dossier_donnees: Path, dossier_preuves: Path, jours: int = 30) -> str:
    depuis = datetime.now(timezone.utc) - timedelta(days=jours)
    lignes = lire_lignes(dossier_donnees, depuis)
    conf = _config_publique()
    noms = {f["id"]: f["nom"] for f in conf["fournisseurs"]}
    fournisseurs = sorted({l["fournisseur"] for l in lignes if l.get("type") in ("mesure", "chemin", "empreinte")})
    dossiers = {f: construire(f, lignes, dossier_preuves) for f in fournisseurs}
    nb_mesures = sum(1 for l in lignes if l.get("type") == "mesure")
    debut = min((l["horodatage"] for l in lignes), default="")[:10]
    fin = max((l["horodatage"] for l in lignes), default="")[:10]

    o = ["# Les fournisseurs d'IA européens à l'épreuve de DORA", "",
         f"*Brouillon généré automatiquement le {datetime.now(timezone.utc):%d/%m/%Y}. Période mesurée : {debut} → {fin}. "
         f"{nb_mesures} appels mesurés, {len(fournisseurs)} hébergeur(s).*", "",
         "> À relire avant publication. Les chiffres viennent des mesures ; les passages [À COMMENTER] sont à écrire.", "",
         "## En bref", "", "[À COMMENTER : les 3 constats qui comptent pour un responsable des risques fournisseurs]", "",
         "## Pourquoi ce rapport", "",
         "Les entités financières européennes doivent surveiller en continu leurs prestataires TIC (DORA, art. 28), "
         "y compris leurs fournisseurs d'IA. Le 31 juillet 2026, les autorités européennes de supervision ont appelé à des "
         "inventaires tenus à jour des API et composants d'IA, et pointé les points de défaillance uniques partagés par plusieurs "
         "établissements. Ce rapport apporte des mesures indépendantes sur les hébergeurs d'IA européens.", "",
         "## 1. Disponibilité mesurée", "", "| Hébergeur | Modèle | Disponibilité | Plus longue série d'échecs | Offre mesurée |", "|---|---|---|---|---|"]
    for f, d in dossiers.items():
        for p in d["performance"]:
            o.append(f"| {noms.get(f, f)} | {p['modele']} | {p['disponibilite_pct']:g} % | {p['plus_longue_serie_echecs_h']} h | {', '.join(p['offres'])} |")
    o += ["", "[À COMMENTER]", "", "## 2. Par où passent vraiment les requêtes", ""]
    for f, d in dossiers.items():
        r = d["reseau"]
        if r:
            o.append(f"- **{noms.get(f, f)}** : {'; '.join(r['constats'])}")
    o += ["", "Portée : ces relevés décrivent l'entrée réseau des API, pas le lieu exact de traitement.", "", "[À COMMENTER]", "",
          "## 3. Les modèles changent-ils sans prévenir ?", ""]
    for f, d in dossiers.items():
        for s in d["stabilite"]:
            o.append(f"- {noms.get(f, f)} · {s['modele']} : {s['empreintes']} empreintes, {len(s['alertes'])} alerte(s) de changement")
        for c in d["changements_catalogue"]:
            if c["retires"]:
                o.append(f"- {noms.get(f, f)} : {len(c['retires'])} modèle(s) retiré(s) du catalogue le {c['horodatage'][:10]}")
    o += ["", "[À COMMENTER]", "", "## 4. Peut-on changer de fournisseur ?", ""]
    vus = set()
    for d in dossiers.values():
        for a in d["substituabilite"]:
            if a["modele"] in vus:
                continue
            vus.add(a["modele"])
            servi_par = {d2["fournisseur"]["nom"] for d2 in dossiers.values() if any(p["modele"] == a["modele"] for p in d2["performance"])}
            o.append(f"- {a['modele']} : servi et mesuré chez {len(servi_par)} hébergeur(s) européen(s) ({', '.join(sorted(servi_par))})")
    o += ["", "[À COMMENTER : ce que cela implique pour la stratégie de sortie et le risque de concentration]", "",
          "## Méthode", "",
          "Appels réels toutes les heures, mêmes questions pour tous, aucun appel retenté ; relevé quotidien du chemin réseau "
          "(DNS, opérateur, pays via RIPEstat, intermédiaires visibles) ; empreinte quotidienne du modèle ; manifestes quotidiens "
          "ancrés via OpenTimestamps. Code et mesures brutes publics.", ""]
    return "\n".join(o)
