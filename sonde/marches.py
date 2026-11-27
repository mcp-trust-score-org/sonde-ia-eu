"""Les marchés publics de l'IA : une source officielle pour le mercato.

Deux bases publiques, gratuites et sans clé :
- le BOAMP (marchés publics français), via l'open data de la DILA ;
- TED (marchés publics de l'Union européenne), via son API de recherche.

On y cherche les avis qui parlent d'intelligence artificielle :
- un « résultat de marché » (attribution) = une SIGNATURE officielle, publiée par l'acheteur public avec le nom du
  titulaire : candidat au mercato (« C'est signé. », tampon OFFICIEL) ;
- un « avis de marché » (appel d'offres en cours) = rien n'est signé : à surveiller, jamais présenté comme un choix.

Rien n'entre au mercato automatiquement : les avis sont listés dans le brouillon du jour, la rédaction vérifie l'avis
(lien officiel) et décide. Écrit public/marches.json (les 60 derniers jours).
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

BOAMP = "https://boamp-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/boamp/records"
TED = "https://api.ted.europa.eu/v3/notices/search"
# En-tête HTTP : ASCII seulement (un « é » ici a empêché la toute première collecte, le 27/11).
AGENT = "Iris (sonde-ia-eu) - veille des marches publics de l'IA"

# Ce que l'objet de l'avis doit contenir pour parler d'IA (mots entiers, insensible à la casse).
MOTS_IA = re.compile(
    r"intelligence artificielle|\bi\.?a\.? g[ée]n[ée]rative|\bia\b|artificial intelligence|\bgenerative ai\b|\bllm\b|"
    r"mod[èe]les? de langage|large language model|agents? conversationnel|chatbot|assistant (virtuel|conversationnel|ia)|"
    r"\bmistral ai\b|\bopenai\b|chatgpt|\bcopilot\b|\banthropic\b",
    re.I)

# Les fournisseurs qu'on sait reconnaître dans un avis (titulaire, solution citée).
FOURNISSEURS = {
    "Mistral AI": r"mistral ai|mistral\.ai|\bmistral (large|medium|small|nemo|le chat)|le chat de mistral",
    "OpenAI": r"\bopenai\b|chatgpt",
    "Anthropic": r"\banthropic\b|claude (ai|pro|sonnet|opus|haiku)|claude\.ai",
    "Microsoft": r"\bmicrosoft\b|\bcopilot\b|\bazure\b",
    "Google": r"\bgoogle\b|\bgemini\b",
    "Amazon (AWS)": r"amazon web services|\baws\b|\bbedrock\b",
    "Meta": r"\bllama\b",
    "OVHcloud": r"\bovh",
    "Scaleway": r"\bscaleway\b",
    "IONOS": r"\bionos\b",
    "Outscale": r"\boutscale\b",
    "LightOn": r"\blighton\b",
    "Aleph Alpha": r"aleph alpha",
    "IBM": r"\bibm\b|watsonx",
}


def fournisseurs_cites(texte: str) -> list[str]:
    return [nom for nom, motif in FOURNISSEURS.items() if re.search(motif, texte or "", re.I)]


def parle_d_ia(texte: str) -> bool:
    return bool(MOTS_IA.search(texte or ""))


def _texte(valeur) -> str:
    """Tout le texte d'un champ (chaîne, liste, dictionnaire multilingue, JSON en chaîne)."""
    if valeur is None:
        return ""
    if isinstance(valeur, str):
        return valeur
    if isinstance(valeur, dict):
        for langue in ("fra", "fr", "eng", "en"):
            if langue in valeur:
                return _texte(valeur[langue])
        return " ".join(_texte(v) for v in valeur.values())
    if isinstance(valeur, (list, tuple)):
        return " ".join(_texte(v) for v in valeur)
    return str(valeur)


# ---------------------------------------------------------------------------- BOAMP

def avis_boamp(enr: dict) -> dict | None:
    objet = _texte(enr.get("objet"))
    donnees = _texte(enr.get("donnees"))
    if not parle_d_ia(objet):
        return None                                   # l'IA doit être dans l'objet du marché, pas seulement citée
    nature = _texte(enr.get("nature_categorise_libelle") or enr.get("nature_libelle"))
    if "rectificatif" in nature.lower():
        return None
    resultat = "résultat" in nature.lower() or "attribution" in nature.lower()
    idweb = str(enr.get("idweb") or "")
    return {
        "id": f"boamp:{idweb}", "base": "BOAMP", "pays": "France",
        "type": "attribution" if resultat else "appel_offres",
        "date": str(enr.get("dateparution") or "")[:10],
        "acheteur": _texte(enr.get("nomacheteur")).strip(),
        "objet": re.sub(r"\s+", " ", objet).strip()[:300],
        "fournisseurs": fournisseurs_cites(donnees + " " + objet),
        "date_limite": str(enr.get("datelimitereponse") or "")[:10] or None,
        "url": enr.get("url_avis") or (f"https://www.boamp.fr/pages/avis/?q=idweb:{idweb}" if idweb else None),
    }


