"""Le tableau de pilotage d'Iris : écrit iris/donnees/pilotage.json (appelé par `python -m sonde site`).

Trois questions, sans rien deviner au-delà des fichiers du dépôt :
  - Rédaction : jour par jour, ce que la charte prévoit (config/redaction.yaml, rubrique « rythme »)
    et où en est chaque article : brouillon prêt, à vérifier, publié, écarté… ou rédaction pas lancée.
  - Sonde : combien de passages de la mesure (prévue toutes les heures) et de la veille (prévue toutes
    les 10 minutes) ont vraiment eu lieu, et les interruptions de plus de 2 heures.
  - Site : quand les données et les articles ont été mis à jour pour la dernière fois.
L'audience (les articles les plus lus) n'est pas ici : elle est comptée par le site (api/vue.js) et
lue par la page de pilotage avec sa clé (api/stats.js).
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")
NOMS = {"une": "À la une", "tous_connectes": "Tous connectés", "detour": "Le Détour",
        "et_si": "Et si… ? (Iris Plus)", "meteo_semaine": "Météo de la semaine (Iris Plus)", "et_si_verif": "Et si… · revérification"}
INTERRUPTION_H = 2


def _lire(chemin: Path, defaut=None):
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return defaut


def _quand(texte: str | None) -> datetime | None:
    try:
        return datetime.fromisoformat(texte) if texte else None
    except ValueError:
        return None


def attendus(jour: date, rythme: dict) -> list[dict]:
    """Ce que la charte prévoit ce jour-là. « optionnel » : seulement s'il y a un événement."""
    j = jour.weekday()
    sortie = []
    une = rythme.get("une") or {}
    if une.get("bilan_le") == j:
        sortie.append({"rubrique": "une", "quoi": "Bilan de la semaine"})
    else:
        sortie.append({"rubrique": "une", "quoi": "À chaud, s'il y a un incident", "optionnel": True})
    if j in ((rythme.get("tous_connectes") or {}).get("jours") or []):
        reflexe = (rythme.get("tous_connectes") or {}).get("reflexe_de_la_semaine") == j
        sortie.append({"rubrique": "tous_connectes", "quoi": "Sujet du jour" + (" + réflexe de la semaine" if reflexe else "")})
    if j in ((rythme.get("detour") or {}).get("jours") or []):
        sortie.append({"rubrique": "detour", "quoi": "Sélection de liens"})
    if j == 0 and jour.day <= 7:
        sortie.append({"rubrique": "et_si", "quoi": "Nouveau « Et si… ? »"})
    if j == 6:
        sortie.append({"rubrique": "meteo_semaine", "quoi": "Météo de la semaine (à écrire et déposer)"})
    return sortie


def _titre(article: dict) -> str:
    """Le titre d'un article en ligne, sans balises (le Détour : celui du premier lien)."""
    t = article.get("title") or ""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", re.sub(r"<br\s*/?>", " ", t))).strip()


def _etat_proposition(p: dict) -> str:
    if p.get("statut") == "publie":
        return "publié"
    if p.get("statut") == "ecarte":
        return "écarté"
    if p.get("alertes_charte"):
        return "à vérifier"
    return "brouillon prêt"


