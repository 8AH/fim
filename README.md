# JPJR / Je prends, je rends

Créé par **Les Frères Poulain**.

Modifié par **8AH**.

```
Version modifiée pour utiliser Ollama (llama3.1:8b) et faster-whisper-server en lieu et place d'OpenAI.
```

JPJR est une petite application web développée avec Flask pour gérer un inventaire d'objets et suivre les emprunts. Elle intègre une interface d'administration, une API JSON et des commandes vocales optionnelles via faster-whisper-server.

**Vidéo de présentation du projet :** [Lien YouTube](https://www.youtube.com/watch?v=ZFS_MIF8jPY&t)

## 🚀 Démarrage Rapide

### 1. Installation locale (Python)

1.  Créez et activez un environnement virtuel Python :
    ```bash
    # Créer l'environnement (une seule fois)
    python -m venv venv

    # Activer l'environnement (pour chaque nouvelle session de terminal)
    # Sur Windows :
    venv\Scripts\activate
    # Sur macOS/Linux :
    source venv/bin/activate
    ```
2.  Installez les dépendances :
    ```bash
    pip install -r requirements.txt
    ```
3.  Créez un fichier `.env` à partir de `.env.example` et configurez les variables pour la base de données et l'API (voir `docs/documentation_technique.md` pour plus de détails).
4.  Lancez l'application :
    ```bash
    python -m src.app
    ```

Par défaut, l'application utilise SQLite. Vous pouvez passer à PostgreSQL en définissant `DB_TYPE=postgresql` dans votre fichier `.env`.
<!-- 
---

### 2. Utilisation avec Docker Compose

#### a) Avec SQLite (par défaut)

Créez un fichier `docker-compose.yml` à la racine du projet avec le contenu suivant :

```yaml
services:
  app:
    image: ghcr.io/lfpoulain/jpjr:latest
    container_name: jpjr_app
    env_file:
      - .env
    volumes:
      - ./data:/app/data
    ports:
      - "5001:5001"
    restart: unless-stopped
```

Créez un fichier `.env` à la racine du projet avec par exemple :

```env
# Configuration de la base de données
# Choisissez le type de base de données : 'postgresql' ou 'sqlite'
DB_TYPE=sqlite

# --- Paramètre pour SQLite (ignoré si DB_TYPE=postgresql) ---
# Nom du fichier de la base de données SQLite. Si non défini, 'jpjr.db' sera utilisé par défaut.
SQLITE_DB_NAME=jpjr.db

# --- Clés d'API ---
# Clé API pour les services OpenAI (Whisper pour la transcription, GPT pour le chat)
OPENAI_API_KEY='sk-proj-YOUR_OPENAI_API_KEY'

# --- Sécurité Flask ---
# Clé secrète utilisée par Flask pour signer les sessions. Doit être une chaîne de caractères longue et aléatoire.
# Vous pouvez en générer une avec : python -c 'import secrets; print(secrets.token_hex(16))'
SECRET_KEY='your_very_secret_flask_key'

# --- Mode Débogage Flask ---
# Mettre à 1 pour activer le mode débogage de Flask (rechargement automatique, logs détaillés).
# Mettre à 0 pour le mode production.
FLASK_DEBUG=0
```

Lancez l'application :
```bash
docker-compose up -d
```

#### b) Avec PostgreSQL

Créez un fichier `docker-compose.yml` à la racine du projet avec le contenu suivant :

```yaml
services:
  app:
    image: ghcr.io/lfpoulain/jpjr:latest
    container_name: jpjr_app
    env_file:
      - .env
    ports:
      - "5001:5001"
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:16
    container_name: jpjr_db
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_HOST_AUTH_METHOD: trust
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  pgdata:
```

Créez un fichier `.env` à la racine du projet avec par exemple :

```env
# Configuration de la base de données
# Choisissez le type de base de données : 'postgresql' ou 'sqlite'
DB_TYPE=postgresql

# --- Paramètres pour PostgreSQL (ignorés si DB_TYPE=sqlite) ---
DB_HOST=db # Si utilisation de docker, mettre 'db' pour le conteneur PostgreSQL
DB_NAME=jpjr_db
DB_USER=admin
DB_PASSWORD=your_secure_password
DB_PORT=5432

# --- Clés d'API ---
# Clé API pour les services OpenAI (Whisper pour la transcription, GPT pour le chat)
OPENAI_API_KEY='sk-proj-YOUR_OPENAI_API_KEY'

# --- Sécurité Flask ---
# Clé secrète utilisée par Flask pour signer les sessions. Doit être une chaîne de caractères longue et aléatoire.
# Vous pouvez en générer une avec : python -c 'import secrets; print(secrets.token_hex(16))'
SECRET_KEY='your_very_secret_flask_key'

# --- Mode Débogage Flask ---
# Mettre à 1 pour activer le mode débogage de Flask (rechargement automatique, logs détaillés).
# Mettre à 0 pour le mode production.
FLASK_DEBUG=0
```

Lancez l'ensemble :
```bash
docker-compose up -d
``` -->

---

## ✨ Fonctionnalités Clés

*   🗃️ **Gestion d'Inventaire Détaillée :** Organisez avec précision vos articles, utilisateurs et emplacements de stockage (zones, meubles, tiroirs).
*   🤝 **Suivi d'Emprunts Efficace :** Enregistrez les prêts, définissez des dates de retour et gardez un œil sur les articles empruntés.
*   📦 **Flexibilité des Articles : Conventionnels & Temporaires**
    *   **Articles Conventionnels :** Vos objets permanents, soigneusement rangés avec un emplacement fixe (ex: "Zone: Bureau, Meuble: Étagère").
    *   **Articles Temporaires :** Pour les besoins du moment ! Créez-les à la volée, souvent par une simple commande vocale (ex: "piles").
*   🔌 **API JSON Robuste :** Intégrez JPJR à d'autres outils ou services grâce à des points de terminaison complets pour les articles, prêts, emplacements et services d'IA.
*   🎙️ **Commandes Vocales Intelligentes (propulsées par 4o Transcribe et GPT-4o-mini) :**
    *   **Depuis le Tableau de Bord (Dashboard) :**
        *   ⚡ **Ajout Rapide "Temporaire" :** Dictez et ajoutez instantanément des articles sans emplacement prédéfini.
        *   🧠 **Mode "Complet" (Recherche/Ajout Intelligent) :** L'IA identifie vos articles, les rapproche de votre inventaire existant ou crée de nouveaux articles temporaires. (Note : peut solliciter davantage l'API pour une pertinence accrue).
    *   🏠 **Page Dédiée "Ajout Vocal Conventionnel" :** Dictez le nom de l'article ET son emplacement (Zone, Meuble, Tiroir) pour l'intégrer parfaitement à votre système de rangement, avec l'aide de l'IA pour un rapprochement intelligent.
