"""La météo de l'IA : l'état de chaque fournisseur, en mots simples.

    python -m sonde meteo     # écrit public/meteo.json et public/minutes/AAAA-MM-JJ.json

États (du meilleur au pire) :
  soleil    tout va bien
  eclaircie ça marche, un peu plus lent que d'habitude
  nuage     ça ralentit nettement, ou quelques échecs
  orage     en panne
  inconnu   pas de mesure récente

La vigilance (vert, jaune, orange, rouge) ajoute ce qui est connu à l'avance
(événements de config/veille.yaml) et la tendance des dernières minutes.
Les prévisions sont simples et annoncées comme telles : la situation actuelle
prolongée, plus les événements connus. On ne prétend pas deviner la fin d'une panne.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median

from .rapport import lire_lignes
from .veille import lire_veille

ETATS = ["soleil", "eclaircie", "nuage", "orage"]
LIBELLES = {
    "soleil": "Tout va bien",
    "eclaircie": "Ça marche, un peu lent",
    "nuage": "Ça ralentit",
    "orage": "En panne",
    "inconnu": "Pas de mesure récente",
}
CIEL = {"soleil": "Soleil", "eclaircie": "Éclaircies", "nuage": "Nuageux", "orage": "Orage", "inconnu": "Inconnu"}
VIGILANCES = ["vert", "jaune", "orange", "rouge"]


def _h(l: dict) -> datetime:
    return datetime.fromisoformat(l["horodatage"])


def _minute(d: datetime) -> datetime:
    return d.replace(second=0, microsecond=0)


def reference_ttft(lignes: list[dict]) -> float | None:
    v = [l["ttft_ms"] for l in lignes if l.get("succes") and l.get("ttft_ms")]
    return median(v) if len(v) >= 5 else None


def juger(lignes_fenetre: list[dict], ref_ttft: float | None, r: dict) -> dict:
    """État sur une fenêtre de lignes (veille ou mesures), dans l'ordre chronologique."""
    if not lignes_fenetre:
        return {"etat": "inconnu", "taux_erreur": None, "ttft_ms": None, "lenteur": None, "appels": 0}
    n = len(lignes_fenetre)
    echecs = sum(not l.get("succes") for l in lignes_fenetre)
    taux = echecs / n
    consecutifs = 0
    for l in reversed(lignes_fenetre):
        if l.get("succes"):
            break
        consecutifs += 1
    ttfts = [l["ttft_ms"] for l in lignes_fenetre if l.get("succes") and l.get("ttft_ms")]
    t = median(ttfts) if ttfts else None
    lenteur = (t / ref_ttft) if (t and ref_ttft) else None
    if taux >= r["orage_taux_erreur"] or consecutifs >= r["orage_echecs_consecutifs"]:
        etat = "orage"
    elif taux >= r["nuage_taux_erreur"] or (lenteur or 0) >= r["nuage_lenteur"]:
        etat = "nuage"
    elif (lenteur or 0) >= r["eclaircie_lenteur"]:
        etat = "eclaircie"
    else:
        etat = "soleil"
    return {"etat": etat, "taux_erreur": round(taux, 3), "ttft_ms": round(t) if t else None,
            "lenteur": round(lenteur, 2) if lenteur else None, "appels": n}


def statut_minutes(lignes: list[dict], debut: datetime, fin: datetime) -> list[int | None]:
    """Une case par minute : 1 = réussi, 0 = échec, None = pas de mesure."""
    par_minute: dict[datetime, list[bool]] = defaultdict(list)
    for l in lignes:
        par_minute[_minute(_h(l))].append(bool(l.get("succes")))
    cases, m = [], _minute(debut)
    while m < fin:
        v = par_minute.get(m)
        cases.append(None if v is None else int(all(v)))
        m += timedelta(minutes=1)
    return cases


