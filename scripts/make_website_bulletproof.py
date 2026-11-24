import os
import re
import glob
import json
from pathlib import Path

ROOT = Path("D:/kethravax/website")
SCRIPTS = Path("D:/kethravax/scripts")

INLINE_LOGO = """<svg class="brand-logo" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="30" height="30" aria-label="KETHRAVAX Logo" style="vertical-align:middle; flex-shrink:0;">
  <defs>
    <linearGradient id="kethraGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00F0FF" />
      <stop offset="50%" stop-color="#38BDF8" />
      <stop offset="100%" stop-color="#8B5CF6" />
    </linearGradient>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#070B14" />
      <stop offset="100%" stop-color="#0F172A" />
    </linearGradient>
  </defs>
  <rect width="100" height="100" rx="22" fill="url(#bgGrad)" stroke="#1E293B" stroke-width="2" />
  <circle cx="50" cy="50" r="38" stroke="url(#kethraGrad)" stroke-width="3" fill="none" opacity="0.35" stroke-dasharray="14 6" />
  <line x1="50" y1="16" x2="50" y2="24" stroke="#00F0FF" stroke-width="3" stroke-linecap="round" />
  <line x1="50" y1="76" x2="50" y2="84" stroke="#8B5CF6" stroke-width="3" stroke-linecap="round" />
  <line x1="16" y1="50" x2="24" y2="50" stroke="#00F0FF" stroke-width="3" stroke-linecap="round" />
  <line x1="76" y1="50" x2="84" y2="50" stroke="#8B5CF6" stroke-width="3" stroke-linecap="round" />
  <path d="M 34 28 L 34 72" stroke="url(#kethraGrad)" stroke-width="6" stroke-linecap="round" />
  <path d="M 36 50 L 64 28" stroke="url(#kethraGrad)" stroke-width="5.5" stroke-linecap="round" />
  <path d="M 44 43 L 66 72" stroke="#00F0FF" stroke-width="5.5" stroke-linecap="round" />
  <circle cx="34" cy="28" r="4" fill="#00F0FF" />
  <circle cx="34" cy="72" r="4" fill="#8B5CF6" />
  <circle cx="64" cy="28" r="4.5" fill="#00F0FF" />
  <circle cx="66" cy="72" r="4.5" fill="#8B5CF6" />
  <circle cx="44" cy="43" r="3.5" fill="#38BDF8" />
</svg>"""

GOOGLE_TAG = '<meta name="google-site-verification" content="SGokPX2GrobpJD7DfOw4PNA5FjAGcAkZ-196p22EQJU" />'

CLARITY_TAG = """  <!-- Microsoft Clarity -->
  <script type="text/javascript">
    (function(c,l,a,r,i,t,y){
        c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
        t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
        y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
    })(window, document, "clarity", "script", "zinlob90sp");
  </script>"""

def process_html_files():
    css_content = (ROOT / "styles.css").read_text(encoding="utf-8")
    style_block = f"<style id=\"kethravax-core-css\">\n{css_content}\n</style>"

    html_files = list(ROOT.glob("*.html")) + list((ROOT / "explorer").glob("*.html"))

    for p in html_files:
        if "google" in p.name:
            continue
        
        content = p.read_text(encoding="utf-8")

        # 1. Replace logo image with inline SVG
        content = re.sub(
            r'<img\s+src="[^"]*favicon\.svg"[^>]*>',
            INLINE_LOGO,
            content
        )

        # 2. Ensure Google Verification meta tag in <head>
        if "SGokPX2GrobpJD7DfOw4PNA5FjAGcAkZ-196p22EQJU" not in content:
            content = content.replace("<head>", f"<head>\n  {GOOGLE_TAG}")

        # 3. Ensure Microsoft Clarity in <head>
        if "zinlob90sp" not in content:
            content = content.replace("</head>", f"{CLARITY_TAG}\n</head>")

        # 4. Inject full CSS into <style>
        if "<style" in content:
            # Replace existing <style>...</style> block
            content = re.sub(r'<style(?:\s+id="[^"]*")?>.*?</style>', style_block, content, flags=re.DOTALL)
        else:
            # Insert style block right before </head>
            content = content.replace("</head>", f"  {style_block}\n</head>")

        # 5. Cache buster for external assets
        content = re.sub(r'href="styles\.css(?:\?[^"]*)?"', 'href="styles.css?v=20261124-v5"', content)
        content = re.sub(r'src="img/studio-preview\.gif(?:\?[^"]*)?"', 'src="img/studio-preview.gif?v=20261124-v5"', content)

        p.write_text(content, encoding="utf-8")
        print(f"Processed & inlined full CSS in {p.relative_to(ROOT)} ({len(content):,} chars)")

