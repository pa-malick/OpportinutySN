<p align="center">
  <img src="docs/logo.svg" alt="OpportunitySN" width="360" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Vue.js-4FC08D?style=flat-square&logo=vuedotjs&logoColor=white" alt="Vue.js" />
  <img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white" alt="GitHub Actions" />
  <img src="https://img.shields.io/badge/Make-6D00CC?style=flat-square&logo=make&logoColor=white" alt="Make" />
</p>

<p align="center"><strong>Pipeline d'automatisation de bout en bout : collecte → traitement → diffusion, sans intervention humaine.</strong></p>

# OpportunitySN

**Veille automatisee du marche de l'emploi Tech au Senegal.**

OpportunitySN est une pipeline de data engineering qui collecte des offres
d'emploi, les nettoie, detecte les anomalies de salaire, suit les tendances de
competences, et diffuse le tout via un dashboard, des emails et des alertes
Slack/WhatsApp (grace a Make).

**Auteur** : Papa Malick NDIAYE, etudiant en Master Data Science et Genie
Logiciel (Universite Alioune Diop de Bambey), Data Scientist et AI Engineer.

- GitHub : [pa-malick](https://github.com/pa-malick)
- LinkedIn : [papa-malick-ndiaye](https://www.linkedin.com/in/papa-malick-ndiaye-b58b22309)

---

## Automatisation (le coeur du projet)

Avant tout, OpportunitySN est un projet d'**automatisation** : une fois en ligne,
il tourne seul, sans intervention humaine. Trois maillons entierement automatises :

- **Collecte planifiee** : un cron GitHub Actions (et un DAG Airflow) relance le
  scraping chaque matin a 08:00, met a jour les donnees et redeploie le tableau de bord.
- **Traitement automatique** : nettoyage, validation Pydantic, detection d'anomalies
  de salaire et de tendances, sans aucune action manuelle.
- **Diffusion automatique** : a chaque execution, un webhook Make relaie les alertes
  vers email / Slack / WhatsApp, et les utilisateurs s'abonnent depuis le site.

**La boucle quotidienne, sans personne aux commandes :**

```
   Chaque matin a 08:00
           |
   GitHub Actions (cron)  ->  scraping + ETL + analyse
           |                          |
           v                          v
   Webhook Make               nouveau snapshot commite
   (email / Slack / WhatsApp)         |
                                      v
                          Netlify redeploie le site a jour
```

> **On deploie une seule fois, et le systeme collecte, analyse, alerte et se met
> a jour tout seul, chaque jour.** C'est ca, le coeur du projet.

## Ce que fait le projet

En une phrase : il transforme des donnees brutes du marche de l'emploi en
insights actionnables, automatiquement.

1. **Collecte** les offres depuis plusieurs sources (scraping Python).
2. **Nettoie et valide** chaque offre (ETL + Pydantic), puis stocke en base.
3. **Analyse** les salaires (detection d'anomalies) et les tendances (competences
   qui montent, entreprises qui recrutent).
4. **Alerte** les decideurs sur ce qui compte (nouvelle offre Data, salaire
   inhabituel, competence tres demandee).
5. **Diffuse** via un dashboard web, un rapport email, et un webhook Make qui
   relaie vers Slack, Google Sheets ou WhatsApp.

## La stack (100% gratuite)

| Couche          | Outils                                        |
|-----------------|-----------------------------------------------|
| Scraping        | requests, BeautifulSoup                       |
| ETL             | pandas, SQLAlchemy, Pydantic                  |
| Base de donnees | SQLite (par defaut), PostgreSQL possible      |
| Analyse         | numpy, scipy (Z-score, IQR)                   |
| Notification    | smtplib, Jinja2, Webhook Make/Zapier          |
| Dashboard       | Streamlit, Plotly                             |
| Orchestration   | schedule (simple), Airflow (optionnel)        |
| Conteneurs      | Docker, Docker Compose                        |
| Tests           | pytest, pytest-cov                            |

## Architecture en une image

```
 Scraping (Python)
      |
      v
 ETL + validation (Pydantic)
      |
      v
 Base de donnees (SQLite / PostgreSQL)
      |
      v
 Analyse (anomalies + tendances)
      |
      +--> Dashboard Streamlit
      +--> Email (rapport HTML)
      +--> Webhook --> Make/Zapier --> Slack / Google Sheets / WhatsApp
```

Le detail fichier par fichier est dans `ARCHITECTURE_FICHIERS.txt`.

## Demarrage rapide

Pre-requis : Python 3.11 ou plus.

```bash
# 1. Installer les dependances
pip install -r requirements.txt

# 2. Copier la config et l'ajuster si besoin
cp .env.example .env

# 3. Lancer toute la pipeline (utilise la source de demonstration)
python main.py

# 4. Ouvrir le dashboard
streamlit run src/dashboard/app.py
```

Par defaut, le projet tourne sans aucune cle ni compte externe grace a la source
de demonstration (`demo_scraper`). Les emails et le webhook Make sont en mode
simulation tant que tu ne les actives pas dans le `.env`.

Pour ajouter le vrai scraper EmploiSenegal (necessite une connexion) :

```bash
python main.py --reel
```

## Lancer les tests

```bash
pytest --cov=src --cov-report=term-missing
```

## Deploiement

Voir `docs/DEPLOYMENT.md`. En resume : le projet se lance en une commande avec
Docker Compose, et se deploie gratuitement sur Render ou Railway.

```bash
docker compose -f docker/docker-compose.yml up --build
```

## Structure du projet

```
src/
  scrapers/      collecte des offres
  pipeline/      ETL, stockage, validation
  analysis/      anomalies, tendances, alertes
  notification/  email + webhook Make
  dashboard/     application Streamlit
orchestration/   planification (schedule / Airflow)
docker/          conteneurisation
tests/           tests unitaires
docs/            documentation + rapport Word
```

## Choix assumes

- **SQLite par defaut** pour que le projet tourne partout sans installation.
  Passer a PostgreSQL demande juste de changer une ligne dans le `.env`.
- **Une source de demonstration** pour garantir un jeu de donnees stable, meme
  si un site change son HTML ou bloque les robots. Les vrais scrapers restent
  presents et fonctionnels.
- **Code + no-code** : Python fait le travail lourd, Make gere la distribution
  des alertes. C'est l'approche hybride qu'on retrouve en entreprise.

## Licence

Projet personnel a but pedagogique et de portfolio.
