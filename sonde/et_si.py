"""La série « Et si… ? » d'Iris Plus : un brouillon par mois, et la revérification des anciens.

Appelé par `python -m sonde rediger` (voir redaction.py) :
  - le premier lundi du mois, un sujet est choisi dans config/et-si.yaml selon l'actualité,
    puis le rédacteur écrit un brouillon en 5 parties (redaction/CHARTE.md, section 6) ;
  - chaque jour, un sujet proposé il y a plus de six mois est revérifié : ses sources sont relues
    et le rédacteur dit ce qui a changé.

La partie « La vraie question » pose des questions sans y répondre : la série aide à réfléchir,
elle ne donne pas d'avis. Un contrôle signale toute prise de position.
L'état de la série (sujets proposés, dates de vérification) est dans redaction/et-si.json.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .redaction import _alertes_lecture, _lire, _lire_sources, _mots, _date, date_en_toutes_lettres, PARIS

PARTIES = (("et_si", "Et si…"), ("existe_deja", "Ce qui existe déjà"), ("ca_coince", "Là où ça coince"),
           ("vraie_question", "La vraie question"))

# Formules qui tranchent à la place du lecteur : la partie 4 doit seulement poser des questions.
AVIS = re.compile(r"\b(selon nous|à notre avis|nous pensons|nous croyons|nous recommandons|le mieux est|mieux vaut|"
                  r"nous devons|notre point de vue|la bonne réponse|c'est une bonne chose|c'est une mauvaise chose)\b", re.I)
# Dans « La vraie question », même « il faut » tranche : ailleurs, il décrit une limite (« il faut un téléphone récent »).
TRANCHE = re.compile(r"\b(il faut|il faudrait|il ne faut pas|on doit|on devrait)\b", re.I)

FORMAT = """Réponds avec ce JSON :
{
 "tag": "Et si… ?",
 "title": "la question du sujet, éventuellement reformulée, terminée par ?",
 "chapo": "2 phrases : le fait réel de départ, puis la question",
 "et_si": ["paragraphe : le fait réel d'où part la question (panne mesurée ou actualité de la fiche)"],
 "existe_deja": ["paragraphe court", "paragraphe court"],
 "ca_coince": ["une limite concrète par paragraphe : matériel nécessaire, batterie, ce qui repasse par le cloud, ce qui reste une promesse"],
 "vraie_question": ["2 à 4 questions ouvertes, chacune terminée par ?, sans y répondre"],
 "geste": "une chose simple à tester ou à faire",
 "sources": [{"label": "Média ou organisme : de quoi il s'agit", "url": "…"}],
 "a_verifier": ["ce que la rédaction doit vérifier avant publication"]
}"""


def jour_du_et_si(jour: datetime, reglages: dict) -> bool:
    semaine = reglages.get("semaine_du_mois", 1)
    return jour.weekday() == reglages.get("jour", 0) and (jour.day - 1) // 7 + 1 == semaine


def _contient(texte: str, mot: str) -> bool:
    plat, m = " " + " ".join(_mots(texte)) + " ", " ".join(_mots(mot))
    return bool(m) and f" {m} " in plat


def accroches(sujet: dict, tend: dict) -> list[dict]:
    """Articles récents (presse et médias du Détour) qui contiennent un mot-clé du sujet."""
    trouves, vus = [], set()
    for a in (tend.get("detour") or []) + (tend.get("presse") or []):
        texte = f"{a.get('titre', '')} {a.get('resume', '')}"
        if a.get("url") in vus:
            continue
        mots = [m for m in sujet.get("mots_cles") or [] if _contient(texte, m)]
        if mots:
            vus.add(a["url"])
            trouves.append({"titre": a.get("titre"), "media": a.get("media"), "url": a["url"], "date": a.get("date"),
                            "mots_cles": mots})
    return sorted(trouves, key=lambda x: (len(x["mots_cles"]), x.get("date") or ""), reverse=True)


def pannes_mesurees(alertes: list[dict], maintenant: datetime, jours: int = 31) -> list[dict]:
    """Les orages vus par la sonde dans le mois écoulé (heure de Paris)."""
    limite = maintenant - timedelta(days=jours)
    sortie = []
    for a in alertes or []:
        quand = _date(a.get("horodatage"))
        if a.get("type") == "orage" and quand and quand >= limite:
            sortie.append({"fournisseur": a.get("fournisseur"), "quand": quand.astimezone(PARIS).strftime("%d/%m %H h %M"),
                           "texte": a.get("texte")})
    return sortie[-5:]


def choisir(reserve: list[dict], etat: dict, tend: dict, pannes: list[dict],
            prochain: str | None = None) -> tuple[dict | None, list[dict], list[str]]:
    """Le sujet du mois : celui imposé par la rédaction (« prochain »), sinon celui qui a le plus
    d'accroches d'actualité, parmi ceux jamais proposés."""
    libres = [s for s in reserve if s.get("id") not in (etat.get("sujets") or {})]
    if not libres:
        return None, [], ["La réserve de sujets est vide : ajouter des sujets dans config/et-si.yaml."]
    impose = next((s for s in libres if prochain and s.get("id") == prochain), None)
    if impose:
        acc = accroches(impose, tend)
        ok = acc or (impose.get("panne_mesuree") and pannes)
        return impose, acc, [] if ok else ["Aucune accroche d'actualité ce mois-ci : le « Et si… » doit partir "
                                           "d'un fait réel, à trouver avant publication."]
    notes = []
    for rang, s in enumerate(libres):
        acc = accroches(s, tend)
        points = len(acc) + (3 if s.get("panne_mesuree") and pannes else 0)
        notes.append((points, -rang, s, acc))
    points, _, sujet, acc = max(notes, key=lambda n: (n[0], n[1]))
    alertes = [] if points else ["Aucune accroche d'actualité ce mois-ci : le « Et si… » doit partir d'un fait réel, "
                                 "à trouver avant publication."]
    return sujet, acc, alertes


def controler_et_si(art: dict, fiche: dict) -> list[str]:
    alertes = []
    for champ, nom in PARTIES:
        if not [x for x in art.get(champ) or [] if str(x).strip()]:
            alertes.append(f"Partie manquante : {nom}.")
    if not (art.get("geste") or "").strip():
        alertes.append("Partie manquante : Le geste.")
    if not (art.get("title") or "").strip().endswith("?"):
        alertes.append("Le titre doit être une question.")
    questions = [str(x).strip() for x in art.get("vraie_question") or []]
    if any(not q.endswith("?") for q in questions):
        alertes.append("La vraie question : chaque phrase doit être une question, sans réponse.")
    tout = json.dumps({k: v for k, v in art.items() if k not in ("sources", "a_verifier")}, ensure_ascii=False)
    avis = AVIS.search(tout) or TRANCHE.search(" ".join(questions))
    if avis:
        alertes.append(f"Point de vue : la série aide à réfléchir, elle ne tranche pas. Formule à retirer : « {avis.group(0)} ».")
    if "!" in tout:
        alertes.append("Point d'exclamation : à retirer.")
    connues = {s.get("url") for s in fiche.get("sources_de_base") or []} | {a.get("url") for a in fiche.get("accroches") or []}
    sources = [s for s in art.get("sources") or [] if s.get("url")]
    if not sources:
        alertes.append("Aucune source avec un lien.")
    inventees = [s["url"] for s in sources if s["url"] not in connues]
    if inventees:
        alertes.append(f"Source absente de la fiche (lien inventé ?) : {inventees[0]} — à vérifier ou retirer.")
    lues = [s for s in (fiche.get("sources_de_base") or []) + (fiche.get("accroches") or []) if s.get("etat") == "lu"]
    if not lues:
        alertes.append("Aucune source n'a pu être lue : « Ce qui existe déjà » ne repose sur rien de vérifié.")
    if [x for x in art.get("a_verifier") or [] if str(x).strip()]:
        alertes.append("Le rédacteur signale des points à vérifier (liste en bas) : à régler avant publication.")
    if "[À VÉRIFIER" in json.dumps(art, ensure_ascii=False).upper():
        alertes.append("Le brouillon contient des points [À VÉRIFIER] : à compléter avant publication.")
    return alertes


def _lecture_pour(art: dict) -> dict:
    """L'article sous la forme attendue par les contrôles de lecture (passages recopiés)."""
    corps = [x for champ, _ in PARTIES for x in art.get(champ) or []] + [art.get("geste") or ""]
    return {"title": art.get("title"), "chapo": art.get("chapo"), "fait": corps}