def lire_boamp(client: httpx.Client, depuis: datetime, limite: int = 100) -> list[dict]:
    termes = ['"intelligence artificielle"', '"IA générative"', '"modèle de langage"', '"LLM"', '"agent conversationnel"']
    where = f"dateparution >= date'{depuis.date().isoformat()}' and ({' or '.join(termes)})"
    r = client.get(BOAMP, params={"where": where, "order_by": "dateparution desc", "limit": limite})
    r.raise_for_status()
    return [a for a in (avis_boamp(e) for e in r.json().get("results") or []) if a]


# ---------------------------------------------------------------------------- TED

CHAMPS_TED = ["publication-number", "notice-title", "buyer-name", "buyer-country", "notice-type",
              "publication-date", "winner-name", "links"]


def avis_ted(n: dict) -> dict | None:
    titre = _texte(n.get("notice-title"))
    if not parle_d_ia(titre):
        return None
    type_avis = _texte(n.get("notice-type")).lower()
    attribution = type_avis.startswith("can") or "award" in type_avis or "result" in type_avis
    numero = str(n.get("publication-number") or "")
    gagnants = _texte(n.get("winner-name"))
    liens = n.get("links") or {}
    url = None
    if isinstance(liens, dict):
        html = liens.get("html") or {}
        url = (html.get("FRA") or html.get("ENG") or next(iter(html.values()), None)) if isinstance(html, dict) else None
    return {
        "id": f"ted:{numero}", "base": "TED", "pays": _texte(n.get("buyer-country")).strip() or None,
        "type": "attribution" if attribution else "appel_offres",
        "date": str(n.get("publication-date") or "")[:10],
        "acheteur": _texte(n.get("buyer-name")).strip()[:200],
        "objet": re.sub(r"\s+", " ", titre).strip()[:300],
        "fournisseurs": fournisseurs_cites(gagnants + " " + titre),
        "titulaire": gagnants.strip()[:200] or None,
        "url": url or (f"https://ted.europa.eu/fr/notice/-/detail/{numero}" if numero else None),
    }


def lire_ted(client: httpx.Client, depuis: datetime, limite: int = 100) -> list[dict]:
    requete = (f'(FT~"artificial intelligence" OR FT~"intelligence artificielle" OR FT~"large language model" '
               f'OR FT~"generative AI") AND publication-date>={depuis.strftime("%Y%m%d")}')
    corps = {"query": requete, "fields": CHAMPS_TED, "limit": limite, "page": 1, "scope": "ALL",
             "paginationMode": "PAGE_NUMBER", "checkQuerySyntax": False}
    r = client.post(TED, json=corps)
    if r.status_code == 400:                          # un champ refusé : on réessaie avec le strict minimum
        corps["fields"] = ["publication-number", "notice-title", "buyer-name", "notice-type", "publication-date"]
        r = client.post(TED, json=corps)
    r.raise_for_status()
    return [a for a in (avis_ted(n) for n in r.json().get("notices") or []) if a]


# ---------------------------------------------------------------------------- ensemble

def collecter(racine: Path, client: httpx.Client | None = None, maintenant: datetime | None = None,
              jours: int = 4, garder: int = 60) -> dict:
    """Ajoute à public/marches.json les avis des derniers jours. Une base en panne n'arrête rien."""
    maintenant = maintenant or datetime.now(timezone.utc)
    depuis = maintenant - timedelta(days=jours)
    chemin = racine / "public" / "marches.json"
    try:
        ancien = json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        ancien = {}
    avis = {a["id"]: a for a in ancien.get("avis") or []}
    sources = {}
    propre = client is None
    client = client or httpx.Client(timeout=60, headers={"User-Agent": AGENT})
    try:
        for nom, lire in (("BOAMP", lire_boamp), ("TED", lire_ted)):
            try:
                trouves = lire(client, depuis)
                for a in trouves:
                    a.setdefault("vu_le", maintenant.date().isoformat())
                    avis[a["id"]] = {**avis.get(a["id"], {}), **a}
                sources[nom] = {"etat": "ok", "nombre": len(trouves)}
            except (httpx.HTTPError, ValueError, KeyError) as e:
                sources[nom] = {"etat": "erreur", "raison": f"{type(e).__name__}: {str(e)[:160]}"}
    finally:
        if propre:
            client.close()
    limite = (maintenant - timedelta(days=garder)).date().isoformat()
    garde = sorted((a for a in avis.values() if (a.get("date") or "9999") >= limite),
                   key=lambda a: (a.get("date") or "", a["id"]), reverse=True)
    sortie = {"maj": maintenant.isoformat(timespec="seconds"), "sources": sources, "avis": garde}
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(json.dumps(sortie, ensure_ascii=False, indent=1), encoding="utf-8")
    return sortie


def a_signaler(racine: Path, vus: set, n: int = 8) -> list[dict]:
    """Les avis pas encore montrés à la rédaction : d'abord les attributions qui citent un fournisseur."""
    try:
        d = json.loads((racine / "public" / "marches.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    nouveaux = [a for a in d.get("avis") or [] if a["id"] not in vus]
    nouveaux.sort(key=lambda a: (a["type"] == "attribution", bool(a.get("fournisseurs")), a.get("date") or ""), reverse=True)
    return nouveaux[:n]
