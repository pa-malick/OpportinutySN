"""
Configuration du logging pour tout le projet.

Plutot que des print() partout, on utilise un vrai logger. Avantage :
on ecrit a la fois dans la console (pour suivre en direct) et dans un
fichier (pour garder une trace apres coup). Chaque module recupere son
logger avec get_logger(__name__).
"""

import logging
from logging.handlers import RotatingFileHandler

from src.config import LOGS_DIR

# Format lisible : date, niveau, nom du module, message.
_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(nom):
    """
    Retourne un logger configure.

    On evite de reconfigurer deux fois le meme logger (sinon on aurait
    des messages en double).
    """
    logger = logging.getLogger(nom)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(_FORMAT, datefmt=_DATE_FORMAT)

    # 1) Sortie console
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    # 2) Sortie fichier avec rotation (le fichier ne grossit pas a l'infini).
    fichier = RotatingFileHandler(
        LOGS_DIR / "opportunity.log",
        maxBytes=1_000_000,   # 1 Mo par fichier
        backupCount=3,        # on garde 3 anciens fichiers
        encoding="utf-8",
    )
    fichier.setFormatter(formatter)
    logger.addHandler(fichier)

    return logger
