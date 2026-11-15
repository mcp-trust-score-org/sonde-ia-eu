"""Ligne de commande.

    python -m sonde mesurer                 # toutes les tâches, tous les fournisseurs avec clé
    python -m sonde mesurer --echantillon 3 # 3 tâches par exécution, en rotation (usage horaire)
    python -m sonde mesurer --fournisseurs scaleway ovhcloud
    python -m sonde rapport --jours 7       # écrit public/classement.md et public/resume.json
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from .mesure import RACINE, charger_yaml, executer
from .rapport import produire


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

    args = p.parse_args(argv)

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
