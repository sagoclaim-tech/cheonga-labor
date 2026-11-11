/* 청아노무법인 앱 서비스워커: 화면과 기준 데이터는 항상 최신을 먼저 받고, 연결이 없으면 저장본을 씁니다. */
const CACHE = "cheonga-v45";
const SHELL = ["./", "index.html", "data.json", "interp.json", "guides.json", "manifest.webmanifest", "icons/icon-192.png", "icons/icon-512.png", "icons/apple-touch-icon.png", "icons/favicon-32.png", "icons/badge-96.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
async function networkFirst(req, key) {
  const c = await caches.open(CACHE);
  try { const res = await fetch(req, { cache: "no-store" }); if (res && res.ok) c.put(key || req, res.clone()); return res; }
  catch (err) { const hit = await c.match(key || req, { ignoreSearch: true }); if (hit) return hit; throw err; }
}
async function staleWhileRevalidate(req) {
  const c = await caches.open(CACHE); const hit = await c.match(req);
  const net = fetch(req).then(res => { if (res && (res.ok || res.type === "opaque")) c.put(req, res.clone()); return res; }).catch(() => hit);
  return hit || net;
}
self.addEventListener("fetch", e => {
  const req = e.request; if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin === location.origin && (url.pathname.endsWith("/data.json") || url.pathname.endsWith("/interp.json") || url.pathname.endsWith("/guides.json"))) { e.respondWith(networkFirst(req, new Request(url.origin + url.pathname))); return; }
  if (url.hostname === "sagoclaim-tech.github.io" && url.pathname.startsWith("/labor-briefing/daily/")) { e.respondWith(networkFirst(req, new Request(url.origin + url.pathname))); return; }
  /* 앱 화면만 index.html로 저장. 검색용 페이지(interp/, figures/, grants/, changes.html)는 자기 주소로 저장 */
  if (req.mode === "navigate") { const app = url.origin === location.origin && /\/(index\.html)?$/.test(url.pathname); e.respondWith(app ? networkFirst(req, "index.html") : networkFirst(req)); return; }
  e.respondWith(staleWhileRevalidate(req));
});

/* 새 소식 알림(웹 푸시): 서버가 보낸 내용을 알림으로 띄운다. 안드로이드는 읽지 않은 알림이 있는 동안 앱 아이콘에 배지가 붙는다. */
self.addEventListener("push", e => {
  let d = {}; try { d = e.data ? e.data.json() : {}; } catch (err) { d = {}; }
  const opt = { body: String(d.body || ""), icon: "icons/icon-192.png", badge: "icons/badge-96.png", tag: String(d.tag || "cn-" + Date.now()), renotify: true, data: { url: String(d.url || "./"), tab: String(d.tab || "") } };
  e.waitUntil(self.registration.showNotification(String(d.title || "청아 노무수첩 새 소식"), opt)
    .then(() => self.registration.getNotifications())
    .then(ns => { if (self.navigator && navigator.setAppBadge) return navigator.setAppBadge(ns.length).catch(() => {}); }));
});
self.addEventListener("notificationclick", e => {
  const d = e.notification.data || {}; e.notification.close();
  let url; try { url = new URL(d.url || "./", self.registration.scope); if (url.origin !== location.origin) throw 0; url = url.href; } catch (err) { url = self.registration.scope; }
  e.waitUntil(self.clients.matchAll({ type: "window", includeUncontrolled: true }).then(cs => {
    for (const c of cs) { if (c.url.indexOf(self.registration.scope) === 0 && "focus" in c) { c.postMessage({ type: "cn-open", tab: d.tab || "", url }); return c.focus(); } }
    return self.clients.openWindow(url);
  }));
});
