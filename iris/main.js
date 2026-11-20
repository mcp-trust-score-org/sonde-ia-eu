/* =========================================================
   IRIS — plaquette : navigation et interactions
   Toutes les données ci-dessous sont des données de démo.
   ========================================================= */

/* ---------- Données fournisseurs (carte, dispo, tableau SLA) ----------
   s = sun | cloudsun | fog | rain | storm
   dx / dy = décalage de l'étiquette sur la carte, en % */
const PROVIDERS = [
  { name: "AWS · Dublin",       lat: 53.35, lon: -6.26, s: "sun",      txt: "Ensoleillé",                    sla: 99.99, mes: 99.94,  avoir: 440, dx: 4,   dy: -12 },
  { name: "Azure · Amsterdam",  lat: 52.37, lon: 4.9,   s: "storm",    txt: "Orage · ne répond plus",        sla: 99.9,  mes: 99.68,  avoir: 400, dx: 16,  dy: -13 },
  { name: "OVHcloud · Roubaix", lat: 50.69, lon: 3.17,  s: "fog",      txt: "Brouillard · +30 % de latence", sla: 99.95, mes: 99.97,  avoir: 0,   dx: -20, dy: 1 },
  { name: "AWS · Francfort",    lat: 50.11, lon: 8.68,  s: "sun",      txt: "Ensoleillé",                    sla: 99.99, mes: 100,    avoir: 0,   dx: 22,  dy: 5 },
  { name: "IONOS · Berlin",     lat: 52.52, lon: 13.4,  s: "cloudsun", txt: "Éclaircies · SLA non tenu",     sla: 99.95, mes: 99.89,  avoir: 400, dx: 20,  dy: -4 },
  { name: "Scaleway · Paris",   lat: 48.85, lon: 2.35,  s: "sun",      txt: "Grand soleil",                  sla: 99.9,  mes: 99.99,  avoir: 0,   dx: -22, dy: 12 },
  { name: "Mistral AI · Paris", lat: 48.6,  lon: 2.6,   s: "sun",      txt: "Grand soleil",                  sla: 99.9,  mes: 99.95,  avoir: 0,   dx: -19, dy: 23 },
  { name: "Google · Milan",     lat: 45.46, lon: 9.19,  s: "cloudsun", txt: "Éclaircies",                    sla: 99.9,  mes: 99.93,  avoir: 0,   dx: 21,  dy: 7 },
];
const pct = (v) => v.toLocaleString("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " %";

/* ---------- « Et chez nous, aujourd'hui ? » ----------
   Version collaborateurs de la météo : les outils du quotidien,
   sans SLA, sans montants, sans alertes. Données de démo, cohérentes avec Ma Météo. */
const TOOLS = [
  { name: "Messagerie", s: "sun", txt: "Tout fonctionne" },
  { name: "Visio", s: "sun", txt: "Tout fonctionne" },
  { name: "Portail client et intranet", s: "storm", txt: "Indisponible. L'équipe informatique est dessus, rien à faire de votre côté." },
  { name: "CRM", s: "fog", txt: "Un peu lent depuis ce matin" },
  { name: "Assistant IA interne", s: "sun", txt: "Tout fonctionne" },
  { name: "Stockage des fichiers", s: "sun", txt: "Tout fonctionne" },
];
function chezNousHTML() {
  return `<p class="impact-kicker">Et chez nous, aujourd'hui ?</p>
    <ul class="tools">${TOOLS.map((t) => `<li class="${t.s === "storm" ? "storm" : ""}"><svg class="wx"><use href="#wx-${t.s}"/></svg><b>${t.name}</b><span>${t.txt}</span></li>`).join("")}</ul>
    <a href="#meteo" class="read">→ <u>Voir la météo complète</u></a>`;
}
document.querySelectorAll("[data-chez-nous]").forEach((el) => (el.innerHTML = chezNousHTML()));

/* ---------- Articles d'À la une ----------
   Chaque histoire suit la ligne éditoriale en trois temps :
   le fait inattendu → la conséquence technologique → la dépendance révélée,
   puis se termine par « Quel impact chez moi ? » qui renvoie vers Ma Météo. */
const ARTICLES = {
  clim: {
    tag: "À la une", tagClass: "flag-red", img: "assets/une-statue.jpg", time: "6 min", demo: true,
    title: "Une clim tombe en panne.<br/>Azure s'est tu <mark>47 minutes.</mark>",
    chapo: "Un équipement aussi banal qu'un climatiseur a mis à l'arrêt une partie du cloud européen de Microsoft. Le statut officiel, lui, est resté vert pendant 31 minutes.",
    fait: ["À 14:12, un groupe de refroidissement tombe en panne dans un datacenter de la région d'Amsterdam.", "Rien d'exceptionnel : ce type d'équipement casse, se répare, et d'habitude personne n'en entend parler."],
    consequence: ["Quand la température monte dans les salles, les serveurs se protègent : ils ralentissent, puis s'arrêtent. Machines virtuelles, bases de données, API : tout ce qui est hébergé dans la zone devient injoignable, y compris les outils d'IA qui s'appuient dessus.", "Pendant 31 minutes, la page de statut officielle affiche pourtant « tout fonctionne ». Les premiers signaux viennent des utilisateurs, pas du fournisseur."],
    lien: ["Votre disponibilité dépend d'équipements que vous ne voyez pas, chez des fournisseurs qui notent eux-mêmes leur performance.", "Iris mesure de l'extérieur, en continu, et garde les preuves horodatées. C'est ce qui permet de décider vite, de réclamer son dû et de déclarer l'incident si nécessaire."],
    impact: {
      status: "Vous êtes concerné", level: "red",
      rows: [["Fournisseur touché", "Microsoft Azure · Amsterdam"], ["Durée mesurée", "47 min 34 s"], ["Vos services touchés", "2 sur 14"], ["Avoir estimé", "≈ 400 €"], ["Déclaration DORA", "À évaluer, rapport pré-rempli"]],
      ctas: [["#meteo", "Voir ma météo →", "btn-yellow"], ["#alertes", "Décider maintenant", "btn-outline"]],
    },
  },
  fibre: {
    tag: "Réseau", img: "assets/photos/reseau.jpg", time: "4 min", demo: true,
    title: "Une pelleteuse coupe une fibre.<br/>Tout le nord <mark>ralentit.</mark>",
    chapo: "Un chantier de voirie, un coup de godet, et des milliers d'utilisateurs voient leurs applications ramer. Rien n'est en panne. Tout est plus lent.",
    fait: ["Sur un chantier, une pelleteuse sectionne un câble de fibre optique enterré.", "Ce genre d'accident est courant : les réseaux passent sous nos rues, et les travaux aussi."],
    consequence: ["Le trafic se réoriente automatiquement par d'autres chemins, plus longs et plus chargés. Rien ne s'arrête, mais le temps de réponse grimpe.", "Pour une application métier ou un assistant d'IA, quelques centaines de millisecondes de plus suffisent à rendre l'usage pénible."],
    lien: ["Une lenteur n'apparaît presque jamais sur une page de statut. Iris compare les temps de réponse de vos fournisseurs à leur niveau habituel et signale l'écart avant que vos équipes ne s'en plaignent."],
    impact: {
      status: "Vous êtes peut-être concerné", level: "yellow",
      rows: [["Fournisseur à surveiller", "OVHcloud · Roubaix"], ["Latence", "+30 % depuis 6 h"], ["Panne", "Aucune"], ["Avoir", "Non : le SLA porte sur la disponibilité"], ["Action", "Rien pour l'instant, Iris surveille"]],
      ctas: [["#meteo", "Voir ma météo →", "btn-yellow"]],
    },
  },
  maj: {
    tag: "Retour sur · juillet 2024", img: "assets/photos/logiciel.jpg", time: "5 min", demo: false,
    title: "Une mise à jour de routine.<br/><mark>8,5 millions</mark> d'écrans bleus.",
    chapo: "En juillet 2024, un fichier de mise à jour d'un logiciel de sécurité a bloqué des millions d'ordinateurs Windows en quelques heures. Le rappel le plus spectaculaire de notre dépendance à un seul maillon.",
    fait: ["Le 19 juillet 2024, l'éditeur de cybersécurité CrowdStrike publie une mise à jour de contenu pour son agent Falcon.", "Une opération de routine, du genre qu'aucun dirigeant ne suit."],
    consequence: ["Le fichier est défectueux. Les ordinateurs Windows qui le reçoivent plantent et redémarrent en boucle : environ 8,5 millions de machines selon Microsoft.", "Compagnies aériennes, hôpitaux, banques, chaînes de télévision : pendant des heures, et des jours pour certains, l'activité s'arrête."],
    lien: ["Le maillon faible n'était ni le cloud ni le réseau, mais un logiciel présent partout. C'est précisément ce que DORA demande de cartographier : vos prestataires critiques, et ceux dont ils dépendent eux-mêmes.", "Plus de deux ans après, la question reste entière : savez-vous quels logiciels, chez vos fournisseurs, pourraient vous arrêter du jour au lendemain ?"],
    impact: {
      status: "Aucune anomalie mesurée chez vos fournisseurs", level: "green",
      rows: [["Fournisseurs surveillés", "8"], ["Incident logiciel en cours", "Aucun"], ["Registre d'informations", "À mettre à jour d'ici 12 jours"]],
      ctas: [["#meteo", "Voir ma météo →", "btn-yellow"], ["#alertes", "Mettre à jour le registre", "btn-outline"]],
    },
  },
  tempete: {
    tag: "Énergie", img: "assets/photos/energie.jpg", time: "3 min", demo: true,
    title: "Une tempête coupe le courant.<br/>Le secours <mark>tiendra-t-il ?</mark>",
    chapo: "Quand le réseau électrique tombe, un datacenter bascule sur ses batteries puis sur ses groupes électrogènes. En théorie.",
    fait: ["Une tempête traverse le nord de l'Europe et prive des milliers de foyers d'électricité.", "Les datacenters de la zone perdent eux aussi leur alimentation principale."],
    consequence: ["Les batteries prennent le relais quelques minutes, le temps que les groupes électrogènes démarrent. Si l'un d'eux démarre mal, ou si le carburant manque, des salles entières s'éteignent.", "Le scénario est rare. C'est aussi celui que les fournisseurs détaillent le moins."],
    lien: ["Iris place chacun de vos fournisseurs sur la carte. Quand un événement touche une zone, vous savez tout de suite lesquels sont exposés."],
    impact: {
      status: "Aucune anomalie mesurée chez vos fournisseurs", level: "green",
      rows: [["Fournisseurs dans la zone touchée", "0 sur 8"], ["Maintenance prévue", "AWS Dublin, samedi"]],
      ctas: [["#meteo", "Voir ma météo →", "btn-yellow"]],
    },
  },
  certificat: {
    tag: "À la une", tagClass: "flag-red", img: "assets/une-statue.jpg", time: "5 min", demo: true,
    title: "Un certificat expire à minuit.<br/>Mistral se tait <mark>2&nbsp;h&nbsp;10.</mark>",
    chapo: "Pas de cyberattaque, pas de panne matérielle : un fichier arrivé à sa date d'expiration a suffi à couper un service d'IA pendant toute une partie de la nuit.",
    fait: ["Un certificat de sécurité, le petit fichier qui permet d'établir une connexion chiffrée, arrive à expiration à minuit.", "Sa date était connue depuis un an. Personne ne l'avait inscrite au bon endroit."],
    consequence: ["À 0 h 00, les applications qui appellent l'API refusent la connexion : sans certificat valide, pas de communication chiffrée. Les assistants, chatbots et automatisations branchés dessus s'arrêtent net.", "Il faut 2 h 10 à l'équipe d'astreinte pour trouver la cause et déployer un nouveau certificat."],
    lien: ["La panne la plus bête est souvent la plus longue à diagnostiquer, parce que personne ne la cherche.", "Iris mesure la disponibilité nuit et jour, y compris quand vos équipes dorment, et garde la preuve de chaque minute perdue."],
    impact: {
      status: "Vous êtes concerné", level: "red",
      rows: [["Fournisseur touché", "Mistral AI · API"], ["Durée mesurée", "2 h 10 (0 h 00 → 2 h 10)"], ["Vos services touchés", "Assistant interne"], ["Engagement", "99,90 % : environ 43 min tolérées par mois"], ["Avoir estimé", "≈ 150 €"]],
      ctas: [["#meteo", "Voir ma météo →", "btn-yellow"], ["#indicateurs", "Récupérer cet avoir", "btn-outline"]],
    },
  },
  "azure-suite": {
    tag: "Suite", img: "assets/card-bureau.jpg", time: "4 min", demo: true,
    title: "Azure publie son rapport.<br/>La clim n'était <mark>pas seule.</mark>",
    chapo: "Vingt-quatre heures après la panne d'Amsterdam, le rapport d'incident est tombé. Il raconte une histoire plus longue que celle d'un climatiseur.",
    fait: ["Le rapport confirme la panne du groupe de refroidissement.", "Il révèle aussi que l'équipement de secours était en maintenance ce jour-là."],
    consequence: ["Avec le secours à l'arrêt, une seule défaillance suffisait. La bascule automatique n'a pas pu se faire, et les serveurs se sont arrêtés pour se protéger.", "Le rapport annonce 41 minutes d'interruption. Iris en a mesuré 47."],
    lien: ["Six minutes d'écart : c'est la différence entre ce que dit le fournisseur et ce que vivent vos utilisateurs.", "Pour une réclamation ou une déclaration DORA, c'est votre mesure qui compte. Celle d'Iris est horodatée."],
    impact: {
      status: "Votre dossier est prêt", level: "yellow",
      rows: [["Durée annoncée / mesurée", "41 min / 47 min"], ["Avoir", "≈ 400 €, réclamation prête"], ["Déclaration DORA", "Rapport pré-rempli, à valider"]],
      ctas: [["#meteo", "Voir ma météo →", "btn-yellow"], ["#rapports", "Ouvrir le rapport", "btn-outline"]],
    },
  },
  heure: {
    tag: "Logiciel", img: "assets/card-pieces.jpg", time: "3 min", demo: true,
    title: "L'heure d'hiver arrive.<br/>Une tâche tourne <mark>deux fois.</mark>",
    chapo: "Une heure qui existe deux fois dans la même nuit, et un traitement automatique qui ne sait pas compter.",
    fait: ["La nuit du passage à l'heure d'hiver, il est deux fois 2 h 30.", "Un rendez-vous banal du calendrier, que les serveurs gèrent… presque toujours."],
    consequence: ["Une tâche planifiée à 2 h 30 s'exécute deux fois. Chez un prestataire de paiement, cela suffit à prélever certains clients en double.", "Le service client découvre le problème le lundi matin."],
    lien: ["Ce type d'erreur ne fait tomber aucun serveur : aucune page de statut ne passe au rouge. Iris suit aussi les incidents déclarés et les anomalies de vos fournisseurs, pas seulement les pannes franches."],
    impact: {
      status: "Aucune anomalie mesurée chez vos fournisseurs", level: "green",
      rows: [["Prestataires de paiement surveillés", "Aucun pour l'instant"], ["Prochain changement d'heure", "28 mars 2027"]],
      ctas: [["#meteo", "Voir ma météo →", "btn-yellow"]],
    },
  },
  ecureuil: {
    tag: "Infrastructure", img: "assets/card-nuages.jpg", time: "3 min", demo: true,
    title: "Un écureuil grignote un câble.<br/>Une région <mark>bascule.</mark>",
    chapo: "Les rongeurs comptent parmi les causes de coupure les plus anciennes des réseaux électriques. Celui-ci a testé un plan de secours.",
    fait: ["Un écureuil s'attaque à un câble électrique près d'un poste d'alimentation.", "L'anecdote fait sourire. Les électriciens, beaucoup moins : c'est une cause de coupure bien connue."],
    consequence: ["Le datacenter voisin perd une de ses deux arrivées électriques et bascule sur la seconde. Pendant quelques secondes, des connexions sont coupées, puis tout repart."],
    lien: ["Un plan de secours qui fonctionne ne se voit pas, sauf si on mesure. Iris enregistre ces micro-coupures : elles signalent parfois une fragilité, et elles comptent dans vos SLA."],
    impact: {
      status: "Aucune anomalie mesurée chez vos fournisseurs", level: "green",
      rows: [["Fournisseurs dans la zone", "0 sur 8"], ["Micro-coupures mesurées ce mois", "3, toutes sous 1 minute"]],
      ctas: [["#meteo", "Voir ma météo →", "btn-yellow"]],
    },
  },
  gta: {
    audience: "public", tag: "Jeux vidéo", tagClass: "flag-cream", img: "assets/photos/jeux-video.jpg", time: "4 min",
    title: "GTA VI sort aujourd'hui.<br/>Est-il vraiment <mark>à vous ?</mark>",
    chapo: "GTA VI arrive enfin sur PS5 et Xbox Series, après des années d'attente et deux reports. Derrière la fête, une question que peu de joueurs se posent : qu'avez-vous acheté, au juste ?",
    fait: ["Grand Theft Auto VI sort ce 19 novembre 2026 sur PS5 et Xbox Series X|S. Annoncé d'abord pour 2025, il a été repoussé deux fois.", "Avant même le lancement, le jeu était en tête des ventes du PlayStation Store dans toutes les régions où il était en précommande."],
    consequence: ["Des millions de joueurs lancent le même jeu le même jour. Téléchargement, mises à jour, connexion au compte, mode en ligne : tout passe par des serveurs que personne ne voit.", "Les grands lancements mettent souvent ces infrastructures à rude épreuve. Pour le joueur, la partie commence parfois par une attente qui ne dépend pas de lui."],
    lien: ["Un jeu acheté en téléchargement est attaché à un compte et à une boutique en ligne. Si le compte est bloqué, ou si un service ferme un jour, l'accès peut disparaître avec lui.", "Même la version en boîte de GTA VI ne contient pas de disque, seulement un code de téléchargement.", "Ce n'est pas propre à GTA : c'est le cas de la plupart des films, livres et musiques achetés en ligne."],
    sources: [{ label: "Selectra : préchargement de GTA VI, version en boîte sans disque", url: "https://selectra.info/telecom/actualites/marche/gta-vi-prechargement-10-novembre-temps-box" }],
    reflexes: ["Activez la double authentification sur votre compte de jeu : c'est lui qui contient votre bibliothèque.", "Faites la liste de ce que vous possédez sur disque, et de ce qui dépend d'un compte.", "Le jour d'un gros lancement, téléchargez à l'avance ou en heures creuses."],
  },
  labubu: {
    audience: "public", tag: "Retour sur · Société · été 2025", tagClass: "flag-cream", img: "assets/photos/societe.jpg", time: "4 min",
    title: "Une peluche affole la planète.<br/>Les robots <mark>achètent avant vous.</mark>",
    chapo: "Les Labubu, petits monstres aux dents pointues vendus par le fabricant chinois Pop Mart, partent en quelques minutes à chaque sortie. Souvent pas dans les mains des fans.",
    fait: ["Une peluche porte-clés à l'air espiègle devient l'accessoire que tout le monde veut, des stars de la K-pop aux cours de récré.", "À chaque nouvelle série, files d'attente devant les boutiques et ruptures de stock en ligne. En Corée, Pop Mart a même suspendu ses ventes en magasin en juin 2025, après des bousculades entre clients."],
    consequence: ["Le site et l'application de Pop Mart ont cédé sous un afflux de visiteurs que l'entreprise n'avait pas prévu.", "Surtout, les revendeurs ne cliquent plus à la main : des robots surveillent les stocks et achètent automatiquement à la seconde où un produit apparaît. Comme le résume un revendeur : c'est devenu « des bots contre des bots »."],
    lien: ["Face à un script, un humain qui rafraîchit sa page part perdant. La pénurie profite alors à la revente à prix gonflé, et aux contrefaçons.", "Billets de concert, baskets, consoles : la même mécanique se répète pour chaque produit rare vendu en ligne."],
    reflexes: ["Achetez sur les canaux officiels : un prix trop beau cache souvent une contrefaçon.", "Méfiez-vous des liens « dernière chance » reçus par message : c'est un appât classique d'arnaque.", "Dans une file d'attente en ligne, rafraîchir sans arrêt ne fait pas gagner : ça peut même vous faire bloquer."],
  },
  blackout: {
    audience: "public", tag: "Retour sur · Énergie · avril 2025", tagClass: "flag-cream", img: "assets/photos/energie.jpg", time: "5 min",
    title: "L'Espagne s'éteint à 12 h 33.<br/>Plus moyen de <mark>payer son pain.</mark>",
    chapo: "Le 28 avril 2025, une panne d'électricité géante a plongé l'Espagne et le Portugal dans le noir. En quelques secondes, tout ce qui passe par un écran s'est arrêté.",
    fait: ["Lundi 28 avril 2025, 12 h 33. En cinq secondes, le réseau espagnol perd 15 gigawatts, environ 60 % de la consommation du moment.", "L'Espagne, le Portugal et quelques communes du sud de la France se retrouvent sans courant. Le retour à la normale prendra jusqu'au lendemain matin."],
    consequence: ["Trains et métros à l'arrêt, feux de circulation éteints, internet et réseau mobile intermittents.", "Et une surprise pour beaucoup : impossible de payer. Les terminaux de carte ne répondent plus, les distributeurs de billets non plus. Sans espèces, plus moyen d'acheter à manger."],
    lien: ["Nous avons rangé la radio, le liquide et le papier au fond d'un tiroir, parce que le téléphone fait tout. Le jour où il ne capte plus, il ne fait plus rien.", "Ce jour-là, à Barcelone, les radios à piles se sont arrachées dans les magasins."],
    reflexes: ["Gardez un peu d'argent liquide chez vous.", "Une radio à piles et une batterie externe chargée tiennent dans un tiroir.", "Notez sur papier quelques numéros importants : ils sont tous dans un téléphone qui peut s'éteindre."],
  },
  harper: {
    audience: "detour", tag: "24 h chez… · IA · Épisode 1", img: "assets/photos/ia.jpg", time: "6 min",
    title: "Ils font en un jour<br/>ce qui en prenait <mark>sept.</mark>",
    chapo: "Dans « 24 h chez… », Iris passe une journée, par écran interposé, dans une entreprise qui vit de l'IA. Premier épisode : Harper, un courtier en assurance soutenu par Y Combinator.",
    fait: ["Harper est une société de courtage en assurance pour les PME, fondée par Dakotah Rice et Tushar Nair et soutenue par l'accélérateur Y Combinator. Elle a levé 47 millions de dollars.", "Sa promesse : trouver une assurance professionnelle en un ou deux jours, là où le courtage traditionnel en demande cinq à sept. La plateforme met en relation les entreprises avec plus de 160 assureurs et gagne environ 1 000 clients par mois."],
    consequence: ["Une journée chez Harper, c'est un briefing commercial, une revue des ventes, la correction d'un bug dans l'analyse automatique des devis, et le déploiement d'agents vocaux d'IA.", "Ici, l'IA n'est pas un outil parmi d'autres : c'est la chaîne de production. Si le modèle qui lit les devis se trompe, ou si le fournisseur qui fait parler les agents tombe, c'est le cœur du métier qui s'arrête."],
    lien: ["Les entreprises « nées de l'IA » montrent en accéléré ce qui arrive à toutes les autres : chaque gain de vitesse ajoute un fournisseur dont on dépend.", "Dans votre quotidien, combien d'outils s'appuient déjà sur un modèle d'IA ? Résumé de réunion, tri des mails, aide à la rédaction : la liste s'allonge sans qu'on la voie."],
    source: { label: "« 24 Hours Inside a $47M YC AI-native Insurance Startup », chaîne Will Phillips, août 2026", url: "https://www.youtube.com/watch?v=5tjNU_hsERk" },
  },
  "22ans": {
    audience: "public", tag: "Jeux vidéo", tagClass: "flag-cream", img: "assets/photos/jeux-video.jpg", time: "3 min",
    title: "22 ans pour télécharger GTA VI.<br/>La fracture numérique <mark>en une capture.</mark>",
    chapo: "Une vidéo fait le tour des réseaux : un internaute camerounais montre l'écran de sa console, qui lui annonce 22 ans et 4 jours de téléchargement pour GTA VI. On rit. Puis on regarde le chiffre de plus près.",
    fait: ["Sur l'écran, la barre de progression affiche 0,001 Go téléchargé sur 209,758 Go, avec cette estimation : « 22 years 4 days left ». Relayée notamment par le média Ulyces, la vidéo cumule des milliers de réactions.", "L'estimation est calculée au tout début du téléchargement, elle exagère sans doute. Mais l'ordre de grandeur, lui, dit quelque chose de vrai."],
    consequence: ["GTA VI pèse plus de 200 Go, et même la version en boîte ne contient pas de disque, seulement un code : tout le monde doit télécharger le jeu en entier.", "Avec une bonne fibre, c'est l'affaire d'une soirée. Avec une connexion lente et chère, comme celle que décrit la presse camerounaise, ça devient presque impossible. Le jeu le plus attendu de la décennie n'est vraiment accessible qu'à ceux qui ont le bon réseau."],
    lien: ["Quand tout passe par le téléchargement, la qualité de votre connexion décide de ce à quoi vous avez accès : un jeu, mais aussi un cours en ligne, une démarche administrative, une consultation en visio.", "Chez vous, la question n'est peut-être pas 22 ans, mais 22 heures : combien de temps tiendriez-vous si votre box tombait en panne ?"],
    reflexes: ["Testez votre débit réel, en câble et en Wi-Fi : l'écart est souvent énorme.", "Pour les gros téléchargements, branchez la console en câble et lancez-les la nuit.", "Gardez le partage de connexion de votre téléphone en solution de secours, en surveillant votre forfait."],
    sources: [
      { label: "La vidéo, relayée par Ulyces (Instagram)", url: "https://www.instagram.com/ulyces.co/" },
      { label: "Selectra : préchargement de GTA VI et temps de téléchargement", url: "https://selectra.info/telecom/actualites/marche/gta-vi-prechargement-10-novembre-temps-box" },
      { label: "Le360 Afrique : au Cameroun, une connexion internet onéreuse et lente", url: "https://afrique.le360.ma/societe/cameroun-connexion-internet-onereuse-et-lente-on-telecharge-les-deboires-plutot-que-les-fichiers_HXCJBG2NANA3RGBUT3M2KOPQFY/" },
    ],
  },
};

function renderArticle(id) {
  const a = ARTICLES[id];
  const el = document.getElementById("article");
  if (!a || !el) return false;
  const paras = (arr) => arr.map((p) => `<p>${p}</p>`).join("");
  const pub = a.audience === "public" || a.audience === "detour";
  const backTo = a.audience === "public" ? ["#vies", "Tous connectés"] : a.audience === "detour" ? ["#detour", "Le Détour"] : ["#une", "À la une"];
  const visual = `<div class="art-img${a.img.includes("/photos/") ? " art-photo" : ""}" style="background-image:url('${a.img}')"></div>`;
  const ending = pub
    ? `${a.reflexes ? `<section class="impact impact-reflex">
        <p class="impact-kicker">Le bon réflexe</p>
        <ul class="reflexes">${a.reflexes.map((r) => `<li>${r}</li>`).join("")}</ul>
      </section>` : ""}
      ${(() => { const src = a.sources || (a.source ? [a.source] : []); return src.length ? `<div class="art-source"><b>${src.length > 1 ? "Sources" : "Source"}</b>${src.map((x) => `<a href="${x.url}" target="_blank" rel="noopener">${x.label} ↗</a>`).join("")}</div>` : ""; })()}
      ${a.audience === "public" ? `<a class="bridge" href="#une"><span>Vous êtes une entreprise ?</span><b>La même dépendance existe chez vos fournisseurs. Voir l'édition pro →</b></a>` : ""}`
    : `<section class="impact impact-${a.impact.level}" data-plan="premium">
        <p class="impact-kicker">Quel impact chez moi ?</p>
        <h2>${a.impact.status}</h2>
        <dl>${a.impact.rows.map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join("")}</dl>
        <div class="impact-ctas">${a.impact.ctas.map(([h, t, c]) => `<a href="${h}" class="btn ${c}">${t}</a>`).join("")}</div>
      </section>
      <section class="impact impact-teaser" data-plan="standard">
        <p class="impact-kicker">Quel impact chez moi ?</p>
        <h2>Vos fournisseurs sont-ils concernés ?</h2>
        <p class="teaser-txt">Avec Iris Premium, vos fournisseurs sont surveillés en continu. Vous savez en un coup d'œil si vous êtes touché, ce que ça vous coûte, et vous avez les preuves pour réclamer ou déclarer.</p>
        <div class="impact-ctas"><button type="button" class="btn btn-yellow" data-set-plan="premium">★ Découvrir Premium</button></div>
      </section>`;
  el.innerHTML = `
    <a href="${backTo[0]}" class="back">← ${backTo[1]}</a>
    <header class="art-head">
      <span class="flag ${a.tagClass || ""}">${a.tag}</span>
      <h1 class="display art-title">${a.title}</h1>
      <p class="art-chapo">${a.chapo}</p>
      <p class="art-meta">${a.time} de lecture${a.audience === "public" ? " · Édition grand public" : ""}${a.demo ? " · Article de démonstration" : ""}</p>
    </header>
    ${visual}
    <div class="art-body">
      <section class="step"><span class="step-n">01</span><div><h2>Le fait inattendu</h2>${paras(a.fait)}</div></section>
      <section class="step"><span class="step-n">02</span><div><h2>La conséquence technologique</h2>${paras(a.consequence)}</div></section>
      <section class="step"><span class="step-n">03</span><div><h2>${pub ? "Et vous ?" : "La dépendance révélée"}</h2>${paras(a.lien)}</div></section>
      ${ending}
    </div>`;
  return true;
}

/* ---------- Même hauteur de une pour toutes les éditions ----------
   L'illustration est cadrée en « cover » : à hauteur égale, elle est identique d'un jour à l'autre. */
function equalizeHeroes() {
  const heroes = [...document.querySelectorAll("#view-une .day .une-hero")];
  if (!heroes.length || window.matchMedia("(max-width: 720px)").matches) { heroes.forEach((h) => (h.style.minHeight = "")); return; }
  const days = [...document.querySelectorAll("#view-une .day")];
  const view = document.getElementById("view-une");
  const wasActive = view.classList.contains("active");
  const state = days.map((d) => d.hidden);
  view.style.cssText = wasActive ? "" : "display:block;visibility:hidden;position:absolute;left:-9999px;width:" + document.querySelector("main").clientWidth + "px";
  days.forEach((d) => { d.hidden = false; });
  heroes.forEach((h) => (h.style.minHeight = ""));
  const max = Math.max(...heroes.map((h) => h.getBoundingClientRect().height));
  heroes.forEach((h) => (h.style.minHeight = max + "px"));
  days.forEach((d, i) => { d.hidden = state[i]; });
  view.style.cssText = "";
}
window.addEventListener("resize", equalizeHeroes);
if (document.fonts && document.fonts.ready) document.fonts.ready.then(equalizeHeroes);
equalizeHeroes();

/* ---------- Édition du jour (sélecteur Jeu. / Ven.) ---------- */
(function daySwitch() {
  const sw = document.querySelector(".day-switch");
  if (!sw) return;
  sw.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    sw.querySelectorAll("button").forEach((x) => x.classList.toggle("on", x === b));
    document.querySelectorAll(".day").forEach((d) => (d.hidden = d.dataset.day !== b.dataset.day));
  });
})();


