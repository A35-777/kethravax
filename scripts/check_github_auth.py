import subprocess
import urllib.request
import json
import sys

def get_git_credentials():
    p = subprocess.Popen(
        ['git', 'credential', 'fill'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    out, err = p.communicate(input='protocol=https\nhost=github.com\n\n')
    creds = {}
    for line in out.splitlines():
        if '=' in line:
            k, v = line.split('=', 1)
            creds[k.strip()] = v.strip()
    return creds

def check_auth():
    creds = get_git_credentials()
    token = creds.get('password')
    username = creds.get('username')
    print(f"Discovered user from GCM: {username}")
    if not token:
        print("No token found in credential helper.")
        return None
    
    req = urllib.request.Request(
        'https://api.github.com/user',
        headers={
            'Authorization': f'token {token}',
            'User-Agent': 'Kethravax-Release-Manager',
            'Accept': 'application/vnd.github.v3+json'
        }
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print(f"Successfully authenticated as: {data.get('login')} ({data.get('name')})")
            print(f"Scopes: {resp.headers.get('X-OAuth-Scopes')}")
            return token, data.get('login')
    except Exception as e:
        print(f"GitHub API check failed: {e}")
        return None

if __name__ == '__main__':
    res = check_auth()
    if res:
        token, login = res
        print(f"Ready to automate repository creation for {login}!")

