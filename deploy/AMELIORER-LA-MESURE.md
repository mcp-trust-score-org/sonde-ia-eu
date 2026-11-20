# Améliorer la mesure : ce qui est corrigé, ce qui reste à faire de ton côté

## Ce qui est corrigé dans le code

### 1. Les relevés quotidiens n'étaient plus jamais faits
Les trois workflows (veille, mesure horaire, relevés quotidiens) partageaient le même groupe
`concurrency: mesure`. GitHub n'y garde qu'un seul lancement en attente : les relevés quotidiens
étaient **annulés tous les jours** (avoirs, bulletin, preuves horodatées, chemin réseau).
Chaque workflow a maintenant son propre groupe, et l'enregistrement réessaie si deux workflows
publient en même temps.

### 2. La région à chaque mesure
Chaque mesure de veille garde maintenant l'hôte de l'API et l'adresse IP vers laquelle il pointait
à cet instant (`hote`, `ip`). Croisée avec le chemin réseau quotidien (`python -m sonde chemin`),
elle dit par quel opérateur et quel pays la requête est entrée. Elle ne dit pas où tourne le modèle.

## Ce qui reste à faire de ton côté

### 3. Mesurer vraiment toutes les 10 minutes (gratuit, 10 minutes de réglage)
Les crons de GitHub sont « au mieux » : sur ce dépôt, la veille prévue toutes les 10 minutes
ne tourne en réalité qu'environ **toutes les 4 heures**. La solution gratuite : un service externe
qui lance la veille à heure fixe.

1. **Créer un jeton GitHub** : github.com → ta photo → *Settings* → *Developer settings* →
   *Personal access tokens* → *Fine-grained tokens* → *Generate new token*.
   - Resource owner : `mcp-trust-score-org` ; Repository access : *Only select repositories* → `sonde-ia-eu`.
   - Permissions → Repository permissions → **Actions : Read and write**. Rien d'autre.
   - Copie le jeton (il ne s'affiche qu'une fois). Ne le colle jamais dans le dépôt ni dans une conversation.
2. **Créer un compte gratuit sur cron-job.org**, puis *Create cronjob* :
   - URL : `https://api.github.com/repos/mcp-trust-score-org/sonde-ia-eu/actions/workflows/veille.yml/dispatches`
   - Exécution : toutes les 10 minutes.
   - Onglet *Advanced* : méthode **POST** ;
     en-têtes `Authorization: Bearer <ton jeton>`, `Accept: application/vnd.github+json` ;
     corps de la requête : `{"ref":"main"}`.
3. Dans GitHub → onglet *Actions* → *Veille (sans serveur)*, tu dois voir un lancement
   « workflow_dispatch » toutes les 10 minutes.

Le dépôt étant public, les minutes de GitHub Actions sont gratuites.

### 4. Un deuxième point de mesure
Aujourd'hui, tout est mesuré depuis les serveurs de GitHub (souvent aux États-Unis).
Une panne de leur réseau ressemblerait à une panne d'un fournisseur.
Le dossier `deploy/` sait déjà installer la sonde sur un petit serveur Linux en France
(`deploy/installer.sh`, quelques euros par mois chez un hébergeur français).
Dis-moi quand tu as un serveur : il faudra adapter la publication pour que les deux points
(GitHub et le serveur) mesurent en parallèle sans s'écraser, puis le moteur de croisement
tiendra compte des deux.

### 5. Des mesures couvertes par les contrats
Aujourd'hui, les mesures ne sont couvertes par aucun SLA :
- **OVHcloud** est mesuré en **usage anonyme gratuit** (aucune clé) ;
- **Mistral** et **Scaleway** sont sur des **offres gratuites** (`offre: gratuite` dans `config/fournisseurs.yaml`) ;
  le SLA Mistral ne couvre que les contrats entreprise, celui de Scaleway exclut les crédits offerts.

Pour pouvoir réclamer des avoirs sur ces mesures : un compte payant chez chaque fournisseur,
puis sa clé dans GitHub → *Settings* → *Secrets and variables* → *Actions* :
`OVH_AI_ENDPOINTS_ACCESS_TOKEN`, `MISTRAL_API_KEY`, `SCW_SECRET_KEY`, `IONOS_API_TOKEN`.
Passe ensuite `offre: payante` dans `config/fournisseurs.yaml`.
En attendant, les montants d'avoirs affichés doivent rester présentés comme des **estimations pédagogiques**.
