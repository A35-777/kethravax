import os
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

def api_request(method, url, token, payload=None):
    headers = {
        'Authorization': f'token {token}',
        'User-Agent': 'Kethravax-Release-Manager',
        'Accept': 'application/vnd.github.v3+json'
    }
    data = None
    if payload is not None:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(payload).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode('utf-8')
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        try:
            err_json = json.loads(body)
        except Exception:
            err_json = {'error': body}
        return e.code, err_json

def main():
    creds = get_git_credentials()
    token = creds.get('password')
    username = creds.get('username', 'A35-777')
    if not token:
        print("Error: No GitHub token found in git credential manager.")
        sys.exit(1)
    
    repo_name = 'kethravax'
    repo_full = f'{username}/{repo_name}'
    print(f"Targeting repository: {repo_full}")

    # Step 1: Check if repository exists
    status, res = api_request('GET', f'https://api.github.com/repos/{repo_full}', token)
    if status == 200:
        print(f"Repository {repo_full} already exists on GitHub.")
    elif status == 404:
        print(f"Creating repository {repo_full} on GitHub...")
        create_payload = {
            'name': repo_name,
            'description': 'Precision learned structural byte-stream segmentation and firmware architecture identification engine (PyTorch)',
            'homepage': 'https://kethravax.pages.dev',
            'private': False,
            'has_issues': True,
            'has_projects': True,
            'has_wiki': True
        }
        status, res = api_request('POST', 'https://api.github.com/user/repos', token, create_payload)
        if status in (200, 201):
            print(f"Successfully created GitHub repository: {res.get('html_url')}")
        else:
            print(f"Failed to create repo. Status: {status}, Response: {res}")
            sys.exit(1)
    else:
        print(f"Unexpected status checking repo: {status}, {res}")
        sys.exit(1)

    # Step 2: Configure Git locally and push
    os.chdir('d:/kethravax')
    subprocess.run(['git', 'config', 'user.name', username], check=True)
    subprocess.run(['git', 'config', 'user.email', 'toaringoel@gmail.com'], check=True)
    subprocess.run(['git', 'branch', '-M', 'main'], check=True)

    # Check remotes
    p_rem = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True)
    remote_url = f'https://github.com/{repo_full}.git'
    if 'origin' in p_rem.stdout:
        subprocess.run(['git', 'remote', 'set-url', 'origin', remote_url], check=True)
    else:
        subprocess.run(['git', 'remote', 'add', 'origin', remote_url], check=True)

    # Stage all updates and commit
    subprocess.run(['git', 'add', '-A'], check=True)
    p_st = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
    if p_st.stdout.strip():
        subprocess.run(['git', 'commit', '-m', 'feat: open-source release suite, website with interactive explorer, and CI'], check=True)
        print("Committed pending changes.")
    else:
        print("Working tree is clean.")

    # Push to origin main
    print(f"Pushing to {remote_url} on branch main...")
    p_push = subprocess.run(['git', 'push', '-u', 'origin', 'main'], capture_output=True, text=True)
    print(p_push.stdout)
    if p_push.stderr:
        print(p_push.stderr)
    if p_push.returncode != 0:
        print("Git push failed!")
        sys.exit(1)
    print("Git push succeeded!")

    # Step 3: Create GitHub Release v0.1.0
    print("Creating GitHub release v0.1.0...")
    rel_status, rel_res = api_request('GET', f'https://api.github.com/repos/{repo_full}/releases/tags/v0.1.0', token)
    if rel_status == 200:
        print("Release v0.1.0 already exists.")
    else:
        rel_payload = {
            'tag_name': 'v0.1.0',
            'target_commitish': 'main',
            'name': 'Kethravax v0.1.0 — Learned Structural Byte-Stream Segmentation',
            'body': """# Kethravax v0.1.0 Release

Kethravax is an open-source, learned neural and statistical system for **multi-class structural segmentation and ISA discovery across raw, unheadered binary streams**.

### Key Capabilities
- **Multi-Class Byte Segmentation:** Identifies contiguous byte ranges for `CODE`, `DATA_STRING`, `DATA_TABLE`, `DATA_RAW`, `PADDING`, `COMPRESSED_OPAQUE`, and `UNKNOWN_AMBIGUOUS`.
- **ISA Identification:** Identifies 7 instruction set architectures (`x86_64`, `x86_32`, `arm32_arm`, `arm32_thumb`, `aarch64`, `mips32`, `riscv`).
- **Dense Byte-Level Ground Truth:** Pure-Python parsers for PE/COFF and ELF/DWARF binaries extracting exact section and mapping symbol boundaries (`$a`, `$t`, `$d`).
- **Pretrained Hybrid Neural Architecture:** KethraSeg-Hybrid (Multi-scale 1D Dilated Conv + Bidirectional LSTM + Multi-Head Output).
- **Interactive Binary Explorer:** Zero-dependency client-side WebAssembly/HTML5 visual byte inspector and segment visualizer.
- **Python SDK & CLI:** High-level `BinarySegmenter` API and `kethravax` CLI.

### Live Demo & Website
- Website & Documentation: [https://kethravax.pages.dev](https://kethravax.pages.dev)
- Interactive Explorer: [https://kethravax.pages.dev/explorer/](https://kethravax.pages.dev/explorer/)
""",
            'draft': False,
            'prerelease': False
        }
        status, rel_data = api_request('POST', f'https://api.github.com/repos/{repo_full}/releases', token, rel_payload)
        if status in (200, 201):
            print(f"Created GitHub Release: {rel_data.get('html_url')}")
        else:
            print(f"Failed to create release: {status}, {rel_data}")

if __name__ == '__main__':
    main()

