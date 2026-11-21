"""Ligne de commande.

    python -m sonde mesurer                 # toutes les tâches, tous les fournisseurs avec clé
    python -m sonde mesurer --echantillon 3 # 3 tâches par exécution, en rotation (usage horaire)
    python -m sonde mesurer --fournisseurs scaleway ovhcloud
    python -m sonde rapport --jours 7       # écrit public/classement.md et public/resume.json
    python -m sonde chemin                  # relevé du chemin réseau réel de chaque API
    python -m sonde empreinte               # empreinte quotidienne des modèles
    python -m sonde horodater               # manifeste du jour + ancrage OpenTimestamps
    python -m sonde dossiers                # un dossier de surveillance par fournisseur
    python -m sonde rapport-public          # brouillon du rapport public

    python -m sonde veille [--boucle]       # appel minimal par fournisseur, chaque minute
    python -m sonde meteo                   # public/meteo.json : la météo de l'IA
    python -m sonde alertes                 # envoie les changements de temps (ntfy, webhook)
    python -m sonde avoirs --mois 2026-10 [--facture scaleway=2400] [--ticket ovhcloud=2026-10-08T09:20]
    python -m sonde attestation --fournisseur ovhcloud --debut 2026-11-16T14:00 --fin 2026-11-16T16:00
    python -m sonde bulletin                # image et texte du bulletin du matin
    python -m sonde direct                  # meteo + alertes (à lancer après chaque veille)
    python -m sonde actualites              # événements inattendus collectés (public/actualites.json)
    python -m sonde croiser                 # croise événements et mesures (rapports/croisement.md)
    python -m sonde tendances               # sujets grand public et liens du Détour (public/tendances.json)
    python -m sonde rediger                 # propositions d'articles du jour (redaction/propositions/)
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

import json
import os
from datetime import datetime, timezone

from .mesure import RACINE, charger_yaml, executer
from .rapport import lire_lignes, produire


def _ajouter(lignes: list[dict], dossier: Path) -> None:
    dossier.mkdir(parents=True, exist_ok=True)
    with open(dossier / f"{datetime.now(timezone.utc):%Y-%m}.jsonl", "a", encoding="utf-8") as f:
        for l in lignes:
            f.write(json.dumps(l, ensure_ascii=False) + "\n")


def _utc(texte: str) -> datetime:
    d = datetime.fromisoformat(texte)
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _direct(donnees: Path) -> None:
    from .alertes import traiter
    from .meteo import produire_meteo
    config = charger_yaml(RACINE / "config" / "fournisseurs.yaml")
    conf_v = charger_yaml(RACINE / "config" / "veille.yaml")
    meteo = produire_meteo(donnees, RACINE / "public", config, conf_v)
    print("  météo :", meteo["phrase"])
    for a in traiter(donnees, RACINE / "public", charger_yaml(RACINE / "config" / "contrats.yaml")):
        print(f"  alerte : {a['titre']} ({', '.join(a['canaux']) or 'aucun canal configuré'})")
    from .statuts import produire_statuts
    statuts = produire_statuts(config, RACINE / "public")
    lus = [k for k, v in statuts["fournisseurs"].items() if v.get("etat_officiel")]
    print(f"  pages de statut lues : {', '.join(lus) or 'aucune'}")
    from .sla import publier_contrats
    publier_contrats(charger_yaml(RACINE / "config" / "contrats.yaml"), RACINE / "public")
    from .retours import relever, totaliser
    n = relever(donnees)
    totaliser(donnees, RACINE / "public")
    if n:
        print(f"  retours des membres : {n} nouveau(x)")


def _commandes_direct(args, donnees: Path, preuves: Path) -> int:
    config = charger_yaml(RACINE / "config" / "fournisseurs.yaml")
    if args.commande == "veille":
        from .veille import boucle, veiller
        conf_v = charger_yaml(RACINE / "config" / "veille.yaml")
        point = os.environ.get("POINT_DE_MESURE", "local")
        apres = (lambda _l: _direct(donnees)) if args.avec_meteo else None
        if args.boucle:
            print(f"Veille à la minute depuis « {point} ». Ctrl+C pour arrêter.", flush=True)
            boucle(config, conf_v, donnees, point, apres)
            return 0
        lignes = asyncio.run(veiller(config, conf_v, donnees, point=point, fournisseurs_filtre=args.fournisseurs))
        for l in lignes:
            etat = f"ok en {l['ttft_ms']} ms" if l["succes"] else f"ÉCHEC ({l['erreur']})"
            print(f"  - {l['fournisseur']} · {l['modele_id'] or '?'} : {etat}")
        if apres:
            apres(lignes)
        return 0
    if args.commande in ("meteo", "direct"):
        if args.commande == "direct":
            _direct(donnees)
            return 0
        from .meteo import produire_meteo
        meteo = produire_meteo(donnees, RACINE / "public", config, charger_yaml(RACINE / "config" / "veille.yaml"))
        print(meteo["phrase"])
        for f in meteo["fournisseurs"]:
            print(f"  - {f['nom_court']} : {f['ciel']} ({f['libelle']}), vigilance {f['vigilance']}")
        return 0
    if args.commande == "alertes":
        from .alertes import traiter
        alertes = traiter(donnees, RACINE / "public", charger_yaml(RACINE / "config" / "contrats.yaml"))
        for a in alertes:
            print(f"  - {a['titre']} ({', '.join(a['canaux']) or 'aucun canal configuré'})")
        if not alertes:
            print("  aucun changement")
        return 0
    if args.commande == "avoirs":
        from .sla import mois_precedent, produire_avoirs
        mois = args.mois or mois_precedent()
        factures = {k: float(v.replace(",", ".")) for k, v in (x.split("=", 1) for x in args.facture)}
        tickets: dict[str, list[datetime]] = {}
        for x in args.ticket:
            k, v = x.split("=", 1)
            tickets.setdefault(k, []).append(_utc(v))
        res = produire_avoirs(donnees, RACINE / "public", RACINE / "reclamations", config,
                              charger_yaml(RACINE / "config" / "contrats.yaml"), mois, factures, tickets)
        if not res:
            print(f"  aucune mesure de veille pour {mois}")
        for r in res:
            dispo = "—" if r["disponibilite_pct"] is None else f"{r['disponibilite_pct']:.3f} %"
            ligne = f"  - {r['fournisseur']} : {dispo} mesurés (couverture {r['couverture_pct']} %), palier {r['avoir_pct']:g} %"
            if "avoir_eur" in r:
                ligne += f", avoir {r['avoir_eur']:.2f} € → reclamations/{mois}/{r['fournisseur']}.md"
            if r["minutes_non_decomptees_faute_de_ticket"]:
                ligne += (f", {r['minutes_non_decomptees_faute_de_ticket']} min de panne non décomptées faute de ticket "
                          f"(avec ticket immédiat : {r['disponibilite_si_ticket_immediat_pct']} %)")
            if r["engagement_pct"] is None:
                ligne += ", pas d'engagement renseigné dans config/contrats.yaml"
            ligne += f", à réclamer avant le {r['echeance']}" + ("" if r["verifie"] else " (contrat non vérifié)")
            print(ligne)
        return 0
    if args.commande == "dossier-client":
        from .dossier_client import assembler, ecrire
        from .sla import mois_precedent
        client = charger_yaml(Path(args.client_fichier)) if args.client_fichier else {}
        if args.client:
            client["nom"] = args.client
        if args.facture is not None:
            client.setdefault("factures", {}).setdefault(args.fournisseur, {})[args.mois or mois_precedent()] = args.facture
        d = assembler(donnees, RACINE / "public", RACINE / "preuves", config,
                      charger_yaml(RACINE / "config" / "contrats.yaml"), client, args.fournisseur, args.mois or mois_precedent())
        chemin = ecrire(d, Path(args.sortie))
        print(f"  dossier écrit : {chemin} ({len(d['pannes'])} panne(s))")
        return 0
    if args.commande == "attestation":
        from .attestation import attester, ecrire
        a = attester(donnees, preuves, config, args.fournisseur, _utc(args.debut), _utc(args.fin))
        chemin = ecrire(a, RACINE / "attestations")
        print(f"  - {chemin.relative_to(RACINE)} : {a['minutes_en_echec']} minutes en échec sur {a['minutes_mesurees']} mesurées")
        return 0
    if args.commande == "bulletin":
        from .bulletin import produire_bulletin
        for c in produire_bulletin(RACINE / "public", args.signature, args.adresse):
            print("  -", c.relative_to(RACINE))
        return 0
    return 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="sonde", description="Mesure des API d'IA européennes")
    sous = p.add_subparsers(dest="commande", required=True)

    m = sous.add_parser("mesurer", help="lancer une série de mesures")
    m.add_argument("--config", type=Path, default=RACINE / "config" / "fournisseurs.yaml")
    m.add_argument("--taches", type=Path, default=RACINE / "config" / "taches.yaml")
    m.add_argument("--donnees", type=Path, default=RACINE / "data")
    m.add_argument("--echantillon", type=int, default=None, help="nombre de tâches par exécution")
    m.add_argument("--fournisseurs", nargs="*", default=None)

    r = sous.add_parser("rapport", help="produire le classement")
    r.add_argument("--donnees", type=Path, default=RACINE / "data")
    r.add_argument("--sortie", type=Path, default=RACINE / "public")
    r.add_argument("--jours", type=int, default=7)

    c = sous.add_parser("chemin", help="relever le chemin réseau réel")
    c.add_argument("--fournisseurs", nargs="*", default=None)
    e = sous.add_parser("empreinte", help="prendre l'empreinte des modèles")
    e.add_argument("--fournisseurs", nargs="*", default=None)
    sous.add_parser("horodater", help="manifeste du jour et ancrage OpenTimestamps")
    d = sous.add_parser("dossiers", help="dossiers de surveillance par fournisseur")
    d.add_argument("--jours", type=int, default=30)
    rp = sous.add_parser("rapport-public", help="brouillon du rapport public")
    rp.add_argument("--jours", type=int, default=30)

    v = sous.add_parser("veille", help="appel minimal par fournisseur (à la minute)")
    v.add_argument("--boucle", action="store_true", help="tourner en continu, un passage par minute")
    v.add_argument("--avec-meteo", action="store_true", help="recalculer la météo et les alertes après chaque passage")
    v.add_argument("--fournisseurs", nargs="*", default=None)
    sous.add_parser("meteo", help="calculer la météo de l'IA")
    sous.add_parser("alertes", help="envoyer les alertes de changement de temps")
    sous.add_parser("direct", help="météo puis alertes")
    sous.add_parser("actualites", help="collecter les événements inattendus")
    sous.add_parser("croiser", help="croiser les événements avec les mesures")
    sous.add_parser("tendances", help="sujets grand public et articles pour le Détour")
    sous.add_parser("rediger", help="propositions d'articles du jour, selon la charte")
    pub = sous.add_parser("publier", help="publier un brouillon validé sur le site (iris/publies.json)")
    pub.add_argument("--rubrique", default="une")
    pub.add_argument("--date", default="")
    pub.add_argument("--numero", type=int, default=1)
    pub.add_argument("--forcer", action="store_true")
    pub.add_argument("--retirer", default="", help="dernier-une, dernier-tous_connectes, dernier-detour ou un identifiant")
    av = sous.add_parser("avoirs", help="avoirs dus selon les contrats")
    av.add_argument("--mois", default=None, help="AAAA-MM (par défaut : le mois précédent)")
    av.add_argument("--facture", nargs="*", default=[], help="fournisseur=montant en euros")
    av.add_argument("--ticket", nargs="*", default=[], help="fournisseur=AAAA-MM-JJTHH:MM (UTC), une par ticket")
    at = sous.add_parser("attestation", help="attestation de panne sur un créneau")
    at.add_argument("--fournisseur", required=True)
    at.add_argument("--debut", required=True, help="AAAA-MM-JJTHH:MM (UTC)")
    at.add_argument("--fin", required=True, help="AAAA-MM-JJTHH:MM (UTC)")
    dc = sous.add_parser("dossier-client", help="dossier d'incident complet pour un client")
    dc.add_argument("--fournisseur", required=True)
    dc.add_argument("--mois", default=None, help="AAAA-MM (par défaut : le mois précédent)")
    dc.add_argument("--client-fichier", default=None, help="fichier YAML du client (dépôt privé)")
    dc.add_argument("--client", default=None, help="nom du client, si pas de fichier")
    dc.add_argument("--facture", type=float, default=None, help="facture du mois en euros, si pas de fichier")
    dc.add_argument("--sortie", default=str(RACINE / "dossiers-clients"))
    b = sous.add_parser("bulletin", help="bulletin du matin (image + texte)")
    b.add_argument("--signature", default=os.environ.get("BULLETIN_SIGNATURE"))
    b.add_argument("--adresse", default=os.environ.get("BULLETIN_ADRESSE"))

    args = p.parse_args(argv)
    donnees, preuves = RACINE / "data", RACINE / "preuves"

    if args.commande in ("veille", "meteo", "alertes", "direct", "avoirs", "attestation", "bulletin", "dossier-client"):
        return _commandes_direct(args, donnees, preuves)

    if args.commande == "actualites":
        from .actualites import produire_actualites
        res = produire_actualites(charger_yaml(RACINE / "config" / "actualites.yaml"), RACINE)
        for nom, etat in res["sources"].items():
            print(f"  - {nom} : {etat['etat']}" + (f" ({etat['raison']})" if etat.get("raison") else ""))
        print(f"  {len(res['evenements'])} événement(s), {len(res['angles_morts_sonde'])} angle(s) mort(s) de la sonde")
        return 0

    if args.commande == "croiser":
        from .croisement import croiser
        res = croiser(RACINE / "public", [RACINE / "public" / "actualites.json", RACINE / "config" / "evenements.json"],
                      RACINE / "rapports")
        print(f"  {len(res['impacts'])} impact(s) à relire dans rapports/croisement.md")
        for i in res["impacts"]:
            print(f"  [{i['correlation']['niveau']:<12}] {i['evenement']['fournisseur']:<10} {i['evenement']['titre'][:70]}")
        return 0

    if args.commande == "tendances":
        from .tendances import produire_tendances
        res = produire_tendances(charger_yaml(RACINE / "config" / "redaction.yaml"), RACINE)
        for nom, etat in res["sources"].items():
            print(f"  - {nom} : {etat['etat']}" + (f" ({etat.get('nombre')})" if "nombre" in etat else f" ({etat.get('raison')})"))
        return 0

    if args.commande == "publier":
        from .publication import RefusPublication, publier, retirer
        if args.retirer:
            n = retirer(RACINE, args.retirer)
            print(f"  {n} élément(s) retiré(s) du site.")
            return 0 if n else 1
        try:
            res = publier(RACINE, args.rubrique, args.date, args.numero, args.forcer)
        except RefusPublication as e:
            print(f"::error::Publication refusée : {e}")
            print(f"  Publication refusée : {e}")
            return 1
        print(f"  Publié sur le site : {res['titre']} ({res['rubrique']}, brouillon du {res['date']})")
        for a in res["alertes"]:
            print(f"::warning::{a}")
        return 0

    if args.commande == "rediger":
        from .redaction import rediger
        res = rediger(charger_yaml(RACINE / "config" / "redaction.yaml"), RACINE)
        for prop in res["propositions"]:
            titre = (prop.get("article") or {}).get("title") or f"{len(prop.get('liens') or [])} lien(s)"
            print(f"  [{prop['rubrique']:<14}] {prop['auteur']:<22} {titre[:70]} · {len(prop['alertes_charte'])} alerte(s)")
        print(f"  → redaction/propositions/{res['date']}.md")
        return 0

    if args.commande == "chemin":
        from .chemin import tracer
        config = charger_yaml(RACINE / "config" / "fournisseurs.yaml")
        point = os.environ.get("POINT_DE_MESURE", "GitHub Actions (" + os.environ.get("RUNNER_OS", "local") + ")")
        lignes = asyncio.run(tracer(config, args.fournisseurs, point))
        _ajouter(lignes, donnees)
        for l in lignes:
            print(f"  - {l['fournisseur']} ({l['hote']}) : {l['verdict']} · " + " ; ".join(l["constats"]))
        return 0

    if args.commande == "empreinte":
        from datetime import timedelta
        from .empreinte import executer_empreintes
        config = charger_yaml(RACINE / "config" / "fournisseurs.yaml")
        conf_e = charger_yaml(RACINE / "config" / "empreinte.yaml")
        anciennes = [l for l in lire_lignes(donnees, datetime(2000, 1, 1, tzinfo=timezone.utc)) if l.get("type") == "empreinte"]
        lignes = asyncio.run(executer_empreintes(config, conf_e, anciennes, os.environ, args.fournisseurs))
        _ajouter(lignes, donnees)
        for l in lignes:
            etat = "référence" if l["est_reference"] else f"similarité {l['similarite_reference']}"
            print(f"  - {l['fournisseur']} · {l['modele']} : {etat}" + (" · ALERTE changement probable" if l.get("alerte") else ""))
        return 0

    if args.commande == "horodater":
        from .horodatage import ancrer, completer_preuves, ecrire_manifeste
        for s_ in completer_preuves(preuves):
            print("  -", s_)
        m = ecrire_manifeste(donnees, preuves)
        print(f"  - {m.name} : {ancrer(m)}")
        return 0

    if args.commande == "dossiers":
        from .dossier import produire_dossiers
        for chemin in produire_dossiers(donnees, RACINE / "dossiers", preuves, args.jours):
            print("  -", chemin.relative_to(RACINE))
        return 0

    if args.commande == "rapport-public":
        from .rapport_public import brouillon
        sortie = RACINE / "rapports"
        sortie.mkdir(exist_ok=True)
        f = sortie / "brouillon-courant.md"
        f.write_text(brouillon(donnees, preuves, args.jours), encoding="utf-8")
        print("  -", f.relative_to(RACINE))
        return 0

    if args.commande == "mesurer":
        config = charger_yaml(args.config)
        taches = charger_yaml(args.taches)["taches"]
        lignes = asyncio.run(executer(config, taches, args.donnees, args.echantillon, args.fournisseurs))
        mesures = [l for l in lignes if l["type"] == "mesure"]
        ok = sum(l["succes"] for l in mesures)
        print(f"{len(mesures)} appels, {ok} réussis, {len(mesures) - ok} échecs.")
        for l in lignes:
            if l["type"] == "absent":
                print(f"  - {l['fournisseur']} : modèle {l['modele']} introuvable dans le catalogue")
            elif l["type"] == "catalogue" and l["erreur"]:
                print(f"  - {l['fournisseur']} : catalogue illisible ({l['erreur'][:80]})")
        return 0

    print(produire(args.donnees, args.sortie, args.jours))
    return 0


if __name__ == "__main__":
    sys.exit(main())
