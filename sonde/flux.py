"""Le flux RSS du site (iris/flux.xml) : les derniers articles publiés, pour Brevo et les lecteurs RSS.

Réécrit à chaque publication et à chaque retrait (sonde/publication.py). Brevo lit ce flux
chaque jour et envoie un mail à ses inscrits s'il y a du nouveau.
L'adresse du site vient de la variable SITE_URL (dans GitHub : Settings → Secrets and
variables → Actions → Variables).
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")
SITE_PAR_DEFAUT = "https://sonde-ia-eu-iris.vercel.app"
RUBRIQUES = {"une": "À la une", "tous_connectes": "Tous connectés"}


def _plat(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html or "")).replace(" .", ".").strip()


def _quand(a: dict) -> datetime:
    if a.get("publie_le"):
        try:
            return datetime.fromisoformat(a["publie_le"])
        except ValueError:
            pass
    return datetime.fromisoformat(a.get("date", "2026-01-01") + "T07:00:00").replace(tzinfo=PARIS)


def ecrire_flux(racine: Path, site: str | None = None, n: int = 20) -> Path:
    site = (site or os.environ.get("SITE_URL") or SITE_PAR_DEFAUT).rstrip("/")
    pub_chemin = racine / "iris" / "publies.json"
    publies = json.loads(pub_chemin.read_text(encoding="utf-8")) if pub_chemin.exists() else {}
    articles = [(k, a) for k in RUBRIQUES for a in publies.get(k) or [] if a.get("id") and a.get("title")]
    articles.sort(key=lambda x: _quand(x[1]), reverse=True)
    items = []
    for k, a in articles[:n]:
        lien = f"{site}/#article-{a['id']}"
        items.append(f"""  <item>
   <title>{escape(_plat(a['title']))}</title>
   <link>{escape(lien)}</link>
   <guid isPermaLink="false">iris-{escape(a['id'])}</guid>
   <category>{escape(RUBRIQUES[k])}</category>
   <pubDate>{format_datetime(_quand(a))}</pubDate>
   <description>{escape(_plat(a.get('chapo', '')))}</description>
  </item>""")
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
 <channel>
  <title>Iris · Voir venir. Transmettre l'essentiel.</title>
  <link>{escape(site)}/</link>
  <description>Les événements inattendus qui révèlent notre dépendance à la technologie.</description>
  <language>fr</language>
{chr(10).join(items)}
 </channel>
</rss>
"""
    sortie = racine / "iris" / "flux.xml"
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text(xml, encoding="utf-8")
    return sortie
