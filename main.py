"""
Point d'entree du projet OpportunitySN.

Ce script enchaine toute la chaine de veille, dans l'ordre :

    1. Scraping    : on collecte les offres depuis les sources.
    2. ETL         : nettoyage, validation, stockage en base.
    3. Analyse     : detection d'anomalies + tendances.
    4. Alertes     : construction des alertes.
    5. Notification: generation et envoi (ou simulation) du rapport email.

Usage :
    python main.py                # tout, avec la source de demonstration
    python main.py --reel         # ajoute les sources reelles RemoteOK + Arbeitnow (reseau requis)
    python main.py --nombre 120   # nombre d'offres a generer en demo

L'idee est qu'une seule commande fasse tourner tout le projet de bout en bout.
C'est ce qu'on appellera plus tard depuis le planificateur (cron / schedule).
"""

import argparse

from src.analysis.alerts import generer_alertes
from src.analysis.anomaly_detection import detecter_anomalies
from src.analysis.trend_analysis import salaire_moyen_par_categorie, resume_marche
from src.logger import get_logger
from src.notification.email_service import envoyer_rapport
from src.notification.webhook_service import envoyer_webhook
from src.pipeline.etl import run_etl
from src.pipeline.storage import charger_offres
from src.scrapers.arbeitnow_scraper import ArbeitnowScraper
from src.scrapers.demo_scraper import DemoScraper
from src.scrapers.emploidakar_scraper import EmploiDakarScraper
from src.scrapers.expatdakar_scraper import ExpatDakarScraper
from src.scrapers.remoteok_scraper import RemoteOkScraper
from src.scrapers.senjob_scraper import SenjobScraper

logger = get_logger(__name__)


def collecter(utiliser_reel, nombre_demo):
    """
    Lance les scrapers choisis et fusionne leurs resultats.

    On active toujours la source de demonstration (pour garantir un jeu de
    donnees, meme hors ligne). Les sources reelles ne sont ajoutees que si
    l'utilisateur le demande (--reel), car elles dependent du reseau.

    Sources reelles actuelles :
        - RemoteOK et Arbeitnow : API JSON publiques de jobs Tech en remote.
        - Emploi Dakar : offres Tech locales (Senegal), via le JSON-LD des pages.
        - Expat-Dakar : offres Tech locales, avec parfois de vrais salaires.
        - Senjob : offres Tech locales (categorie Informatique), via le HTML.
    EmploiSenegal est laisse de cote (protege par Cloudflare, 403).
    """
    offres = []

    demo = DemoScraper(nombre=nombre_demo, graine=42)
    offres.extend(demo.run())

    if utiliser_reel:
        sources = (
            RemoteOkScraper(limite=100),
            ArbeitnowScraper(limite=100),
            EmploiDakarScraper(limite=12),
            ExpatDakarScraper(limite=12),
            SenjobScraper(pages=2),
        )
        for scraper in sources:
            offres.extend(scraper.run())

    logger.info("Collecte terminee : %s offres au total.", len(offres))
    return offres


def executer(utiliser_reel=False, nombre_demo=80):
    """Execute la pipeline complete et retourne un resume."""
    logger.info("############ Demarrage de la pipeline OpportunitySN ############")

    # 1. Scraping
    offres_brutes = collecter(utiliser_reel, nombre_demo)

    # 2. ETL
    resume_etl = run_etl(offres_brutes)

    # 3. On recharge depuis la base (donnees propres et dedoublonnees).
    df = charger_offres()

    # 4. Analyse
    df, anomalies = detecter_anomalies(df)
    resume = resume_marche(df)
    salaires = salaire_moyen_par_categorie(df)

    # 5. Alertes
    alertes = generer_alertes(df, anomalies)

    # 6. Notification (rapport HTML + email si active)
    chemin_rapport = envoyer_rapport(resume, alertes, salaires)

    # 7. Automatisation no-code : on pousse les alertes vers Make/Zapier, qui
    #    les redistribue ensuite (Slack, Google Sheets, WhatsApp, email...).
    envoyer_webhook(resume, alertes)

    logger.info("############ Pipeline terminee ############")
    logger.info("Resume ETL     : %s", resume_etl)
    logger.info("Resume marche  : %s", resume)
    logger.info("Alertes        : %s", len(alertes))
    logger.info("Rapport genere : %s", chemin_rapport)

    return {
        "etl": resume_etl,
        "marche": resume,
        "nb_alertes": len(alertes),
        "rapport": str(chemin_rapport),
    }


def main():
    parser = argparse.ArgumentParser(description="Pipeline de veille emploi Tech OpportunitySN")
    parser.add_argument("--reel", action="store_true", help="Activer aussi les sources reelles (RemoteOK + Arbeitnow)")
    parser.add_argument("--nombre", type=int, default=80, help="Nombre d'offres a generer en demo")
    args = parser.parse_args()

    executer(utiliser_reel=args.reel, nombre_demo=args.nombre)


if __name__ == "__main__":
    main()