/* ---------- Les articles les plus lus (encart latéral) ---------- */
const MOST_READ = {
  pro: ["clim", "maj", "fibre"],
  public: ["gta", "22ans", "blackout"],
};
document.querySelectorAll("[data-most-read]").forEach((el) => {
  const ids = MOST_READ[el.dataset.mostRead] || [];
  el.innerHTML = `<p class="mr-title">Les articles les plus <span class="nowrap">lus<i class="mr-dot" aria-hidden="true"></i></span></p><ol class="mr-list">${ids.filter((id) => ARTICLES[id]).map((id) => {
    const a = ARTICLES[id];
    const t = a.title.replace(/<[^>]+>/g, " ").replace(/&nbsp;/g, " ").replace(/\s+/g, " ").trim();
    return `<li><a href="#article-${id}"><span class="mr-tag">${a.tag}</span><span class="mr-t">${t}</span><span class="mr-time">${a.time} de lecture</span></a></li>`;
  }).join("")}</ol>`;
});

/* ---------- Le Détour : sélection d'articles d'autres médias ---------- */
const EXTERNAL = [
  { source: "Next", cat: "Réseau", img: "reseau", title: "GTA VI peut-il casser Internet ?", why: "Ce que 200 Go téléchargés en même temps font aux réseaux.", url: "https://next.ink/265265/gta-vi-peut-il-casser-internet/" },
  { source: "Le Grand Continent", cat: "Énergie", img: "energie", title: "Comprendre la panne d'électricité en Espagne et au Portugal", why: "Le décryptage du blackout du 28 avril 2025.", url: "https://legrandcontinent.eu/fr/2025/04/28/comprendre-la-panne-delectricite-en-espagne-et-au-portugal/" },
  { source: "Reporterre", cat: "Société", img: "societe", title: "Panne géante en Espagne : 12 heures sans électricité", why: "Le récit d'une journée où plus rien ne passait par un écran.", url: "https://reporterre.net/Panne-geante-en-Espagne-pendant-12-heures-j-ai-vecu-sans-electricite" },
  { source: "Le360 Afrique", cat: "Réseau", img: "savoir", title: "Cameroun : une connexion internet chère et lente", why: "La fracture numérique, vue de l'intérieur.", url: "https://afrique.le360.ma/societe/cameroun-connexion-internet-onereuse-et-lente-on-telecharge-les-deboires-plutot-que-les-fichiers_HXCJBG2NANA3RGBUT3M2KOPQFY/" },
  { source: "Selectra", cat: "Jeux vidéo", img: "jeux-video", title: "GTA VI : combien de temps pour le télécharger ?", why: "Le calcul selon votre box, et pourquoi la boîte ne contient pas de disque.", url: "https://selectra.info/telecom/actualites/marche/gta-vi-prechargement-10-novembre-temps-box" },
  { source: "404 Media", cat: "Média à suivre", img: "innovation", title: "Un média tech indépendant, fondé par des journalistes", why: "Leurs enquêtes sur les coulisses de la tech (en anglais).", url: "https://404media.co/about" },
];
(function renderExternal() {
  const el = document.getElementById("ext-grid");
  if (!el) return;
  el.innerHTML = EXTERNAL.map((x) => `<a class="ext-card" href="${x.url}" target="_blank" rel="noopener">
      <div class="ext-img" style="background-image:url('assets/photos/${x.img}.jpg')"></div>
      <div class="ext-body"><span class="ext-src">${x.source} ↗</span><span class="pc-tag">${x.cat}</span><h3>${x.title}</h3><p>${x.why}</p></div>
    </a>`).join("");
})();

