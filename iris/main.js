/* =========================================================
   IRIS — plaquette : navigation et interactions
   Toutes les données ci-dessous sont des données de démo.
   ========================================================= */

/* ---------- Données fournisseurs (carte, dispo, tableau SLA) ----------
   s = sun | cloudsun | fog | rain | storm
   dx / dy = décalage de l'étiquette sur la carte, en % */


/* ---------- Articles d'À la une ----------
   Chaque histoire suit la ligne éditoriale en trois temps :
   le fait inattendu → la conséquence technologique → la dépendance révélée,
   puis se termine par « Quel impact chez moi ? » qui renvoie vers Ma Météo. */
const ARTICLES = {
  maj: {
    tag: "Retour sur · juillet 2024", img: "assets/photos/logiciel.jpg", time: "5 min", demo: false,
    title: "Une mise à jour de routine.<br/><mark>8,5 millions</mark> d'écrans bleus.",
    chapo: "En juillet 2024, un fichier de mise à jour d'un logiciel de sécurité a bloqué des millions d'ordinateurs Windows en quelques heures. Le rappel le plus spectaculaire de notre dépendance à un seul maillon.",
    fait: ["Le 19 juillet 2024, l'éditeur de cybersécurité CrowdStrike publie une mise à jour de contenu pour son agent Falcon.", "Une opération de routine, du genre qu'aucun dirigeant ne suit."],
    consequence: ["Le fichier est défectueux. Les ordinateurs Windows qui le reçoivent plantent et redémarrent en boucle : environ 8,5 millions de machines selon Microsoft.", "Compagnies aériennes, hôpitaux, banques, chaînes de télévision : pendant des heures, et des jours pour certains, l'activité s'arrête."],
    lien: ["Le maillon faible n'était ni le cloud ni le réseau, mais un logiciel présent partout. C'est précisément ce que DORA demande de cartographier : vos prestataires critiques, et ceux dont ils dépendent eux-mêmes.", "Plus de deux ans après, la question reste entière : savez-vous quels logiciels, chez vos fournisseurs, pourraient vous arrêter du jour au lendemain ?"],
    impact: {
      status: "Aucune anomalie mesurée chez les fournisseurs suivis", level: "green",
      confidence: { level: "non", lieu: false, moment: false, symptome: false, officiel: false },
      rows: [["Fournisseurs surveillés", "8"], ["Incident logiciel en cours", "Aucun"], ["Registre d'informations", "À mettre à jour d'ici 12 jours"]],
      ctas: [["#meteo", "Voir ma météo →", "btn-yellow"], ["#alertes", "Mettre à jour le registre", "btn-outline"]],
    },
  },
  ovh: {
    tag: "À la une", tagClass: "flag-red", img: "assets/photos/ia.jpg", time: "4 min", demo: false,
    title: "Un matin comme les autres.<br/>Une IA <mark>14 fois</mark> plus lente.",
    chapo: "Ce vendredi, le modèle d'IA qu'OVHcloud loue aux entreprises s'est mis à hésiter longuement avant chaque réponse. Pas d'écran noir, pas d'alerte : juste une attente. C'est souvent comme ça que commence une panne d'IA.",
    fait: ["Tôt le matin, OVHcloud signale un incident sur son service d'intelligence artificielle, celui qui fait tourner des modèles pour des milliers d'entreprises françaises.", "Un message discret, sur une page de statut que presque personne ne consulte."],
    consequence: ["Au même moment, notre sonde interroge le modèle Llama. D'habitude, il répond presque instantanément. Là, il fait attendre ses utilisateurs de longues secondes, parfois plus de deux minutes.", "Les autres modèles du même hébergeur répondent normalement. La panne ne touche qu'un rouage, mais il suffit : chatbot de service client, assistant interne, outil de rédaction… tout ce qui repose sur ce modèle se fige."],
    lien: ["On choisit un hébergeur français pour garder la main sur ses données. On oublie qu'on dépend aussi d'un modèle précis, et qu'il n'existe souvent aucun plan B.", "Si votre IA ralentissait demain matin, combien de temps faudrait-il avant que quelqu'un s'en aperçoive ?"],
    sources: [{ label: "OVHcloud : page de statut, incident AI Endpoints du 20 novembre 2026", url: "https://stspg.io/vlkf6x66jncd" }],
    impact: {
      status: "Un fournisseur suivi a été touché", level: "red",
      confidence: { level: "confirme", lieu: true, moment: true, symptome: true, officiel: true },
      rows: [["Fournisseur touché", "OVHcloud · AI Endpoints"], ["Modèle touché", "Llama 3.3 70B"], ["Mesuré à 9 h", "16,7 s avant le premier mot, contre 1,2 s d'habitude"], ["Incident officiel", "De 7 h 53 à 13 h 19"], ["Avoir", "Aucun : pas d'engagement de service sur cette offre"]],
      ctas: [["#meteo", "Voir ma météo →", "btn-yellow"], ["#alertes", "Prévoir un modèle de secours", "btn-outline"]],
    },
  },
  cloudflare: {
    tag: "Bilan · Réseau · semaine 47", img: "assets/photos/reseau.jpg", time: "4 min", demo: false,
    title: "Une semaine ordinaire sur Internet.<br/><mark>32 incidents</mark> chez un seul acteur.",
    chapo: "Cette semaine, Cloudflare, l'entreprise américaine qui transporte une large part du web, a signalé des incidents presque tous les jours. La plupart se sont produits loin d'ici. L'un d'eux, à Paris, rappelle un détail que peu d'entreprises connaissent : l'IA de Mistral passe par Cloudflare.",
    fait: ["Dans la nuit de mardi à mercredi, Cloudflare signale un ralentissement de son réseau parisien. Une heure plus tard, tout est rentré dans l'ordre.", "Le genre d'incident qui ne fait jamais la une."],
    consequence: ["Cloudflare se place entre les internautes et des milliers de services. Quand l'un de ses points de passage ralentit, tout ce qui transite par lui ralentit aussi.", "En traçant le chemin des requêtes vers Mistral, notre sonde a découvert qu'elles passaient par Cloudflare. Cette nuit-là, elle était entre deux relevés : impossible de dire si Mistral a été touché. Mais il pouvait l'être."],
    lien: ["Choisir une IA européenne ne suffit pas pour être indépendant. Entre vous et elle, il y a des intermédiaires que vous n'avez pas choisis, et avec qui vous n'avez signé aucun contrat. C'est précisément ce que DORA demande de cartographier : vos prestataires critiques, et ceux dont ils dépendent eux-mêmes.", "Savez-vous par où passent vos requêtes avant d'arriver à votre IA ?"],
    sources: [{ label: "Cloudflare : page de statut, incident réseau à Paris du 18 novembre 2026", url: "https://www.cloudflarestatus.com/incidents/k3r9i5tbre4i" }],
    impact: {
      status: "Aucune anomalie mesurée chez les fournisseurs suivis", level: "green",
      confidence: { level: "non", lieu: true, moment: false, symptome: false, officiel: false },
      rows: [["Intermédiaire découvert", "Mistral AI passe par Cloudflare"], ["Incidents Cloudflare cette semaine", "32, dont 4 en Europe ou sur tout le réseau"], ["Mesure pendant l'incident de Paris", "Aucune : entre deux relevés"], ["Registre d'informations", "Ajouter Cloudflare comme sous-traitant de Mistral"]],
      ctas: [["#meteo", "Voir ma météo →", "btn-yellow"], ["#rapports", "Mettre à jour le registre", "btn-outline"]],
    },
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
};

/* ---------- Tag de relecture ----------
   Calculé par la sonde (voir regles-de-gestion/). Il n'est JAMAIS affiché sur le site :
   il n'apparaît que dans l'écran de relecture (#relecture), pour décider de publier ou non. */
const TAG_LABELS = { confirme: "Confirmé", probable: "Probable", possible: "Possible", non: "Aucune anomalie" };

/* ---------- En bas d'un article : les fournisseurs suivis par Iris qu'il mentionne ----------
   Premium : leur état mesuré et un accès direct à Ma Météo, Alertes et Indicateurs.
   Standard : la même proposition, avec l'invitation à passer en Premium. */
const RAPPEL = "À titre indicatif : mesures externes et automatisées, à vérifier avec votre équipe informatique et vos fournisseurs.";
const LIENS_PREMIUM = `<a href="#meteo" class="btn btn-yellow">Ma Météo →</a><a href="#alertes" class="btn btn-outline">Alertes</a><a href="#indicateurs" class="btn btn-outline">Indicateurs</a>`;
const SUIVIS = [
  { id: "mistral", nom: "Mistral AI", motif: /\bmistral\b/i },
  { id: "scaleway", nom: "Scaleway", motif: /\bscaleway\b/i },
  { id: "ovhcloud", nom: "OVHcloud", motif: /\bovh(cloud)?\b/i },
  { id: "ionos", nom: "IONOS", motif: /\bionos\b/i },
];
let IRIS_METEO = null;   // rempli quand donnees/meteo.json arrive
function suiviFournisseurs(a) {
  const texte = [a.title, a.chapo, ...(a.fait || []), ...(a.consequence || []), ...(a.lien || [])].join(" ").replace(/<[^>]+>/g, " ");
  const cites = SUIVIS.filter((f) => f.motif.test(texte));
  if (!cites.length) return null;
  const noms = cites.map((f) => f.nom).join(", ").replace(/, ([^,]*)$/, " et $1");
  const etat = (f) => {
    const m = ((IRIS_METEO && IRIS_METEO.fournisseurs) || []).find((x) => x.id === f.id);
    if (!m) return `<li><b>${f.nom}</b><span>suivi heure par heure</span></li>`;
    const ic = { soleil: "sun", eclaircie: "cloudsun", nuage: "fog", orage: "storm" }[m.etat] || "unknown";
    return `<li class="${m.etat === "orage" ? "storm" : ""}"><svg class="wx"><use href="#wx-${ic}"/></svg><b>${f.nom}</b><span>${m.libelle}${m.ttft_ms ? " · " + m.ttft_ms.toLocaleString("fr-FR") + " ms" : ""}</span></li>`;
  };
  return {
    premium: `<section class="impact impact-suivi" data-plan="premium">
        <p class="impact-kicker">Suivre ${noms}</p>
        <h2>Ce que la sonde mesure en ce moment</h2>
        <ul class="tools">${cites.map(etat).join("")}</ul>
        <p class="impact-note">${RAPPEL}</p>
        <div class="impact-ctas">${LIENS_PREMIUM}</div>
      </section>`,
    standard: `<section class="impact impact-teaser" data-plan="standard">
        <p class="impact-kicker">Suivre ${noms}</p>
        <h2>${cites.length > 1 ? "Ces fournisseurs sont suivis" : "Ce fournisseur est suivi"} heure par heure par Iris</h2>
        <p class="teaser-txt">Avec Iris Premium : ${cites.length > 1 ? "leur" : "sa"} météo en direct, ${cites.length > 1 ? "leurs" : "ses"} alertes de panne et de lenteur, ${cites.length > 1 ? "leurs" : "ses"} engagements de disponibilité tenus ou non, et les preuves.</p>
        <div class="impact-ctas"><button type="button" class="btn btn-yellow" data-set-plan="premium">★ Passer en Premium</button></div>
      </section>`,
  };
}

// Le bon réflexe : le début de chaque geste en gras (« Comparez les prix » des versions…), comme sur la maquette.
// Jusqu'à la première virgule si elle arrive tôt, sinon les trois premiers mots. Déjà du gras dans le texte : on n'y touche pas.
function debutGras(r) {
  if (/<b>|<strong>/.test(r)) return r;
  const virgule = r.indexOf(",");
  if (virgule > 0 && r.slice(0, virgule).split(/\s+/).length <= 6) return `<b>${r.slice(0, virgule)}</b>${r.slice(virgule)}`;
  const mots = r.split(" ");
  return mots.length > 4 ? `<b>${mots.slice(0, 3).join(" ")}</b> ${mots.slice(3).join(" ")}` : r;
}

/* ---------- Temps de lecture : « 2 min » (l'essentiel) ou l'article en entier ----------
   Réglage dans la cloche : « Me laisser choisir » (par défaut), « Toujours 2 min », « Toujours en entier ».
   Il reste sur l'appareil (localStorage) : Iris ne sait rien du lecteur.
   Une notification ouvre l'article avec ?lecture=2, ?lecture=10 ou ?lecture=notif (= selon le réglage, sinon 2 min). */
const DUREE_CLE = "iris-duree";
const lireDuree = () => { try { return localStorage.getItem(DUREE_CLE) || "choisir"; } catch (e) { return "choisir"; } };
let MODE_DEMANDE = null;
(function lectureDepuisUrl() {
  const p = new URLSearchParams(location.search).get("lecture");
  if (!p) return;
  MODE_DEMANDE = p === "10" ? "long" : p === "2" ? "court" : (lireDuree() === "10" ? "long" : "court");
  try { history.replaceState(null, "", location.pathname + location.hash); } catch (e) { /* pas grave */ }
})();
const MODES = {};   // le mode choisi pour chaque article pendant la visite
const aLEssentiel = (a) => Boolean(a && a.mini && a.mini.fait && a.mini.consequence);
function modeDe(id, a) {
  if (!aLEssentiel(a)) return "long";
  if (!MODES[id]) {
    MODES[id] = MODE_DEMANDE || (lireDuree() === "2" ? "court" : "long");
    MODE_DEMANDE = null;
  }
  return MODES[id];
}
const ICONE_CHRONO = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="13" r="8"/><path d="M12 9v4l2.5 2M9 2h6"/></svg>';
const ICONE_LIVRE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 5h7a3 3 0 0 1 3 3v12a2 2 0 0 0-2-2H2zM22 5h-7a3 3 0 0 0-3 3v12a2 2 0 0 1 2-2h8z"/></svg>';
function compterEvenement(evenement, id) {   // pour le pilotage : sans rien savoir du lecteur
  try { navigator.sendBeacon("/api/vue", new Blob([JSON.stringify({ id, evenement })], { type: "application/json" })); } catch (e) { /* pas grave */ }
}
document.addEventListener("click", (e) => {
  const b = e.target.closest("[data-mode]");
  if (!b) return;
  const id = (location.hash.match(/^#article-(.+)$/) || [])[1];
  if (!id || !ARTICLES[id]) return;
  const avant = MODES[id];
  MODES[id] = b.dataset.mode;
  if (avant === "court" && b.dataset.mode === "long") compterEvenement("entier", "article-" + id);
  renderArticle(id);
  window.scrollTo(0, 0);
});

function renderArticle(id) {
  const a = ARTICLES[id];
  const el = document.getElementById("article");
  if (!a || !el) return false;
  const mode = modeDe(id, a);
  const paras = (arr) => arr.map((p) => `<p>${p}</p>`).join("");
  const pub = a.audience === "public" || a.audience === "detour";
  const backTo = a.audience === "public" ? ["#vies", "Tous connectés"] : a.audience === "detour" ? ["#detour", "Le Détour"] : ["#une", "À la une"];
  const visual = `<div class="art-img${a.img.includes("/photos/") ? " art-photo" : ""}" style="background-image:url('${a.img}')"></div>`;
  const srcList = a.sources || (a.source ? [a.source] : []);
  const srcHtml = srcList.length ? `<div class="art-source"><b>${srcList.length > 1 ? "Sources" : "Source"}</b>${srcList.map((x) => `<a href="${x.url}" target="_blank" rel="noopener">${x.label} ↗</a>`).join("")}</div>` : "";
  const suivi = suiviFournisseurs(a);
  const bonReflexe = a.reflexes ? `<section class="bon-reflexe">
        <h2>Le bon réflexe</h2>
        <p class="br-sous">${a.reflexes_intro || `${["", "Un geste simple", "Deux gestes simples", "Trois gestes simples", "Quatre gestes simples"][a.reflexes.length] || "Des gestes simples"}, à faire tout de suite.`}</p>
        <ol class="br-liste">${a.reflexes.map((r, i) => `<li><span class="br-num">${String(i + 1).padStart(2, "0")}</span><span>${debutGras(r)}</span></li>`).join("")}</ol>
      </section>` : "";
  const bascule = aLEssentiel(a) ? `<div class="duree-bascule" role="group" aria-label="Temps de lecture">
        <button type="button" data-mode="court" aria-pressed="${mode === "court"}">${ICONE_CHRONO}2 min</button>
        <button type="button" data-mode="long" aria-pressed="${mode === "long"}">${ICONE_LIVRE}En entier</button>
      </div>` : "";
  if (mode === "court") {
    const m = a.mini;
    const dernier = pub ? (m.dependance || (a.lien || []).slice(-1)[0]) : m.dependance;
    el.innerHTML = `
    <div class="art-haut"><a href="${backTo[0]}" class="back">← ${backTo[1]}</a>${bascule}</div>
    <header class="art-head">
      <span class="flag ${a.tagClass || ""}">${a.tag}</span>
      <h1 class="display art-title">${a.title}</h1>
      <p class="art-meta">L'essentiel en 2 min${a.audience === "public" ? " · Édition grand public" : ""}</p>
    </header>
    <div class="art-body art-court">
      <section class="essentiel" aria-label="L'essentiel">
        <p class="ess-kicker">L'essentiel</p>
        <ol>
          <li><span class="ess-n">01</span><p><b>Le fait.</b> ${m.fait}</p></li>
          <li><span class="ess-n">02</span><p><b>La conséquence.</b> ${m.consequence}</p></li>
          ${dernier ? `<li><span class="ess-n">03</span><p><b>${pub ? "Et vous ?" : "La dépendance."}</b> ${dernier}</p></li>` : ""}
        </ol>
      </section>
      ${pub ? bonReflexe : `<p class="ess-sonde" data-plan="premium"><b>Ce que la sonde a mesuré :</b> ${a.impact.status}.</p>`}
      <button type="button" class="btn-entier" data-mode="long">${ICONE_LIVRE}Lire en entier · ${a.time}</button>
      <p class="ess-note">Votre choix se règle dans la cloche. Il reste sur cet appareil : Iris ne sait rien de vous.</p>
    </div>`;
    return true;
  }
  const ending = pub
    ? `${bonReflexe}
      ${suivi ? suivi.premium + suivi.standard : ""}
      ${srcHtml}
      ${a.audience === "public" ? `<a class="bridge" href="#une"><span>Vous êtes une entreprise ?</span><b>La même dépendance existe chez vos fournisseurs. Voir l'édition pro →</b></a>` : ""}`
    : `<section class="impact impact-${a.impact.level}" data-plan="premium">
        <p class="impact-kicker">Ce que la sonde a mesuré</p>
        <h2>${a.impact.status}</h2>
        <dl>${a.impact.rows.map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join("")}</dl>
        <p class="impact-note">${RAPPEL}</p>
        ${suivi ? "" : `<div class="impact-ctas">${LIENS_PREMIUM}</div>`}
      </section>
      ${suivi ? suivi.standard : `<section class="impact impact-teaser" data-plan="standard">
        <p class="impact-kicker">Ce que la sonde a mesuré</p>
        <h2>Les fournisseurs d'IA étaient-ils touchés ?</h2>
        <p class="teaser-txt">Avec Iris Premium, vous suivez heure par heure les fournisseurs d'IA européens mesurés par notre sonde : pannes, lenteurs, engagements tenus ou non, avec les preuves.</p>
        <div class="impact-ctas"><button type="button" class="btn btn-yellow" data-set-plan="premium">★ Passer en Premium</button></div>
      </section>`}
      ${suivi ? suivi.premium : ""}
      ${srcHtml}`;
  el.innerHTML = `
    <div class="art-haut"><a href="${backTo[0]}" class="back">← ${backTo[1]}</a>${bascule}</div>
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

/* ---------- Écran de relecture (réservé à la rédaction) ----------
   Accessible par /#relecture, sans lien dans la navigation. */
function renderRelecture() {
  const el = document.getElementById("relecture");
  if (!el) return;
  const rows = Object.entries(ARTICLES).filter(([, a]) => a.impact && a.impact.confidence).map(([id, a]) => {
    const c = a.impact.confidence;
    const crit = c.level === "non" ? "Aucune anomalie dans la fenêtre"
      : [["lieu", "Lieu"], ["moment", "Moment"], ["symptome", "Symptôme"], ["officiel", "Officiel"]].map(([k, t]) => `${c[k] ? "✓" : "○"} ${t}`).join(" · ");
    const titre = a.title.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
    return `<tr data-id="${id}">
      <td><a href="#article-${id}">${titre}</a></td>
      <td><span class="rtag rtag-${c.level}">${TAG_LABELS[c.level]}</span></td>
      <td class="muted small">${crit}</td>
      <td class="small">${a.impact.status}</td>
      <td class="rdecision"><button class="btn btn-yellow btn-sm" data-dec="publier">Publier</button><button class="btn btn-outline btn-sm" data-dec="retenir">Ne pas publier</button></td>
    </tr>`;
  }).join("");
  el.innerHTML = `<table class="sla rtable"><thead><tr><th>Article</th><th>Tag</th><th>Critères</th><th>Texte proposé</th><th>Décision</th></tr></thead><tbody>${rows}</tbody></table>`;
  el.addEventListener("click", (e) => {
    const b = e.target.closest("[data-dec]");
    if (!b) return;
    const td = b.closest("td");
    td.innerHTML = b.dataset.dec === "publier" ? `<span class="rdone ok">✓ Publié</span>` : `<span class="rdone">Retenu, non publié</span>`;
  });
}
renderRelecture();

/* ---------- Les articles les plus lus (encart latéral) ---------- */
const MOST_READ = {
  pro: ["ovh", "maj", "cloudflare"],
  public: ["blackout", "labubu"],
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
const EXTERNAL = [   // novembre 2026 au plus tôt : pas d'actualités trop anciennes dans le Détour
  { source: "The Register", cat: "Cloud", img: "logiciel", date: "2026-11-21", title: "AWS aussi est tombé en panne. Pourquoi personne n'en a parlé (en anglais)", why: "Une panne chez le géant du cloud, passée presque inaperçue.", url: "https://www.theregister.com/columnists/2026/11/21/aws-got-hit-by-an-outage-too-heres-why-you-didnt-hear-about-it/5311511" },
  { source: "Ars Technica", cat: "Réseau", img: "reseau", date: "2026-11-20", title: "Tous les vols arrêtés aux États-Unis : la cause bientôt connue (en anglais)", why: "Un ancien de l'aviation civile américaine explique comment moderniser un réseau vieux de plusieurs décennies sans tout clouer au sol.", url: "https://arstechnica.com/gadgets/2026/11/how-faa-can-modernize-us-national-airspace-system-without-emergency-ground-stops/" },
  { source: "Le Monde", cat: "Cybersécurité", img: "savoir", date: "2026-11-19", title: "Cybersécurité : « il y a urgence pour la résilience de la nation » (payant ?)", why: "Après le vote de la loi, 20 000 entreprises et entités publiques auront deux ans pour appliquer leurs nouvelles obligations.", url: "https://www.lemonde.fr/pixels/article/2026/11/19/anne-le-henanff-en-matiere-de-cybersecurite-il-y-a-urgence-pour-la-resilience-de-la-nation_6813364_4408996.html" },
  { source: "Next", cat: "Énergie", img: "energie", date: "2026-11-19", title: "Datacenters : après la course à l'énergie, la bataille de l'acceptabilité", why: "Les opérateurs de datacenters ont un nouveau mot d'ordre : se faire accepter, par le public comme par les autorités.", url: "https://next.ink/268399/les-datacenters-face-au-mur-de-lacceptabilite/" },
  { source: "Next", cat: "Réseau", img: "reseau", date: "2026-11-18", title: "Fibre optique : après le déploiement, le déchirement", why: "Qui paiera l'entretien des réseaux de fibre construits par les collectivités ? Le bras de fer est lancé.", url: "https://next.ink/268128/fibre-optique-apres-le-deploiement-le-dechirement/" },
  { source: "404 Media", cat: "Logiciel", img: "logiciel", date: "2026-11-17", title: "« BREAKING: Everything » : quand tout repose sur la même pièce (en anglais)", why: "La célèbre tour de logiciels qui tient sur une seule brique, appliquée à tout le reste.", url: "https://www.404media.co/breaking-everything/" },
];
// Le Détour reste frais tout seul : 30 jours au plus, 9 liens au plus, le plus récent en grand,
// badge « Nouveau » pendant 3 jours. Rien d'avant novembre 2026.
function renderExternal() {
  const el = document.getElementById("ext-grid");
  if (!el) return;
  const jour = (n) => new Date(Date.now() - n * 864e5).toISOString().slice(0, 10);
  const limite = jour(30) > "2026-11-01" ? jour(30) : "2026-11-01";
  const liens = EXTERNAL.filter((x) => (x.date || "") >= limite)
    .sort((a, b) => String(b.date || "").localeCompare(String(a.date || "")) || String(b.publie_le || "").localeCompare(String(a.publie_le || "")))
    .slice(0, 9);
  const quand = (d) => new Date(d + "T12:00:00").toLocaleDateString("fr-FR", { day: "numeric", month: "short" });
  el.innerHTML = liens.map((x, i) => `<a class="ext-card${i === 0 ? " ext-vedette" : ""}" href="${x.url}" target="_blank" rel="noopener">
      <div class="ext-img" style="background-image:url('assets/photos/${x.img}.jpg')"></div>
      <div class="ext-body"><span class="ext-src">${x.source} ↗${x.date > jour(3) ? ' <b class="ext-new">Nouveau</b>' : ""}</span><span class="pc-tag">${x.cat} · ${quand(x.date)}</span><h3>${x.title}</h3><p>${x.why}</p></div>
    </a>`).join("");
}
renderExternal();

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
const VIEWS = ["relecture", "une", "vies", "plus", "pluslecture", "meteo", "alertes", "indicateurs", "detour", "rapports"];
// Compte une lecture d'article pour le tableau de pilotage (une fois par article et par visite, sans rien
// savoir du lecteur). Rien n'est compté pour les pages de pilotage ou les rubriques.
function compterLecture(hash) {
  if (!/^(article-|plus-etsi-|plus-meteo)/.test(hash)) return;
  try { if (sessionStorage.getItem("lu:" + hash)) return; sessionStorage.setItem("lu:" + hash, "1"); } catch (e) { /* navigation privée */ }
  setTimeout(() => {
    const h = document.querySelector(".view.active h1, .view.active h2");
    const id = hash === "plus-meteo" ? "plus-meteo-" + (((window.PLUS || {}).meteo_semaine || [{}])[0].id || "") : hash;
    const corps = JSON.stringify({ id, titre: h ? h.textContent : "" });
    try { navigator.sendBeacon("/api/vue", new Blob([corps], { type: "application/json" })); } catch (e) { /* pas grave */ }
  }, 1500);
}

function show(hash) {
  compterLecture(hash);
  let view = hash, tab = hash;
  if (hash.startsWith("article-") && renderArticle(hash.slice(8))) {
    view = "article";
    const aud = ARTICLES[hash.slice(8)].audience;
    tab = aud === "public" ? "vies" : aud === "detour" ? "detour" : "une";
  }
  else if (hash.startsWith("plus-")) { view = "pluslecture"; tab = "plus"; plusLecture(hash.slice(5)); }
  else if (!VIEWS.includes(hash)) { view = tab = "une"; }
  document.querySelectorAll(".view").forEach((v) => v.classList.toggle("active", v.dataset.view === view));
  document.querySelectorAll(".tabs a").forEach((a) => a.classList.toggle("active", a.dataset.view === tab));
  const t = document.querySelector(`.tabs a[data-view="${tab}"]`);
  if (t) t.scrollIntoView({ block: "nearest", inline: "center" });
  window.scrollTo(0, 0);
}
window.addEventListener("hashchange", () => show(location.hash.slice(1)));

/* ---------- Date du jour ---------- */

/* ---------- Carte météo ----------
   Projection identique à celle de assets/europe-dots.svg
   (lon -12→32, lat 35→62, 20 px par degré de latitude). */
const MAP = { lon0: -12, lat1: 62, kx: 13.3826, ky: 20, w: 588.83, h: 540 };
const project = (lat, lon) => ({
  x: ((lon - MAP.lon0) * MAP.kx) / MAP.w * 100,
  y: ((MAP.lat1 - lat) * MAP.ky) / MAP.h * 100,
});



/* ---------- Ma Météo : les vraies mesures de la sonde ----------
   donnees/meteo.json, alertes.json, contrats.json et statuts.json sont copiés depuis public/
   à chaque passage de la sonde (Actions → Mesure horaire). Rien n'est inventé ici. */
const METEO_ICONE = { soleil: "sun", eclaircie: "cloudsun", nuage: "fog", orage: "storm", inconnu: "unknown" };
const METEO_MOT = { orage: "Orageux.", nuage: "Nuageux.", eclaircie: "Éclaircies.", soleil: "Ensoleillé.", inconnu: "Pas de mesure." };
const METEO_LIEU = {   // position sur la carte : ville de la région annoncée par le fournisseur
  mistral: { lat: 48.86, lon: 2.35, dx: -22, dy: 14 }, scaleway: { lat: 48.6, lon: 2.6, dx: -20, dy: 30 },
  ovhcloud: { lat: 50.69, lon: 3.17, dx: -21, dy: -8 }, ionos: { lat: 52.52, lon: 13.4, dx: 18, dy: -6 },
};
const pct1 = (v) => (v == null ? "—" : v.toLocaleString("fr-FR", { maximumFractionDigits: v >= 99.9 ? 2 : 1 }) + " %");
const ilYa = (iso) => {
  const min = Math.max(0, Math.round((Date.now() - new Date(iso)) / 60000));
  if (min < 60) return `il y a ${min} min`;
  if (min < 48 * 60) return `il y a ${Math.round(min / 60)} h`;
  return `il y a ${Math.round(min / 1440)} j`;
};
const heureParis = (iso) => new Date(iso).toLocaleTimeString("fr-FR", { hour: "2-digit", timeZone: "Europe/Paris" }).replace(/\s*h?$/, " h");
// Les mesures et les articles ne sont plus copiés dans le site à chaque passage de la sonde (sinon Vercel
// redéploierait 150 fois par jour, au-delà de sa limite) : on les lit à jour sur GitHub, via /d/ (voir vercel.json).
// Repli : la copie du site, si GitHub ne répond pas (ou en local).
function frais(chemin) {
  return fetch("/d/" + chemin + "?t=" + Math.floor(Date.now() / 60000), { cache: "no-store" })
    .then((r) => (r.ok ? r : Promise.reject(r)))
    .catch(() => fetch(chemin, { cache: "no-store" }));
}
const lire = (f) => frais("donnees/" + f).then((r) => (r.ok ? r.json() : null)).catch(() => null);

// Les pannes des 30 derniers jours : chaque alerte « orage » ouvre une panne, la « fin de l'orage » qui suit la ferme.
// Les incidents mesurés avant le début du journal (meteo.json) complètent, sans doublon. Durées : entre deux passages.
function episodesDePanne(alertes, m) {
  const depuis = new Date(Date.now() - 30 * 864e5).toISOString();
  const res = [];
  const parF = {};
  [...(alertes || [])].sort((a, b) => String(a.horodatage).localeCompare(String(b.horodatage))).forEach((a) => {
    const ouvert = parF[a.fournisseur];
    if (a.type === "orage" && !ouvert) parF[a.fournisseur] = { fournisseur: a.fournisseur, debut: a.horodatage };
    if (a.type === "fin_orage" && ouvert) {
      ouvert.fin = a.horodatage;
      ouvert.duree_min = Math.round((new Date(a.horodatage) - new Date(ouvert.debut)) / 60000);
      res.push(ouvert); delete parF[a.fournisseur];
    }
  });
  const maintenant = (m && m.genere_le) || new Date().toISOString();
  Object.values(parF).forEach((o) => res.push({ ...o, en_cours: true, duree_min: Math.round((new Date(maintenant) - new Date(o.debut)) / 60000) }));
  ((m && m.fournisseurs) || []).forEach((f) => (f.incidents_30j || []).forEach((i) => {
    const chevauche = res.some((e) => e.fournisseur === f.id && e.debut <= (i.fin || maintenant) && (e.fin || maintenant) >= i.debut);
    if (!chevauche) res.push({ fournisseur: f.id, debut: i.debut, fin: i.fin, duree_min: i.duree_min, en_cours: i.en_cours });
  }));
  return res.filter((e) => (e.fin || maintenant) >= depuis).sort((a, b) => String(b.debut).localeCompare(String(a.debut)));
}
const nomCourt = (m, id) => ((m && m.fournisseurs) || []).find((f) => f.id === id)?.nom_court || id;
const jourHeure = (iso) => new Date(iso).toLocaleString("fr-FR", { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", timeZone: "Europe/Paris" }).replace(":", " h ");

Promise.all([lire("meteo.json"), lire("alertes.json"), lire("contrats.json"), lire("statuts.json")]).then(([m, alertes, contrats, statuts]) => {
  const vue = document.getElementById("view-meteo");
  if (!vue) return;
  if (!m || !(m.fournisseurs || []).length) {
    document.getElementById("meteo-date").textContent = "Les mesures ne sont pas encore disponibles. Elles arrivent au prochain passage de la sonde.";
    return;
  }
  IRIS_METEO = m;
  if (location.hash.startsWith("#article-")) show(location.hash.slice(1));
  const F = m.fournisseurs;
  const officiel = (statuts && statuts.fournisseurs) || {};
  const engagement = Object.fromEntries((contrats || []).filter((c) => c.suivi_par_la_sonde).map((c) => [c.id, c.engagement_pct]));

  // En-tête : quand, d'où, et le temps qu'il fait
  const vieux = Date.now() - new Date(m.genere_le) > 2 * 3600e3;
  document.getElementById("meteo-date").innerHTML = `Dernière mesure ${ilYa(m.genere_le)}${vieux ? " <b class=\"c-yellow\">(mesures en retard)</b>" : ""} · depuis ${m.point_de_mesure || "la sonde Iris"}`;
  const ordre = ["orage", "nuage", "eclaircie", "soleil"];
  const pire = ordre.find((e) => F.some((f) => f.etat === e)) || "inconnu";
  document.getElementById("meteo-ciel").setAttribute("href", "#wx-" + METEO_ICONE[pire]);
  document.getElementById("meteo-mot").textContent = METEO_MOT[pire];
  document.getElementById("meteo-phrase").innerHTML = m.phrase + (pire === "orage" ? ' <a href="#alertes">Voir l\'alerte →</a>' : "");
  document.getElementById("meteo-nb").textContent = `${F.length} surveillés`;
  if (m.historique_depuis) document.getElementById("meteo-depuis").textContent = "mesures depuis le " + new Date(m.historique_depuis + "T12:00").toLocaleDateString("fr-FR", { day: "numeric", month: "long" });
  if (m.methode) document.getElementById("meteo-methode").textContent = "Méthode : " + m.methode;

  // Carte
  const carte = document.getElementById("meteo-map");
  const NS = "http://www.w3.org/2000/svg";
  const traits = document.createElementNS(NS, "svg");
  traits.setAttribute("class", "wx-line"); traits.setAttribute("viewBox", "0 0 100 100"); traits.setAttribute("preserveAspectRatio", "none");
  carte.appendChild(traits);
  const detail = (f) => {
    if (f.etat === "inconnu") return "Pas de mesure récente";
    const t = f.ttft_ms ? ` · ${f.ttft_ms.toLocaleString("fr-FR")} ms` : "";
    const off = officiel[f.id] && officiel[f.id].etat_officiel;
    return f.libelle + t + (f.etat === "orage" && off ? ` · page officielle : « ${off} »` : "");
  };
  F.forEach((f) => {
    const lieu = METEO_LIEU[f.id];
    if (!lieu) return;
    const { x, y } = project(lieu.lat, lieu.lon);
    const ic = METEO_ICONE[f.etat] || "unknown";
    const pin = document.createElement("span");
    pin.className = `pin s-${ic}`; pin.style.left = `${x}%`; pin.style.top = `${y}%`; pin.title = f.nom;
    carte.appendChild(pin);
    const l = document.createElementNS(NS, "line");
    l.setAttribute("x1", x); l.setAttribute("y1", y); l.setAttribute("x2", x + lieu.dx); l.setAttribute("y2", y + lieu.dy);
    l.setAttribute("vector-effect", "non-scaling-stroke");
    traits.appendChild(l);
    const c = document.createElement("div");
    c.className = `wx-card${f.etat === "orage" ? " storm" : ""}`;
    c.style.left = `${x + lieu.dx}%`; c.style.top = `${y + lieu.dy}%`;
    c.innerHTML = `<svg class="wx"><use href="#wx-${ic}"/></svg><div><b>${f.nom_court || f.nom}</b><span>${detail(f)}</span></div>`;
    carte.appendChild(c);
  });
  const liste = document.createElement("ul");
  liste.className = "wx-list";
  liste.innerHTML = F.map((f) => `<li class="${f.etat === "orage" ? "storm" : ""}"><svg class="wx"><use href="#wx-${METEO_ICONE[f.etat] || "unknown"}"/></svg><b>${f.nom_court || f.nom}</b><span>${detail(f)}</span></li>`).join("");
  carte.after(liste);

  // Ces dernières heures (mesures puis prévision)
  // les colonnes sont alignées sur l'heure : un fournisseur sans point à une heure donnée affiche « pas de mesure »
  const cle = (iso) => new Date(iso).toISOString().slice(0, 13);
  const heures = {};
  F.forEach((f) => (f.chronologie || []).forEach((p) => { if (!heures[cle(p.heure)] || p.nature === "mesure") heures[cle(p.heure)] = p; }));
  const colonnes = Object.keys(heures).sort();
  const cellule = (p) => p
    ? `<td class="${p.nature === "prevision" ? "prev" : ""}" title="${p.nature === "prevision" ? "Prévision : " + (p.certitude || "") : (p.ttft_ms ? p.ttft_ms + " ms" : "pas de mesure")}"><svg class="wx"><use href="#wx-${METEO_ICONE[p.etat] || "unknown"}"/></svg></td>`
    : `<td title="pas de mesure"><svg class="wx"><use href="#wx-unknown"/></svg></td>`;
  document.getElementById("meteo-heures").innerHTML = `<table><thead><tr><th></th>${colonnes.map((k) => `<th class="${heures[k].nature === "prevision" ? "prev" : ""}">${heureParis(heures[k].heure)}</th>`).join("")}</tr></thead><tbody>${
    F.map((f) => {
      const parHeure = {};
      (f.chronologie || []).forEach((p) => { if (!parHeure[cle(p.heure)] || p.nature === "mesure") parHeure[cle(p.heure)] = p; });
      return `<tr><th>${f.nom_court || f.nom}</th>${colonnes.map((k) => cellule(parHeure[k])).join("")}</tr>`;
    }).join("")
  }</tbody></table>`;

  // Les 3 piliers, calculés sur les mesures
  const mesures = F.filter((f) => f.disponibilite && f.disponibilite["7j"] != null);
  const dispo7 = mesures.length ? mesures.reduce((t, f) => t + f.disponibilite["7j"], 0) / mesures.length : null;
  const pannes = episodesDePanne(alertes, m);
  const minutes = pannes.reduce((t, p) => t + (p.duree_min || 0), 0);
  const suivis = F.filter((f) => engagement[f.id] != null && f.disponibilite && f.disponibilite["30j"] != null);
  const tenus = suivis.filter((f) => f.disponibilite["30j"] >= engagement[f.id]);
  const barre = (v) => Math.max(4, Math.min(100, v));
  document.getElementById("meteo-piliers").innerHTML = `
    <li><span class="sc-ico">⚡</span><span class="sc-name">Disponibilité mesurée (7 j)</span><b>${pct1(dispo7)}</b><i style="--w:${barre(((dispo7 || 0) - 90) * 10)}%"></i></li>
    <li><span class="sc-ico">⛈</span><span class="sc-name">Pannes mesurées (30 j)</span><b>${pannes.length ? `${pannes.length} panne${pannes.length > 1 ? "s" : ""} · ${minutes} min` : "aucune"}</b><i style="--w:${barre(pannes.length * 20)}%"></i></li>
    <li><span class="sc-ico">⚖</span><span class="sc-name">Engagements tenus (30 j)</span><b>${tenus.length} / ${suivis.length}</b><i style="--w:${suivis.length ? barre(tenus.length / suivis.length * 100) : 4}%"></i></li>`;

  // Disponibilité mesurée vs engagement
  const MIN = 90, MAX = 100, pos = (v) => Math.max(0, Math.min(100, ((v - MIN) / (MAX - MIN)) * 100));
  const ul = document.getElementById("dispo");
  ul.innerHTML = F.map((f) => {
    const v = f.disponibilite && f.disponibilite["30j"], e = engagement[f.id];
    if (v == null) return `<li><span>${f.nom_court || f.nom}</span><span class="track"></span><b class="muted">—</b></li>`;
    const ko = e != null && v < e;
    return `<li><span>${f.nom_court || f.nom}</span>
      <span class="track" title="${e != null ? "Engagement " + pct1(e) + " · " : ""}mesuré ${pct1(v)}">
        <span class="fill${ko ? " ko" : ""}" style="width:${pos(v)}%"></span>${e != null ? `<span class="tick" style="left:${pos(e)}%"></span>` : ""}
      </span><b>${pct1(v)}</b></li>`;
  }).join("");
  ul.insertAdjacentHTML("afterend", `<p class="dispo-note">Trait blanc = engagement de disponibilité du contrat. Rouge = engagement non tenu sur la période mesurée. Échelle 90 → 100 %.</p>`);

  // Signaux : incidents officiels en cours, puis les dernières alertes de la sonde
  const couleur = { rouge: "red", orange: "yellow", jaune: "yellow", vert: "grey" };
  const signaux = [];
  Object.entries(officiel).forEach(([id, o]) => {
    if (o && o.incident_en_cours) signaux.push({ c: "red", t: `${(F.find((f) => f.id === id) || {}).nom_court || id} : ${o.incident_en_cours.titre || "incident annoncé"}`, h: o.incident_en_cours.debut });
  });
  [...(alertes || [])].sort((a, b) => String(b.horodatage).localeCompare(String(a.horodatage))).slice(0, 5)
    .forEach((a) => signaux.push({ c: couleur[a.niveau] || "grey", t: a.titre, h: a.horodatage }));
  document.getElementById("meteo-signaux").innerHTML = signaux.length
    ? signaux.slice(0, 6).map((x) => `<li><span class="sd sd-${x.c}"></span><span>${x.t}</span><time>${x.h ? ilYa(x.h) : ""}</time></li>`).join("")
    : `<li><span class="sd sd-grey"></span><span>Aucun signal ces derniers jours.</span><time></time></li>`;
});


/* ---------- Alertes, Indicateurs, Rapports : les vraies données de la sonde ---------- */
Promise.all([lire("meteo.json"), lire("alertes.json"), lire("contrats.json"), lire("avoirs.json"), lire("rapports.json"), lire("statuts.json")])
  .then(([m, alertes, contrats, avoirs, rapports, statuts]) => {
    const F = (m && m.fournisseurs) || [];
    const parId = Object.fromEntries(F.map((f) => [f.id, f]));
    const contrat = Object.fromEntries((contrats || []).map((c) => [c.id, c]));
    const pannes = episodesDePanne(alertes, m);

    // --- Demander à Iris : réponses calculées sur les mesures
    const mn = (x) => x.toLocaleString("fr-FR");
    const parFour = {};
    pannes.forEach((p) => (parFour[p.fournisseur] = (parFour[p.fournisseur] || 0) + (p.duree_min || 0)));
    const classement = Object.entries(parFour).sort((a, b) => b[1] - a[1]);
    const moisA = Object.keys(avoirs || {}).sort().pop();
    const dusA = ((avoirs && avoirs[moisA]) || []).filter((l) => l.engagement_tenu === false && l.avoir_pct > 0);
    const rapides = F.filter((f) => f.ttft_ms).sort((a, b) => a.ttft_ms - b.ttft_ms);
    const rappel = " <span class=\"muted\">Mesure externe, à titre indicatif.</span>";
    ANSWERS = [
      classement.length ? `Sur 30 jours, <b>${nomCourt(m, classement[0][0])}</b> cumule <b>${mn(classement[0][1])} minutes</b> de panne mesurées${classement[1] ? `, devant ${classement.slice(1).map(([id, v]) => `${nomCourt(m, id)} (${mn(v)} min)`).join(", ")}` : ""}. Les autres fournisseurs suivis n'ont pas eu de panne.` + rappel : "Aucune panne mesurée sur 30 jours." + rappel,
      dusA.length ? dusA.map((l) => `<b>${nomCourt(m, l.fournisseur)}</b> promet ${pct1(l.engagement_pct)} ; la sonde a mesuré ${pct1(l.disponibilite_pct)} ce mois-ci sur ${l.fenetres_mesurees} créneaux. Avoir possible : <b>${l.avoir_pct} % de la facture</b>, pour les clients payants, avant le ${new Date(l.echeance + "T12:00").toLocaleDateString("fr-FR", { day: "numeric", month: "long" })}.`).join(" ") + " Vérifiez avec votre propre suivi avant de réclamer." + rappel : "Aucun engagement de disponibilité non tenu ce mois-ci, d'après la sonde." + rappel,
      rapides.length ? `En ce moment, <b>${rapides[0].nom_court}</b> répond le plus vite : <b>${mn(rapides[0].ttft_ms)} ms</b> avant le premier mot. ${rapides.slice(1).map((f) => `${f.nom_court} : ${mn(f.ttft_ms)} ms`).join(" · ")}.` + rappel : "Pas de mesure récente de rapidité." + rappel,
    ];

    // --- Badge : fournisseurs en panne ou en vigilance en ce moment
    const actifs = F.filter((f) => f.etat === "orage" || ["orange", "rouge"].includes(f.vigilance));
    const badge = document.getElementById("alertes-badge");
    if (badge && actifs.length) { badge.textContent = actifs.length; badge.hidden = false; }

    // --- Alertes
    const liste = document.getElementById("alertes-liste");
    if (liste) {
      const journal = [...(alertes || [])].sort((a, b) => String(b.horodatage).localeCompare(String(a.horodatage)));
      document.getElementById("alertes-titre").textContent = `Alertes (${journal.length})`;
      const derniere = {};
      journal.forEach((a) => { if (!derniere[a.fournisseur]) derniere[a.fournisseur] = a; });
      const icone = { orage: `<svg class="al-ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M13 2L4 14h7l-1 8 9-12h-7z" fill="#FF4A3D"/></svg>`,
        vigilance: `<svg class="al-ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.5L22 20H2z" fill="#FFCC00"/><path d="M12 9v5" stroke="#0A0A0A" stroke-width="2" stroke-linecap="round"/><circle cx="12" cy="16.8" r="1.2" fill="#0A0A0A"/></svg>`,
        fin_orage: `<svg class="al-ico" aria-hidden="true"><use href="#wx-sun"/></svg>` };
      liste.innerHTML = journal.length ? journal.map((a) => {
        const f = parId[a.fournisseur] || {};
        const enCours = derniere[a.fournisseur] === a && (a.type === "orage" ? f.etat === "orage" : a.type === "vigilance" ? ["orange", "rouge"].includes(f.vigilance) : false);
        const cat = { orage: "panne", fin_orage: "retour", vigilance: "lenteur" }[a.type] + (enCours ? " encours" : "");
        const chip = { orage: ["chip-red", "Panne"], vigilance: ["chip-yellow", "Lenteur"], fin_orage: ["chip-grey", "Retour au calme"] }[a.type] || ["", a.type];
        const bouton = a.type === "fin_orage" ? `<a href="#indicateurs" class="btn btn-outline">Voir le calcul d'avoir</a>`
          : `<a href="#meteo" class="btn ${enCours ? "btn-yellow" : "btn-outline"}">${enCours ? "Voir ma météo" : "Voir la météo"}</a>`;
        return `<article class="alert-row${enCours && a.type === "orage" ? " critical" : ""}" data-cat="${cat}">
          ${icone[a.type] || icone.vigilance}
          <div class="al-body">
            <h3>${a.titre}</h3>
            <div class="chips"><span class="chip ${chip[0]}">${chip[1]}</span>${enCours ? '<span class="chip chip-red">En cours</span>' : ""}<span class="chip">${f.nom_court || a.fournisseur}</span><span class="chip">${jourHeure(a.horodatage)}</span></div>
            <p>${a.texte}</p>
          </div>
          <div class="al-side"><time>${ilYa(a.horodatage)}</time>${bouton}</div>
        </article>`;
      }).join("") : `<p class="muted">Aucune alerte : la sonde n'a rien vu d'anormal.</p>`;
    }

    // --- Indicateurs
    const piliers = document.getElementById("indic-piliers");
    if (piliers && F.length) {
      const d30 = F.filter((f) => f.disponibilite && f.disponibilite["30j"] != null);
      const dispo = d30.length ? d30.reduce((t, f) => t + f.disponibilite["30j"], 0) / d30.length : null;
      const minutes = pannes.reduce((t, p) => t + (p.duree_min || 0), 0);
      const officiels = Object.values((statuts && statuts.fournisseurs) || {}).filter((o) => o && o.type === "statuspage").length;
      const dossiers = (rapports && rapports.dossiers) || [], preuves = (rapports && rapports.preuves) || [];
      const mois = Object.keys(avoirs || {}).sort().pop();
      const lignes = (avoirs && avoirs[mois]) || [];
      const dus = lignes.filter((l) => l.engagement_tenu === false && l.avoir_pct > 0);
      const nomMois = mois ? new Date(mois + "-15").toLocaleDateString("fr-FR", { month: "long", year: "numeric" }) : "";
      piliers.innerHTML = `
        <article class="pillar">
          <span class="pl-q">Est-ce que ça tient ?</span><h3>Disponibilité</h3>
          <div class="pl-num">${dispo == null ? "—" : dispo.toLocaleString("fr-FR", { maximumFractionDigits: 1 })}<small>%</small></div>
          <p class="muted small">disponibilité moyenne mesurée de vos ${F.length} fournisseurs (30 j)</p>
          <ul class="kv"><li><span>Pannes mesurées</span><b>${pannes.length}</b></li><li><span>Minutes en panne</span><b>${minutes} min</b></li>
            <li><span>En panne maintenant</span><b class="${F.some((f) => f.etat === "orage") ? "c-yellow" : ""}">${F.filter((f) => f.etat === "orage").map((f) => f.nom_court).join(", ") || "aucun"}</b></li></ul>
        </article>
        <article class="pillar">
          <span class="pl-q">Ai-je les preuves ?</span><h3>Traçabilité</h3>
          <div class="pl-num">${dossiers.length}<small> / ${F.length}</small></div>
          <p class="muted small">fournisseurs avec un dossier de surveillance à jour</p>
          <ul class="kv"><li><span>Fournisseurs mesurés chaque heure</span><b>${F.length} / ${F.length}</b></li>
            <li><span>Pages de statut officielles suivies</span><b>${officiels} / ${F.length}</b></li>
            <li><span>Journées de preuves horodatées</span><b>${preuves.length}</b></li></ul>
        </article>
        <article class="pillar pillar-yellow">
          <span class="pl-q">Qu'est-ce qu'on me doit ?</span><h3>Avoirs</h3>
          <div class="pl-num">${dus.length}<small> avoir${dus.length > 1 ? "s" : ""}</small></div>
          <p class="small">possible${dus.length > 1 ? "s" : ""} en ${nomMois} : engagement de disponibilité non tenu</p>
          <ul class="kv">${dus.map((l) => `<li><span>${nomCourt(m, l.fournisseur)}</span><b>${l.avoir_pct} % de la facture</b></li>`).join("") || "<li><span>Aucun engagement non tenu</span><b>—</b></li>"}
            ${dus.length ? `<li><span>À réclamer avant le</span><b>${new Date(dus[0].echeance + "T12:00").toLocaleDateString("fr-FR", { day: "numeric", month: "long" })}</b></li>` : ""}</ul>
        </article>`;
      document.getElementById("indic-mois").textContent = nomMois ? "Mois en cours : " + nomMois : "";
      const ecart = (v, e) => (v - e >= 0 ? "+" : "−") + Math.abs(v - e).toLocaleString("fr-FR", { maximumFractionDigits: 2 }) + " pt";
      document.getElementById("sla-body").innerHTML = lignes.map((l) => {
        const ko = l.engagement_tenu === false;
        return `<tr><td>${nomCourt(m, l.fournisseur)}<br><span class="muted small">${l.service || ""}</span></td><td>${pct1(l.engagement_pct)}</td><td>${pct1(l.disponibilite_pct)}</td>
          <td class="${ko ? "ko" : "ok"}">${ecart(l.disponibilite_pct, l.engagement_pct)}</td>
          <td class="${l.avoir_pct ? "money" : "ok"}">${l.avoir_pct ? l.avoir_pct + " % de la facture" : "—"}</td>
          <td>${l.echeance ? new Date(l.echeance + "T12:00").toLocaleDateString("fr-FR", { day: "numeric", month: "short" }) : "—"}</td>
          <td>${l.fenetres_mesurees} fenêtres</td></tr>`;
      }).join("");
      const couverts = [...new Set(lignes.map((l) => (contrat[l.fournisseur] || {}).qui_est_couvert).filter(Boolean))];
      document.getElementById("indic-note").innerHTML = `Calcul indicatif, d'après les barèmes publiés par chaque fournisseur. Une « fenêtre » est un créneau de 5 minutes où la sonde a mesuré le service : plus il y en a, plus le chiffre est solide. Les avoirs ne concernent que les clients payants${couverts.length ? " (" + couverts[0] + ", par exemple)" : ""} : la sonde, elle, mesure en offre gratuite ou anonyme.`;
    }

    // --- Rapports
    const rl = document.getElementById("rapports-liste");
    if (rl) {
      const depot = (rapports && rapports.depot) || "https://github.com/mcp-trust-score-org/sonde-ia-eu";
      const doc = `<svg class="doc" viewBox="0 0 24 24"><path d="M6 2h9l5 5v15H6z M15 2v5h5 M9 12h8M9 15h8M9 18h5" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>`;
      const jourCourt = (iso) => iso ? new Date(iso).toLocaleDateString("fr-FR", { day: "numeric", month: "short", year: "numeric" }) : "";
      const items = [];
      ((rapports && rapports.dossiers) || []).forEach((d) => items.push({ cat: "dossier", quand: d.genere_le,
        html: `${doc}<div><h3>Dossier de surveillance — ${d.nom}</h3><p>Disponibilité, pannes, chemin réseau, stabilité du modèle, fournisseurs de repli. Période du ${jourCourt(d.periode && d.periode.debut)} au ${jourCourt(d.periode && d.periode.fin)}.</p></div><span class="chip chip-yellow">DORA · NIS2</span><time>${jourCourt(d.genere_le)}</time><a class="dl" href="${depot}/blob/main/${d.fichier}" target="_blank" rel="noopener" aria-label="Ouvrir le dossier">↗</a>` }));
      const mois = Object.keys(avoirs || {}).sort().pop();
      ((avoirs && avoirs[mois]) || []).filter((l) => l.engagement_tenu === false).forEach((l) => items.push({ cat: "avoir", quand: m && m.genere_le,
        html: `${doc}<div><h3>Calcul d'avoir — ${nomCourt(m, l.fournisseur)}, ${new Date(mois + "-15").toLocaleDateString("fr-FR", { month: "long", year: "numeric" })}</h3><p>Engagement ${pct1(l.engagement_pct)}, mesuré ${pct1(l.disponibilite_pct)} sur ${l.fenetres_mesurees} fenêtres. Avoir indicatif : ${l.avoir_pct} % de la facture, à réclamer avant le ${new Date(l.echeance + "T12:00").toLocaleDateString("fr-FR", { day: "numeric", month: "long" })}.</p></div><span class="chip">Avoir SLA</span><time>${jourCourt(m && m.genere_le)}</time><a class="dl" href="#indicateurs" aria-label="Voir le calcul">→</a>` }));
      ((rapports && rapports.preuves) || []).forEach((p) => items.push({ cat: "preuve", quand: p.genere_le,
        html: `${doc}<div><h3>Preuves horodatées — ${new Date(p.jour + "T12:00").toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long" })}</h3><p>Empreintes de ${p.fichiers} fichier${p.fichiers > 1 ? "s" : ""} de mesures${p.horodatage ? ", scellées avec OpenTimestamps : personne ne peut les modifier après coup sans que ça se voie" : ""}.</p></div><span class="chip chip-grey">Preuve</span><time>${jourCourt(p.genere_le)}</time><a class="dl" href="${depot}/blob/main/${p.fichier}" target="_blank" rel="noopener" aria-label="Ouvrir la preuve">↗</a>` }));
      rl.innerHTML = items.length ? items.map((x) => `<div class="report-row" data-cat="${x.cat}">${x.html}</div>`).join("") : `<p class="muted">Aucun rapport pour l'instant.</p>`;
    }
  });

/* ---------- Filtres (Alertes, Rapports) ---------- */
document.querySelectorAll("[data-filter-group]").forEach((group) => {
  const scope = group.closest(".view");
  group.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    group.querySelectorAll("button").forEach((x) => x.classList.toggle("on", x === b));
    const f = b.dataset.f;
    scope.querySelectorAll("[data-cat]").forEach((item) => item.classList.toggle("is-hidden", f !== "all" && !item.dataset.cat.split(" ").includes(f)));
  });
});


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