def incidents(lignes: list[dict], min_minutes: int = 2, maintenant: datetime | None = None) -> list[dict]:
    """Pannes = au moins `min_minutes` minutes d'échec consécutives (minutes mesurées)."""
    # Une minute est en échec si tous ses appels ont échoué (plusieurs passages par minute possibles).
    par_minute: dict[datetime, list[dict]] = defaultdict(list)
    for l in lignes:
        par_minute[_minute(_h(l))].append(l)
    lignes = []
    for m in sorted(par_minute):
        ls = par_minute[m]
        ok = [l for l in ls if l.get("succes")]
        lignes.append(ok[0] if ok else ls[-1])
    res, courant = [], None
    for l in lignes:
        if not l.get("succes"):
            if courant is None:
                courant = {"debut": l["horodatage"], "fin": l["horodatage"], "minutes": 0, "erreurs": defaultdict(int)}
            courant["fin"] = l["horodatage"]
            courant["minutes"] += 1
            courant["erreurs"][(l.get("erreur") or "échec")[:60]] += 1
        else:
            if courant and courant["minutes"] >= min_minutes:
                courant["en_cours"] = False
                res.append(courant)
            courant = None
    if courant and courant["minutes"] >= min_minutes:
        courant["en_cours"] = True
        res.append(courant)
    for i in res:
        d, f = datetime.fromisoformat(i["debut"]), datetime.fromisoformat(i["fin"])
        i["duree_min"] = int((f - d).total_seconds() // 60) + 1
        i["erreurs"] = dict(sorted(i["erreurs"].items(), key=lambda kv: -kv[1])[:3])
    return res


def disponibilite(lignes: list[dict]) -> float | None:
    if not lignes:
        return None
    return round(100 * sum(bool(l.get("succes")) for l in lignes) / len(lignes), 3)


def evenements_actifs(evenements: list[dict], fournisseur: str, debut: datetime, fin: datetime) -> list[dict]:
    out = []
    for e in evenements or []:
        if e.get("fournisseur") not in (fournisseur, "*"):
            continue
        ed, ef = datetime.fromisoformat(e["debut"]), datetime.fromisoformat(e["fin"])
        if ed < fin and ef > debut:
            out.append(e)
    return out


def vigilance(etat: dict, evts_proches: list[dict]) -> tuple[str, str | None]:
    niveau, raison = "vert", None
    if etat["etat"] == "orage":
        niveau, raison = "rouge", "Panne en cours"
    elif etat["etat"] == "nuage":
        niveau = "orange"
        if (etat.get("taux_erreur") or 0) > 0:
            raison = f"{round(100 * etat['taux_erreur'])} % d'échecs sur les dernières minutes"
        else:
            raison = f"Temps de réponse {etat['lenteur']:.1f} fois plus long que d'habitude".replace(".", ",")
    elif etat["etat"] == "eclaircie":
        niveau = "jaune"
        raison = f"Temps de réponse {etat['lenteur']:.1f} fois plus long que d'habitude".replace(".", ",")
    for e in evts_proches:
        n = e.get("niveau", "jaune")
        if VIGILANCES.index(n) > VIGILANCES.index(niveau):
            niveau, raison = n, e.get("raison")
        elif raison is None:
            raison = e.get("raison")
    return niveau, raison


def _pire(a: str, b: str) -> str:
    if a == "inconnu":
        return b
    if b == "inconnu":
        return a
    return a if ETATS.index(a) >= ETATS.index(b) else b


def chronologie(lignes: list[dict], ref: float | None, r: dict, maintenant: datetime, heures: int = 6) -> list[dict]:
    """État heure par heure, des `heures` dernières heures jusqu'à maintenant (mesuré)."""
    debut_h = maintenant.replace(minute=0, second=0, microsecond=0) - timedelta(hours=heures)
    points = []
    for k in range(heures + 1):
        a = debut_h + timedelta(hours=k)
        b = min(a + timedelta(hours=1), maintenant)
        fen = [l for l in lignes if a <= _h(l) < b]
        j = juger(fen, ref, r)
        points.append({"heure": a.isoformat(timespec="minutes"), "etat": j["etat"],
                       "ttft_ms": j["ttft_ms"], "taux_erreur": j["taux_erreur"], "nature": "mesure"})
    return points


def prevision(etat_actuel: str, evenements: list[dict], fournisseur: str, maintenant: datetime, heures: int = 3) -> list[dict]:
    """Prévision prudente : la situation actuelle prolongée d'une heure, puis les seuls événements connus."""
    points = []
    base = maintenant.replace(minute=0, second=0, microsecond=0)
    for k in range(1, heures + 1):
        a = base + timedelta(hours=k)
        evts = evenements_actifs(evenements, fournisseur, a, a + timedelta(hours=1))
        if k == 1 and etat_actuel in ("orage", "nuage"):
            etat, certitude = etat_actuel, "situation actuelle prolongée"
        elif evts:
            etat = "nuage" if any(e.get("niveau") in ("orange", "rouge") for e in evts) else "eclaircie"
            certitude = evts[0].get("raison") or "événement annoncé"
        else:
            etat, certitude = "inconnu", "rien d'annoncé"
        points.append({"heure": a.isoformat(timespec="minutes"), "etat": etat, "nature": "prevision", "certitude": certitude})
    return points


def phrase_du_jour(fournisseurs: list[dict]) -> str:
    connus = [f for f in fournisseurs if f["etat"] != "inconnu"]
    if not connus:
        return "Pas encore de mesure récente."
    pannes = [f["nom_court"] for f in connus if f["etat"] == "orage"]
    lents = [f["nom_court"] for f in connus if f["etat"] in ("nuage", "eclaircie")]
    calmes = len(connus) - len(pannes) - len(lents)

    def liste(xs):
        return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " et " + xs[-1]

    if not pannes and not lents:
        return f"Temps calme sur les {len(connus)} fournisseurs." if len(connus) > 1 else "Temps calme."
    morceaux = []
    if calmes:
        morceaux.append(f"Temps calme sur {calmes} fournisseur{'s' if calmes > 1 else ''}")
    if lents:
        morceaux.append(f"nuages sur {liste(lents)}")
    if pannes:
        morceaux.append(f"orage sur {liste(pannes)}")
    s = ", ".join(morceaux)
    return s[0].upper() + s[1:] + "."


def calculer(config: dict, conf_veille: dict, veille: list[dict], mesures: list[dict], maintenant: datetime) -> dict:
    r = conf_veille["meteo"]
    evenements = conf_veille.get("evenements") or []
    fen = timedelta(minutes=r["fenetre_min"])
    par_f = defaultdict(list)
    for l in veille:
        par_f[l["fournisseur"]].append(l)
    mes_f = defaultdict(list)
    for l in mesures:
        if l.get("type") == "mesure":
            mes_f[l["fournisseur"]].append(l)

    sortie = []
    for f in config["fournisseurs"]:
        v = sorted(par_f.get(f["id"], []), key=_h)
        m = sorted(mes_f.get(f["id"], []), key=_h)
        if not v and not m:
            continue
        recents_v = [l for l in v if _h(l) > maintenant - fen]
        source = "veille"
        if recents_v:
            fenetre = recents_v
        else:
            # Pas de veille récente : on se rabat sur la dernière mesure horaire (moins précise).
            source = "horaire"
            fenetre = [l for l in m if _h(l) > maintenant - timedelta(hours=2)]
            if fenetre:
                derniere = max(l["execution"] for l in fenetre)
                fenetre = [l for l in fenetre if l["execution"] == derniere]
        base = v if v else m
        ref = reference_ttft([l for l in base if _h(l) > maintenant - timedelta(days=7) and _h(l) <= maintenant - fen])
        j = juger(fenetre, ref, r)
        evts = evenements_actifs(evenements, f["id"], maintenant, maintenant + timedelta(hours=3))
        niv, raison = vigilance(j, evts)
        inc = incidents(v, r["incident_min_minutes"]) if v else []
        inc_30 = [i for i in inc if datetime.fromisoformat(i["fin"]) > maintenant - timedelta(days=30)]
        en_cours = next((i for i in inc_30 if i.get("en_cours")), None)
        dispo = {}
        for nom, jours in (("24h", 1), ("7j", 7), ("30j", 30)):
            dispo[nom] = disponibilite([l for l in base if _h(l) > maintenant - timedelta(days=jours)])
        sortie.append({
            "id": f["id"], "nom": f["nom"], "nom_court": f["nom"].split(" ")[0], "pays": f.get("pays"),
            "offre": (v or m)[-1].get("offre"), "source": source,
            "etat": j["etat"], "ciel": CIEL[j["etat"]], "libelle": LIBELLES[j["etat"]],
            "taux_erreur": j["taux_erreur"], "ttft_ms": j["ttft_ms"], "reference_ttft_ms": round(ref) if ref else None,
            "lenteur": j["lenteur"], "vigilance": niv, "raison": raison,
            "panne_en_cours": ({"depuis": en_cours["debut"], "minutes": en_cours["duree_min"],
                               "erreurs": en_cours["erreurs"]} if en_cours else None),
            "disponibilite": dispo,
            "incidents_30j": [{k: i[k] for k in ("debut", "fin", "duree_min", "en_cours", "erreurs")} for i in reversed(inc_30)][:20],
            "chronologie": chronologie(v or m, ref, r, maintenant) + prevision(j["etat"], evenements, f["id"], maintenant),
            "derniere_mesure": (v or m)[-1]["horodatage"],
            "modele_veille": v[-1].get("modele") if v else None,
        })
    return {
        "genere_le": maintenant.isoformat(timespec="seconds"),
        "phrase": phrase_du_jour(sortie),
        "point_de_mesure": (veille[-1].get("point") if veille else None),
        "fournisseurs": sortie,
        "methode": ("Un appel minimal par fournisseur et par minute (veille), plus 11 tâches en français "
                    "chaque heure. Orage : au moins 50 % d'échecs sur 10 minutes ou 3 échecs de suite. "
                    "Les prévisions prolongent la situation actuelle et ajoutent les événements annoncés."),
    }


def produire_meteo(dossier_donnees: Path, dossier_public: Path, config: dict, conf_veille: dict,
                   maintenant: datetime | None = None) -> dict:
    maintenant = maintenant or datetime.now(timezone.utc)
    veille = lire_veille(dossier_donnees, maintenant - timedelta(days=30), maintenant)
    mesures = lire_lignes(dossier_donnees, maintenant - timedelta(days=30))
    meteo = calculer(config, conf_veille, veille, mesures, maintenant)
    dossier_public.mkdir(parents=True, exist_ok=True)
    (dossier_public / "meteo.json").write_text(json.dumps(meteo, ensure_ascii=False, indent=1), encoding="utf-8")
    # Les minutes du jour, en résumé compact : une lettre par minute et par fournisseur.
    debut = maintenant.replace(hour=0, minute=0, second=0, microsecond=0)
    minutes = {"jour": f"{debut:%Y-%m-%d}", "legende": {"1": "réussi", "0": "échec", "-": "pas de mesure"}, "fournisseurs": {}}
    for f in config["fournisseurs"]:
        lf = [l for l in veille if l["fournisseur"] == f["id"] and _h(l) >= debut]
        if lf:
            cases = statut_minutes(lf, debut, _minute(maintenant) + timedelta(minutes=1))
            minutes["fournisseurs"][f["id"]] = "".join("-" if c is None else str(c) for c in cases)
    (dossier_public / "minutes").mkdir(exist_ok=True)
    (dossier_public / "minutes" / f"{debut:%Y-%m-%d}.json").write_text(json.dumps(minutes, ensure_ascii=False), encoding="utf-8")
    return meteo
