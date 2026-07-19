"""
Scraper pour RemoteOK (https://remoteok.com).

RemoteOK expose une API JSON publique et documentee : une simple requete GET
renvoie la liste des offres Tech en teletravail. C'est bien plus fiable qu'un
scraping HTML classique (pas de selecteurs CSS qui cassent, pas de Cloudflare).

Condition d'utilisation imposee par RemoteOK (voir le champ "legal" de leur
reponse) : citer RemoteOK comme source et garder le lien retour vers l'offre.
On respecte ca en conservant source="remoteok" et l'url d'origine sur chaque
offre.

Comme c'est une API documentee faite pour etre appelee, on desactive la
verification robots.txt : le robots autorise deja /api, mais le lecteur Python
se fait bloquer par le pare-feu quand il lit le robots (faux negatif). Verifie
a la main le 2026-07-17 : robots.txt de RemoteOK autorise /api.
"""

from src.scrapers.base_scraper import BaseScraper
from src.scrapers.reference_data import COMPETENCES_TECH, INDICATEURS_TECH
from src.scrapers.utils_scraping import (
    est_offre_tech,
    extraire_competences,
    nettoyer_html,
    nettoyer_texte,
)


class RemoteOkScraper(BaseScraper):
    """Recupere les offres Tech en remote listees sur RemoteOK (via leur API)."""

    source = "remoteok"
    url_depart = "https://remoteok.com/api"

    def __init__(self, limite=100):
        # API documentee : pas de robots a verifier (voir docstring du module).
        super().__init__(respecter_robots=False)
        self.limite = limite

    def parse(self):
        donnees = self.telecharger_json(self.url_depart)
        if not donnees:
            return []

        offres = []
        for element in donnees:
            # Le tout premier element de la reponse RemoteOK n'est pas une offre
            # mais un bloc de metadonnees legales : on le saute.
            if not isinstance(element, dict) or "position" not in element:
                continue
            offre = self._parser_offre(element)
            if offre:
                offres.append(offre)
            if len(offres) >= self.limite:
                break
        return offres

    def _parser_offre(self, e):
        """Transforme une offre brute de l'API en dictionnaire propre."""
        titre = nettoyer_html(e.get("position"))
        if not titre:
            return None

        tags = e.get("tags") if isinstance(e.get("tags"), list) else []

        # On ne garde que les vrais postes Tech (l'API renvoie tous les metiers).
        if not est_offre_tech(f"{titre} {' '.join(tags)}", INDICATEURS_TECH):
            return None

        entreprise = nettoyer_texte(e.get("company")) or "Non precise"
        lieu = nettoyer_texte(e.get("location")) or "Remote"

        # On cherche les competences dans la description + les tags de l'offre.
        description = nettoyer_html(e.get("description"))
        texte_competences = f"{description} {' '.join(tags)}"
        competences = extraire_competences(texte_competences, COMPETENCES_TECH)

        # Salaire : RemoteOK met souvent 0 quand il est inconnu. On ne veut pas
        # d'un faux "0 FCFA", donc on le convertit en None (non precise).
        sal_min = e.get("salary_min") or None
        sal_max = e.get("salary_max") or None

        # La date est au format ISO ("2026-07-16T21:39:00+00:00"), on garde
        # juste la partie date.
        date_pub = e.get("date")
        date_publication = date_pub[:10] if isinstance(date_pub, str) else None

        return {
            "titre": titre,
            "entreprise": entreprise,
            "lieu": lieu,
            "pays": "Remote",
            "categorie": None,  # devine plus tard dans l'ETL
            "competences": competences,
            "salaire_min": sal_min,
            "salaire_max": sal_max,
            "devise": "USD",  # RemoteOK publie les salaires en dollars
            "date_publication": date_publication,
            "source": self.source,
            "url": e.get("url"),
        }
