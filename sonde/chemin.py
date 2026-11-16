"""Chemin réseau réel de chaque API : par où passent vraiment les requêtes.

Pour chaque fournisseur :
  1. résolution DNS du nom d'hôte de l'API (adresses IPv4 et IPv6) ;
  2. pour chaque adresse, l'opérateur réseau qui l'annonce (numéro d'AS et titulaire)
     et son pays, via l'API publique RIPEstat (RIPE NCC, sans clé) ;
  3. les intermédiaires visibles dans les en-têtes HTTP (CDN, proxy, répartiteur de charge).

Ce que cela prouve : l'infrastructure réseau publique par laquelle entrent les requêtes.
Ce que cela ne prouve pas : l'endroit exact où le modèle tourne derrière cette entrée.
Le dossier le dit explicitement.
"""

from __future__ import annotations

import asyncio
import socket
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx

RIPESTAT = "https://stat.ripe.net/data"

# Opérateurs dont la société mère relève d'une juridiction non européenne (exposition possible
# au CLOUD Act américain ou équivalent). Correspondance par mot-clé dans le titulaire de l'AS.
# Liste volontairement courte et vérifiable ; à compléter au fil des constats.
OPERATEURS_NON_UE = {
    "CLOUDFLARE": ("Cloudflare", "US"),
    "AMAZON": ("Amazon (AWS / CloudFront)", "US"),
    "GOOGLE": ("Google", "US"),
    "MICROSOFT": ("Microsoft", "US"),
    "AKAMAI": ("Akamai", "US"),
    "FASTLY": ("Fastly", "US"),
    "ORACLE": ("Oracle", "US"),
    "DIGITALOCEAN": ("DigitalOcean", "US"),
    "INCAPSULA": ("Imperva", "US"),
    "ZSCALER": ("Zscaler", "US"),
    "VERCEL": ("Vercel", "US"),
}
OPERATEURS_UE = {
    "OVH": ("OVHcloud", "FR"),
    "SCALEWAY": ("Scaleway", "FR"),
    "ONLINE S.A.S": ("Scaleway (Online SAS)", "FR"),
    "IONOS": ("IONOS", "DE"),
    "1&1": ("IONOS (1&1)", "DE"),
    "HETZNER": ("Hetzner", "DE"),
    "OUTSCALE": ("3DS Outscale", "FR"),
    "BUNNY": ("Bunny.net", "SI"),
    "GCORE": ("Gcore", "LU"),
}
PAYS_UE_EEE = set("AT BE BG HR CY CZ DK EE FI FR DE GR HU IE IT LV LT LU MT NL PL PT RO SK SI ES SE IS LI NO".split())

# En-têtes qui trahissent un intermédiaire, et à qui ils appartiennent.
SIGNATURES_ENTETES = [
    ("cf-ray", None, "Cloudflare"),
    ("server", "cloudflare", "Cloudflare"),
    ("x-amz-cf-id", None, "Amazon CloudFront"),
    ("x-amz-cf-pop", None, "Amazon CloudFront"),
    ("via", "cloudfront", "Amazon CloudFront"),
    ("x-amzn-requestid", None, "Amazon (AWS)"),
    ("x-azure-ref", None, "Microsoft Azure Front Door"),
    ("x-msedge-ref", None, "Microsoft Azure"),
    ("x-served-by", "cache-", "Fastly"),
    ("x-fastly-request-id", None, "Fastly"),
    ("server", "akamai", "Akamai"),
    ("x-akamai-transformed", None, "Akamai"),
    ("server", "gws", "Google"),
    ("via", "google", "Google Cloud"),
    ("x-vercel-id", None, "Vercel"),
    ("server", "bunnycdn", "Bunny.net"),
]
JURIDICTION_INTERMEDIAIRE = {
    "Cloudflare": "US", "Amazon CloudFront": "US", "Amazon (AWS)": "US", "Microsoft Azure Front Door": "US",
    "Microsoft Azure": "US", "Fastly": "US", "Akamai": "US", "Google": "US", "Google Cloud": "US",
    "Vercel": "US", "Bunny.net": "SI",
}


def classer_operateur(titulaire: str | None) -> tuple[str | None, str | None]:
    """Renvoie (nom lisible, pays de la société mère) si l'opérateur est connu."""
    t = (titulaire or "").upper()
    for cle, val in {**OPERATEURS_NON_UE, **OPERATEURS_UE}.items():
        if cle in t:
            return val
    return None, None


def intermediaires_depuis_entetes(entetes: dict[str, str]) -> list[str]:
    h = {k.lower(): str(v).lower() for k, v in entetes.items()}
    trouves = []
    for nom, motif, qui in SIGNATURES_ENTETES:
        if nom in h and (motif is None or motif in h[nom]) and qui not in trouves:
            trouves.append(qui)
    return trouves


