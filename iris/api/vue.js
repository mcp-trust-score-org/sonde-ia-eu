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
  // Deux compteurs de plus, toujours sans rien savoir du lecteur : un article lu « en entier » après l'essentiel
  // en 2 min, et les stories « L'essentiel du jour » ouvertes et vues jusqu'au bout.
  const evenement = String(corps.evenement || "");
  if (evenement) {
    try {
      if (evenement === "entier") await commande("HINCRBY", "iris:entier", id, 1);
      else if (evenement === "stories_debut" || evenement === "stories_fin") await commande("HINCRBY", "iris:stories", evenement.slice(8), 1);
      else return res.status(400).json({ erreur: "Événement inconnu." });
      return res.status(204).end();
    } catch (e) {
      return res.status(503).json({ erreur: "Compteur indisponible." });
    }
  }
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
