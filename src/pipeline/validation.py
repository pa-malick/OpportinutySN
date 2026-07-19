"""
Validation des donnees avec Pydantic.

Le scraping renvoie des dictionnaires bruts, potentiellement sales ou
incomplets. Avant de stocker quoi que ce soit, on fait passer chaque offre
par ce "controle qualite". Pydantic verifie les types, applique des valeurs
par defaut, et rejette proprement ce qui est vraiment inutilisable.

Avantage concret : on garantit qu'une offre en base a toujours la meme forme,
ce qui simplifie enormement l'analyse et le dashboard plus tard.
"""

import hashlib
from datetime import date
from typing import ClassVar, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class OffreEmploi(BaseModel):
    """Schema d'une offre d'emploi validee."""

    titre: str
    entreprise: str = "Non precise"
    lieu: str = "Non precise"
    pays: str = "Senegal"
    categorie: Optional[str] = None
    competences: List[str] = Field(default_factory=list)
    salaire_min: Optional[int] = None
    salaire_max: Optional[int] = None
    devise: str = "XOF"
    date_publication: Optional[date] = None
    source: str
    url: str

    @field_validator("titre")
    @classmethod
    def titre_non_vide(cls, valeur):
        """Une offre sans titre n'a aucun interet, on la rejette."""
        if not valeur or not valeur.strip():
            raise ValueError("Le titre est obligatoire")
        return valeur.strip()

    # Au-dela de ce seuil, c'est forcement une erreur de parsing (numero de
    # telephone, identifiant, nombres colles...) et pas un salaire. Genereux
    # pour laisser passer les hauts salaires cadres, meme en XOF annuel.
    SALAIRE_MAX_PLAUSIBLE: ClassVar[int] = 100_000_000

    @field_validator("salaire_min", "salaire_max")
    @classmethod
    def salaire_positif(cls, valeur):
        """Ecarte les salaires negatifs ou absurdement grands (erreurs de parsing)."""
        if valeur is not None and (valeur < 0 or valeur > cls.SALAIRE_MAX_PLAUSIBLE):
            return None
        return valeur

    @model_validator(mode="after")
    def coherence_salaire(self):
        """
        On verifie que salaire_min <= salaire_max.

        Si les deux sont inverses (ca arrive avec un mauvais parsing), on les
        remet dans le bon ordre plutot que de jeter l'offre.
        """
        if (
            self.salaire_min is not None
            and self.salaire_max is not None
            and self.salaire_min > self.salaire_max
        ):
            self.salaire_min, self.salaire_max = self.salaire_max, self.salaire_min
        return self

    def identifiant(self):
        """
        Genere un identifiant unique et stable pour l'offre.

        On se base sur le titre + entreprise + source. Deux scraps du meme
        poste donneront le meme identifiant, ce qui permet de dedoublonner
        proprement (voir l'ETL).
        """
        base = f"{self.titre}|{self.entreprise}|{self.source}".lower()
        return hashlib.md5(base.encode("utf-8")).hexdigest()

    def salaire_moyen(self):
        """Retourne le salaire moyen de la fourchette, ou None si inconnu."""
        if self.salaire_min is not None and self.salaire_max is not None:
            return (self.salaire_min + self.salaire_max) / 2
        return self.salaire_min or self.salaire_max


def valider_offres(offres_brutes):
    """
    Valide une liste d'offres brutes (dictionnaires).

    Retourne deux listes : les offres valides (objets OffreEmploi) et les
    offres rejetees (avec la raison). On garde les rejets pour pouvoir les
    inspecter, pas question de les faire disparaitre en silence.
    """
    valides = []
    rejetees = []
    for brute in offres_brutes:
        try:
            valides.append(OffreEmploi(**brute))
        except Exception as e:  # noqa: BLE001
            rejetees.append({"offre": brute, "raison": str(e)})
    return valides, rejetees