/* ---------- Type de compte (démo) ----------
   Standard : pas de données fournisseurs, donc aucune affirmation « chez vous ».
   Premium : Ma Météo activée, le lecteur voit l'impact chez lui. */
function setPlan(plan) {
  document.body.dataset.plan = plan;
  document.querySelectorAll("[data-set-plan]").forEach((b) => b.classList.toggle("on", b.dataset.setPlan === plan && b.closest(".plan-switch")));
  try { localStorage.setItem("iris-plan", plan); } catch (e) {}
}
document.addEventListener("click", (e) => {
  const b = e.target.closest("[data-set-plan]");
  if (b) setPlan(b.dataset.setPlan);
});
let savedPlan = "standard";
try { savedPlan = localStorage.getItem("iris-plan") || "standard"; } catch (e) {}
setPlan(savedPlan);

/* ---------- Navigation par onglets (hash) ---------- */
const VIEWS = ["une", "vies", "meteo", "alertes", "indicateurs", "detour", "rapports"];
function show(hash) {
  let view = hash, tab = hash;
  if (hash.startsWith("article-") && renderArticle(hash.slice(8))) {
    view = "article";
    const aud = ARTICLES[hash.slice(8)].audience;
    tab = aud === "public" ? "vies" : aud === "detour" ? "detour" : "une";
  }
  else if (!VIEWS.includes(hash)) { view = tab = "une"; }
  document.querySelectorAll(".view").forEach((v) => v.classList.toggle("active", v.dataset.view === view));
  document.querySelectorAll(".tabs a").forEach((a) => a.classList.toggle("active", a.dataset.view === tab));
  const t = document.querySelector(`.tabs a[data-view="${tab}"]`);
  if (t) t.scrollIntoView({ block: "nearest", inline: "center" });
  window.scrollTo(0, 0);
}
window.addEventListener("hashchange", () => show(location.hash.slice(1)));

