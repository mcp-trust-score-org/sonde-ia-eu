"""Cohérence d'un article avec le jour de publication et avec ce qui est déjà sur le site.

Deux contrôles, utilisés par le rédacteur (alertes dans les brouillons) et par la publication
(refus, sauf si « forcer » est coché) :

- titre périmé : « GTA VI sort ce jeudi » publié un samedi. Le titre annonce un événement
  au présent ou au futur alors que le jour est passé ;
- doublon : le sujet est déjà en ligne dans la rubrique (grand titre ou cartes).
"""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import date
from pathlib import Path

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
RELATIFS = ("aujourd hui", "ce soir", "cette nuit", "demain", "ce matin")
# Pages dont le contenu écrit à la main compte aussi. À la une est exclue : ses éditions des jours
# passés sont des archives, et une « suite » sur le même sujet y est normale.
SECTIONS = {"tous_connectes": "view-vies"}

# Mots trop courants pour signaler un doublon à eux seuls (comparés sans accents).
VIDES = set("""
dans pour avec sans plus moins tout tous toute toutes leur leurs vous votre notre nous cette sont etre
fait faire encore aujourd hui vraiment comme quand apres avant depuis entre meme aussi tres chez contre
sous vers mais donc alors deja elle elles ils ont peut peuvent suffit simple quoi rien personne
lundi mardi mercredi jeudi vendredi samedi dimanche janvier fevrier mars avril juin juillet aout septembre
octobre novembre decembre minutes heures jours semaine annee
""".split())


def _plat(texte: str) -> str:
    t = re.sub(r"<[^>]+>", " ", texte or "")
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


def mots_forts(titre: str) -> set[str]:
    """Les mots qui portent le sujet : noms propres, sigles (GTA, VI) et mots longs peu courants."""
    brut = re.sub(r"<[^>]+>", " ", titre or "")
    forts = set()
    for m in re.findall(r"[\wÀ-ÿ'’-]+", brut):
        p = _plat(m).replace(" ", "")
        if not p or p in VIDES:
            continue
        sigle = len(m) >= 2 and m.isupper()
        if sigle or len(p) >= 5:
            forts.add(p)
    return forts


def titre_perime(titre: str, date_brouillon: date, date_publication: date) -> str | None:
    """Un titre au présent ou au futur qui ne colle plus au jour où il est publié."""
    plat = f" {_plat(titre)} "
    jour_pub = JOURS[date_publication.weekday()]
    for j in JOURS:
        if j != jour_pub and (f" ce {j} " in plat or f" {j} prochain " in plat):
            return (f"Titre périmé : il dit « {'ce ' + j if f' ce {j} ' in plat else j + ' prochain'} », mais l'article "
                    f"est publié un {jour_pub}. Si l'événement est passé, le titre doit le dire au passé "
                    f"(« est sorti {j} »).")
    if date_publication > date_brouillon:
        for r in RELATIFS:
            if f" {r} " in plat:
                return (f"Titre périmé : il dit « {r.replace('aujourd hui', 'aujourd’hui')} », mais le brouillon date du "
                        f"{date_brouillon.isoformat()} et l'article est publié le {date_publication.isoformat()}.")
    return None


def titres_en_ligne(racine: Path, rubrique: str) -> list[dict]:
    """Ce que le lecteur voit déjà dans la rubrique : les articles publiés et ceux écrits dans la page."""
    vus = []
    pub = racine / "iris" / "publies.json"
    if pub.exists():
        try:
            for a in json.loads(pub.read_text(encoding="utf-8")).get(rubrique) or []:
                if a.get("title"):
                    vus.append({"id": a.get("id"), "titre": a["title"], "img": a.get("img")})
        except ValueError:
            pass
    page = racine / "iris" / "index.html"
    section = SECTIONS.get(rubrique)
    if section and page.exists():
        html = page.read_text(encoding="utf-8")
        debut = html.find(f'id="{section}"')
        if debut >= 0:
            fin = html.find("<section", debut + 1)
            bloc = html[debut: fin if fin > 0 else None]
            for t in re.findall(r"<h[13][^>]*>(.*?)</h[13]>", bloc, re.S):
                vus.append({"id": None, "titre": t.strip(), "img": None})
    return vus


def doublon(titre: str, en_ligne: list[dict], sauf_id: str | None = None) -> str | None:
    """Le sujet du titre est-il déjà en ligne ? Deux mots forts en commun suffisent."""
    forts = mots_forts(titre)
    for x in en_ligne:
        if sauf_id and x.get("id") == sauf_id:
            continue
        communs = forts & mots_forts(x["titre"])
        if len(communs) >= 2:
            deja = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", x["titre"])).strip()
            return f"Doublon : ce sujet est déjà en ligne dans la rubrique (« {deja[:90]} »)."
    return None


# ---------------------------------------------------------------- lien technologique sourcé

# Familles de mots qui font le lien avec la technologie. Si le texte en emploie une que les
# articles lus n'emploient jamais, le lien a peut-être été inventé pour coller à la rubrique.
TECHNO = {
    "numérique": r"numeriques?|digital\w*",
    "électronique": r"electroniques?",
    "téléphone": r"smartphones?|telephones?|iphones?|mobiles?",
    "application": r"applis?|applications? (?:mobiles?|de messagerie)|appli\w*",
    "messagerie": r"messageries?|sms|whatsapp|telegram|textos?",
    "internet": r"internet|en ligne|web",
    "intelligence artificielle": r"intelligence artificielle|ia|chatgpt|algorithmes?",
    "serveurs": r"serveurs?|cloud|datacenters?|centres? de donnees",
    "réseaux sociaux": r"reseaux? sociaux|reseau social|tiktok|instagram|facebook",
    "piratage": r"cyber\w*|piratages?|pirates? informatiques?|hackers?|rancongiciels?",
    "connecté": r"connecte(?:e|s|es)?|objets? connectes?",
    "logiciel": r"logiciels?|ordinateurs?|informatiques?",
    "téléchargement": r"telecharg\w+|dematerialis\w+|streaming|consoles?",
}


def _famille_presente(motif: str, plat: str) -> bool:
    return re.search(rf"(?<![a-z0-9])(?:{motif})(?![a-z0-9])", plat) is not None


def techno_non_sourcee(article: dict, textes: list[str]) -> list[str]:
    """Les mots technologiques du titre, du chapeau, du fait et de la conséquence qui
    n'apparaissent dans aucun des articles lus. Vide si aucun article n'a été lu."""
    sources = " ".join(_plat(t) for t in textes if t)
    if not sources.strip():
        return []
    a = article or {}
    mini = a.get("une_mini") or {}
    texte = _plat(" ".join([a.get("title") or "", a.get("chapo") or ""] + list(a.get("fait") or [])
                           + list(a.get("consequence") or []) + [str(v) for v in mini.values()]))
    return [nom for nom, motif in TECHNO.items()
            if _famille_presente(motif, texte) and not _famille_presente(motif, sources)]
