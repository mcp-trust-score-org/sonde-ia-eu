// Liste des appareils abonnés aux notifications, gardée dans une base Redis (Upstash),
// branchée depuis Vercel : Storage → Upstash for Redis. Vercel fournit l'adresse et la clé.
// Les fichiers qui commencent par « _ » ne sont pas des adresses du site.
const URL_BASE = process.env.KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL;
const CLE = process.env.KV_REST_API_TOKEN || process.env.UPSTASH_REDIS_REST_TOKEN;
const LISTE = "iris:abonnes";

async function commande(...args) {
  if (!URL_BASE || !CLE) throw new Error("Base des abonnés non branchée (Vercel → Storage → Upstash for Redis).");
  const r = await fetch(URL_BASE, {
    method: "POST",
    headers: { Authorization: `Bearer ${CLE}`, "Content-Type": "application/json" },
    body: JSON.stringify(args),
  });
  const j = await r.json();
  if (j.error) throw new Error(j.error);
  return j.result;
}

module.exports = {
  commande,
  ajouter: (abo) => commande("HSET", LISTE, abo.endpoint, JSON.stringify(abo)),
  retirer: (endpoint) => commande("HDEL", LISTE, endpoint),
  async un(endpoint) {
    const v = await commande("HGET", LISTE, endpoint);
    try { return v ? JSON.parse(v) : null; } catch (e) { return null; }
  },
  async tous() {
    const plat = (await commande("HGETALL", LISTE)) || [];
    const abos = [];
    for (let i = 1; i < plat.length; i += 2) {
      try { abos.push(JSON.parse(plat[i])); } catch (e) { /* entrée abîmée : ignorée */ }
    }
    return abos;
  },
};