def nouveau(redacteur, client, conf_serie: dict, etat: dict, tend: dict, alertes_sonde: list, jour, maintenant, lecture) -> dict:
    reglages = conf_serie.get("reglages") or {}
    pannes = pannes_mesurees(alertes_sonde, maintenant)
    impose = (reglages.get("programme") or {}).get(jour.date().isoformat()) or reglages.get("prochain")
    sujet, acc, alertes = choisir(conf_serie.get("sujets") or [], etat, tend, pannes, impose)
    if not sujet:
        return {"rubrique": "et_si", "auteur": "fiche", "article": {}, "fiche": {}, "alertes_charte": alertes}
    acc = acc[: reglages.get("accroches_max", 4)]
    conf_lecture = {**lecture, "max_articles": 10}
    base = _lire_sources(client, sujet.get("sources_de_base") or [], conf_lecture) if lecture.get("actif", True) else []
    lues = _lire_sources(client, acc, conf_lecture) if acc and lecture.get("actif", True) else acc
    for a, d in zip(lues, acc):
        a["date"] = d.get("date")
    fiche = {"question": sujet["question"], "angle": sujet.get("angle"), "pannes_mesurees_par_la_sonde": pannes,
             "accroches": lues, "sources_de_base": base}
    if not sujet.get("sources_de_base"):
        alertes.append("Ce sujet n'a pas encore de sources de base vérifiées dans config/et-si.yaml : "
                       "« Ce qui existe déjà » ne repose que sur l'actualité du mois.")
    art, auteur = {}, "fiche"
    if redacteur and redacteur.actif:
        try:
            art = redacteur.ecrire(
                f"Nous sommes le {date_en_toutes_lettres(jour)}. Rubrique : Et si… ? (Iris Plus), un sujet par mois "
                "pour réfléchir aux limites de la technologie. Écris l'article en 5 parties, à partir de la fiche "
                "seulement : 1) Et si… : pars d'un fait réel de la fiche (une panne mesurée par la sonde ou un article "
                "d'actualité) ; 2) Ce qui existe déjà : les faits des sources lues ; 3) Là où ça coince : les limites "
                "concrètes ; 4) La vraie question : 2 à 4 questions ouvertes sur ce que ça change pour nous, ce qu'on y "
                "perd ou y gagne. Tu ne réponds PAS à ces questions et tu ne donnes AUCUN avis, ni « il faut », ni "
                "« selon nous » : le lecteur réfléchit seul. 5) Le geste : une chose simple à tester. Ton calme, phrases "
                "courtes, pas de point d'exclamation, pas de promesse. Chaque fait vient d'une source de la fiche, "
                "reformulée avec tes mots ; une source non lue n'apporte que son titre.\n\n" + FORMAT,
                fiche, "et_si")
            auteur = redacteur.modele
            alertes += controler_et_si(art, fiche)
            alertes += [a for a in _alertes_lecture(lues + base, _lecture_pour(art))
                        if not a.startswith("Ligne éditoriale")]
        except RuntimeError as e:
            alertes.append(f"Le rédacteur n'a pas répondu ({e}) : fiche à rédiger à la main.")
    else:
        alertes.append("Pas de rédacteur disponible : fiche à rédiger à la main.")
    etat.setdefault("sujets", {})[sujet["id"]] = {
        "question": sujet["question"], "propose_le": jour.date().isoformat(), "verifie_le": jour.date().isoformat(),
        "sources": [s.get("url") for s in (art.get("sources") or []) if s.get("url")] or
                   [s["url"] for s in sujet.get("sources_de_base") or []],
        "article": art}
    return {"rubrique": "et_si", "sujet": sujet["id"], "auteur": auteur, "article": art, "fiche": fiche,
            "alertes_charte": alertes}


