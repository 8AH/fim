# Utilise une image Python officielle
FROM python:3.13-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier les fichiers nécessaires
COPY requirements.txt ./
COPY src/ ./src/
COPY config/ ./config/

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le .env à la racine du projet (sera monté en prod/dev)
COPY .env.example .env

# Ajouter /app au PYTHONPATH pour que config/ soit visible
ENV PYTHONPATH="/app"

# Exposer le port Flask
EXPOSE 443

# Commande de lancement (modifiez si le point d'entrée diffère)
CMD ["python", "src/app.py"]
