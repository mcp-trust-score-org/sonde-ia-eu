"""Publication d'un brouillon validé sur le site (iris/publies.json)."""

import json
from pathlib import Path

import pytest

from sonde.publication import RefusPublication, publier, retirer
from tests.test_redaction import ARTICLE_TC, ARTICLE_UNE


def _brouillons(tmp_path: Path, propositions: list) -> Path:
    d = tmp_path / "redaction" / "propositions"
    d.mkdir(parents=True)
    (d / "2026-11-22.json").write_text(json.dumps({"date": "2026-11-22", "propositions": propositions}, ensure_ascii=False))
    return tmp_path


UNE = {"rubrique": "une", "tag_interne": "Confirmé", "image": "assets/photos/ia.jpg", "article": ARTICLE_UNE,
       "fiche": {"fournisseurs_concernes": ["OVHcloud"], "debut": "vendredi 20 novembre, 7 h 53",
                 "mesures_de_la_sonde": [{"ce_que_la_sonde_a_vu": "Ralentissement mesuré à 9 h"}]}}


def test_publier_une_et_tous_connectes(tmp_path):
    r = _brouillons(tmp_path, [UNE, {"rubrique": "tous_connectes", "image": "assets/photos/jeux-video.jpg", "article": ARTICLE_TC}])
    publier(r, "À la une", "2026-11-22")
    publier(r, "Tous connectés", "2026-11-22")
    pub = json.loads((r / "iris" / "publies.json").read_text())
    une = pub["une"][0]
    assert une["title"] == ARTICLE_UNE["title"] and une["impact"]["level"] == "red"
    assert "Confirmé" not in json.dumps(pub, ensure_ascii=False)          # le tag interne n'est jamais publié
    assert pub["tous_connectes"][0]["audience"] == "public" and len(pub["tous_connectes"][0]["reflexes"]) == 3
    props = json.loads((r / "redaction" / "propositions" / "2026-11-22.json").read_text())
    assert props["propositions"][0]["statut"] == "publie"
    publier(r, "une", "2026-11-22")                                       # republier ne crée pas de doublon
    assert len(json.loads((r / "iris" / "publies.json").read_text())["une"]) == 1


def test_garde_fous(tmp_path):
    a_verifier = {**UNE, "article": {**ARTICLE_UNE, "chapo": "Le service [À VÉRIFIER : nom du modèle] a ralenti."}}
    r = _brouillons(tmp_path, [{"rubrique": "une", "article": {}}, a_verifier,
                               {"rubrique": "detour", "liens": [{"media": "Next", "titre": "T", "url": "https://x"}]}])
    with pytest.raises(RefusPublication, match="pas été rédigé"):
        publier(r, "une", "2026-11-22", numero=1)
    with pytest.raises(RefusPublication, match="À VÉRIFIER"):
        publier(r, "une", "2026-11-22", numero=2)
    assert publier(r, "une", "2026-11-22", numero=2, forcer=True)["rubrique"] == "une"
    with pytest.raises(RefusPublication, match="pourquoi le lire"):
        publier(r, "detour", "2026-11-22")
    with pytest.raises(RefusPublication, match="Pas de brouillons"):
        publier(r, "une", "2026-11-30")


def test_retirer_le_dernier(tmp_path):
    r = _brouillons(tmp_path, [UNE])
    publier(r, "une", "2026-11-22")
    assert retirer(r, "dernier-une") == 1
    assert json.loads((r / "iris" / "publies.json").read_text())["une"] == []


# ---- Le cas du 21 novembre : « GTA VI sort ce jeudi », publié un samedi, sous un grand titre GTA VI

from datetime import datetime, timezone

GTA_JEUDI = {**ARTICLE_TC, "title": "GTA VI sort ce jeudi.<br/>Sa version <mark>sans disque</mark> inquiète les joueurs."}
SAMEDI = datetime(2026, 11, 21, 17, 0, tzinfo=timezone.utc)
PAGE = """<section class="view" id="view-vies"><article class="une-hero vies-hero">
<h1 class="display">GTA VI sort aujourd'hui.<br/>Est-il vraiment <mark>à vous ?</mark></h1></article>
<div class="cards4"><a><h3>Une peluche affole la planète. Les robots achètent avant vous.</h3></a></div></section>
<section id="view-relecture"></section>"""


