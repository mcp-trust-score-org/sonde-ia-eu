# Sonde IA EU

Mesure indépendante et continue des API d'IA hébergées en Europe : **disponibilité, délai avant le premier mot, durée, débit, qualité en français et coût**, pour le même modèle servi par plusieurs hébergeurs.

C'est la première brique de l'observatoire, puis du routeur : chaque mesure est conservée, et l'historique devient l'actif.

## Ce que mesure chaque appel

| Mesure | Comment |
| --- | --- |
| Disponibilité | L'appel aboutit-il ? Les erreurs HTTP, délais dépassés et réponses vides comptent comme indisponibilité. |
| Premier mot (TTFT) | Temps entre l'envoi et le premier morceau de texte reçu en streaming. |
| Durée | Temps total de la réponse. |
| Jetons/s | Jetons de sortie divisés par le temps de génération (après le premier mot). |
| Qualité FR | 11 tâches en français vérifiées automatiquement (calcul, extraction JSON, orthographe, consignes…). |
| Coût | Jetons × prix public, si tu renseignes les prix dans `config/fournisseurs.yaml`. |
| Catalogue | La liste des modèles de chaque fournisseur est relevée à chaque passage : modèles ajoutés, retirés, API injoignable. |

Les identifiants de modèles ne sont pas figés : la sonde lit `/v1/models` et retrouve, par exemple, `Meta-Llama-3_3-70B-Instruct` chez OVHcloud et `meta-llama/Llama-3.3-70B-Instruct` chez IONOS comme le même modèle `llama-3.3-70b`.

## Démarrer en local

```bash
pip install -r requirements.txt
export SCW_SECRET_KEY=...                  # au moins une clé
export OVH_AI_ENDPOINTS_ACCESS_TOKEN=...
python -m sonde mesurer                    # toutes les tâches
python -m sonde rapport --jours 7          # écrit public/classement.md et public/resume.json
```

Un fournisseur sans clé est ignoré. Un modèle qui n'est pas au catalogue d'un fournisseur est signalé, pas compté comme panne.

## Démarrer sans carte bancaire

| Fournisseur | Sans carte ? | Comment |
| --- | --- | --- |
| OVHcloud | Oui, sans compte | Aucune clé : la sonde passe en accès anonyme (2 requêtes par minute et par modèle), une requête toutes les 31 s. |
| Mistral | Oui | Plan gratuit Experiment : compte + vérification par SMS. Les requêtes de ce plan peuvent servir à entraîner les modèles de Mistral (sans gravité ici : nos prompts sont publics). |
| Scaleway | Oui, limité | Compte sans moyen de paiement : limites plus strictes, palier gratuit d'1 million de jetons. |
| IONOS | Non | Contrat nécessaire. |

Les mesures faites sur une offre gratuite ou anonyme sont marquées comme telles dans le classement (par exemple `ovhcloud (anonyme)`) : leurs limites de débit ne sont pas celles d'un client payant. Avant de publier un classement, passer sur des offres payantes et mettre `offre: payante` dans `config/fournisseurs.yaml`.

## Mettre en route la mesure horaire (GitHub Actions)

1. Pousse ce dossier dans un nouveau dépôt GitHub (public : minutes Actions gratuites et illimitées).
2. Dans **Settings → Secrets and variables → Actions**, ajoute les clés : `MISTRAL_API_KEY`, `SCW_SECRET_KEY`, `OVH_AI_ENDPOINTS_ACCESS_TOKEN`, `IONOS_API_TOKEN`.
3. Onglet **Actions → Mesure horaire → Run workflow** pour un premier passage.

Ensuite, chaque heure : 3 tâches en rotation × 3 modèles × 4 fournisseurs, soit 36 appels. Les mesures s'ajoutent dans `data/AAAA-MM.jsonl`, et le classement sur 7 jours est régénéré dans `public/`.

## Relevés quotidiens : la surveillance pour DORA

Le workflow `quotidien.yml` tourne chaque jour à 3 h 41 UTC :

| Commande | Ce qu'elle produit |
| --- | --- |
| `python -m sonde chemin` | Chemin réseau réel de chaque API : adresses, opérateur réseau, pays (RIPEstat), intermédiaires visibles (CDN). Verdict prudent : « UE observé », « intermédiaire non UE », « indéterminé ». |
| `python -m sonde empreinte` | Empreinte des modèles : 8 questions fixes à temperature 0, comparées à la référence. Alerte « changement probable » après deux écarts consécutifs. |
| `python -m sonde dossiers` | Un dossier de surveillance par fournisseur dans `dossiers/` (Markdown + JSON), avec la correspondance indicative vers DORA (registre B_02.02, B_05.02, B_07.01) et l'AI Act. |
| `python -m sonde rapport-public` | Brouillon du rapport public dans `rapports/brouillon-courant.md`, à commenter avant publication. |
| `python -m sonde horodater` | Manifeste du jour dans `preuves/` (SHA-256 de chaque fichier de mesures) ancré via OpenTimestamps. |

