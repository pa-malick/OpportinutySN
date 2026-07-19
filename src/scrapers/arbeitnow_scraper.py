"""
Scraper pour Arbeitnow (https://www.arbeitnow.com).

Arbeitnow expose une API JSON publique et gratuite qui liste des offres, dont
beaucoup en teletravail. Comme RemoteOK, on prefere l'API au scraping HTML :
c'est stable et poli (une seule requete).

Le robots.txt d'Arbeitnow autorise /api (verifie a la main le 2026-07-17). Le
lecteur robots de Python se fait bloquer par le pare-feu et repond "interdit"
a tort, donc on desactive la verification pour cette source documentee.

Particularites de la source :
    - Pas de champ salaire : on tente de le deviner depuis la description.
    - Les dates sont des timestamps Unix (secondes).
    - Les descriptions sont en HTML : on les nettoie avant analyse.
"""

from datetime import datetime, timezone

from src.scrapers.base_scraper import BaseScraper
from src.scrapers.reference_data import COMPETENCES_TECH, INDICATEURS_TECH
from src.scrapers.utils_scraping import (
    est_offre_tech,
    extraire_competences,
    nettoyer_html,
    nettoyer_texte,
)


class ArbeitnowScraper(BaseScraper):
    """Recupere les offres listees sur Arbeitnow (via leur API job board)."""

    source = "arbeitnow"
    url_depart = "https://www.arbeitnow.com/api/job-board-api"

    def __init__(self, limite=100):
        # API documentee : pas de robots a verifier (voir docstring du module).
        super().__init__(respecter_robots=False)
        self.limite = limite

    def parse(self):
        donnees = self.telecharger_json(self.url_depart)
        if not donnees:
            return []

        # Les offres sont dans la cle "data".
        elements = donnees.get("data", []) if isinstance(donnees, dict) else []
        offres = []
        for e in elements:
            offre = self._parser_offre(e)
            if offre:
                offres.append(offre)
            if len(offres) >= self.limite:
                break
        return offres

    def _parser_offre(self, e):
        """Transforme une offre brute de l'API en dictionnaire propre."""
        titre = nettoyer_texte(e.get("title"))
        if not titre:
            return None

        tags = e.get("tags") if isinstance(e.get("tags"), list) else []

        # On ne garde que les vrais postes Tech (l'API renvoie tous les metiers).
        if not est_offre_tech(f"{titre} {' '.join(tags)}", INDICATEURS_TECH):
            return None

        entreprise = nettoyer_texte(e.get("company_name")) or "Non precise"

        # Si l'offre est en remote et sans lieu clair, on note "Remote".
        lieu = nettoyer_texte(e.get("location"))
        if not lieu:
            lieu = "Remote" if e.get("remote") else "Non precise"

        # Competences : depuis la description nettoyee + les tags.
        description = nettoyer_html(e.get("description"))
        texte_competences = f"{description} {' '.join(tags)}"
        competences = extraire_competences(texte_competences, COMPETENCES_TECH)

        # Arbeitnow n'a pas de champ salaire. Le deviner dans la description
        # libre donne trop de faux positifs (numeros, identifiants), donc on
        # laisse None : mieux vaut pas de salaire qu'un salaire faux.
        sal_min, sal_max = None, None

        # created_at est un timestamp Unix (secondes) -> date lisible.
        date_publication = None
        ts = e.get("created_at")
        if isinstance(ts, (int, float)):
            date_publication = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")

        return {
            "titre": titre,
            "entreprise": entreprise,
            "lieu": lieu,
            "pays": "Remote" if e.get("remote") else "International",
            "categorie": None,  # devine plus tard dans l'ETL
            "competences": competences,
            "salaire_min": sal_min,
            "salaire_max": sal_max,
            "devise": "EUR",  # Arbeitnow est majoritairement Europe
            "date_publication": date_publication,
            "source": self.source,
            "url": e.get("url"),
        }
