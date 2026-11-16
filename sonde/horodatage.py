"""Preuves horodatées : rendre les mesures opposables.

Chaque jour, on écrit un manifeste qui donne, pour chaque fichier de mesures, son nombre de
lignes et l'empreinte SHA-256 de son contenu à cet instant. Le manifeste est ensuite ancré
dans la blockchain Bitcoin via OpenTimestamps (gratuit, sans portefeuille) : on obtient un
fichier .ots qui prouve que le manifeste existait à cette date, donc que les mesures n'ont
pas été modifiées depuis.

Vérifier une preuve plus tard :
  1. tronquer le fichier de mesures au nombre de lignes indiqué dans le manifeste ;
  2. recalculer son SHA-256 et le comparer au manifeste ;
  3. `ots verify preuves/AAAA-MM-JJ.json.ots` (atteste la date du manifeste).
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def empreinte_fichier(chemin: Path, nb_lignes: int | None = None) -> tuple[str, int]:
    """SHA-256 des nb_lignes premières lignes (toutes si None)."""
    h, n = hashlib.sha256(), 0
    with open(chemin, "rb") as f:
        for ligne in f:
            if nb_lignes is not None and n >= nb_lignes:
                break
            h.update(ligne)
            n += 1
    return h.hexdigest(), n


def ecrire_manifeste(dossier_donnees: Path, dossier_preuves: Path, quand: datetime | None = None) -> Path:
    quand = quand or datetime.now(timezone.utc)
    dossier_preuves.mkdir(parents=True, exist_ok=True)
    fichiers = {}
    # Mesures horaires (data/*.jsonl) et veille à la minute (data/veille/*.jsonl).
    for f in sorted(dossier_donnees.glob("*.jsonl")) + sorted(dossier_donnees.glob("veille/*.jsonl")):
        sha, n = empreinte_fichier(f)
        fichiers[f.relative_to(dossier_donnees).as_posix()] = {"sha256": sha, "lignes": n}
    manifeste = {
        "genere_le": quand.isoformat(timespec="seconds"),
        "methode": "SHA-256 du contenu des N premières lignes de chaque fichier de mesures",
        "fichiers": fichiers,
    }
    chemin = dossier_preuves / f"{quand:%Y-%m-%d}.json"
    chemin.write_text(json.dumps(manifeste, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return chemin


def ancrer(chemin: Path) -> str:
    """Demande l'horodatage OpenTimestamps. Renvoie un statut lisible, ne lève jamais."""
    ots = shutil.which("ots")
    if not ots:
        return "ots absent (pip install opentimestamps-client)"
    try:
        r = subprocess.run([ots, "stamp", str(chemin)], capture_output=True, text=True, timeout=120)
        return "ancrage demandé" if r.returncode == 0 else f"échec : {r.stderr.strip()[:160]}"
    except Exception as e:
        return f"échec : {e}"


def completer_preuves(dossier_preuves: Path) -> list[str]:
    """Les preuves OTS se complètent après quelques heures (confirmation Bitcoin)."""
    ots = shutil.which("ots")
    if not ots:
        return []
    statuts = []
    for p in sorted(dossier_preuves.glob("*.ots")):
        try:
            r = subprocess.run([ots, "upgrade", str(p)], capture_output=True, text=True, timeout=120)
            statuts.append(f"{p.name}: {'complète' if r.returncode == 0 else 'en attente'}")
        except Exception:
            statuts.append(f"{p.name}: en attente")
    return statuts


def verifier_manifeste(chemin_manifeste: Path, dossier_donnees: Path) -> dict[str, bool]:
    m = json.loads(chemin_manifeste.read_text(encoding="utf-8"))
    resultat = {}
    for nom, info in m["fichiers"].items():
        f = dossier_donnees / nom
        resultat[nom] = f.exists() and empreinte_fichier(f, info["lignes"])[0] == info["sha256"]
    return resultat