/* ---------- Date du jour ---------- */
(function setDate() {
  const el = document.getElementById("meteo-date");
  if (!el) return;
  const d = new Date();
  const jour = d.toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long" });
  const h = d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" }).replace(":", "h");
  el.textContent = `${jour.charAt(0).toUpperCase() + jour.slice(1)} · ${h} · en temps réel`;
})();

/* ---------- Carte météo ----------
   Projection identique à celle de assets/europe-dots.svg
   (lon -12→32, lat 35→62, 20 px par degré de latitude). */
const MAP = { lon0: -12, lat1: 62, kx: 13.3826, ky: 20, w: 588.83, h: 540 };
const project = (lat, lon) => ({
  x: ((lon - MAP.lon0) * MAP.kx) / MAP.w * 100,
  y: ((MAP.lat1 - lat) * MAP.ky) / MAP.h * 100,
});

(function drawMap() {
  const map = document.getElementById("meteo-map");
  if (!map) return;
  const NS = "http://www.w3.org/2000/svg";
  const lines = document.createElementNS(NS, "svg");
  lines.setAttribute("class", "wx-line");
  lines.setAttribute("viewBox", "0 0 100 100");
  lines.setAttribute("preserveAspectRatio", "none");
  map.appendChild(lines);

  PROVIDERS.forEach((p) => {
    const { x, y } = project(p.lat, p.lon);
    const pin = document.createElement("span");
    pin.className = `pin s-${p.s}`;
    pin.style.left = `${x}%`; pin.style.top = `${y}%`;
    pin.title = p.name;
    map.appendChild(pin);

    const cx = x + p.dx, cy = y + p.dy;
    const l = document.createElementNS(NS, "line");
    l.setAttribute("x1", x); l.setAttribute("y1", y); l.setAttribute("x2", cx); l.setAttribute("y2", cy);
    l.setAttribute("vector-effect", "non-scaling-stroke");
    lines.appendChild(l);

    const card = document.createElement("div");
    card.className = `wx-card${p.s === "storm" ? " storm" : ""}`;
    card.style.left = `${cx}%`; card.style.top = `${cy}%`;
    card.innerHTML = `<svg class="wx"><use href="#wx-${p.s}"/></svg><div><b>${p.name}</b><span>${p.txt}</span></div>`;
    map.appendChild(card);
  });

  // Liste (remplace les étiquettes sur mobile)
  const list = document.createElement("ul");
  list.className = "wx-list";
  list.innerHTML = PROVIDERS.map((p) =>
    `<li class="${p.s === "storm" ? "storm" : ""}"><svg class="wx"><use href="#wx-${p.s}"/></svg><b>${p.name}</b><span>${p.txt}</span></li>`
  ).join("");
  map.after(list);
})();

