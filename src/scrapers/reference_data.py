"""
Donnees de reference utilisees par les scrapers.

On centralise ici la liste des competences a detecter et les categories
de metiers. Comme ca, si le marche evolue (nouvelle techno a la mode),
on met a jour un seul endroit.
"""

# Competences techniques que l'on cherche a reperer dans les offres.
COMPETENCES_TECH = [
    "Python", "SQL", "Java", "JavaScript", "TypeScript", "R", "Scala", "Go",
    "Docker", "Kubernetes", "Airflow", "Spark", "Hadoop", "Kafka",
    "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "PyTorch",
    "Power BI", "Tableau", "Excel", "Streamlit",
    "AWS", "Azure", "GCP",
    "Git", "Linux", "Machine Learning", "Deep Learning", "NLP",
    "PostgreSQL", "MongoDB", "MySQL", "ETL", "API", "FastAPI", "Django", "Flask",
]

# Indices qu'un poste releve bien de la Tech. Les API generalistes (RemoteOK,
# Arbeitnow) renvoient tous les metiers (vente, marketing, beaute...). On ne
# garde que les offres dont le titre ou les tags contiennent un de ces mots,
# pour rester fidele a une veille "emploi Tech".
INDICATEURS_TECH = [
    "developer", "developpeur", "développeur", "development", "software",
    "engineer", "ingenieur", "ingénieur", "devops", "backend", "back-end",
    "frontend", "front-end", "fullstack", "full-stack", "full stack",
    "programmer", "programmeur", "data scientist", "data analyst",
    "data engineer", "machine learning", "deep learning", "ml engineer",
    "cloud", "sysadmin", "system administrator", "sre", "qa engineer",
    "cybersecurity", "cyber security", "security engineer", "web developer",
    "mobile developer", "android", "ios developer", "python", "java",
    "javascript", "typescript", "golang", "react", "node.js", "nodejs",
    "database", "informatique", "tech lead", "architect", "it support",
    "blockchain", "data ", "analytics",
    # Termes FR (sites senegalais francophones). Sans risque pour les API
    # anglophones qui ne les contiennent pas.
    "reseau", "réseau", "systeme", "système", "base de donnees",
    "base de données", "integrateur", "intégrateur", "webmaster",
    "informaticien", "genie logiciel", "génie logiciel", "digital",
]

# Grandes categories de metiers, pour ranger les offres.
CATEGORIES = [
    "Data Science",
    "Data Engineering",
    "Developpement Logiciel",
    "DevOps / Cloud",
    "Business Intelligence",
    "Finance / Comptabilite",
]

# Villes frequentes au Senegal (utile pour la demo et la normalisation).
VILLES_SENEGAL = [
    "Dakar", "Thies", "Saint-Louis", "Diamniadio", "Rufisque",
    "Ziguinchor", "Touba", "Kaolack", "Remote",
]
