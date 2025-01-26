FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copie des fichiers de l'application
COPY . .

# Création des dossiers nécessaires
RUN mkdir -p uploads generated

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Configuration de l'environnement
ENV FLASK_APP=run.py
ENV FLASK_ENV=production
ENV PORT=8000
ENV HOST=0.0.0.0
ENV SECRET_KEY=your-secret-key-here

# Exposition du port
EXPOSE 8000

# Commande de démarrage
CMD ["gunicorn", "--bind", "$HOST:$PORT", "--workers", "2", "--threads", "4", "--timeout", "120", "run:app"]
