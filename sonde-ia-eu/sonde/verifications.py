"""Vérification automatique des réponses aux tâches."""

from __future__ import annotations

import json
import re
import unicodedata


def normaliser(texte: str) -> str:
    """Minuscules, sans accents, espaces compactés."""
    texte = unicodedata.normalize("NFKD", texte)
    texte = "".join(c for c in texte if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texte.lower()).strip()


def _premier_nombre(texte: str) -> float | None:
    # Accepte 178,8 / 178.80 / 1 234,5
    m = re.search(r"-?\d[\d\s  ]*(?:[.,]\d+)?", texte)
    if not m:
        return None
    brut = re.sub(r"[\s  ]", "", m.group(0)).replace(",", ".")
    try:
        return float(brut)
    except ValueError:
        return None


def _extraire_json(texte: str):
    # Retire un éventuel bloc ```json ... ```
    bloc = re.search(r"```(?:json)?\s*(.*?)```", texte, re.S)
    candidat = bloc.group(1) if bloc else texte
    debut, fin = candidat.find("{"), candidat.rfind("}")
    if debut == -1 or fin == -1:
        return None
    try:
        return json.loads(candidat[debut : fin + 1])
    except json.JSONDecodeError:
        return None


def verifier(reponse: str, regle: dict) -> bool:
    """Renvoie True si la réponse satisfait la règle de vérification."""
    type_ = regle["type"]
    rep = normaliser(reponse)

    if type_ == "contient":
        return any(normaliser(v) in rep for v in regle["valeurs"])

    if type_ == "contient_tout":
        return all(normaliser(v) in rep for v in regle["valeurs"])

    if type_ == "nombre":
        n = _premier_nombre(reponse)
        return n is not None and abs(n - float(regle["valeur"])) < 0.01

    if type_ == "json_cles":
        obj = _extraire_json(reponse)
        if not isinstance(obj, dict):
            return False
        cles = {normaliser(k) for k in obj}
        if not all(normaliser(c) in cles for c in regle["cles"]):
            return False
        valeurs = normaliser(" ".join(str(v) for v in obj.values()))
        return all(normaliser(v) in valeurs for v in regle.get("valeurs", []))

    if type_ == "regex":
        return all(re.search(motif, reponse) for motif in regle["valeurs"])

    if type_ == "nb_lignes":
        lignes = [l for l in reponse.strip().splitlines() if l.strip()]
        return len(lignes) == int(regle["valeur"])

    raise ValueError(f"Type de vérification inconnu : {type_}")
