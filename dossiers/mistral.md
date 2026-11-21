# Dossier de surveillance – Mistral AI

Période : 2026-11-15 → 2026-11-21 · généré le 2026-11-21 11:56 UTC

> Ce dossier rassemble des mesures externes indépendantes. Il aide à documenter la surveillance d'un prestataire TIC ; il ne constitue ni une évaluation des risques de l'entité, ni un audit, ni un avis juridique. Les correspondances réglementaires sont indicatives.

## Identification du prestataire

| Champ | Valeur | Source |
|---|---|---|
| Nom | Mistral AI | configuration |
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

Aucune mesure sur la période.

## 2. Chemin réseau observé

**Constat au 2026-11-21 : Intermédiaire ou opérateur non européen observé**

- Entrée réseau 162.159.142.207 opérée par Cloudflare (société mère : US)
- Entrée réseau 172.66.2.203 opérée par Cloudflare (société mère : US)
- Entrée réseau 2606:4700:7::2c3 opérée par Cloudflare (société mère : US)
- Entrée réseau 2a06:98c1:58::2c3 opérée par Cloudflare (société mère : US)
- Intermédiaire Cloudflare visible dans les en-têtes (société mère : US)

- Pays des points d'entrée observés : US
- Opérateurs réseau : Cloudflare
- Intermédiaires visibles : Cloudflare
- Relevés sur la période : 4 · constats distincts : intermediaire_non_ue

Portée : ce relevé montre l'infrastructure par laquelle les requêtes entrent. Il ne prouve pas à lui seul le lieu de traitement du modèle, à confirmer contractuellement (champ B_02.02.0160).

## 3. Stabilité du modèle et catalogue

Pas encore d'empreinte.

## 4. Substituabilité : alternatives mesurées


## 5. Preuves horodatées

2 manifestes quotidiens sur la période, dont 2 ancrés via OpenTimestamps.
Méthode de vérification : voir `sonde/horodatage.py`.
