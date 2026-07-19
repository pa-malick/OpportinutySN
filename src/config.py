"""
Configuration centrale du projet.

L'idee : on regroupe ici tous les parametres (chemins, base de donnees,
scraping, email...). Comme ca on ne se retrouve pas avec des valeurs en dur
un peu partout dans le code. On lit les secrets depuis le fichier .env.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# On charge les variables du fichier .env (s'il existe) dans l'environnement.
load_dotenv()

# --- Chemins du projet ---
# BASE_DIR pointe vers la racine du projet, peu importe d'ou on lance le script.
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DB_DIR = DATA_DIR / "db"
LOGS_DIR = BASE_DIR / "logs"

# On s'assure que les dossiers existent (utile au premier lancement).
for _dossier in (RAW_DIR, PROCESSED_DIR, DB_DIR, LOGS_DIR):
    _dossier.mkdir(parents=True, exist_ok=True)


def _get(cle, defaut):
    """Petit helper : lit une variable d'environnement avec une valeur par defaut."""
    return os.getenv(cle, defaut)


# --- Base de donnees ---
DATABASE_URL = _get("DATABASE_URL", f"sqlite:///{DB_DIR / 'opportunity.db'}")

# --- Scraping ---
SCRAPING_DELAY = float(_get("SCRAPING_DELAY", "2.0"))
USER_AGENT = _get("USER_AGENT", "OpportunitySN-Bot/1.0 (+https://github.com/pa-malick)")
REQUEST_TIMEOUT = 15  # secondes avant d'abandonner une requete
MAX_RETRIES = 3       # nombre d'essais avant de laisser tomber une page

# --- Email ---
SMTP_HOST = _get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(_get("SMTP_PORT", "587"))
SMTP_USER = _get("SMTP_USER", "")
SMTP_PASSWORD = _get("SMTP_PASSWORD", "")
EMAIL_FROM = _get("EMAIL_FROM", "")
EMAIL_TO = _get("EMAIL_TO", "")
# EMAIL_ENABLED = false permet de tester sans vraiment envoyer de mail.
EMAIL_ENABLED = _get("EMAIL_ENABLED", "false").lower() == "true"

# --- Analyse ---
ZSCORE_THRESHOLD = float(_get("ZSCORE_THRESHOLD", "2.5"))

# --- Automatisation no-code (Make / Zapier) ---
# On envoie les alertes a un webhook Make/Zapier qui se charge ensuite de les
# router vers Slack, Google Sheets, WhatsApp, email... C'est le pont entre notre
# pipeline Python et les outils no-code utilises en entreprise.
MAKE_WEBHOOK_URL = _get("MAKE_WEBHOOK_URL", "")
WEBHOOK_ENABLED = _get("WEBHOOK_ENABLED", "false").lower() == "true"

# --- Metadonnees projet (utilisees dans les rapports) ---
PROJET_NOM = "OpportunitySN"
PROJET_AUTEUR = "Papa Malick NDIAYE"
PROJET_GITHUB = "https://github.com/pa-malick"
PROJET_LINKEDIN = "https://www.linkedin.com/in/papa-malick-ndiaye-b58b22309"