def a_reverifier(etat: dict, jour, apres_jours: int) -> str | None:
    """Le sujet le plus anciennement vérifié, s'il l'a été il y a plus de `apres_jours` jours."""
    candidats = []
    for sid, s in (etat.get("sujets") or {}).items():
        try:
            quand = datetime.fromisoformat(s.get("verifie_le") or s.get("propose_le")).date()
        except (TypeError, ValueError):
            continue
        if (jour.date() - quand).days >= apres_jours:
            candidats.append((quand, sid))
    return min(candidats)[1] if candidats else None


def reverifier(redacteur, client, conf_serie: dict, etat: dict, tend: dict, jour, lecture) -> dict | None:
    sid = a_reverifier(etat, jour, (conf_serie.get("reglages") or {}).get("reverifier_apres_jours", 182))
    if not sid:
        return None
    s = etat["sujets"][sid]
    sujet = next((x for x in conf_serie.get("sujets") or [] if x.get("id") == sid), {"id": sid, "mots_cles": []})
    conf_lecture = {**lecture, "max_articles": 10}
    relues = _lire_sources(client, [{"url": u} for u in s.get("sources") or []], conf_lecture) if lecture.get("actif", True) else []
    acc = _lire_sources(client, accroches(sujet, tend)[:3], conf_lecture) if lecture.get("actif", True) else []
    fiche = {"question": s.get("question"), "propose_le": s.get("propose_le"), "article_d_origine": s.get("article"),
             "sources_relues": relues, "actualite_recente": acc}
    alertes = [f"Source devenue illisible ({a['etat']}) : {a['url']} — l'article d'origine s'appuie peut-être sur une page disparue."
               for a in relues if a.get("etat") != "lu"]
    rep, auteur = {}, "fiche"
    if redacteur and redacteur.actif:
        try:
            rep = redacteur.ecrire(
                f"Nous sommes le {date_en_toutes_lettres(jour)}. Rubrique : Et si… ? (Iris Plus), revérification. "
                f"L'article « {s.get('question')} » a été préparé le {s.get('propose_le')}. Compare ses faits "
                "(« article_d_origine ») avec les sources relues aujourd'hui et l'actualité récente de la fiche. "
                "Ne garde que des changements prouvés par la fiche, sans avis. Réponds : {\"change\": true ou false, "
                "\"ce_qui_a_change\": [\"une phrase par changement, avec sa source\"], \"faits_a_retirer\": "
                "[\"les phrases de l'article d'origine qui ne sont plus vraies\"], \"sources\": [{\"label\": \"…\", "
                "\"url\": \"…\"}]}", fiche, "et_si")
            auteur = redacteur.modele
            connues = {a.get("url") for a in relues + acc}
            inventees = [x["url"] for x in rep.get("sources") or [] if x.get("url") and x["url"] not in connues]
            if inventees:
                alertes.append(f"Source absente de la fiche (lien inventé ?) : {inventees[0]}")
        except RuntimeError as e:
            alertes.append(f"Le rédacteur n'a pas répondu ({e}) : relire les sources à la main.")
    s["verifie_le"] = jour.date().isoformat()
    return {"rubrique": "et_si_verif", "sujet": sid, "auteur": auteur, "article": rep, "fiche": fiche,
            "alertes_charte": alertes}


