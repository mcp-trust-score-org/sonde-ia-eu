"""Bulletin du matin : une image à partager (format LinkedIn 1080 × 1350) et son texte.

    python -m sonde bulletin     # écrit public/bulletin.svg, public/bulletin.txt (et .png si cairosvg est installé)
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

COULEUR = {"soleil": "#7BD3A4", "eclaircie": "#FFD25E", "nuage": "#AEB7C2", "orage": "#FF8A6B", "inconnu": "#5B6470"}
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]


def date_fr(d: datetime) -> str:
    return f"{JOURS[d.weekday()]} {d.day} {MOIS[d.month - 1]}"


def position_radar(i: int, n: int, rayon: float) -> tuple[float, float]:
    """Position d'un fournisseur sur le radar : répartis autour du centre, à rayon variable."""
    angle = -math.pi / 2 + 2 * math.pi * i / max(n, 1) + 0.35
    r = rayon * (0.45 + 0.35 * ((i * 37) % 10) / 10)
    return math.cos(angle) * r, math.sin(angle) * r


def _lignes_phrase(phrase: str, largeur: int = 26) -> list[str]:
    mots, lignes, cour = phrase.split(), [], ""
    for m in mots:
        if len(cour) + len(m) + 1 > largeur and cour:
            lignes.append(cour)
            cour = m
        else:
            cour = (cour + " " + m).strip()
    if cour:
        lignes.append(cour)
    return lignes[:4]


def svg(meteo: dict, signature: str = "[TON NOM] · [ADRESSE DU SITE]") -> str:
    quand = datetime.fromisoformat(meteo["genere_le"]).astimezone()
    fs = meteo["fournisseurs"]
    cx, cy, R = 320, 760, 220
    morceaux = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1350" viewBox="0 0 1080 1350" font-family="Geist, Helvetica, Arial, sans-serif">',
        '<defs><radialGradient id="ciel" cx="50%" cy="0%" r="90%"><stop offset="0%" stop-color="#142033"/><stop offset="60%" stop-color="#0B0F14"/></radialGradient>',
        '<radialGradient id="radar" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="#121A24"/><stop offset="100%" stop-color="#0B0F14"/></radialGradient>',
        '<radialGradient id="orage"><stop offset="0%" stop-color="#FF7850" stop-opacity=".85"/><stop offset="45%" stop-color="#FF7850" stop-opacity=".35"/><stop offset="72%" stop-color="#FF7850" stop-opacity="0"/></radialGradient>',
        '<radialGradient id="nuage"><stop offset="0%" stop-color="#AEB7C2" stop-opacity=".5"/><stop offset="70%" stop-color="#AEB7C2" stop-opacity="0"/></radialGradient></defs>',
        '<rect width="1080" height="1350" fill="url(#ciel)"/>',
        '<text x="96" y="140" font-size="40" font-weight="600" fill="#F2F4F7">La météo de l\'IA</text>',
        f'<text x="984" y="140" font-size="30" fill="#8E98A5" text-anchor="end">{escape(date_fr(quand))}</text>',
    ]
    y = 260
    for ligne in _lignes_phrase(meteo["phrase"]):
        morceaux.append(f'<text x="96" y="{y}" font-size="72" fill="#F2F4F7" letter-spacing="-1.5">{escape(ligne)}</text>')
        y += 84
    morceaux += [
        f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="url(#radar)" stroke="#222A33" stroke-width="2"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{R * 0.66:.0f}" fill="none" stroke="#1C2530" stroke-width="2"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{R * 0.33:.0f}" fill="none" stroke="#1C2530" stroke-width="2"/>',
        f'<line x1="{cx - R}" y1="{cy}" x2="{cx + R}" y2="{cy}" stroke="#1C2530" stroke-width="2"/>',
        f'<line x1="{cx}" y1="{cy - R}" x2="{cx}" y2="{cy + R}" stroke="#1C2530" stroke-width="2"/>',
    ]
    for i, f in enumerate(fs):
        dx, dy = position_radar(i, len(fs), R)
        x, yy = cx + dx, cy + dy
        if f["etat"] == "orage":
            morceaux.append(f'<ellipse cx="{x:.0f}" cy="{yy:.0f}" rx="80" ry="66" fill="url(#orage)"/>')
        elif f["etat"] == "nuage":
            morceaux.append(f'<ellipse cx="{x:.0f}" cy="{yy:.0f}" rx="56" ry="44" fill="url(#nuage)"/>')
        morceaux.append(f'<circle cx="{x:.0f}" cy="{yy:.0f}" r="9" fill="{COULEUR[f["etat"]]}" stroke="#0B0F14" stroke-width="5"/>')
    ly = 600
    for f in fs[:6]:
        morceaux += [
            f'<circle cx="610" cy="{ly - 10}" r="10" fill="{COULEUR[f["etat"]]}"/>',
            f'<text x="636" y="{ly}" font-size="36" font-weight="500" fill="#F2F4F7">{escape(f["nom_court"])}</text>',
            f'<text x="636" y="{ly + 40}" font-size="27" fill="#C3CAD3">{escape(f["ciel"] + ", " + f["libelle"].lower())}</text>',
            f'<line x1="600" y1="{ly + 66}" x2="984" y2="{ly + 66}" stroke="#1C2530" stroke-width="2"/>',
        ]
        ly += 104
    surveiller = [f for f in fs if f["vigilance"] in ("jaune", "orange") and f.get("raison")]
    if surveiller:
        s = surveiller[0]
        morceaux.append(f'<text x="96" y="1110" font-size="30" fill="#C3CAD3">À surveiller : {escape(s["nom_court"])}, {escape(s["raison"][0].lower() + s["raison"][1:])}.</text>')
    morceaux += [
        '<line x1="96" y1="1210" x2="984" y2="1210" stroke="#222A33" stroke-width="2"/>',
        f'<text x="96" y="1262" font-size="28" font-weight="500" fill="#F2F4F7">{escape(signature)}</text>',
        f'<text x="984" y="1262" font-size="24" fill="#8E98A5" text-anchor="end">Mesuré chaque minute{(" depuis " + escape(meteo["point_de_mesure"])) if meteo.get("point_de_mesure") else ""}</text>',
        "</svg>",
    ]
    return "\n".join(morceaux)


