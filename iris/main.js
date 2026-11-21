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
  maj: {
    tag: "Retour sur · juillet 2024", img: "assets/photos/logiciel.jpg", time: "5 min", demo: false,
    title: "Une mise à jour de routine.<br/><mark>8,5 millions</mark> d'écrans bleus.",
    chapo: "En juillet 2024, un fichier de mise à jour d'un logiciel de sécurité a bloqué des millions d'ordinateurs Windows en quelques heures. Le rappel le plus spectaculaire de notre dépendance à un seul maillon.",
    fait: ["Le 19 juillet 2024, l'éditeur de cybersécurité CrowdStrike publie une mise à jour de contenu pour son agent Falcon.", "Une opération de routine, du genre qu'aucun dirigeant ne suit."],
    consequence: ["Le fichier est défectueux. Les ordinateurs Windows qui le reçoivent plantent et redémarrent en boucle : environ 8,5 millions de machines selon Microsoft.", "Compagnies aériennes, hôpitaux, banques, chaînes de télévision : pendant des heures, et des jours pour certains, l'activité s'arrête."],
    lien: ["Le maillon faible n'était ni le cloud ni le réseau, mais un logiciel présent partout. C'est précisément ce que DORA demande de cartographier : vos prestataires critiques, et ceux dont ils dépendent eux-mêmes.", "Plus de deux ans après, la question reste entière : savez-vous quels logiciels, chez vos fournisseurs, pourraient vous arrêter du jour au lendemain ?"],
    impact: {
      status: "Aucune anomalie mesurée chez vos fournisseurs", level: "green",
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
      status: "Vous êtes concerné", level: "red",
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
      status: "Aucune anomalie mesurée chez vos fournisseurs", level: "green",
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

function renderArticle(id) {
  const a = ARTICLES[id];
  const el = document.getElementById("article");
  if (!a || !el) return false;
  const paras = (arr) => arr.map((p) => `<p>${p}</p>`).join("");
  const pub = a.audience === "public" || a.audience === "detour";
  const backTo = a.audience === "public" ? ["#vies", "Tous connectés"] : a.audience === "detour" ? ["#detour", "Le Détour"] : ["#une", "À la une"];
  const visual = `<div class="art-img${a.img.includes("/photos/") ? " art-photo" : ""}" style="background-image:url('${a.img}')"></div>`;
  const srcList = a.sources || (a.source ? [a.source] : []);
  const srcHtml = srcList.length ? `<div class="art-source"><b>${srcList.length > 1 ? "Sources" : "Source"}</b>${srcList.map((x) => `<a href="${x.url}" target="_blank" rel="noopener">${x.label} ↗</a>`).join("")}</div>` : "";
  const ending = pub
    ? `${a.reflexes ? `<section class="impact impact-reflex">
        <p class="impact-kicker">Le bon réflexe</p>
        <ul class="reflexes">${a.reflexes.map((r) => `<li>${r}</li>`).join("")}</ul>
      </section>` : ""}
      ${srcHtml}
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
      </section>
      ${srcHtml}`;
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
  { source: "404 Media", cat: "Logiciel", img: "innovation", date: "2026-11-17", title: "« BREAKING: Everything » : quand tout repose sur la même pièce (en anglais)", why: "La célèbre tour de logiciels qui tient sur une seule brique, appliquée à tout le reste.", url: "https://www.404media.co/breaking-everything/" },
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
const VIEWS = ["relecture", "une", "vies", "meteo", "alertes", "indicateurs", "detour", "rapports"];
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
fetch("publies.json", { cache: "no-store" })
  .then((r) => (r.ok ? r.json() : null))
  .then((pub) => {
    if (!pub) return;
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

  bouton.addEventListener("click", (e) => {
    e.stopPropagation();
    panneau.hidden = !panneau.hidden;
    bouton.setAttribute("aria-expanded", String(!panneau.hidden));
  });
  document.addEventListener("click", (e) => {
    if (!panneau.hidden && !panneau.contains(e.target)) { panneau.hidden = true; bouton.setAttribute("aria-expanded", "false"); }
  });

  function cle(base64) {   // clé publique VAPID → format attendu par le navigateur
    const b = (base64 + "=".repeat((4 - (base64.length % 4)) % 4)).replace(/-/g, "+").replace(/_/g, "/");
    return Uint8Array.from(atob(b), (c) => c.charCodeAt(0));
  }
  function afficher(abonne, message) {
    bouton.classList.toggle("on", abonne);
    etat.textContent = message || (abonne ? "Activées sur cet appareil." : "Une notification à chaque article publié.");
    action.textContent = abonne ? "Désactiver" : "Activer les notifications";
    action.dataset.abonne = abonne ? "1" : "";
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
    afficher(Boolean(abo) && Notification.permission === "granted");
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
      const ok = await fetch("/api/abonner", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(abo) });
      if (!ok.ok) { await abo.unsubscribe(); throw new Error("abonnement"); }
      afficher(true, "C'est fait : vous serez prévenu à chaque nouvel article.");
    } catch (e) {
      afficher(false, "Ça n'a pas marché. Réessayez dans un instant.");
    } finally {
      action.disabled = false;
    }
  });
})();

show(location.hash.slice(1));
