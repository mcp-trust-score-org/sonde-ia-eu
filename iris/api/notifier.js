// POST /api/notifier : envoie une notification à tous les appareils abonnés.
// Appelé par GitHub (Actions → « Publier un brouillon ») avec le secret NOTIF_SECRET.
// Corps : { "titre": "…", "texte": "…", "url": "/#article-…", "sujet": "articles" | "alertes" | "plus", "deux_modes": true,
//          "fournisseurs": ["anthropic", …] }  ← un mouvement du mercato : reçu aussi par ceux qui suivent ces fournisseurs (Iris Club)
// « plus » : envoyé par GitHub (plus.yml) quand une nouvelle météo de la semaine ou un « Et si… ? » est en ligne.
// Appelé aussi par la veille de la sonde (sonde/alertes.py) pour les alertes Premium, sujet « alertes ».
const webpush = require("web-push");
const stockage = require("./_stockage");

module.exports = async (req, res) => {
  if (req.method !== "POST") return res.status(405).json({ erreur: "Méthode non permise." });
  const secret = process.env.NOTIF_SECRET;
  if (!secret || req.headers.authorization !== `Bearer ${secret}`) return res.status(401).json({ erreur: "Non autorisé." });
  const { VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_SUBJECT } = process.env;
  if (!VAPID_PUBLIC_KEY || !VAPID_PRIVATE_KEY) return res.status(503).json({ erreur: "Clés VAPID absentes." });
  webpush.setVapidDetails(VAPID_SUBJECT || "mailto:contact@iris.example", VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY);

  const corps = typeof req.body === "string" ? JSON.parse(req.body || "{}") : req.body || {};
  const sujet = ["alertes", "plus", "redaction"].includes(corps.sujet) ? corps.sujet : "articles";
  const message = JSON.stringify({
    tag: { alertes: "iris-alerte", plus: "iris-plus", redaction: "iris-redaction" }[sujet] || "iris-article",
    titre: String(corps.titre || "Iris · nouvel article").slice(0, 120),
    texte: String(corps.texte || "").slice(0, 240),
    url: /^\/[^/]/.test(corps.url || "") ? corps.url : "/",
    deux_modes: corps.deux_modes === true,   // un article : boutons « 2 min » / « En entier » (sw.js)
  });
  try {
    // Un appareil abonné avant les sujets ne reçoit que les articles.
    const concernes = Array.isArray(corps.fournisseurs) ? corps.fournisseurs : [];
    const abos = (await stockage.tous()).filter((a) => (Array.isArray(a.sujets) ? a.sujets : ["articles"]).includes(sujet)
      || (concernes.length && (a.fournisseurs || []).some((f) => concernes.includes(f))));
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
    return res.status(200).json({ abonnes: abos.length, envoyes, retires, echecs });
  } catch (e) {
    return res.status(500).json({ erreur: e.message });
  }
};
