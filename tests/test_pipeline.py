"""
Tests de la couche pipeline (validation + transformation ETL).

On verifie que la validation attrape bien les mauvaises donnees et que la
transformation dedoublonne et devine correctement les categories.
"""

from src.pipeline.etl import deviner_categorie, transformer
from src.pipeline.validation import OffreEmploi, valider_offres
from tests.fixtures import offre_invalide, offres_exemple


def test_validation_accepte_offre_correcte():
    """Une offre bien formee doit passer la validation sans probleme."""
    valides, rejetees = valider_offres([offres_exemple()[0]])
    assert len(valides) == 1
    assert len(rejetees) == 0
    assert valides[0].titre == "Data Scientist"


def test_validation_rejette_titre_vide():
    """Une offre au titre vide doit etre rejetee proprement."""
    valides, rejetees = valider_offres([offre_invalide()])
    assert len(valides) == 0
    assert len(rejetees) == 1
    assert "titre" in rejetees[0]["raison"].lower()


def test_validation_corrige_salaire_inverse():
    """Si min > max, la validation doit remettre les valeurs dans l'ordre."""
    offre = OffreEmploi(
        titre="Test", source="demo", url="http://x",
        salaire_min=1_000_000, salaire_max=500_000,
    )
    assert offre.salaire_min == 500_000
    assert offre.salaire_max == 1_000_000


def test_identifiant_stable():
    """Deux offres identiques (titre + entreprise + source) ont le meme id."""
    o1 = OffreEmploi(titre="Data Scientist", entreprise="Sonatel", source="demo", url="http://a")
    o2 = OffreEmploi(titre="Data Scientist", entreprise="Sonatel", source="demo", url="http://b")
    assert o1.identifiant() == o2.identifiant()


def test_deviner_categorie():
    """La categorie doit etre devinee a partir du titre."""
    assert deviner_categorie("Data Scientist Senior", []) == "Data Science"
    assert deviner_categorie("Ingenieur DevOps", []) == "DevOps / Cloud"
    assert deviner_categorie("Poste mysterieux", []) == "Autre"


def test_transformer_dedoublonne():
    """La transformation doit retirer le doublon present dans les fixtures."""
    brutes = offres_exemple()  # 3 offres dont 1 doublon
    propres = transformer(brutes)
    assert len(propres) == 2  # le doublon a saute
    # La categorie a bien ete devinee (elle etait None au depart).
    assert all(o["categorie"] is not None for o in propres)
