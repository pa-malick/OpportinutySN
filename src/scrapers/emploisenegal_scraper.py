"""
Scraper pour EmploiSenegal (https://www.emploisenegal.com).

C'est un exemple de scraper HTML "reel" : on telecharge les pages de resultats
et on lit le HTML avec BeautifulSoup. Les sites web changent regulierement leur
structure, donc les selecteurs CSS ci-dessous peuvent devoir etre ajustes un
jour. C'est normal, ca fait partie du metier de la veille.

Note : ce scraper est ecrit pour etre poli (delai + robots.txt herites de la
classe de base). Si le site est inaccessible ou a change, la methode run()
heritee attrape l'erreur et renvoie une liste vide sans faire planter le reste.
"""

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.scrapers.base_scraper import BaseScraper
from src.scrapers.reference_data import COMPETENCES_TECH
from src.scrapers.utils_scraping import (
    extraire_competences,
    extraire_salaire,
    nettoyer_texte,
)


class EmploiSenegalScraper(BaseScraper):
    """Recupere les offres Tech/Data listees sur EmploiSenegal."""

    source = "emploisenegal"
    url_depart = "https://www.emploisenegal.com/recherche-jobs-senegal"

    def __init__(self, nombre_pages=2, respecter_robots=True):
        super().__init__(respecter_robots=respecter_robots)
        self.nombre_pages = nombre_pages

    def parse(self):
        offres = []
        for page in range(1, self.nombre_pages + 1):
            url = f"{self.url_depart}?page={page}"
            html = self.telecharger(url)
            if not html:
                continue
            offres.extend(self._parser_page(html))
        return offres

    def _parser_page(self, html):
        """Extrait les offres d'une page de resultats."""
        soup = BeautifulSoup(html, "lxml")
        resultats = []

        # Chaque offre est dans un bloc "card job". Si la structure change,
        # c'est ici qu'il faudra adapter le selecteur.
        cartes = soup.select("div.card-job")
        for carte in cartes:
            try:
                resultats.append(self._parser_carte(carte))
            except Exception:  # noqa: BLE001
                # Une carte mal formee ne doit pas casser toute la page.
                continue

        return [o for o in resultats if o is not None]

    def _parser_carte(self, carte):
        """Transforme un bloc HTML d'offre en dictionnaire propre."""
        titre_tag = carte.select_one("h3 a")
        if not titre_tag:
            return None

        titre = nettoyer_texte(titre_tag.get_text())
        lien = urljoin(self.url_depart, titre_tag.get("href", ""))

        entreprise_tag = carte.select_one("a.card-job-company")
        entreprise = nettoyer_texte(entreprise_tag.get_text()) if entreprise_tag else "Non precise"

        lieu_tag = carte.select_one("ul.list-default li")
        lieu = nettoyer_texte(lieu_tag.get_text()) if lieu_tag else "Non precise"

        # La description sert a detecter competences et salaire.
        description_tag = carte.select_one("div.card-job-detail p")
        description = nettoyer_texte(description_tag.get_text()) if description_tag else ""

        sal_min, sal_max = extraire_salaire(description)
        competences = extraire_competences(description, COMPETENCES_TECH)

        return {
            "titre": titre,
            "entreprise": entreprise,
            "lieu": lieu,
            "pays": "Senegal",
            "categorie": None,  # sera devine plus tard dans l'ETL
            "competences": competences,
            "salaire_min": sal_min,
            "salaire_max": sal_max,
            "devise": "XOF",
            "date_publication": None,
            "source": self.source,
            "url": lien,
        }
