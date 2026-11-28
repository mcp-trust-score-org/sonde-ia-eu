// La file des notifications à valider (pilotage → Notifications). Rien de ce qui passe ici ne part vers les lecteurs
// sans le feu vert de la rédaction.
//
// Depuis GitHub (secret NOTIF_SECRET) :
//   POST { action: "proposer", item: { cle, type, titre, texte, url, sujet, fournisseurs, details } }
//        → la notification attend dans « À valider », et la rédaction est prévenue sur son téléphone (sujet « redaction »).
//   POST { action: "tic" } → envoie ce qui était programmé et dont l'heure est passée (appelé toutes les 15 min).
// Depuis le pilotage (clé PILOTAGE_CLE) :
//   GET → { a_valider, a_venir, envoyees } (et fait partir au passage ce qui est programmé et dû)
//   POST { action: "envoyer" | "programmer" (avec quand) | "annuler" | "tester", id }
//   « tester » : envoie la notification aux seuls appareils de la rédaction, avec « [Test] » devant.
const crypto = require("crypto");
const stockage = require("./_stockage");
const { envoyer } = require("./_envoi");

const FILE = "iris:file";
const TYPES = { mercato: "Mercato", point: "Point du vendredi", autre: "Notification" };

const lire = async () => {
  const plat = (await stockage.commande("HGETALL", FILE)) || [];
  const items = [];
  for (let i = 1; i < plat.length; i += 2) { try { items.push(JSON.parse(plat[i])); } catch (e) { /* abîmé */ } }
  return items;
};
const garder = (it) => stockage.commande("HSET", FILE, it.id, JSON.stringify(it));

async function partir(it) {
  const r = await envoyer({ titre: it.titre, texte: it.texte, url: it.url, sujet: it.sujet, fournisseurs: it.fournisseurs },
    { type: TYPES[it.type] || "Notification" });
  Object.assign(it, { etat: "envoye", envoye_le: new Date().toISOString(), recus: r.envoyes });
  await garder(it);
  return r;
}

// Ce qui est programmé et dont l'heure est passée part maintenant. Les envois et annulations de plus de 30 jours s'effacent.
async function tic() {
  const maintenant = Date.now();
  let partis = 0;
  for (const it of await lire()) {
    if (it.etat === "programme" && Date.parse(it.quand) <= maintenant) { await partir(it); partis++; }
    else if (["envoye", "annule"].includes(it.etat) && maintenant - Date.parse(it.envoye_le || it.annule_le || it.cree_le) > 30 * 864e5) {
      await stockage.commande("HDEL", FILE, it.id);
    }
  }
  return partis;
}

module.exports = async (req, res) => {
  const auth = req.headers.authorization || "";
  const github = process.env.NOTIF_SECRET && auth === `Bearer ${process.env.NOTIF_SECRET}`;
  const redaction = process.env.PILOTAGE_CLE && auth === `Bearer ${process.env.PILOTAGE_CLE}`;
  if (!github && !redaction) return res.status(401).json({ erreur: "Non autorisé." });
  try {
    if (req.method === "GET") {
      if (!redaction) return res.status(401).json({ erreur: "Clé de pilotage attendue." });
      await tic();
      const items = (await lire()).sort((a, b) => String(b.cree_le).localeCompare(String(a.cree_le)));
      const plat = (await stockage.commande("LRANGE", "iris:envois", 0, 29)) || [];
      const envoyees = plat.map((x) => { try { return JSON.parse(x); } catch (e) { return null; } }).filter(Boolean);
      res.setHeader("Cache-Control", "no-store");
      return res.status(200).json({
        a_valider: items.filter((i) => i.etat === "a_valider"),
        a_venir: items.filter((i) => i.etat === "programme").sort((a, b) => a.quand.localeCompare(b.quand)),
        envoyees,
      });
    }
    if (req.method !== "POST") return res.status(405).json({ erreur: "Méthode non permise." });
    const c = typeof req.body === "string" ? JSON.parse(req.body || "{}") : req.body || {};

    if (c.action === "tic") return res.status(200).json({ partis: await tic() });

    if (c.action === "proposer") {
      if (!github) return res.status(401).json({ erreur: "Réservé à GitHub." });
      const x = c.item || {};
      const id = String(x.cle || crypto.randomUUID()).replace(/[^a-z0-9-]/gi, "-").slice(0, 100);
      if (await stockage.commande("HEXISTS", FILE, id)) return res.status(200).json({ ok: true, deja: true });
      const it = { id, type: TYPES[x.type] ? x.type : "autre", titre: String(x.titre || "").slice(0, 120), texte: String(x.texte || "").slice(0, 240),
        url: x.url || "/", sujet: x.sujet || "articles", fournisseurs: Array.isArray(x.fournisseurs) ? x.fournisseurs : [],
        details: x.details || null, etat: "a_valider", cree_le: new Date().toISOString() };
      await garder(it);
      // La rédaction est prévenue sur son téléphone (rappels de pilotage activés).
      const court = it.titre.replace(/^Le mercato de l'IA · /, "");
      await envoyer({ titre: `À valider · ${TYPES[it.type]}`, texte: `${court}. Envoyer, programmer ou annuler dans le pilotage.`,
        url: "/pilotage.html#notifications", sujet: "redaction" }, { journal: false }).catch(() => null);
      return res.status(200).json({ ok: true, id });
    }

    if (!redaction) return res.status(401).json({ erreur: "Clé de pilotage attendue." });
    const brut = await stockage.commande("HGET", FILE, String(c.id || ""));
    if (!brut) return res.status(404).json({ erreur: "Notification introuvable." });
    const it = JSON.parse(brut);
    if (it.etat === "envoye") return res.status(409).json({ erreur: "Déjà envoyée." });

    if (c.action === "envoyer") return res.status(200).json(await partir(it));
    if (c.action === "tester") {
      const r = await envoyer({ titre: `[Test] ${it.titre}`, texte: it.texte, url: it.url, sujet: "redaction" }, { journal: false });
      return res.status(200).json(r);
    }
    if (c.action === "programmer") {
      const quand = Date.parse(c.quand);
      if (!quand || quand < Date.now() - 60e3) return res.status(400).json({ erreur: "Choisissez une date à venir." });
      Object.assign(it, { etat: "programme", quand: new Date(quand).toISOString() });
      await garder(it);
      return res.status(200).json({ ok: true, quand: it.quand });
    }
    if (c.action === "annuler") {
      Object.assign(it, { etat: "annule", annule_le: new Date().toISOString() });
      await garder(it);
      return res.status(200).json({ ok: true });
    }
    if (c.action === "remettre") {                // une programmation qu'on reprend : retour dans « À valider »
      Object.assign(it, { etat: "a_valider", quand: null });
      await garder(it);
      return res.status(200).json({ ok: true });
    }
    return res.status(400).json({ erreur: "Action inconnue." });
  } catch (e) {
    return res.status(e.code || 500).json({ erreur: e.message });
  }
};
