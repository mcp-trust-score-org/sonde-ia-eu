# Dossier de surveillance – OVHcloud AI Endpoints

Période : 2026-11-15 → 2026-11-21 · généré le 2026-11-21 17:20 UTC

> Ce dossier rassemble des mesures externes indépendantes. Il aide à documenter la surveillance d'un prestataire TIC ; il ne constitue ni une évaluation des risques de l'entité, ni un audit, ni un avis juridique. Les correspondances réglementaires sont indicatives.

## Identification du prestataire

| Champ | Valeur | Source |
|---|---|---|
| Nom | OVHcloud AI Endpoints | configuration |
| Pays du siège | FR | déclaratif, à confirmer au registre du commerce |
| Identifiant LEI ou EUID | à compléter | GLEIF / registre du commerce |
| Société mère ultime | à compléter | registre du commerce |

## Correspondance réglementaire (indicative)

| Section du dossier | Ce qu'elle aide à documenter |
|---|---|
| Disponibilité, incidents, performance | DORA art. 28 (surveillance continue des prestataires TIC), art. 30 §2 (niveaux de service) |
| Chemin réseau observé : pays et opérateurs d'entrée | Registre d'information B_02.02.0130 (pays de fourniture du service) – élément d'observation |
| Intermédiaires techniques identifiés | Registre B_05.02 (chaîne de sous-traitance TIC) – éléments à confirmer contractuellement |
| Stabilité du modèle, changements de catalogue | DORA art. 28 ; AI Act art. 26 (surveillance du fonctionnement par le déployeur) ; déclaration des ESA du 31/07/2026 (inventaires des API et composants d'IA tenus à jour) |
| Fournisseurs alternatifs mesurés | Registre B_07.01.0050, 0110, 0120 (substituabilité, alternatives identifiées) ; DORA art. 28 §8 (stratégie de sortie), art. 29 (risque de concentration) |
| Preuves horodatées | Traçabilité des éléments de surveillance (piste d'audit) |

## 1. Disponibilité et performance

| Modèle | Appels | Disponibilité | 1er mot médian | 1er mot p95 | Heures avec échec | Plus longue série d'échecs | Offre mesurée |
|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 60 | 75 % | 841 ms | 1,1 s | 9 | 1 h | anonyme |
| llama-3.3-70b | 60 | 81.67 % | 1,2 s | 129,2 s | 5 | 1 h | anonyme |
| mistral-small-3.2 | 60 | 83.33 % | 991 ms | 32,4 s | 5 | 1 h | anonyme |

Les mesures en offre gratuite ou anonyme subissent des limites de débit propres à ces offres : elles ne reflètent pas forcément le service contractuel d'un client payant.

## 2. Chemin réseau observé

**Constat au 2026-11-21 : Entrées réseau opérées et localisées dans l'UE/EEE**

- Toutes les entrées réseau observées sont opérées et localisées dans l'UE/EEE

- Pays des points d'entrée observés : FR
- Opérateurs réseau : OVHcloud
- Intermédiaires visibles : aucun
- Relevés sur la période : 9 · constats distincts : ue_observe

Portée : ce relevé montre l'infrastructure par laquelle les requêtes entrent. Il ne prouve pas à lui seul le lieu de traitement du modèle, à confirmer contractuellement (champ B_02.02.0160).

## 3. Stabilité du modèle et catalogue

| Modèle | Empreintes | Similarité avec la référence | Alertes de changement | Changements d'identifiant |
|---|---|---|---|---|
| gpt-oss-120b | 9 | référence en cours | 0 | 0 |
| llama-3.3-70b | 9 | 0.62 | 0 | 0 |
| mistral-small-3.2 | 9 | 0.73 | 2 | 0 |
- 2026-11-21 16:43 · mistral-small-3.2 : changement probable (similarité 0.73 sous la variation normale (médiane 1.00, limite 0.96))
- 2026-11-21 17:11 · mistral-small-3.2 : changement probable (similarité 0.73 sous la variation normale (médiane 1.00, limite 0.96))

Changements de catalogue :
- 2026-11-17 : +9 / -0
- 2026-11-19 : +3 / -0
- 2026-11-19 : +1 / -1 (retirés : Olala-v1.0-summarize)

## 4. Substituabilité : alternatives mesurées

- gpt-oss-120b : aucune alternative européenne mesurée à ce jour
- llama-3.3-70b : aucune alternative européenne mesurée à ce jour
- mistral-small-3.2 : aucune alternative européenne mesurée à ce jour

## 5. Preuves horodatées

3 manifestes quotidiens sur la période, dont 3 ancrés via OpenTimestamps.
Méthode de vérification : voir `sonde/horodatage.py`.
