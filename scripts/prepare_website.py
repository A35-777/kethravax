import os
import shutil
from pathlib import Path

website_dir = Path("d:/kethravax/website")
explorer_dir = website_dir / "explorer"
explorer_dir.mkdir(parents=True, exist_ok=True)

# Copy explorer/index.html to website/explorer/index.html
shutil.copy("d:/kethravax/explorer/index.html", explorer_dir / "index.html")
print(f"Copied explorer to {explorer_dir / 'index.html'}")

# Update HTML files
for html_file in website_dir.glob("*.html"):
    content = html_file.read_text(encoding="utf-8")
    content = content.replace("https://github.com/kethravax/kethravax", "https://github.com/A35-777/kethravax")
    content = content.replace("../explorer/index.html", "explorer/index.html")
    html_file.write_text(content, encoding="utf-8")
    print(f"Updated {html_file.name}")

# Also update explorer index.html links back to website
explorer_html = explorer_dir / "index.html"
exp_content = explorer_html.read_text(encoding="utf-8")
exp_content = exp_content.replace("https://github.com/kethravax/kethravax", "https://github.com/A35-777/kethravax")
exp_content = exp_content.replace("../website/index.html", "../index.html")
explorer_html.write_text(exp_content, encoding="utf-8")
print("Updated website/explorer/index.html")
