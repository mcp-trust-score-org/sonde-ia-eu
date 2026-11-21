// POST /api/abonner   : enregistre un appareil (le navigateur envoie son abonnement).
// DELETE /api/abonner : le retire (bouton « Désactiver »).
const stockage = require("./_stockage");

function valide(abo) {
  return abo && typeof abo.endpoint === "string" && /^https:\/\//.test(abo.endpoint) && abo.endpoint.length < 1000
    && abo.keys && typeof abo.keys.p256dh === "string" && typeof abo.keys.auth === "string";
}

module.exports = async (req, res) => {
  const abo = typeof req.body === "string" ? JSON.parse(req.body || "{}") : req.body;
  try {
    if (req.method === "POST") {
      if (!valide(abo)) return res.status(400).json({ erreur: "Abonnement invalide." });
      await stockage.ajouter({ endpoint: abo.endpoint, keys: { p256dh: abo.keys.p256dh, auth: abo.keys.auth } });
      return res.status(201).json({ ok: true });
    }
    if (req.method === "DELETE") {
      if (!abo || !abo.endpoint) return res.status(400).json({ erreur: "Adresse d'abonnement manquante." });
      await stockage.retirer(abo.endpoint);
      return res.status(200).json({ ok: true });
    }
    res.setHeader("Allow", "POST, DELETE");
    return res.status(405).json({ erreur: "Méthode non permise." });
  } catch (e) {
    return res.status(500).json({ erreur: e.message });
  }
};
