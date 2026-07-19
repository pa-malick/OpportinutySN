"""
Scraper pour Senjob (https://senjob.com), categorie Informatique.

Senjob n'expose ni API ni JSON-LD : on lit donc directement le HTML de la page
liste. Bonne surprise : la liste contient deja le titre, la ville et la date de
chaque offre, ce qui evite de telecharger chaque annonce une par une (poli et
rapide, 1 a 2 requetes suffisent).

La categorie "Informatique, Telecoms, Reseaux" porte le numero 8, on l'utilise
pour ne recuperer que les offres Tech (le filtre reste imparfait, donc on
repasse un filtre de pertinence sur le titre). Le site n'affiche pas l'entreprise
ni le salaire dans la liste : on les laisse a "Non precise" / None.

Robots.txt verifie le 2026-07-18 : la page liste (/offres-d-emploi.php) est
autorisee (seuls /cvs/ et certains chemins candidats sont interdits). User-Agent
navigateur pour eviter tout filtrage.
"""

import re
from datetime import date
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.scrapers.base_scraper import BaseScraper
from src.scrapers.reference_data import COMPETENCES_TECH, INDICATEURS_TECH
from src.scrapers.utils_scraping import (
    est_offre_tech,
    extraire_competences,
    nettoyer_html,
    nettoyer_texte,
)

NAVIGATEUR_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Abreviations de mois en francais telles qu'affichees par Senjob.
MOIS_FR = {
    "jan": 1, "fev": 2, "mar": 3, "avr": 4, "mai": 5, "juin": 6,
    "juil": 7, "aou": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


class SenjobScraper(BaseScraper):
    """Recupere les offres Tech locales de Senjob (categorie Informatique)."""

    source = "senjob"
    url_depart = "https://senjob.com/sn/offres-d-emploi.php?Category=8"

    def __init__(self, pages=2):
        # robots autorise la page liste (verifie), on evite le re-check a chaque appel.
        super().__init__(respecter_robots=False)
        self.pages = pages
        self.session.headers.update({"User-Agent": NAVIGATEUR_UA})

    def parse(self):
        offres = []
        vus = set()
        for page in range(1, self.pages + 1):
            url = f"{self.url_depart}&page={page}"
            html = self.telecharger(url)
            if not html:
                continue
            for offre in self._parser_liste(html):
                # Dedoublonnage inter-pages sur l'URL.
                if offre["url"] in vus:
                    continue
                vus.add(offre["url"])
                offres.append(offre)
        return offres

    def _parser_liste(self, html):
        """Extrait les offres Tech d'une page liste."""
        soup = BeautifulSoup(html, "lxml")
        resultats = []
        for lien in soup.find_all("a", href=re.compile(r"/jobseekers/.+_e_\d+\.html")):
            tr = lien.find_parent("tr")
            if tr is None or "Publi" not in tr.get_text():
                # On ne garde que les vraies lignes d'offres (avec "Publie:").
                continue

            titre = nettoyer_html(lien.get_text())
            if not titre:
                continue
            # Filtre de pertinence Tech (la categorie laisse passer du non-IT).
            if not est_offre_tech(titre, INDICATEURS_TECH):
                continue

            resultats.append(self._construire_offre(titre, lien, tr))
        return resultats

    def _construire_offre(self, titre, lien, tr):
        cellules = tr.find_all("td")
        textes = [nettoyer_texte(td.get_text(" ", strip=True)) for td in cellules]

        # La ville est la cellule juste avant celle qui contient "Publie:".
        lieu = "Senegal"
        date_publication = None
        for i, txt in enumerate(textes):
            if txt.startswith("Publi"):
                if i > 0 and textes[i - 1]:
                    lieu = textes[i - 1]
                date_publication = self._parser_date(txt)
                break

        return {
            "titre": titre,
            "entreprise": "Non precise",  # non affiche par Senjob dans la liste
            "lieu": lieu,
            "pays": "Senegal",
            "categorie": None,  # devine plus tard dans l'ETL
            "competences": extraire_competences(titre, COMPETENCES_TECH),
            "salaire_min": None,  # non affiche
            "salaire_max": None,
            "devise": "XOF",
            "date_publication": date_publication,
            "source": self.source,
            "url": urljoin(self.url_depart, lien.get("href", "")),
        }

    @staticmethod
    def _parser_date(texte):
        """'Publie: 10 Juil.' -> date(2026, 7, 10). None si illisible."""
        m = re.search(r"(\d{1,2})\s+([A-Za-zÀ-ÿ]+)", texte)
        if not m:
            return None
        jour = int(m.group(1))
        # On enleve les accents grossierement pour matcher la table des mois.
        mois_txt = (
            m.group(2).lower()
            .replace("é", "e").replace("è", "e").replace("û", "u").replace("ô", "o")
        )
        mois = None
        for prefixe, num in MOIS_FR.items():
            if mois_txt.startswith(prefixe):
                mois = num
                break
        if mois is None:
            return None
        try:
            # Senjob n'indique pas l'annee : on prend l'annee courante.
            return date(date.today().year, mois, jour)
        except ValueError:
            return None