def redaction(racine: Path, aujourd_hui: date, rythme: dict, avant: int = 13, apres: int = 6,
              suivi_depuis: str | None = None) -> list[dict]:
    plus = _lire(racine / "iris" / "plus.json", {}) or {}
    meteos = {e.get("publie_le") for e in plus.get("meteo_semaine") or []}
    etsis = {a.get("publie_le"): a for a in plus.get("et_si") or []}
    # Ce qui est vraiment en ligne fait foi (iris/publies.json) : un article peut avoir été publié sans passer
    # par « Publier un brouillon » (article écrit à la main et déposé), et son brouillon n'est alors jamais marqué.
    publies = _lire(racine / "iris" / "publies.json", {}) or {}
    en_ligne = {}
    for rub in ("une", "tous_connectes", "detour"):
        for x in publies.get(rub) or []:
            if x.get("date"):
                en_ligne.setdefault((rub, str(x["date"])[:10]), x)
    jours = []
    for i in range(-avant, apres + 1):
        jour = aujourd_hui + timedelta(days=i)
        iso = jour.isoformat()
        fichier = racine / "redaction" / "propositions" / f"{iso}.json"
        props = (_lire(fichier, {}) or {}).get("propositions") or []
        lancee = fichier.exists()
        lignes, vues = [], set()
        for a in attendus(jour, rythme):
            rub = a["rubrique"]
            ligne = {"rubrique": rub, "nom": NOMS.get(rub, rub), "quoi": a["quoi"], "optionnel": bool(a.get("optionnel"))}
            if suivi_depuis and iso < suivi_depuis and not any(p.get("rubrique") == rub for p in props) \
                    and not (rub == "meteo_semaine" and iso in meteos):
                ligne["etat"] = "avant le lancement"
            elif (rub, iso) in en_ligne:
                ligne["etat"] = "publié"
                ligne["titre"] = _titre(en_ligne[(rub, iso)])
            elif rub == "meteo_semaine":
                ligne["etat"] = "publié" if iso in meteos else ("à venir" if jour >= aujourd_hui else "non publié")
            elif rub == "et_si" and iso in etsis:
                ligne["etat"] = "publié"
            elif jour > aujourd_hui:
                ligne["etat"] = "à venir"
            else:
                trouves = [p for p in props if p.get("rubrique") == rub]
                vues.update(id(p) for p in trouves)
                if trouves:
                    etats = [_etat_proposition(p) for p in trouves]
                    ligne["etat"] = next((e for e in ("publié", "à vérifier", "brouillon prêt") if e in etats), etats[0])
                    ligne["brouillons"] = len(trouves)
                    if ligne["etat"] in ("brouillon prêt", "à vérifier") and jour < aujourd_hui:
                        # « À chaud » est facultatif : ne pas le publier est un choix de la rédaction, pas un raté.
                        ligne["etat"] = "non retenu" if ligne["optionnel"] else "non publié"
                elif not lancee and jour <= aujourd_hui:
                    ligne["etat"] = "rédaction pas lancée" if not ligne["optionnel"] else "rien (pas d'incident ?)"
                else:
                    ligne["etat"] = "rien (pas d'incident)" if ligne["optionnel"] else "aucun brouillon"
            lignes.append(ligne)
        for (rub, d), x in en_ligne.items():  # publié un jour où la charte ne l'attendait pas
            if d == iso and rub not in [l["rubrique"] for l in lignes]:
                lignes.append({"rubrique": rub, "nom": NOMS.get(rub, rub), "quoi": "En plus", "etat": "publié",
                               "titre": _titre(x)})
        for p in props:                      # brouillons en plus de la charte (revérification, etc.)
            if id(p) not in vues and p.get("rubrique") not in [l["rubrique"] for l in lignes]:
                lignes.append({"rubrique": p.get("rubrique"), "nom": NOMS.get(p.get("rubrique"), p.get("rubrique")),
                               "quoi": "En plus", "etat": _etat_proposition(p)})
        jours.append({"date": iso, "aujourdhui": i == 0, "redaction_lancee": lancee, "lignes": lignes})
    return jours


