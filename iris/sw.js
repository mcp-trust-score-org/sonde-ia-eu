// Iris : reçoit les notifications (nouvel article, alerte panne) et ouvre la bonne page au clic.
// Un article peut proposer deux durées (« deux_modes ») : sur Android et ordinateur, deux boutons « 2 min » et
// « En entier » ; sur iPhone (pas de boutons), toucher ouvre l'essentiel en 2 min, ou l'article entier si le
// lecteur l'a réglé ainsi dans la cloche (main.js, ?lecture=notif).
self.addEventListener("push", (event) => {
  let d = {};
  try { d = event.data ? event.data.json() : {}; } catch (e) { d = { titre: event.data && event.data.text() }; }
  const options = {
    body: d.texte || "",
    icon: "/assets/icone-app-192.png",
    badge: "/assets/icone-app-192.png",
    data: { url: d.url || "/", deux_modes: Boolean(d.deux_modes) },
    tag: d.tag || "iris-article",
    renotify: true,
  };
  if (d.deux_modes) options.actions = [{ action: "court", title: "2 min" }, { action: "long", title: "En entier" }];
  event.waitUntil(self.registration.showNotification(d.titre || "Iris · nouvel article", options));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const donnees = event.notification.data || {};
  const cible = new URL(donnees.url || "/", self.location.origin);
  if (donnees.deux_modes) cible.searchParams.set("lecture", event.action === "long" ? "10" : event.action === "court" ? "2" : "notif");
  const url = cible.href;
  event.waitUntil((async () => {
    const fenetres = await clients.matchAll({ type: "window", includeUncontrolled: true });
    for (const f of fenetres) {
      if (new URL(f.url).origin === self.location.origin) { await f.focus(); return f.navigate(url); }
    }
    return clients.openWindow(url);
  })());
});
