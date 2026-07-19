"""
Stockage des offres en base de donnees (SQLAlchemy + SQLite par defaut).

On utilise SQLAlchemy comme couche d'abstraction : le code est le meme que la
base soit SQLite (pour le dev) ou PostgreSQL (pour la prod). Il suffit de
changer DATABASE_URL dans le .env.

On garde un identifiant unique par offre pour eviter les doublons, et une
colonne date_collecte pour construire un historique (utile pour l'analyse de
tendances : on voit ce qui apparait et disparait dans le temps).
"""

import json
from datetime import date, datetime

import pandas as pd
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from src.config import DATABASE_URL
from src.logger import get_logger

logger = get_logger(__name__)

Base = declarative_base()


class OffreDB(Base):
    """Table des offres. Une ligne = une offre unique."""

    __tablename__ = "offres"

    id = Column(String(32), primary_key=True)  # l'identifiant md5 de l'offre
    titre = Column(String(255), nullable=False)
    entreprise = Column(String(255))
    lieu = Column(String(255))
    pays = Column(String(100))
    categorie = Column(String(100))
    competences = Column(Text)  # liste stockee en JSON
    salaire_min = Column(Integer)
    salaire_max = Column(Integer)
    devise = Column(String(10))
    date_publication = Column(Date)
    source = Column(String(100))
    url = Column(Text)
    date_collecte = Column(DateTime, default=datetime.now)


# On cree le moteur une seule fois, partage par tout le module.
_engine = create_engine(DATABASE_URL, echo=False, future=True)
_Session = sessionmaker(bind=_engine)


def init_db():
    """Cree les tables si elles n'existent pas encore."""
    Base.metadata.create_all(_engine)
    logger.info("Base de donnees prete (%s)", DATABASE_URL)


def sauvegarder_offres(offres):
    """
    Enregistre une liste d'objets OffreEmploi (valides) en base.

    On fait un "upsert" maison : si l'offre existe deja (meme identifiant),
    on la met a jour ; sinon on l'insere. Resultat : jamais de doublon.
    Retourne le couple (nb_nouvelles, nb_mises_a_jour).
    """
    init_db()
    nouvelles, majs = 0, 0

    with _Session() as session:
        for offre in offres:
            oid = offre.identifiant()
            existante = session.get(OffreDB, oid)

            valeurs = {
                "titre": offre.titre,
                "entreprise": offre.entreprise,
                "lieu": offre.lieu,
                "pays": offre.pays,
                "categorie": offre.categorie,
                "competences": json.dumps(offre.competences, ensure_ascii=False),
                "salaire_min": offre.salaire_min,
                "salaire_max": offre.salaire_max,
                "devise": offre.devise,
                "date_publication": offre.date_publication,
                "source": offre.source,
                "url": offre.url,
            }

            if existante:
                for cle, val in valeurs.items():
                    setattr(existante, cle, val)
                majs += 1
            else:
                session.add(OffreDB(id=oid, **valeurs))
                nouvelles += 1

        session.commit()

    logger.info("Sauvegarde : %s nouvelles, %s mises a jour.", nouvelles, majs)
    return nouvelles, majs


def charger_offres():
    """
    Charge toutes les offres depuis la base dans un DataFrame pandas.

    Le DataFrame est le format ideal pour l'analyse et le dashboard. On
    reconvertit la colonne competences (JSON) en vraie liste Python au passage.
    """
    init_db()
    with _Session() as session:
        lignes = session.query(OffreDB).all()

    donnees = []
    for ligne in lignes:
        donnees.append({
            "id": ligne.id,
            "titre": ligne.titre,
            "entreprise": ligne.entreprise,
            "lieu": ligne.lieu,
            "pays": ligne.pays,
            "categorie": ligne.categorie,
            "competences": json.loads(ligne.competences) if ligne.competences else [],
            "salaire_min": ligne.salaire_min,
            "salaire_max": ligne.salaire_max,
            "devise": ligne.devise,
            "date_publication": ligne.date_publication,
            "source": ligne.source,
            "url": ligne.url,
            "date_collecte": ligne.date_collecte,
        })

    df = pd.DataFrame(donnees)
    logger.info("%s offres chargees depuis la base.", len(df))
    return df
