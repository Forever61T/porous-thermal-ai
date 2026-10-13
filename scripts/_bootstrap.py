"""Allow 'python scripts/file.py' without installing this small project as a package."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