def _brouillons_du_21(tmp_path: Path, article: dict, page: str | None = None) -> Path:
    d = tmp_path / "redaction" / "propositions"
    d.mkdir(parents=True)
    (d / "2026-11-21.json").write_text(json.dumps({"date": "2026-11-21", "propositions": [
        {"rubrique": "tous_connectes", "image": "assets/photos/jeux-video.jpg", "article": article}]}, ensure_ascii=False))
    if page:
        (tmp_path / "iris").mkdir()
        (tmp_path / "iris" / "index.html").write_text(page)
    return tmp_path


def test_titre_perime_refuse(tmp_path):
    r = _brouillons_du_21(tmp_path, GTA_JEUDI)
    with pytest.raises(RefusPublication, match="Titre périmé.*ce jeudi.*samedi"):
        publier(r, "tous_connectes", "2026-11-21", maintenant=SAMEDI)
    assert publier(r, "tous_connectes", "2026-11-21", maintenant=SAMEDI, forcer=True)["rubrique"] == "tous_connectes"


def test_titre_au_passe_accepte(tmp_path):
    passe = {**GTA_JEUDI, "title": "GTA VI est sorti jeudi.<br/>Sa boîte ne contient <mark>aucun disque.</mark>"}
    r = _brouillons_du_21(tmp_path, passe)
    assert publier(r, "tous_connectes", "2026-11-21", maintenant=SAMEDI)["rubrique"] == "tous_connectes"


def test_brouillon_d_un_jour_passe_va_aux_archives(tmp_path):
    import xml.etree.ElementTree as ET
    r = _brouillons_du_21(tmp_path, ARTICLE_TC)          # « GTA VI sort aujourd'hui », brouillon du 21
    res = publier(r, "tous_connectes", "2026-11-21", maintenant=datetime(2026, 11, 23, 9, tzinfo=timezone.utc))
    assert res["archive"] is True and res["date"] == "2026-11-21"   # son « aujourd'hui » est le 21 : rien de périmé
    item = ET.parse(r / "iris" / "flux.xml").getroot().find("channel/item")
    assert "21 Nov 2026" in item.findtext("pubDate")                # daté du 21 dans le flux, pas du 23
    assert publier(r, "tous_connectes", "2026-11-21", maintenant=SAMEDI)["archive"] is False


def test_doublon_avec_le_grand_titre_refuse(tmp_path):
    passe = {**GTA_JEUDI, "title": "GTA VI est sorti jeudi.<br/>Sa boîte ne contient <mark>aucun disque.</mark>"}
    r = _brouillons_du_21(tmp_path, passe, PAGE)
    with pytest.raises(RefusPublication, match="Doublon.*GTA VI sort aujourd'hui"):
        publier(r, "tous_connectes", "2026-11-21", maintenant=SAMEDI)
    autre = {**ARTICLE_TC, "title": "Un mathématicien dit avoir résolu Riemann.<br/>Avec <mark>une IA.</mark>"}
    r2 = _brouillons_du_21(tmp_path / "b", autre, PAGE)
    assert publier(r2, "tous_connectes", "2026-11-21", maintenant=SAMEDI)["rubrique"] == "tous_connectes"


def test_grand_titre_par_defaut_ou_carte_seulement(tmp_path):
    autre = {**ARTICLE_TC, "title": "Un mathématicien dit avoir résolu Riemann.<br/>Avec <mark>une IA.</mark>"}
    r = _brouillons_du_21(tmp_path, autre)
    publier(r, "tous_connectes", "2026-11-21", maintenant=SAMEDI)
    assert "place" not in json.loads((r / "iris" / "publies.json").read_text())["tous_connectes"][0]
    publier(r, "tous_connectes", "2026-11-21", maintenant=SAMEDI, carte=True)
    assert json.loads((r / "iris" / "publies.json").read_text())["tous_connectes"][0]["place"] == "carte"


