"""Paths and reproducibility helpers. All paths resolve relative to this project."""
from pathlib import Path
import hashlib
import json
import platform
import sys
import importlib.metadata

ROOT = Path(__file__).resolve().parents[1]

def config(project):
    return json.loads((ROOT / 'configs' / f'{project}.json').read_text())

def save_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def environment():
    packages = ['numpy','pandas','openpyxl','scipy','scikit-learn','matplotlib','joblib','pytest']
    return dict(python=sys.version, platform=platform.platform(), processor=platform.machine(),
                packages={p: importlib.metadata.version(p) for p in packages}, gpu_used=False)