def resoudre(hote: str) -> list[str]:
    try:
        infos = socket.getaddrinfo(hote, 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        return []
    return sorted({i[4][0] for i in infos})


async def _ripe(client: httpx.AsyncClient, appel: str, ressource: str) -> dict:
    r = await client.get(f"{RIPESTAT}/{appel}/data.json", params={"resource": ressource, "sourceapp": "sonde-ia-eu"})
    r.raise_for_status()
    return r.json().get("data") or {}


async def decrire_ip(client: httpx.AsyncClient, ip: str) -> dict:
    d = {"ip": ip, "asn": None, "prefixe": None, "titulaire": None, "pays_ip": None,
         "operateur": None, "pays_operateur": None, "erreur": None}
    try:
        net = await _ripe(client, "network-info", ip)
        asns = net.get("asns") or []
        d["prefixe"] = net.get("prefix")
        if asns:
            d["asn"] = int(str(asns[0]).replace("AS", ""))
            ov = await _ripe(client, "as-overview", f"AS{d['asn']}")
            d["titulaire"] = ov.get("holder")
        geo = await _ripe(client, "maxmind-geo-lite", ip)
        for res in geo.get("located_resources") or []:
            for loc in res.get("locations") or []:
                if loc.get("country"):
                    d["pays_ip"] = loc["country"]
                    break
            if d["pays_ip"]:
                break
    except Exception as e:
        d["erreur"] = " ".join(f"{type(e).__name__}: {e}".split())[:200]
    d["operateur"], d["pays_operateur"] = classer_operateur(d["titulaire"])
    return d


async def entetes_http(client: httpx.AsyncClient, url: str) -> tuple[int | None, dict]:
    try:
        r = await client.get(url, follow_redirects=False)
        return r.status_code, dict(r.headers)
    except Exception:
        return None, {}


def verdict(ips: list[dict], intermediaires: list[str]) -> tuple[str, list[str]]:
    """Synthèse prudente : on ne conclut que sur ce qui est observé."""
    constats = []
    for i in ips:
        if i["pays_operateur"] and i["pays_operateur"] not in PAYS_UE_EEE:
            constats.append(f"Entrée réseau {i['ip']} opérée par {i['operateur']} (société mère : {i['pays_operateur']})")
        elif i["pays_ip"] and i["pays_ip"] not in PAYS_UE_EEE:
            constats.append(f"Entrée réseau {i['ip']} localisée hors UE ({i['pays_ip']})")
    for x in intermediaires:
        pays = JURIDICTION_INTERMEDIAIRE.get(x)
        if pays and pays not in PAYS_UE_EEE:
            constats.append(f"Intermédiaire {x} visible dans les en-têtes (société mère : {pays})")
    if not ips:
        return "indetermine", ["Nom d'hôte non résolu"]
    if constats:
        return "intermediaire_non_ue", constats
    if all(i["pays_operateur"] in PAYS_UE_EEE or (i["pays_operateur"] is None and i["pays_ip"] in PAYS_UE_EEE) for i in ips):
        return "ue_observe", ["Toutes les entrées réseau observées sont opérées et localisées dans l'UE/EEE"]
    return "indetermine", ["Opérateur non reconnu : à qualifier manuellement"]


async def tracer(config: dict, fournisseurs_filtre: list[str] | None = None, point_de_mesure: str = "") -> list[dict]:
    lignes = []
    async with httpx.AsyncClient(timeout=httpx.Timeout(20, connect=10)) as client:
        for f in config["fournisseurs"]:
            if fournisseurs_filtre and f["id"] not in fournisseurs_filtre:
                continue
            hote = urlparse(f["base_url"]).hostname
            adresses = await asyncio.to_thread(resoudre, hote)
            ips = [await decrire_ip(client, ip) for ip in adresses[:6]]
            statut, entetes = await entetes_http(client, f"{f['base_url']}/models")
            inter = intermediaires_depuis_entetes(entetes)
            v, constats = verdict(ips, inter)
            lignes.append({
                "type": "chemin",
                "horodatage": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "fournisseur": f["id"], "hote": hote, "point_de_mesure": point_de_mesure,
                "ips": ips, "statut_http": statut,
                "entetes_observes": {k: v for k, v in entetes.items() if k.lower() in
                                     {"server", "via", "cf-ray", "x-cache", "x-served-by", "x-amz-cf-pop", "x-azure-ref"}},
                "intermediaires": inter, "verdict": v, "constats": constats,
            })
    return lignes
