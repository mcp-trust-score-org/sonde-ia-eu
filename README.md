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
