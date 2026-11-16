#!/usr/bin/env bash
# Publie les résumés (public/, preuves/) sur GitHub. Les mesures brutes à la minute restent sur le serveur.
set -euo pipefail
cd "$(dirname "$0")/.."
git add public preuves 2>/dev/null || true
git diff --cached --quiet && exit 0
git -c user.name="sonde-ia-eu" -c user.email="sonde-ia-eu@users.noreply.github.com" \
  commit -q -m "Météo $(date -u +%Y-%m-%dT%H:%MZ)"
git pull -q --rebase --autostash -X theirs || git rebase --abort
git push -q
