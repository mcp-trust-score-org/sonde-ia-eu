"""Rédaction : les propositions d'articles du jour, selon redaction/CHARTE.md.

    python -m sonde rediger         # écrit redaction/propositions/AAAA-MM-JJ.md et .json

Chaque jour, selon le rythme de config/redaction.yaml :
  - À la une : le meilleur événement croisé avec les mesures de la sonde (un par jour),
    et le bilan de la semaine le lundi ;
  - Tous connectés : un sujet tiré des tendances (Wikipédia, presse grand public),
    retenu seulement s'il passe le test du « Et vous ? » ;
  - Le Détour : une sélection de liens vers les médias de référence.

Le rédacteur est un modèle d'IA (par défaut Mistral, clé déjà dans les secrets) qui reçoit
la charte en consigne et UNIQUEMENT les faits collectés. Sans clé, ou s'il échoue, GitHub écrit
une fiche (faits, sources, structure) à rédiger à la main.

Chaque brouillon passe les contrôles de la charte ; les écarts sont signalés, jamais corrigés
en silence. Rien n'est publié sur le site : tout part en relecture.
"""

from __future__ import annotations

import json
import os
import re
import time
import traceback
from html.parser import HTMLParser
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

PARIS = ZoneInfo("Europe/Paris")
NIVEAUX = {"confirme": 4, "probable": 3, "possible": 2, "non_concerne": 1}
TAGS_INTERNES = {"confirme": "Confirmé", "probable": "Probable", "possible": "Possible",
                 "non_concerne": "Aucune anomalie", "non_mesure": "Non mesuré"}
TYPES_EXTERIEURS = {"meteo", "energie", "reseau", "materiel", "refroidissement", "cyberattaque"}
CATEGORIE_PAR_TYPE = {"meteo": ("Météo", "meteo"), "energie": ("Énergie", "energie"), "reseau": ("Réseau", "reseau"),
                      "materiel": ("Infrastructure", "cloud"), "refroidissement": ("Infrastructure", "cloud"),
                      "cyberattaque": ("Cybersécurité", "cyberattaque"), "incident_fournisseur": ("IA", "ia"),
                      "incident_amont": ("Réseau", "reseau"), "logiciel": ("Logiciel", "logiciel")}
CHAMPS_ARTICLE = ("tag", "title", "chapo", "fait", "consequence", "lien")


# ---------------------------------------------------------------- utilitaires

def _lire(chemin: Path, defaut):
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return defaut


def _date(texte):
    if not texte:
        return None
    try:
        d = datetime.fromisoformat(str(texte).replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _paris(d: datetime | None) -> str | None:
    """« vendredi 20 novembre, 7 h 53 » : l'heure de Paris, écrite comme dans un article."""
    if not d:
        return None
    jours = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
    mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre",
            "octobre", "novembre", "décembre"]
    p = d.astimezone(PARIS)
    return f"{jours[p.weekday()]} {p.day} {mois[p.month - 1]}, {p.hour} h {p.minute:02d}"


def _texte(article: dict) -> str:
    morceaux = [article.get("chapo") or ""]
    for champ in ("fait", "consequence", "lien"):
        morceaux += article.get(champ) or []
    return " ".join(morceaux)


# ---------------------------------------------------------------- lecture des articles

