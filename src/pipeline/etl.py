"""
Pipeline ETL : Extract, Transform, Load.

C'est le chef d'orchestre du traitement des donnees. Il prend les offres brutes
sorties des scrapers et les amene jusqu'a la base, propres et validees :

    1. Extract  : deja fait par les scrapers, on recoit une liste de dicts.
    2. Transform: nettoyage, deviner la categorie, dedoublonnage, validation.
    3. Load     : ecriture en base + sauvegarde des CSV (raw et processed).

On garde une copie CSV a chaque etape. C'est une bonne pratique de data
engineering : si un bug apparait plus loin, on peut revenir a la donnee brute
et rejouer le traitement sans re-scraper.
"""

from datetime import datetime

import pandas as pd

from src.config import PROCESSED_DIR, RAW_DIR
from src.logger import get_logger
from src.pipeline.storage import sauvegarder_offres
from src.pipeline.validation import valider_offres

logger = get_logger(__name__)

# Mots-cles pour deviner la categorie a partir du titre. Simple et efficace.
MOTS_CLES_CATEGORIE = {
    "Data Science": ["data scientist", "machine learning", "ml engineer", "ia", "intelligence artificielle"],
    "Data Engineering": ["data engineer", "ingenieur data", "etl", "pipeline", "big data"],
    "Developpement Logiciel": ["developpeur", "developer", "software", "backend", "frontend", "full stack"],
    "DevOps / Cloud": ["devops", "cloud", "sre", "kubernetes", "infrastructure"],
    "Business Intelligence": ["bi", "power bi", "tableau", "data analyst", "analyste data", "reporting"],
    "Finance / Comptabilite": ["financier", "comptable", "controleur", "audit", "gestion"],
}


def deviner_categorie(titre, competences):
    """
    Devine la categorie d'une offre a partir de son titre et ses competences.

    On cherche des mots-cles dans le titre en priorite. Utile quand un scraper
    ne fournit pas la categorie (cas d'EmploiSenegal par exemple).
    """
    texte = (titre or "").lower() + " " + " ".join(competences or []).lower()
    for categorie, mots in MOTS_CLES_CATEGORIE.items():
        if any(mot in texte for mot in mots):
            return categorie
    return "Autre"


def transformer(offres_brutes):
    """
    Etape Transform : nettoie et enrichit les offres.

    - complete la categorie manquante,
    - retire les doublons dans le lot courant (meme titre + entreprise + source).
    """
    vues = set()
    propres = []

    for offre in offres_brutes:
        # On devine la categorie si le scraper ne l'a pas fournie.
        if not offre.get("categorie"):
            offre["categorie"] = deviner_categorie(
                offre.get("titre"), offre.get("competences")
            )

        # Cle de dedoublonnage a l'interieur du lot.
        cle = (
            str(offre.get("titre", "")).lower().strip(),
            str(offre.get("entreprise", "")).lower().strip(),
            offre.get("source"),
        )
        if cle in vues:
            continue
        vues.add(cle)
        propres.append(offre)

    logger.info(
        "Transform : %s offres en entree, %s apres dedoublonnage.",
        len(offres_brutes), len(propres),
    )
    return propres


def _sauver_csv(offres, dossier, prefixe):
    """Sauvegarde une liste d'offres en CSV horodate (pour la tracabilite)."""
    if not offres:
        return None
    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
    chemin = dossier / f"{prefixe}_{horodatage}.csv"
    pd.DataFrame(offres).to_csv(chemin, index=False, encoding="utf-8")
    logger.info("CSV ecrit : %s", chemin)
    return chemin


def run_etl(offres_brutes):
    """
    Lance toute la chaine ETL sur une liste d'offres brutes.

    Retourne un petit resume (dictionnaire) pratique pour le rapport final.
    """
    logger.info("=== Debut ETL (%s offres brutes) ===", len(offres_brutes))

    # Load "raw" : on garde une trace des donnees telles que recues.
    _sauver_csv(offres_brutes, RAW_DIR, "offres_brutes")

    # Transform
    offres_propres = transformer(offres_brutes)

    # Validation Pydantic
    valides, rejetees = valider_offres(offres_propres)
    if rejetees:
        logger.warning("%s offres rejetees a la validation.", len(rejetees))

    # Load "processed" : la donnee propre, prete a l'analyse.
    _sauver_csv(
        [v.model_dump() for v in valides], PROCESSED_DIR, "offres_propres"
    )

    # Load base de donnees
    nouvelles, majs = sauvegarder_offres(valides)

    resume = {
        "brutes": len(offres_brutes),
        "apres_dedoublonnage": len(offres_propres),
        "valides": len(valides),
        "rejetees": len(rejetees),
        "nouvelles_en_base": nouvelles,
        "mises_a_jour": majs,
    }
    logger.info("=== Fin ETL : %s ===", resume)
    return resume
