// GET /api/rappels?moment=matin|midi|soir : les rappels de rédaction, envoyés sur les appareils
// abonnés au sujet « redaction » (bouton dans la page de pilotage, protégé par PILOTAGE_CLE).
// Vercel l'appelle trois fois par jour (vercel.json, « crons ») avec le secret CRON_SECRET.
//   matin (7 h-8 h) : la rédaction du jour n'a pas tourné ?
//   midi (11 h-12 h) : des brouillons attendent une relecture, ou un article prévu n'a pas de brouillon ?
//   soir (18 h-19 h) : un article prévu aujourd'hui n'est toujours pas publié ? (dimanche : la météo de la semaine)
// Rien à signaler : aucune notification. Le rythme reprend celui de config/redaction.yaml (rubrique « rythme »).
const DEPOT = "https://raw.githubusercontent.com/mcp-trust-score-org/sonde-ia-eu/main";
const NOMS = { une: "À la une", tous_connectes: "Tous connectés", detour: "Le Détour", et_si: "Et si… ?" };

// Même rythme que config/redaction.yaml (0 = lundi … 6 = dimanche). À changer aux deux endroits.
function prevus(jourSemaine, quantieme) {
  const r = [];
  if (jourSemaine === 0) r.push("une");                       // bilan de la semaine
  if ([0, 2, 4, 5].includes(jourSemaine)) r.push("tous_connectes");
  if ([1, 4].includes(jourSemaine)) r.push("detour");
  if (jourSemaine === 0 && quantieme <= 7) r.push("et_si");
  return r;
}

function aujourdhuiParis(maintenant = new Date()) {
  const p = Object.fromEntries(new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Paris", year: "numeric", month: "2-digit", day: "2-digit", weekday: "short", hour: "2-digit", hour12: false })
    .formatToParts(maintenant).map((x) => [x.type, x.value]));
  const iso = `${p.year}-${p.month}-${p.day}`;
  const js = { Mon: 0, Tue: 1, Wed: 2, Thu: 3, Fri: 4, Sat: 5, Sun: 6 }[p.weekday];
  return { iso, jourSemaine: js, quantieme: Number(p.day), heure: Number(p.hour) };
}

// Ce qu'il faut dire, ou null. Séparé de l'envoi pour être testé.
function message(moment, jour, propositions, plus) {
  const props = propositions ? propositions.propositions || [] : null;
  const attendus = prevus(jour.jourSemaine, jour.quantieme);
  if (moment === "matin") {
    if (props === null) return "La rédaction du jour n'a pas tourné. Actions → Relevés quotidiens → Run workflow.";
    return null;
  }
  if (props === null) return "Toujours pas de brouillons aujourd'hui : la rédaction n'a pas tourné. Actions → Relevés quotidiens → Run workflow.";
  const enAttente = props.filter((p) => p.statut !== "publie" && p.statut !== "ecarte" && NOMS[p.rubrique]);
  const publies = new Set(props.filter((p) => p.statut === "publie").map((p) => p.rubrique));
  const sansBrouillon = attendus.filter((r) => r !== "et_si" && !props.some((p) => p.rubrique === r));
  const morceaux = [];
  if (moment === "midi") {
    if (enAttente.length) morceaux.push(`${enAttente.length} brouillon${enAttente.length > 1 ? "s" : ""} à relire : ${[...new Set(enAttente.map((p) => NOMS[p.rubrique]))].join(", ")}.`);
    if (sansBrouillon.length) morceaux.push(`Pas de brouillon pour ${sansBrouillon.map((r) => NOMS[r]).join(", ")}.`);
    // Les marchés publics attribués (BOAMP, TED) : des signatures officielles, candidates au mercato
    const attrib = ((propositions && propositions.marches_publics) || []).filter((a) => a.type === "attribution");
    if (attrib.length) {
      const a = attrib[0];
      morceaux.push(`Marché public attribué : ${String(a.acheteur || "un acheteur public").slice(0, 60)}${a.fournisseurs && a.fournisseurs.length ? ` (${a.fournisseurs.join(", ")})` : ""}${attrib.length > 1 ? ` (+${attrib.length - 1})` : ""}. Pour le mercato ?`);
    }
    // Les sujets qui font réfléchir (CHARTE, « Et si… ? ») : une piste à garder ou non, jamais publiée telle quelle.
    const pistes = (propositions && propositions.pistes_reflexion) || [];
    if (pistes.length) {
      const p = pistes[0];
      const autres = pistes.length > 1 ? ` (+${pistes.length - 1} autre${pistes.length > 2 ? "s" : ""})` : "";
      morceaux.push(p.sujet
        ? `L'actualité rejoint ton idée « ${p.sujet} » : ${p.media || "un article"}${autres}. Voir les brouillons.`
        : `Sujet qui fait réfléchir : « ${String(p.titre || "").slice(0, 90)} »${p.media ? ` (${p.media})` : ""}${autres}. À garder dans le panier ?`);
    }
  }
  if (moment === "soir") {
    const pasPublies = attendus.filter((r) => r !== "et_si" && !publies.has(r));
    if (pasPublies.length) morceaux.push(`Pas encore publié aujourd'hui : ${pasPublies.map((r) => NOMS[r]).join(", ")}.`);
    if (jour.jourSemaine === 6 && !((plus && plus.meteo_semaine) || []).some((e) => e.publie_le === jour.iso)) morceaux.push("La météo de la semaine n'est pas encore en ligne.");
    if (attendus.includes("et_si") && !((plus && plus.et_si) || []).some((a) => a.publie_le === jour.iso)) morceaux.push("Le « Et si… ? » du mois n'est pas encore en ligne.");
  }
  return morceaux.length ? morceaux.join(" ") : null;
}

async function lireJson(url) {
  const r = await fetch(url, { cache: "no-store" });
  if (r.status === 404) return null;
  if (!r.ok) throw new Error(`GitHub a répondu ${r.status}`);
  return r.json();
}

module.exports = async (req, res) => {
  const secret = process.env.CRON_SECRET;
  if (!secret || req.headers.authorization !== `Bearer ${secret}`) return res.status(401).json({ erreur: "Non autorisé." });
  const jour = aujourdhuiParis();
  const moment = ["matin", "midi", "soir"].includes((req.query || {}).moment) ? req.query.moment
    : jour.heure < 10 ? "matin" : jour.heure < 15 ? "midi" : "soir";
  try {
    const [props, plus] = await Promise.all([lireJson(`${DEPOT}/redaction/propositions/${jour.iso}.json`), lireJson(`${DEPOT}/iris/plus.json`)]);
    const texte = message(moment, jour, props, plus);
    if (!texte) return res.status(200).json({ moment, rappel: null });
    const site = (process.env.SITE_URL || `https://${req.headers.host}`).replace(/\/$/, "");
    const r = await fetch(`${site}/api/notifier`, {
      method: "POST", headers: { Authorization: `Bearer ${process.env.NOTIF_SECRET}`, "Content-Type": "application/json" },
      body: JSON.stringify({ sujet: "redaction", titre: "Iris · Rappel de rédaction", texte, url: "/pilotage.html" }),
    });
    return res.status(200).json({ moment, rappel: texte, envoi: r.status });
  } catch (e) {
    return res.status(502).json({ moment, erreur: String(e.message || e) });
  }
};
module.exports.message = message;
module.exports.prevus = prevus;
