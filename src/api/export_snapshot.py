"""
Exporte un instantane des offres vers un fichier JSON.

But : que l'outil affiche de vraies donnees meme sans lancer l'API (site
deploye en statique, ou demo hors ligne). Le front essaie d'abord l'API en
direct, puis se rabat sur ce fichier.

Lancer avec :  python -m src.api.export_snapshot
Le fichier est ecrit dans frontend/public/offres.json
"""

import json

from src.api.server import build_offres
from src.config import BASE_DIR
from src.logger import get_logger

logger = get_logger(__name__)

SORTIE = BASE_DIR / "frontend" / "public" / "offres.json"


def exporter():
    donnees = build_offres()
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    SORTIE.write_text(json.dumps(donnees, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Snapshot ecrit : %s (%s offres)", SORTIE, len(donnees["offres"]))


if __name__ == "__main__":
    exporter()
