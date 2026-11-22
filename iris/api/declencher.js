// GET /api/declencher : le réveil de secours de la rédaction.
// Vercel l'appelle chaque matin (vercel.json, « crons »), avec le secret CRON_SECRET.
// Si GitHub n'a pas lancé « Relevés quotidiens » aujourd'hui (il saute parfois ses lancements programmés),
// on appuie à sa place sur « Run workflow ». Sinon, on ne fait rien : jamais deux rédactions le même jour.
// Variables Vercel : CRON_SECRET (une phrase secrète) et GH_DISPATCH_TOKEN (clé GitHub, droit « Actions : lecture et écriture »).
const DEPOT = "mcp-trust-score-org/sonde-ia-eu";
const WORKFLOW = "quotidien.yml";

module.exports = async (req, res) => {
  const secret = process.env.CRON_SECRET;
  if (!secret || req.headers.authorization !== `Bearer ${secret}`) return res.status(401).json({ erreur: "Non autorisé." });
  const jeton = process.env.GH_DISPATCH_TOKEN;
  if (!jeton) return res.status(503).json({ erreur: "Clé GitHub absente (GH_DISPATCH_TOKEN)." });
  const entetes = { Authorization: `Bearer ${jeton}`, Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "iris-reveil" };
  const api = `https://api.github.com/repos/${DEPOT}/actions/workflows/${WORKFLOW}`;
  const aujourdhui = new Date().toISOString().slice(0, 10);
  try {
    // Une exécution d'aujourd'hui en cours, en attente ou réussie ? Alors GitHub s'en est chargé.
    const r = await fetch(`${api}/runs?created=>=${aujourdhui}&per_page=20`, { headers: entetes });
    if (!r.ok) return res.status(502).json({ erreur: `GitHub a répondu ${r.status} en lisant les exécutions.` });
    const { workflow_runs = [] } = await r.json();
    const deja = workflow_runs.find((x) => x.status !== "completed" || x.conclusion === "success");
    if (deja) return res.status(200).json({ action: "rien", raison: `déjà lancé aujourd'hui (${deja.event}, ${deja.status})` });
    const d = await fetch(`${api}/dispatches`, { method: "POST", headers: entetes, body: JSON.stringify({ ref: "main" }) });
    if (d.status !== 204) return res.status(502).json({ erreur: `GitHub a refusé le lancement (${d.status}).` });
    return res.status(200).json({ action: "lancé", raison: "aucune exécution réussie ou en cours aujourd'hui" });
  } catch (e) {
    return res.status(502).json({ erreur: String(e.message || e) });
  }
};
