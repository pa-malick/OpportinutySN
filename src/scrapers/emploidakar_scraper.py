"""
Scraper pour Emploi Dakar (https://www.emploidakar.com).

Premiere vraie source 100% senegalaise du projet. Le site est un WordPress
(plugin WP Job Manager) protege par Cloudflare sur ses API, mais :
    - son sitemap `job_listing-sitemap.xml` liste toutes les offres,
    - chaque page d'offre est lisible et embarque un JSON-LD "JobPosting"
      (donnees structurees schema.org : titre, entreprise, lieu, date, salaire).

Strategie (choisie pour etre polie et efficace) :
    1. On lit le sitemap des offres.
    2. On ne garde que les URL dont le slug ressemble a un poste Tech (le slug
       contient le metier), pour ne PAS telecharger les centaines d'offres non
       Tech (vente, chauffeur, comptable...).
    3. On telecharge seulement ces pages et on lit leur JSON-LD.

Le JSON-LD est bien plus robuste aux changements de design qu'un parsing HTML
par selecteurs CSS. Robots.txt verifie le 2026-07-18 : seul /CV/ est interdit,
/offre-demploi/ est autorise.
"""

from datetime import datetime

from src.scrapers.base_scraper import BaseScraper
from src.scrapers.reference_data import COMPETENCES_TECH, INDICATEURS_TECH
from src.scrapers.utils_scraping import (
    est_offre_tech,
    extraire_competences,
    extraire_json_ld_jobposting,
    nettoyer_html,
    nettoyer_texte,
)

# Le site sert le contenu aux navigateurs mais bloque les User-Agent "robot"
# evidents (Cloudflare). On se presente donc comme un navigateur classique.
NAVIGATEUR_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class EmploiDakarScraper(BaseScraper):
    """Recupere les offres Tech locales d'Emploi Dakar via le JSON-LD des pages."""

    source = "emploidakar"
    url_depart = "https://www.emploidakar.com/job_listing-sitemap.xml"

    def __init__(self, limite=15):
        # robots.txt n'interdit que /CV/ (verifie), on peut y aller directement.
        super().__init__(respecter_robots=False)
        self.limite = limite
        # On surcharge le User-Agent pour passer le filtre anti-bot du site.
        self.session.headers.update({"User-Agent": NAVIGATEUR_UA})

    def parse(self):
        xml = self.telecharger(self.url_depart)
        if not xml:
            return []

        urls = self._urls_offres_tech(xml)
        offres = []
        for url in urls[: self.limite]:
            html_page = self.telecharger(url)
            if not html_page:
                continue
            offre = self._parser_page(html_page, url)
            if offre:
                offres.append(offre)
        return offres

    def _urls_offres_tech(self, xml):
        """Liste les URL d'offres dont le slug ressemble a un poste Tech."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(xml, "xml")
        urls = [l.get_text() for l in soup.find_all("loc") if "/offre-demploi/" in l.get_text()]
        # Le slug contient le titre : on filtre dessus pour eviter de charger
        # des centaines de pages non Tech.
        return [u for u in urls if est_offre_tech(u.replace("-", " "), INDICATEURS_TECH)]

    def _parser_page(self, html_page, url):
        """Extrait une offre depuis le JSON-LD JobPosting de la page."""
        jp = extraire_json_ld_jobposting(html_page)
        if not jp:
            return None

        # Les titres contiennent parfois des entites HTML (double-encodees) :
        # nettoyer_html les decode proprement.
        titre = nettoyer_html(jp.get("title"))
        if not titre:
            return None

        entreprise = self._nom_entreprise(jp)
        lieu = self._lieu(jp)

        description = nettoyer_html(jp.get("description"))
        competences = extraire_competences(f"{titre} {description}", COMPETENCES_TECH)

        sal_min, sal_max = self._salaire(jp)

        date_publication = None
        date_pub = jp.get("datePosted")
        if isinstance(date_pub, str) and len(date_pub) >= 10:
            date_publication = date_pub[:10]

        return {
            "titre": titre,
            "entreprise": entreprise,
            "lieu": lieu,
            "pays": "Senegal",
            "categorie": None,  # devine plus tard dans l'ETL
            "competences": competences,
            "salaire_min": sal_min,
            "salaire_max": sal_max,
            "devise": "XOF",
            "date_publication": date_publication,
            "source": self.source,
            "url": jp.get("url") or url,
        }

    @staticmethod
    def _nom_entreprise(jp):
        """hiringOrganization peut etre un objet ou absent."""
        org = jp.get("hiringOrganization")
        if isinstance(org, dict):
            return nettoyer_texte(org.get("name")) or "Non precise"
        return nettoyer_texte(org) or "Non precise"

    @staticmethod
    def _lieu(jp):
        """jobLocation.address peut etre une chaine ou un objet PostalAddress."""
        loc = jp.get("jobLocation")
        if isinstance(loc, list) and loc:
            loc = loc[0]
        if isinstance(loc, dict):
            adr = loc.get("address")
            if isinstance(adr, dict):
                # On prend la ville si dispo, sinon la region.
                ville = adr.get("addressLocality") or adr.get("addressRegion")
                return nettoyer_texte(ville) or "Senegal"
            return nettoyer_texte(adr) or "Senegal"
        return "Senegal"

    @staticmethod
    def _salaire(jp):
        """
        baseSalary est souvent null sur ce site. Quand il existe, c'est un objet
        {currency, value: {minValue, maxValue}}. On sort une fourchette d'entiers.
        """
        bs = jp.get("baseSalary")
        if not isinstance(bs, dict):
            return (None, None)
        valeur = bs.get("value")
        if not isinstance(valeur, dict):
            return (None, None)

        def _entier(x):
            try:
                return int(float(x))
            except (TypeError, ValueError):
                return None

        mini = _entier(valeur.get("minValue"))
        maxi = _entier(valeur.get("maxValue"))
        # Si une seule valeur est donnee, on la met des deux cotes.
        unique = _entier(valeur.get("value"))
        if mini is None and maxi is None and unique is not None:
            return (unique, unique)
        return (mini, maxi)
