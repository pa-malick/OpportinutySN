"""
Analyse de tendances du marche.

Ici on calcule les agregats qui repondent aux vraies questions business :
    - Quels metiers recrutent le plus ?
    - Quelles competences sont les plus demandees ?
    - Qui recrute (top entreprises) ?
    - Quels sont les salaires moyens par categorie ?
    - Comment le volume d'offres evolue dans le temps ?

Ces fonctions renvoient des DataFrames simples, directement affichables dans le
dashboard ou le rapport email.
"""

from collections import Counter

import pandas as pd

from src.logger import get_logger

logger = get_logger(__name__)


def salaire_moyen_par_categorie(df):
    """Salaire moyen (moyenne de la fourchette) par categorie, trie decroissant."""
    if df.empty:
        return pd.DataFrame(columns=["categorie", "salaire_moyen", "nombre_offres"])

    df = df.copy()
    df["salaire_ref"] = df[["salaire_min", "salaire_max"]].mean(axis=1)
    resultat = (
        df.groupby("categorie")
        .agg(salaire_moyen=("salaire_ref", "mean"), nombre_offres=("id", "count"))
        .reset_index()
        .sort_values("salaire_moyen", ascending=False)
    )
    resultat["salaire_moyen"] = resultat["salaire_moyen"].round(0)
    return resultat


def competences_les_plus_demandees(df, top=15):
    """
    Compte les competences les plus citees dans les offres.

    La colonne competences contient des listes, donc on les met a plat avant
    de compter avec un Counter. Retourne les 'top' competences.
    """
    if df.empty:
        return pd.DataFrame(columns=["competence", "occurrences"])

    compteur = Counter()
    for liste in df["competences"]:
        if isinstance(liste, list):
            compteur.update(liste)

    donnees = compteur.most_common(top)
    return pd.DataFrame(donnees, columns=["competence", "occurrences"])


def top_entreprises(df, top=10):
    """Classe les entreprises par nombre d'offres publiees."""
    if df.empty:
        return pd.DataFrame(columns=["entreprise", "nombre_offres"])

    resultat = (
        df["entreprise"].value_counts().head(top).reset_index()
    )
    resultat.columns = ["entreprise", "nombre_offres"]
    return resultat


def offres_par_ville(df):
    """Repartition des offres par ville."""
    if df.empty:
        return pd.DataFrame(columns=["lieu", "nombre_offres"])
    resultat = df["lieu"].value_counts().reset_index()
    resultat.columns = ["lieu", "nombre_offres"]
    return resultat


def volume_dans_le_temps(df):
    """
    Nombre d'offres par jour de publication.

    Permet de tracer une courbe d'activite du marche. On ignore les offres
    sans date de publication.
    """
    if df.empty or "date_publication" not in df:
        return pd.DataFrame(columns=["date_publication", "nombre_offres"])

    valides = df.dropna(subset=["date_publication"])
    if valides.empty:
        return pd.DataFrame(columns=["date_publication", "nombre_offres"])

    resultat = (
        valides.groupby("date_publication").size().reset_index(name="nombre_offres")
        .sort_values("date_publication")
    )
    return resultat


def resume_marche(df):
    """
    Construit un petit resume chiffre du marche.

    Pratique pour l'entete du rapport email et les "cartes" du dashboard.
    """
    if df.empty:
        return {
            "total_offres": 0,
            "nombre_entreprises": 0,
            "nombre_categories": 0,
            "salaire_median": None,
            "competence_top": None,
        }

    df = df.copy()
    df["salaire_ref"] = df[["salaire_min", "salaire_max"]].mean(axis=1)
    comp = competences_les_plus_demandees(df, top=1)

    return {
        "total_offres": len(df),
        "nombre_entreprises": df["entreprise"].nunique(),
        "nombre_categories": df["categorie"].nunique(),
        "salaire_median": round(df["salaire_ref"].median(), 0) if df["salaire_ref"].notna().any() else None,
        "competence_top": comp.iloc[0]["competence"] if not comp.empty else None,
    }
