import urllib.request
import time

urls = [
    'https://kethravax.pages.dev/',
    'https://kethravax.pages.dev/how-it-works.html',
    'https://kethravax.pages.dev/benchmarks.html',
    'https://kethravax.pages.dev/research.html',
    'https://kethravax.pages.dev/docs.html',
    'https://kethravax.pages.dev/explorer/index.html',
    'https://kethravax.pages.dev/explorer/',
    'https://kethravax.pages.dev/styles.css',
    'https://kethravax.pages.dev/robots.txt',
    'https://kethravax.pages.dev/sitemap.xml',
    'https://0596ca08.kethravax.pages.dev/'
]

all_passed = True
for url in urls:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()
            print(f"PASS: {url} -> HTTP {resp.status} ({len(content)} bytes)")
    except Exception as e:
        print(f"FAIL: {url} -> {e}")
        all_passed = False

if all_passed:
    print("\n>>> ALL LIVE ROUTES VERIFIED 100% OPERATIONAL! <<<")
else:
    print("\n>>> SOME ROUTES FAILED <<<")