// Les réponses sont calculées sur les mesures de la sonde (donnees/), jamais sur les systèmes du lecteur.
let ANSWERS = ["Les mesures se chargent, réessayez dans un instant.", "Les mesures se chargent, réessayez dans un instant.", "Les mesures se chargent, réessayez dans un instant."];
const FALLBACK = "Je réponds avec les mesures de la sonde Iris : pannes, avoirs possibles, rapidité. Essayez une des questions proposées. Je n'ai pas accès à vos systèmes, et mes chiffres sont indicatifs.";

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
    const t = push("Iris consulte ses mesures…", "iris");
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
    else if (/réclam|avoir|rembours|argent|€|sla/.test(low)) a = ANSWERS[1];
    else if (/vite|rapide|lent|latence|temps de réponse/.test(low)) a = ANSWERS[2];
    ask(q, a);
    input.value = "";
  });
})();

/* ---------- Articles publiés par la rédaction (iris/publies.json) ----------
   Écrits par la sonde, validés dans GitHub (Actions → « Publier un brouillon »).
   Le fichier est relu à chaque visite : un article publié apparaît sans toucher au code. */
const JOURS = ["Dim.", "Lun.", "Mar.", "Mer.", "Jeu.", "Ven.", "Sam."];
const MOIS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."];
function propre(html) {   // seules les balises de mise en forme du titre sont gardées
  return String(html || "").replace(/<(?!\/?(mark|br)\b)[^>]*>/gi, "");
}
function etiquetteJour(iso) {
  const d = new Date(iso + "T12:00:00");
  return `${JOURS[d.getDay()]} ${d.getDate()} ${MOIS[d.getMonth()]}`;
}
function carte(a, lien) {
  return `<a class="photo-card" href="#article-${a.id}">
      <div class="pc-img pc-photo" style="background-image:url('${a.img}')"></div>
      <div class="pc-body"><span class="pc-tag">${propre(a.tag)}</span><h3>${propre(a.title).replace(/<br\s*\/?>/g, " ").replace(/<\/?mark>/g, "")}</h3><span class="pc-link">${lien}</span><span class="pc-time">${a.date ? etiquetteJour(a.date) + " · " : ""}${a.time} de lecture</span></div>
    </a>`;
}
function une(a, grandPublic) {
  const m = a.mini || {};
  const dernier = grandPublic ? (m.dependance || (a.lien || []).slice(-1)[0]) : m.dependance;
  return `<article class="une-hero${grandPublic ? " vies-hero" : ""}">
    <div class="une-hero-img" style="background-image:url('${a.img}')"></div>
    <div class="une-hero-text">
      ${grandPublic ? `<span class="flag flag-cream">${propre(a.tag)}</span>` : `<span class="flag flag-red">À la une</span>`}
      <h1 class="display">${propre(a.title)}</h1>
      <ol class="steps-mini">
        ${m.fait ? `<li><span>Le fait</span>${propre(m.fait)}</li>` : ""}
        ${m.consequence ? `<li><span>La conséquence</span>${propre(m.consequence)}</li>` : ""}
        ${dernier ? `<li><span>${grandPublic ? "Et vous ?" : "La dépendance"}</span>${propre(dernier)}</li>` : ""}
      </ol>
      <a href="#article-${a.id}" class="read">→ <u>${grandPublic ? "Lire l'histoire" : "Lire l'analyse"} (${a.time})</u></a>
    </div>
  </article>`;
}
// Le grand titre : l'actualité la plus récente. Un bilan ou un « Retour sur » parle du passé :
// il ne prend le grand titre que s'il n'y a aucune actualité publiée. « Carte seulement » : jamais.
function choisirTete(liste) {
  const possibles = liste.filter((a) => a.place !== "carte");
  const actu = possibles.filter((a) => !/^\s*(Bilan|Retour sur)\b/i.test(String(a.tag || "").replace(/<[^>]+>/g, "")));
  return actu[0] || possibles[0];
}
// L'ancien grand titre (écrit dans la page) devient une carte quand un article publié prend sa place.
function carteDepuisGrandTitre(h, lienTexte = "Et vous ? →") {
  const img = (h.querySelector(".une-hero-img").style.backgroundImage.match(/url\(["']?([^"')]+)/) || [])[1] || "";
  const lien = h.querySelector("a.read");
  const temps = (lien.textContent.match(/\(([^)]+)\)/) || [])[1] || "4 min";
  return `<a class="photo-card" href="${lien.getAttribute("href")}">
      <div class="pc-img pc-photo" style="background-image:url('${img}')"></div>
      <div class="pc-body"><span class="pc-tag">${h.querySelector(".flag").textContent}</span><h3>${h.querySelector("h1").innerHTML.replace(/<br\s*\/?>/g, " ").replace(/<\/?mark>/g, "")}</h3><span class="pc-link">${lienTexte}</span><span class="pc-time">${temps} de lecture</span></div>
    </a>`;
}
var PUB = null;   // les articles publiés, pour « L'essentiel du jour »
frais("publies.json")
  .then((r) => (r.ok ? r.json() : null))
  .then((pub) => {
    if (!pub) return;
    PUB = pub;
    const nettoyer = (x) => (Array.isArray(x) ? x.map(nettoyer) : typeof x === "string" ? propre(x) : x);
    [...(pub.une || []), ...(pub.tous_connectes || [])].forEach((a) => {
      if (!a || !a.id) return;
      const n = { demo: false, ...a };
      ["title", "chapo", "fait", "consequence", "lien", "reflexes"].forEach((k) => { if (n[k]) n[k] = nettoyer(n[k]); });
      ARTICLES[a.id] = n;
    });

    // À la une : une seule page. Le dernier article publié devient le grand titre ; l'ancien grand
    // titre et les autres articles publiés passent en tête des cartes (comme Tous connectés).
    const cartesUne = document.querySelector("#view-une .cards3");
    const pubUne = [...(pub.une || [])].sort((x, y) => String(y.date || "").localeCompare(String(x.date || "")));
    if (cartesUne && pubUne.length) {
      const tete = choisirTete(pubUne);
      const ancien = document.querySelector("#view-une .une-hero");
      let cartes = pubUne.filter((a) => a !== tete).slice(0, 3).map((a) => carte(a, "Lire l'analyse →")).join("");
      if (tete && ancien) {
        cartes += carteDepuisGrandTitre(ancien, "Lire l'analyse →");
        ancien.outerHTML = une(tete);
      }
      cartesUne.insertAdjacentHTML("afterbegin", cartes);
    }

    // Tous connectés : le dernier article publié devient le grand titre ; l'ancien grand titre
    // et les autres articles publiés passent en tête des cartes (« carte seulement » : cartes uniquement).
    const grille = document.querySelector("#view-vies .cards4");
    // du plus récent au plus ancien : un article d'archive (daté d'un jour passé) ne prend pas le grand titre
    const tc = [...(pub.tous_connectes || [])].sort((x, y) => String(y.date || "").localeCompare(String(x.date || "")));
    if (grille && tc.length) {
      const tete = choisirTete(tc);
      const ancien = document.querySelector("#view-vies .vies-hero");
      let cartes = tc.filter((a) => a !== tete).slice(0, 3).map((a) => carte(a, "Et vous ? →")).join("");
      if (tete && ancien) {
        cartes += carteDepuisGrandTitre(ancien);
        ancien.outerHTML = une(tete, true);
      }
      grille.insertAdjacentHTML("afterbegin", cartes);
      // Le bon réflexe : celui « de la semaine » proposé par le rédacteur (moins de 7 jours),
      // sinon le premier réflexe de l'article en grand titre. Jamais écrit à la main.
      const rc = grille.querySelector(".reflex-card");
      const ilYa7Jours = new Date(Date.now() - 7 * 864e5).toISOString().slice(0, 10);
      const rs = tc.find((a) => a.reflexe_semaine && String(a.date || "") >= ilYa7Jours);
      const source = rs || (tete && (tete.reflexes || []).length ? tete : null);
      if (rc && source) {
        const titreArticle = propre(source.title).replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").replace(/ \./g, ".").trim();
        rc.querySelector("h3").textContent = rs ? rs.reflexe_semaine.titre || "" : propre(source.reflexes[0]).replace(/<[^>]+>/g, "");
        rc.querySelector("p").textContent = rs ? rs.reflexe_semaine.texte || "" : `Tiré de « ${titreArticle} »`;
      }
    }

    // Le Détour : les liens publiés passent en tête de la sélection
    if ((pub.detour || []).length) {
      EXTERNAL.unshift(...pub.detour.filter((x) => !EXTERNAL.some((e) => e.url === x.url)));
      renderExternal();
    }

    if (location.hash.startsWith("#article-")) show(location.hash.slice(1));
  })
  .catch(() => {});

/* ---------- Être prévenu des nouveaux articles : notifications sur l'appareil ----------
   sw.js reçoit les notifications ; /api/cle, /api/abonner (fonctions Vercel) gèrent l'abonnement. */
(function alertesArticles() {
  const bouton = document.querySelector("[data-cloche]");
  const panneau = document.getElementById("panneau-alerte");
  if (!bouton || !panneau) return;
  const etat = panneau.querySelector("[data-push-etat]");
  const action = panneau.querySelector("[data-push-activer]");
  const ios = panneau.querySelector("[data-push-ios]");
  const possible = "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;
  const iPhone = /iPhone|iPad|iPod/.test(navigator.userAgent);
  const installe = window.matchMedia("(display-mode: standalone)").matches || navigator.standalone;

  const test = panneau.querySelector("[data-push-test]");
  const options = [...panneau.querySelectorAll("[data-push-sujet]")];   // « plus » (Iris Plus), « alertes » (Premium)
  bouton.addEventListener("click", (e) => {
    e.stopPropagation();
    panneau.hidden = !panneau.hidden;
    bouton.setAttribute("aria-expanded", String(!panneau.hidden));
    // Sur téléphone, le panneau est fixé à l'écran : on le place juste sous la cloche.
    panneau.style.setProperty("--pa-top", Math.round(bouton.getBoundingClientRect().bottom + 10) + "px");
  });
  document.addEventListener("click", (e) => {
    if (!panneau.hidden && !panneau.contains(e.target)) { panneau.hidden = true; bouton.setAttribute("aria-expanded", "false"); }
  });

  function cle(base64) {   // clé publique VAPID → format attendu par le navigateur
    const b = (base64 + "=".repeat((4 - (base64.length % 4)) % 4)).replace(/-/g, "+").replace(/_/g, "/");
    return Uint8Array.from(atob(b), (c) => c.charCodeAt(0));
  }
  // Sujets reçus par cet appareil : « articles » toujours ; « plus » et « alertes » en option.
  const lireSujets = () => { try { return JSON.parse(localStorage.getItem("iris-sujets") || "null") || ["articles"]; } catch (e) { return ["articles"]; } };
  const garderSujets = (s) => { try { localStorage.setItem("iris-sujets", JSON.stringify(s)); } catch (e) { /* navigation privée */ } };
  async function envoyerAbonnement(abo, sujets) {
    return fetch("/api/abonner", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...abo.toJSON(), sujets }) });
  }
  function afficher(abonne, message) {
    bouton.classList.toggle("on", abonne);
    const sujets = lireSujets();
    options.forEach((o) => { o.closest("[data-push-option]").hidden = !abonne; o.checked = sujets.includes(o.dataset.pushSujet); });
    etat.textContent = message || (abonne ? "Activées sur cet appareil." : "Une notification à chaque article publié : À la une, Tous connectés, Le Détour.");
    action.textContent = abonne ? "Désactiver" : "Activer les notifications";
    action.dataset.abonne = abonne ? "1" : "";
    if (test) test.hidden = !abonne;
  }

  if (!possible) {
    if (iPhone && !installe) { ios.hidden = false; action.hidden = true; etat.textContent = "Sur iPhone, les notifications marchent une fois Iris ajouté à l'écran d'accueil."; }
    else { action.hidden = true; etat.textContent = "Ce navigateur ne permet pas les notifications."; }
    return;
  }
  let enregistrement = null;
  navigator.serviceWorker.register("/sw.js").then(async (r) => {
    enregistrement = r;
    const abo = await r.pushManager.getSubscription();
    const actif = Boolean(abo) && Notification.permission === "granted";
    afficher(actif);
    // À chaque ouverture, on redit au site ce que ce téléphone veut recevoir : si l'adresse d'abonnement
    // a changé (l'iPhone la renouvelle parfois) ou si le site l'a perdue, tout se remet en place tout seul.
    // (Seulement si ce téléphone a déjà gardé ses choix : sinon on risquerait d'effacer une option cochée.)
    let choixGardes = false;
    try { choixGardes = localStorage.getItem("iris-sujets") !== null; } catch (e) { /* navigation privée */ }
    if (actif && choixGardes) envoyerAbonnement(abo, lireSujets()).catch(() => { /* hors ligne : ce sera pour la prochaine fois */ });
  }).catch(() => { action.hidden = true; etat.textContent = "Notifications indisponibles pour l'instant."; });

  action.addEventListener("click", async () => {
    if (!enregistrement) return;
    action.disabled = true;
    try {
      if (action.dataset.abonne) {
        const abo = await enregistrement.pushManager.getSubscription();
        if (abo) {
          await fetch("/api/abonner", { method: "DELETE", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ endpoint: abo.endpoint }) });
          await abo.unsubscribe();
        }
        afficher(false, "Désactivées. Vous pouvez les réactiver à tout moment.");
        return;
      }
      const permission = await Notification.requestPermission();
      if (permission !== "granted") {
        afficher(false, "Notifications refusées. Pour changer d'avis : réglages du site dans votre navigateur.");
        return;
      }
      const r = await fetch("/api/cle", { cache: "no-store" });
      if (!r.ok) throw new Error("clé");
      const abo = await enregistrement.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: cle((await r.json()).cle) });
      const ok = await envoyerAbonnement(abo, lireSujets());
      if (!ok.ok) { await abo.unsubscribe(); throw new Error("abonnement"); }
      afficher(true, "C'est fait : vous serez prévenu à chaque nouvel article.");
    } catch (e) {
      afficher(false, "Ça n'a pas marché. Réessayez dans un instant.");
    } finally {
      action.disabled = false;
    }
  });

  const NOMS_SUJETS = { plus: "IRIS Plus", alertes: "alertes Premium", redaction: "rappels de rédaction" };
  // « M'envoyer un test » : le site envoie une notification à ce téléphone seul et dit ce qu'il a enregistré.
  if (test) test.addEventListener("click", async () => {
    const abo = enregistrement && await enregistrement.pushManager.getSubscription();
    if (!abo) return;
    test.disabled = true;
    etat.textContent = "Envoi d'un essai…";
    try {
      await envoyerAbonnement(abo, lireSujets());   // d'abord, on remet l'abonnement à jour
      const r = await fetch("/api/tester", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ endpoint: abo.endpoint }) });
      const j = await r.json().catch(() => ({}));
      const liste = (j.sujets || []).filter((s) => s !== "articles").map((s) => NOMS_SUJETS[s] || s);
      const recu = "Ce téléphone reçoit : nouveaux articles" + liste.map((s) => ", " + s).join("") + ".";
      if (j.envoye) etat.textContent = "Essai envoyé : il doit arriver dans quelques secondes. " + recu + " Rien ne s'affiche ? Regardez le mode Concentration et Réglages → Notifications → Iris.";
      else if (r.status === 429) etat.textContent = "Un essai par minute. " + recu;
      else if (j.inscrit === false) { afficher(false, "Ce téléphone n'était plus inscrit. Touchez « Activer les notifications » pour le réinscrire."); }
      else etat.textContent = (j.erreur || "L'essai n'est pas parti.") + " " + recu;
    } catch (e) {
      etat.textContent = "L'essai n'est pas parti. Réessayez dans un instant.";
    } finally {
      test.disabled = false;
    }
  });
  options.forEach((opt) => opt.addEventListener("change", async () => {
    const abo = enregistrement && await enregistrement.pushManager.getSubscription();
    if (!abo) { opt.checked = false; return; }
    const sujets = ["articles", ...options.filter((o) => o.checked).map((o) => o.dataset.pushSujet)];
    opt.disabled = true;
    try {
      const r = await envoyerAbonnement(abo, sujets);
      if (!r.ok) throw new Error("abonnement");
      garderSujets(sujets);
      etat.textContent = "Activées : nouveaux articles" + sujets.slice(1).map((s) => ", " + NOMS_SUJETS[s]).join("") + ".";
    } catch (e) {
      opt.checked = !opt.checked;
      etat.textContent = "Ça n'a pas marché. Réessayez dans un instant.";
    } finally {
      opt.disabled = false;
    }
  }));
})();

