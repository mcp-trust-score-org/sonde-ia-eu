"""Tendances : ce qui passionne les gens, et des articles d'autres médias pour le Détour.

    python -m sonde tendances       # écrit public/tendances.json

Sources, toutes gratuites et publiques :
  - les pages les plus lues de Wikipédia la veille (français et anglais) : un très bon
    indicateur de ce qui occupe les gens (une sortie de jeu, un phénomène, un événement) ;
  - les titres de la presse grand public, par leurs flux RSS (et GDELT si activé) ;
  - pour le Détour, les flux RSS des médias de référence (config/redaction.yaml).

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

import re
import xml.etree.ElementTree as ET

from .actualites import (ENTETES, GdeltErreur, GdeltRefus, _date, _enfant, _gdelt_date, _gdelt_get, _iso, _local,
                         _motif, _plat)

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


# ---------------------------------------------------------------- flux RSS des médias

def _sans_balises(texte: str | None) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", texte or "")).strip()


def lire_flux(client, flux: list[dict], depuis: datetime, mots: list[str] | None = None) -> tuple[list, dict]:
    """Articles récents de flux RSS ou Atom → (articles, état de chaque flux).

    Le flux RSS est fait pour être lu par des logiciels : titre, lien, date et résumé.
    `mots` : si donné, on ne garde que les articles dont le titre ou le résumé en contient un
    (pour un média généraliste, seulement ce qui touche à la technologie).
    """
    rx = _motif(mots) if mots else None
    articles, etats, vus = [], {}, set()
    for f in flux:
        nom = f.get("nom") or f["url"]
        try:
            r = client.get(f["url"], timeout=20, follow_redirects=True)
            r.raise_for_status()
            racine = ET.fromstring(r.content)
        except (httpx.HTTPError, ET.ParseError) as e:
            etats[nom] = f"erreur ({type(e).__name__})"
            continue
        n = 0
        for item in (e for e in racine.iter() if _local(e.tag) in ("item", "entry")):
            titre = _sans_balises(_enfant(item, "title"))
            lien = None
            for e in item:
                if _local(e.tag) == "link":
                    lien = (e.text or "").strip() or e.attrib.get("href")
                    if e.attrib.get("rel", "alternate") == "alternate":
                        break
            quand = _date(_enfant(item, "pubDate") or _enfant(item, "published") or _enfant(item, "updated")
                          or _enfant(item, "date"))
            resume = _sans_balises(_enfant(item, "description") or _enfant(item, "summary"))[:400]
            if not titre or not lien or (quand and quand < depuis) or _plat(titre) in vus:
                continue
            if rx and not f.get("tout") and not rx.search(_plat(titre + " " + resume)):
                continue
            vus.add(_plat(titre))
            n += 1
            articles.append({"media": nom, "titre": titre, "url": lien, "date": _iso(quand), "resume": resume or None,
                             "langue": f.get("langue", "français")})
        etats[nom] = f"ok ({n})"
    return articles, etats


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

def lire_detour(client, conf: dict, maintenant: datetime) -> tuple[list, dict]:
    """Articles récents des médias de référence (leurs flux RSS), qui touchent à la technologie."""
    flux = [{"nom": m["nom"], "url": m["flux"], "langue": m.get("langue", "français"), "tout": m.get("tout", False)}
            for m in conf.get("medias") or [] if m.get("flux")]
    return lire_flux(client, flux, maintenant - timedelta(days=conf.get("jours", 7)), conf.get("mots"))


# ---------------------------------------------------------------- production

def produire_tendances(conf: dict, racine: Path, client: httpx.Client | None = None,
                       maintenant: datetime | None = None, attendre=time.sleep) -> dict:
    """Écrit public/tendances.json. Ne lève jamais : chaque source a son propre état."""
    maintenant = maintenant or datetime.now(timezone.utc)
    t = conf.get("tendances") or {}
    propre = client is None
    client = client or httpx.Client(timeout=30, follow_redirects=True, headers=ENTETES)
    etats, res, detail = {}, {"wikipedia": [], "presse": [], "detour": []}, {}

    def tenter(nom, cle, fonction, *a):
        try:
            r = fonction(*a)
            if isinstance(r, tuple):          # (articles, état de chaque flux)
                r, detail[nom] = r
            res[cle] += r
            etats[nom] = {"etat": "ok", "nombre": len(r)}
        except (httpx.HTTPError, GdeltErreur, ValueError, KeyError) as e:
            etats[nom] = {"etat": "erreur", "raison": f"{type(e).__name__}: {e}"[:200]}

    try:
        if t.get("wikipedia"):
            tenter("Wikipédia", "wikipedia", lire_wikipedia, client, t["wikipedia"], maintenant)
        if t.get("flux"):
            tenter("Presse grand public (flux RSS)", "presse", lire_flux, client, t["flux"], maintenant - timedelta(days=2))
        if (t.get("gdelt") or {}).get("actif", False):
            tenter("Presse grand public (GDELT)", "presse", lire_presse_grand_public, client, t["gdelt"], maintenant, attendre)
        if conf.get("detour"):
            tenter("Détour (flux RSS)", "detour", lire_detour, client, conf["detour"], maintenant)
    finally:
        if propre:
            client.close()

    sortie = {"genere_le": maintenant.isoformat(timespec="seconds"), "sources": etats, "flux": detail, **res}
    (racine / "public").mkdir(parents=True, exist_ok=True)
    (racine / "public" / "tendances.json").write_text(json.dumps(sortie, ensure_ascii=False, indent=1), encoding="utf-8")
    return sortie