/* ---------- Disponibilité vs SLA (barres) ---------- */
(function drawDispo() {
  const ul = document.getElementById("dispo");
  if (!ul) return;
  const MIN = 99.5, MAX = 100;
  const pos = (v) => Math.max(0, Math.min(100, ((v - MIN) / (MAX - MIN)) * 100));
  ul.innerHTML = PROVIDERS.map((p) => {
    const ko = p.mes < p.sla;
    return `<li><span>${p.name}</span>
      <span class="track" title="SLA ${pct(p.sla)} · mesuré ${pct(p.mes)}">
        <span class="fill${ko ? " ko" : ""}" style="width:${pos(p.mes)}%"></span>
        <span class="tick" style="left:${pos(p.sla)}%"></span>
      </span><b>${pct(p.mes)}</b></li>`;
  }).join("");
  ul.insertAdjacentHTML("afterend", `<p class="dispo-note">Trait blanc = SLA promis. Rouge = engagement non tenu, avoir réclamable. Échelle 99,5 → 100 %.</p>`);
})();

/* ---------- Tableau SLA (Indicateurs) ---------- */
(function drawSla() {
  const tb = document.getElementById("sla-body");
  if (!tb) return;
  const rows = [...PROVIDERS].sort((a, b) => b.avoir - a.avoir);
  tb.innerHTML = rows.map((p) => {
    const ecart = p.mes - p.sla;
    const ko = ecart < 0;
    const e = (ecart >= 0 ? "+" : "−") + Math.abs(ecart).toLocaleString("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " pt";
    return `<tr>
      <td>${p.name}</td><td>${pct(p.sla)}</td><td>${pct(p.mes)}</td>
      <td class="${ko ? "ko" : "ok"}">${e}</td>
      <td class="${p.avoir ? "money" : "ok"}">${p.avoir ? "≈ " + p.avoir + " €" : "—"}</td>
      <td>${p.avoir ? `<a href="#rapports" class="btn btn-yellow">Réclamer</a>` : ""}</td></tr>`;
  }).join("");
})();

/* ---------- Filtres (Alertes, Rapports) ---------- */
document.querySelectorAll("[data-filter-group]").forEach((group) => {
  const scope = group.closest(".view");
  group.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    group.querySelectorAll("button").forEach((x) => x.classList.toggle("on", x === b));
    const f = b.dataset.f;
    scope.querySelectorAll("[data-cat]").forEach((item) => item.classList.toggle("is-hidden", f !== "all" && item.dataset.cat !== f));
  });
});