def texte(meteo: dict, adresse: str = "[ADRESSE DU SITE]") -> str:
    quand = datetime.fromisoformat(meteo["genere_le"]).astimezone()
    lignes = [f"La météo de l'IA, {date_fr(quand).lower()}.", "", meteo["phrase"], ""]
    for f in meteo["fournisseurs"]:
        d = f["disponibilite"].get("24h")
        dispo = f" · {str(d).replace('.', ',')} % sur 24 h" if d is not None else ""
        lignes.append(f"• {f['nom_court']} : {f['ciel'].lower()}, {f['libelle'].lower()}{dispo}")
    limite = datetime.fromisoformat(meteo["genere_le"]) - timedelta(hours=24)
    pannes = [(f["nom_court"], i) for f in meteo["fournisseurs"] for i in f.get("incidents_30j", [])
              if datetime.fromisoformat(i["fin"]) > limite]
    if pannes:
        lignes += ["", "Pannes des dernières 24 h :"]
        lignes += [f"• {n} : {i['duree_min']} min, à partir de {datetime.fromisoformat(i['debut']).astimezone():%H:%M}" for n, i in pannes[:5]]
    lignes += ["", "Mesure indépendante, chaque minute, des fournisseurs d'IA européens.", f"La météo en direct : {adresse}",
               "", "#IA #Mistral #Scaleway #OVHcloud #DORA"]
    return "\n".join(lignes)


def produire_bulletin(dossier_public: Path, signature: str | None = None, adresse: str | None = None) -> list[Path]:
    meteo = json.loads((dossier_public / "meteo.json").read_text(encoding="utf-8"))
    sorties = []
    p_svg = dossier_public / "bulletin.svg"
    p_svg.write_text(svg(meteo, signature or "[TON NOM] · [ADRESSE DU SITE]"), encoding="utf-8")
    sorties.append(p_svg)
    p_txt = dossier_public / "bulletin.txt"
    p_txt.write_text(texte(meteo, adresse or "[ADRESSE DU SITE]"), encoding="utf-8")
    sorties.append(p_txt)
    try:
        import cairosvg  # facultatif : pip install cairosvg
        p_png = dossier_public / "bulletin.png"
        cairosvg.svg2png(url=str(p_svg), write_to=str(p_png))
        sorties.append(p_png)
    except Exception:
        pass
    return sorties
