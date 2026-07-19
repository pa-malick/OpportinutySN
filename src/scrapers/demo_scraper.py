"""
Scraper de demonstration.

Pourquoi ce fichier ? Les sites d'emploi changent souvent leur HTML, bloquent
les robots, ou demandent un login. Pour que le projet soit toujours executable
(par un recruteur, un correcteur, ou toi en entretien), on genere ici un jeu
de donnees realiste du marche Tech senegalais.

Ce n'est PAS de la triche : c'est une source parmi d'autres, qui permet de
tester toute la pipeline (ETL, analyse, alertes, dashboard) sans dependre du
reseau. Les vrais scrapers HTML sont dans les autres fichiers du dossier.

On introduit volontairement quelques offres au salaire anormal, pour que la
detection d'anomalies ait de la matiere a se mettre sous la dent.
"""

import random
from datetime import datetime, timedelta

from src.scrapers.base_scraper import BaseScraper
from src.scrapers.reference_data import CATEGORIES, COMPETENCES_TECH, VILLES_SENEGAL

# Quelques entreprises credibles (mix local et international present au Senegal).
ENTREPRISES = [
    "Sonatel", "Wave", "Expresso", "Free Senegal", "L3M Holding",
    "Atos Senegal", "PayDunya", "InTouch", "Baamtu", "GAINDE 2000",
    "Ecobank", "BICIS", "Orange Digital Center", "SudPay", "Solid",
]

# Modeles de titres par categorie, pour generer des intitules coherents.
TITRES_PAR_CATEGORIE = {
    "Data Science": ["Data Scientist", "Analyste Data", "ML Engineer"],
    "Data Engineering": ["Data Engineer", "Ingenieur Data", "Ingenieur ETL"],
    "Developpement Logiciel": ["Developpeur Backend", "Developpeur Full Stack", "Ingenieur Logiciel"],
    "DevOps / Cloud": ["Ingenieur DevOps", "Administrateur Cloud", "SRE"],
    "Business Intelligence": ["Analyste BI", "Consultant Power BI", "Data Analyst"],
    "Finance / Comptabilite": ["Analyste Financier", "Controleur de Gestion", "Comptable"],
}

# Fourchette de salaire mensuel realiste (FCFA) par categorie : (mini, maxi).
SALAIRE_PAR_CATEGORIE = {
    "Data Science": (600_000, 1_500_000),
    "Data Engineering": (700_000, 1_600_000),
    "Developpement Logiciel": (500_000, 1_400_000),
    "DevOps / Cloud": (700_000, 1_700_000),
    "Business Intelligence": (450_000, 1_200_000),
    "Finance / Comptabilite": (400_000, 1_100_000),
}


class DemoScraper(BaseScraper):
    """Genere un jeu d'offres realiste, sans acces reseau."""

    source = "demo"
    url_depart = ""

    def __init__(self, nombre=80, graine=None):
        # On n'a pas besoin de robots.txt ici, donc on desactive la verif.
        super().__init__(respecter_robots=False)
        self.nombre = nombre
        # Une graine fixe rend le jeu reproductible (pratique pour les tests).
        self.random = random.Random(graine)

    def parse(self):
        offres = []
        aujourd_hui = datetime.now()

        for _ in range(self.nombre):
            categorie = self.random.choice(CATEGORIES)
            titre = self.random.choice(TITRES_PAR_CATEGORIE[categorie])
            entreprise = self.random.choice(ENTREPRISES)
            ville = self.random.choice(VILLES_SENEGAL)

            sal_min, sal_max = self._tirer_salaire(categorie)

            # Date de publication sur les 30 derniers jours.
            jours = self.random.randint(0, 30)
            date_pub = (aujourd_hui - timedelta(days=jours)).strftime("%Y-%m-%d")

            # On tire 2 a 5 competences au hasard pour cette offre.
            competences = self.random.sample(COMPETENCES_TECH, self.random.randint(2, 5))

            offres.append({
                "titre": titre,
                "entreprise": entreprise,
                "lieu": ville,
                "pays": "Senegal",
                "categorie": categorie,
                "competences": competences,
                "salaire_min": sal_min,
                "salaire_max": sal_max,
                "devise": "XOF",
                "date_publication": date_pub,
                "source": self.source,
                "url": f"https://demo.local/offre/{self.random.randint(1000, 9999)}",
            })
        return offres

    def _tirer_salaire(self, categorie):
        """
        Tire un salaire dans la fourchette de la categorie.

        Dans 5% des cas, on genere volontairement une valeur aberrante
        (trop haute ou trop basse) pour tester la detection d'anomalies.
        """
        bas, haut = SALAIRE_PAR_CATEGORIE[categorie]
        if self.random.random() < 0.05:
            # Anomalie : soit ridiculement bas, soit exagerement haut.
            if self.random.random() < 0.5:
                base = self.random.randint(50_000, 150_000)
            else:
                base = self.random.randint(3_000_000, 5_000_000)
        else:
            base = self.random.randint(bas, haut)

        # On cree une petite fourchette autour de la valeur de base.
        largeur = int(base * 0.15)
        return (base, base + largeur)
