"""
DAG Airflow (optionnel, pour la version "qui impressionne").

Airflow est l'outil standard de l'industrie pour orchestrer des pipelines de
donnees. Ce fichier decrit notre pipeline sous forme de graphe de taches (DAG) :
scraping -> etl -> analyse -> notification.

Ce fichier n'est utile que si Airflow est installe. On le garde separe pour que
le projet reste lancable sans Airflow (via schedule_jobs.py). Pour l'utiliser,
copier ce fichier dans le dossier dags/ d'une installation Airflow.
"""

from datetime import datetime, timedelta

# Ces imports ne fonctionnent que dans un environnement Airflow.
try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    AIRFLOW_DISPONIBLE = True
except ImportError:
    AIRFLOW_DISPONIBLE = False


def _tache_scraping(**_):
    from src.scrapers.demo_scraper import DemoScraper
    offres = DemoScraper(nombre=80, graine=42).run()
    # En vrai on passerait les donnees via XCom ; ici on garde simple et on
    # relance la collecte dans l'ETL. Le but est de montrer la structure.
    return len(offres)


def _tache_pipeline(**_):
    from main import executer
    executer(utiliser_reel=False, nombre_demo=80)


if AIRFLOW_DISPONIBLE:
    arguments_defaut = {
        "owner": "papa-malick",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    }

    with DAG(
        dag_id="opportunity_sn_veille",
        description="Pipeline de veille emploi Tech Senegal",
        default_args=arguments_defaut,
        schedule_interval="0 8 * * *",  # tous les jours a 8h
        start_date=datetime(2026, 1, 1),
        catchup=False,
        tags=["veille", "data-engineering"],
    ) as dag:

        verifier = PythonOperator(
            task_id="verifier_sources",
            python_callable=_tache_scraping,
        )

        lancer = PythonOperator(
            task_id="executer_pipeline",
            python_callable=_tache_pipeline,
        )

        # Ordre d'execution : on verifie les sources, puis on lance la pipeline.
        verifier >> lancer
