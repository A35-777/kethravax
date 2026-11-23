import os
import glob
import json
from pathlib import Path

def get_content_type(filename):
    if filename.endswith(".html"): return "text/html; charset=utf-8"
    if filename.endswith(".css"): return "text/css; charset=utf-8"
    if filename.endswith(".js"): return "application/javascript; charset=utf-8"
    if filename.endswith(".svg"): return "image/svg+xml"
    if filename.endswith(".xml"): return "application/xml; charset=utf-8"
    if filename.endswith(".txt"): return "text/plain; charset=utf-8"
    if filename.endswith(".json"): return "application/json; charset=utf-8"
    return "text/plain; charset=utf-8"

def main():
    root = Path("D:/kethravax/website")
    assets = {}

    # Root files
    for p in root.glob("*"):
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

    # Explorer subfolder
    exp_dir = root / "explorer"
    if exp_dir.exists():
        for p in exp_dir.glob("*"):
            if p.is_file():
                route = "/explorer/" + p.name
                content = p.read_text(encoding="utf-8")
                assets[route] = {
                    "body": content,
                    "type": get_content_type(p.name)
                }
                if p.name == "index.html":
                    assets["/explorer"] = assets[route]
                    assets["/explorer/"] = assets[route]

    print(f"Packed {len(assets)} routes into assets dictionary.")

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

    let asset = ASSETS[pathname];
    if (!asset && !pathname.includes('.')) {{
      asset = ASSETS[pathname + '.html'];
    }}

    if (asset) {{
      return new Response(asset.body, {{
        status: 200,
        headers: {{
          "Content-Type": asset.type,
          "Cache-Control": "public, max-age=0, must-revalidate",
          "X-Content-Type-Options": "nosniff",
          "X-Frame-Options": "SAMEORIGIN",
          "Referrer-Policy": "strict-origin-when-cross-origin",
          "Permissions-Policy": "camera=(), microphone=(), geolocation=()"
        }}
      }});
    }}

    return new Response("404 Not Found — KETHRAVAX", {{
      status: 404,
      headers: {{ "Content-Type": "text/plain; charset=utf-8" }}
    }});
  }}
}};
"""

    worker_path = root / "_worker.js"
    worker_path.write_text(worker_code, encoding="utf-8")
    print(f"Wrote self-contained _worker.js ({len(worker_code):,} chars, {len(worker_code)/1024:.1f} KB)")

if __name__ == "__main__":
    main()