Limites à connaître : le chemin réseau décrit l'entrée des requêtes, pas le lieu exact de traitement du modèle ; les runners GitHub ne garantissent pas leur région, ce qui peut modifier la résolution DNS ; l'empreinte détecte des changements nets de comportement, pas les variations très fines.

## Page publique

`index.html`, à la racine, affiche le classement, la courbe de rapidité, les incidents et les hébergeurs à venir. Elle lit `public/resume.json` et `public/historique.json`, régénérés à chaque mesure : elle se met donc à jour toute seule.

Pour la mettre en ligne gratuitement : **Settings → Pages → Build and deployment → Source : Deploy from a branch → Branch : `main`, dossier `/ (root)` → Save**. L'adresse s'affiche en haut de la même page au bout d'une ou deux minutes.

## Iris, la météo de l'IA : la veille à la minute

La sonde fait maintenant tourner le service complet : veille à la minute, météo, alertes, avoirs, attestations et bulletin du matin. L'appli **Iris** (dossier `iris/`) affiche tout cela à partir des fichiers publiés dans `public/`.

| Commande | Ce qu'elle fait |
| --- | --- |
| `python -m sonde veille` | Un appel minimal (« Réponds seulement : OK ») par fournisseur. `--boucle` : un passage au début de chaque minute, sans fin. `--avec-meteo` : météo et alertes après chaque passage. Lignes dans `data/veille/AAAA-MM-JJ.jsonl`. |
| `python -m sonde meteo` | Écrit `public/meteo.json` : état de chaque fournisseur (soleil, éclaircies, nuages, orage), vigilance, pannes des 30 derniers jours, disponibilité 24 h / 7 j / 30 j, chronologie des 6 dernières heures et prévision prudente des 3 suivantes. Écrit aussi `public/minutes/AAAA-MM-JJ.json`, une case par minute. |
| `python -m sonde alertes` | Prévient au début d'un orage, à sa fin et au passage en vigilance orange, sans jamais répéter. Canaux : application ntfy (`NTFY_TOPIC`) et webhook Slack/Discord/Teams (`ALERTE_WEBHOOK_URL`). Journal dans `public/alertes.json`. |
| `python -m sonde direct` | `meteo` puis `alertes`. |
| `python -m sonde avoirs` | Disponibilité du mois selon la définition de panne de chaque contrat (`config/contrats.yaml`), palier d'avoir et date limite. Avec `--facture scaleway=2400`, un dossier de réclamation prêt à envoyer dans `reclamations/AAAA-MM/`. Avec `--ticket ovhcloud=2026-10-08T09:20`, tient compte des contrats où la panne ne compte qu'à partir du ticket. |
| `python -m sonde attestation --fournisseur ovhcloud --debut … --fin …` | Attestation de panne horodatée sur un créneau, minute par minute, avec les empreintes SHA-256 des mesures, dans `attestations/`. |
| `python -m sonde bulletin` | Bulletin du matin : `public/bulletin.svg` (format LinkedIn 1080 × 1350, et `.png` si `cairosvg` est installé) et le texte du post dans `public/bulletin.txt`. |

Les dossiers `reclamations/` et `attestations/` contiennent des données propres à un membre (factures) : ils ne sont pas envoyés sur GitHub.

### Avant toute réclamation : vérifier les contrats

`config/contrats.yaml` contient les engagements publics connus. Tout ce qui est marqué `verifie: false` est une **estimation** : recopie les conditions exactes du contrat du membre, puis passe `verifie: true`. Pour OVHcloud, la règle « la panne compte à partir du ticket » vient des conditions américaines : à vérifier pour l'offre européenne. Mistral et IONOS n'ont pas encore d'engagement renseigné.

### Recevoir les alertes sur ton téléphone (gratuit, sans compte)

1. Installe l'application **ntfy** (iPhone ou Android).
2. Choisis un nom de sujet difficile à deviner, par exemple `iris-alertes-7k2p9`, et abonne-toi à ce sujet dans l'application.
3. Sur GitHub : **Settings → Secrets and variables → Actions → New repository secret**, nom `NTFY_TOPIC`, valeur ton sujet. Sur un serveur : la ligne `NTFY_TOPIC=` de `/etc/sonde-ia-eu.env`.
4. Pour afficher le bouton « Recevoir les alertes » dans l'appli, mets le même sujet dans `REGLAGES.ntfy`, en haut du script de `iris/index.html`.

