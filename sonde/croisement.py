#!/usr/bin/env python3
"""Croisement « événements inattendus ↔ mesures de la sonde ».

    python -m sonde croiser      # écrit rapports/croisement.json et rapports/croisement.md

Événements croisés : public/actualites.json (collecte automatique), config/evenements.json
(ajouts à la main) et les incidents des pages de statut des fournisseurs (public/statuts.json).
Pour chaque événement et chaque fournisseur concerné, un « impact » avec son tag de relecture
(Confirmé, Probable, Possible, Aucune anomalie). Règles : regles-de-gestion/.

Rien n'est publié : le tag sert à la rédaction pour décider. Attention, ce dépôt est public :
les fichiers de rapports/ sont lisibles par tous sur GitHub.
"""
import glob
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

VERSION_REGLES = "1.3.1"

# ---------- Paramètres (reprennent regles-de-gestion/correlation-rules.yaml) ----------
FENETRE_AVANT_MIN = 15          # R2 : on regarde 15 min avant le début de l'événement…
FENETRE_APRES_MIN = 30          # … et 30 min après sa fin
DUREE_PAR_DEFAUT_H = 2          # si l'événement n'a pas de fin connue
LENTEUR_MULTIPLICATEUR = 1.3    # lenteur = temps de réponse médian > 1,3 × la référence
TAUX_ECHEC_MIN = 0.34           # erreurs = au moins 1 appel sur 3 en échec dans l'heure
MIN_POINTS_DE_MESURE = 2        # R0 : il faut 2 points de mesure (réseaux) différents

SYMPTOMES_ATTENDUS = {
    "refroidissement": {"indisponibilite"},
    "energie": {"indisponibilite"},
    "materiel": {"indisponibilite", "erreurs"},
    "reseau": {"lenteur", "erreurs", "indisponibilite"},
    "certificat": {"erreurs", "indisponibilite"},
    "logiciel": {"erreurs", "indisponibilite"},
    "maintenance": {"indisponibilite", "lenteur"},
    "cyberattaque": {"indisponibilite", "erreurs", "lenteur"},
    "incident_fournisseur": {"indisponibilite", "erreurs", "lenteur"},
    "incident_amont": {"indisponibilite", "erreurs", "lenteur"},
    "meteo": {"indisponibilite", "lenteur"},
    "autre": {"indisponibilite", "lenteur", "erreurs"},
}

LIBELLES = {
    "confirme": "Confirmé",
    "probable": "Probable",
    "possible": "Possible",
    "non_concerne": "Aucune anomalie",
}

GABARITS = {
    "confirme": "Nos mesures montrent une interruption qui correspond à l'incident reconnu par {fournisseur}.",
    "probable": "Nos mesures montrent {symptome} au même moment. {fournisseur} n'a pas encore confirmé d'incident.",
    "possible": "Un signal faible a été mesuré chez {fournisseur}. Il est en cours de vérification.",
    "non_concerne": "Aucune anomalie mesurée chez vos fournisseurs",
}

SYMPTOME_TEXTE = {
    "indisponibilite": "une interruption",
    "erreurs": "des erreurs",
    "lenteur": "un ralentissement",
}


# ---------- Utilitaires ----------
def lire_json(chemin, defaut=None):
    try:
        with open(chemin, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return defaut


def date(s):
    """Lit une date ISO (avec ou sans secondes) et la renvoie en UTC."""
    if s is None:
        return None
    d = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)


def iso(d):
    return d.strftime("%Y-%m-%dT%H:%M:%SZ") if d else None


def id_fournisseur(nom):
    """« ovhcloud (anonyme) » → « ovhcloud »."""
    return nom.split(" ")[0].strip().lower()


# ---------- Chargement des mesures ----------
def charger_minutes(dossier):
    """minutes/AAAA-MM-JJ.json → liste de mesures {fournisseur, heure, ok}."""
    mesures = []
    for chemin in sorted(glob.glob(os.path.join(dossier, "minutes", "*.json"))):
        d = lire_json(chemin, {})
        jour = d.get("jour")
        if not jour:
            continue
        minuit = date(jour + "T00:00:00+00:00")
        for fourn, ligne in d.get("fournisseurs", {}).items():
            for i, c in enumerate(ligne):
                if c in "01":
                    mesures.append({
                        "fournisseur": id_fournisseur(fourn),
                        "heure": minuit + timedelta(minutes=i),
                        "ok": c == "1",
                        "source": f"minutes/{os.path.basename(chemin)}#{i:04d}",
                    })
    return mesures


