# Charte éditoriale d'Iris

Iris raconte **les événements inattendus qui révèlent notre dépendance à la technologie**.

Ce document est la référence de la rédaction. GitHub s'en sert aussi, chaque jour, pour préparer des propositions d'articles : le modèle qui rédige les brouillons reçoit cette charte en consigne.

## 0. Rien n'est publié automatiquement

GitHub propose des brouillons dans `redaction/propositions/`. La rédaction choisit ce qui part en ligne, ce qui est retravaillé et ce qui est écarté.

- Un événement sans anomalie mesurée peut faire l'objet d'un brouillon. Il reste un brouillon jusqu'à décision de la rédaction.
- Le tag de confiance (Confirmé, Probable, Possible, Aucune anomalie) sert à la relecture. Il n'apparaît jamais sur le site.

## 1. Règles communes aux rubriques

### Le style d'écriture

- **Le titre** tient en deux phrases courtes : une situation banale, puis sa conséquence.
- **Un seul élément surligné** dans le titre (balise `<mark>`) : un chiffre fort ou quelques mots.
- **Le chapô** fait 2 ou 3 phrases et pose l'enjeu sans tout dire.
- **Chaque étape** tient en deux paragraphes courts : d'abord le fait, puis une phrase qui prend du recul.
- **Peu de chiffres dans le texte.** On raconte une histoire, pas un tableau de bord. Le chiffre fort va dans le titre ; le détail chiffré va dans l'encadré Premium.
- **On finit par une question au lecteur.**
- **Pas de point d'exclamation, pas de « choc », pas de jargon non expliqué.**

### L'honnêteté

- On n'invente jamais un fait, une citation, un chiffre, une date ou une source.
- Quand la sonde n'a rien mesuré, on l'écrit (« notre sonde était entre deux relevés »).
- Une info virale est vérifiée avant d'être reprise, et toujours liée à sa source.
- On n'expose jamais un particulier : pas de nom, pas de visage, pas de compte personnel.
- Chaque article cite ses sources avec un lien direct.
- On lit les articles avant d'écrire : GitHub ouvre les articles de presse retenus et en donne le texte au rédacteur. Un article payant ou protégé reste non lu, et le brouillon le signale : ce qui en vient est à vérifier à la main.
- On ne recopie pas les articles des autres médias : on raconte avec nos mots. Une citation, si elle est indispensable, fait moins de 15 mots, entre guillemets, avec le nom du média.

### Les études, sondages et chiffres d'entreprises

Les cabinets de conseil (McKinsey, BCG, Bain, Deloitte, EY, KPMG, PwC, Wavestone…), Gartner et les entreprises de la tech **vendent** de la transformation numérique et de l'IA, et beaucoup ont des partenariats avec les géants du secteur. Leurs études peuvent être citées, à quatre conditions :
- **on nomme toujours qui parle** : « selon une étude du cabinet BCG », jamais « selon une étude » ;
- **on donne la méthode** quand on cite un chiffre (combien de personnes interrogées, qui, où) ; sans méthode publiée, pas de chiffre ;
- **un sondage ou une prévision n'est jamais présenté comme un fait** : « 67 % des dirigeants pensent que… » n'est pas « 67 % des entreprises font… » ;
- **on recoupe** avec une source publique ou indépendante quand c'est possible.

