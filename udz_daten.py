"""Vorgerechnete Zahlen (daten/vorgerechnet.json, erzeugt von tools/vorrechnen.py)."""

import json
from functools import lru_cache
from pathlib import Path

DATEI = Path(__file__).resolve().parent / "daten" / "vorgerechnet.json"


@lru_cache(maxsize=1)
def laden() -> dict:
    return json.loads(DATEI.read_text(encoding="utf-8"))
