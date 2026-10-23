import os

for root, dirs, files in os.walk('.'):
    if '.git' in root or 'node_modules' in root: continue
    for f in files:
        if f.endswith(('.cmd', '.bat', '.ps1', '.py', '.cs', '.json')):
            path = os.path.join(root, f)
            try:
                content = open(path, 'r', encoding='utf-8', errors='ignore').read()
                if 'Published models need a compatible native host' in content or 'compatible native host' in content:
                    print(f"Found in: {path}")
            except Exception:
                pass
