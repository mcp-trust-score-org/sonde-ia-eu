# Règles de gestion — Corrélation « fait ↔ mesures de la sonde »

> Objectif : relier automatiquement un événement (fait d'actualité, incident fournisseur) aux mesures de la sonde, calculer un **niveau de confiance**, et proposer un encadré « Quel impact chez moi ? ».
> **Rien n'est publié automatiquement.** La sonde prépare, la rédaction relit et valide.
> **Le niveau de confiance est un tag de relecture.** Il n'est jamais affiché sur le site. Il sert à la rédaction pour décider de publier ou non : **c'est la rédaction qui filtre, pas les règles.**

Paramètres chiffrés : `correlation-rules.yaml`. Format de sortie envoyé au média : `impact.schema.json` (exemple : `exemple-impact.json`).

---

## 1. Entrées

| Entrée | Contenu minimum | Origine |
|---|---|---|
| **Inventaire client** | Pour chaque service : fournisseur, région, point de mesure (URL/API), criticité, SLA contractuel | Paramétrage client |
| **Mesures** | Horodatage UTC, point de mesure (ville + opérateur), disponibilité, latence, code d'erreur | Sonde |
| **Événements** | Source (type + URL), fournisseur, région (ou « global »), début, fin éventuelle, type d'événement | Pages de statut, rapports d'incident, presse, réseaux |

Toutes les heures sont stockées en **UTC**. La conversion en heure locale se fait uniquement à l'affichage.

---

## 2. Définition d'une anomalie

Une anomalie est retenue seulement si elle dépasse les seuils de `correlation-rules.yaml` (section `anomalies`) :

- **Indisponibilité** : plusieurs vérifications consécutives en échec.
- **Lenteur** : latence p95 au-dessus de la référence habituelle (même service, même créneau horaire, sur les 7 derniers jours) pendant une durée minimale.
- **Erreurs** : taux d'erreurs au-dessus du seuil pendant une durée minimale.

**R0 — Plusieurs points de mesure.** Une anomalie n'est attribuée au fournisseur que si elle est vue depuis **au moins 2 points de mesure sur des réseaux différents**. Vue depuis un seul point, elle est classée `locale` et ne peut jamais dépasser le niveau « Possible ».

---

## 3. Les quatre critères

| Code | Critère | Vrai si… |
|---|---|---|
| **R1 — Lieu** | Même fournisseur et même région | Le fournisseur de l'événement est dans l'inventaire du client, et la région correspond (ou l'événement est « global ») |
| **R2 — Moment** | Même fenêtre de temps | Le début de l'anomalie tombe dans la fenêtre autour du début de l'événement (`fenetre_temps`) |
| **R3 — Symptôme** | Symptôme cohérent | Le type d'anomalie mesuré fait partie des symptômes attendus pour ce type d'événement (`symptomes_attendus`) |
| **R4 — Officiel** | Reconnu par le fournisseur | Une source de type `statut_fournisseur` ou `rapport_incident` confirme l'incident |

---

## 4. Calcul du niveau de confiance

| Niveau | Règle | Tag (relecture seulement) |
|---|---|---|
| **Confirmé** | R1 + R2 + R3 + R4, et anomalie multi-points (R0) | Tag rouge |
| **Probable** | R1 + R2 + R3, anomalie multi-points, sans R4 | Tag jaune |
| **Possible** | R1 vrai, plus R2 **ou** R3 ; ou anomalie seulement `locale` | Tag gris |
| **Aucune anomalie** | Le fournisseur ou la région n'est pas dans l'inventaire, **ou** R1 vrai mais aucune anomalie mesurée dans la fenêtre | Tag vert |
| **Hors périmètre** | Événement sans fournisseur identifiable | Pas d'encadré « impact » |

Le résultat « Aucune anomalie » est une information à part entière : s'il est publié, il s'affiche « Aucune anomalie mesurée chez vos fournisseurs ».

---

## 5. Règles de rédaction automatique

- **R5 — Jamais de cause affirmée par la sonde.** La sonde mesure des symptômes. La cause vient toujours d'une source citée (fournisseur, presse), avec son URL.
- **R6 — Formulations imposées par niveau** (gabarits dans `correlation-rules.yaml`, section `gabarits`) :
  - Confirmé : « Nos mesures montrent une interruption qui correspond à l'incident reconnu par {fournisseur}. »
  - Probable : « Nos mesures montrent {symptôme} au même moment. {fournisseur} n'a pas encore confirmé d'incident. »
  - Possible : « Un signal faible a été mesuré. Il est en cours de vérification. »
  - Aucune anomalie : « Aucune anomalie mesurée chez vos fournisseurs »
- **R7 — Avoirs.** Un avoir n'est calculé que pour les niveaux Confirmé et Probable, à partir du SLA contractuel du client. Il est toujours affiché comme **estimé** (« ≈ »).
- **R8 — Confidentialité.** Aucune donnée client n'apparaît dans les contenus publics (« Dans nos vies », Le Détour). Les données d'impact ne sont visibles que par le client concerné.

---

## 6. Tag de relecture

- **R12 bis — Pas de mesure, pas de niveau.** Si la sonde n'a fait aucune mesure du fournisseur pendant l'événement (trou entre deux relevés), l'impact n'est pas classé : il part dans les événements « non couverts ». Il n'est jamais présenté comme un « signal faible ».
- **R13 — Tag invisible sur le site.** Le niveau (Confirmé, Probable, Possible, Aucune anomalie) est enregistré avec chaque impact dans le champ `correlation.niveau`. Il s'affiche uniquement dans l'écran de relecture de la rédaction, jamais dans un contenu publié.
- **R14 — La rédaction décide.** Les règles calculent le tag et proposent un texte ; elles ne bloquent ni ne publient rien. La décision « publier / ne pas publier » est prise par la rédaction, au cas par cas, et enregistrée (R10).
- **R15 — Aucune anomalie.** Quand aucune anomalie n'est mesurée chez les fournisseurs du client pendant l'événement, le texte proposé est : « Aucune anomalie mesurée chez vos fournisseurs ».

---

## 7. Circuit de validation

```
brouillon_auto → a_relire → valide → publie
                      ↘ rejete
```

- **R9 — Pas de publication automatique.** Seule la rédaction peut passer un contenu à `valide`, puis à `publie`, en s'appuyant sur le tag de relecture.
- **R10 — Traçabilité.** Chaque impact conserve : les identifiants des mesures utilisées (preuves), les sources de l'événement, la version des règles, la personne qui a validé et la date.
- **R11 — Révision.** Si une confirmation officielle arrive après coup, le niveau est recalculé (Probable → Confirmé) et le contenu repasse à `a_relire`. Si un fournisseur dément ou corrige, même chose à la baisse.
- **R12 — Délai.** Un impact Confirmé ou Probable non relu sous le délai défini (`alerte_relecture`) déclenche une alerte à la rédaction.

---

## 8. Exemples de la maquette

| Article | R1 | R2 | R3 | R4 | Niveau |
|---|:-:|:-:|:-:|:-:|---|
| La clim et Azure Amsterdam | ✓ | ✓ | ✓ (indisponibilité) | ✓ | **Confirmé** |
| La fibre coupée et OVHcloud Roubaix | ✓ | ✓ | ✓ (lenteur) | ✗ | **Probable** |
| Le certificat et l'API Mistral | ✓ | ✓ | ✓ (erreurs) | ✓ | **Confirmé** |
| La tempête | ✗ | – | – | – | **Aucune anomalie** |
| CrowdStrike (Retour sur) | ✗ | – | – | – | **Aucune anomalie** |
