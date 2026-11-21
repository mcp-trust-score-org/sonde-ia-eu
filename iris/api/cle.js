// GET /api/cle : la clé publique dont le navigateur a besoin pour s'abonner.
module.exports = (req, res) => {
  const cle = process.env.VAPID_PUBLIC_KEY;
  if (!cle) return res.status(503).json({ erreur: "Notifications pas encore configurées (VAPID_PUBLIC_KEY)." });
  res.setHeader("Cache-Control", "no-store");
  res.status(200).json({ cle });
};
