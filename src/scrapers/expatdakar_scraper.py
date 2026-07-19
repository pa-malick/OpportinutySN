"""
Scraper pour Expat-Dakar (https://www.expat-dakar.com), categorie emploi info.

Interet principal : c'est une des rares sources senegalaises qui AFFICHE des
salaires (ex "Entre 100 000 et 200 000"), precieux pour faire vivre la
detection d'anomalies. Sans salaires reels, cette analyse tourne a vide.

Comment on procede :
    1. On lit la page categorie "emploi-informatique" et on recupere les liens
       des annonces (/annonce/...), qu'on filtre sur les postes Tech.
    2. Chaque annonce embarque un JSON-LD JobPosting (imbrique dans @graph)
       -> titre, entreprise, date. On le lit avec notre helper.
    3. Le salaire n'est pas dans le JSON-LD (baseSalary souvent null) mais dans
       un <span class="listing-item__price"> -> on l'extrait a part.
    4. Le lieu vient de la PostalAddress du @graph.

Robots.txt verifie le 2026-07-18 : seuls /admin, /compte, /cdn-cgi sont
interdits ; la categorie emploi est autorisee. User-Agent navigateur requis.
"""

import json
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.scrapers.base_scraper import BaseScraper
from src.scrapers.reference_data import COMPETENCES_TECH, INDICATEURS_TECH
from src.scrapers.utils_scraping import (
    est_offre_tech,
    extraire_competences,
    extraire_json_ld_jobposting,
    extraire_salaire,
    nettoyer_html,
    nettoyer_texte,
)

# Le site bloque les User-Agent "robot" evidents : on se presente en navigateur.
NAVIGATEUR_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class ExpatDakarScraper(BaseScraper):
    """Recupere les offres Tech d'Expat-Dakar, avec leurs salaires quand dispo."""

    source = "expatdakar"
    url_depart = "https://www.expat-dakar.com/emploi-informatique"

    def __init__(self, limite=15):
        # robots.txt n'interdit pas la categorie emploi (verifie).
        super().__init__(respecter_robots=False)
        self.limite = limite
        self.session.headers.update({"User-Agent": NAVIGATEUR_UA})

    def parse(self):
        html = self.telecharger(self.url_depart)
        if not html:
            return []

        urls = self._urls_offres_tech(html)
        offres = []
        for url in urls[: self.limite]:
            page = self.telecharger(url)
            if not page:
                continue
            offre = self._parser_page(page, url)
            if offre:
                offres.append(offre)
        return offres

    def _urls_offres_tech(self, html):
        """Liste les URL d'annonces Tech de la page categorie."""
        soup = BeautifulSoup(html, "lxml")
        urls = []
        for a in soup.find_all("a", href=True):
            if "/annonce/" in a["href"]:
                urls.append(urljoin(self.url_depart, a["href"]))
        urls = list(dict.fromkeys(urls))  # dedoublonne en gardant l'ordre
        # La categorie est deja "informatique" mais des annonces hors sujet s'y
        # glissent (caissier, magasin...). On filtre sur le slug par securite.
        return [u for u in urls if est_offre_tech(u.replace("-", " "), INDICATEURS_TECH)]

    def _parser_page(self, html, url):
        """Extrait une offre : JSON-LD pour l'essentiel, span pour le salaire."""
        jp = extraire_json_ld_jobposting(html)
        if not jp:
            return None

        titre = nettoyer_html(jp.get("title"))
        if not titre:
            return None

        entreprise = self._nom_entreprise(jp)
        lieu = self._lieu(html)
        sal_min, sal_max = self._salaire(html)

        description = nettoyer_html(jp.get("description"))
        competences = extraire_competences(f"{titre} {description}", COMPETENCES_TECH)

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
        org = jp.get("hiringOrganization")
        if isinstance(org, dict):
            return nettoyer_texte(org.get("name")) or "Non precise"
        return nettoyer_texte(org) or "Non precise"

    @staticmethod
    def _salaire(html):
        """Le salaire est dans un span de prix (ex 'Entre 100 000 et 200 000')."""
        soup = BeautifulSoup(html, "lxml")
        el = soup.select_one(".listing-item__price")
        if not el:
            return (None, None)
        texte = el.get_text(strip=True)
        # "Non defini" ou vide -> pas de salaire.
        if not texte or "defin" in texte.lower():
            return (None, None)
        return extraire_salaire(texte)

    @staticmethod
    def _lieu(html):
        """La ville vient d'une PostalAddress du @graph (region, sinon localite)."""
        soup = BeautifulSoup(html, "lxml")
        for bloc in soup.find_all("script", type="application/ld+json"):
            try:
                donnees = json.loads(bloc.string or "")
            except (json.JSONDecodeError, TypeError):
                continue
            graph = donnees.get("@graph", []) if isinstance(donnees, dict) else []
            for node in graph:
                if isinstance(node, dict) and node.get("@type") == "PostalAddress":
                    ville = node.get("addressRegion") or node.get("addressLocality")
                    if ville:
                        return nettoyer_texte(ville)
        return "Dakar"
