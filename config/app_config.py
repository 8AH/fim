"""
Configuration de l'application pour JPJR.
Gère les clés API et autres paramètres d'application via le fichier .env.
"""
import os
from dotenv import load_dotenv, set_key, find_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Clés de configuration gérées
CONFIG_KEYS = {
    'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', '')
}

def get_app_config_values():
    """
    Retourne un dictionnaire des valeurs de configuration actuelles de l'application,
    basé sur les variables d'environnement chargées.
    """
    # Recharger les valeurs au cas où elles auraient été modifiées en dehors de cette session
    load_dotenv()
    current_config = {}
    for key in CONFIG_KEYS.keys():
        current_config[key] = os.getenv(key, '')
    return current_config

def save_app_config_value(key_to_save, value_to_save):
    """
    Enregistre une valeur de configuration spécifique dans le fichier .env.
    Met également à jour la configuration globale CONFIG_KEYS pour la session courante.
    Retourne True en cas de succès, False sinon.
    """
    if key_to_save not in CONFIG_KEYS:
        print(f"ERREUR: Clé de configuration inconnue: {key_to_save}")
        return False

    # Mettre à jour la configuration globale CONFIG_KEYS pour la session courante
    CONFIG_KEYS[key_to_save] = value_to_save

    # Trouver le chemin du fichier .env. S'il n'est pas trouvé, le créer à la racine.
    dotenv_path = find_dotenv(usecwd=True) # Cherche d'abord dans le CWD
    if not dotenv_path or not os.path.exists(dotenv_path):
        # Tenter de le situer par rapport à ce fichier de config
        config_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(config_dir) # Remonter d'un niveau (de config/ à la racine)
        dotenv_path = os.path.join(project_root, '.env')
        if not os.path.exists(dotenv_path):
            try:
                open(dotenv_path, 'a').close() # Crée le fichier s'il n'existe pas
                print(f"INFO: Fichier .env créé à {dotenv_path}")
            except Exception as e:
                print(f"ERREUR: Impossible de créer le fichier .env à {dotenv_path}: {str(e)}")
                return False
    
    try:
        set_key(dotenv_path, key_to_save, str(value_to_save))
        print(f"INFO: Configuration '{key_to_save}' enregistrée dans {dotenv_path}")
        return True
    except Exception as e:
        print(f"ERREUR: Impossible d'enregistrer la configuration '{key_to_save}' dans {dotenv_path}: {str(e)}")
        return False

if __name__ == '__main__':
    print("Configuration actuelle de l'application:")
    print(get_app_config_values())

    # Test de sauvegarde (décommenter pour tester)
    # test_key = 'OPENAI_API_KEY'
    # test_value = 'nouvelle_cle_api_test_123'
    # print(f"\nTest de sauvegarde pour {test_key}...")
    # if save_app_config_value(test_key, test_value):
    #     print(f"  {test_key} sauvegardée avec succès.")
    #     reloaded_config = get_app_config_values()
    #     print(f"  Valeur rechargée: {reloaded_config.get(test_key)}")
    #     # Restaurer l'ancienne valeur si nécessaire ou laisser la nouvelle pour le test
    #     # save_app_config_value(test_key, CONFIG_KEYS[test_key]) # Pour restaurer
    # else:
    #     print(f"  Échec de la sauvegarde de {test_key}.")
