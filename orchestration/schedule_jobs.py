"""
Planificateur simple avec la librairie 'schedule'.

But : faire tourner la pipeline automatiquement, par exemple tous les jours a
8h. C'est l'alternative legere a Airflow, sans rien installer de lourd. On
laisse ce script tourner en fond (ou dans un conteneur Docker) et il declenche
la pipeline tout seul.

Lancer avec :  python orchestration/schedule_jobs.py
"""

import time

import schedule

from main import executer
from src.logger import get_logger

logger = get_logger(__name__)


def job():
    """La tache planifiee : une execution complete de la pipeline."""
    logger.info("Declenchement planifie de la pipeline.")
    try:
        executer(utiliser_reel=False, nombre_demo=80)
    except Exception as e:  # noqa: BLE001
        # On ne veut surtout pas que le planificateur s'arrete sur une erreur.
        logger.error("La pipeline planifiee a echoue : %s", e)


def main():
    # Tous les jours a 08:00. On peut ajouter d'autres creneaux facilement.
    schedule.every().day.at("08:00").do(job)
    logger.info("Planificateur demarre. Prochaine execution a 08:00.")

    # On lance une fois tout de suite pour ne pas attendre le lendemain au 1er run.
    job()

    while True:
        schedule.run_pending()
        time.sleep(60)  # on verifie chaque minute s'il y a une tache a lancer


if __name__ == "__main__":
    main()