class _Extracteur(HTMLParser):
    """Garde le texte des paragraphes d'une page, sans menus, pieds de page ni scripts."""
    IGNORES = {"script", "style", "nav", "footer", "aside", "header", "form", "noscript", "figure"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.pile, self.dans_p, self.dans_article = [], 0, 0
        self.p_article, self.p_tous, self.courant = [], [], []

    def handle_starttag(self, tag, attrs):
        if tag in ("br", "img", "meta", "link", "hr", "input"):
            return
        self.pile.append(tag)
        if tag == "article":
            self.dans_article += 1
        if tag == "p":
            self.dans_p += 1
            self.courant = []

    def handle_endtag(self, tag):
        if tag not in self.pile:
            return
        while self.pile:
            t = self.pile.pop()
            if t == "article":
                self.dans_article -= 1
            if t == "p" and self.dans_p:
                self.dans_p -= 1
                texte = re.sub(r"\s+", " ", "".join(self.courant)).strip()
                if len(texte) >= 60:
                    (self.p_article if self.dans_article else self.p_tous).append(texte)
            if t == tag:
                break

    def handle_data(self, data):
        if self.dans_p and not any(t in self.IGNORES for t in self.pile):
            self.courant.append(data)


def lire_article(client, url: str, conf: dict) -> dict:
    """Le texte d'un article de presse, pour que le rédacteur en tire les faits (jamais pour le recopier)."""
    if not url:
        return {"url": url, "etat": "pas de lien"}
    try:
        r = client.get(url, timeout=conf.get("delai_s", 15), follow_redirects=True,
                       headers={"User-Agent": conf.get("agent", "Mozilla/5.0 (compatible; IrisRedaction/1.0)")})
    except httpx.HTTPError as e:
        return {"url": url, "etat": f"injoignable ({type(e).__name__})"}
    if r.status_code != 200:
        return {"url": url, "etat": f"illisible (HTTP {r.status_code})"}
    if "html" not in r.headers.get("content-type", "html"):
        return {"url": url, "etat": "pas une page web"}
    ex = _Extracteur()
    try:
        ex.feed(r.text)
    except Exception:   # page mal formée : on garde ce qui a été lu
        pass
    paragraphes = ex.p_article or ex.p_tous
    texte = "\n".join(paragraphes)[: conf.get("max_caracteres", 6000)]
    if len(texte) < conf.get("min_caracteres", 400):
        return {"url": url, "etat": "texte trop court (article payant ou page protégée ?)", "texte": texte or None}
    return {"url": url, "etat": "lu", "texte": texte}


def _mots(texte: str) -> list[str]:
    import unicodedata
    t = unicodedata.normalize("NFKD", texte or "").lower()
    return re.findall(r"[a-z0-9]+", "".join(c for c in t if not unicodedata.combining(c)))


def passages_recopies(article: dict, textes: list[str], n: int = 12) -> list[str]:
    """Suites de n mots identiques entre le brouillon et les articles lus : signe d'un passage recopié."""
    sources = set()
    for t in textes:
        m = _mots(t)
        sources |= {" ".join(m[i:i + n]) for i in range(len(m) - n + 1)}
    if not sources:
        return []
    m = _mots(_texte(article) + " " + " ".join(article.get("reflexes") or []))
    trouves, i = [], 0
    while i <= len(m) - n:
        g = " ".join(m[i:i + n])
        if g in sources:
            trouves.append(g)
            i += n
        else:
            i += 1
    return trouves


def _lire_sources(client, sources: list[dict], conf: dict) -> list[dict]:
    lus = []
    for src in sources[: conf.get("max_articles", 3)]:
        a = lire_article(client, src.get("url"), conf)
        lus.append({**{k: v for k, v in src.items() if k in ("titre", "label", "media", "url")}, **a})
    return lus


def _alertes_lecture(lus: list[dict], article: dict) -> list[str]:
    alertes = [f"Article non lu ({a['etat']}) : {a.get('url')} — vérifier à la main ce qui en vient."
               for a in lus if a.get("etat") != "lu"]
    if lus and not [a for a in lus if a.get("etat") == "lu"]:
        alertes.append("Aucun article n'a pu être lu : le brouillon ne repose que sur des titres.")
    copies = passages_recopies(article, [a.get("texte") or "" for a in lus])
    if copies:
        alertes.append(f"{len(copies)} passage(s) recopié(s) d'un article (12 mots identiques ou plus) : à reformuler. "
                       f"Exemple : « {copies[0]} »")
    return alertes


# ---------------------------------------------------------------- contrôles de la charte

def controler(article: dict, rubrique: str) -> list[str]:
    """Écarts à la charte (section 5). Signalés en relecture, jamais corrigés en silence."""
    alertes = []
    titre = article.get("title") or ""
    if titre.count("<mark>") != 1:
        alertes.append(f"Le titre doit avoir un seul élément surligné (<mark>) : il en a {titre.count('<mark>')}.")
    titre_plat = re.sub(r"<[^>]+>", " ", titre).lower()
    if rubrique == "une" and re.search(r"\b(vous|votre|vos)\b", titre_plat):
        alertes.append("À la une : le titre ne doit pas interpeller le lecteur (pas de « vous »).")
    if len(re.sub(r"\s+", " ", titre_plat).strip()) > 90:
        alertes.append("Titre long (plus de 90 caractères) : deux phrases courtes.")
    corps = _texte(article)
    if "!" in titre + corps:
        alertes.append("Point d'exclamation : à retirer.")
    derniere = ((article.get("lien") or [""])[-1] or "").strip()
    if not derniere.endswith("?"):
        alertes.append("Le texte doit se terminer par une question au lecteur.")
    chiffres = re.findall(r"\d+(?:[.,]\d+)?", re.sub(r"\b(19|20)\d{2}\b", "", corps))
    if len(chiffres) > 3:
        alertes.append(f"Trop de chiffres dans le texte ({len(chiffres)}) : en garder 3 au plus, le détail va dans l'encadré Premium.")
    if not [s for s in article.get("sources") or [] if s.get("url")]:
        alertes.append("Aucune source avec un lien.")
    if rubrique == "tous_connectes":
        if len(article.get("reflexes") or []) != 3:
            alertes.append("Tous connectés : il faut exactement 3 bons réflexes.")
        if re.search(r"\bvos fournisseurs\b", corps.lower()):
            alertes.append("Tous connectés : ne pas parler de « vos fournisseurs ».")
    for champ in CHAMPS_ARTICLE:
        if not article.get(champ):
            alertes.append(f"Champ manquant : {champ}.")
    if "[À VÉRIFIER" in json.dumps(article, ensure_ascii=False).upper():
        alertes.append("Le brouillon contient des points [À VÉRIFIER] : à compléter avant publication.")
    return alertes


# ---------------------------------------------------------------- le rédacteur (modèle d'IA)

class Redacteur:
    """Appelle un modèle compatible OpenAI avec la charte en consigne.

    Plusieurs services sont essayés dans l'ordre de config/redaction.yaml (`services`) :
    ceux qui demandent une clé absente sont sautés ; si un modèle ne répond pas, on passe
    au suivant, puis au service suivant. Le premier qui répond est gardé pour la suite.
    """

    def __init__(self, conf: dict, charte: str, client: httpx.Client, env: dict, attendre=None):
        self.charte, self.client, self.attendre = charte, client, attendre or time.sleep
        self.conf = conf
        services = conf.get("services")
        if not services:   # ancien format : un service principal et un secours
            services = [{k: v for k, v in conf.items() if k in ("base_url", "cle_env", "modele", "modeles", "pause_s")}]
            if conf.get("secours"):
                services.append(conf["secours"])
        self.services = []
        for sv in services:
            cle = env.get(sv["cle_env"]) if sv.get("cle_env") else None
            if cle or sv.get("sans_cle"):
                modeles = list(sv.get("modeles") or [sv.get("modele", "mistral-medium-latest")])
                self.services.append({**sv, "cle": cle, "modeles": modeles, "appels": 0})
        self.essais = [(sv, m) for sv in self.services for m in sv["modeles"]]
        self.modele = self.essais[0][1] if self.essais else None
        self.journal = []                       # chaque appel : service, modèle, résultat (lisible dans le brouillon)
        self.budget_s = conf.get("budget_s", 600)
        self.debut = time.monotonic()
        self.horloge = time.monotonic

    @property
    def actif(self) -> bool:
        return bool(self.essais)

    def charte_pour(self, rubrique: str | None) -> str:
        """Les règles communes et la section de la rubrique : une consigne plus courte."""
        if not rubrique:
            return self.charte
        garde = {"une": "## 2.", "tous_connectes": "## 3.", "detour": "## 4."}[rubrique]
        morceaux = re.split(r"(?m)^(?=## )", self.charte)
        return "".join(m for m in morceaux if not m.startswith("## ") or m.startswith(("## 0.", "## 1.", "## 5.", garde)))

    def ecrire(self, consigne: str, fiche: dict, rubrique: str | None = None) -> dict:
        """Essaie le modèle qui a répondu en dernier, puis les autres dans l'ordre ; garde celui qui répond."""
        erreurs = []
        ordre = sorted(self.essais, key=lambda e: e[1] != self.modele)
        for sv, modele in ordre:
            if self.horloge() - self.debut > self.budget_s:
                erreurs.append(f"temps écoulé ({self.budget_s // 60} min) : arrêt des essais pour aujourd'hui")
                break
            if sv.get("sature"):
                erreurs.append(f"{modele} : {sv.get('nom')} saturé, non réessayé")
                continue
            try:
                rep = self._ecrire(consigne, fiche, modele, sv, rubrique)
                self.modele = modele
                return rep
            except RuntimeError as e:
                erreurs.append(f"{modele} : {e}")
        raise RuntimeError(" ; ".join(erreurs)[:400])

    def _ecrire(self, consigne: str, fiche: dict, modele: str, sv: dict, rubrique: str | None = None) -> dict:
        systeme = (
            "Tu es rédacteur pour Iris, un média français. Tu écris en français, en respectant STRICTEMENT "
            "la charte ci-dessous.\n\nRègle absolue : tu n'utilises QUE les faits fournis dans la fiche. "
            "Tu n'inventes aucun fait, chiffre, date, citation, nom ou source. Si une information te manque "
            "pour raconter l'histoire, écris « [À VÉRIFIER : ce qui manque] » à la place.\n"
            "Les heures de la fiche sont déjà en heure de Paris.\n"
            "Quand la fiche contient le texte d'articles de presse (« texte »), c'est ta source de faits : "
            "tu les reformules entièrement avec tes mots. Tu ne recopies jamais une phrase, ni une suite de plus "
            "de quelques mots ; une citation, si elle est indispensable, fait moins de 15 mots, entre guillemets, "
            "avec le nom du média. Un article marqué non lu ne t'apporte que son titre.\n"
            "Tu réponds uniquement par un objet JSON valide, sans texte autour.\n\n"
            "=== CHARTE ===\n" + self.charte_pour(rubrique)
        )
        if sv.get("max_caracteres_entree"):
            # Certains services gratuits limitent la taille d'une requête : on raccourcit les textes d'articles.
            fiche = alleger(fiche, sv["max_caracteres_entree"] - len(systeme) - len(consigne))
        corps = {"model": modele, "temperature": self.conf.get("temperature", 0.4),
                 "response_format": {"type": "json_object"},
                 "messages": [{"role": "system", "content": systeme},
                              {"role": "user", "content": consigne + "\n\n=== FICHE ===\n" + json.dumps(fiche, ensure_ascii=False, indent=1)}]}
        derniere = None
        refus = 0
        entetes = {**(sv.get("entetes") or {}), **({"Authorization": f"Bearer {sv['cle']}"} if sv.get("cle") else {})}

        def noter(resultat):
            self.journal.append({"service": sv.get("nom") or sv["base_url"], "modele": modele, "rubrique": rubrique,
                                 "resultat": resultat[:160]})
        for essai in range(self.conf.get("essais", 2)):
            if sv["appels"] and sv.get("pause_s"):
                self.attendre(sv["pause_s"])           # services gratuits : quelques requêtes par minute
            sv["appels"] += 1
            try:
                r = self.client.post(f"{sv['base_url'].rstrip('/')}/chat/completions", json=corps,
                                     headers=entetes, timeout=self.conf.get("delai_s", 90))
                if r.status_code == 429:
                    refus += 1
                    noter("HTTP 429 (trop de requêtes)")
                    if refus >= 2:
                        sv["sature"] = True               # inutile d'insister sur ce service aujourd'hui
                if r.status_code == 429 and essai + 1 < self.conf.get("essais", 2) and not sv.get("sature"):
                    # Trop de requêtes : on attend le délai demandé par le service (ou une minute), puis on réessaie.
                    try:
                        delai = float(r.headers.get("retry-after") or sv.get("attente_429_s", 65))
                    except ValueError:
                        delai = sv.get("attente_429_s", 65)
                    self.attendre(min(delai, 120))
                    derniere = "HTTP 429 (trop de requêtes)"
                    continue
                if r.status_code in (400, 422) and "response_format" in corps:
                    corps.pop("response_format")       # modèle qui ne connaît pas le mode JSON : on réessaie sans
                    derniere = f"HTTP {r.status_code}"
                    continue
                if r.status_code >= 400:
                    noter(f"HTTP {r.status_code} {r.text.strip()[:100]}")
                r.raise_for_status()
                try:
                    donnees = r.json()
                except ValueError:
                    detail = f"réponse illisible (HTTP {r.status_code}, {r.headers.get('content-type', '?')}) : {r.text.strip()[:120]!r}"
                    noter(detail)
                    derniere = detail
                    continue
                choix = (donnees.get("choices") or [{}])[0]
                message = choix.get("message") or {}
                texte = message.get("content") or ""
                if isinstance(texte, list):   # certains services renvoient le texte en morceaux
                    texte = "".join(m.get("text", "") for m in texte if isinstance(m, dict))
                if not texte.strip():
                    detail = (f"réponse vide (fin : {choix.get('finish_reason')}, refus : {message.get('refusal')}, "
                              f"début : {json.dumps(donnees, ensure_ascii=False)[:160]})")
                    noter(detail)
                    derniere = detail
                    if "response_format" in corps:
                        corps.pop("response_format")   # on réessaie sans le mode JSON imposé
                    continue
                texte = re.sub(r"^```(?:json)?|```$", "", texte.strip()).strip()
                debut, fin = texte.find("{"), texte.rfind("}")
                try:
                    rep = json.loads(texte[debut:fin + 1] if debut >= 0 else texte)
                except ValueError:
                    detail = f"texte qui n'est pas du JSON : {texte[:120]!r}"
                    noter(detail)
                    derniere = detail
                    continue
                noter("ok")
                return rep
            except (httpx.HTTPError, KeyError, IndexError) as e:
                derniere = f"{type(e).__name__}: {e}"[:200]
                if not isinstance(e, httpx.HTTPStatusError):
                    noter(derniere)
        raise RuntimeError(derniere or "réponse vide")


def alleger(fiche, budget: int):
    """Raccourcit les textes d'articles (puis les listes) jusqu'à tenir dans `budget` caractères."""
    import copy
    f = copy.deepcopy(fiche)
    longs = ("texte", "debut_de_l_article", "resume")

    def taille():
        return len(json.dumps(f, ensure_ascii=False, indent=1))

    def parcourir(x, action):
        if isinstance(x, dict):
            for k, v in x.items():
                if k in longs and isinstance(v, str):
                    x[k] = action(v)
                else:
                    parcourir(v, action)
        elif isinstance(x, list):
            for v in x:
                parcourir(v, action)

    for _ in range(12):
        if taille() <= budget:
            return f
        parcourir(f, lambda t: t[: max(300, int(len(t) * 0.7))] + ("…" if len(t) > 300 else ""))
    def couper_listes(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if isinstance(v, list) and len(v) > 5:
                    x[k] = v[: max(5, int(len(v) * 0.6))]
                couper_listes(x[k])
        elif isinstance(x, list):
            for v in x:
                couper_listes(v)
    for _ in range(6):
        if taille() <= budget:
            break
        couper_listes(f)
    return f


FORMAT_ARTICLE = """Réponds avec ce JSON :
{
 "tag": "catégorie, avec le format si besoin (ex. « Réseau », « Bilan · Réseau · semaine 47 »)",
 "title": "deux phrases courtes séparées par <br/>, un seul <mark>…</mark>",
 "chapo": "2 ou 3 phrases",
 "fait": ["paragraphe court", "phrase de recul"],
 "consequence": ["paragraphe court", "phrase de recul"],
 "lien": ["paragraphe", "question finale au lecteur, terminée par ?"],
 "une_mini": {"fait": "une ligne", "consequence": "une ligne", "dependance": "une ligne"},
 "sources": [{"label": "Média ou organisme : de quoi il s'agit", "url": "…"}],
 "a_verifier": ["ce que la rédaction doit vérifier avant publication"]%s
}"""


# ---------------------------------------------------------------- À la une

FAMILLES_DE_MODELES = r"(deepseek|glm|qwen|llama|mistral|mixtral|codestral|devstral|magistral|pixtral|gpt|gemma|phi|kimi|bge|whisper|flux|minimax|claude|gemini)"


def modele_non_suivi(titre: str, suivis: list[str]) -> str | None:
    """Le modèle cité par un incident, s'il n'est pas l'un de ceux que la sonde mesure (sinon None).
    Un incident sur « DeepSeek v4.1 Flash » ne dit rien des modèles mesurés : « Aucune anomalie » serait trompeur."""
    plat = " ".join(_mots(titre))
    cite = re.search(FAMILLES_DE_MODELES + r"[\w .\-]*", titre, re.I)
    if not cite:
        return None
    for nom in suivis:
        mots = [m for m in _mots(nom) if len(m) > 1][:2]
        if mots and all(m in plat.split() for m in mots):
            return None
    return " ".join(cite.group(0).split()[:3])


def candidats_une(actus: dict, croisement: dict, maintenant: datetime, deja: set, suivis: list[str] | None = None) -> list[dict]:
    """Événements de la semaine, classés : niveau de corrélation, cause extérieure, reprise presse, fraîcheur."""
    par_id: dict[str, dict] = {}
    for e in actus.get("evenements") or []:
        par_id[e["id"]] = {"evenement": e, "impacts": []}
    for i in croisement.get("impacts") or []:
        ev = i["evenement"]
        par_id.setdefault(ev["id"], {"evenement": {**ev, "fournisseurs": []}, "impacts": []})["impacts"].append(i)
    candidats = []
    for eid, c in par_id.items():
        if eid in deja or c["evenement"].get("exemple"):
            continue
        debut = _date(c["evenement"].get("debut"))
        if not debut or debut < maintenant - timedelta(days=7) or debut > maintenant:
            continue
        niveaux = [i["correlation"]["niveau"] for i in c["impacts"]]
        meilleur = max(niveaux, key=lambda n: NIVEAUX.get(n, 0)) if niveaux else "non_mesure"
        e = c["evenement"]
        hors_sonde = modele_non_suivi(e.get("titre") or "", suivis or [])
        if hors_sonde and meilleur == "non_concerne":
            meilleur = "non_mesure"          # « aucune anomalie » ne vaut que pour les modèles mesurés
            c["modele_non_suivi"] = hors_sonde
        score = NIVEAUX.get(meilleur, 0) * 10
        score += 6 if e.get("type") in TYPES_EXTERIEURS else 0
        score += min(4, ((e.get("presse") or {}).get("nb_medias") or 0))
        score += {"major": 3, "critical": 4, "rouge": 4, "orange": 2, "repris": 2}.get(e.get("gravite") or "", 0)
        score -= (maintenant - debut).total_seconds() / 86400 * 2   # 2 points de moins par jour d'ancienneté
        candidats.append({"id": eid, "score": round(score, 1), "niveau": meilleur, **c})
    return sorted(candidats, key=lambda c: c["score"], reverse=True)


def fiche_une(c: dict) -> dict:
    """Les faits d'un événement, et seulement eux, à donner au rédacteur."""
    e = c["evenement"]
    debut, fin = _date(e.get("debut")), _date(e.get("fin"))
    mesures = []
    for i in c["impacts"]:
        m = i["mesures"]
        mesures.append({
            "fournisseur": i["evenement"]["fournisseur"],
            "ce_que_la_sonde_a_vu": i["correlation"]["texte_propose"],
            "anomalies": [{"heure": _paris(_date(a["heure"])), "detail": a["detail"]} for a in m.get("anomalies") or []],
            "nombre_de_mesures_pendant_l_evenement": m.get("mesures_dans_la_fenetre"),
            "incident_officiel": bool(m.get("incident_officiel")),
        })
    if c.get("modele_non_suivi"):
        for m in mesures:
            m["ce_que_la_sonde_a_vu"] = (f"La sonde ne mesure pas le modèle {c['modele_non_suivi']} : "
                                         "impossible de dire si des utilisateurs ont été touchés.")
    return {
        "evenement": e.get("titre"), "type": e.get("type"),
        "debut": _paris(debut), "fin": _paris(fin) if fin and fin > (debut or fin) else None,
        "fournisseurs_concernes": sorted({i["evenement"]["fournisseur"] for i in c["impacts"]}) or e.get("fournisseurs"),
        "pourquoi_ce_fournisseur": e.get("pourquoi"),
        "mesures_de_la_sonde": mesures or "aucune mesure de la sonde pendant l'événement",
        "presse": e.get("presse"),
        "sources": [{"label": s.get("titre"), "url": s.get("url")} for s in e.get("sources") or [] if s.get("url")],
    }


def fiche_bilan(actus: dict, croisement: dict, maintenant: datetime) -> dict:
    """Les chiffres de la semaine écoulée : le bilan du lundi."""
    depuis = maintenant - timedelta(days=7)
    evts = [e for e in actus.get("evenements") or [] if (_date(e.get("debut")) or depuis) >= depuis]
    par_acteur, par_type = {}, {}
    for e in evts:
        acteur = (e.get("titre") or "").split(" : ")[0] if e.get("source_auto") not in ("meteoalarm", "gdelt") else e.get("source_auto")
        par_acteur[acteur] = par_acteur.get(acteur, 0) + 1
        par_type[e.get("type") or "autre"] = par_type.get(e.get("type") or "autre", 0) + 1
    impacts = [i for i in croisement.get("impacts") or [] if (_date(i["evenement"]["debut"]) or depuis) >= depuis]
    niveaux = {}
    for i in impacts:
        n = i["correlation"]["niveau"]
        niveaux[TAGS_INTERNES.get(n, n)] = niveaux.get(TAGS_INTERNES.get(n, n), 0) + 1
    anomalies = [{"fournisseur": i["evenement"]["fournisseur"], "evenement": i["evenement"]["titre"],
                  "anomalies": [a["detail"] for a in i["mesures"]["anomalies"]]}
                 for i in impacts if i["mesures"]["anomalies"]]
    return {
        "semaine": f"du {_paris(depuis).rsplit(',', 1)[0]} au {_paris(maintenant - timedelta(days=1)).rsplit(',', 1)[0]}",
        "numero_de_semaine": (maintenant - timedelta(days=1)).astimezone(PARIS).isocalendar().week,
        "evenements_collectes": len(evts), "par_acteur": dict(sorted(par_acteur.items(), key=lambda x: -x[1])),
        "par_type": par_type, "croisements_par_niveau": niveaux, "anomalies_mesurees": anomalies,
        "non_couverts": len(croisement.get("non_couverts") or []),
        "evenements_ecartes_pages_de_statut": len(actus.get("ecartes_pages_de_statut") or []),
    }


# ---------------------------------------------------------------- Tous connectés et Détour

def _parle_de(sujet: str, titre: str) -> bool:
    """Le titre parle-t-il du sujet ? Les deux premiers mots significatifs, ou le sigle
    (« Grand Theft Auto VI » → « GTA VI »). Le complément entre parenthèses est ignoré."""
    sujet = re.sub(r"\s*\(.*\)", "", sujet)
    plat = " " + " ".join(_mots(titre)) + " "
    mots = [m for m in _mots(sujet) if len(m) > 3]
    if mots and all(f" {m} " in plat for m in mots[:2]):
        return True
    brut = sujet.split()
    suite = [x for x in brut if re.fullmatch(r"[IVX]+|\d+", x)]
    initiales = [x for x in brut if x not in suite and x[:1].isupper()]
    if len(initiales) >= 2:
        sigle = "".join(x[0] for x in initiales).lower() + "".join(" " + x.lower() for x in suite)
        return f" {sigle} " in plat
    return False


def fiche_tous_connectes(tend: dict, deja: set, n: int = 25) -> dict:
    """Ce qui occupe les gens, avec les titres de presse qui en parlent (seules sources de faits)."""
    presse = tend.get("presse") or []
    sujets = []
    for w in tend.get("wikipedia") or []:
        if w["sujet"].lower() in deja:
            continue
        lies = [p for p in presse if _parle_de(w["sujet"], p["titre"])][:4]
        sujets.append({"sujet": w["sujet"], "langue": w["projet"][:2], "rang_wikipedia": w["rang"], "page": w["url"],
                       "titres_de_presse": [{"titre": p["titre"], "media": p["media"], "url": p["url"]} for p in lies]})
    presse_seule = [{"titre": p["titre"], "media": p["media"], "url": p["url"]} for p in presse[:40]]
    return {"tendances_wikipedia": sujets[:n], "presse_grand_public": presse_seule}


def choisir_detour(tend: dict, deja: set, n: int) -> list[dict]:
    """Les plus récents, en variant les médias (2 par média au plus)."""
    choix, par_media = [], {}
    for a in tend.get("detour") or []:
        if a["url"] in deja or par_media.get(a["media"], 0) >= 2:
            continue
        par_media[a["media"]] = par_media.get(a["media"], 0) + 1
        choix.append(a)
    return choix[: n * 2]


# ---------------------------------------------------------------- production

def _brouillon(redacteur, consigne, fiche, rubrique, format_, extra_format="") -> tuple[dict, str, list]:
    """(article, auteur, alertes). Repli sur une fiche à rédiger si le rédacteur n'est pas disponible."""
    if redacteur and redacteur.actif:
        try:
            art = redacteur.ecrire(consigne + "\n\n" + (FORMAT_ARTICLE % extra_format), fiche, rubrique)
            if art.get("aucun"):
                return art, redacteur.modele, []
            return art, redacteur.modele, controler(art, rubrique)
        except RuntimeError as e:
            return {}, "fiche", [f"Le rédacteur n'a pas répondu ({e}) : fiche à rédiger à la main."]
    return {}, "fiche", ["Pas de rédacteur disponible : fiche à rédiger à la main."]


def _tous_connectes(redacteur, client, tend, deja, tc, jour, images, lecture) -> dict:
    fiche = fiche_tous_connectes(tend, deja.get("tous_connectes", set()))
    if not fiche["tendances_wikipedia"] and not fiche["presse_grand_public"]:
        return {"rubrique": "tous_connectes", "auteur": "fiche", "article": {}, "fiche": fiche,
                "alertes_charte": ["Aucune tendance collectée (lancer « python -m sonde tendances ») : pas de sujet proposé."]}
    if not redacteur.actif:
        return {"rubrique": "tous_connectes", "auteur": "fiche", "article": {}, "fiche": fiche,
                "alertes_charte": ["Pas de rédacteur configuré (clé absente) : choisir un sujet dans la fiche."]}
    # 1) Choisir le sujet
    try:
        choix = redacteur.ecrire(
            "Rubrique : Tous connectés (édition grand public). Parmi les tendances de la fiche, choisis LE sujet "
            "qui passe le test : on peut écrire le « Et vous ? » en une phrase (une dépendance à la technologie "
            "dans la vie de tous les jours). Pas de filtre par thème : pop culture, achats, société, monde. "
            "Il faut au moins un article de presse de la fiche qui en parle. Réponds : {\"sujet\": \"…\", "
            "\"et_vous\": \"la phrase du test\", \"urls\": [\"jusqu'à 3 liens d'articles de la fiche sur ce sujet\"]} "
            "ou {\"aucun\": true, \"raison\": \"…\"}.", fiche, "tous_connectes")
    except RuntimeError as e:
        return {"rubrique": "tous_connectes", "auteur": "fiche", "article": {}, "fiche": fiche,
                "alertes_charte": [f"Le rédacteur n'a pas répondu ({e}) : choisir un sujet dans la fiche."]}
    if choix.get("aucun"):
        return {"rubrique": "tous_connectes", "auteur": redacteur.modele, "article": {}, "fiche": fiche,
                "alertes_charte": [f"Aucun sujet retenu : {choix.get('raison', 'sans raison')}"]}
    connus = {x["url"]: x for x in fiche["presse_grand_public"]}
    for t in fiche["tendances_wikipedia"]:
        connus.update({x["url"]: x for x in t["titres_de_presse"]})
    urls = [u for u in choix.get("urls") or [] if u in connus]   # jamais un lien inventé
    # 2) Lire les articles
    lus = _lire_sources(client, [connus[u] for u in urls], lecture) if lecture.get("actif", True) else \
        [{**connus[u], "etat": "lecture désactivée"} for u in urls]
    fiche_sujet = {"sujet": choix.get("sujet"), "et_vous": choix.get("et_vous"), "articles_de_presse": lus}
    # 3) Écrire
    reflexe = jour.weekday() == tc.get("reflexe_de_la_semaine", 0)
    art, auteur, alertes = _brouillon(redacteur, (
        "Rubrique : Tous connectés (édition grand public). Écris l'article sur ce sujet à partir des articles de "
        "presse de la fiche, reformulés avec tes mots, et cite-les en sources. Le titre peut interpeller le lecteur. "
        "Étape 3 : « Et vous ? ». Ajoute exactement 3 bons réflexes."
        + (" Ajoute aussi le bon réflexe de la semaine (une phrase-titre et une phrase d'explication)." if reflexe else "")),
        fiche_sujet, "tous_connectes", "a_chaud",
        ',\n "sujet": "le sujet",\n "categorie": "jeux-video, musique, cinema, societe, sante, politique, medias, savoir, innovation ou autre",\n "reflexes": ["…", "…", "…"]'
        + (',\n "reflexe_de_la_semaine": {"titre": "…", "texte": "…"}' if reflexe else ""))
    if not urls:
        alertes.append("Le rédacteur n'a indiqué aucun article de la fiche : sujet sans source vérifiable.")
    if art:
        alertes += _alertes_lecture(lus, art)
        if choix.get("sujet"):
            deja.setdefault("tous_connectes", set()).add(choix["sujet"].lower())
    cat = art.get("categorie") or "autre"
    return {"rubrique": "tous_connectes", "format": "a_chaud", "auteur": auteur,
            "image": f"assets/photos/{images.get(cat, images.get('autre', 'innovation.jpg'))}",
            "article": art, "fiche": {**fiche_sujet, "tendances": fiche}, "alertes_charte": alertes}


def _detour(redacteur, client, tend, deja, dt, lecture) -> dict:
    n = dt.get("liens", 6)
    choix = choisir_detour(tend, deja.get("detour", set()), n)
    liens, auteur, alertes = [], "fiche", []
    if choix and lecture.get("actif", True):
        for a in choix:
            lu = lire_article(client, a["url"], lecture)
            a["debut_de_l_article"] = (lu.get("texte") or "")[: lecture.get("detour_caracteres", 1500)] or None
            a["etat_lecture"] = lu["etat"]
    if choix and redacteur.actif:
        try:
            rep = redacteur.ecrire(
                f"Rubrique : Le Détour. Parmi ces articles d'autres médias, choisis-en {n} qui éclairent une "
                "dépendance à la technologie et apprennent quelque chose. Varie les médias et les sujets. "
                "Pour chacun, écris UNE phrase « pourquoi le lire », avec tes mots, d'après le début de l'article "
                "(ou le titre seul s'il n'a pas pu être lu), sans rien inventer. Réponds : {\"liens\": [{\"url\": \"…\", "
                "\"categorie\": \"…\", \"pourquoi\": \"…\"}]}", {"articles": choix}, "detour")
            par_url = {a["url"]: a for a in choix}
            liens = [{**{k: v for k, v in par_url[l["url"]].items() if k != "debut_de_l_article"},
                      "categorie": l.get("categorie"), "pourquoi": l.get("pourquoi")}
                     for l in rep.get("liens") or [] if l.get("url") in par_url][:n]
            auteur = redacteur.modele
        except RuntimeError as e:
            alertes.append(f"Le rédacteur n'a pas répondu ({e}).")
    if not liens:
        liens = [{**{k: v for k, v in a.items() if k != "debut_de_l_article"}, "categorie": None, "pourquoi": None}
                 for a in choix[:n]]
        if not choix:
            alertes.append("Aucun article récent trouvé chez les médias de référence.")
    non_lus = [l for l in liens if l.get("etat_lecture") and l["etat_lecture"] != "lu"]
    if non_lus:
        alertes.append(f"{len(non_lus)} article(s) non lu(s) (payant ou protégé ?) : leur « pourquoi le lire » vient du titre seul.")
    for l in liens:
        if l.get("langue") == "anglais":
            l["mention"] = "(en anglais)"
        if l.get("etat_lecture") and "payant" in l["etat_lecture"]:
            l["mention"] = (l.get("mention", "") + " (payant ?)").strip()
        deja.setdefault("detour", set()).add(l["url"])
    return {"rubrique": "detour", "auteur": auteur, "liens": liens, "alertes_charte": alertes}


class _Liste(list):
    """Une liste qui enregistre les brouillons à chaque ajout."""
    apres_ajout = None

    def append(self, x):
        super().append(x)
        if self.apres_ajout:
            self.apres_ajout()


def rediger(conf: dict, racine: Path, client: httpx.Client | None = None, env: dict | None = None,
            maintenant: datetime | None = None, attendre=None) -> dict:
    env = env if env is not None else os.environ
    maintenant = maintenant or datetime.now(timezone.utc)
    jour = maintenant.astimezone(PARIS)
    rythme = conf.get("rythme") or {}
    images = conf.get("images") or {}
    charte = (racine / "redaction" / "CHARTE.md").read_text(encoding="utf-8")
    actus = _lire(racine / "public" / "actualites.json", {})
    croisement = _lire(racine / "rapports" / "croisement.json", {})
    tend = _lire(racine / "public" / "tendances.json", {})
    chemin_deja = racine / "redaction" / "deja-proposes.json"
    deja_brut = _lire(chemin_deja, {"une": [], "tous_connectes": [], "detour": []})
    deja = {k: set(v) for k, v in deja_brut.items()}

    propre = client is None
    client = client or httpx.Client(timeout=90)
    redacteur = Redacteur(conf.get("redacteur") or {}, charte, client, env, attendre)
    lecture = conf.get("lecture") or {}
    propositions, reserve_une = _Liste(), []
    etat = {"jour": jour, "maintenant": maintenant, "propositions": propositions, "reserve_une": reserve_une,
            "tend": tend, "redacteur": redacteur, "racine": racine, "deja": deja, "chemin_deja": chemin_deja}
    propositions.apres_ajout = lambda: enregistrer(etat, "en_cours")
    enregistrer(etat, "en_cours")

    try:
        # ---- À la une : un sujet par jour
        suivis = []
        try:
            import yaml
            fz = yaml.safe_load((racine / "config" / "fournisseurs.yaml").read_text(encoding="utf-8")) or {}
            suivis = [m.get("nom") or m.get("id") for m in fz.get("modeles") or []]
        except (OSError, ValueError, ImportError):
            pass
        candidats = candidats_une(actus, croisement, maintenant, deja.get("une", set()), suivis)
        for c in candidats[: (rythme.get("une") or {}).get("par_jour", 1)]:
            fiche = fiche_une(c)
            presse = [{"titre": x.get("titre"), "url": x.get("url")} for x in c["evenement"].get("sources") or []
                      if x.get("type") == "presse"]
            lus = _lire_sources(client, presse, lecture) if presse and lecture.get("actif", True) else []
            if lus:
                fiche["articles_de_presse"] = lus
            label, cle_img = CATEGORIE_PAR_TYPE.get(c["evenement"].get("type"), ("Cloud", "cloud"))
            art, auteur, alertes = _brouillon(redacteur, (
                "Rubrique : À la une (édition entreprises). Format : À chaud. Catégorie suggérée : " + label + ".\n"
                "Écris l'article à partir de la fiche. Titre factuel, sans « vous ». Si la sonde n'a rien mesuré, "
                "dis-le honnêtement dans la conséquence. Étape 3 : « La dépendance révélée »."), fiche, "une", "a_chaud")
            if art and lus:
                alertes += _alertes_lecture(lus, art)
            propositions.append({"rubrique": "une", "format": "a_chaud", "evenement_id": c["id"],
                                 "tag_interne": TAGS_INTERNES.get(c["niveau"], c["niveau"]), "score": c["score"],
                                 "auteur": auteur, "image": f"assets/photos/{images.get(cle_img, images.get('autre', 'innovation.jpg'))}",
                                 "article": art, "fiche": fiche, "alertes_charte": alertes})
            deja.setdefault("une", set()).add(c["id"])
        reserve_une[:] = [{"titre": c["evenement"].get("titre"), "tag_interne": TAGS_INTERNES.get(c["niveau"]), "score": c["score"]}
                          for c in candidats[1: 1 + rythme.get("candidats_affiches", 10)]]

        # ---- À la une : le bilan du lundi
        if jour.weekday() == (rythme.get("une") or {}).get("bilan_le", 0):
            fiche = fiche_bilan(actus, croisement, maintenant)
            art, auteur, alertes = _brouillon(redacteur, (
                "Rubrique : À la une (édition entreprises). Format : Bilan de la semaine. "
                "Raconte la semaine comme une histoire, avec UN chiffre fort dans le titre. "
                "Tag au format « Bilan · catégorie · semaine N »."), fiche, "une", "bilan")
            propositions.append({"rubrique": "une", "format": "bilan", "auteur": auteur, "image": "assets/photos/reseau.jpg",
                                 "article": art, "fiche": fiche, "alertes_charte": alertes})

        # ---- Tous connectés : 1) choisir le sujet, 2) lire les articles, 3) écrire
        tc = rythme.get("tous_connectes") or {}
        if jour.weekday() in tc.get("jours", [0, 2, 4, 5]):
            propositions.append(_tous_connectes(redacteur, client, tend, deja, tc, jour, images, lecture))

        # ---- Le Détour
        dt = rythme.get("detour") or {}
        if jour.weekday() in dt.get("jours", [4]):
            propositions.append(_detour(redacteur, client, tend, deja, dt, lecture))
    except Exception as e:   # jamais de passage muet : l'erreur est écrite dans le fichier des brouillons
        etat["erreur"] = f"{type(e).__name__}: {e}\n" + traceback.format_exc()[-1500:]
        print(etat["erreur"])
    finally:
        if propre:
            client.close()

    return enregistrer(etat, "a_relire" if not etat.get("erreur") else "erreur")


def enregistrer(etat: dict, statut: str) -> dict:
    """Écrit les brouillons tels qu'ils sont. Appelé à chaque étape : un passage coupé laisse quand même
    un fichier qui dit où il s'est arrêté."""
    sortie = {"date": etat["jour"].date().isoformat(), "genere_le": etat["maintenant"].isoformat(timespec="seconds"),
              "statut": statut, "propositions": etat["propositions"], "reserve_une": etat["reserve_une"],
              "sources_tendances": etat["tend"].get("sources"), "journal_redacteur": etat["redacteur"].journal}
    if etat.get("erreur"):
        sortie["erreur"] = etat["erreur"]
    dossier = etat["racine"] / "redaction" / "propositions"
    dossier.mkdir(parents=True, exist_ok=True)
    (dossier / f"{sortie['date']}.json").write_text(json.dumps(sortie, ensure_ascii=False, indent=1), encoding="utf-8")
    (dossier / f"{sortie['date']}.md").write_text(en_markdown(sortie), encoding="utf-8")
    etat["chemin_deja"].write_text(json.dumps({k: sorted(v)[-500:] for k, v in etat["deja"].items()}, ensure_ascii=False, indent=1),
                                   encoding="utf-8")
    return sortie


# ---------------------------------------------------------------- lecture humaine

NOMS = {"une": "À la une", "tous_connectes": "Tous connectés", "detour": "Le Détour"}
FORMATS = {"a_chaud": "À chaud", "bilan": "Bilan"}


def en_markdown(s: dict) -> str:
    l = [f"# Propositions du {s['date']}", "",
         "Brouillons préparés par GitHub selon `redaction/CHARTE.md`. **Rien n'est publié** : à relire, retravailler ou écarter.", ""]
    if s.get("statut") == "en_cours":
        l += ["> ⚠ **Passage interrompu** : la rédaction n'est pas allée au bout (temps dépassé ?). "
              "Voici ce qui était prêt.", ""]
    if s.get("erreur"):
        l += ["> ⚠ **Erreur pendant la rédaction** (détail en bas de page).", ""]
    for p in s["propositions"]:
        entete = f"## {NOMS[p['rubrique']]}" + (f" · {FORMATS.get(p.get('format'), '')}" if p.get("format") else "")
        l += [entete, ""]
        meta = [f"Rédigé par : {p['auteur']}"]
        if p.get("tag_interne"):
            meta.append(f"Tag interne : **{p['tag_interne']}** (jamais affiché sur le site)")
        if p.get("image"):
            meta.append(f"Image : `{p['image']}`")
        l += [" · ".join(meta), ""]
        if p.get("alertes_charte"):
            l += ["**À vérifier**", ""] + [f"- ⚠ {a}" for a in p["alertes_charte"]] + [""]
        a = p.get("article") or {}
        if p["rubrique"] == "detour":
            for x in p.get("liens") or []:
                l.append(f"- **{x['media']}** · {x.get('categorie') or '…'} · [{x['titre']}]({x['url']}) {x.get('mention', '')}".rstrip())
                l.append(f"  {x.get('pourquoi') or '_Pourquoi le lire : à écrire._'}")
            l.append("")
            continue
        if a:
            l += [f"*{a.get('tag', '')}*", "", f"### {re.sub(r'<br/?>', ' / ', a.get('title', ''))}", "", a.get("chapo", ""), ""]
            for titre, champ in (("Le fait inattendu", "fait"), ("La conséquence technologique", "consequence"),
                                 ("Et vous ?" if p["rubrique"] == "tous_connectes" else "La dépendance révélée", "lien")):
                l += [f"**{titre}**", ""] + [f"{x}\n" for x in a.get(champ) or []]
            if a.get("reflexes"):
                l += ["**Le bon réflexe**", ""] + [f"{i}. {r}" for i, r in enumerate(a["reflexes"], 1)] + [""]
            if a.get("reflexe_de_la_semaine"):
                r = a["reflexe_de_la_semaine"]
                l += [f"**Bon réflexe de la semaine** : {r.get('titre')} {r.get('texte')}", ""]
            if a.get("une_mini"):
                m = a["une_mini"]
                l += ["**En une** : " + " / ".join(f"{k} : {v}" for k, v in m.items()), ""]
            if a.get("sources"):
                l += ["**Sources**", ""] + [f"- [{x.get('label')}]({x.get('url')})" for x in a["sources"]] + [""]
            if a.get("a_verifier"):
                l += ["**Points à vérifier signalés par le rédacteur**", ""] + [f"- {x}" for x in a["a_verifier"]] + [""]
        l += [f"<details{' open' if p['auteur'] == 'fiche' else ''}><summary>Faits fournis au rédacteur</summary>", "", "```json",
              json.dumps(p.get("fiche"), ensure_ascii=False, indent=1)[:6000], "```", "</details>", ""]
    if s.get("journal_redacteur"):
        l += ["## Journal du rédacteur", "", "| Service | Modèle | Rubrique | Résultat |", "|---|---|---|---|"]
        l += [f"| {j['service']} | {j['modele']} | {j.get('rubrique') or ''} | {j['resultat'].replace('|', '/')} |"
              for j in s["journal_redacteur"]] + [""]
    if s.get("erreur"):
        l += ["## Erreur", "", "```", s["erreur"], "```", ""]
    if s.get("reserve_une"):
        l += ["## En réserve pour À la une", ""] + [f"- {r['titre']} ({r['tag_interne']})" for r in s["reserve_une"]] + [""]
    return "\n".join(l)
