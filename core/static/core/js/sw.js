// Service Worker for PWA - required by Chrome on Android for installability
// This handles fetch events so Chrome recognizes the app as installable

const CACHE_NAME = 'self-stats-v1';

// Install event - cache resources if needed
self.addEventListener('install', (event) => {
    // Skip waiting to activate immediately
    self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== CACHE_NAME)
                    .map((name) => caches.delete(name))
            );
        })
    );
    // Take control of all pages immediately
    return self.clients.claim();
});

// Fetch event - REQUIRED for Chrome installability
// This intercepts network requests. For a simple PWA, we just pass through to network.
self.addEventListener('fetch', (event) => {
    // For this app, we use network-first strategy (always fetch from network)
    // This ensures fresh data since it's a dynamic Django app
    event.respondWith(
        fetch(event.request).catch(() => {
            // If network fails, could fall back to cache here if needed
            // For now, just let it fail normally
            return new Response('Offline', { status: 503 });
        })
    );
});
