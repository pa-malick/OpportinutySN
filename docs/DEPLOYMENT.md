# Guide de deploiement

Ce guide couvre trois facons de faire tourner OpportunitySN : en local, avec
Docker, et en ligne (gratuitement).

## 1. En local

```bash
# Cloner le depot
git clone https://github.com/pa-malick/OpportunitySN.git
cd OpportunitySN

# Environnement virtuel (recommande)
python -m venv venv
# Windows :
venv\Scripts\activate
# Linux / Mac :
source venv/bin/activate

# Dependances
pip install -r requirements.txt

# Config
cp .env.example .env

# Lancer la pipeline
python main.py

# Lancer le dashboard
streamlit run src/dashboard/app.py
```

## 2. Avec Docker (recommande)

Docker permet de tout lancer sans se soucier des versions de Python ou des
librairies. Deux services demarrent : le dashboard et le planificateur.

```bash
# Depuis la racine du projet
docker compose -f docker/docker-compose.yml up --build
```

Le dashboard est alors accessible sur http://localhost:8501

Pour arreter :

```bash
docker compose -f docker/docker-compose.yml down
```

## 3. En ligne, gratuitement

### Option A : Render (le plus simple pour le dashboard)

1. Pousser le projet sur GitHub.
2. Creer un compte gratuit sur render.com.
3. New > Web Service, connecter le depot GitHub.
4. Configurer :
   - Build command : `pip install -r requirements.txt`
   - Start command : `streamlit run src/dashboard/app.py --server.address=0.0.0.0 --server.port=$PORT`
5. Ajouter les variables d'environnement (celles du `.env`).

### Option B : Railway

Meme principe, railway.app detecte le projet Python automatiquement. On ajoute
les variables d'environnement dans l'onglet Variables.

### Option C : Streamlit Community Cloud (gratuit, dedie au dashboard)

Parfait si on veut juste partager le dashboard : share.streamlit.io, on pointe
vers `src/dashboard/app.py`, et c'est en ligne.

## Configurer les alertes Make (no-code)

1. Creer un compte gratuit sur make.com.
2. Nouveau scenario, module **Webhooks > Custom webhook**, copier l'URL generee.
3. Coller cette URL dans `.env` (MAKE_WEBHOOK_URL) et mettre `WEBHOOK_ENABLED=true`.
4. Dans Make, brancher apres le webhook les modules voulus : Slack, Google
   Sheets, WhatsApp, email... Le JSON envoye contient `alertes`, `total_offres`,
   `salaire_median`, etc.

## Configurer l'email (Gmail)

1. Activer la validation en deux etapes sur le compte Google.
2. Creer un "mot de passe d'application" (Google Account > Securite).
3. Renseigner SMTP_USER, SMTP_PASSWORD, EMAIL_TO dans `.env`.
4. Mettre `EMAIL_ENABLED=true`.

## Planification automatique

En local ou dans le conteneur `planificateur`, le script
`orchestration/schedule_jobs.py` relance la pipeline chaque jour a 8h. Pour une
version plus pro, le DAG Airflow est fourni dans `orchestration/airflow_dag.py`.