def charger_historique(dossier):
    """historique.json → points horaires {fournisseur, modele, heure, appels, reussis, ttft_median_ms}."""
    d = lire_json(os.path.join(dossier, "historique.json"), {}) or {}
    points = []
    for p in d.get("points", []):
        points.append({
            "fournisseur": id_fournisseur(p["fournisseur"]),
            "modele": p.get("modele"),
            "heure": date(p["heure"]),
            "appels": p.get("appels", 0),
            "reussis": p.get("reussis", 0),
            "ttft_median_ms": p.get("ttft_median_ms"),
        })
    return points


def evenements_officiels(statuts):
    """Les incidents des pages de statut deviennent des événements à croiser."""
    evts = []
    for fourn, info in (statuts or {}).get("fournisseurs", {}).items():
        incidents = list(info.get("incidents_30j", []))
        if info.get("incident_en_cours"):
            incidents.append(info["incident_en_cours"])
        for inc in incidents:
            evts.append({
                "id": f"statut-{fourn}-{inc.get('debut', '')}",
                "titre": inc.get("titre", "Incident déclaré"),
                "type": "incident_fournisseur",
                "fournisseurs": [fourn],
                "debut": inc.get("debut"),
                "fin": inc.get("fin"),
                "impact_officiel": inc.get("impact"),
                "sources": [{"type": "statut_fournisseur", "url": inc.get("lien"), "titre": inc.get("titre")}],
            })
    return evts


def confirmation_officielle(statuts, fourn, debut, fin):
    """R4 : un incident officiel du fournisseur chevauche-t-il la fenêtre ?"""
    info = (statuts or {}).get("fournisseurs", {}).get(fourn, {})
    incidents = list(info.get("incidents_30j", []))
    if info.get("incident_en_cours"):
        incidents.append(info["incident_en_cours"])
    for inc in incidents:
        d = date(inc.get("debut"))
        f = date(inc.get("fin")) or datetime.now(timezone.utc)
        if d and d <= fin and f >= debut:
            return inc
    return None


