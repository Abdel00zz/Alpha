FROM python:3.11-slim

WORKDIR /app

# Copie des requirements d'abord pour le cache des layers
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du reste des fichiers
COPY . .

# Création des dossiers nécessaires
RUN mkdir -p uploads generated

# Variables d'environnement
ENV PORT=8000
ENV FLASK_APP=run.py
ENV FLASK_ENV=production

# Commande de démarrage
CMD exec gunicorn --bind 0.0.0.0:$PORT run:app
