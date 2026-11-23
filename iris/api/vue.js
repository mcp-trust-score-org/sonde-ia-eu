// POST /api/vue : compte une lecture d'article, pour le tableau de pilotage (les articles qui marchent).
// Corps : { "id": "article-…" | "plus-etsi-…" | "plus-meteo-…", "titre": "…" }
// Aucune donnée sur le lecteur : ni adresse, ni cookie, ni appareil. Seulement un compteur par article et par jour.
const { commande } = require("./_stockage");

module.exports = async (req, res) => {
  if (req.method !== "POST") return res.status(405).end();
  let corps = req.body || {};
  if (typeof corps === "string") { try { corps = JSON.parse(corps); } catch (e) { corps = {}; } }
  const id = String(corps.id || "");
  if (!/^(article|plus)-[\w-]{1,80}$/.test(id)) return res.status(400).json({ erreur: "Identifiant d'article invalide." });
  const jour = new Date().toISOString().slice(0, 10);
  try {
    await commande("HINCRBY", "iris:vues", id, 1);
    await commande("HINCRBY", `iris:vues:${jour}`, id, 1);
    await commande("EXPIRE", `iris:vues:${jour}`, 60 * 60 * 24 * 100);
    if (corps.titre) await commande("HSET", "iris:titres", id, String(corps.titre).replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim().slice(0, 160));
    return res.status(204).end();
  } catch (e) {
    return res.status(503).json({ erreur: "Compteur indisponible." });
  }
};
