"""Les cartes partageables du mercato de l'IA (1080 × 1350, format LinkedIn / Instagram).

Une carte par mouvement de iris/mercato.json, dessinée à partir de ses données : « C'est signé. », le tampon
OFFICIEL ou PRESSE, l'entreprise, le mouvement, la phrase de contexte, « L'enjeu » (s'il est renseigné), la source.
Écrites dans iris/cartes/<id>.jpg (lues en direct par le site : /d/cartes/<id>.jpg).

    python -m sonde.cartes            # dessine les cartes qui manquent
    python -m sonde.cartes --toutes   # les redessine toutes
Les polices (Barlow, Barlow Condensed : SIL OFL ; Roboto Slab : Apache 2.0) sont dans sonde/polices/.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RACINE = Path(__file__).resolve().parent.parent
POLICES = Path(__file__).resolve().parent / "polices"
L, H = 1080, 1350
NOIR, JAUNE, ROUGE, CREME, GRIS, TRAIT = (10, 10, 10), (255, 204, 0), (255, 74, 61), (244, 241, 234), (201, 201, 201), (42, 42, 42)
MARGE = 56
LIEN = "Lire l'article sur iris.media"      # le texte du lien en bas de la carte (à changer avec le nom de domaine)


def identifiant(x: dict) -> str:
    """Un identifiant stable pour un mouvement : entreprise + mois + destination."""
    brut = f"{x.get('entreprise', '')}-{x.get('date', '')}-{x.get('pour', '')}"
    brut = "".join(c for c in unicodedata.normalize("NFKD", brut) if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", brut).strip("-")[:80]     # même calcul que idMercato() dans iris/main.js


def _police(nom: str, taille: int, graisse: int | None = None) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(POLICES / nom), taille)
    if graisse:
        f.set_variation_by_axes([graisse])
    return f


def _lignes(d: ImageDraw.ImageDraw, texte: str, police, largeur: int) -> list[str]:
    mots, lignes, ligne = texte.split(), [], ""
    for m in mots:
        essai = (ligne + " " + m).strip()
        if d.textlength(essai, font=police) <= largeur or not ligne:
            ligne = essai
        else:
            lignes.append(ligne)
            ligne = m
    return lignes + ([ligne] if ligne else [])


def _ajuster(d, texte: str, nom: str, taille: int, largeur: int, mini: int):
    """La plus grande taille (jusqu'à `mini`) où le texte tient sur une ligne."""
    while taille > mini and d.textlength(texte, font=_police(nom, taille)) > largeur:
        taille -= 2
    return _police(nom, taille)


def _tampon(texte: str, couleur, police, epaisseur: int, pointilles: bool = False) -> Image.Image:
    w = int(police.getlength(texte)) + 40
    h = police.size + 22
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if pointilles:
        for x in range(0, w, 18):
            d.line([(x, 1), (min(x + 10, w), 1)], fill=couleur, width=epaisseur)
            d.line([(x, h - 2), (min(x + 10, w), h - 2)], fill=couleur, width=epaisseur)
        for y in range(0, h, 18):
            d.line([(1, y), (1, min(y + 10, h))], fill=couleur, width=epaisseur)
            d.line([(w - 2, y), (w - 2, min(y + 10, h))], fill=couleur, width=epaisseur)
    else:
        d.rectangle([epaisseur // 2, epaisseur // 2, w - epaisseur // 2 - 1, h - epaisseur // 2 - 1], outline=couleur, width=epaisseur)
    d.text((w / 2, h / 2 + 2), texte, font=police, fill=couleur, anchor="mm")
    return im.rotate(7, expand=True, resample=Image.BICUBIC)


def dessiner(x: dict, image_entete: Path) -> Image.Image:
    carte = Image.new("RGB", (L, H), NOIR)
    d = ImageDraw.Draw(carte)
    largeur = L - 2 * MARGE

    # L'image et l'étiquette
    haut = 490
    try:
        entete = Image.open(image_entete).convert("RGB")
        r = max(L / entete.width, haut / entete.height)
        entete = entete.resize((round(entete.width * r), round(entete.height * r)), Image.LANCZOS)
        g, t = (entete.width - L) // 2, (entete.height - haut) // 2
        carte.paste(entete.crop((g, t, g + L, t + haut)), (0, 0))
    except OSError:
        pass
    eti = _police("BarlowCondensed-ExtraBold.ttf", 34)
    tw = d.textlength("LE MERCATO DE L'IA", font=eti)
    d.rectangle([40, 40, 40 + tw + 32, 40 + 52], fill=JAUNE)
    d.text((56, 66), "LE MERCATO DE L'IA", font=eti, fill=(17, 17, 17), anchor="lm")

    y = haut + 40
    # « C'est signé. » et le tampon
    titre = _police("BarlowCondensed-ExtraBold.ttf", 128)
    d.text((MARGE, y - 6), "C’EST SIGNÉ.", font=titre, fill=JAUNE)
    tx = MARGE + d.textlength("C’EST SIGNÉ.", font=titre) + 34
    officiel = x.get("annonce") == "entreprise"
    tampon = _tampon("OFFICIEL" if officiel else "PRESSE", ROUGE if officiel else CREME,
                     _police("BarlowCondensed-ExtraBold.ttf", 56), 6, pointilles=not officiel)
    carte.paste(tampon, (int(tx), y + 2), tampon)
    y += 134

    # L'entreprise
    nom = str(x.get("entreprise", "")).upper()
    f_nom = _ajuster(d, nom, "BarlowCondensed-ExtraBold.ttf", 74, largeur, 52)
    for ligne in _lignes(d, nom, f_nom, largeur)[:2]:
        d.text((MARGE, y), ligne, font=f_nom, fill=(255, 255, 255))
        y += int(f_nom.size * 1.02)
    y += 16

    # Le mouvement : « SIGNE AVEC » ou « QUITTE … → »
    f_eti = _police("BarlowCondensed-ExtraBold.ttf", 40)
    f_pour = _police("BarlowCondensed-Bold.ttf", 54)
    quitte = x.get("quitte") or []
    if quitte:
        texte_q = ", ".join(quitte)
        d.text((MARGE, y + 8), "QUITTE", font=f_eti, fill=ROUGE)
        qx = MARGE + d.textlength("QUITTE ", font=f_eti) + 6
        f_q = _police("BarlowCondensed-Bold.ttf", 44)
        d.text((qx, y + 6), texte_q, font=f_q, fill=GRIS)
        lw = d.textlength(texte_q, font=f_q)
        d.line([(qx, y + 6 + f_q.size * 0.62), (qx + lw, y + 6 + f_q.size * 0.62)], fill=GRIS, width=4)
        y += 64
        etiquette = "POUR"
    else:
        etiquette = "SIGNE AVEC"
    d.text((MARGE, y + 10), etiquette, font=f_eti, fill=ROUGE)
    # Sur la carte, la destination en court : « Claude (Anthropic, États-Unis) » → « Claude (Anthropic) »
    pour = re.sub(r"\(([^,()]+),[^()]*\)", r"(\1)", str(x.get("pour", "")))
    px = MARGE + d.textlength(etiquette, font=f_eti) + 24
    f_pour = _ajuster(d, pour, "BarlowCondensed-Bold.ttf", 54, L - MARGE - px - 36, 36)
    pw = d.textlength(pour, font=f_pour)
    d.rectangle([px, y, px + pw + 36, y + f_pour.size + 14], fill=JAUNE)
    d.text((px + 18, y + 4), pour, font=f_pour, fill=(17, 17, 17))
    y += f_pour.size + 14 + 26
    if x.get("en_partie"):
        f_p = _police("Barlow-Medium.ttf", 24)
        d.rectangle([MARGE, y - 8, MARGE + d.textlength("EN PARTIE", font=f_p) + 20, y + 26], outline=CREME, width=2)
        d.text((MARGE + 10, y - 6), "EN PARTIE", font=f_p, fill=CREME)
        y += 44

    # La phrase de contexte
    f_txt = _police("Barlow-Regular.ttf", 34)
    for ligne in _lignes(d, str(x.get("comment", "")).rstrip(".") + ".", f_txt, largeur)[:3]:
        d.text((MARGE, y), ligne, font=f_txt, fill=CREME)
        y += 45
    y += 22

    # L'enjeu (facultatif)
    if x.get("enjeu"):
        f_e = _police("Barlow-Regular.ttf", 29)
        f_lab = _police("BarlowCondensed-ExtraBold.ttf", 38)
        lab_w = d.textlength("L'ENJEU", font=f_lab) + 28
        texte_x = MARGE + 28 + lab_w + 30
        lignes = _lignes(d, x["enjeu"], f_e, L - MARGE - 28 - texte_x)[:3]
        bh = max(100, len(lignes) * 39 + 48)
        if y + bh < H - 200:
            d.rounded_rectangle([MARGE, y, L - MARGE, y + bh], radius=22, outline=JAUNE, width=3)
            d.rectangle([MARGE + 28, y + bh / 2 - 26, MARGE + 28 + lab_w, y + bh / 2 + 26], fill=JAUNE)
            d.text((MARGE + 42, y + bh / 2), "L'ENJEU", font=f_lab, fill=(17, 17, 17), anchor="lm")
            d.line([(texte_x - 16, y + 26), (texte_x - 16, y + bh - 26)], fill=JAUNE, width=2)
            ty = y + (bh - len(lignes) * 39) / 2
            for ligne in lignes:
                d.text((texte_x, ty), ligne, font=f_e, fill=CREME)
                ty += 39

    # Le pied : la source et le logo
    pied = H - 150
    d.line([(MARGE, pied), (L - MARGE, pied)], fill=TRAIT, width=2)
    src = x.get("source") or {}
    date_src = str(src.get("date") or "")
    mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_src):
        a, m, j = date_src.split("-")
        date_src = f"{int(j)} {mois[int(m) - 1]} {a}"
    # L'icône de lien (deux maillons penchés), dessinée
    icone = Image.new("RGBA", (60, 60), (0, 0, 0, 0))
    di = ImageDraw.Draw(icone)
    di.rounded_rectangle([12, 6, 30, 32], radius=9, outline=GRIS, width=4)
    di.rounded_rectangle([12, 26, 30, 52], radius=9, outline=GRIS, width=4)
    icone = icone.rotate(-45, resample=Image.BICUBIC)
    carte.paste(icone, (MARGE - 12, pied + 18), icone)
    tx = MARGE + 50
    f_src = _police("Barlow-Regular.ttf", 26)
    d.text((tx, pied + 34), f"Source : {src.get('media', '')}{', ' + date_src if date_src else ''}", font=f_src, fill=GRIS)
    f_lien = _police("Barlow-Medium.ttf", 27)
    d.text((tx, pied + 76), LIEN, font=f_lien, fill=CREME)
    ax = tx + d.textlength(LIEN, font=f_lien) + 14          # la petite flèche ↗, dessinée (absente de la police)
    d.line([(ax, pied + 106), (ax + 16, pied + 90)], fill=JAUNE, width=3)
    d.line([(ax + 4, pied + 89), (ax + 17, pied + 89), (ax + 17, pied + 102)], fill=JAUNE, width=3)
    d.line([(tx, pied + 120), (ax + 20, pied + 120)], fill=JAUNE, width=4)
    f_logo = _police("RobotoSlab.ttf", 76, 900)
    lw = d.textlength("IRIS", font=f_logo)
    lx = L - MARGE - lw - 26
    d.line([(lx - 34, pied + 28), (lx - 34, pied + 122)], fill=TRAIT, width=2)
    d.text((lx, pied + 30), "IRIS", font=f_logo, fill=CREME)
    d.ellipse([lx + lw + 6, pied + 38, lx + lw + 25, pied + 57], fill=JAUNE)
    return carte


def produire(racine: Path = RACINE, toutes: bool = False) -> list[str]:
    donnees = json.loads((racine / "iris" / "mercato.json").read_text(encoding="utf-8"))
    dossier = racine / "iris" / "cartes"
    dossier.mkdir(parents=True, exist_ok=True)
    faites = []
    for x in donnees.get("transferts") or []:
        cible = dossier / f"{identifiant(x)}.jpg"
        if cible.exists() and not toutes:
            continue
        dessiner(x, racine / "iris" / "assets" / "photos" / "mercato.jpg").save(cible, quality=88, optimize=True)
        faites.append(cible.name)
    return faites


if __name__ == "__main__":
    for nom in produire(toutes="--toutes" in sys.argv):
        print("  carte :", nom)
