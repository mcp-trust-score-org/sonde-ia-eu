# Croisement événements ↔ mesures — à relire

Généré le 2026-11-23T20:16:13Z · règles 1.3.1 · mesures du 2026-11-16T09:56:00Z au 2026-11-23T11:11:00Z

Le tag n'est jamais publié : il sert à décider. Rien n'est publié sans validation.

| Tag | Fournisseur | Événement | Début (UTC) | Critères | Texte proposé |
|---|---|---|---|---|---|
| **Aucune anomalie** | Mistral | Cloudflare : Increased HTTP 5xx Errors in Brussels | 2026-11-23T02:34:00Z | ✓ Lieu · ○ Moment · ○ Symptôme · ○ Officiel | Aucune anomalie mesurée chez vos fournisseurs |
| **Aucune anomalie** | Scaleway | [GENERATIVE API] - [GLOBAL] - Increased error rate for model DeepSeek v4.1 Flash 1017 | 2026-11-17T14:43:00Z | ✓ Lieu · ○ Moment · ○ Symptôme · ✓ Officiel | Aucune anomalie mesurée chez vos fournisseurs |
| **Aucune anomalie** | Scaleway | [Generative API] - [global] - GLM-5.3 timeouts | 2026-11-16T14:06:00Z | ✓ Lieu · ○ Moment · ○ Symptôme · ✓ Officiel | Aucune anomalie mesurée chez vos fournisseurs |
| **Confirmé** | OVHcloud | [GLOBAL][AI & Machine Learning] - AI Endpoint Incident Notification | 2026-11-20T06:53:00Z | ✓ Lieu · ✓ Moment · ✓ Symptôme · ✓ Officiel | Nos mesures montrent une interruption qui correspond à l'incident reconnu par OVHcloud. |

_8 événement(s) tombent hors de la période mesurée par la sonde : non croisés._

## Détail

### Cloudflare : Increased HTTP 5xx Errors in Brussels — Mistral
- Tag : **Aucune anomalie**
- Mesures dans la fenêtre : 1
- ⚠️ Mesures depuis un seul point : une panne locale de la sonde ressemblerait à une panne du fournisseur.
- ⚠️ Seulement 1 mesure(s) dans la fenêtre : peu de recul.

### [GENERATIVE API] - [GLOBAL] - Increased error rate for model DeepSeek v4.1 Flash 1017 — Scaleway
- Tag : **Aucune anomalie**
- Mesures dans la fenêtre : 11
- Incident officiel : [GENERATIVE API] - [GLOBAL] - Increased error rate for model DeepSeek v4.1 Flash 1017 (2026-11-17T14:43+00:00 → 2026-11-19T13:20+00:00, impact minor)
- ⚠️ Mesures depuis un seul point : une panne locale de la sonde ressemblerait à une panne du fournisseur.
- ⚠️ Le fournisseur a déclaré un incident, mais la sonde n'a rien vu (modèle ou région non mesurés ?).

### [Generative API] - [global] - GLM-5.3 timeouts — Scaleway
- Tag : **Aucune anomalie**
- Mesures dans la fenêtre : 11
- Incident officiel : [GENERATIVE API] - [GLOBAL] - Increased error rate for model DeepSeek v4.1 Flash 1017 (2026-11-17T14:43+00:00 → 2026-11-19T13:20+00:00, impact minor)
- ⚠️ Mesures depuis un seul point : une panne locale de la sonde ressemblerait à une panne du fournisseur.
- ⚠️ Le fournisseur a déclaré un incident, mais la sonde n'a rien vu (modèle ou région non mesurés ?).

### [GLOBAL][AI & Machine Learning] - AI Endpoint Incident Notification — OVHcloud
- Tag : **Confirmé**
- Mesures dans la fenêtre : 4
- Anomalie : lenteur à 2026-11-20T08:00:00Z (llama-3.3-70b : 16731 ms contre 1159 ms d'habitude) — preuve : `historique.json 2026-11-20T08:00:00Z llama-3.3-70b`
- Incident officiel : [GLOBAL][AI & Machine Learning] - AI Endpoint Incident Notification (2026-11-20T06:53+00:00 → 2026-11-20T12:19+00:00, impact major)
- ⚠️ Mesures depuis un seul point : une panne locale de la sonde ressemblerait à une panne du fournisseur.
- ⚠️ Contrat non vérifié : ne pas annoncer d'avoir.
