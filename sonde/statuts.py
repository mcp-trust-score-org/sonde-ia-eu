"""Pages de statut officielles : ce que chaque fournisseur reconnaît lui-même.

Appelé à chaque `python -m sonde direct` : écrit public/statuts.json.

Pour chaque fournisseur, on lit sa page de statut publique et on garde :
  - son état officiel du moment (tout fonctionne, dégradé, panne, maintenance) ;
  - ses incidents récents qui concernent le service suivi.

L'appli compare ensuite ces incidents aux pannes que la sonde a mesurées : une panne
mesurée mais jamais signalée par le fournisseur est l'argument le plus fort d'une
réclamation. Les textes sont cités tels quels, sans interprétation.

Réglage dans config/fournisseurs.yaml, par fournisseur :
    statut:
      type: statuspage            # pages Atlassian Statuspage (API publique /api/v2/…)
      url: https://status.exemple.com
      motif: "AI Endpoint"        # morceau du nom du composant ou de l'incident à suivre
ou, quand la page n'offre pas de données lisibles automatiquement :
    statut: {type: lien, url: https://status.exemple.com}
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

GRAVITE = {"operational": 0, "under_maintenance": 1, "degraded_performance": 2, "partial_outage": 3, "major_outage": 4}
LIBELLE = {0: "Tout fonctionne", 1: "Maintenance", 2: "Performances dégradées", 3: "Panne partielle", 4: "Panne majeure"}


def _concerne(motif: str, *textes: str | None) -> bool:
    m = re.compile(re.escape(motif), re.IGNORECASE)
    return any(t and m.search(t) for t in textes)


def lire_statuspage(client: httpx.Client, url: str, motif: str, maintenant: datetime) -> dict:
    """État officiel et incidents des 30 derniers jours, pour les composants qui contiennent `motif`."""
    base = url.rstrip("/")
    resume = client.get(f"{base}/api/v2/summary.json")
    resume.raise_for_status()
    s = resume.json()
    composants = [c for c in s.get("components") or [] if _concerne(motif, c.get("name"))]
    ids = {c["id"] for c in composants}
    gravite = max((GRAVITE.get(c.get("status"), 0) for c in composants), default=None)

    hist = client.get(f"{base}/api/v2/incidents.json")
    hist.raise_for_status()
    limite = maintenant - timedelta(days=30)
    incidents = []
    for i in hist.json().get("incidents") or []:
        noms = [c.get("name") for c in i.get("components") or []]
        touche = any(c.get("id") in ids for c in i.get("components") or []) or _concerne(motif, i.get("name"), *noms)
        if not touche or not i.get("created_at"):
            continue
        debut = datetime.fromisoformat(i["created_at"].replace("Z", "+00:00"))
        if debut < limite:
            continue
        incidents.append({
            "titre": i.get("name"), "debut": debut.astimezone(timezone.utc).isoformat(timespec="minutes"),
            "fin": (datetime.fromisoformat(i["resolved_at"].replace("Z", "+00:00")).astimezone(timezone.utc).isoformat(timespec="minutes")
                    if i.get("resolved_at") else None),
            "impact": i.get("impact"), "lien": i.get("shortlink") or f"{base}/incidents/{i.get('id')}",
        })
    en_cours = [i for i in incidents if not i["fin"]]
    if en_cours and (gravite or 0) < 2:
        gravite = 2   # un incident ouvert sur le service compte au moins comme une dégradation
    return {"etat_officiel": LIBELLE.get(gravite) if gravite is not None else None,
            "gravite": gravite, "incident_en_cours": en_cours[0] if en_cours else None,
            "incidents_30j": incidents[:30], "composants_suivis": [c.get("name") for c in composants]}


def produire_statuts(config: dict, dossier_public: Path, client: httpx.Client | None = None,
                     maintenant: datetime | None = None) -> dict:
    """Écrit public/statuts.json. Ne lève jamais : une page injoignable est notée comme telle."""
    maintenant = maintenant or datetime.now(timezone.utc)
    propre = client is None
    client = client or httpx.Client(timeout=15, follow_redirects=True, headers={"Accept": "application/json"})
    sortie = {"genere_le": maintenant.isoformat(timespec="seconds"), "fournisseurs": {}}
    try:
        for f in config["fournisseurs"] + config.get("assistants", []):
            st = f.get("statut")
            if not st or not st.get("url"):
                continue
            entree = {"type": st.get("type", "lien"), "url": st["url"]}
            if entree["type"] == "statuspage":
                try:
                    entree.update(lire_statuspage(client, st["url"], st.get("motif", ""), maintenant))
                except (httpx.HTTPError, ValueError, KeyError) as e:
                    entree["erreur"] = f"page de statut illisible ({type(e).__name__})"
            sortie["fournisseurs"][f["id"]] = entree
    finally:
        if propre:
            client.close()
    dossier_public.mkdir(parents=True, exist_ok=True)
    (dossier_public / "statuts.json").write_text(json.dumps(sortie, ensure_ascii=False, indent=1), encoding="utf-8")
    return sortie
