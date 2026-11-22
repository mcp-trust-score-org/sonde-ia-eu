"""Notifications IRIS Plus : seuls une nouvelle météo de la semaine ou un nouveau « Et si… ? » préviennent."""

import json

import httpx

from sonde.plus import notifier_nouveautes, nouveautes

AVANT = {"meteo_semaine": [{"id": "2026-11-22", "titre": "Une semaine qui finit à l'orage."}],
         "et_si": [{"id": "edge", "question": "Et si votre IA marchait même quand Internet tombe ?"}]}


def test_nouveautes():
    assert nouveautes(AVANT, AVANT) == []                                   # correction de texte : rien
    apres = {"meteo_semaine": [{"id": "2026-11-29", "titre": "Beau fixe."}] + AVANT["meteo_semaine"],
             "et_si": [{"id": "post-quantique", "question": "Et si un ordinateur quantique lisait vos messages ?"}] + AVANT["et_si"]}
    n = nouveautes(AVANT, apres)
    assert [x["url"] for x in n] == ["/#plus-meteo", "/#plus-etsi-post-quantique"]
    assert all(x["sujet"] == "plus" for x in n) and n[0]["texte"] == "Beau fixe."
    assert nouveautes(None, apres) == [] and nouveautes({}, apres) == []    # première installation : rien


def test_envoi(tmp_path):
    avant, apres = tmp_path / "avant.json", tmp_path / "apres.json"
    avant.write_text(json.dumps(AVANT))
    apres.write_text(json.dumps({**AVANT, "et_si": [{"id": "gps", "question": "Et si le GPS s'arrêtait ?"}] + AVANT["et_si"]}))
    recus = []
    client = httpx.Client(transport=httpx.MockTransport(
        lambda r: recus.append((str(r.url), r.headers["authorization"], json.loads(r.content))) or httpx.Response(200)))
    faits = notifier_nouveautes(avant, apres, {"NOTIF_SECRET": "s", "SITE_URL": "https://iris.example"}, client)
    assert faits == ["Iris Plus · Et si… ?"]
    assert recus[0][0] == "https://iris.example/api/notifier" and recus[0][1] == "Bearer s" and recus[0][2]["sujet"] == "plus"
    assert notifier_nouveautes(avant, apres, {}, client) == []               # sans secret : rien