show(location.hash.slice(1));

/* ---------- IRIS Plus : la météo de la semaine et « Et si… ? » ----------
   Le texte vient de plus.json (écrit par la rédaction) ; les jours et les coupures de la météo viennent
   des mesures de la sonde (figées dans l'édition, sinon donnees/semaine.json). Rien n'est déduit au-delà.
   Dans plus.json, **mot** met un mot en gras. */
const SEM_JOUR = ["Dim.", "Lun.", "Mar.", "Mer.", "Jeu.", "Ven.", "Sam."];
const echap = (s) => String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const riche = (s) => echap(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
const jourDe = (iso) => new Date(iso + "T12:00:00Z");
const dateCourte = (iso) => jourDe(iso).toLocaleDateString("fr-FR", { day: "numeric", month: "long", timeZone: "Europe/Paris" });
const dateMini = (iso) => jourDe(iso).toLocaleDateString("fr-FR", { day: "numeric", month: "short", timeZone: "Europe/Paris" });
const dateLongue = (iso) => jourDe(iso).toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long", timeZone: "Europe/Paris" });
const periode = (e) => `du ${e.du.slice(5, 7) === e.au.slice(5, 7) ? jourDe(e.du).getUTCDate() : dateCourte(e.du)} au ${dateCourte(e.au)}`;
const titreSurligne = (a) => {
  const q = echap(a.question), s = echap(a.surligne || "");
  return s && q.endsWith(s) ? q.slice(0, -s.length) + `<mark>${s}</mark>` : q;
};
const ETAPES = [
  ["1. La question", null],
  ["2. Ce qui existe déjà", "Les faits observés, les solutions déjà en place, tous sourcés."],
  ["3. Là où ça coince", "Les limites concrètes : matériel, batterie, services qui repassent par le cloud, promesses non tenues."],
  ["4. La vraie question", "Ce que ça change pour nous, au quotidien : ce qu'on y gagne (ou on y perd), selon les usages."],
  ["5. Le geste", "Une chose simple à tester ou à faire pour être plus préparé·e."],
];
var PLUS, SEMAINE, PLUS_ATTENTE;   // var sans valeur : show() peut être appelé avant cette ligne, sans que rien ne soit effacé

function editionMesures(e) {
  const m = e.mesures || {};
  return {
    jours: (m.jours || (SEMAINE && SEMAINE.jours) || []).filter((j) => j.date >= e.du && j.date <= e.au),
    coupures: (m.coupures || (SEMAINE && SEMAINE.coupures) || []).filter((c) => c.jour >= e.du && c.jour <= e.au),
    suivis: m.suivis || (SEMAINE && SEMAINE.suivis) || {},
    methode: m.methode || (SEMAINE && SEMAINE.methode) || "",
  };
}

/* ----- Page d'accueil d'IRIS Plus ----- */
function plusHero(a) {
  return `
    <div class="ph-haut">
      <div class="ph-texte">
        <span class="ph-kicker">Et si…</span>
        <h2 class="plus-titre">${titreSurligne(a)}</h2>
        <p class="ph-chapo">${echap(a.chapo)}</p>
        <p class="ph-temps">${echap(a.temps_lecture)} de lecture</p>
      </div>
      <div class="ph-image" style="background-image:url('${echap(a.image)}')" aria-hidden="true"></div>
    </div>
    <ol class="ph-etapes">${ETAPES.map(([t, d]) => `<li><b>${t}</b><span>${echap(d || a.question)}</span></li>`).join("")}</ol>
    <a class="ph-cta" href="#plus-etsi-${echap(a.id)}">Explorer l'analyse →</a>`;
}

function plusMeteoCarte(e) {
  return `
    <div class="pc-head"><h4>La météo de la semaine</h4><span class="pc-pill">Chaque dimanche</span></div>
    <h3 class="pc-titre">Semaine ${periode(e)}</h3>
    <p class="pc-sous">L'essentiel tech en un coup d'œil.</p>
    <ul class="pc-lignes">${(e.essentiel || []).map((x) => `<li><span class="pc-cat">${echap(x.categorie)}</span><span>${echap(x.texte)}</span></li>`).join("")}</ul>
    <a class="pc-cta" href="#plus-meteo">Voir la météo complète</a>`;
}

function plusProchains(liste) {
  return `
    <h4 class="pc-grand">Prochains « Et si… »</h4>
    <ul class="pc-prochains">${(liste || []).map((x) => `<li><span class="pc-date">${dateMini(x.date)}</span><b>${echap(x.question)}</b></li>`).join("") || `<li class="muted">Programme à venir.</li>`}</ul>`;
}

function plusCartes(plus) {
  const publies = (plus.et_si || []).slice(1).map((a) => `<a class="plus-mini" href="#plus-etsi-${echap(a.id)}">
      <div class="pm-img" style="background-image:url('${echap(a.image)}')"></div>
      <div class="pm-corps"><b>${echap(a.question)}</b><span>${echap(a.temps_lecture)} de lecture</span></div></a>`);
  const bientot = (plus.a_venir || []).map((a) => `<div class="plus-mini pm-bientot">
      <div class="pm-img" style="background-image:url('${echap(a.image)}')"></div>
      <div class="pm-corps"><b>${echap(a.question)}</b><span>Bientôt</span></div></div>`);
  return [...publies, ...bientot].slice(0, 3).join("");
}

/* ----- La météo de la semaine, en entier ----- */
function meteoComplete(e) {
  const { coupures, methode } = editionMesures(e);
  // Premier chiffre calculé sur les mesures : jours avec au moins une coupure, par fournisseur.
  const parFour = {};
  coupures.forEach((c) => { (parFour[c.nom] = parFour[c.nom] || new Set()).add(c.jour); });
  const calcules = Object.entries(parFour).map(([nom, j]) => ({ chiffre: String(j.size), texte: `jour${j.size > 1 ? "s" : ""} avec des coupures chez ${nom}` }));
  const coup = [...calcules, ...(e.coup_doeil || [])].slice(0, 3);
  const plage = (c) => c.a ? `${c.de} → ${c.a}` : `À partir de ${c.de}<small>(toujours en échec au dernier passage)</small>`;
  const [premier, ...suite] = e.temps || [];
  return `
  <section class="pl-hero pl-hero-meteo" style="--pl-img:url('${echap(e.image || "assets/photos/meteo-semaine.jpg")}')">
    <nav class="pl-fil"><a href="#plus">IRIS Plus</a><span>›</span>La météo de la semaine</nav>
    <span class="pl-kicker">La météo de la semaine · ${periode(e)}</span>
    <h1 class="pl-titre">${echap(e.titre)}</h1>
    ${e.chapo ? `<p class="pl-chapo">${echap(e.chapo)}</p>` : ""}
  </section>
  <div class="pl-corps"><div class="pl-int">
    ${coup.length ? `<div class="pl-coup"><h3><span class="barre-j"></span>En un coup d'œil</h3>${coup.map((x) => `<div>${x.chiffre ? `<strong>${echap(x.chiffre)}</strong>` : ""}<span>${x.fort ? `<b>${echap(x.fort)}</b>` : ""}${echap(x.texte)}</span></div>`).join("")}</div>` : ""}
    <div class="pl-deux">
      <div class="pl-gauche">
        <h3><span class="barre-j"></span>Le temps qu'il a fait</h3>
        ${premier ? `<p>${riche(premier)}</p>` : ""}
        <div data-acces="plus">
          ${suite.map((x) => `<p>${riche(x)}</p>`).join("")}
          ${(e.touche || []).length ? `<hr/><h3><span class="barre-j"></span>Ce qui a pu vous toucher</h3>` + e.touche.map((x) => `<div class="pl-touche">${x.marque ? `<span class="pl-marque">${echap(x.marque)}</span>` : "<span></span>"}<div><p><b>${echap(x.titre)}</b> ${riche(x.texte)}</p>${x.source && x.source.url ? `<a class="pl-src" href="${echap(x.source.url)}" target="_blank" rel="noopener">${echap(x.source.label || "Source")} ↗</a>` : ""}</div></div>`).join("") : ""}
          ${e.prevision ? `<hr/><h3><span class="barre-j"></span>La prévision</h3><p>${riche(e.prevision)}</p>` : ""}
        </div>
      </div>
      <aside class="pl-droite" data-acces="plus">
        ${coupures.length ? `<div class="pl-encart"><h3>Les coupures mesurées</h3><table class="pl-table">${coupures.map((c) => `<tr><th>${SEM_JOUR[jourDe(c.jour).getUTCDay()]} ${jourDe(c.jour).getUTCDate()}</th><td>${echap(c.nom)}</td><td>${plage(c)}</td></tr>`).join("")}</table><p class="pl-note">${echap(methode)}</p></div>` : ""}
        ${e.geste ? `<div class="pl-geste"><h3><span class="barre-n"></span>Le geste de la semaine</h3><p>${riche(e.geste)}</p><p class="pl-rappel">À titre indicatif : mesures externes et automatisées, à vérifier avec votre équipe informatique et vos fournisseurs.</p></div>` : ""}
      </aside>
    </div>
    ${(PLUS.meteo_semaine || []).length > 1 ? `<div class="pl-archives" data-acces="plus"><h3><span class="barre-j"></span>Les semaines précédentes</h3><ul>${PLUS.meteo_semaine.filter((x) => x !== e).map((x) => `<li><a href="#plus-meteo-${echap(x.id)}">Semaine ${periode(x)} · ${echap(x.titre)}</a></li>`).join("")}</ul></div>` : ""}
  </div></div>`;
}

/* ----- Un « Et si… ? », en entier ----- */
function etSiComplet(a) {
  const st = a.sous_titres || {};
  const puces = (x) => `<ul class="pl-puces">${(x || []).map((p) => `<li>${riche(p)}</li>`).join("")}</ul>`;
  const partie = (n, titre, sousTitre, contenu) => `<section class="pl-partie"><div class="pl-num"><span>${n}.</span><h3>${titre}</h3></div><div class="pl-contenu">${sousTitre ? `<h4>${riche(sousTitre)}</h4>` : ""}${contenu}</div></section>`;
  const source = (s) => { const [nom, ...reste] = String(s.label).split(" : "); return `<li><a href="${echap(s.url)}"${s.url.startsWith("#") ? "" : ' target="_blank" rel="noopener"'}><b>${echap(nom)}</b>${reste.length ? " : " + echap(reste.join(" : ")) : ""}</a></li>`; };
  return `
  <section class="pl-hero pl-hero-etsi" style="--pl-img:url('${echap(a.image_entete || a.image)}')">
    <nav class="pl-fil"><a href="#plus">← IRIS Plus</a><span>›</span>Et si…</nav>
    <span class="pl-kicker">Et si… — ${dateLongue(a.publie_le)}</span>
    <h1 class="pl-titre plus-titre">${titreSurligne(a)}</h1>
    <p class="pl-chapo">${echap(a.chapo)}</p>
    <p class="pl-temps">${echap(a.temps_lecture)} de lecture</p>
  </section>
  <div class="pl-corps"><div class="pl-int pl-corps-etsi">
    <div class="pl-gauche">
      ${partie(1, "La question", st.et_si, (a.et_si || []).map((p) => `<p>${riche(p)}</p>`).join(""))}
      <div data-acces="plus">
        ${partie(2, "Ce qui existe déjà", st.existe_deja, puces(a.existe_deja))}
        ${partie(3, "Là où ça coince", st.ca_coince, puces(a.ca_coince))}
        ${partie(4, "La vraie question", st.vraie_question, puces(a.vraie_question))}
        ${a.geste ? partie(5, "Le geste", null, `<div class="pl-geste pl-geste-court">${st.geste ? `<h4>${riche(st.geste)}</h4>` : ""}<p>${riche(a.geste)}</p></div>`) : ""}
      </div>
    </div>
    <aside class="pl-droite">
      ${(a.en_bref || []).length ? `<div class="pl-encart"><h3><span class="barre-j"></span>En bref</h3><dl class="pl-bref">${a.en_bref.map((x) => `<dt>${echap(x.label)}</dt><dd>${riche(x.texte)}</dd>`).join("")}</dl></div>` : ""}
      ${(a.sources || []).length ? `<div class="pl-encart" data-acces="plus"><h3><span class="barre-j"></span>Sources</h3><ul class="pl-sources">${a.sources.map(source).join("")}</ul>${a.verifie_le ? `<p class="pl-note">Faits vérifiés le ${dateLongue(a.verifie_le)}.<br/>Ils sont revérifiés tous les six mois.</p>` : ""}</div>` : ""}
    </aside>
  </div></div>`;
}

function plusLecture(id) {
  if (!PLUS) { PLUS_ATTENTE = id; return; }
  const boite = document.getElementById("plus-lecture");
  const editions = PLUS.meteo_semaine || [];
  if (id === "analyses") {
    boite.innerHTML = `<section class="pl-hero pl-hero-liste"><nav class="pl-fil"><a href="#plus">← IRIS Plus</a><span>›</span>Toutes les analyses</nav>
      <span class="pl-kicker">Et si…</span><h1 class="pl-titre">Toutes les analyses</h1>
      <p class="pl-chapo">Un fait réel, et ses conséquences à explorer. Un nouveau sujet chaque mois.</p></section>
      <div class="plus-cartes plus-cartes-liste">${[...(PLUS.et_si || []).map((a) => `<a class="plus-mini" href="#plus-etsi-${echap(a.id)}"><div class="pm-img" style="background-image:url('${echap(a.image)}')"></div><div class="pm-corps"><b>${echap(a.question)}</b><span>${dateLongue(a.publie_le)} · ${echap(a.temps_lecture)} de lecture</span></div></a>`),
        ...(PLUS.a_venir || []).map((a) => `<div class="plus-mini pm-bientot"><div class="pm-img" style="background-image:url('${echap(a.image)}')"></div><div class="pm-corps"><b>${echap(a.question)}</b><span>Bientôt</span></div></div>`)].join("")}</div>`;
  } else if (id === "meteo" || id.startsWith("meteo-")) {
    const e = editions.find((x) => "meteo-" + x.id === id) || editions[0];
    boite.innerHTML = e ? meteoComplete(e) : `<p class="muted">La première météo de la semaine arrive dimanche.</p>`;
  } else {
    const a = (PLUS.et_si || []).find((x) => "etsi-" + x.id === id);
    boite.innerHTML = a ? etSiComplet(a) : `<p class="muted">Cet article n'existe pas ou n'est plus en ligne.</p>`;
  }
  window.scrollTo(0, 0);
}

Promise.all([frais("plus.json").then((r) => (r.ok ? r.json() : null)).catch(() => null), lire("semaine.json")])
  .then(([plus, semaine]) => {
    PLUS = plus || { meteo_semaine: [], et_si: [] };
    SEMAINE = semaine;
    const hero = (PLUS.et_si || [])[0];
    document.getElementById("plus-hero").innerHTML = hero ? plusHero(hero) : `<p class="muted">Le premier « Et si… ? » arrive bientôt.</p>`;
    const e = (PLUS.meteo_semaine || [])[0];
    document.getElementById("plus-meteo-carte").innerHTML = e ? plusMeteoCarte(e) : `<p class="muted">La première météo de la semaine arrive dimanche.</p>`;
    document.getElementById("plus-prochains").innerHTML = plusProchains(PLUS.prochains_et_si);
    if (PLUS_ATTENTE) { plusLecture(PLUS_ATTENTE); PLUS_ATTENTE = null; }
  });


/* ---------- Le réglage « Temps de lecture » (cloche) ---------- */
(function reglageDuree() {
  const choix = [...document.querySelectorAll('input[name="iris-duree"]')];
  if (!choix.length) return;
  const actuel = lireDuree();
  choix.forEach((c) => {
    c.checked = c.value === actuel;
    c.addEventListener("change", () => {
      try { localStorage.setItem(DUREE_CLE, c.value); } catch (e) { /* navigation privée */ }
      Object.keys(MODES).forEach((k) => delete MODES[k]);   // le nouveau réglage vaut pour les prochains articles ouverts
    });
  });
})();

/* ---------- « L'essentiel du jour en 2 minutes » : les stories d'Iris ----------
   Seulement ce qui est nouveau depuis la dernière fois (mémorisé sur l'appareil), à son rythme :
   aucun défilement automatique. La météo dit « pas de mesure récente » quand la sonde n'a pas tourné. */
const ESS_VU = "iris-essentiel-vu";
const echapE = (t) => String(t == null ? "" : t).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const texteSeul = (h) => propre(h).replace(/<br\s*\/?>/g, " ").replace(/<\/?mark>/g, "").replace(/\s+/g, " ").replace(/ \./g, ".").trim();
function diapositivesEssentiel() {
  let vu = null;
  try { vu = localStorage.getItem(ESS_VU); } catch (e) { /* */ }
  const depuis = vu || new Date(Date.now() - 2 * 864e5).toISOString();
  const nouveau = (x) => String(x.publie_le || (x.date ? x.date + "T23:59:59" : "")) > depuis;
  const d = [];
  const m = IRIS_METEO;
  if (m && (m.fournisseurs || []).length && document.body.dataset.plan === "premium") {   // Ma Météo est réservée à Premium
    const recente = Date.now() - new Date(m.genere_le) < 3 * 3600e3;
    d.push({ type: "meteo", kicker: "La météo des IA", titre: recente ? (m.phrase || "La météo du jour") : "Pas de mesure récente",
      lignes: m.fournisseurs.map((f) => [f.nom_court || f.nom, recente ? (METEO_MOT[f.etat] || "Pas de mesure.").replace(/\.$/, "") : "pas de mesure récente"]),
      note: recente ? `Mesures de la sonde Iris, ${ilYa(m.genere_le)}.` : `Dernière mesure de la sonde ${ilYa(m.genere_le)}.`, lien: "#meteo", libelle: "Voir la météo" });
  }
  const pub = PUB || {};
  const articles = [...(pub.une || []).map((a) => ({ ...a, rub: "À la une" })), ...(pub.tous_connectes || []).map((a) => ({ ...a, rub: "Tous connectés" }))]
    .filter((a) => a.id && a.mini && a.mini.fait && nouveau(a))
    .sort((x, y) => String(y.publie_le || y.date).localeCompare(String(x.publie_le || x.date))).slice(0, 4);
  articles.forEach((a) => d.push({ type: "article", kicker: a.rub, img: a.img, titre: texteSeul(a.title),
    texte: `${a.mini.fait} ${a.mini.consequence}`, reflexe: (a.reflexes || [])[0], lien: `#article-${a.id}`, libelle: "Lire en entier", id: a.id }));
  const det = (pub.detour || []).filter(nouveau).sort((x, y) => String(y.publie_le || "").localeCompare(String(x.publie_le || "")))[0];
  if (det) d.push({ type: "detour", kicker: `Le Détour · ${det.source}`, img: `assets/photos/${det.img}.jpg`, titre: det.title, texte: det.why, lien: det.url, externe: true, libelle: "Lire chez " + det.source });
  const P = window.PLUS || {};
  const abonne = document.body.dataset.plan !== "standard";
  const ms = (P.meteo_semaine || [])[0];
  if (ms && String(ms.id || ms.au || "") + "T23:59:59" > depuis) d.push({ type: "plus", kicker: "Iris Plus · La météo de la semaine", img: ms.image,
    titre: ms.titre, texte: abonne ? ms.chapo : "Réservé aux abonnés Iris Plus.", lien: abonne ? "#plus-meteo" : "#plus", libelle: abonne ? "Lire la météo" : "Découvrir Iris Plus" });
  const es = (P.et_si || [])[0];
  if (es && String(es.publie_le || "") + "T23:59:59" > depuis) d.push({ type: "plus", kicker: "Iris Plus · Et si… ?", img: es.image,
    titre: es.question, texte: abonne ? (es.en_bref || []).slice(0, 2).map((x) => (x && x.texte) || x).join(" ") : "Réservé aux abonnés Iris Plus.", lien: abonne ? `#plus-etsi-${es.id}` : "#plus", libelle: abonne ? "Lire l'analyse" : "Découvrir Iris Plus" });
  if (d.every((x) => x.type === "meteo")) d.push({ type: "rien", titre: "Rien de neuf depuis votre dernière visite.", texte: "Iris publie quand il y a quelque chose à dire. Revenez demain matin." });
  const rs = [...(pub.tous_connectes || [])].filter((a) => a.reflexe_semaine).sort((x, y) => String(y.date || "").localeCompare(String(x.date || "")))[0];
  d.push({ type: "fin", titre: "Vous êtes à jour.", texte: rs ? `Le réflexe de la semaine : <b>${echapE(rs.reflexe_semaine.titre)}.</b> ${echapE(rs.reflexe_semaine.texte)}` : "L'essentiel d'Iris en 2 minutes, chaque jour." });
  return d;
}
(function essentiel() {
  const ecran = document.getElementById("essentiel");
  if (!ecran) return;
  const barres = document.getElementById("ess-barres");
  const zone = document.getElementById("ess-slide");
  const lire = document.getElementById("ess-lire");
  const suivant = document.getElementById("ess-suivant");
  const precedent = document.getElementById("ess-precedent");
  let d = [], i = 0, dernierFocus = null, fini = false;
  const peindre = () => {
    const s = d[i];
    barres.innerHTML = d.map((_, k) => `<span class="${k <= i ? "on" : ""}"></span>`).join("");
    const img = s.img ? `<div class="ess-img" style="background-image:url('${echapE(s.img)}')" role="img" aria-label=""></div>` : "";
    if (s.type === "meteo") zone.innerHTML = `<span class="ess-tag ess-tag-j">${s.kicker}</span><h2>${echapE(s.titre)}</h2>
      <ul class="ess-meteo">${s.lignes.map(([n, e]) => `<li><b>${echapE(n)}</b><span>${echapE(e)}</span></li>`).join("")}</ul><p class="ess-petit">${s.note}</p>`;
    else if (s.type === "fin" || s.type === "rien") zone.innerHTML = `<div class="ess-barre-j"></div><h2>${echapE(s.titre)}</h2><p>${s.texte}</p>`;
    else zone.innerHTML = `${img}<span class="ess-tag">${echapE(s.kicker)}</span><h2>${echapE(s.titre)}</h2><p>${echapE(s.texte)}</p>
      ${s.reflexe ? `<p class="ess-reflexe"><b>Le bon réflexe :</b> ${propre(s.reflexe)}</p>` : ""}`;
    lire.hidden = !s.lien;
    lire.textContent = s.libelle || "";
    precedent.disabled = i === 0;
    suivant.textContent = i === d.length - 1 ? "Terminer" : "Suivant";
    if (s.type === "fin" && !fini) {
      fini = true;
      try { localStorage.setItem(ESS_VU, new Date().toISOString()); } catch (e) { /* */ }
      compterEvenement("stories_fin", "article-essentiel");
    }
  };
  const ouvrir = () => {
    d = diapositivesEssentiel(); i = 0; fini = false;
    dernierFocus = document.activeElement;
    ecran.hidden = false;
    document.body.classList.add("ess-ouvert");
    peindre();
    compterEvenement("stories_debut", "article-essentiel");
    ecran.querySelector("[data-fermer-essentiel]").focus();
  };
  const fermer = () => {
    ecran.hidden = true;
    document.body.classList.remove("ess-ouvert");
    if (dernierFocus) dernierFocus.focus();
  };
  document.addEventListener("click", (e) => {
    if (e.target.closest("[data-ouvrir-essentiel]")) { e.preventDefault(); ouvrir(); }
    else if (e.target.closest("[data-fermer-essentiel]")) fermer();
  });
  suivant.addEventListener("click", () => { if (i < d.length - 1) { i++; peindre(); } else fermer(); });
  precedent.addEventListener("click", () => { if (i > 0) { i--; peindre(); } });
  lire.addEventListener("click", () => {
    const s = d[i];
    if (!s || !s.lien) return;
    if (s.externe) { window.open(s.lien, "_blank", "noopener"); return; }
    if (s.id) MODES[s.id] = "long";
    fermer();
    location.hash = s.lien;
  });
  document.addEventListener("keydown", (e) => {
    if (ecran.hidden) return;
    if (e.key === "Escape") fermer();
    else if (e.key === "ArrowRight") suivant.click();
    else if (e.key === "ArrowLeft") precedent.click();
  });
})();


/* ---------- Le mercato de l'IA : qui quitte qui (encadré de l'À la une) ----------
   Une ligne = un changement de fournisseur annoncé publiquement, avec sa source (iris/mercato.json, lu en direct).
   « Ce qu'elle dit » reste ce que l'entreprise affirme : jamais présenté comme un fait. */
function htmlSur(t) {
  return String(t == null ? "" : t).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function moisCourt(aaaaMm) {
  const [a, m] = String(aaaaMm || "").split("-").map(Number);
  return a && m ? `${MOIS[m - 1]} ${a}` : "";
}
// Une ligne du mercato. complet : avec « Ce qu'elle dit » et la source (tableau complet).
function ligneMercato(x, complet) {
  return `<li class="mx">
      <div class="mx-top"><b>${htmlSur(x.entreprise)}</b><span>${htmlSur(x.secteur)} · ${htmlSur(x.pays)} · ${moisCourt(x.date)}</span></div>
      <div class="mx-move"><span class="mx-from">${htmlSur((x.quitte || []).join(", "))}</span><span class="mx-arrow" aria-label="vers">→</span><span class="mx-to">${htmlSur(x.pour)}</span></div>
      ${x.en_partie || complet ? `<p class="mx-how">${complet ? htmlSur(x.comment) : ""}${x.en_partie ? ' <em class="mx-partie">en partie</em>' : ""}</p>` : ""}
      ${complet ? `<div class="mx-dit"><p><b>Ce qu'elle dit.</b> ${htmlSur(x.dit)}</p>${x.source && /^https:\/\//.test(x.source.url || "") ? `<a href="${htmlSur(x.source.url)}" target="_blank" rel="noopener">Source : ${htmlSur(x.source.media)} ↗</a>` : ""}</div>` : ""}
    </li>`;
}
function constatMercato(t) {
  const noms = { chine: "chinois", usa: "américains", europe: "européens" };
  const parOrigine = {};
  t.forEach((x) => { parOrigine[x.pour_origine] = (parOrigine[x.pour_origine] || 0) + 1; });
  const [orig, nb] = Object.entries(parOrigine).sort((a, b) => b[1] - a[1])[0] || [];
  return nb > 1 && noms[orig] ? `<p class="mx-constat"><b>${nb} transferts sur ${t.length}</b> vont vers des modèles ${noms[orig]}.</p>` : "";
}
function rendreMercato(d, complet = false) {
  const t = (d && d.transferts) || [];
  if (!t.length) return "";
  const maj = d.mis_a_jour ? new Date(d.mis_a_jour + "T12:00").toLocaleDateString("fr-FR", { day: "numeric", month: "long" }) : "";
  return `${complet ? "" : `<div class="mx-image" role="img" aria-label="Une main robotique déplace un pion sur un échiquier"></div>`}
    <div class="mx-corps">
    <p class="mx-titre"${complet ? ' id="mxc-titre"' : ""}>Le mercato de l'IA</p>
    ${constatMercato(t)}
    <ol class="mx-list">${(complet ? t : t.slice(0, 4)).map((x) => ligneMercato(x, complet)).join("")}</ol>
    ${complet ? `<p class="mx-pied">Une entreprise, c'est une anecdote. Plusieurs, une tendance. Chaque transfert a sa source : un changement annoncé publiquement ou rapporté par un média reconnu. « Ce qu'elle dit » est ce que l'entreprise affirme, pas un fait vérifié par Iris.${maj ? ` <span>Mis à jour le ${maj}.</span>` : ""}</p>`
      : `<button type="button" class="mx-tout" data-ouvrir-mercato>Voir le tableau complet <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 4h6v6M20 4l-9 9M18 14v6H4V6h6"/></svg></button>`}
    </div>`;
}
(function mercato() {
  const el = document.querySelector("[data-mercato]");
  const ecran = document.getElementById("mercato-complet");
  if (!el) return;
  let donnees = null;
  const ouvrir = () => {
    if (!ecran || !donnees) return;
    document.getElementById("mxc-contenu").innerHTML = rendreMercato(donnees, true);
    ecran.hidden = false; document.body.style.overflow = "hidden";
    ecran.querySelector("[data-fermer-mercato]").focus();
  };
  const fermer = () => { if (ecran) { ecran.hidden = true; document.body.style.overflow = ""; } };
  document.addEventListener("click", (e) => {
    if (e.target.closest("[data-ouvrir-mercato]")) { e.preventDefault(); ouvrir(); }
    else if (e.target.closest("[data-fermer-mercato]") || e.target === ecran) fermer();
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && ecran && !ecran.hidden) fermer(); });
  frais("mercato.json").then((r) => (r.ok ? r.json() : null)).then((d) => {
    const h = rendreMercato(d);
    if (!h) return;
    donnees = d; el.innerHTML = h; el.hidden = false;
    // Depuis une notification du mercato : /?mercato=1#une ouvre le tableau complet.
    if (new URLSearchParams(location.search).get("mercato") === "1") ouvrir();
  }).catch(() => {});
})();
if (typeof module !== "undefined") module.exports = { rendreMercato };
