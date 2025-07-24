# FIM / Fablab Inventory Manager

*Basé sur l'outil [JPJR](https://github.com/lfpoulain/jpjr) des **Frères Poulain**.*

FIM est une application web développée avec Flask pour gérer l'inventaire d'un fablab. Elle intègre une interface d'administration, une API JSON et des commandes vocales optionnelles via [speaches](https://github.com/speaches-ai/speaches/).

Une carte graphique NVIDIA supportant CUDA est nécessaire pour faire tourner les fonctionnalités d'IA (chat et reconnaissance vocale).

## 🚀 Démarrage Rapide

### 1. Script d'installation (Ubuntu) - Recommandé pour les débutants

DISCLAIMER : Le script a été testé sur un Ubuntu Desktop 24.10. D'autres distributions (Ubuntu-based) ou versions pourraient fonctionner mais c'est à vos risques et périls.

Clonez le dépôt avec git et rendez-vous dans le dossier local :

```batch 
git clone https://github.com/8AH/fim.git
cd fim
bash ./install_script.sh
```

De là, le script installera les premières dépendansces (curl et dialog) et vous permet d'installer toutes les dépendances pour le logiciel (Docker, Pilotes Graphiques NVIDIA, NVIDIA Container Toolkit), lancera les containers et téléchargera les modèles pour les fonctionnalités IA.

Il téléchargera aussi le gestionnaire de paquets [Homebrew ](https://brew.sh/) ainsi que [oxker](https://github.com/mrjackwills/oxker) pour administrer les containers docker.

Il existe aussi une configuration personnalisée qui permet de choisir les composants à installer.

### 2. Utilisation avec Docker Compose

*En cours de rédaction*

---

## ✨ Fonctionnalités Clés

*   🗃️ **Gestion d'Inventaire Détaillée :** Organisez avec précision vos articles, utilisateurs et emplacements de stockage (zones, meubles, tiroirs).
*   🤝 **Suivi d'Emprunts Efficace :** Enregistrez les prêts, définissez des dates de retour et gardez un œil sur les articles empruntés.
*   📦 **Flexibilité des Articles : Conventionnels & Temporaires**
    *   **Articles Conventionnels :** Vos objets permanents, soigneusement rangés avec un emplacement fixe (ex: "Zone: Bureau, Meuble: Étagère").
    *   **Articles Temporaires :** Pour les besoins du moment ! Créez-les à la volée, souvent par une simple commande vocale (ex: "piles").
*   🔌 **API JSON Robuste :** Intégrez FIM à d'autres outils ou services grâce à des points de terminaison complets pour les articles, prêts, emplacements et services d'IA.
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