*   💬 **Dialogue avec vos Données (via llama3.1:8b) :** Posez des questions en langage naturel sur votre inventaire directement depuis la barre de menu !
*   📄 **Export PDF Pratique :** Obtenez une copie de votre inventaire complet au format PDF en un clic.

## 🗄️ Base de Données : Flexibilité SQLite & PostgreSQL

*   **SQLite (par défaut) :** Idéal pour une utilisation locale et un développement rapide. La base de données est un simple fichier dans le projet.
*   **PostgreSQL :** Recommandé pour une utilisation plus robuste. Il permet d'exposer la base de données à des outils externes, notamment pour des applications d'intelligence artificielle qui pourraient avoir besoin d'analyser les données d'inventaire.

## 🏗️ Structure du Projet

```
config/                           # Modules de configuration
data/                             # Fichier SQLite3
docker/                           # Fichiers Docker spécifiques
docs/                             # Documentation technique
src/                              # Code source de l'application
    app.py                        # Point d'entrée de Flask
    models/                       # Modèles SQLAlchemy
    routes/                       # Blueprints (groupes de routes)
    static/                       # Fichiers statiques (CSS, JS, images)
    templates/                    # Modèles Jinja2
```

## ©️ Licence

Ce projet est sous licence [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International](http://creativecommons.org/licenses/by-nc-sa/4.0/).

[![Licence CC BY-NC-SA 4.0](https://i.creativecommons.org/l/by-nc-sa/4.0/88x31.png)](http://creativecommons.org/licenses/by-nc-sa/4.0/)

See the [technical documentation](docs/documentation_technique.md) for a complete guide.