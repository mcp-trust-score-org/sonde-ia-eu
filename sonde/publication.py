"""Publication : un brouillon validé passe sur le site.

    python -m sonde publier --rubrique une [--date 2026-11-22] [--numero 1] [--forcer]
    python -m sonde publier --retirer <id>

Le brouillon est lu dans redaction/propositions/<date>.json et ajouté à iris/publies.json,
que le site lit au chargement. Rien n'est publié sans cette commande : c'est la décision
de la rédaction (dans GitHub : Actions → « Publier un brouillon » → Run workflow).

Garde-fous : on ne publie pas une fiche vide (le rédacteur n'a pas écrit l'article), ni un
brouillon qui contient encore des [À VÉRIFIER] — sauf avec --forcer.
Le tag de confiance n'est jamais publié : il ne sert qu'à la relecture.
"""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")
RUBRIQUES = {"une": "une", "a la une": "une", "à la une": "une", "tous_connectes": "tous_connectes",
             "tous connectes": "tous_connectes", "tous connectés": "tous_connectes", "detour": "detour",
             "le detour": "detour", "le détour": "detour", "détour": "detour"}
IMAGES_DETOUR = {"réseau": "reseau", "reseau": "reseau", "énergie": "energie", "energie": "energie",
                 "ia": "innovation", "jeux vidéo": "jeux-video", "société": "societe", "societe": "societe",
                 "cybersécurité": "savoir", "santé": "sante", "politique": "politique", "médias": "medias-tv"}
NIVEAUX_SITE = {  # tag interne → encadré Premium (le tag lui-même n'est jamais affiché)
    "Confirmé": ("red", "Vos fournisseurs ont été touchés"),
    "Probable": ("orange", "Vos fournisseurs ont probablement été touchés"),
    "Possible": ("orange", "Un signal faible chez vos fournisseurs"),
    "Aucune anomalie": ("green", "Aucune anomalie mesurée chez vos fournisseurs"),
    "Non mesuré": ("green", "Notre sonde n'a pas mesuré cet événement"),
}


class RefusPublication(Exception):
    """Le brouillon ne peut pas être publié tel quel : le message dit pourquoi."""


def _slug(texte: str) -> str:
    t = unicodedata.normalize("NFKD", re.sub(r"<[^>]+>", " ", texte or "")).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:50] or "article"


def _texte_brut(x) -> str:
    return re.sub(r"<[^>]+>", " ", json.dumps(x, ensure_ascii=False))


def _impact(p: dict) -> dict:
    """L'encadré « Quel impact chez moi ? » (Premium), tiré des faits de la fiche."""
    niveau, statut = NIVEAUX_SITE.get(p.get("tag_interne") or "", ("green", "Aucune anomalie mesurée chez vos fournisseurs"))
    f = p.get("fiche") or {}
    lignes = []
    if f.get("fournisseurs_concernes"):
        lignes.append(["Fournisseur concerné", ", ".join(f["fournisseurs_concernes"])])
    if f.get("debut"):
        lignes.append(["Événement", f"du {f['debut']}" + (f" au {f['fin']}" if f.get("fin") else "")])
    mesures = f.get("mesures_de_la_sonde")
    if isinstance(mesures, list) and mesures:
        lignes.append(["Ce que la sonde a vu", mesures[0].get("ce_que_la_sonde_a_vu") or "—"])
    elif isinstance(mesures, str):
        lignes.append(["Ce que la sonde a vu", mesures])
    return {"status": statut, "level": niveau,
            "rows": lignes or [["Ce que la sonde a vu", statut]],
            "ctas": [["#meteo", "Voir ma météo →", "btn-yellow"], ["#rapports", "Mes rapports", "btn-outline"]]}


def vers_le_site(p: dict, date: str) -> dict:
    """Un brouillon (redaction/propositions) → un article au format du site (iris/main.js)."""
    rub = p["rubrique"]
    if rub == "detour":
        liens = [l for l in p.get("liens") or [] if l.get("url")]
        if not liens:
            raise RefusPublication("Ce Détour ne contient aucun lien.")
        sans_phrase = [l["titre"] for l in liens if not l.get("pourquoi")]
        if sans_phrase:
            raise RefusPublication(f"{len(sans_phrase)} lien(s) sans phrase « pourquoi le lire » : à écrire avant publication.")
        return {"rubrique": "detour", "date": date, "liens": [{
            "source": l["media"], "cat": l.get("categorie") or "À lire",
            "img": IMAGES_DETOUR.get((l.get("categorie") or "").lower(), "innovation"),
            "title": l["titre"] + (f" {l['mention']}" if l.get("mention") else ""), "why": l["pourquoi"], "url": l["url"],
            "date": date,
        } for l in liens]}
    a = p.get("article") or {}
    if not a.get("title"):
        raise RefusPublication("Ce brouillon n'a pas été rédigé (fiche seule) : rien à publier.")
    art = {
        "id": f"{date.replace('-', '')}-{_slug(a['title'])}",
        "rubrique": rub, "date": date,
        "tag": a.get("tag") or ("À la une" if rub == "une" else "Tous connectés"),
        "tagClass": "flag-red" if rub == "une" else "flag-cream",
        "img": p.get("image") or "assets/photos/innovation.jpg",
        "time": "4 min", "title": a["title"], "chapo": a.get("chapo", ""),
        "fait": a.get("fait") or [], "consequence": a.get("consequence") or [], "lien": a.get("lien") or [],
        "sources": [{"label": s.get("label") or s.get("url"), "url": s["url"]} for s in a.get("sources") or [] if s.get("url")],
        "mini": a.get("une_mini") or {},
    }
    if rub == "tous_connectes":
        art["audience"] = "public"
        art["reflexes"] = a.get("reflexes") or []
        if a.get("reflexe_de_la_semaine"):
            art["reflexe_semaine"] = a["reflexe_de_la_semaine"]
    else:
        art["impact"] = _impact(p)
    return art


