#!/usr/bin/env bash
# Installe la veille à la minute sur un petit serveur Linux (Ubuntu ou Debian), en France de préférence.
#
#   1. Sur le serveur :  git clone https://github.com/<toi>/sonde-ia-eu.git ~/sonde-ia-eu
#   2. Puis :            sudo bash ~/sonde-ia-eu/deploy/installer.sh
#   3. Remplis les clés : sudo nano /etc/sonde-ia-eu.env   puis   sudo systemctl restart sonde-veille
#
# Ce que ça installe :
#   sonde-veille.service        la veille, un passage par minute, puis météo et alertes
#   sonde-publier.timer         toutes les 5 minutes, publie public/ sur GitHub (l'appli se met à jour)
#   sonde-quotidien.timer       chaque nuit : avoirs, bulletin, preuves horodatées
set -euo pipefail

DOSSIER="$(cd "$(dirname "$0")/.." && pwd)"
UTILISATEUR="${SUDO_USER:-$(whoami)}"

apt-get update -qq
apt-get install -y -qq python3 python3-venv git >/dev/null

sudo -u "$UTILISATEUR" python3 -m venv "$DOSSIER/.venv"
sudo -u "$UTILISATEUR" "$DOSSIER/.venv/bin/pip" install -q -r "$DOSSIER/requirements.txt" opentimestamps-client cairosvg

if [ ! -f /etc/sonde-ia-eu.env ]; then
  cat > /etc/sonde-ia-eu.env <<'ENV'
# Clés des fournisseurs (laisser vide si tu n'en as pas : OVHcloud fonctionne sans clé)
MISTRAL_API_KEY=
SCW_SECRET_KEY=
OVH_AI_ENDPOINTS_ACCESS_TOKEN=
IONOS_API_TOKEN=
# Alertes : sujet ntfy (application gratuite ntfy sur le téléphone) et/ou webhook Slack/Discord
NTFY_TOPIC=
ALERTE_WEBHOOK_URL=
# Affiché sur l'appli et les attestations
POINT_DE_MESURE=Paris, France
# Bas du bulletin du matin
BULLETIN_SIGNATURE=
BULLETIN_ADRESSE=
ENV
  chmod 600 /etc/sonde-ia-eu.env
fi

for f in sonde-veille.service sonde-publier.service sonde-publier.timer sonde-quotidien.service sonde-quotidien.timer; do
  sed -e "s#@DOSSIER@#$DOSSIER#g" -e "s#@UTILISATEUR@#$UTILISATEUR#g" "$DOSSIER/deploy/$f" > "/etc/systemd/system/$f"
done
chmod +x "$DOSSIER/deploy/publier.sh" "$DOSSIER/deploy/quotidien.sh"
systemctl daemon-reload
systemctl enable --now sonde-veille.service sonde-publier.timer sonde-quotidien.timer

echo
echo "Installé. Suivre la veille en direct :  journalctl -u sonde-veille -f"
echo "Pense à remplir /etc/sonde-ia-eu.env, puis : sudo systemctl restart sonde-veille"
echo "Pour la publication sur GitHub, voir le README (section « Serveur »)."
