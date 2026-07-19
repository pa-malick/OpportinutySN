# OpportunitySN, outil de veille (front-end)

Interface de veille du marche de l'emploi Tech au Senegal. Un vrai outil de
travail : on filtre a gauche, on lit les resultats a droite. Sobre, rapide,
lisible.

## Ce qu'on peut faire

- Filtrer les offres par metier, ville, recherche texte et salaire minimum.
- Lire les chiffres cles (offres, entreprises, salaire median, anomalies).
- Voir les salaires par metier, les competences demandees, les recruteurs, et
  le volume d'offres dans le temps.
- Reperer les salaires anormaux (lignes surlignees dans la table).
- Exporter la selection courante en CSV.

Tout se recalcule en direct a chaque changement de filtre.

## Stack

- Vue 3 (Composition API, `<script setup>`)
- Tailwind CSS
- Agregation et graphiques faits maison (aucune librairie de charts, ca reste leger)

## Demarrer

```bash
cd frontend
npm install --legacy-peer-deps
npm run dev          # http://localhost:5173
```

## D'ou viennent les donnees

Le front tente d'abord l'API FastAPI en direct (`http://localhost:8000/api/offres`),
puis se rabat sur le snapshot `public/offres.json`. Il affiche donc toujours de
vraies donnees, avec ou sans backend.

Pour rafraichir les donnees :

```bash
# a la racine du projet
python main.py                       # relance la pipeline
python -m src.api.export_snapshot    # regenere public/offres.json
# et/ou lancer l'API live :
python -m uvicorn src.api.server:app --port 8000
```

## Structure

```
src/
  App.vue                  layout de l'outil + etat des filtres
  components/
    FilterPanel.vue        filtres (metier, ville, recherche, salaire)
    KpiRow.vue             les 4 chiffres cles
    BarList.vue            graphique a barres reutilisable
    TrendLine.vue          courbe du volume (SVG)
    OffersTable.vue        table detaillee, triable, anomalies surlignees
  composables/
    useOffres.js           chargement des offres (API puis snapshot)
  utils/
    aggregate.js           agregats (kpis, salaires, competences...)
    format.js              formatage FCFA + export CSV
```
