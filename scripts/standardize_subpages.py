import glob
import os
import re

NAV_ITEMS = [
    ("index.html", "Home"),
    ("features.html", "Features"),
    ("benchmarks.html", "Benchmarks"),
    ("how-it-works.html", "How It Works"),
    ("docs.html", "Docs"),
    ("about.html", "About"),
    ("changelog.html", "Changelog"),
    ("explorer/index.html", "⚡ Explorer"),
]

def generate_header(active_file):
    links = []
    for target, label in NAV_ITEMS:
        is_active = (target == active_file)
        active_cls = ' class="active"' if is_active else ''
        style = ' style="color:var(--cyan); font-weight:700;"' if "Explorer" in label else ''
        target_attr = ' target="_blank" rel="noopener"' if "Explorer" in label else ''
        links.append(f'        <a href="{target}"{active_cls}{style}{target_attr}>{label}</a>')
    nav_links = "\n".join(links)

    return f'''  <!-- Site Header -->
  <header class="site-header">
    <div class="nav-container">
      <a href="index.html" class="brand">
        <img src="favicon.svg" alt="KETHRAVAX Logo" width="30" height="30">
        <span>KETHRAVAX</span>
        <span class="brand-badge">v0.1.0</span>
      </a>
      <nav class="nav-menu" aria-label="Main Navigation">
{nav_links}
      </nav>
      <div class="nav-actions">
        <a href="https://github.com/A35-777/kethravax" target="_blank" rel="noopener" class="btn btn-secondary btn-sm">GitHub ↗</a>
        <button id="theme-toggle" class="theme-btn" onclick="toggleTheme()" aria-label="Toggle Theme">🌓</button>
      </div>
    </div>
  </header>'''

FOOTER = '''  <!-- Site Footer -->
  <footer class="site-footer">
    <div class="container">
      <div class="footer-grid">
        <div class="footer-brand">
          <a href="index.html" class="brand">
            <img src="favicon.svg" alt="KETHRAVAX Logo" width="28" height="28">
            <span>KETHRAVAX</span>
          </a>
          <p>
            Precision multi-class structural byte segmentation and ISA discovery for raw, headerless binary streams.
          </p>
          <p style="margin-top:0.75rem; color:var(--text-dim); font-size:0.8rem;">
            Designed &amp; Maintained by <strong>Arin Goel</strong>.
          </p>
        </div>

        <div class="footer-col">
          <h4>Navigation</h4>
          <ul>
            <li><a href="index.html">Home</a></li>
            <li><a href="features.html">Features</a></li>
            <li><a href="benchmarks.html">Benchmarks</a></li>
            <li><a href="how-it-works.html">How It Works</a></li>
            <li><a href="docs.html">Documentation</a></li>
            <li><a href="explorer/index.html">Binary Explorer</a></li>
          </ul>
        </div>

        <div class="footer-col">
          <h4>Research &amp; Specs</h4>
          <ul>
            <li><a href="research.html">Research Paper</a></li>
            <li><a href="benchmarks.html">KethraCorpus Benchmark</a></li>
            <li><a href="changelog.html">Changelog</a></li>
            <li><a href="https://github.com/A35-777/kethravax/blob/main/docs/ARCHITECTURE.md" target="_blank" rel="noopener">Architecture RFC</a></li>
            <li><a href="https://github.com/A35-777/kethravax/blob/main/docs/LABEL_TAXONOMY.md" target="_blank" rel="noopener">Taxonomy Spec</a></li>
          </ul>
        </div>

        <div class="footer-col">
          <h4>Open Source</h4>
          <ul>
            <li><a href="https://github.com/A35-777/kethravax" target="_blank" rel="noopener">GitHub Repository</a></li>
            <li><a href="https://github.com/A35-777/kethravax/issues" target="_blank" rel="noopener">Issue Tracker</a></li>
            <li><a href="feedback.html">Submit Feedback</a></li>
            <li><a href="privacy.html">Privacy Pledge</a></li>
            <li><a href="https://github.com/A35-777/kethravax/blob/main/LICENSE" target="_blank" rel="noopener">Apache-2.0 License</a></li>
          </ul>
        </div>
      </div>

      <div class="footer-bottom">
        <div>
          &copy; 2026 Arin Goel. Released under the Apache-2.0 License.
        </div>
        <div style="display:flex; gap:1.25rem;">
          <a href="privacy.html" style="color:var(--text-dim); text-decoration:none;">Privacy</a>
          <a href="docs.html" style="color:var(--text-dim); text-decoration:none;">Docs</a>
          <a href="https://github.com/A35-777/kethravax" target="_blank" rel="noopener" style="color:var(--text-dim); text-decoration:none;">GitHub</a>
        </div>
      </div>
    </div>
  </footer>'''

def update_page(path):
    fname = os.path.basename(path)
    if fname in ["index.html", "llms.txt", "robots.txt", "sitemap.xml"]:
        return
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace header
    header_regex = r'<header class="site-header">.*?</header>'
    new_header = generate_header(fname)
    if re.search(header_regex, content, re.DOTALL):
        content = re.sub(header_regex, new_header, content, flags=re.DOTALL)
    
    # Replace footer
    footer_regex = r'<footer class="site-footer">.*?</footer>'
    if re.search(footer_regex, content, re.DOTALL):
        content = re.sub(footer_regex, FOOTER, content, flags=re.DOTALL)

    # Ensure app.js is included before </body>
    if 'src="app.js"' not in content:
        content = content.replace('</body>', '  <script src="app.js"></script>\n</body>')

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Updated {fname} header, footer, and scripts.")

def main():
    pages = sorted(glob.glob("D:/kethravax/website/*.html"))
    for p in pages:
        update_page(p)

if __name__ == "__main__":
    main()
