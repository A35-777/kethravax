import urllib.request

urls = [
    'https://kethravax.pages.dev/',
    'https://kethravax.pages.dev/how-it-works.html',
    'https://kethravax.pages.dev/benchmarks.html',
    'https://kethravax.pages.dev/research.html',
    'https://kethravax.pages.dev/docs.html',
    'https://kethravax.pages.dev/explorer/',
    'https://kethravax.pages.dev/styles.css',
    'https://kethravax.pages.dev/robots.txt',
    'https://kethravax.pages.dev/sitemap.xml',
    'https://fd7447f5.kethravax.pages.dev/'
]

for url in urls:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read()
            print(f"PASS: {url} -> HTTP {resp.status} ({len(content)} bytes)")
    except Exception as e:
        print(f"FAIL: {url} -> {e}")
