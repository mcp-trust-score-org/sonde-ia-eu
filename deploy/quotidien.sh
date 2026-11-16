#!/usr/bin/env bash
# Chaque nuit sur le serveur : avoirs, bulletin du matin, manifeste horodaté des mesures.
set -uo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python
$PY -m sonde avoirs
$PY -m sonde avoirs --mois "$(date -u +%Y-%m)"
$PY -m sonde meteo
$PY -m sonde bulletin
$PY -m sonde horodater
"$(dirname "$0")/publier.sh"
