# IRIS — le média

> Voir venir. Transmettre l'essentiel.

Site public du média Iris : HTML, CSS et JavaScript simples, **sans build ni dépendance**.
Il se déploie tel quel sur Vercel.

## Mettre en ligne

```bash
cd iris-media
git init
git add .
git commit -m "Iris : site média"
git branch -M main
git remote add origin https://github.com/<ton-compte>/iris-media.git
git push -u origin main
```

Puis sur vercel.com : **Add New → Project → Import** le dépôt `iris-media`.
Framework preset : **Other**. Build command : vide. Output directory : vide.
Chaque `git push` redéploie le site.

## Rubriques

| Onglet | Adresse | Accès | Contenu |
|---|---|---|---|
| À la une | `/#une` | Tous | Les événements inattendus qui révèlent notre dépendance à la technologie. Deux éditions (Jeu. / Ven.) |
| Tous connectés | `/#vies` | Tous | L'édition grand public |
| Le Détour | `/#detour` | Tous | Sélection d'articles d'autres médias + série « 24 h chez… » |
| Ma Météo | `/#meteo` | Premium | Carte des fournisseurs, piliers, dispo vs SLA, signaux |
| Alertes | `/#alertes` | Premium | Un fait, une conséquence, un bouton |
| Indicateurs | `/#indicateurs` | Premium | Performance · Conformité · Avoirs |
| Rapports | `/#rapports` | Premium | Dossiers DORA, NIS2, réclamation SLA |
| Talk to my data | bouton de la barre | Premium | Démo de questions en langage naturel |
| Articles | `/#article-<id>` | Tous | Le fait inattendu → La conséquence technologique → La dépendance révélée (ou « Et vous ? ») |

Les encarts « Les articles les plus lus » sont sur À la une et Tous connectés.

### Standard / Premium

Un sélecteur **Standard / Premium** dans la barre sert à la démo.
- **Standard** : aucune donnée sur les fournisseurs du lecteur. La une parle de « La dépendance » et l'encadré d'impact invite à passer Premium.
- **Premium** : la une affiche « Chez vous » et l'encadré « Quel impact chez moi ? » montre les vrais chiffres.

Dans le vrai produit, ce sélecteur disparaît : c'est le compte connecté qui décide, et les onglets Premium sont protégés par une connexion.

## Structure

```
index.html        les écrans du site
styles.css        la DA (tokens en haut du fichier) et la mise en page
main.js           onglets, articles, carte météo, filtres, encarts, chat
vercel.json       URLs propres + cache des images
assets/
  logo.svg        IRIS + point de notification jaune
  favicon.svg
  europe-dots.svg carte de la météo
  une-statue.jpg  visuel de la une
  card-*.jpg      visuels des cartes de l'édition du vendredi
  photos/         banque de photos par catégorie (noir et blanc + jaune)
```

### Banque de photos (`assets/photos/`)

| Fichier | Catégorie |
|---|---|
| `jeux-video.jpg` | Jeux vidéo (borne d'arcade) |
| `logiciel.jpg` | Logiciel (mains robot / humaine) |
| `ia.jpg` | IA (mains robot / humaine) |
| `reseau.jpg` | Réseau (antenne) |
| `energie.jpg` | Énergie (pylônes) |
| `societe.jpg` | Société (file d'attente) |
| `politique.jpg` | Politique (temple) |
| `innovation.jpg` | Innovation (astronaute) |
| `sante.jpg` | Santé |
| `savoir.jpg` | Savoir (livres) |
| `medias-tv.jpg` | Médias (télé) |
| `pop-culture-*.jpg` | Pop culture : cinéma, concert, BD, vinyle |
| `une-statue-arc.jpg` | Réserve pour la une |

Une catégorie = une photo. Pour remplacer une photo, garde le même nom de fichier.

## Modifier les contenus

Tout est en haut de `main.js` :
- `ARTICLES` : les articles (titre, chapo, trois étapes, impact, sources, photo) ;
- `PROVIDERS` : les fournisseurs de la carte et du tableau SLA ;
- `MOST_READ` : les articles les plus lus (3 par rubrique) ;
- `EXTERNAL` : la sélection du Détour (liens vers d'autres médias) ;
- `ANSWERS` : les réponses de démo du chat.

Les cartes des pages sont dans `index.html`.

## Charte

| Token | Valeur | Usage |
|---|---|---|
| `--bg` | `#0A0A0A` | fond |
| `--panel` | `#141414` | cartes, panneaux |
| `--yellow` | `#FFCC00` | signal, point du logo, surlignage des titres, boutons |
| `--paper` | `#EFEAE0` | fond des cartes photo |
| `--cream` | `#F4F1EA` | titres |
| `--red` | `#FF4A3D` | critique / panne |

Typographies : **Barlow Condensed** 800 en capitales pour les titres, **Barlow** pour le texte (Google Fonts).

## Avant la mise en ligne publique

- Tous les chiffres et plusieurs articles sont **de démonstration** (mention affichée sur les articles concernés).
- Faire vérifier par un juriste : la disponibilité de la marque « Iris », les formulations sur les fournisseurs nommés, les liens vers d'autres médias.
- L'écran de relecture n'est **pas** dans ce dépôt : il est dans `iris-relecture`, à protéger par une connexion.
