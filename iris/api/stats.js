// GET /api/stats : l'audience, pour la page de pilotage. Protégée par la clé PILOTAGE_CLE (variable Vercel),
// envoyée dans l'en-tête « Authorization: Bearer … ».
// Réponse : les articles les plus lus (depuis le début, sur 7 jours, aujourd'hui) et les abonnés aux notifications.
const { commande } = require("./_stockage");

const enObjet = (plat) => { const o = {}; for (let i = 0; i < (plat || []).length; i += 2) o[plat[i]] = Number(plat[i + 1]) || plat[i + 1]; return o; };

module.exports = async (req, res) => {
  const cle = process.env.PILOTAGE_CLE;
  if (!cle || req.headers.authorization !== `Bearer ${cle}`) return res.status(401).json({ erreur: "Clé de pilotage absente ou fausse." });
  try {
    const total = enObjet(await commande("HGETALL", "iris:vues"));
    const titres = enObjet(await commande("HGETALL", "iris:titres"));
    const jours = [];
    for (let i = 0; i < 7; i++) jours.push(new Date(Date.now() - i * 864e5).toISOString().slice(0, 10));
    const parJour = {};
    for (const j of jours) parJour[j] = enObjet(await commande("HGETALL", `iris:vues:${j}`));
    const semaine = {};
    Object.values(parJour).forEach((o) => Object.entries(o).forEach(([id, n]) => { semaine[id] = (semaine[id] || 0) + n; }));
    const articles = Object.keys(total).map((id) => ({ id, titre: titres[id] || id, total: total[id], semaine: semaine[id] || 0, aujourdhui: parJour[jours[0]][id] || 0 }))
      .sort((a, b) => b.semaine - a.semaine || b.total - a.total);
    const abos = enObjet(await commande("HGETALL", "iris:abonnes"));
    const sujets = { articles: 0, plus: 0, alertes: 0 };
    Object.values(abos).forEach((v) => { try { (JSON.parse(v).sujets || ["articles"]).forEach((s) => { sujets[s] = (sujets[s] || 0) + 1; }); } catch (e) { /* ignoré */ } });
    return res.status(200).json({
      genere_le: new Date().toISOString(), articles: articles.slice(0, 30),
      lectures_par_jour: jours.map((j) => ({ date: j, lectures: Object.values(parJour[j]).reduce((a, b) => a + b, 0) })).reverse(),
      abonnes: { appareils: Object.keys(abos).length, sujets },
    });
  } catch (e) {
    return res.status(503).json({ erreur: "Compteurs indisponibles : " + e.message });
  }
};
