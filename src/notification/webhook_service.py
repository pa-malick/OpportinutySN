"""
Envoi des alertes vers Make (ou Zapier) via un webhook.

C'est le pont entre notre pipeline Python et le monde no-code. On envoie un
simple JSON a une URL de webhook Make. Ensuite, dans Make, on branche ce qu'on
veut sans ecrire de code : envoyer un message Slack, ajouter une ligne dans un
Google Sheet, envoyer un WhatsApp, un email...

Architecture :
    Python (scraping + analyse)  ->  Webhook  ->  Make/Zapier  ->  Slack / Sheets / WhatsApp

C'est exactement le genre de chaine hybride "code + no-code" qu'on retrouve en
entreprise : le code fait le travail lourd, l'outil no-code gere la distribution.

Deux modes, comme pour l'email :
    - WEBHOOK_ENABLED=true  : on poste vraiment vers Make.
    - WEBHOOK_ENABLED=false : mode simulation, on loggue le payload sans l'envoyer.
"""

from datetime import datetime

import requests

from src.config import (
    MAKE_WEBHOOK_URL,
    PROJET_NOM,
    REQUEST_TIMEOUT,
    WEBHOOK_ENABLED,
)
from src.logger import get_logger

logger = get_logger(__name__)


def construire_payload(resume, alertes):
    """
    Prepare le JSON envoye a Make.

    On garde une structure simple et plate, plus facile a manipuler dans les
    modules Make (pas d'imbrication compliquee).
    """
    return {
        "projet": PROJET_NOM,
        "genere_le": datetime.now().isoformat(timespec="seconds"),
        "total_offres": resume.get("total_offres", 0),
        "salaire_median": resume.get("salaire_median"),
        "competence_top": resume.get("competence_top"),
        "nombre_alertes": len(alertes),
        # On limite a 10 alertes pour garder le message digeste dans Slack/WhatsApp.
        "alertes": alertes[:10],
    }


def envoyer_webhook(resume, alertes):
    """
    Envoie (ou simule) le payload vers le webhook Make.

    Retourne True si l'envoi a reussi, False sinon. On n'attrape pas l'erreur
    pour la faire remonter : la pipeline continue meme si Make est injoignable.
    """
    payload = construire_payload(resume, alertes)

    if not WEBHOOK_ENABLED:
        logger.info("WEBHOOK_ENABLED=false : envoi Make simule (%s alertes).", len(alertes))
        return False

    if not MAKE_WEBHOOK_URL:
        logger.warning("MAKE_WEBHOOK_URL vide, envoi vers Make annule.")
        return False

    try:
        reponse = requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=REQUEST_TIMEOUT)
        reponse.raise_for_status()
        logger.info("Payload envoye a Make (statut %s).", reponse.status_code)
        return True
    except requests.RequestException as e:
        logger.error("Echec de l'envoi vers Make : %s", e)
        return False