Attention : sur ntfy.sh, n'importe qui connaissant le nom du sujet peut s'y abonner, et aussi y publier. Pour des alertes réservées aux membres, il faudra un sujet protégé (offre payante de ntfy ou serveur ntfy à toi).

### Option A, sans serveur : un passage toutes les 10 minutes

Le workflow `veille.yml` fait tourner la veille sur GitHub Actions toutes les 10 minutes, gratuitement. C'est suffisant pour démarrer, mais GitHub décale souvent ses passages de plusieurs minutes, et ses machines ne sont pas en France. Pour des attestations et des avoirs crédibles, passe à l'option B.

### Option B, avec un serveur en France : chaque minute

Il te faut un petit serveur Linux (Ubuntu) chez un hébergeur français, de l'ordre de 4 à 6 € par mois.

1. Sur le serveur : `git clone https://github.com/<toi>/sonde-ia-eu.git ~/sonde-ia-eu`
2. Puis : `sudo bash ~/sonde-ia-eu/deploy/installer.sh`
3. Remplis les clés et les alertes : `sudo nano /etc/sonde-ia-eu.env`, puis `sudo systemctl restart sonde-veille`.
4. Pour que le serveur puisse publier sur GitHub : crée un jeton (GitHub → Settings → Developer settings → Fine-grained tokens, accès « Contents : Read and write » sur ce seul dépôt), puis sur le serveur : `cd ~/sonde-ia-eu && git remote set-url origin https://<jeton>@github.com/<toi>/sonde-ia-eu.git`.
5. Sur GitHub : **Settings → Secrets and variables → Actions → Variables → New repository variable**, nom `VEILLE_SERVEUR`, valeur `oui`. Les workflows GitHub laissent alors la météo, les avoirs et les preuves au serveur. Désactive aussi le workflow « Veille (sans serveur) ».

Pour suivre la veille en direct : `journalctl -u sonde-veille -f`.

Les mesures brutes à la minute restent sur le serveur (`data/veille/`), car elles sont volumineuses. Le manifeste horodaté de chaque nuit, publié dans `preuves/`, contient leur empreinte : c'est ce qui permet de prouver plus tard qu'elles n'ont pas été modifiées. **Sauvegarde le dossier `data/veille/` du serveur** (par exemple une fois par semaine) : sans lui, les preuves ne peuvent plus être vérifiées.

### L'appli Iris

Avec GitHub Pages activé (voir « Page publique »), l'appli est à l'adresse `https://<toi>.github.io/sonde-ia-eu/iris/`. Elle se met à jour toute seule chaque minute. Elle montre :

- la phrase du jour et le radar, que l'on peut rembobiner sur les 6 dernières heures et avancer sur les 3 prochaines (prévision) ;
- la panne en cours, avec l'itinéraire bis ;
- une tuile par fournisseur ; un clic ouvre sa disponibilité et ses pannes récentes ;
- les alertes récentes, le bouton d'abonnement et « Je vois un problème » (ouvre un signalement sur GitHub) ;
- ce que les fournisseurs doivent pour le dernier mois calculé. Le membre tape ses factures : elles restent dans son navigateur et ne sont envoyées nulle part.

Ce qui viendra avec l'espace membres (deuxième étape) : les comptes, le compteur « 14 membres touchés », les signalements comptés en direct et l'envoi des réclamations depuis l'appli.

## Ajouter un fournisseur ou un modèle

- Fournisseur : un bloc dans `config/fournisseurs.yaml` (`base_url` compatible OpenAI + nom de la variable de clé).
- Modèle : un bloc dans `modeles` avec ses `motifs` de nom ; `exact` force un identifiant chez un fournisseur.
- Tâche : un bloc dans `config/taches.yaml` avec sa règle de vérification.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

Les tests utilisent un faux serveur compatible OpenAI qui simule un fournisseur rapide, lent, en panne, un autre qui refuse le paramètre `stream_options`, et un catalogue injoignable.

## Règles de neutralité (à publier avec le classement)

- Même prompt, même `temperature: 0`, même `max_tokens` pour tous.
- Un échec n'est jamais retenté : il est mesuré.
- Les mesures brutes sont publiques (`data/`), pour que chacun puisse refaire les calculs.
- Aucun fournisseur ne paie pour être mesuré ni pour son classement.

## Limites connues

- Les mesures partent des serveurs de GitHub (souvent aux États-Unis) : la latence réseau s'ajoute. Pour des chiffres représentatifs d'un utilisateur européen, faire tourner la sonde depuis une machine en Europe (un petit serveur à quelques euros par mois suffit).
- Quand un fournisseur ne renvoie pas le nombre de jetons, il est estimé (≈ 4 caractères par jeton) et marqué `jetons_estimes`.
- 11 tâches donnent un signal de qualité, pas un benchmark complet : à enrichir avec le temps.
