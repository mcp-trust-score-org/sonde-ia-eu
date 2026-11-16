"""Alertes : prévenir dès qu'un fournisseur change de temps, sans répéter.

    python -m sonde alertes    # compare public/meteo.json à l'état précédent et envoie les nouveautés

Canaux (variables d'environnement, tous facultatifs) :
  NTFY_TOPIC          notification sur le téléphone via l'application gratuite ntfy (ntfy.sh)
  NTFY_SERVEUR        autre serveur ntfy (par défaut https://ntfy.sh)
  ALERTE_WEBHOOK_URL  webhook Slack, Discord, Teams ou Mattermost (message texte)

Les alertes sont aussi ajoutées à public/alertes.json : l'appli les affiche.
On n'alerte que sur un changement : début d'orage, fin d'orage, passage en vigilance orange.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import httpx

from .retours import sujet_retours


def _heure(iso: str | None) -> str:
    if not iso:
        return "?"
    return datetime.fromisoformat(iso).astimezone().strftime("%H:%M")


def conseil_contrat(contrats: dict, fournisseur: str) -> str | None:
    c = (contrats or {}).get("contrats", {}).get(fournisseur) or {}
    if c.get("debut_decompte") == "ticket":
        return "Ouvrez un ticket maintenant : chez ce fournisseur, le temps de panne ne compte qu'à partir du ticket."
    return None


def detecter(precedent: dict, meteo: dict, contrats: dict | None = None) -> list[dict]:
    """Liste des alertes à envoyer, d'après l'état précédent {fournisseur: {etat, vigilance}}."""
    alertes = []
    calmes = [f["nom_court"] for f in meteo["fournisseurs"] if f["etat"] in ("soleil", "eclaircie")]
    for f in meteo["fournisseurs"]:
        avant = precedent.get(f["id"], {})
        e_av, v_av = avant.get("etat"), avant.get("vigilance")
        if f["etat"] == "inconnu":
            continue
        bis = [n for n in calmes if n != f["nom_court"]]
        if f["etat"] == "orage" and e_av != "orage":
            p = f.get("panne_en_cours") or {}
            texte = f"{f['nom']} est en panne"
            if p.get("depuis"):
                texte += f" depuis {_heure(p['depuis'])}"
            if f.get("taux_erreur") is not None:
                texte += f" ({round(100 * f['taux_erreur'])} % d'échecs)"
            texte += ". La panne vient du fournisseur, pas de chez vous."
            if bis:
                texte += f" Itinéraire bis : {', '.join(bis)} fonctionne normalement."
            c = conseil_contrat(contrats or {}, f["id"])
            if c:
                texte += " " + c
            alertes.append({"fournisseur": f["id"], "type": "orage", "niveau": "rouge",
                            "titre": f"Orage sur {f['nom_court']}", "texte": texte})
        elif e_av == "orage" and f["etat"] != "orage":
            dernier = (f.get("incidents_30j") or [{}])[0]
            duree = dernier.get("duree_min")
            texte = f"{f['nom']} fonctionne de nouveau"
            texte += f", après {duree} minutes de panne." if duree else "."
            texte += " Pensez à la réclamation : le dossier se prépare avec `python -m sonde avoirs`."
            alertes.append({"fournisseur": f["id"], "type": "fin_orage", "niveau": "vert",
                            "titre": f"Fin de l'orage sur {f['nom_court']}", "texte": texte})
        elif f["vigilance"] == "orange" and v_av not in ("orange", "rouge"):
            alertes.append({"fournisseur": f["id"], "type": "vigilance", "niveau": "orange",
                            "titre": f"Vigilance orange sur {f['nom_court']}",
                            "texte": f"{f['nom']} : {f.get('raison') or 'dégradation en cours'}."})
    return alertes


def envoyer(alerte: dict, env: dict | None = None, client: httpx.Client | None = None) -> list[str]:
    """Envoie sur les canaux configurés. Renvoie la liste des canaux réussis ; ne lève jamais."""
    env = env if env is not None else os.environ
    faits = []
    propre = client is None
    client = client or httpx.Client(timeout=10)
    try:
        topic = env.get("NTFY_TOPIC")
        if topic:
            serveur = env.get("NTFY_SERVEUR", "https://ntfy.sh").rstrip("/")
            priorite = {"rouge": 5, "orange": 4}.get(alerte["niveau"], 3)
            tag = {"rouge": "cloud_with_lightning", "orange": "warning", "vert": "sunny"}.get(alerte["niveau"], "cloud")
            corps = {"topic": topic, "message": alerte["texte"], "title": alerte["titre"],
                     "priority": priorite, "tags": [tag]}
            # Deux boutons dans la notification : le membre dit s'il est touché, sans rien installer.
            retours = sujet_retours(env)
            if retours and alerte.get("id") and alerte.get("type") in ("orage", "vigilance"):
                url = f"{serveur}/{retours}"
                corps["actions"] = [
                    {"action": "http", "label": "Moi aussi", "url": url, "method": "POST",
                     "body": f"touche|{alerte['id']}", "clear": True},
                    {"action": "http", "label": "Pas chez moi", "url": url, "method": "POST",
                     "body": f"pas_touche|{alerte['id']}", "clear": True},
                ]
            try:
                # Publication en JSON : accents et boutons passent sans souci.
                r = client.post(serveur, json=corps)
                if r.status_code < 300:
                    faits.append("ntfy")
            except httpx.HTTPError:
                pass
        url = env.get("ALERTE_WEBHOOK_URL")
        if url:
            texte = f"*{alerte['titre']}*\n{alerte['texte']}"
            try:
                r = client.post(url, json={"text": texte, "content": texte})
                if r.status_code < 300:
                    faits.append("webhook")
            except httpx.HTTPError:
                pass
    finally:
        if propre:
            client.close()
    return faits


def traiter(dossier_donnees: Path, dossier_public: Path, contrats: dict | None = None,
            env: dict | None = None, envoi=envoyer) -> list[dict]:
    meteo = json.loads((dossier_public / "meteo.json").read_text(encoding="utf-8"))
    f_etat = dossier_donnees / "alertes-etat.json"
    try:
        precedent = json.loads(f_etat.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        precedent = None
    alertes = detecter(precedent or {}, meteo, contrats) if precedent is not None else []
    # Premier passage : on enregistre l'état sans alerter (sinon toute panne déjà en cours repartirait).
    for a in alertes:
        a["horodatage"] = meteo["genere_le"]
        moment = datetime.fromisoformat(meteo["genere_le"]).astimezone(timezone.utc).strftime("%Y%m%d%H%M")
        a["id"] = f"{a['fournisseur']}-{a['type']}-{moment}".lower().replace("_", "-")
        a["canaux"] = envoi(a, env)
    f_journal = dossier_public / "alertes.json"
    try:
        journal = json.loads(f_journal.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        journal = []
    journal = (list(reversed(alertes)) + journal)[:100]
    f_journal.write_text(json.dumps(journal, ensure_ascii=False, indent=1), encoding="utf-8")
    dossier_donnees.mkdir(parents=True, exist_ok=True)
    f_etat.write_text(json.dumps({f["id"]: {"etat": f["etat"], "vigilance": f["vigilance"]} for f in meteo["fournisseurs"]},
                                 ensure_ascii=False), encoding="utf-8")
    return alertes
