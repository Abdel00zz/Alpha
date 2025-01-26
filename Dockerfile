FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copie des fichiers de l'application
COPY . .

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Configuration de l'environnement
ENV FLASK_APP=run.py
ENV FLASK_ENV=production

# Exposition du port
EXPOSE 8000

# Commande de démarrage
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "run:app"]
