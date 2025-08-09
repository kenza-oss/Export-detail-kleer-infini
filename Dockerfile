# Dockerfile pour KleerLogistics
FROM python:3.11-slim

# Variables d'environnement Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Répertoire de travail (racine du projet)
WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        libffi-dev \
        libssl-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements.txt ./

#installer les dépendances Python 
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le code de l'application
COPY . /app/
WORKDIR /app/kleerlogistics

# Créer un utilisateur non-root et donner la propriété du code
RUN adduser --disabled-password --gecos '' appuser 
RUN chown -R appuser:appuser /app
USER appuser

# RUN DJANGO_SETTINGS_MODULE=config.settings.production python kleerlogistics/manage.py collectstatic --noinput || true

# Exposer le port
EXPOSE 8000

# Lancer l'application avec Gunicorn
CMD ["gunicorn", "--access-logfile", "-", "--workers", "3", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
