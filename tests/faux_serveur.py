"""Faux serveur compatible OpenAI pour tester la sonde sans clé ni réseau.

Chaque préfixe d'URL simule un comportement de fournisseur :
  /rapide   : bonnes réponses, renvoie l'usage
  /lent     : 300 ms avant le premier mot, se trompe sur le calcul
  /panne    : HTTP 503 sur chaque appel
  /strict   : refuse `stream_options` (HTTP 400), ne renvoie jamais l'usage
  /catako   : catalogue en erreur
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import yaml
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Route

TACHES = yaml.safe_load((Path(__file__).resolve().parent.parent / "config" / "taches.yaml").read_text(encoding="utf-8"))["taches"]

BONNES_REPONSES = {
    "calcul-abonnement": "178,80",
    "raisonnement-ages": "10",
    "extraction-json": '```json\n{"nom": "Claire Dubois", "ville": "Lyon", "date": "3 mars 2026"}\n```',
    "classification-client": "Livraison",
    "correction-orthographe": "Les dossiers que j'ai envoyés hier sont arrivés.",
    "traduction-anglais": "The report must be submitted before Friday.",
    "connaissance-cnil": "CNIL",
    "date-jour-semaine": "Mardi",
    "code-python": "def est_pair(n):\n    return n % 2 == 0",
    "format-trois-lignes": "Fraise\nCerise\nFramboise",
    "resume-court": "Le règlement européen classe les IA par niveau de risque et impose des obligations aux systèmes à haut risque.",
}

CATALOGUE = ["Meta-Llama-3_3-70B-Instruct", "gpt-oss-120b", "Qwen3-32B"]


def _tache(prompt: str) -> str | None:
    for t in TACHES:
        if t["prompt"] == prompt:
            return t["id"]
    return None


async def modeles(request: Request):
    if request.path_params["prov"] == "catako":
        return JSONResponse({"error": "boom"}, status_code=500)
    return JSONResponse({"object": "list", "data": [{"id": m, "object": "model"} for m in CATALOGUE]})


async def chat(request: Request):
    prov = request.path_params["prov"]
    corps = await request.json()
    if prov == "panne":
        return JSONResponse({"error": "service indisponible"}, status_code=503)
    if prov == "strict" and "stream_options" in corps:
        return JSONResponse({"error": "Unknown parameter: stream_options"}, status_code=400)

    tache = _tache(corps["messages"][-1]["content"])
    texte = BONNES_REPONSES.get(tache, "Je ne sais pas.")
    if prov == "lent" and tache == "calcul-abonnement":
        texte = "149"

    async def flux():
        if prov == "lent":
            await asyncio.sleep(0.3)
        morceaux = [texte[i : i + 8] for i in range(0, len(texte), 8)]
        for m in morceaux:
            evt = {"choices": [{"index": 0, "delta": {"content": m}}]}
            yield f"data: {json.dumps(evt)}\n\n"
            await asyncio.sleep(0.005)
        if corps.get("stream_options", {}).get("include_usage"):
            usage = {"prompt_tokens": 40, "completion_tokens": len(morceaux) * 2, "total_tokens": 40 + len(morceaux) * 2}
            yield f"data: {json.dumps({'choices': [], 'usage': usage})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(flux(), media_type="text/event-stream")


app = Starlette(routes=[
    Route("/{prov}/v1/models", modeles),
    Route("/{prov}/v1/chat/completions", chat, methods=["POST"]),
])
