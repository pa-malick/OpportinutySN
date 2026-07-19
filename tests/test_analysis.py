"""
Tests de la couche analyse (anomalies + tendances).

On fabrique un petit DataFrame maison : plein de salaires "normaux" et une
valeur clairement aberrante, puis on verifie que la detection la repere.
"""

import pandas as pd

from src.analysis.anomaly_detection import detecter_anomalies
from src.analysis.trend_analysis import (
    competences_les_plus_demandees,
    salaire_moyen_par_categorie,
)


def _dataframe_test():
    """Construit un DataFrame avec une anomalie evidente en derniere ligne."""
    lignes = []
    # 10 offres Data Science autour de 1 000 000 FCFA (normales).
    for i in range(10):
        lignes.append({
            "id": f"n{i}",
            "titre": "Data Scientist",
            "entreprise": "Sonatel",
            "lieu": "Dakar",
            "categorie": "Data Science",
            "competences": ["Python", "SQL"],
            "salaire_min": 950_000,
            "salaire_max": 1_050_000,
        })
    # Une offre a 5 000 000 : clairement hors norme.
    lignes.append({
        "id": "anomalie",
        "titre": "Data Scientist",
        "entreprise": "MysteryCorp",
        "lieu": "Dakar",
        "categorie": "Data Science",
        "competences": ["Python"],
        "salaire_min": 5_000_000,
        "salaire_max": 5_200_000,
    })
    return pd.DataFrame(lignes)


def test_detection_anomalie():
    """L'offre a 5 millions doit etre reperee comme anomalie."""
    df = _dataframe_test()
    _, anomalies = detecter_anomalies(df)
    assert "anomalie" in anomalies["id"].values
    # Les offres normales ne doivent pas etre signalees.
    assert len(anomalies) == 1


def test_salaire_moyen_par_categorie():
    """Le calcul du salaire moyen par categorie doit renvoyer une ligne par metier."""
    df = _dataframe_test()
    resultat = salaire_moyen_par_categorie(df)
    assert list(resultat["categorie"]) == ["Data Science"]
    assert resultat.iloc[0]["nombre_offres"] == 11


def test_competences_les_plus_demandees():
    """Python doit ressortir comme la competence la plus citee."""
    df = _dataframe_test()
    top = competences_les_plus_demandees(df, top=5)
    assert top.iloc[0]["competence"] == "Python"


def test_dataframe_vide():
    """Les fonctions doivent gerer un DataFrame vide sans planter."""
    vide = pd.DataFrame()
    df, anomalies = detecter_anomalies(vide)
    assert anomalies.empty
