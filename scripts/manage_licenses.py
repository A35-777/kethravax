import subprocess
import urllib.request
import json
import base64
import os

def get_token():
    p = subprocess.Popen(['git', 'credential', 'fill'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, _ = p.communicate(input='protocol=https\nhost=github.com\n\n')
    for line in out.splitlines():
        if line.startswith('password='):
            return line.split('=', 1)[1]
    return os.environ.get('GITHUB_TOKEN', '')

def inspect_licenses():
    token = get_token()
    headers = {
        'Authorization': f'token {token}',
        'User-Agent': 'Kethravax-Script',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Get all repos
    req = urllib.request.Request('https://api.github.com/user/repos?per_page=100&type=owner', headers=headers)
    with urllib.request.urlopen(req) as resp:
        repos = json.loads(resp.read().decode('utf-8'))
        
    for r in repos:
        name = r['name']
        url = f"https://api.github.com/repos/A35-777/{name}/license"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                raw = base64.b64decode(data['content']).decode('utf-8', errors='ignore')
                print(f"=== {name} (path: {data['path']}, sha: {data['sha']}) ===")
                lines = raw.splitlines()
                for line in lines[:10]:
                    print("  ", line)
        except urllib.error.HTTPError as e:
            print(f"=== {name} === No standard license: HTTP {e.code}")

if __name__ == '__main__':
    inspect_licenses()
