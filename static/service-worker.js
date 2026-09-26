// Caches the app shell so the UI opens offline; API calls always go to the network.
const CACHE = 'bash-bookmarks-v2';
const SHELL = [
  '/',
  '/app.css',
  '/app.js',
  '/manifest.json',
  '/icon.svg',
  '/icon-192.png',
  '/favicon.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET' || url.origin !== location.origin || url.pathname.startsWith('/api/')) {
    return;
  }

  // Network first, fall back to the cached shell (/share is served by the same page)
  const key = event.request.mode === 'navigate' ? '/' : event.request;
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (response.ok) {
          const copy = response.clone();
          caches.open(CACHE).then((cache) => cache.put(key, copy));
        }
        return response;
      })
      .catch(() => caches.match(key, { ignoreSearch: true }))
  );
});
