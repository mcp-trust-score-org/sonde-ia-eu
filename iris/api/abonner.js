// POST /api/abonner   : enregistre un appareil (le navigateur envoie son abonnement et ses sujets :
//                       « articles », et en option « plus » pour IRIS Plus
//                       et « alertes » pour les alertes Premium). « redaction » (rappels de rédaction)
//                       n'est accepté qu'avec la clé de pilotage (en-tête Authorization: Bearer PILOTAGE_CLE),
//                       avec { "redaction": true | false } ; le site, lui, ne l'enlève jamais.
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
      const permis = ["articles", "alertes", "plus"];
      const pilote = !!process.env.PILOTAGE_CLE && req.headers.authorization === `Bearer ${process.env.PILOTAGE_CLE}`;
      const avant = await stockage.un(abo.endpoint);
      const avaitRedaction = !!(avant && (avant.sujets || []).includes("redaction"));
      let sujets;
      if (typeof abo.redaction === "boolean") {          // depuis la page de pilotage
        if (!pilote) return res.status(401).json({ erreur: "Clé de pilotage absente ou fausse." });
        sujets = ((avant && avant.sujets) || []).filter((s) => s !== "redaction");
        if (abo.redaction) sujets.push("redaction");
      } else {                                            // depuis le site
        sujets = Array.isArray(abo.sujets) ? abo.sujets.filter((s) => permis.includes(s)) : ["articles"];
        if (!sujets.length) sujets = ["articles"];
        if (avaitRedaction) sujets.push("redaction");
      }
      await stockage.ajouter({ endpoint: abo.endpoint, keys: { p256dh: abo.keys.p256dh, auth: abo.keys.auth }, sujets });
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