def sonde(racine: Path, maintenant: datetime, jours: int = 7) -> dict:
    debut = maintenant - timedelta(days=jours)
    veille, mesures = defaultdict(set), defaultdict(set)
    passages = []
    for f in sorted((racine / "data" / "veille").glob("*.jsonl"))[-(jours + 1):]:
        for l in f.read_text(encoding="utf-8").splitlines():
            try:
                d = json.loads(l)
            except ValueError:
                continue
            q = _quand(d.get("horodatage"))
            if d.get("type") == "veille" and q and q >= debut:
                cle = q.replace(second=0, microsecond=0)
                if cle not in passages:
                    passages.append(cle)
                veille[q.astimezone(PARIS).date().isoformat()].add(cle)
    for f in sorted((racine / "data").glob("*.jsonl"))[-2:]:
        for l in f.read_text(encoding="utf-8").splitlines():
            try:
                d = json.loads(l)
            except ValueError:
                continue
            q = _quand(d.get("horodatage"))
            if d.get("type") == "mesure" and q and q >= debut:
                mesures[q.astimezone(PARIS).date().isoformat()].add(d.get("execution") or q.strftime("%Y%m%d%H"))
    passages.sort()
    trous = []
    reperes = (passages or [debut]) + [maintenant]   # le début de la fenêtre n'est pas une interruption
    for a, b in zip(reperes, reperes[1:]):
        if (b - a) >= timedelta(hours=INTERRUPTION_H):
            trous.append({"de": a.isoformat(timespec="minutes"), "a": b.isoformat(timespec="minutes"),
                          "heures": round((b - a).total_seconds() / 3600, 1), "en_cours": b == maintenant})
    derniere_veille = passages[-1] if passages else None
    derniere_mesure = None
    for f in sorted((racine / "data").glob("*.jsonl"))[-1:]:
        for l in reversed(f.read_text(encoding="utf-8").splitlines()):
            d = json.loads(l)
            if d.get("type") == "mesure":
                derniere_mesure = _quand(d.get("horodatage"))
                break

    def etat(q, ok_h, retard_h):
        if not q:
            return "arrêtée"
        h = (maintenant - q).total_seconds() / 3600
        return "ok" if h <= ok_h else "en retard" if h <= retard_h else "arrêtée"

    jours_l = []
    for i in range(jours - 1, -1, -1):
        j = (maintenant.astimezone(PARIS).date() - timedelta(days=i)).isoformat()
        jours_l.append({"date": j, "veille": len(veille.get(j, ())), "veille_prevue": 144,
                        "mesures": len(mesures.get(j, ())), "mesures_prevues": 24})
    return {
        "veille": {"derniere": derniere_veille.isoformat(timespec="minutes") if derniere_veille else None,
                   "etat": etat(derniere_veille, 1, 3), "prevue": "toutes les 10 minutes"},
        "mesure": {"derniere": derniere_mesure.isoformat(timespec="minutes") if derniere_mesure else None,
                   "etat": etat(derniere_mesure, 2, 6), "prevue": "toutes les heures"},
        "jours": jours_l,
        "interruptions": trous[-10:],
    }


def site(racine: Path) -> dict:
    publies = _lire(racine / "iris" / "publies.json", {}) or {}
    meteo = _lire(racine / "iris" / "donnees" / "meteo.json", {}) or {}
    plus = _lire(racine / "iris" / "plus.json", {}) or {}
    derniers = {}
    for rub in ("une", "tous_connectes", "detour"):
        liste = publies.get(rub) or []
        if liste:
            x = liste[0]
            derniers[rub] = {"nom": NOMS[rub], "titre": x.get("title") or x.get("titre"), "publie_le": x.get("publie_le"),
                             "nombre": len(liste)}
        else:
            derniers[rub] = {"nom": NOMS[rub], "titre": None, "publie_le": None, "nombre": 0}
    m = (plus.get("meteo_semaine") or [{}])[0]
    e = (plus.get("et_si") or [{}])[0]
    return {
        "donnees_meteo": meteo.get("genere_le"),
        "articles_mis_a_jour": publies.get("mis_a_jour"),
        "derniers": derniers,
        "iris_plus": {"meteo": {"titre": m.get("titre"), "publie_le": m.get("publie_le")},
                      "et_si": {"titre": e.get("question"), "publie_le": e.get("publie_le")},
                      "prochains": plus.get("prochains_et_si") or []},
    }


def produire(racine: Path, sortie: Path, maintenant: datetime | None = None) -> dict:
    maintenant = maintenant or datetime.now(timezone.utc)
    try:
        import yaml
        conf = yaml.safe_load((racine / "config" / "redaction.yaml").read_text(encoding="utf-8")) or {}
    except (OSError, ValueError, ImportError):
        conf = {}
    rythme = conf.get("rythme") or {}
    depuis = str((conf.get("pilotage") or {}).get("suivi_depuis") or "") or None
    res = {"genere_le": maintenant.isoformat(timespec="seconds"), "suivi_depuis": depuis,
           "redaction": redaction(racine, maintenant.astimezone(PARIS).date(), rythme, suivi_depuis=depuis),
           "sonde": sonde(racine, maintenant), "site": site(racine)}
    (sortie / "pilotage.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res
