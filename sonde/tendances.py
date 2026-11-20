"""Tendances : ce qui passionne les gens, et des articles d'autres médias pour le Détour.

    python -m sonde tendances       # écrit public/tendances.json

Trois sources, toutes gratuites et publiques :
  - les pages les plus lues de Wikipédia la veille (français et anglais) : un très bon
    indicateur de ce qui occupe les gens (une sortie de jeu, un phénomène, un événement) ;
  - la presse grand public via GDELT, sur des mots qui signalent souvent une dépendance
    numérique (panne, rupture de stock, file d'attente, arnaque…), tous sujets confondus ;
  - pour le Détour, les articles récents des médias de référence (config/redaction.yaml).

Aucun filtre par thème : le test du « Et vous ? » est appliqué au moment de la rédaction.
Une source injoignable est notée, sans bloquer les autres.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import httpx

from .actualites import ENTETES, GdeltErreur, GdeltRefus, _gdelt_date, _gdelt_get, _iso, _plat

WIKIMEDIA = "https://wikimedia.org/api/rest_v1/metrics/pageviews/top/{projet}/all-access/{d:%Y/%m/%d}"
ESPACES_EXCLUS = ("spécial:", "special:", "wikipédia:", "wikipedia:", "fichier:", "file:", "portail:",
                  "portal:", "aide:", "help:", "catégorie:", "category:", "modèle:", "template:", "utilisateur:", "user:")


def _terme(m: str) -> str:
    return f'"{m}"' if (" " in m or "-" in m or "'" in m) else m


def _ou(termes: list[str]) -> str:
    return "(" + " OR ".join(termes) + ")" if len(termes) > 1 else termes[0]


def _gdelt_requete_souple(client, construire, liste: list, params: dict, attendre, conf: dict, appels: list) -> list:
    """Interroge GDELT ; si la requête est jugée trop complexe, la coupe en deux (deux fois au plus)."""
    def une(l, profondeur):
        if appels[0]:
            attendre(conf.get("pause_s", 6))
        appels[0] += 1
        try:
            return _gdelt_get(client, {**params, "query": construire(l)}, attendre,
                              conf.get("essais", 4), conf.get("attente_429_s", 15))
        except GdeltRefus:
            if profondeur >= 2 or len(l) < 2:
                raise
            m = len(l) // 2
            return une(l[:m], profondeur + 1) + une(l[m:], profondeur + 1)
    return une(liste, 0)


# ---------------------------------------------------------------- Wikipédia

def lire_wikipedia(client, conf: dict, maintenant: datetime) -> list:
    """Pages les plus lues la veille (ou l'avant-veille si la veille n'est pas encore publiée)."""
    exclus = {e.lower() for e in conf.get("exclure") or []}
    sortie = []
    for projet in conf.get("projets") or ["fr.wikipedia.org"]:
        donnees, jour = None, None
        for recul in (1, 2):
            jour = (maintenant - timedelta(days=recul)).date()
            r = client.get(WIKIMEDIA.format(projet=projet, d=jour))
            if r.status_code == 404:
                continue
            r.raise_for_status()
            donnees = r.json()
            break
        if donnees is None:
            raise ValueError(f"{projet} : pas encore de classement publié")
        articles = ((donnees.get("items") or [{}])[0]).get("articles") or []
        rang = 0
        for a in articles:
            titre = a.get("article") or ""
            t = titre.lower()
            if t in exclus or t.startswith(ESPACES_EXCLUS) or t.startswith("-"):
                continue
            rang += 1
            sortie.append({
                "source": "wikipedia", "projet": projet, "jour": jour.isoformat(), "rang": rang,
                "sujet": titre.replace("_", " "), "vues": a.get("views"),
                "url": f"https://{projet}/wiki/{quote(titre)}",
            })
            if rang >= conf.get("nombre", 30):
                break
    return sortie


# ---------------------------------------------------------------- presse grand public

def lire_presse_grand_public(client, conf: dict, maintenant: datetime, attendre) -> list:
    """Articles récents (48 h) qui contiennent un mot signalant une dépendance numérique."""
    mots = [_terme(m) for m in conf.get("mots") or []]
    if not mots:
        return []
    langues = conf.get("langues") or []
    filtre = (" " + _ou([f"sourcelang:{l}" for l in langues])) if langues else ""
    params = {"mode": "ArtList", "format": "json", "timespan": "2d", "sort": "DateDesc",
              "maxrecords": conf.get("max_articles", 250)}
    articles = _gdelt_requete_souple(client, lambda l: _ou(l) + filtre, mots, params, attendre, conf, [0])
    vus, sortie = set(), []
    depuis = maintenant - timedelta(days=2)
    for a in articles:
        titre = (a.get("title") or "").strip()
        cle = _plat(titre)
        quand = _gdelt_date(a.get("seendate"))
        if not titre or cle in vus or (quand and quand < depuis):
            continue
        vus.add(cle)
        sortie.append({"source": "presse", "titre": titre, "url": a.get("url"), "media": a.get("domain"),
                       "langue": a.get("language"), "pays": a.get("sourcecountry"), "date": _iso(quand)})
    return sortie


# ---------------------------------------------------------------- Détour

def lire_detour(client, conf: dict, gdelt_conf: dict, maintenant: datetime, attendre) -> list:
    """Articles récents des médias de référence qui touchent à la technologie et à ses dépendances."""
    medias = conf.get("medias") or []
    mots = [_terme(m) for m in conf.get("mots") or []]
    if not medias:
        return []
    par_domaine = {m["domaine"].lower(): m for m in medias}
    params = {"mode": "ArtList", "format": "json", "timespan": f"{conf.get('jours', 7)}d", "sort": "DateDesc",
              "maxrecords": 250}
    construire = lambda doms: _ou([f"domain:{d}" for d in doms]) + (" " + _ou(mots) if mots else "")
    articles = _gdelt_requete_souple(client, construire, list(par_domaine), params, attendre, gdelt_conf, [0])
    vus, sortie = set(), []
    for a in articles:
        url = a.get("url") or ""
        domaine = (a.get("domain") or "").lower()
        media = par_domaine.get(domaine) or next((m for d, m in par_domaine.items() if domaine.endswith("." + d)), None)
        if not media or (media.get("chemin") and media["chemin"] not in url):
            continue
        titre = (a.get("title") or "").strip()
        if not titre or _plat(titre) in vus:
            continue
        vus.add(_plat(titre))
        sortie.append({"media": media["nom"], "titre": titre, "url": url,
                       "langue": media.get("langue", "français"), "date": _iso(_gdelt_date(a.get("seendate")))})
    return sortie


# ---------------------------------------------------------------- production

def produire_tendances(conf: dict, racine: Path, client: httpx.Client | None = None,
                       maintenant: datetime | None = None, attendre=time.sleep) -> dict:
    """Écrit public/tendances.json. Ne lève jamais : chaque source a son propre état."""
    maintenant = maintenant or datetime.now(timezone.utc)
    t = conf.get("tendances") or {}
    propre = client is None
    client = client or httpx.Client(timeout=30, follow_redirects=True, headers=ENTETES)
    etats, res = {}, {"wikipedia": [], "presse": [], "detour": []}

    def tenter(nom, cle, fonction, *a):
        try:
            res[cle] = fonction(*a)
            etats[nom] = {"etat": "ok", "nombre": len(res[cle])}
        except (httpx.HTTPError, GdeltErreur, ValueError, KeyError) as e:
            etats[nom] = {"etat": "erreur", "raison": f"{type(e).__name__}: {e}"[:200]}

    try:
        if t.get("wikipedia"):
            tenter("Wikipédia", "wikipedia", lire_wikipedia, client, t["wikipedia"], maintenant)
        if t.get("gdelt"):
            tenter("Presse grand public (GDELT)", "presse", lire_presse_grand_public, client, t["gdelt"], maintenant, attendre)
        if conf.get("detour"):
            attendre((t.get("gdelt") or {}).get("pause_s", 6))
            tenter("Détour (GDELT)", "detour", lire_detour, client, conf["detour"], t.get("gdelt") or {}, maintenant, attendre)
    finally:
        if propre:
            client.close()

    sortie = {"genere_le": maintenant.isoformat(timespec="seconds"), "sources": etats, **res}
    (racine / "public").mkdir(parents=True, exist_ok=True)
    (racine / "public" / "tendances.json").write_text(json.dumps(sortie, ensure_ascii=False, indent=1), encoding="utf-8")
    return sortie
