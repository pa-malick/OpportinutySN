"""
Classe de base pour tous les scrapers.

L'idee de design : chaque source (EmploiSenegal, Indeed, une demo...) herite
de BaseScraper. La classe mere s'occupe de tout ce qui est commun :
    - faire des requetes HTTP proprement (avec retry et timeout),
    - respecter un delai entre les requetes (throttling),
    - verifier le robots.txt,
    - garder une session ouverte.

Chaque scraper enfant n'a plus qu'a implementer une seule methode : parse().
Ca s'appelle le patron de conception "Template Method". C'est ce qui rend
l'ajout d'une nouvelle source rapide et sans copier-coller.
"""

import json
import time
from abc import ABC, abstractmethod

import requests

from src.config import MAX_RETRIES, REQUEST_TIMEOUT, SCRAPING_DELAY, USER_AGENT
from src.logger import get_logger
from src.scrapers.utils_scraping import robots_autorise

logger = get_logger(__name__)


class BaseScraper(ABC):
    """Classe abstraite : on ne l'utilise jamais seule, on en herite."""

    # Chaque scraper enfant doit definir son nom de source et son URL de depart.
    source = "base"
    url_depart = ""

    def __init__(self, respecter_robots=True):
        self.respecter_robots = respecter_robots
        # Une session requests reutilise la connexion, c'est plus rapide.
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def telecharger(self, url):
        """
        Telecharge une page et retourne son HTML (ou None en cas d'echec).

        On gere ici les points sensibles d'un scraping en production :
            - le respect du robots.txt,
            - le retry avec attente progressive si le serveur repond mal,
            - le throttling pour ne pas surcharger le site.
        """
        if self.respecter_robots and not robots_autorise(url, USER_AGENT):
            logger.warning("robots.txt interdit %s, on saute cette page.", url)
            return None

        for essai in range(1, MAX_RETRIES + 1):
            try:
                reponse = self.session.get(url, timeout=REQUEST_TIMEOUT)
                reponse.raise_for_status()
                # On attend un peu avant la prochaine requete, question de politesse.
                time.sleep(SCRAPING_DELAY)
                return reponse.text
            except requests.RequestException as e:
                # Attente progressive : 2s, 4s, 6s... pour laisser le serveur respirer.
                attente = SCRAPING_DELAY * essai
                logger.warning(
                    "Echec %s/%s sur %s (%s). Nouvel essai dans %.1fs.",
                    essai, MAX_RETRIES, url, e, attente,
                )
                time.sleep(attente)

        logger.error("Abandon apres %s essais sur %s", MAX_RETRIES, url)
        return None

    def telecharger_json(self, url):
        """
        Comme telecharger(), mais pour une API : renvoie le JSON deja parse.

        Pratique pour les sources qui exposent une API (RemoteOK, Arbeitnow...)
        plutot que du HTML. On reutilise tout le travail de telecharger()
        (retry, throttling) et on decode juste la reponse en objet Python.
        Renvoie None si le telechargement echoue ou si ce n'est pas du JSON.
        """
        texte = self.telecharger(url)
        if not texte:
            return None
        try:
            return json.loads(texte)
        except json.JSONDecodeError as e:
            logger.error("Reponse non-JSON depuis %s : %s", url, e)
            return None

    @abstractmethod
    def parse(self):
        """
        A implementer dans chaque scraper enfant.

        Doit retourner une liste de dictionnaires, un par offre d'emploi.
        """
        raise NotImplementedError

    def run(self):
        """
        Point d'entree unique d'un scraper.

        On enveloppe parse() dans un try/except pour qu'un scraper qui
        plante ne fasse pas tomber toute la pipeline. On loggue et on
        retourne une liste vide, la pipeline continuera avec les autres sources.
        """
        logger.info("Demarrage du scraper : %s", self.source)
        try:
            offres = self.parse()
            logger.info("%s : %s offres recuperees.", self.source, len(offres))
            return offres
        except Exception as e:  # noqa: BLE001
            logger.error("Le scraper %s a plante : %s", self.source, e)
            return []
