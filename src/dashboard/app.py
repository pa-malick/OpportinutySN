"""
Dashboard Streamlit : la vitrine du projet pour un decideur.

On lit les offres depuis la base, on calcule les analyses, et on affiche le
tout sous forme de cartes et de graphiques interactifs. Streamlit permet de
faire une vraie appli web en quelques dizaines de lignes, sans HTML/JS.

Lancer avec :  streamlit run src/dashboard/app.py
"""

import plotly.express as px
import streamlit as st

from src.analysis.anomaly_detection import detecter_anomalies
from src.analysis.trend_analysis import (
    competences_les_plus_demandees,
    offres_par_ville,
    salaire_moyen_par_categorie,
    resume_marche,
    top_entreprises,
    volume_dans_le_temps,
)
from src.config import PROJET_AUTEUR, PROJET_GITHUB, PROJET_LINKEDIN
from src.pipeline.storage import charger_offres

# Couleur d'accent du projet, reprise partout pour un rendu coherent.
COULEUR = "#0f766e"

st.set_page_config(page_title="Veille Emploi Tech Senegal", page_icon="📊", layout="wide")


@st.cache_data(ttl=300)
def _charger():
    """
    Charge les offres depuis la base.

    On met en cache 5 minutes pour que le dashboard reste rapide meme si on
    clique partout (on ne relit pas la base a chaque interaction).
    """
    return charger_offres()


def main():
    st.title("Veille marche emploi Tech, Senegal")
    st.caption(f"Projet OpportunitySN, par {PROJET_AUTEUR}")

    df = _charger()

    if df.empty:
        st.warning(
            "Aucune donnee en base. Lance d'abord la pipeline avec :  python main.py"
        )
        return

    # --- Barre laterale : filtres ---
    st.sidebar.header("Filtres")
    categories = sorted(df["categorie"].dropna().unique())
    choix_cat = st.sidebar.multiselect("Categorie", categories, default=categories)
    villes = sorted(df["lieu"].dropna().unique())
    choix_ville = st.sidebar.multiselect("Ville", villes, default=villes)

    filtre = df[df["categorie"].isin(choix_cat) & df["lieu"].isin(choix_ville)]
    if filtre.empty:
        st.info("Aucune offre ne correspond aux filtres choisis.")
        return

    # --- Cartes de synthese ---
    resume = resume_marche(filtre)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Offres suivies", resume["total_offres"])
    c2.metric("Entreprises", resume["nombre_entreprises"])
    salaire = resume["salaire_median"]
    c3.metric("Salaire median", f"{int(salaire):,} FCFA".replace(",", " ") if salaire else "n/d")
    c4.metric("Competence n1", resume["competence_top"] or "n/d")

    st.divider()

    # --- Ligne 1 : salaires par metier + competences ---
    col_g, col_d = st.columns(2)

    with col_g:
        st.subheader("Salaire moyen par metier")
        sal = salaire_moyen_par_categorie(filtre)
        fig = px.bar(
            sal, x="salaire_moyen", y="categorie", orientation="h",
            labels={"salaire_moyen": "Salaire moyen (FCFA)", "categorie": ""},
            color_discrete_sequence=[COULEUR],
        )
        fig.update_layout(showlegend=False, height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col_d:
        st.subheader("Competences les plus demandees")
        comp = competences_les_plus_demandees(filtre, top=12)
        fig = px.bar(
            comp, x="occurrences", y="competence", orientation="h",
            labels={"occurrences": "Nombre d'offres", "competence": ""},
            color_discrete_sequence=[COULEUR],
        )
        fig.update_layout(showlegend=False, height=350, yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

    # --- Ligne 2 : top entreprises + volume dans le temps ---
    col_g2, col_d2 = st.columns(2)

    with col_g2:
        st.subheader("Qui recrute le plus")
        ent = top_entreprises(filtre, top=10)
        fig = px.bar(
            ent, x="nombre_offres", y="entreprise", orientation="h",
            labels={"nombre_offres": "Offres", "entreprise": ""},
            color_discrete_sequence=[COULEUR],
        )
        fig.update_layout(showlegend=False, height=350, yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

    with col_d2:
        st.subheader("Volume d'offres dans le temps")
        volume = volume_dans_le_temps(filtre)
        if volume.empty:
            st.info("Pas de date de publication exploitable.")
        else:
            fig = px.line(
                volume, x="date_publication", y="nombre_offres", markers=True,
                labels={"date_publication": "Date", "nombre_offres": "Offres"},
                color_discrete_sequence=[COULEUR],
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

    # --- Anomalies detectees ---
    st.divider()
    st.subheader("Offres au salaire inhabituel (anomalies detectees)")
    _, anomalies = detecter_anomalies(filtre)
    if anomalies.empty:
        st.success("Aucune anomalie de salaire detectee.")
    else:
        st.dataframe(
            anomalies[["titre", "entreprise", "categorie", "lieu", "salaire_min", "salaire_max"]],
            use_container_width=True, hide_index=True,
        )

    # --- Pied de page ---
    st.divider()
    st.caption(f"GitHub : {PROJET_GITHUB}  |  LinkedIn : {PROJET_LINKEDIN}")


if __name__ == "__main__":
    main()