def publier(racine: Path, rubrique: str, date: str | None = None, numero: int = 1, forcer: bool = False,
            maintenant: datetime | None = None) -> dict:
    maintenant = maintenant or datetime.now(timezone.utc)
    rub = RUBRIQUES.get((rubrique or "").strip().lower())
    if not rub:
        raise RefusPublication(f"Rubrique inconnue : {rubrique!r} (une, tous_connectes ou detour).")
    date = (date or "").strip() or maintenant.astimezone(PARIS).date().isoformat()
    chemin = racine / "redaction" / "propositions" / f"{date}.json"
    if not chemin.exists():
        raise RefusPublication(f"Pas de brouillons pour le {date}.")
    props = json.loads(chemin.read_text(encoding="utf-8"))
    candidats = [p for p in props.get("propositions") or [] if p.get("rubrique") == rub]
    if not candidats:
        raise RefusPublication(f"Pas de brouillon « {rub} » le {date}.")
    if not 1 <= numero <= len(candidats):
        raise RefusPublication(f"Il n'y a que {len(candidats)} brouillon(s) « {rub} » le {date}.")
    p = candidats[numero - 1]
    article = vers_le_site(p, date)
    if not forcer and "À VÉRIFIER" in _texte_brut(article).upper():
        raise RefusPublication("Le brouillon contient encore des [À VÉRIFIER]. Corrigez-les, ou cochez « forcer ».")

    sortie = racine / "iris" / "publies.json"
    publies = json.loads(sortie.read_text(encoding="utf-8")) if sortie.exists() else {"une": [], "tous_connectes": [], "detour": []}
    if rub == "detour":
        deja = {l["url"] for l in publies.get("detour") or []}
        publies["detour"] = [l for l in article["liens"] if l["url"] not in deja] + (publies.get("detour") or [])
        ident = f"detour-{date}"
    else:
        publies[rub] = [article] + [x for x in publies.get(rub) or [] if x.get("id") != article["id"]]
        ident = article["id"]
    publies["mis_a_jour"] = maintenant.isoformat(timespec="seconds")
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text(json.dumps(publies, ensure_ascii=False, indent=1), encoding="utf-8")

    p["statut"] = "publie"
    p["publie_le"] = maintenant.isoformat(timespec="seconds")
    chemin.write_text(json.dumps(props, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"id": ident, "rubrique": rub, "date": date, "alertes": p.get("alertes_charte") or [],
            "titre": re.sub(r"<[^>]+>", " ", article.get("title") or f"{len(article.get('liens', []))} lien(s)")}


def retirer(racine: Path, quoi: str) -> int:
    """Retire du site : « dernier-une », « dernier-tous_connectes », « dernier-detour » (la dernière
    sélection), ou l'identifiant d'un article. Renvoie le nombre d'éléments retirés."""
    sortie = racine / "iris" / "publies.json"
    if not sortie.exists():
        return 0
    publies = json.loads(sortie.read_text(encoding="utf-8"))
    taille = lambda: sum(len(publies.get(k) or []) for k in ("une", "tous_connectes", "detour"))
    avant = taille()
    quoi = (quoi or "").strip()
    if quoi.startswith("dernier-"):
        k = RUBRIQUES.get(quoi[8:].replace("_", " ").strip(), quoi[8:])
        liste = publies.get(k) or []
        if k == "detour" and liste:
            derniere = liste[0].get("date")
            publies[k] = [l for l in liste if l.get("date") != derniere]
        else:
            publies[k] = liste[1:]
    else:
        for k in ("une", "tous_connectes"):
            publies[k] = [x for x in publies.get(k) or [] if x.get("id") != quoi]
    sortie.write_text(json.dumps(publies, ensure_ascii=False, indent=1), encoding="utf-8")
    return avant - taille()
