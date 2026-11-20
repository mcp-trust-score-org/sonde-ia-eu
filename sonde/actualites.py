"""Actualités : les événements inattendus à croiser avec les mesures de la sonde.

    python -m sonde actualites      # écrit public/actualites.json

Sources (réglées dans config/actualites.yaml), toutes gratuites et publiques :
  - pages de statut des acteurs en amont (Cloudflare…) : leurs incidents touchent
    les fournisseurs qui passent par eux ; celle de GitHub signale les angles morts de la sonde ;
  - alertes météo officielles Meteoalarm (orange et rouge), rapprochées des sites des fournisseurs ;
  - alertes de sécurité du CERT-FR (ANSSI) qui citent un fournisseur ou un acteur dont il dépend ;
  - coupures d'internet par pays (Cloudflare Radar), si un jeton gratuit est fourni ;
  - la presse en ligne mondiale via GDELT (gratuit, sans clé), avec un tri en quatre filtres :
    l'acteur doit être cité dans le titre, avec un mot d'incident, sans mot hors sujet
    (bourse, rachat…), puis les articles qui racontent la même chose sont regroupés.
    Google Actualités est exclu : ses conditions réservent ses flux à un usage personnel.

Chaque événement est écrit au format de config/evenements.json. Rien n'est publié dans le média :
le croisement (python -m sonde croiser) en tire des impacts à relire.
Une source injoignable est notée dans « sources », sans jamais bloquer les autres.
"""

from __future__ import annotations

import json
import os
import re
import time
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import httpx

ENTETES = {"User-Agent": "sonde-ia-eu (veille d'incidents ; https://github.com/mcp-trust-score-org/sonde-ia-eu)"}


# ---------------------------------------------------------------- utilitaires

def _date(texte: str | None) -> datetime | None:
    """Lit une date ISO 8601 ou RFC 822 (flux RSS) et la renvoie en UTC."""
    if not texte:
        return None
    texte = texte.strip()
    try:
        d = datetime.fromisoformat(texte.replace("Z", "+00:00"))
    except ValueError:
        try:
            d = parsedate_to_datetime(texte)
        except (TypeError, ValueError):
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)


def _iso(d: datetime | None) -> str | None:
    return d.isoformat(timespec="minutes") if d else None


def _local(tag: str) -> str:
    """Nom d'un élément XML sans son espace de noms."""
    return tag.rsplit("}", 1)[-1]


def _enfant(el: ET.Element, nom: str) -> str | None:
    for e in el.iter():
        if _local(e.tag) == nom and e is not el:
            return (e.text or "").strip() or e.attrib.get("href")
    return None


