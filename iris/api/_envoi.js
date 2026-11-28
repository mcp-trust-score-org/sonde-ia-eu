// L'envoi d'une notification aux appareils abonnés, partagé par /api/notifier (envois directs : articles, alertes,
// rappels) et /api/file (la file de validation du pilotage). Chaque envoi aux lecteurs est noté dans l'historique
// (iris:envois, les 50 derniers), visible dans le pilotage → Notifications → Envoyées.
const webpush = require("web-push");
const stockage = require("./_stockage");

const SUJETS = ["articles", "alertes", "plus", "redaction"];

function pret() {
  const { VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_SUBJECT } = process.env;
  if (!VAPID_PUBLIC_KEY || !VAPID_PRIVATE_KEY) throw Object.assign(new Error("Clés VAPID absentes."), { code: 503 });
  webpush.setVapidDetails(VAPID_SUBJECT || "mailto:contact@iris.example", VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY);
}

// corps : { titre, texte, url, sujet, deux_modes, fournisseurs } ; type : pour l'historique (« Article », « Mercato »…)
async function envoyer(corps, { type = null, journal = true } = {}) {
  pret();
  const sujet = SUJETS.includes(corps.sujet) ? corps.sujet : "articles";
  const message = JSON.stringify({
    tag: { alertes: "iris-alerte", plus: "iris-plus", redaction: "iris-redaction" }[sujet] || "iris-article",
    titre: String(corps.titre || "Iris · nouvel article").slice(0, 120),
    texte: String(corps.texte || "").slice(0, 240),
    url: /^\/[^/]/.test(corps.url || "") ? corps.url : "/",
    deux_modes: corps.deux_modes === true,   // un article : boutons « 2 min » / « En entier » (sw.js)
  });
  // Un appareil abonné avant les sujets ne reçoit que les articles. Un mouvement du mercato va aussi à ceux qui
  // suivent les fournisseurs concernés (Iris Club).
  const concernes = Array.isArray(corps.fournisseurs) ? corps.fournisseurs : [];
  const abos = (await stockage.tous()).filter((a) => (Array.isArray(a.sujets) ? a.sujets : ["articles"]).includes(sujet)
    || (sujet !== "redaction" && concernes.length && (a.fournisseurs || []).some((f) => concernes.includes(f))));
  let envoyes = 0, retires = 0, echecs = 0;
  await Promise.all(abos.map(async (abo) => {
    try {
      await webpush.sendNotification(abo, message, { TTL: 24 * 3600 });
      envoyes++;
    } catch (e) {
      if (e.statusCode === 404 || e.statusCode === 410) { await stockage.retirer(abo.endpoint); retires++; }
      else echecs++;
    }
  }));
  if (journal && sujet !== "redaction") {
    const ligne = { quand: new Date().toISOString(), type: type || { alertes: "Alerte", plus: "Iris Plus" }[sujet] || "Article",
      titre: String(corps.titre || "").slice(0, 160), texte: String(corps.texte || "").slice(0, 240), sujet, recus: envoyes };
    try {
      await stockage.commande("LPUSH", "iris:envois", JSON.stringify(ligne));
      await stockage.commande("LTRIM", "iris:envois", 0, 49);
    } catch (e) { /* l'historique ne doit jamais bloquer un envoi */ }
  }
  return { abonnes: abos.length, envoyes, retires, echecs };
}

module.exports = { envoyer, SUJETS };
