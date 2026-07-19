"""
Service d'envoi d'emails.

On construit un rapport HTML (a partir du template Jinja2) puis on l'envoie par
SMTP. Deux modes :

    - EMAIL_ENABLED=true  : envoi reel via le serveur SMTP configure.
    - EMAIL_ENABLED=false : mode simulation. On n'envoie rien, on sauvegarde le
      HTML dans data/processed pour pouvoir le verifier a l'oeil. Parfait pour
      developper sans spammer sa boite mail.

Le rapport HTML sauvegarde sert aussi de livrable "exemple de rapport genere".
"""

import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.config import (
    EMAIL_ENABLED,
    EMAIL_FROM,
    EMAIL_TO,
    PROCESSED_DIR,
    PROJET_AUTEUR,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USER,
)
from src.logger import get_logger

logger = get_logger(__name__)

# Dossier ou se trouve le template HTML.
_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def construire_rapport_html(resume, alertes, salaires):
    """
    Remplit le template Jinja2 avec les donnees et retourne le HTML final.

    - resume   : dictionnaire de chiffres cles (voir trend_analysis.resume_marche)
    - alertes  : liste d'alertes (voir alerts.generer_alertes)
    - salaires : DataFrame des salaires moyens par categorie
    """
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=True,
    )
    template = env.get_template("rapport_html.j2")

    html = template.render(
        date_rapport=datetime.now().strftime("%d/%m/%Y a %H:%M"),
        resume=resume,
        alertes=alertes,
        # to_dict("records") transforme le DataFrame en liste de dicts, plus
        # facile a parcourir dans le template.
        salaires=salaires.to_dict("records"),
        auteur=PROJET_AUTEUR,
    )
    return html


def _sauvegarder_html(html):
    """Ecrit le rapport HTML sur disque (livrable + verification en mode dev)."""
    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
    chemin = PROCESSED_DIR / f"rapport_{horodatage}.html"
    chemin.write_text(html, encoding="utf-8")
    logger.info("Rapport HTML sauvegarde : %s", chemin)
    return chemin


def envoyer_rapport(resume, alertes, salaires, sujet=None):
    """
    Construit et envoie (ou simule) le rapport par email.

    Retourne le chemin du HTML sauvegarde. On sauvegarde toujours une copie,
    qu'on envoie ou non.
    """
    html = construire_rapport_html(resume, alertes, salaires)
    chemin = _sauvegarder_html(html)

    if not EMAIL_ENABLED:
        logger.info(
            "EMAIL_ENABLED=false : envoi simule. Ouvre %s pour voir le rapport.",
            chemin,
        )
        return chemin

    if not (SMTP_USER and SMTP_PASSWORD and EMAIL_TO):
        logger.warning("Config SMTP incomplete, envoi annule (le HTML reste sauvegarde).")
        return chemin

    sujet = sujet or f"Veille emploi Tech, {len(alertes)} alertes"
    message = MIMEMultipart("alternative")
    message["Subject"] = sujet
    message["From"] = EMAIL_FROM
    message["To"] = EMAIL_TO
    message.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as serveur:
            serveur.starttls()  # on chiffre la connexion
            serveur.login(SMTP_USER, SMTP_PASSWORD)
            serveur.sendmail(EMAIL_FROM, EMAIL_TO.split(","), message.as_string())
        logger.info("Email envoye a %s", EMAIL_TO)
    except Exception as e:  # noqa: BLE001
        logger.error("Echec de l'envoi de l'email : %s", e)

    return chemin