Ces cabinets ne font pas partie des sources lues automatiquement par le rédacteur : leurs études passent par le panier de la rédaction (voir section 4). Les écoles, les universités et les organismes publics (CNIL, ANSSI, Arcep, Inria, CNRS, Insee, Conseil de l'IA et du numérique) sont privilégiés : ils n'ont rien à vendre.

### L'essentiel en 2 minutes

Chaque article d'À la une et de Tous connectés a un résumé en trois lignes (le fait, la conséquence, la dépendance). Il s'affiche seul quand le lecteur choisit « 2 min », dans « L'essentiel du jour » et dans les notifications. Donc chaque ligne :
- **se lit seule** : elle nomme qui ou quoi (« OVHcloud signale… »), jamais « il », « elle » ou « cela » en tête ;
- **tient en une phrase**, 140 caractères au plus ;
- **dit la même chose que l'article**, sans chiffre ou fait qui n'y serait pas.

### Les images

Elles viennent de la banque de photos par catégorie (`iris/assets/photos/`) : les mains pour l'IA et le logiciel, la borne d'arcade pour les jeux vidéo, l'antenne pour le réseau, etc. Jamais de logo, de produit de marque ni de personnage connu.

### Les quatre formats

| Format | Ce que c'est | Mention dans le tag |
|---|---|---|
| À chaud | Un fait de la semaine | Catégorie seule (« Réseau ») |
| Suite | Ce qu'on a appris depuis, par exemple un rapport d'incident publié après coup | « Suite · … » |
| Retour sur | Une histoire plus ancienne qui éclaire une dépendance d'aujourd'hui | « Retour sur · catégorie · mois année » |
| Bilan | Une semaine ou un mois résumé en une histoire | « Bilan · catégorie · semaine N » |

## 2. À la une : l'édition pour les entreprises

**Pour qui** : les dirigeants, DSI et responsables conformité qui dépendent de fournisseurs de cloud et d'IA.

**Rythme** : un sujet par jour, et un bilan chaque lundi.

**Les sujets**

- Un événement extérieur qui touche l'informatique : météo, incendie, coupure d'électricité ou de fibre, cyberattaque, erreur humaine.
- Les pannes et ralentissements des fournisseurs eux-mêmes.
- Les intermédiaires cachés, par exemple Cloudflare derrière Mistral.

**Les titres** sont factuels et racontent à distance, avec le contraste entre un fait banal et sa conséquence. Ils n'interpellent pas le lecteur (pas de « vous » dans le titre).

Exemples validés :
- « Une clim tombe en panne. Azure s'est tu <mark>47 minutes.</mark> »
- « Une mise à jour de routine. <mark>8,5 millions</mark> d'écrans bleus. »
- « Une pelleteuse coupe une fibre. Tout le nord <mark>ralentit.</mark> »

**La structure**

1. **Le fait inattendu**
2. **La conséquence technologique**
3. **La dépendance révélée.** Si le sujet s'y prête, on la relie à DORA ou NIS2.

L'article se termine par l'encadré « Ce que la sonde a mesuré » :
- **en Standard**, une invitation à passer en Premium ;
- **en Premium**, l'effet sur les fournisseurs de l'entreprise : durée mesurée, avoir possible, déclaration à faire. Quand la sonde n'a rien vu, l'encadré dit seulement : « Aucune anomalie mesurée chez vos fournisseurs ».

**En une**, le grand titre affiche trois lignes courtes : Le fait, La conséquence, puis La dépendance (en Standard) ou Ce que la sonde a vu (en Premium).

**Iris est un média.** Iris ne se connecte pas aux systèmes de ses lecteurs : tout ce qui est « mesuré » l'est de l'extérieur, par la sonde, sur les fournisseurs qu'elle suit. On n'écrit jamais « chez vous » ou « vos services » comme si on connaissait le système du lecteur. Les chiffres sont indicatifs et toujours accompagnés du rappel : à vérifier avec son équipe informatique et ses fournisseurs.

**Sources des propositions** : les événements croisés avec les mesures de la sonde (alertes officielles, pages de statut, presse via GDELT). Le bilan du lundi s'appuie sur les sept derniers jours.

## 3. Tous connectés : l'édition grand public

**Pour qui** : tout le monde, sans connaissances techniques.

**Rythme** : 3 ou 4 sujets par semaine, plus le bon réflexe de la semaine.

**Les sujets** : tout ce qui passionne les gens. Pop culture (jeux vidéo, musique, cinéma, séries), phénomènes d'achat, faits de société, le monde. Pas de filtre par thème.

**Le test : trois questions, toutes obligatoires.**

1. **Quelle technologie lâche, sature, change les règles ou surprend ?** Elle doit être nommée dans les articles de presse : une appli, un compte, un réseau, une panne, un écran, un algorithme, un service en ligne. Si on doit la supposer ou l'ajouter nous-mêmes, le sujet ne passe pas.
2. **Beaucoup de gens l'ont-ils vu ou vécu cette semaine ?** Un sujet repris par la presse nationale, pas un fait local.
3. **Le « Et vous ? » révèle-t-il une dépendance que le lecteur n'avait pas vue ?** Pas une question plaquée sur n'importe quel sujet.

**Ce qui n'est jamais un sujet Iris**, même avec un « Et vous ? » possible :
- les faits divers criminels (cambriolage, agression, explosion de distributeur…) ;
- les affaires judiciaires ou politiques qui visent une personne nommée ;
- les sujets où la technologie n'est qu'un décor.

Exemples validés : GTA VI vendu sans disque (le jeu dépend d'un compte), la peluche que les robots achètent avant nous, l'Espagne privée de paiement pendant la panne géante.
Exemples écartés (21 novembre 2026) : le préfet soupçonné de fuites vers un parti (affaire politique, technologie inventée) ; deux distributeurs explosés dans la Drôme (fait divers, technologie en décor). Le second a donné un bon sujet une fois repris sous l'angle de fond : le recul des distributeurs et notre plan B en liquide, chiffres de la Banque de France à l'appui.

**Mieux vaut aucun article qu'un article hors ligne.** Si aucun sujet ne passe les trois questions, le rédacteur le dit et ne propose rien.

**Ce qui rend un article partageable**

1. Un sujet que tout le monde a vu cette semaine, publié dans les 48 heures après le pic.
2. Un titre qui retourne la situation, souvent une question. Ici, le titre peut interpeller le lecteur (« Est-il vraiment <mark>à vous ?</mark> », « Les robots <mark>achètent avant vous.</mark> »).
3. Un bon réflexe qu'on a envie d'envoyer à un proche.
4. Un titre qui ne promet jamais plus que l'article, et qui ne fait jamais peur.

**La structure**

1. **Le fait inattendu**
2. **La conséquence technologique**
3. **Et vous ?** : ce que ça change dans la vie du lecteur.

Puis : **Le bon réflexe** (3 conseils concrets, faisables tout de suite), les **sources**, et le pont « Vous êtes une entreprise ? » vers l'édition pro.

**Le ton** : simple, concret, sans jargon, sans faire peur. On ne parle jamais de « vos fournisseurs » : le lecteur n'a pas Iris. Les données de la sonde n'apparaissent pas ici.

**Deux angles pour un même événement** : quand un événement marche pour les deux éditions, on propose deux articles, l'histoire grand public ici et l'angle entreprise dans À la une, avec un lien de l'un à l'autre.

## 4. Le Détour : ailleurs dans les médias

**Pour qui** : les curieux qui veulent aller plus loin.

**Rythme** : deux sélections par semaine, le mardi et le vendredi. Le rédacteur propose 5 liens ; la rédaction garde ceux qu'elle valide (« liens à garder » dans le formulaire de publication, par exemple 1, 3, 4). Un épisode de « 24 h chez… » toutes les deux semaines, choisi à la main.

**Toujours frais** : un lien de moins de 3 jours porte le badge « Nouveau » ; un lien de plus de 30 jours disparaît ; la page en montre 9 au plus, le plus récent en grand. Un lien proposé n'est jamais reproposé.

**La sélection d'articles**

Chaque article est présenté par : le nom du média, une catégorie, le titre, et une seule phrase qui dit pourquoi le lire. Le lien mène directement au média ; on ne reproduit pas son contenu. On signale « (en anglais) » et « (payant) » à côté du titre quand c'est le cas.

Un article est retenu s'il :
- éclaire une dépendance à la technologie, et la phrase « pourquoi le lire » dit laquelle ;
- n'est ni politique, ni un fait divers (mêmes exclusions que Tous connectés) ;
- vient d'un média sérieux ;
- apprend quelque chose qu'Iris ne dit pas déjà.

On varie les formats : enquête, explication, vidéo, podcast.

**Médias de référence** (liste dans `config/redaction.yaml`, à ajuster) : Next, Numerama, Usbek & Rica, Pixels (Le Monde), Le Grand Continent, Reporterre, franceinfo, IT for Business, L'Usine Digitale, Ouest-France, Le Monde du Droit ; sources publiques et académiques : CNIL, CNRS Le journal ; en anglais, Rest of World, 404 Media, Ars Technica, The Register. Les médias généralistes ne sont lus que sur les sujets technologiques (liste de mots dans le même fichier).

**Le panier de la rédaction** (`redaction/panier.yaml`) : la rédaction y colle les liens qu'elle croise (veille, études, vidéos, rapports publics). Au Détour suivant, ils sont proposés en premier, avec leur phrase « pourquoi le lire » ; le rédacteur signale ceux qui sortent de la ligne éditoriale au lieu de les retenir. Un lien du panier n'est proposé qu'une fois. Les lignes marquées `pour: idee` ne sont jamais proposées automatiquement : c'est un pense-bête pour Iris Plus ou un « Retour sur ».

**La série « 24 h chez… »** : une journée, par écran interposé, dans une entreprise qui vit de l'IA. Elle est racontée à partir d'une vidéo ou d'un reportage public, toujours cité, avec la même structure en trois temps. Elle est choisie à la main par la rédaction.

## 5. Contrôles automatiques

Chaque brouillon est vérifié avant d'arriver en relecture. Les écarts sont signalés, jamais corrigés en silence :

- un seul `<mark>` dans le titre ;
- l'essentiel en 2 min (trois lignes) présent, une phrase par ligne, 140 caractères au plus, sans pronom en tête ;
- pas de « vous » dans un titre d'À la une ;
- le texte se termine par une question ;
- pas plus de 3 chiffres dans le corps de l'article ;
- au moins une source avec un lien ;
- 3 bons réflexes pour Tous connectés ;
- pas de point d'exclamation ;
- aucun passage recopié d'un article lu (12 mots identiques à la suite) ;
- les articles qui n'ont pas pu être lus sont listés ;
- titre périmé (« sort ce jeudi » publié un samedi) et sujet déjà en ligne : publication refusée sauf « forcer » ;
- points « à vérifier » laissés par le rédacteur : publication refusée sauf « forcer » ;
- **ligne éditoriale** : les articles de faits divers, de justice et de politique sont retirés de la liste avant le choix du sujet ; le rédacteur doit nommer la technologie en jeu et citer la phrase de l'article qui la montre ; un mot technologique du texte absent des articles lus est signalé. Une alerte « Ligne éditoriale » bloque la publication sauf « forcer ».

## 6. Et si… ? : réfléchir aux limites de la technologie (Iris Plus)

**Pour qui** : les abonnés d'Iris Plus, qui veulent prendre du recul.

**Rythme** : un sujet par mois, préparé le premier lundi. Les sujets sont dans `config/et-si.yaml` ; GitHub choisit celui qui colle le mieux à l'actualité (une panne mesurée par la sonde, ou des articles récents). Un sujet n'est jamais reproposé.

**L'esprit** : la série aide à réfléchir. Elle ne donne **aucun avis** et ne tranche pas à la place du lecteur. Elle part toujours de la vie connectée de tous les jours, et elle dit honnêtement où la technologie s'arrête : pas de promesse, pas d'enthousiasme pour la nouveauté.

**La structure, toujours la même :**

1. **Et si…** : la question, posée à partir d'un fait réel (une panne mesurée par la sonde, une annonce, un article récent).
2. **Ce qui existe déjà** : les faits, tous sourcés.
3. **Là où ça coince** : les limites concrètes (le matériel qu'il faut, la batterie, ce qui repasse par le cloud, ce qui reste une promesse).
4. **La vraie question** : deux à quatre questions ouvertes sur ce que ça change pour nous, ce qu'on y perd ou y gagne. **On ne répond pas à ces questions.**
5. **Le geste** : une chose simple à tester ou à faire.

**Le titre** est la question elle-même, terminée par un point d'interrogation.

**Les sources** : seulement des pages officielles (documentation d'un fournisseur, organisme public) et des médias reconnus. Un blog ou un guide commercial peut donner une piste, jamais un fait.

**Dans le temps** : six mois après, GitHub relit les sources de chaque sujet et dit ce qui a changé. Si un fait n'est plus vrai, la rédaction ajoute un encadré « Ce qui a changé depuis » plutôt que de laisser un article périmé en ligne.

**Contrôles propres à la série** : les 5 parties sont présentes ; le titre est une question ; chaque phrase de « La vraie question » finit par un point d'interrogation ; aucune formule d'avis (« il faut », « selon nous », « mieux vaut »…) ; aucun lien absent de la fiche ; au moins une source lue.

