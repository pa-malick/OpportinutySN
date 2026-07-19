"""
Detection d'anomalies sur les salaires.

Objectif : reperer les offres dont le salaire sort de l'ordinaire (soit une
vraie opportunite, soit une erreur de saisie). On propose deux methodes
classiques et complementaires :

    - Le Z-score : mesure de combien d'ecarts-types une valeur s'eloigne de la
      moyenne. Rapide, mais sensible aux valeurs extremes.
    - L'IQR (ecart interquartile) : basee sur les quartiles, plus robuste quand
      la distribution n'est pas symetrique. C'est la methode du "boxplot".

On applique la detection par categorie de metier, car un salaire "normal" pour
un Data Engineer n'est pas le meme que pour un comptable debutant.
"""

import numpy as np
import pandas as pd

from src.config import ZSCORE_THRESHOLD
from src.logger import get_logger

logger = get_logger(__name__)


def _salaire_reference(df):
    """
    Ajoute une colonne 'salaire_ref' = moyenne de la fourchette.

    On travaille sur cette valeur unique plutot que sur min/max separement,
    c'est plus simple a analyser.
    """
    df = df.copy()
    df["salaire_ref"] = df[["salaire_min", "salaire_max"]].mean(axis=1)
    return df


def detecter_zscore(df, seuil=ZSCORE_THRESHOLD):
    """
    Detection par Z-score, calcule categorie par categorie.

    Une offre est anormale si |z| > seuil (2.5 par defaut, soit environ les
    1% de valeurs les plus extremes). Retourne le DataFrame avec deux colonnes
    ajoutees : 'zscore' et 'anomalie_zscore'.
    """
    df = _salaire_reference(df)
    df["zscore"] = np.nan
    df["anomalie_zscore"] = False

    for categorie, groupe in df.groupby("categorie"):
        salaires = groupe["salaire_ref"].dropna()
        if len(salaires) < 3 or salaires.std(ddof=0) == 0:
            # Pas assez de donnees pour juger, on passe.
            continue
        z = (groupe["salaire_ref"] - salaires.mean()) / salaires.std(ddof=0)
        df.loc[groupe.index, "zscore"] = z
        df.loc[groupe.index, "anomalie_zscore"] = z.abs() > seuil

    nb = int(df["anomalie_zscore"].sum())
    logger.info("Z-score : %s anomalies detectees (seuil=%s).", nb, seuil)
    return df


def detecter_iqr(df):
    """
    Detection par IQR (methode du boxplot), categorie par categorie.

    On considere anormale toute valeur en dehors de
    [Q1 - 1.5*IQR ; Q3 + 1.5*IQR]. Ajoute la colonne 'anomalie_iqr'.
    """
    df = _salaire_reference(df)
    df["anomalie_iqr"] = False

    for categorie, groupe in df.groupby("categorie"):
        salaires = groupe["salaire_ref"].dropna()
        if len(salaires) < 4:
            continue
        q1 = salaires.quantile(0.25)
        q3 = salaires.quantile(0.75)
        iqr = q3 - q1
        borne_basse = q1 - 1.5 * iqr
        borne_haute = q3 + 1.5 * iqr
        masque = (groupe["salaire_ref"] < borne_basse) | (groupe["salaire_ref"] > borne_haute)
        df.loc[groupe.index, "anomalie_iqr"] = masque

    nb = int(df["anomalie_iqr"].sum())
    logger.info("IQR : %s anomalies detectees.", nb)
    return df


def detecter_anomalies(df):
    """
    Combine les deux methodes.

    Une offre est signalee comme anomalie si au moins une des deux methodes la
    detecte. On croise les deux pour limiter les faux negatifs. Retourne le
    DataFrame complet plus le sous-ensemble des anomalies.
    """
    if df.empty:
        return df, df

    df = detecter_zscore(df)
    df = detecter_iqr(df)
    df["anomalie"] = df["anomalie_zscore"] | df["anomalie_iqr"]

    anomalies = df[df["anomalie"]].copy()
    logger.info("Total : %s offres marquees comme anomalies.", len(anomalies))
    return df, anomalies