def build_worker():
    assets = {}

    def get_content_type(filename):
        if filename.endswith(".html"): return "text/html; charset=utf-8"
        if filename.endswith(".css"): return "text/css; charset=utf-8"
        if filename.endswith(".js"): return "application/javascript; charset=utf-8"
        if filename.endswith(".svg"): return "image/svg+xml"
        if filename.endswith(".xml"): return "application/xml; charset=utf-8"
        if filename.endswith(".txt"): return "text/plain; charset=utf-8"
        if filename.endswith(".json"): return "application/json; charset=utf-8"
        return "text/plain; charset=utf-8"

    # Root text files
    for p in ROOT.glob("*"):
        if p.is_file() and not p.name.startswith("_") and not p.name.endswith(".py"):
            route = "/" + p.name
            content = p.read_text(encoding="utf-8")
            assets[route] = {
                "body": content,
                "type": get_content_type(p.name)
            }
            if p.name == "index.html":
                assets["/"] = assets[route]
            elif p.suffix == ".html":
                assets["/" + p.stem] = assets[route]

    # Explorer directory
    exp_dir = ROOT / "explorer"
    if exp_dir.exists():
        for p in exp_dir.glob("*"):
            if p.is_file() and not p.name.endswith(".py"):
                route = "/explorer/" + p.name
                content = p.read_text(encoding="utf-8")
                assets[route] = {
                    "body": content,
                    "type": get_content_type(p.name)
                }
                if p.name == "index.html":
                    assets["/explorer"] = assets[route]
                    assets["/explorer/"] = assets[route]

    print(f"Packed {len(assets)} in-memory routes for edge delivery.")

    worker_code = f"""// KETHRAVAX High-Performance Self-Contained Edge Worker
// Built for Cloudflare Pages & Instant Edge CDN Delivery
// Copyright (c) 2026 Arin Goel. All rights reserved.

const ASSETS = {json.dumps(assets)};

export default {{
  async fetch(request, env, ctx) {{
    const url = new URL(request.url);
    let pathname = url.pathname;

    // Normalization
    if (pathname.length > 1 && pathname.endsWith('/')) {{
      pathname = pathname.slice(0, -1);
    }}

    // Check in-memory assets first (instant 1ms response, 0 CSP)
    let asset = ASSETS[pathname];
    if (!asset && !pathname.includes('.')) {{
      asset = ASSETS[pathname + '.html'];
    }}

    if (asset) {{
      const isHtml = asset.type.startsWith("text/html");
      const cacheControl = isHtml 
        ? "public, max-age=0, must-revalidate" 
        : "public, max-age=86400, stale-while-revalidate=604800";

      return new Response(asset.body, {{
        status: 200,
        headers: {{
          "Content-Type": asset.type,
          "Cache-Control": cacheControl,
          "X-Content-Type-Options": "nosniff",
          "Access-Control-Allow-Origin": "*",
          "Referrer-Policy": "strict-origin-when-cross-origin"
        }}
      }});
    }}

    // Binary assets (e.g. /img/*.png, /img/*.gif) -> fetch from GitHub raw and cache
    if (pathname.startsWith('/img/')) {{
      const upstream = "https://raw.githubusercontent.com/A35-777/kethravax/main/website" + pathname + "?v=20261124-v5";
      const cache = caches.default;
      const cacheKey = new Request(upstream, request);
      let response = await cache.match(cacheKey);

      if (!response) {{
        const originRes = await fetch(upstream, {{
          headers: {{ "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Kethravax-Deploy/5.0" }}
        }});

        if (originRes.ok) {{
          let contentType = "application/octet-stream";
          if (pathname.endsWith(".png")) contentType = "image/png";
          else if (pathname.endsWith(".gif")) contentType = "image/gif";
          else if (pathname.endsWith(".svg")) contentType = "image/svg+xml";

          const headers = new Headers();
          headers.set("Content-Type", contentType);
          headers.set("Cache-Control", "public, max-age=86400, s-maxage=604800");
          headers.set("X-Content-Type-Options", "nosniff");
          headers.set("Access-Control-Allow-Origin", "*");

          response = new Response(originRes.body, {{
            status: 200,
            headers
          }});
          ctx.waitUntil(cache.put(cacheKey, response.clone()));
        }} else {{
          response = new Response("404 Image Not Found — Kethravax: " + pathname, {{
            status: 404,
            headers: {{ "Content-Type": "text/plain; charset=utf-8" }}
          }});
        }}
      }}
      return response;
    }}

    return new Response("404 Not Found — KETHRAVAX", {{
      status: 404,
      headers: {{ "Content-Type": "text/plain; charset=utf-8" }}
    }});
  }}
}};
"""

    worker_file = ROOT / "_worker.js"
    worker_file.write_text(worker_code, encoding="utf-8")
    print(f"Generated standalone _worker.js ({len(worker_code):,} chars, {len(worker_code)/1024:.1f} KB)")

if __name__ == "__main__":
    process_html_files()
    build_worker()
