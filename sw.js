// Minimal service worker — PWA o'rnatish uchun (keshlamaydi, ma'lumot doim yangi)
self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => self.clients.claim());
self.addEventListener('fetch', () => {});
