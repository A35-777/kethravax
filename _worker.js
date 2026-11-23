export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    let pathname = url.pathname;

    if (pathname.endsWith('/') && pathname !== '/') {
      pathname = pathname.slice(0, -1);
    }

    if (pathname === '/' || pathname === '') {
      pathname = '/index.html';
    } else if (pathname === '/explorer' || pathname === '/explorer/') {
      pathname = '/explorer/index.html';
    } else if (!pathname.includes('.')) {
      pathname = pathname + '.html';
    }

    // Version tag to bust edge cache on new release
    const upstream = "https://raw.githubusercontent.com/A35-777/kethravax/main/website" + pathname + "?v=20261123-v7";
    const cache = caches.default;
    const cacheKey = new Request(upstream, request);
    let response = await cache.match(cacheKey);

    if (!response) {
      const originRes = await fetch(upstream, {
        headers: { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Kethravax-Deploy/3.0" }
      });
      if (originRes.ok) {
        let contentType = "text/plain";
        if (pathname.endsWith(".html")) contentType = "text/html; charset=utf-8";
        else if (pathname.endsWith(".css")) contentType = "text/css; charset=utf-8";
        else if (pathname.endsWith(".js")) contentType = "application/javascript; charset=utf-8";
        else if (pathname.endsWith(".png")) contentType = "image/png";
        else if (pathname.endsWith(".gif")) contentType = "image/gif";
        else if (pathname.endsWith(".svg")) contentType = "image/svg+xml";
        else if (pathname.endsWith(".xml")) contentType = "application/xml; charset=utf-8";
        else if (pathname.endsWith(".txt")) contentType = "text/plain; charset=utf-8";
        else if (pathname.endsWith(".json")) contentType = "application/json; charset=utf-8";

        const headers = new Headers(originRes.headers);
        headers.set("Content-Type", contentType);
        headers.set("Cache-Control", "public, max-age=120, s-maxage=600");
        headers.set("X-Content-Type-Options", "nosniff");
        headers.set("X-Frame-Options", "SAMEORIGIN");

        response = new Response(originRes.body, {
          status: 200,
          headers
        });
        ctx.waitUntil(cache.put(cacheKey, response.clone()));
      } else {
        response = new Response("404 Not Found — Kethravax: " + pathname + " (upstream " + originRes.status + ")", {
          status: 404,
          headers: { "Content-Type": "text/plain; charset=utf-8" }
        });
      }
    }

    return response;
  }
};
