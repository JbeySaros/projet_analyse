"""Configuration pytest pour ajouter le répertoire au PYTHONPATH."""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