def test_flux_rss_suit_les_publications(tmp_path, monkeypatch):
    import xml.etree.ElementTree as ET
    monkeypatch.setenv("SITE_URL", "https://iris.example/")
    autre = {**ARTICLE_TC, "title": "Un mathématicien dit avoir résolu Riemann.<br/>Avec <mark>une IA.</mark>",
             "chapo": "Une preuve de <b>250 000</b> pages."}
    r = _brouillons_du_21(tmp_path, autre)
    res = publier(r, "tous_connectes", "2026-11-21", maintenant=SAMEDI)
    assert res["url"] == f"/#article-{res['id']}" and res["texte"] == "Une preuve de 250 000 pages."
    flux = ET.parse(r / "iris" / "flux.xml").getroot()
    item = flux.find("channel/item")
    assert item.findtext("title") == "Un mathématicien dit avoir résolu Riemann. Avec une IA."
    assert item.findtext("link") == f"https://iris.example/#article-{res['id']}"
    assert item.findtext("guid") == f"iris-{res['id']}" and "21 Nov 2026" in item.findtext("pubDate")
    retirer(r, "dernier-tous_connectes")
    assert ET.parse(r / "iris" / "flux.xml").getroot().find("channel/item") is None


def test_points_a_verifier_bloquent_la_publication(tmp_path):
    art = {**ARTICLE_TC, "title": "Un mathématicien dit avoir résolu Riemann.<br/>Avec <mark>une IA.</mark>",
           "a_verifier": ["Confirmer la date exacte du communiqué"]}
    r = _brouillons_du_21(tmp_path, art)
    with pytest.raises(RefusPublication, match="1 point\\(s\\) à vérifier : Confirmer la date"):
        publier(r, "tous_connectes", "2026-11-21", maintenant=SAMEDI)
    assert publier(r, "tous_connectes", "2026-11-21", maintenant=SAMEDI, forcer=True)["rubrique"] == "tous_connectes"


def test_alerte_ligne_editoriale_bloque(tmp_path):
    d = tmp_path / "redaction" / "propositions"
    d.mkdir(parents=True)
    art = {**ARTICLE_TC, "title": "Un mathématicien dit avoir résolu Riemann.<br/>Avec <mark>une IA.</mark>"}
    (d / "2026-11-21.json").write_text(json.dumps({"propositions": [{"rubrique": "tous_connectes", "article": art,
        "alertes_charte": ["Ligne éditoriale : toutes les sources sont des rubriques faits divers, justice ou politique."]}]}))
    with pytest.raises(RefusPublication, match="Ligne éditoriale"):
        publier(tmp_path, "tous_connectes", "2026-11-21", maintenant=SAMEDI)
    assert publier(tmp_path, "tous_connectes", "2026-11-21", maintenant=SAMEDI, forcer=True)["rubrique"] == "tous_connectes"


def test_detour_liens_a_garder(tmp_path):
    liens = [{"media": m, "titre": f"Titre {m}", "url": f"https://{m}.example/a", "pourquoi": "Parce que.", "categorie": "Réseau"}
             for m in ("next", "monde", "register", "ars", "404")]
    d = tmp_path / "redaction" / "propositions"
    d.mkdir(parents=True)
    (d / "2026-11-24.json").write_text(json.dumps({"propositions": [{"rubrique": "detour", "liens": liens}]}))
    with pytest.raises(RefusPublication, match="pas de n° 7"):
        publier(tmp_path, "detour", "2026-11-24", liens="1, 7", maintenant=SAMEDI)
    with pytest.raises(RefusPublication, match="illisible"):
        publier(tmp_path, "detour", "2026-11-24", liens="un et trois", maintenant=SAMEDI)
    publier(tmp_path, "detour", "2026-11-24", liens="1, 3, 4", maintenant=SAMEDI)
    pub = json.loads((tmp_path / "iris" / "publies.json").read_text())
    assert [l["source"] for l in pub["detour"]] == ["next", "register", "ars"]
    assert all(l["date"] == "2026-11-24" and l["publie_le"] for l in pub["detour"])
    # un lien sans « pourquoi » n'empêche plus rien s'il n'est pas gardé
    liens[1]["pourquoi"] = None
    (d / "2026-11-24.json").write_text(json.dumps({"propositions": [{"rubrique": "detour", "liens": liens}]}))
    assert publier(tmp_path, "detour", "2026-11-24", liens="1, 5", maintenant=SAMEDI)["rubrique"] == "detour"
