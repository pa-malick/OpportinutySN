"""
API FastAPI : le pont entre la pipeline Python et le front Vue.

Le front a besoin des memes analyses que le dashboard Streamlit, mais sous forme
de JSON. On reutilise donc exactement les fonctions d'analyse existantes, et on
les expose via quelques routes. Une seule fonction, build_insights(), fait tout
le calcul ; les routes et le script d'export s'en servent.

Lancer avec :  uvicorn src.api.server:app --reload --port 8000
"""

import math
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.analysis.anomaly_detection import detecter_anomalies
from src.analysis.trend_analysis import (
    competences_les_plus_demandees,
    offres_par_ville,
    salaire_moyen_par_categorie,
    resume_marche,
    top_entreprises,
    volume_dans_le_temps,
)
from src.pipeline.storage import charger_offres


def _native(valeur):
    """
    Convertit les types numpy/pandas en types Python purs.

    Sans ca, le JSON planterait sur un np.float64 ou un NaN. On transforme aussi
    les NaN en None, plus propre cote front.
    """
    if valeur is None:
        return None
    if isinstance(valeur, float) and math.isnan(valeur):
        return None
    # numpy expose .item() pour recuperer le scalaire Python equivalent.
    if hasattr(valeur, "item"):
        return valeur.item()
    return valeur


def _records(df):
    """Transforme un DataFrame en liste de dicts avec des types JSON-compatibles."""
    lignes = []
    for ligne in df.to_dict("records"):
        lignes.append({cle: _native(val) for cle, val in ligne.items()})
    return lignes


def build_insights():
    """
    Calcule tout ce dont le front a besoin, en une passe.

    Retourne un dictionnaire pret a etre serialise en JSON. Si la base est vide,
    on renvoie une structure vide mais valide (le front sait la gerer).
    """
    df = charger_offres()

    if df.empty:
        return {
            "stats": resume_marche(df),
            "salaires": [],
            "competences": [],
            "entreprises": [],
            "villes": [],
            "volume": [],
            "anomalies": [],
        }

    # On lance la detection d'anomalies pour enrichir les offres.
    df, anomalies = detecter_anomalies(df)

    stats = {cle: _native(val) for cle, val in resume_marche(df).items()}

    # La date de publication doit devenir une chaine pour le JSON.
    volume = volume_dans_le_temps(df)
    if not volume.empty:
        volume = volume.copy()
        volume["date_publication"] = volume["date_publication"].astype(str)

    colonnes_anom = ["titre", "entreprise", "categorie", "lieu", "salaire_min", "salaire_max"]

    return {
        "stats": stats,
        "salaires": _records(salaire_moyen_par_categorie(df)),
        "competences": _records(competences_les_plus_demandees(df, top=12)),
        "entreprises": _records(top_entreprises(df, top=8)),
        "villes": _records(offres_par_ville(df)),
        "volume": _records(volume),
        "anomalies": _records(anomalies[colonnes_anom]) if not anomalies.empty else [],
    }


def build_offres():
    """
    Renvoie la liste complete des offres, une par ligne, prete pour le front.

    On lance la detection d'anomalies pour attacher a chaque offre son salaire
    de reference et un drapeau 'anomalie'. Le front fait ensuite tout le filtrage
    et les agregats cote navigateur (rapide et interactif sur ce volume).
    """
    df = charger_offres()
    if df.empty:
        return {"generated_at": datetime.now().isoformat(timespec="seconds"), "offres": []}

    df, _ = detecter_anomalies(df)  # ajoute les colonnes salaire_ref et anomalie

    offres = []
    for r in df.to_dict("records"):
        offres.append({
            "titre": r.get("titre"),
            "entreprise": r.get("entreprise"),
            "lieu": r.get("lieu"),
            "categorie": r.get("categorie"),
            "competences": r.get("competences") if isinstance(r.get("competences"), list) else [],
            "salaire_min": _native(r.get("salaire_min")),
            "salaire_max": _native(r.get("salaire_max")),
            "salaire_ref": _native(r.get("salaire_ref")),
            "anomalie": bool(r.get("anomalie", False)),
            "date_publication": str(r["date_publication"]) if r.get("date_publication") else None,
            "source": r.get("source"),
            "url": r.get("url"),
        })

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "offres": offres,
    }


# --- Application FastAPI ---
app = FastAPI(title="OpportunitySN API", version="1.0.0")

# On autorise le front (Vite) a appeler l'API depuis le navigateur.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:4173",  # vite preview
    ],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    """Petite route pour verifier que l'API tourne."""
    return {"status": "ok"}


@app.get("/api/insights")
def insights():
    """Renvoie les agregats deja calcules (garde pour compatibilite)."""
    return build_insights()


@app.get("/api/offres")
def offres():
    """Renvoie toutes les offres brutes. C'est ce que consomme l'outil."""
    return build_offres()
