# Les fournisseurs d'IA européens à l'épreuve de DORA

*Brouillon généré automatiquement le 21/11/2026. Période mesurée : 2026-11-15 → 2026-11-21. 171 appels mesurés, 4 hébergeur(s).*

> À relire avant publication. Les chiffres viennent des mesures ; les passages [À COMMENTER] sont à écrire.

## En bref

[À COMMENTER : les 3 constats qui comptent pour un responsable des risques fournisseurs]

## Pourquoi ce rapport

Les entités financières européennes doivent surveiller en continu leurs prestataires TIC (DORA, art. 28), y compris leurs fournisseurs d'IA. Le 31 juillet 2026, les autorités européennes de supervision ont appelé à des inventaires tenus à jour des API et composants d'IA, et pointé les points de défaillance uniques partagés par plusieurs établissements. Ce rapport apporte des mesures indépendantes sur les hébergeurs d'IA européens.

## 1. Disponibilité mesurée

| Hébergeur | Modèle | Disponibilité | Plus longue série d'échecs | Offre mesurée |
|---|---|---|---|---|
| OVHcloud AI Endpoints | gpt-oss-120b | 77.19 % | 1 h | anonyme |
| OVHcloud AI Endpoints | llama-3.3-70b | 85.96 % | 1 h | anonyme |
| OVHcloud AI Endpoints | mistral-small-3.2 | 85.96 % | 1 h | anonyme |

[À COMMENTER]

## 2. Par où passent vraiment les requêtes

- **IONOS AI Model Hub** : Toutes les entrées réseau observées sont opérées et localisées dans l'UE/EEE
- **Mistral AI** : Entrée réseau 162.159.142.207 opérée par Cloudflare (société mère : US); Entrée réseau 172.66.2.203 opérée par Cloudflare (société mère : US); Entrée réseau 2606:4700:7::2c3 opérée par Cloudflare (société mère : US); Entrée réseau 2a06:98c1:58::2c3 opérée par Cloudflare (société mère : US); Intermédiaire Cloudflare visible dans les en-têtes (société mère : US)
- **OVHcloud AI Endpoints** : Toutes les entrées réseau observées sont opérées et localisées dans l'UE/EEE
- **Scaleway Generative APIs** : Toutes les entrées réseau observées sont opérées et localisées dans l'UE/EEE

Portée : ces relevés décrivent l'entrée réseau des API, pas le lieu exact de traitement.

[À COMMENTER]

## 3. Les modèles changent-ils sans prévenir ?

- OVHcloud AI Endpoints · gpt-oss-120b : 5 empreintes, 0 alerte(s) de changement
- OVHcloud AI Endpoints · llama-3.3-70b : 5 empreintes, 0 alerte(s) de changement
- OVHcloud AI Endpoints · mistral-small-3.2 : 5 empreintes, 0 alerte(s) de changement
- OVHcloud AI Endpoints : 1 modèle(s) retiré(s) du catalogue le 2026-11-19

[À COMMENTER]

## 4. Peut-on changer de fournisseur ?

- gpt-oss-120b : servi et mesuré chez 1 hébergeur(s) européen(s) (OVHcloud AI Endpoints)
- llama-3.3-70b : servi et mesuré chez 1 hébergeur(s) européen(s) (OVHcloud AI Endpoints)
- mistral-small-3.2 : servi et mesuré chez 1 hébergeur(s) européen(s) (OVHcloud AI Endpoints)

[À COMMENTER : ce que cela implique pour la stratégie de sortie et le risque de concentration]

## Méthode

Appels réels toutes les heures, mêmes questions pour tous, aucun appel retenté ; relevé quotidien du chemin réseau (DNS, opérateur, pays via RIPEstat, intermédiaires visibles) ; empreinte quotidienne du modèle ; manifestes quotidiens ancrés via OpenTimestamps. Code et mesures brutes publics.