# ---------- Analyse d'un fournisseur pendant un événement ----------
def reference_lenteur(points, fourn, modele, avant):
    """Médiane des temps de réponse du même modèle sur les 7 jours précédents."""
    valeurs = sorted(
        p["ttft_median_ms"] for p in points
        if p["fournisseur"] == fourn and p["modele"] == modele and p["ttft_median_ms"]
        and avant - timedelta(days=7) <= p["heure"] < avant
    )
    if len(valeurs) < 3:
        return None
    return valeurs[len(valeurs) // 2]


def analyser(fourn, debut, fin, minutes, points):
    """Renvoie les anomalies mesurées dans la fenêtre, et ce qui a été observé."""
    w_debut = debut - timedelta(minutes=FENETRE_AVANT_MIN)
    w_fin = fin + timedelta(minutes=FENETRE_APRES_MIN)
    anomalies = []

    mes = [m for m in minutes if m["fournisseur"] == fourn and w_debut <= m["heure"] <= w_fin]
    for m in mes:
        if not m["ok"]:
            anomalies.append({"symptome": "indisponibilite", "heure": iso(m["heure"]),
                              "detail": "mesure en échec", "preuve": m["source"]})

    pts = [p for p in points if p["fournisseur"] == fourn
           and w_debut - timedelta(minutes=59) <= p["heure"] <= w_fin]
    for p in pts:
        if p["appels"] and (p["appels"] - p["reussis"]) / p["appels"] >= TAUX_ECHEC_MIN:
            anomalies.append({"symptome": "erreurs", "heure": iso(p["heure"]),
                              "detail": f"{p['modele']} : {p['reussis']}/{p['appels']} appels réussis",
                              "preuve": f"historique.json {iso(p['heure'])} {p['modele']}"})
        ref = reference_lenteur(points, fourn, p["modele"], p["heure"])
        if ref and p["ttft_median_ms"] and p["ttft_median_ms"] > ref * LENTEUR_MULTIPLICATEUR:
            anomalies.append({"symptome": "lenteur", "heure": iso(p["heure"]),
                              "detail": f"{p['modele']} : {p['ttft_median_ms']} ms contre {ref} ms d'habitude",
                              "preuve": f"historique.json {iso(p['heure'])} {p['modele']}"})

    return anomalies, len(mes) + len(pts)


def calculer_niveau(lieu, moment, symptome, officiel, multi_points, nb_mesures):
    if not lieu:
        return "non_concerne"
    if not moment:
        # Aucune anomalie mesurée dans la fenêtre. Sans aucune mesure, on ne sait rien :
        # l'événement part dans « non couverts », jamais en « signal faible ».
        return "non_concerne" if nb_mesures else "hors_mesures"
    if symptome and officiel and multi_points:
        return "confirme"
    if symptome and officiel:
        # Reconnu par le fournisseur, mais mesuré depuis un seul point
        return "confirme"
    if symptome and multi_points:
        return "probable"
    if symptome:
        return "probable"
    return "possible"


# ---------- Programme principal ----------
def croiser(donnees: Path, fichiers_evenements: list[Path], sortie: Path, avec_statuts: bool = True) -> dict:
    """donnees : dossier public/ de la sonde. Écrit sortie/croisement.json et .md."""
    class _A:  # garde les noms de l'ancien script autonome
        pass
    args = _A()
    args.donnees, args.sortie, args.sans_statuts = str(donnees), str(sortie), not avec_statuts

    contrats = {c["id"]: c for c in (lire_json(os.path.join(args.donnees, "contrats.json"), []) or [])}
    statuts = lire_json(os.path.join(args.donnees, "statuts.json"), {}) or {}
    minutes = charger_minutes(args.donnees)
    points = charger_historique(args.donnees)
    points_de_mesure = 1  # la sonde mesure aujourd'hui depuis un seul endroit (voir README)

    evts = []
    for fe in fichiers_evenements:
        evts += [e for e in (lire_json(str(fe), {}) or {}).get("evenements", []) if e.get("debut")]
    if not args.sans_statuts:
        evts += evenements_officiels(statuts)

    # On ne croise que les événements couverts par des mesures
    if minutes:
        debut_mesures = min(m["heure"] for m in minutes)
        fin_mesures = max(m["heure"] for m in minutes)
    else:
        debut_mesures = fin_mesures = None

    impacts = []
    non_couverts = []
    for e in evts:
        debut = date(e["debut"])
        fin = date(e.get("fin")) or debut + timedelta(hours=DUREE_PAR_DEFAUT_H)
        cibles = list(contrats) if e.get("fournisseurs") == ["tous"] else e.get("fournisseurs", [])
        couvert = bool(debut_mesures) and fin >= debut_mesures - timedelta(minutes=FENETRE_APRES_MIN) \
            and debut <= fin_mesures + timedelta(minutes=FENETRE_AVANT_MIN)

        for fourn in cibles:
            lieu = fourn in contrats
            anomalies, nb = analyser(fourn, debut, fin, minutes, points) if lieu else ([], 0)
            moment = bool(anomalies)
            attendus = SYMPTOMES_ATTENDUS.get(e.get("type", "autre"), SYMPTOMES_ATTENDUS["autre"])
            symptomes = sorted({a["symptome"] for a in anomalies})
            symptome = any(s in attendus for s in symptomes)
            inc = confirmation_officielle(statuts, fourn, debut, fin) if lieu else None
            officiel = inc is not None
            multi = points_de_mesure >= MIN_POINTS_DE_MESURE

            if not couvert:
                niveau = "hors_mesures"
            else:
                niveau = calculer_niveau(lieu, moment, symptome, officiel, multi, nb)

            nom = contrats.get(fourn, {}).get("nom", fourn)
            texte = GABARITS.get(niveau, "").format(
                fournisseur=nom, symptome=SYMPTOME_TEXTE.get(symptomes[0], "une anomalie") if symptomes else "")

            alertes_relecture = []
            if e.get("exemple"):
                alertes_relecture.append("Événement d'EXEMPLE : à remplacer par un fait réel et sourcé.")
            if e.get("source_auto") == "gdelt":
                presse = e.get("presse") or {}
                alertes_relecture.append("Source presse : lire l'article. L'heure retenue est celle de la parution "
                                         "(fenêtre élargie en amont), pas celle de la panne.")
                if presse.get("nb_medias", 1) < 2:
                    alertes_relecture.append("Un seul média en parle : chercher une seconde source avant de publier.")
            if lieu and not multi:
                alertes_relecture.append("Mesures depuis un seul point : une panne locale de la sonde ressemblerait à une panne du fournisseur.")
            if lieu and nb and nb < 3:
                alertes_relecture.append(f"Seulement {nb} mesure(s) dans la fenêtre : peu de recul.")
            if officiel and not moment and couvert and nb:
                alertes_relecture.append("Le fournisseur a déclaré un incident, mais la sonde n'a rien vu (modèle ou région non mesurés ?).")
            if lieu and not contrats[fourn].get("verifie", False):
                alertes_relecture.append("Contrat non vérifié : ne pas annoncer d'avoir.")

            if niveau == "hors_mesures":
                non_couverts.append({"evenement": e.get("titre"), "fournisseur": nom, "debut": iso(debut),
                                     "raison": "aucune mesure de la sonde sur cette période" if not couvert
                                     else "aucune mesure de la sonde pendant l'événement (trou entre deux relevés)"})
                continue

            impacts.append({
                "impact_id": f"imp-{e['id']}-{fourn}",
                "client_id": "sonde-publique",
                "regles_version": VERSION_REGLES,
                "evenement": {
                    "id": e["id"], "titre": e.get("titre"), "type": e.get("type"),
                    "fournisseur": nom, "debut": iso(debut), "fin": iso(fin),
                    "exemple": bool(e.get("exemple")), "sources": e.get("sources", []),
                    "source_auto": e.get("source_auto"), "pourquoi": e.get("pourquoi"),
                    **({"presse": e["presse"]} if e.get("presse") else {}),
                },
                "correlation": {
                    "lieu": lieu, "moment": moment, "symptome": symptome, "officiel": officiel,
                    "multi_points": multi, "niveau": niveau, "texte_propose": texte,
                },
                "mesures": {
                    "mesures_dans_la_fenetre": nb,
                    "symptomes": symptomes,
                    "anomalies": anomalies,
                    "incident_officiel": inc,
                },
                "alertes_relecture": alertes_relecture,
                "statut_editorial": "a_relire",
                "valide_par": None,
                "valide_le": None,
            })

    os.makedirs(args.sortie, exist_ok=True)
    resultat = {
        "genere_le": iso(datetime.now(timezone.utc)),
        "regles_version": VERSION_REGLES,
        "periode_mesuree": {"debut": iso(debut_mesures), "fin": iso(fin_mesures)},
        "impacts": impacts,
        "non_couverts": non_couverts,
    }
    with open(os.path.join(args.sortie, "croisement.json"), "w", encoding="utf-8") as f:
        json.dump(resultat, f, ensure_ascii=False, indent=2)
    with open(os.path.join(args.sortie, "croisement.md"), "w", encoding="utf-8") as f:
        f.write(rapport_lisible(resultat))

    return resultat


def rapport_lisible(r):
    lignes = [
        "# Croisement événements ↔ mesures — à relire",
        "",
        f"Généré le {r['genere_le']} · règles {r['regles_version']} · "
        f"mesures du {r['periode_mesuree']['debut']} au {r['periode_mesuree']['fin']}",
        "",
        "Le tag n'est jamais publié : il sert à décider. Rien n'est publié sans validation.",
        "",
        "| Tag | Fournisseur | Événement | Début (UTC) | Critères | Texte proposé |",
        "|---|---|---|---|---|---|",
    ]
    for i in r["impacts"]:
        c = i["correlation"]
        crit = " · ".join(f"{'✓' if c[k] else '○'} {t}" for k, t in
                          [("lieu", "Lieu"), ("moment", "Moment"), ("symptome", "Symptôme"), ("officiel", "Officiel")])
        lignes.append(
            f"| **{LIBELLES.get(c['niveau'], 'Hors mesures')}** | {i['evenement']['fournisseur']} | "
            f"{i['evenement']['titre']} | {i['evenement']['debut']} | {crit} | {c['texte_propose'] or '—'} |")
    if r["non_couverts"]:
        lignes += ["", f"_{len(r['non_couverts'])} événement(s) tombent hors de la période mesurée par la sonde : non croisés._"]
    lignes += ["", "## Détail", ""]
    for i in r["impacts"]:
        lignes.append(f"### {i['evenement']['titre']} — {i['evenement']['fournisseur']}")
        lignes.append(f"- Tag : **{LIBELLES.get(i['correlation']['niveau'], 'Hors mesures')}**")
        lignes.append(f"- Mesures dans la fenêtre : {i['mesures']['mesures_dans_la_fenetre']}")
        for a in i["mesures"]["anomalies"]:
            lignes.append(f"- Anomalie : {a['symptome']} à {a['heure']} ({a['detail']}) — preuve : `{a['preuve']}`")
        if i["mesures"]["incident_officiel"]:
            inc = i["mesures"]["incident_officiel"]
            lignes.append(f"- Incident officiel : {inc.get('titre')} ({inc.get('debut')} → {inc.get('fin')}, impact {inc.get('impact')})")
        for al in i["alertes_relecture"]:
            lignes.append(f"- ⚠️ {al}")
        lignes.append("")
    return "\n".join(lignes)
