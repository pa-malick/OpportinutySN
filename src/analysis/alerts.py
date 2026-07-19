"""
Construction des alertes.

Une alerte, c'est une information qui merite l'attention d'un decideur. On en
genere de trois types :

    1. Anomalie de salaire : une offre au salaire tres inhabituel.
    2. Opportunite Data/Tech : une nouvelle offre dans les metiers qui nous
       interessent en priorite.
    3. Signal marche : une competence particulierement demandee en ce moment.

Chaque alerte est un petit dictionnaire uniforme (type, niveau, message), ce
qui rend leur affichage et leur envoi par email tres simples.
"""

from src.analysis.trend_analysis import competences_les_plus_demandees
from src.logger import get_logger

logger = get_logger(__name__)

# Categories que Papa Malick veut suivre en priorite (coeur de sa veille).
CATEGORIES_PRIORITAIRES = ["Data Science", "Data Engineering", "DevOps / Cloud"]


def _alerte(type_, niveau, message):
    """Fabrique une alerte au format standard."""
    return {"type": type_, "niveau": niveau, "message": message}


def alertes_anomalies(anomalies):
    """Cree une alerte par offre au salaire anormal."""
    alertes = []
    for _, offre in anomalies.iterrows():
        salaire = offre.get("salaire_ref")
        salaire_txt = f"{int(salaire):,} FCFA".replace(",", " ") if salaire else "inconnu"
        message = (
            f"Salaire inhabituel pour '{offre['titre']}' chez {offre['entreprise']} "
            f"({offre['categorie']}) : {salaire_txt}."
        )
        alertes.append(_alerte("anomalie", "haute", message))
    return alertes


def alertes_opportunites(df):
    """
    Signale les offres dans les categories prioritaires.

    On se limite aux offres collectees recemment (celles du dernier passage)
    pour ne pas re-alerter sur les memes chaque jour.
    """
    if df.empty:
        return []

    recentes = df.sort_values("date_collecte", ascending=False).head(20)
    interessantes = recentes[recentes["categorie"].isin(CATEGORIES_PRIORITAIRES)]

    alertes = []
    for _, offre in interessantes.iterrows():
        message = (
            f"Nouvelle offre {offre['categorie']} : '{offre['titre']}' "
            f"chez {offre['entreprise']} ({offre['lieu']})."
        )
        alertes.append(_alerte("opportunite", "moyenne", message))
    return alertes


def alertes_tendances(df, seuil=5):
    """
    Signale les competences fortement demandees.

    Si une competence apparait dans plus de 'seuil' offres, on la remonte
    comme un signal marche a suivre.
    """
    top = competences_les_plus_demandees(df, top=5)
    alertes = []
    for _, ligne in top.iterrows():
        if ligne["occurrences"] >= seuil:
            message = (
                f"Competence tres demandee : {ligne['competence']} "
                f"({ligne['occurrences']} offres)."
            )
            alertes.append(_alerte("tendance", "basse", message))
    return alertes


def generer_alertes(df, anomalies):
    """
    Rassemble toutes les alertes en une seule liste, triee par importance.

    Ordre de priorite : haute -> moyenne -> basse.
    """
    toutes = []
    toutes.extend(alertes_anomalies(anomalies))
    toutes.extend(alertes_opportunites(df))
    toutes.extend(alertes_tendances(df))

    ordre = {"haute": 0, "moyenne": 1, "basse": 2}
    toutes.sort(key=lambda a: ordre.get(a["niveau"], 3))

    logger.info("%s alertes generees.", len(toutes))
    return toutes
