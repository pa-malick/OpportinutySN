# Image de base legere avec Python.
FROM python:3.12-slim

# Bonnes pratiques : pas de fichiers .pyc, logs non bufferises (visibles direct).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# On installe d'abord les dependances (cette couche est mise en cache tant que
# requirements.txt ne change pas, donc les builds suivants sont rapides).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Puis on copie le reste du code.
COPY . .

# Port utilise par Streamlit.
EXPOSE 8501

# Par defaut on lance la pipeline une fois. docker-compose surcharge cette
# commande pour chaque service (planificateur ou dashboard).
CMD ["python", "main.py"]
