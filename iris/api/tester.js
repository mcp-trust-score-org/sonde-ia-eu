// POST /api/tester : envoie une notification d'essai à CET appareil seulement (bouton « M'envoyer un test »).
// Corps : { "endpoint": "https://…" } — l'adresse d'abonnement du navigateur.
// Répond { inscrit, sujets } : on voit tout de suite ce que le site a vraiment enregistré pour ce téléphone.
// Un essai par minute et par appareil au plus.
const webpush = require("web-push");
const crypto = require("crypto");
const stockage = require("./_stockage");

module.exports = async (req, res) => {
  if (req.method !== "POST") return res.status(405).json({ erreur: "Méthode non permise." });
  const corps = typeof req.body === "string" ? JSON.parse(req.body || "{}") : req.body || {};
  if (typeof corps.endpoint !== "string" || !/^https:\/\//.test(corps.endpoint)) return res.status(400).json({ erreur: "Adresse manquante." });
  const { VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_SUBJECT } = process.env;
  if (!VAPID_PUBLIC_KEY || !VAPID_PRIVATE_KEY) return res.status(503).json({ erreur: "Clés VAPID absentes." });
  try {
    const abo = await stockage.un(corps.endpoint);
    if (!abo) return res.status(200).json({ inscrit: false, sujets: [] });
    const marque = "iris:test:" + crypto.createHash("sha256").update(corps.endpoint).digest("hex").slice(0, 24);
    if (!(await stockage.commande("SET", marque, "1", "NX", "EX", "60"))) return res.status(429).json({ inscrit: true, sujets: abo.sujets || [], erreur: "Un essai par minute." });
    webpush.setVapidDetails(VAPID_SUBJECT || "mailto:contact@iris.example", VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY);
    try {
      await webpush.sendNotification(abo, JSON.stringify({
        tag: "iris-test", titre: "Iris · notification d'essai",
        texte: "Ça marche : ce téléphone reçoit bien les notifications d'Iris.", url: "/",
      }), { TTL: 600 });
    } catch (e) {
      if (e.statusCode === 404 || e.statusCode === 410) { await stockage.retirer(abo.endpoint); return res.status(200).json({ inscrit: false, sujets: [], perime: true }); }
      return res.status(502).json({ inscrit: true, sujets: abo.sujets || [], erreur: "Le service de notifications du téléphone a refusé (" + (e.statusCode || "?") + " " + String(e.body || e.message || "").slice(0, 120) + ")." });
    }
    return res.status(200).json({ inscrit: true, sujets: abo.sujets || [], envoye: true });
  } catch (e) {
    return res.status(500).json({ erreur: e.message });
  }
};
