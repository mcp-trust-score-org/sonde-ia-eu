"""Publication : un brouillon validé passe sur le site.

    python -m sonde publier --rubrique une [--date 2026-11-22] [--numero 1] [--carte] [--forcer]
    python -m sonde publier --rubrique detour --liens "1, 3, 4"
    python -m sonde publier --retirer <id>

Le brouillon est lu dans redaction/propositions/<date>.json et ajouté à iris/publies.json,
que le site lit au chargement. Rien n'est publié sans cette commande : c'est la décision
de la rédaction (dans GitHub : Actions → « Publier un brouillon » → Run workflow).

Date : un article garde la date de son brouillon. Publier le brouillon d'un jour passé l'ajoute
aux archives de ce jour-là (sans prendre le grand titre du jour, sans notification), et son
« aujourd'hui » se lit par rapport à cette date.

Emplacement : par défaut, l'article le plus récent devient le grand titre de sa rubrique
(l'ancien grand titre descend en première carte). Avec --carte, il ne va que dans les cartes.

Garde-fous : on ne publie pas une fiche vide (le rédacteur n'a pas écrit l'article), ni —
sauf avec --forcer — un brouillon qui contient encore des [À VÉRIFIER] ou des points « à vérifier » du rédacteur, un titre périmé
(« sort ce jeudi » publié un samedi) ou un sujet déjà en ligne dans la rubrique.
Le tag de confiance n'est jamais publié : il ne sert qu'à la relecture.
"""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .coherence import doublon, titre_perime, titres_en_ligne
from .flux import ecrire_flux

PARIS = ZoneInfo("Europe/Paris")
RUBRIQUES = {"une": "une", "a la une": "une", "à la une": "une", "tous_connectes": "tous_connectes",
             "tous connectes": "tous_connectes", "tous connectés": "tous_connectes", "detour": "detour",
             "le detour": "detour", "le détour": "detour", "détour": "detour"}
# Catégorie du lien (écrite librement par le rédacteur) → image de la banque iris/assets/photos.
# On compare sans accents ni majuscules ; si la catégorie est inconnue, on cherche aussi dans le titre.
IMAGES_DETOUR = [
    (("puce", "puces", "semi conducteur", "semi conducteurs", "semiconducteur", "semiconducteurs", "gpu", "gpus",
      "processeur", "processeurs", "nvidia", "materiel", "hardware", "chip", "chips", "tsmc"), "puces"),
    (("regulation", "reglementation", "droit", "justice", "loi", "juridique", "tribunal", "dma", "rgpd",
      "concurrence", "amende"), "regulation"),
    (("cinema", "film", "serie", "streaming video"), "pop-culture-cinema"),
    (("musique", "audio", "podcast"), "pop-culture-vinyle"),
    (("concert", "festival", "spectacle"), "pop-culture-concert"),
    (("bd", "bande dessinee", "manga", "livre", "edition", "litterature"), "pop-culture-bd"),
    (("jeu video", "jeux video", "jeux", "gaming"), "jeux-video"),
    (("logiciel", "cloud", "open source", "developpement", "application", "ia", "intelligence artificielle",
      "algorithme"), "logiciel"),
    (("reseau", "telecom", "internet", "fibre", "cable", "satellite", "5g", "connectivite"), "reseau"),
    (("energie", "electricite", "datacenter", "data center", "climat", "panne de courant"), "energie"),
    (("sante", "hopital", "medecin", "medical"), "sante"),
    (("politique", "election", "gouvernement", "souverainete"), "politique"),
    (("media", "medias", "presse", "television", "journalisme"), "medias-tv"),
    (("cybersecurite", "securite", "piratage", "cyberattaque", "donnees", "vie privee"), "savoir"),
    (("savoir", "science", "sciences", "mathematiques", "recherche", "education", "ecole"), "savoir"),
    (("societe", "travail", "emploi", "consommation", "vie quotidienne"), "societe"),
    (("espace", "innovation", "futur", "prospective"), "innovation"),
]


