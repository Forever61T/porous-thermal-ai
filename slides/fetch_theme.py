"""Fetch four pinned upstream theme files on explicit user invocation.
Independent implementation. The files retain upstream attribution and licenses.
"""
from pathlib import Path
from urllib.request import urlopen
import hashlib, json

root=Path(__file__).resolve().parent
manifest=json.loads((root/'theme_manifest.json').read_text())
base='https://raw.githubusercontent.com/qychen2001/ZJU-Beamer-Template/'+manifest['commit']+'/'
for name, expected in manifest['sha256'].items():
    target=root/name
    if target.exists():
        if hashlib.sha256(target.read_bytes()).hexdigest()!=expected:
            raise SystemExit('Existing theme file differs; left untouched: '+name)
        print('Verified existing: '+name)
        continue
    with urlopen(base+name,timeout=30) as response:
        payload=response.read()
    if hashlib.sha256(payload).hexdigest()!=expected:
        raise SystemExit('Upstream checksum mismatch: '+name)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(payload)
    print('Fetched and verified: '+name)