/* ---------- Minuteur de l'alerte en cours ---------- */
(function ticker() {
  const el = document.getElementById("since");
  if (!el) return;
  let m = 47;
  setInterval(() => { m += 1; el.textContent = m; }, 60000);
})();

/* ---------- Toast ---------- */
const toastEl = document.getElementById("toast");
let toastT;
function toast(msg) {
  toastEl.textContent = msg;
  toastEl.classList.add("show");
  clearTimeout(toastT);
  toastT = setTimeout(() => toastEl.classList.remove("show"), 2600);
}
document.addEventListener("click", (e) => {
  const t = e.target.closest("[data-toast]");
  if (t) toast(t.dataset.toast);
});

/* ---------- Talk to my data (tiroir + démo scriptée) ---------- */
const drawer = document.getElementById("drawer");
const scrim = document.querySelector(".scrim");
const openChat = () => { drawer.classList.add("open"); scrim.classList.add("open"); drawer.setAttribute("aria-hidden", "false"); setTimeout(() => document.getElementById("chat-text").focus(), 300); };
const closeChat = () => { drawer.classList.remove("open"); scrim.classList.remove("open"); drawer.setAttribute("aria-hidden", "true"); };
document.querySelectorAll("[data-open-chat]").forEach((b) => b.addEventListener("click", openChat));
document.querySelectorAll("[data-close-chat]").forEach((b) => b.addEventListener("click", closeChat));
document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeChat(); });

