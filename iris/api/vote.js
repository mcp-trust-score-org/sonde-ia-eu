// Le vote des lecteurs sur les coups du mercato : « Vous auriez fait le même choix ? » (Oui / Non).
// POST /api/vote { id, choix: "oui"|"non", votant }   → enregistre (un vote par appareil et par coup ; on peut changer d'avis)
// GET  /api/vote?ids=a,b,c                            → { a: { oui: 62, non: 38 } | null, … } (en pour cent)
// Ni le nombre de votes ni les dates ne sont rendus (choix de la rédaction). En dessous de SEUIL votes, le résultat
// est null : un « 100 % de oui » tiré de deux votes n'apprend rien. L'appareil est reconnu par un nombre tiré au
// hasard dans le navigateur (rien de personnel), haché avant d'être gardé.
const crypto = require("crypto");
const { commande } = require("./_stockage");

const SEUIL = 30;
const ID = /^[a-z0-9-]{3,80}$/;

module.exports = async (req, res) => {
  try {
    if (req.method === "POST") {
      const c = typeof req.body === "string" ? JSON.parse(req.body || "{}") : req.body || {};
      if (!ID.test(c.id || "") || !["oui", "non"].includes(c.choix) || !/^[a-z0-9]{16,64}$/.test(c.votant || "")) {
        return res.status(400).json({ erreur: "Vote invalide." });
      }
      const qui = crypto.createHash("sha256").update(c.votant).digest("hex").slice(0, 32);
      const cle = `iris:vote:${c.id}`;
      const avant = await commande("HGET", `${cle}:votants`, qui);
      if (avant === c.choix) return res.status(200).json({ ok: true });
      if (avant) await commande("HINCRBY", cle, avant, -1);          // il change d'avis
      await commande("HINCRBY", cle, c.choix, 1);
      await commande("HSET", `${cle}:votants`, qui, c.choix);
      return res.status(200).json({ ok: true });
    }
    if (req.method === "GET") {
      const ids = String(req.query.ids || "").split(",").filter((x) => ID.test(x)).slice(0, 40);
      const sortie = {};
      for (const id of ids) {
        const plat = (await commande("HGETALL", `iris:vote:${id}`)) || [];
        const v = {};
        for (let i = 0; i < plat.length; i += 2) v[plat[i]] = Number(plat[i + 1]) || 0;
        const oui = Math.max(0, v.oui || 0), non = Math.max(0, v.non || 0), total = oui + non;
        sortie[id] = total >= SEUIL ? { oui: Math.round((100 * oui) / total), non: 100 - Math.round((100 * oui) / total) } : null;
      }
      res.setHeader("Cache-Control", "public, s-maxage=120");
      return res.status(200).json(sortie);
    }
    res.setHeader("Allow", "GET, POST");
    return res.status(405).json({ erreur: "Méthode non permise." });
  } catch (e) {
    return res.status(500).json({ erreur: e.message });
  }
};
