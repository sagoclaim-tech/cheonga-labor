/* 청아노무법인 앱 서비스워커: 화면과 기준 데이터는 항상 최신을 먼저 받고, 연결이 없으면 저장본을 씁니다. */
const CACHE = "cheonga-v26";
const SHELL = ["./", "index.html", "data.json", "interp.json", "manifest.webmanifest", "icons/icon-192.png", "icons/icon-512.png", "icons/apple-touch-icon.png", "icons/favicon-32.png"];
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
  if (url.origin === location.origin && (url.pathname.endsWith("/data.json") || url.pathname.endsWith("/interp.json"))) { e.respondWith(networkFirst(req, new Request(url.origin + url.pathname))); return; }
  if (req.mode === "navigate") { e.respondWith(networkFirst(req, "index.html")); return; }
  e.respondWith(staleWhileRevalidate(req));
});