def _slug(texte: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", texte.lower()).strip("-")[:60]


def dependances(conf: dict, dossier_dossiers: Path) -> dict[str, set[str]]:
    """Fournisseur → acteurs en amont, d'après la config et le chemin réseau relevé."""
    dep = {f: {a.lower() for a in acteurs} for f, acteurs in (conf.get("dependances") or {}).items()}
    for chemin in sorted(dossier_dossiers.glob("*.json")):
        try:
            reseau = json.loads(chemin.read_text(encoding="utf-8")).get("reseau") or {}
        except (OSError, ValueError):
            continue
        for inter in reseau.get("intermediaires") or []:
            dep.setdefault(chemin.stem, set()).add(inter.lower())
    return dep


# ---------------------------------------------------------------- sources

_LOCALISE = re.compile(r"\b(in|at)\s+[A-Z]|\([A-Z]{3}\)")


def _tri_statuspage(sp: dict, incident: dict, noms: str) -> str | None:
    """Raison d'écarter un incident d'une page de statut, ou None pour le garder.

    Une grande page comme celle de Cloudflare publie des dizaines d'incidents par semaine,
    la plupart sans lien avec nos fournisseurs : une ville lointaine, un service qu'ils
    n'utilisent pas, un incident sans impact.
    """
    plat = _plat(noms)
    if (incident.get("impact") or "none") in (sp.get("impacts_ignores") or []):
        return "sans impact déclaré"
    rx_services = _motif(sp.get("services_ignores") or [])
    if rx_services and rx_services.search(plat):
        return "service non utilisé par nos fournisseurs"
    lieux = _motif(sp.get("lieux_utiles") or [])
    if lieux and _LOCALISE.search(noms) and not lieux.search(plat):
        return "localisé hors de nos zones"
    return None


def lire_statuspages(client, conf: dict, dep: dict[str, set[str]], depuis: datetime) -> tuple[list, list, list]:
    """Incidents des pages de statut en amont → (événements, angles morts de la sonde, écartés)."""
    evenements, angles_morts, ecartes = [], [], []
    for sp in conf.get("statuspages") or []:
        r = client.get(f"{sp['url'].rstrip('/')}/api/v2/incidents.json")
        r.raise_for_status()
        motif = re.compile(re.escape(sp["motif"]), re.I) if sp.get("motif") else None
        touches = sorted(f for f, acteurs in dep.items() if sp["id"].lower() in acteurs)
        for i in r.json().get("incidents") or []:
            debut = _date(i.get("created_at"))
            if not debut or debut < depuis:
                continue
            noms = " ".join([i.get("name") or ""] + [c.get("name") or "" for c in i.get("components") or []])
            if motif and not motif.search(noms):
                continue
            e = {
                "id": f"{sp['id']}-{i.get('id') or _slug(i.get('name', ''))}",
                "titre": f"{sp['nom']} : {(i.get('name') or '').strip()}",
                "type": "incident_amont",
                "debut": _iso(debut),
                "fin": _iso(_date(i.get("resolved_at"))),
                "gravite": i.get("impact"),
                "sources": [{"type": "statut_fournisseur", "url": i.get("shortlink") or f"{sp['url']}/incidents/{i.get('id')}",
                             "titre": i.get("name")}],
                "source_auto": sp["id"],
            }
            if sp.get("role") == "sonde":
                angles_morts.append(e)
                continue
            if not touches:
                continue
            raison = _tri_statuspage(sp, i, noms)
            if raison:
                ecartes.append({"titre": e["titre"], "debut": e["debut"], "raison": raison, "url": e["sources"][0]["url"]})
                continue
            e["fournisseurs"] = touches
            e["pourquoi"] = f"{', '.join(touches)} passe(nt) par {sp['nom']} (chemin réseau relevé)"
            evenements.append(e)
    return evenements, angles_morts, ecartes


def lire_meteoalarm(client, conf: dict, sites: dict, depuis: datetime) -> list:
    """Alertes météo orange et rouges sur une zone où tourne un fournisseur suivi."""
    gravites = set(conf.get("gravites") or ["Severe", "Extreme"])
    zones = {}   # (pays, zone en minuscules) → fournisseurs
    for f, liste in sites.items():
        for s in liste:
            for z in s.get("alerte_meteo") or []:
                zones.setdefault((s["pays"], z.lower()), set()).add(f)
    evenements, erreurs = [], []
    for pays, url in (conf.get("pays") or {}).items():
        if not any(p == pays for p, _ in zones):
            continue
        try:
            r = client.get(url)
            r.raise_for_status()
            racine = ET.fromstring(r.content)
        except (httpx.HTTPError, ET.ParseError) as e:
            erreurs.append(f"{pays} : {type(e).__name__}")
            continue
        for entree in (e for e in racine.iter() if _local(e.tag) == "entry"):
            zone = (_enfant(entree, "areaDesc") or "").strip()
            touches = zones.get((pays, zone.lower()))
            if not touches:
                continue
            gravite = _enfant(entree, "severity") or ""
            if gravite not in gravites:
                continue
            debut = _date(_enfant(entree, "onset") or _enfant(entree, "effective") or _enfant(entree, "sent"))
            fin = _date(_enfant(entree, "expires"))
            if not debut or (fin or debut) < depuis:
                continue
            nature = _enfant(entree, "event") or _enfant(entree, "title") or "alerte météo"
            couleur = "rouge" if gravite == "Extreme" else "orange"
            evenements.append({
                "id": f"meteo-{pays}-{_slug(zone)}-{_slug(nature)}-{debut:%Y%m%d%H}",
                "titre": f"Vigilance {couleur} « {nature} » : {zone}",
                "type": "meteo",
                "fournisseurs": sorted(touches),
                "debut": _iso(debut), "fin": _iso(fin),
                "gravite": couleur,
                "sources": [{"type": "alerte_officielle", "url": _enfant(entree, "link") or url, "titre": f"Meteoalarm · {zone}"}],
                "source_auto": "meteoalarm",
                "pourquoi": f"site de {', '.join(sorted(touches))} dans la zone",
            })
    if erreurs and len(erreurs) == len([p for p in (conf.get("pays") or {}) if any(q == p for q, _ in zones)]):
        raise ValueError("flux injoignables : " + ", ".join(erreurs))
    return evenements, erreurs


def lire_cert_fr(client, conf: dict, depuis: datetime) -> list:
    """Publications du CERT-FR qui citent un fournisseur suivi ou un acteur dont il dépend."""
    r = client.get(conf["url"])
    r.raise_for_status()
    racine = ET.fromstring(r.content)
    regles = {f: re.compile("|".join(re.escape(m) for m in mots), re.I) for f, mots in (conf.get("mots_cles") or {}).items() if mots}
    evenements = []
    for item in (e for e in racine.iter() if _local(e.tag) in ("item", "entry")):
        titre = _enfant(item, "title") or ""
        texte = titre + " " + (_enfant(item, "description") or _enfant(item, "summary") or "")
        touches = sorted(f for f, rx in regles.items() if rx.search(texte))
        if not touches:
            continue
        debut = _date(_enfant(item, "pubDate") or _enfant(item, "published") or _enfant(item, "updated"))
        if not debut or debut < depuis:
            continue
        lien = _enfant(item, "link") or conf["url"]
        evenements.append({
            "id": f"certfr-{_slug(titre)}",
            "titre": f"CERT-FR : {titre}",
            "type": "cyberattaque",
            "fournisseurs": touches,
            "debut": _iso(debut), "fin": None,
            "sources": [{"type": "alerte_officielle", "url": lien, "titre": titre}],
            "source_auto": "cert-fr",
            "pourquoi": "le texte cite " + ", ".join(touches),
        })
    return evenements


def lire_cloudflare_radar(client, conf: dict, sites: dict, env: dict, depuis: datetime) -> list:
    """Coupures d'internet détectées par Cloudflare Radar dans un pays où tourne un fournisseur."""
    jeton = env.get(conf.get("cle_env", "CLOUDFLARE_API_TOKEN"))
    if not jeton:
        raise LookupError("pas de jeton (facultatif)")
    par_pays = {}
    for f, liste in sites.items():
        for s in liste:
            par_pays.setdefault(s["pays"], set()).add(f)
    evenements = []
    for pays in conf.get("pays") or []:
        if pays not in par_pays:
            continue
        r = client.get("https://api.cloudflare.com/client/v4/radar/annotations/outages",
                       params={"location": pays, "dateStart": depuis.strftime("%Y-%m-%dT%H:%M:%SZ"), "limit": 50},
                       headers={"Authorization": f"Bearer {jeton}"})
        r.raise_for_status()
        for a in (r.json().get("result") or {}).get("annotations") or []:
            debut = _date(a.get("startDate"))
            if not debut:
                continue
            panne = a.get("outage") or {}
            cause = (panne.get("outageCause") or "").lower()
            ident = a.get("id") or f"{debut:%Y%m%d%H%M}"
            evenements.append({
                "id": f"radar-{pays}-{ident}",
                "titre": f"Coupure d'internet ({pays}) : {a.get('description') or cause or 'cause inconnue'}",
                "type": "energie" if "power" in cause else "reseau",
                "fournisseurs": sorted(par_pays[pays]),
                "debut": _iso(debut), "fin": _iso(_date(a.get("endDate"))),
                "sources": [{"type": "observatoire_reseau", "url": a.get("linkedUrl") or "https://radar.cloudflare.com/outage-center",
                             "titre": a.get("description") or "Cloudflare Radar"}],
                "source_auto": "cloudflare-radar",
                "pourquoi": f"coupure dans un pays où tourne {', '.join(sorted(par_pays[pays]))} (à confirmer : la zone touchée peut être ailleurs dans le pays)",
            })
    return evenements


# ---------------------------------------------------------------- presse (GDELT)

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"


def _plat(texte: str) -> str:
    """Minuscules sans accents, pour comparer des titres en plusieurs langues."""
    t = unicodedata.normalize("NFKD", texte or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def _motif(mots: list[str]) -> re.Pattern | None:
    mots = [m for m in mots or [] if m]
    if not mots:
        return None
    return re.compile(r"(?<![a-z0-9])(" + "|".join(re.escape(_plat(m)) for m in mots) + r")(?![a-z0-9])")


def _gdelt_date(texte: str | None) -> datetime | None:
    try:
        return datetime.strptime(texte or "", "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return _date(texte)


def _requete_gdelt(noms: list[str], mots: list[str]) -> str:
    def terme(m):
        return f'"{m}"' if " " in m or "-" in m else m
    acteurs = " OR ".join(terme(n) for n in noms)
    incidents = " OR ".join(terme(m) for m in mots)
    return f"({acteurs}) ({incidents})" if len(noms) > 1 else f"{terme(noms[0])} ({incidents})"


def _mots_titre(titre: str) -> set[str]:
    return {m for m in re.findall(r"[a-z0-9]+", _plat(titre)) if len(m) > 2}


def _type_presse(titre_plat: str, conf_types: dict, defaut: str) -> str:
    for type_, mots in (conf_types or {}).items():
        rx = _motif(mots)
        if rx and rx.search(titre_plat):
            return type_
    return defaut


class GdeltErreur(Exception):
    """GDELT n'a pas donné d'articles (débit dépassé, panne…)."""


class GdeltRefus(GdeltErreur):
    """GDELT a répondu en texte : la requête elle-même ne lui convient pas."""


def _gdelt_get(client, params: dict, attendre, essais: int = 4, attente_s: float = 15) -> list:
    """Un appel GDELT, réessayé quand il limite le débit (429) ou flanche (5xx)."""
    derniere = ""
    for essai in range(essais):
        if essai:
            attendre(attente_s * essai)   # 15 s, 30 s, 45 s…
        try:
            r = client.get(GDELT_URL, params=params)
        except httpx.HTTPError as e:
            derniere = type(e).__name__
            continue
        if r.status_code == 429 or r.status_code >= 500:
            derniere = f"HTTP {r.status_code} {r.text.strip()[:80]}".strip()
            continue
        if r.status_code >= 400:
            raise GdeltErreur(f"HTTP {r.status_code} {r.text.strip()[:80]}")
        if not r.content.strip():
            return []   # aucun article
        try:
            return r.json().get("articles") or []
        except ValueError:
            raise GdeltRefus(r.text.strip()[:120]) from None
    raise GdeltErreur(f"{derniere} après {essais} essais")


def lire_gdelt(client, conf: dict, dep: dict[str, set[str]], depuis: datetime, maintenant: datetime,
               attendre=time.sleep) -> tuple[list, dict]:
    """Articles de presse (GDELT) → événements « presse » à relire, et un bilan du tri.

    Tri en quatre filtres, sur le titre seulement (GDELT ne donne pas le texte) :
      1. un acteur suivi est cité dans le titre (le nom, pas un mot approchant) ;
      2. un mot d'incident est dans le titre (panne, outage, incendie, Ausfall…) ;
      3. aucun mot hors sujet (bourse, rachat, résultats, offre d'emploi…) ni domaine exclu ;
      4. regroupement : les titres proches sur 48 h deviennent un seul événement,
         avec le nombre de médias qui en parlent.
    """
    acteurs = conf.get("acteurs") or {}
    mots_incident = conf.get("mots_incident") or []
    rx_incident = _motif(mots_incident)
    rx_exclus = _motif(conf.get("mots_exclus") or [])
    domaines_exclus = {d.lower() for d in conf.get("domaines_exclus") or []}
    langues = conf.get("langues") or []
    jours = max(1, (maintenant - depuis).days)
    pause = conf.get("pause_s", 6)
    bilan = {"articles": 0, "sans_acteur": 0, "sans_incident": 0, "hors_sujet": 0, "doublons": 0,
             "retenus": 0, "erreurs": []}
    retenus = []   # (acteur, article)
    vus_url = set()

    params = {"mode": "ArtList", "format": "json", "timespan": f"{jours}d",
              "maxrecords": conf.get("max_articles", 250), "sort": "DateDesc"}
    filtre_langue = (" (" + " OR ".join(f"sourcelang:{l}" for l in langues) + ")") if langues else ""
    appels = [0]

    def interroger(requete: str) -> list:
        if appels[0]:
            attendre(pause)   # GDELT demande au plus une requête toutes les 5 secondes
        appels[0] += 1
        return _gdelt_get(client, {**params, "query": requete + filtre_langue}, attendre,
                          conf.get("essais", 4), conf.get("attente_429_s", 15))

    # Une seule requête pour tous les acteurs (moins de refus pour excès de débit).
    # Si GDELT la juge trop complexe, on repasse à une requête par acteur.
    tous_noms = [n for reg in acteurs.values() for n in (reg.get("noms") or [])]
    lots = []
    try:
        lots.append(interroger(_requete_gdelt(tous_noms, mots_incident)))
    except GdeltRefus as e:
        bilan["requete_groupee"] = f"refusée ({e}) : une requête par acteur"
        for acteur, reg in acteurs.items():
            try:
                lots.append(interroger(_requete_gdelt(reg.get("noms") or [acteur], reg.get("mots_incident") or mots_incident)))
            except GdeltErreur as e2:
                bilan["erreurs"].append(f"{acteur} : {e2}")
        if len(bilan["erreurs"]) == len(acteurs):
            raise ValueError("GDELT : " + "; ".join(bilan["erreurs"])[:250])
    except GdeltErreur as e:
        raise ValueError(f"GDELT : {e}") from None

    motifs = {a: (_motif(reg.get("noms") or [a]),
                  _motif(reg["mots_incident"]) if reg.get("mots_incident") else rx_incident)
              for a, reg in acteurs.items()}
    for articles in lots:
        for a in articles:
            url = a.get("url") or ""
            if url in vus_url:
                bilan["doublons"] += 1
                continue
            vus_url.add(url)
            bilan["articles"] += 1
            titre = (a.get("title") or "").strip()
            plat = _plat(titre)
            domaine = (a.get("domain") or "").lower()
            quand = _gdelt_date(a.get("seendate"))
            if not quand or quand < depuis:
                continue
            cites = [ac for ac, (rx_a, _) in motifs.items() if rx_a and rx_a.search(plat)]
            if not cites:
                bilan["sans_acteur"] += 1
                continue
            cites = [ac for ac in cites if motifs[ac][1] and motifs[ac][1].search(plat)]
            if not cites:
                bilan["sans_incident"] += 1
                continue
            if (rx_exclus and rx_exclus.search(plat)) or any(domaine == d or domaine.endswith("." + d) for d in domaines_exclus):
                bilan["hors_sujet"] += 1
                continue
            for acteur in cites:
                retenus.append((acteur, {"titre": titre, "url": url, "domaine": domaine, "date": quand,
                                         "langue": a.get("language"), "pays": a.get("sourcecountry"),
                                         "mots": _mots_titre(titre)}))

    # 4. Regroupement : même acteur, titres proches (mots en commun), à moins de 48 h.
    seuil = conf.get("seuil_similarite", 0.3)
    groupes: list[dict] = []
    for acteur, art in sorted(retenus, key=lambda x: x[1]["date"]):
        cible = None
        for g in groupes:
            if g["acteur"] != acteur or art["date"] - g["fin"] > timedelta(hours=48):
                continue
            communs = len(art["mots"] & g["mots"]) / max(1, len(art["mots"] | g["mots"]))
            if communs >= seuil or any(art["mots"] == b["mots"] for b in g["articles"]):
                cible = g
                break
        if cible is None:
            groupes.append({"acteur": acteur, "articles": [art], "mots": set(art["mots"]),
                            "debut": art["date"], "fin": art["date"]})
        else:
            if any(b["domaine"] == art["domaine"] for b in cible["articles"]):
                bilan["doublons"] += 1
                continue
            cible["articles"].append(art)
            cible["mots"] |= art["mots"]
            cible["fin"] = max(cible["fin"], art["date"])

    avance = timedelta(hours=conf.get("avance_h", 6))
    evenements = []
    for g in groupes:
        reg = acteurs[g["acteur"]]
        role = reg.get("role", "fournisseur")
        if role == "fournisseur":
            touches = [g["acteur"]]
            defaut = "incident_fournisseur"
        else:
            touches = sorted(f for f, a in dep.items() if g["acteur"].lower() in a) + sorted(reg.get("fournisseurs") or [])
            touches = sorted(set(touches))
            defaut = "incident_amont"
        if not touches:
            continue
        premier = g["articles"][0]
        medias = sorted({a["domaine"] for a in g["articles"]})
        bilan["retenus"] += 1
        evenements.append({
            "id": f"presse-{g['acteur']}-{premier['date']:%Y%m%d}-{_slug(premier['titre'])[:40]}",
            "titre": f"Presse : {premier['titre']}",
            "type": _type_presse(_plat(" ".join(a["titre"] for a in g["articles"])), conf.get("types"), defaut),
            "fournisseurs": touches,
            # La date d'un article est celle de sa parution : la panne a pu commencer avant.
            "debut": _iso(g["debut"] - avance),
            "fin": _iso(g["fin"]),
            "gravite": "repris" if len(medias) >= conf.get("repris_a_partir_de", 2) else "isolé",
            "fiabilite": "presse",
            "presse": {"nb_medias": len(medias), "medias": medias, "premiere_parution": _iso(g["debut"]),
                       "derniere_parution": _iso(g["fin"])},
            "sources": [{"type": "presse", "url": a["url"], "titre": a["titre"], "date": _iso(a["date"])}
                        for a in g["articles"][:6]],
            "source_auto": "gdelt",
            "pourquoi": (f"titre qui cite {g['acteur']} et un mot d'incident ; {len(medias)} média(s)"
                         + ("" if role == "fournisseur" else f" ; {', '.join(touches)} dépend(ent) de {g['acteur']}")),
        })
    return evenements, bilan


# ---------------------------------------------------------------- production

def produire_actualites(conf: dict, racine: Path, client: httpx.Client | None = None,
                        env: dict | None = None, maintenant: datetime | None = None,
                        attendre=time.sleep) -> dict:
    """Écrit public/actualites.json. Ne lève jamais : chaque source a son propre état."""
    env = env if env is not None else os.environ
    maintenant = maintenant or datetime.now(timezone.utc)
    depuis = maintenant - timedelta(days=(conf.get("reglages") or {}).get("jours", 7))
    sources_conf = conf.get("sources") or {}
    sites = conf.get("sites") or {}
    dep = dependances(conf, racine / "dossiers")
    propre = client is None
    client = client or httpx.Client(timeout=(conf.get("reglages") or {}).get("delai_s", 20),
                                    follow_redirects=True, headers=ENTETES)
    evenements, angles_morts, etats = [], [], {}
    bilan_presse = None
    ecartes_statuts = []

    def tenter(nom, fonction, *a):
        try:
            res = fonction(*a)
            etats[nom] = {"etat": "ok"}
            return res
        except LookupError as e:
            etats[nom] = {"etat": "ignorée", "raison": str(e)}
        except (httpx.HTTPError, ET.ParseError, ValueError, KeyError) as e:
            etats[nom] = {"etat": "erreur", "raison": f"{type(e).__name__}: {e}"[:200]}
        return None

    try:
        if sources_conf.get("statuspages"):
            res = tenter("pages de statut en amont", lire_statuspages, client, {"statuspages": sources_conf["statuspages"]}, dep, depuis)
            if res:
                evenements += res[0]
                angles_morts += res[1]
                ecartes_statuts = res[2]
        if sources_conf.get("meteoalarm"):
            res = tenter("Meteoalarm", lire_meteoalarm, client, sources_conf["meteoalarm"], sites, depuis)
            if res:
                evenements += res[0]
                if res[1]:
                    etats["Meteoalarm"] = {"etat": "partiel", "raison": "; ".join(res[1])}
        if sources_conf.get("cert_fr"):
            evenements += tenter("CERT-FR", lire_cert_fr, client, sources_conf["cert_fr"], depuis) or []
        if sources_conf.get("cloudflare_radar"):
            evenements += tenter("Cloudflare Radar", lire_cloudflare_radar, client, sources_conf["cloudflare_radar"], sites, env, depuis) or []
        if sources_conf.get("gdelt"):
            res = tenter("Presse (GDELT)", lire_gdelt, client, sources_conf["gdelt"], dep, depuis, maintenant, attendre)
            if res:
                evenements += res[0]
                bilan_presse = res[1]
                if bilan_presse["erreurs"]:
                    etats["Presse (GDELT)"] = {"etat": "partiel", "raison": "; ".join(bilan_presse["erreurs"])[:300]}
    finally:
        if propre:
            client.close()

    vus, uniques = set(), []
    for e in sorted(evenements, key=lambda e: e["debut"] or "", reverse=True):
        if e["id"] not in vus:
            vus.add(e["id"])
            uniques.append(e)
    sortie = {
        "genere_le": maintenant.isoformat(timespec="seconds"),
        "fenetre_jours": (conf.get("reglages") or {}).get("jours", 7),
        "sources": etats,
        "dependances": {f: sorted(a) for f, a in dep.items()},
        "evenements": uniques,
        "angles_morts_sonde": angles_morts,
        # Gardés pour contrôle : vous pouvez vérifier que le tri n'a rien écarté d'utile.
        "ecartes_pages_de_statut": ecartes_statuts,
    }
    if bilan_presse is not None:
        sortie["tri_presse"] = bilan_presse
    (racine / "public").mkdir(parents=True, exist_ok=True)
    (racine / "public" / "actualites.json").write_text(json.dumps(sortie, ensure_ascii=False, indent=1), encoding="utf-8")
    return sortie
