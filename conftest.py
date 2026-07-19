"""
conftest.py a la racine.

Sa seule presence ici suffit a pytest pour ajouter la racine du projet au
chemin d'import. Ainsi, les tests peuvent faire "from src..." et
"from tests.fixtures import ..." sans configuration supplementaire.
"""

import sys
from pathlib import Path

# On ajoute la racine du projet au debut du sys.path, par securite.
RACINE = Path(__file__).resolve().parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))
