"""Gemeinsame Pfade: Wurzelordner (Module der App), tests/ (Orakel-Hilfen) und tools/ (Atlas-Zählung)."""

import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
for ordner in (WURZEL, WURZEL / "tests", WURZEL / "tools"):
    if str(ordner) not in sys.path:
        sys.path.insert(0, str(ordner))
