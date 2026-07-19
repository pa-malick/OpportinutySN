"""
Tests de la couche scraping.

On teste surtout le scraper de demonstration (reproductible, sans reseau) et
les fonctions utilitaires de parsing. On ne teste pas le vrai scraper HTTP ici,
car il dependrait d'internet, ce qui rendrait les tests fragiles.
"""

from src.scrapers.demo_scraper import DemoScraper
from src.scrapers.utils_scraping import (
    extraire_competences,
    extraire_salaire,
    nettoyer_texte,
)


def test_demo_scraper_nombre_offres():
    """Le scraper doit generer exactement le nombre d'offres demande."""
    offres = DemoScraper(nombre=25, graine=1).run()
    assert len(offres) == 25


def test_demo_scraper_structure():
    """Chaque offre doit contenir les champs attendus."""
    offres = DemoScraper(nombre=5, graine=1).run()
    champs_requis = {"titre", "entreprise", "lieu", "categorie", "competences",
                     "salaire_min", "salaire_max", "source", "url"}
    for offre in offres:
        assert champs_requis.issubset(offre.keys())
        assert offre["salaire_min"] <= offre["salaire_max"]


def test_demo_scraper_reproductible():
    """Avec la meme graine, on doit obtenir exactement le meme jeu de donnees."""
    a = DemoScraper(nombre=10, graine=99).run()
    b = DemoScraper(nombre=10, graine=99).run()
    assert a == b


def test_nettoyer_texte():
    """Les espaces multiples et retours a la ligne doivent disparaitre."""
    assert nettoyer_texte("  Data   \n Scientist  ") == "Data Scientist"
    assert nettoyer_texte(None) == ""


def test_extraire_salaire():
    """Verifie l'extraction de fourchettes de salaire depuis du texte libre."""
    assert extraire_salaire("500 000 - 800 000 FCFA") == (500000, 800000)
    assert extraire_salaire("Salaire : 1 200 000 CFA") == (1200000, 1200000)
    assert extraire_salaire("A negocier") == (None, None)


def test_extraire_competences():
    """La detection de competences doit trouver les bons mots-cles."""
    texte = "Nous cherchons un profil Python avec de l'experience Docker et SQL."
    trouvees = extraire_competences(texte, ["Python", "Docker", "SQL", "Java"])
    assert set(trouvees) == {"Python", "Docker", "SQL"}
