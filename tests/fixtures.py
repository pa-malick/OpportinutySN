"""
Donnees de test partagees entre les fichiers de test.

On centralise ici quelques offres d'exemple pour ne pas les recopier dans
chaque test. On y met volontairement des cas "sales" (titre vide, salaire
inverse) pour verifier que la validation fait bien son travail.
"""


def offres_exemple():
    """Retourne une petite liste d'offres brutes, comme en sortie d'un scraper."""
    return [
        {
            "titre": "Data Scientist",
            "entreprise": "Sonatel",
            "lieu": "Dakar",
            "pays": "Senegal",
            "categorie": None,
            "competences": ["Python", "SQL", "Machine Learning"],
            "salaire_min": 800_000,
            "salaire_max": 1_200_000,
            "devise": "XOF",
            "date_publication": "2026-06-01",
            "source": "demo",
            "url": "https://demo.local/offre/1",
        },
        {
            "titre": "Data Engineer",
            "entreprise": "Wave",
            "lieu": "Dakar",
            "pays": "Senegal",
            "categorie": None,
            "competences": ["Python", "Airflow", "Docker"],
            "salaire_min": 900_000,
            "salaire_max": 1_400_000,
            "devise": "XOF",
            "date_publication": "2026-06-02",
            "source": "demo",
            "url": "https://demo.local/offre/2",
        },
        # Doublon exact de la premiere offre (meme titre + entreprise + source).
        {
            "titre": "Data Scientist",
            "entreprise": "Sonatel",
            "lieu": "Dakar",
            "pays": "Senegal",
            "categorie": None,
            "competences": ["Python"],
            "salaire_min": 800_000,
            "salaire_max": 1_200_000,
            "devise": "XOF",
            "date_publication": "2026-06-01",
            "source": "demo",
            "url": "https://demo.local/offre/1",
        },
    ]


def offre_invalide():
    """Une offre avec un titre vide : elle doit etre rejetee a la validation."""
    return {
        "titre": "   ",
        "entreprise": "Inconnue",
        "source": "demo",
        "url": "https://demo.local/offre/x",
    }