def preparer(redacteur, client, racine: Path, tend: dict, jour, maintenant, lecture) -> list[dict]:
    """Les propositions du jour pour la série (souvent aucune)."""
    try:
        import yaml
        conf_serie = yaml.safe_load((racine / "config" / "et-si.yaml").read_text(encoding="utf-8")) or {}
    except (OSError, ValueError, ImportError):
        return []
    chemin = racine / "redaction" / "et-si.json"
    etat = _lire(chemin, {"sujets": {}})
    sortie = []
    if jour_du_et_si(jour, conf_serie.get("reglages") or {}):
        alertes_sonde = _lire(racine / "iris" / "donnees" / "alertes.json", [])
        sortie.append(nouveau(redacteur, client, conf_serie, etat, tend, alertes_sonde, jour, maintenant, lecture))
    verif = reverifier(redacteur, client, conf_serie, etat, tend, jour, lecture)
    if verif:
        sortie.append(verif)
    if sortie:
        chemin.write_text(json.dumps(etat, ensure_ascii=False, indent=1), encoding="utf-8")
    return sortie


def en_markdown(p: dict) -> list[str]:
    a = p.get("article") or {}
    l = []
    if p["rubrique"] == "et_si_verif":
        if a:
            l += ["**Ça a changé**" if a.get("change") else "**Rien de prouvé n'a changé** : l'article peut rester tel quel.", ""]
            if a.get("ce_qui_a_change"):
                l += ["**Ce qui a changé depuis** (encadré à ajouter)", ""] + [f"- {x}" for x in a["ce_qui_a_change"]] + [""]
            if a.get("faits_a_retirer"):
                l += ["**Phrases qui ne sont plus vraies**", ""] + [f"- {x}" for x in a["faits_a_retirer"]] + [""]
            if a.get("sources"):
                l += ["**Sources**", ""] + [f"- [{x.get('label')}]({x.get('url')})" for x in a["sources"]] + [""]
        return l
    if not a:
        return l
    l += [f"*{a.get('tag', 'Et si… ?')}*", "", f"### {a.get('title', '')}", "", a.get("chapo", ""), ""]
    for champ, nom in PARTIES:
        l += [f"**{nom}**", ""] + [f"{x}\n" for x in a.get(champ) or []]
    l += ["**Le geste**", "", a.get("geste") or "", ""]
    if a.get("sources"):
        l += ["**Sources**", ""] + [f"- [{x.get('label')}]({x.get('url')})" for x in a["sources"]] + [""]
    if a.get("a_verifier"):
        l += ["**Points à vérifier signalés par le rédacteur**", ""] + [f"- {x}" for x in a["a_verifier"]] + [""]
    return l
