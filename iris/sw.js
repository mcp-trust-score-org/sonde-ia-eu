// Iris : reçoit les notifications (nouvel article, alerte panne) et ouvre la bonne page au clic.
self.addEventListener("push", (event) => {
  let d = {};
  try { d = event.data ? event.data.json() : {}; } catch (e) { d = { titre: event.data && event.data.text() }; }
  event.waitUntil(self.registration.showNotification(d.titre || "Iris · nouvel article", {
    body: d.texte || "",
    icon: "/assets/icone-app-192.png",
    badge: "/assets/icone-app-192.png",
    data: { url: d.url || "/" },
    tag: d.tag || "iris-article",
    renotify: true,
  }));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = new URL(event.notification.data.url || "/", self.location.origin).href;
  event.waitUntil((async () => {
    const fenetres = await clients.matchAll({ type: "window", includeUncontrolled: true });
    for (const f of fenetres) {
      if (new URL(f.url).origin === self.location.origin) { await f.focus(); return f.navigate(url); }
    }
    return clients.openWindow(url);
  })());
});