const ANSWERS = [
  "Ce trimestre, <b>Microsoft Azure</b> vous a coûté <b>212 minutes</b> d'indisponibilité, dont 47 mardi. Viennent ensuite OVHcloud (38 min) et IONOS (31 min).",
  "Votre contrat Azure promet <b>99,90 %</b>, j'ai mesuré <b>99,68 %</b> ce mois-ci. Vous pouvez réclamer <b>environ 400 €</b>. Le dossier de preuves est prêt dans Rapports.",
  "Presque. <b>92 %</b> des exigences suivies sont couvertes. Il reste un point : votre <b>registre d'informations</b> doit être mis à jour d'ici 12 jours. Je peux le pré-remplir.",
];
const FALLBACK = "Dans la version complète, je réponds à partir de vos mesures et de vos contrats. Essayez une des questions proposées.";

(function chat() {
  const log = document.getElementById("chat-log");
  const chips = document.getElementById("chat-chips");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-text");
  const push = (html, who) => {
    const m = document.createElement("div");
    m.className = `msg msg-${who}`;
    m.innerHTML = html;
    log.appendChild(m);
    log.scrollTop = log.scrollHeight;
    return m;
  };
  const ask = (q, answer) => {
    push(q.replace(/</g, "&lt;"), "me");
    const t = push("Iris analyse vos données…", "iris");
    t.classList.add("typing");
    setTimeout(() => { t.classList.remove("typing"); t.innerHTML = answer; log.scrollTop = log.scrollHeight; }, 900);
  };
  chips.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (b) ask(b.textContent, ANSWERS[+b.dataset.q]);
  });
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const q = input.value.trim();
    if (!q) return;
    const low = q.toLowerCase();
    let a = FALLBACK;
    if (/minute|coût|panne|incident/.test(low)) a = ANSWERS[0];
    else if (/réclam|avoir|rembours|argent|€/.test(low)) a = ANSWERS[1];
    else if (/dora|nis2|conform|contrôle|audit/.test(low)) a = ANSWERS[2];
    ask(q, a);
    input.value = "";
  });
})();

show(location.hash.slice(1));
