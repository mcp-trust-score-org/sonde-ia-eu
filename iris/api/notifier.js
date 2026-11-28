// POST /api/notifier : envoie une notification à tous les appareils abonnés.
// Appelé par GitHub (Actions → « Publier un brouillon ») avec le secret NOTIF_SECRET.
// Corps : { "titre": "…", "texte": "…", "url": "/#article-…", "sujet": "articles" | "alertes" | "plus", "deux_modes": true,
//          "fournisseurs": ["anthropic", …] }  ← un mouvement du mercato : reçu aussi par ceux qui suivent ces fournisseurs (Iris Club)
// « plus » : envoyé par GitHub (plus.yml) quand une nouvelle météo de la semaine ou un « Et si… ? » est en ligne.
// Appelé aussi par la veille de la sonde (sonde/alertes.py) pour les alertes Premium, sujet « alertes ».
// Le mercato et le point du vendredi ne passent PLUS par ici : ils attendent le feu vert de la rédaction (/api/file).
const { envoyer } = require("./_envoi");

module.exports = async (req, res) => {
  if (req.method !== "POST") return res.status(405).json({ erreur: "Méthode non permise." });
  const secret = process.env.NOTIF_SECRET;
  if (!secret || req.headers.authorization !== `Bearer ${secret}`) return res.status(401).json({ erreur: "Non autorisé." });
  const corps = typeof req.body === "string" ? JSON.parse(req.body || "{}") : req.body || {};
  try {
    return res.status(200).json(await envoyer(corps));
  } catch (e) {
    return res.status(e.code || 500).json({ erreur: e.message });
  }
};