def _sans_accents(t: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", (t or "").lower()) if unicodedata.category(c) != "Mn")


def image_detour(categorie: str | None, titre: str | None = None) -> str:
    """L'image la plus parlante pour un lien du Détour : d'abord par sa catégorie, sinon par les mots de son titre."""
    import re
    for texte in (categorie, titre):
        mots = " " + re.sub(r"[^a-z0-9]+", " ", _sans_accents(texte or "")) + " "
        for cles, image in IMAGES_DETOUR:
            if any(f" {c} " in mots for c in cles):
                return image
    return "innovation"
NIVEAUX_SITE = {  # tag interne → encadré Premium (le tag lui-même n'est jamais affiché)
    "Confirmé": ("red", "Les fournisseurs suivis par Iris ont été touchés"),
    "Probable": ("orange", "Les fournisseurs suivis ont probablement été touchés"),
    "Possible": ("orange", "Un signal faible chez les fournisseurs suivis"),
    "Aucune anomalie": ("green", "Aucune anomalie mesurée chez les fournisseurs suivis"),
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
    niveau, statut = NIVEAUX_SITE.get(p.get("tag_interne") or "", ("green", "Aucune anomalie mesurée chez les fournisseurs suivis"))
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


def garder_liens(liens: list, choix: str | None) -> list:
    """« 1, 3, 4 » → ces liens-là, dans l'ordre du brouillon. Vide ou absent : tous."""
    choix = (choix or "").strip()
    if not choix:
        return liens
    try:
        numeros = sorted({int(x) for x in choix.replace(";", ",").replace(" ", ",").split(",") if x.strip()})
    except ValueError:
        raise RefusPublication(f"« Liens à garder » illisible : {choix!r}. Écrivez par exemple 1, 3, 4.")
    hors = [k for k in numeros if not 1 <= k <= len(liens)]
    if hors:
        raise RefusPublication(f"Ce Détour n'a que {len(liens)} lien(s) : pas de n° {', '.join(map(str, hors))}.")
    return [liens[k - 1] for k in numeros]


def vers_le_site(p: dict, date: str, liens_a_garder: str | None = None) -> dict:
    """Un brouillon (redaction/propositions) → un article au format du site (iris/main.js)."""
    rub = p["rubrique"]
    if rub == "detour":
        liens = garder_liens([l for l in p.get("liens") or [] if l.get("url")], liens_a_garder)
        if not liens:
            raise RefusPublication("Ce Détour ne contient aucun lien.")
        sans_phrase = [l["titre"] for l in liens if not l.get("pourquoi")]
        if sans_phrase:
            raise RefusPublication(f"{len(sans_phrase)} lien(s) sans phrase « pourquoi le lire » : à écrire avant publication.")
        return {"rubrique": "detour", "date": date, "liens": [{
            "source": l["media"], "cat": l.get("categorie") or "À lire",
            "img": image_detour(l.get("categorie"), l.get("titre")),
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
        if a.get("reflexes_intro"):
            art["reflexes_intro"] = a["reflexes_intro"]
        if a.get("reflexe_de_la_semaine"):
            art["reflexe_semaine"] = a["reflexe_de_la_semaine"]
    else:
        art["impact"] = _impact(p)
    return art


def publier(racine: Path, rubrique: str, date: str | None = None, numero: int = 1, forcer: bool = False,
            maintenant: datetime | None = None, carte: bool = False, liens: str | None = None) -> dict:
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
    article = vers_le_site(p, date, liens)
    if not forcer and "À VÉRIFIER" in _texte_brut(article).upper():
        raise RefusPublication("Le brouillon contient encore des [À VÉRIFIER]. Corrigez-les, ou cochez « forcer ».")
    ligne = [a for a in p.get("alertes_charte") or [] if str(a).startswith("Ligne éditoriale")]
    if not forcer and ligne:
        raise RefusPublication(ligne[0] + " Écartez ce brouillon, ou cochez « forcer » si la rédaction l'assume.")
    a_verifier = [str(x).strip() for x in (p.get("article") or {}).get("a_verifier") or [] if str(x).strip()]
    if not forcer and a_verifier:
        raise RefusPublication(f"Le rédacteur a laissé {len(a_verifier)} point(s) à vérifier : " + " ; ".join(a_verifier)[:300]
                               + ". Vérifiez-les, puis cochez « forcer ».")
    if rub != "detour":
        if carte:
            article["place"] = "carte"
        if not forcer:
            jour_edition = datetime.fromisoformat(date).date()     # l'article est daté du jour de son brouillon
            probleme = (titre_perime(article["title"], jour_edition, jour_edition)
                        or doublon(article["title"], titres_en_ligne(racine, rub), sauf_id=article["id"]))
            if probleme:
                raise RefusPublication(probleme + " Corrigez le brouillon, ou cochez « forcer ».")

    sortie = racine / "iris" / "publies.json"
    publies = json.loads(sortie.read_text(encoding="utf-8")) if sortie.exists() else {"une": [], "tous_connectes": [], "detour": []}
    nouveaux = 0
    if rub == "detour":
        deja = {l["url"] for l in publies.get("detour") or []}
        nouveaux = sum(1 for l in article["liens"] if l["url"] not in deja)
        for l in article["liens"]:
            l["publie_le"] = maintenant.isoformat(timespec="seconds")
        publies["detour"] = [l for l in article["liens"] if l["url"] not in deja] + (publies.get("detour") or [])
        p["liens_gardes"] = [l["url"] for l in article["liens"]]
        ident = f"detour-{date}"
    else:
        article["publie_le"] = maintenant.isoformat(timespec="seconds")
        publies[rub] = [article] + [x for x in publies.get(rub) or [] if x.get("id") != article["id"]]
        ident = article["id"]
    publies["mis_a_jour"] = maintenant.isoformat(timespec="seconds")
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text(json.dumps(publies, ensure_ascii=False, indent=1), encoding="utf-8")
    ecrire_flux(racine)

    p["statut"] = "publie"
    p["publie_le"] = maintenant.isoformat(timespec="seconds")
    chemin.write_text(json.dumps(props, ensure_ascii=False, indent=1), encoding="utf-8")
    texte = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", article.get("chapo") or "")).strip()
    return {"id": ident, "rubrique": rub, "date": date, "alertes": p.get("alertes_charte") or [], "nouveaux": nouveaux,
            "url": f"/#article-{ident}" if rub != "detour" else "/#detour", "texte": texte[:200],
            "archive": date < maintenant.astimezone(PARIS).date().isoformat(),
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
    ecrire_flux(racine)
    return avant - taille()
