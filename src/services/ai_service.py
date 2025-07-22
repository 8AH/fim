"""
Service centralisé pour toutes les interactions avec l'IA et la reconnaissance vocale (version Ollama)
"""
import os
import json
import tempfile
import requests
import re
import logging
from dotenv import load_dotenv
from openai import OpenAI  # Import de la bibliothèque OpenAI pour les appels API
from src.models.item import Item  # Import du modèle Item pour la comparaison
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


# Charger les variables d'environnement
load_dotenv()

class AIService:
    """
    Service qui encapsule toutes les interactions avec l'API Ollama
    et fournit des méthodes unifiées pour la transcription audio (placeholder) et l'analyse de texte
    """
    
    def __init__(self):
        self.api_key = "Placeholder"  # Placeholder pour la clé API, peut être configuré via env si nécessaire
        self.ollama_url = os.environ.get('OLLAMA_URL')
        self.whisper_url = os.environ.get('WHISPER_URL') + "/v1/"  # URL du serveur Whisper
        self.completion_url = f'{self.ollama_url}/api/generate'
        self.model_completion = os.environ.get('OLLAMA_MODEL', 'llama3.1:8b')
        self.model_transcription = os.environ.get('WHISPER_MODEL')
    
    def getFileExtension(self, mime_type):
        """
        Retourne l'extension de fichier appropriée pour un type MIME donné
        
        Args:
            mime_type (str): Type MIME (ex: 'audio/webm')
            
        Returns:
            str: Extension de fichier avec le point (ex: '.webm')
        """
        # Nettoyer le type MIME (enlever les paramètres comme codecs)
        base_mime = mime_type.split(';')[0].strip().lower() if ';' in mime_type else mime_type.lower()
        
        # Mapping des types MIME courants vers les extensions
        mime_map = {
            'audio/webm': '.webm',
            'audio/mp4': '.mp4',
            'audio/mpeg': '.mp3',
            'audio/ogg': '.ogg',
            'audio/wav': '.wav',
            'audio/flac': '.flac',
            'audio/x-m4a': '.m4a',
            'audio/aac': '.aac'
        }
        
        # Retourner l'extension correspondante ou une extension par défaut
        return mime_map.get(base_mime, '.audio')
    
    def transcribe_audio(self, audio_file_path, audio_mime_type='audio/webm'):
        """
        Transcrit un fichier audio en texte en utilisant faster-whisper-server
        
        Args:
            audio_file_path (str): Chemin vers le fichier audio
            audio_mime_type (str): Type MIME du fichier audio
            
        Returns:
            str: Texte transcrit
        Raises:
            Exception: En cas d'erreur de transcription avec Whisper
        """
        try:
            with open(audio_file_path, 'rb') as audio_file:
                client = OpenAI(api_key="cant-be-empty", base_url=self.whisper_url)

                files = {
                    'audio_file': (os.path.basename(audio_file_path), audio_file, audio_mime_type)
                }
                logging.info(f"Envoi d'un fichier audio à Whisper: {os.path.basename(audio_file_path)} (type: {audio_mime_type})")
                
                transcript = client.audio.transcriptions.create(
                    model=self.model_transcription, file=audio_file, language="fr",
                )
                return transcript.text
        except requests.exceptions.RequestException as e:
            error_message = f"Erreur de connexion à Whisper: {str(e)}"
            logging.error(error_message)
            raise Exception("Impossible de se connecter au service de transcription. Veuillez vérifier votre connexion et le serveur.")
        except Exception as e:
            logging.error(f"Erreur inattendue lors de la transcription: {str(e)}")
            raise

    def extract_items_from_text(self, text):
        """
        Extrait les noms d'articles à partir d'un texte
        
        Args:
            text (str): Texte transcrit
            
        Returns:
            list: Liste d'articles au format [{"id": 1, "name": "Nom Article"}]
        """
        
        if not text:
            return []
        
        payload = {
            'model': self.model_completion,
            'prompt': (
                "Tu es un assistant spécialisé dans l'extraction d'articles à partir de commandes vocales. "
                "Ton rôle est d'identifier les noms d'articles mentionnés dans la transcription et de les "
                "retourner sous forme de liste structurée. Ignore les mots de liaison, les articles (le, la, les) "
                "et tout ce qui n'est pas un nom d'article.\n"
                f'Voici la transcription d\'une commande vocale pour emprunter des articles: "{text}". '
                "Extrais les noms des articles mentionnés et retourne-les sous forme de liste JSON avec un ID unique "
                "et le nom de chaque article. Format attendu: [{\"id\": 1, \"name\": \"nom de l'article\"}, ...]. "
                "Ne retourne que le JSON, sans aucun autre texte."
            ),
            'stream': False
        }
        
        response = requests.post(self.completion_url, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Erreur lors de l'analyse avec Ollama: {response.text}")
        
        return self._parse_ollama_response(response.json())
    
    def extract_items_with_locations(self, text, locations_context):
        """
        Extrait les articles avec leurs emplacements à partir d'un texte
        
        Args:
            text (str): Texte transcrit
            locations_context (dict): Contexte des emplacements existants
            
        Returns:
            list: Liste d'articles avec leurs emplacements
        """
        
        logger.debug(f"Texte transcrit pour extraction d'inventaire: '{text}'")
        logger.debug(f"Contexte des emplacements reçu: {locations_context}")
        
        if not text or len(text.strip()) < 3:
            logger.info("Texte trop court ou vide, aucun article à extraire")
            return []
        
        if not text:
            return []
        
        # Préparer le contexte pour l'analyse
        zones_context = self._format_zones_context(locations_context.get('zones', []))
        furniture_context = self._format_furniture_context(locations_context.get('furniture', []))
        drawers_context = self._format_drawers_context(locations_context.get('drawers', []))
        
        payload = {
            'model': self.model_completion,
            'prompt': (
                "Tu es un assistant spécialisé dans l'extraction d'articles et de leurs emplacements "
                "à partir de commandes vocales. Ton rôle est d'identifier les noms d'articles mentionnés "
                "dans la transcription et de les associer aux emplacements existants (zone, meuble, tiroir) "
                "en fonction du contexte fourni. Utilise ton jugement pour faire les meilleures associations "
                "possibles entre ce qui est dit et les emplacements disponibles.\n"
                f'Voici la transcription d\'une commande vocale pour ajouter des articles à l\'inventaire: "{text}". '
                f"\n\nVoici le contexte des emplacements existants:\n\nZONES:\n{zones_context}\n\nMEUBLES:\n{furniture_context}\n\nTIROIRS/NIVEAUX:\n{drawers_context}\n\n"
                "Extrais les noms des articles mentionnés et associe-les aux emplacements existants. "
                "Retourne le résultat sous forme de liste JSON avec le format suivant:\n"
                "[{\"name\": \"nom de l'article\", \"zone_id\": id_zone, \"furniture_id\": id_meuble, \"drawer_id\": id_tiroir}, ...]\n\n"
                "Assure-toi que les IDs correspondent bien aux emplacements existants dans le contexte fourni. "
                "Ne retourne que le JSON, sans aucun autre texte."
            ),
            'stream': False
        }
        
        response = requests.post(self.completion_url, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Erreur lors de l'analyse avec Ollama: {response.text}")
        
        return self._parse_ollama_response(response.json())
    
    def get_inventory_chat_response(self, items_list, user_query):
        """
        Obtient une réponse de l'IA pour une question sur l'inventaire.
        Construit le contexte de l'inventaire et interroge l'API de complétion.

        Args:
            items_list (list): Liste des objets Item de l'inventaire.
            user_query (str): La question de l'utilisateur.

        Returns:
            str: La réponse textuelle de l'IA.
        """

        if not user_query: # Sécurité, bien que déjà vérifié dans la route
            return "La question ne peut pas être vide."

        if not items_list:
            inventory_context = "L'inventaire est actuellement vide."
        else:
            # Le prompt détaillé est maintenant construit ici
            inventory_context_parts = [
                "Tu es un assistant IA expert en gestion d'inventaire. "
                "Réponds aux questions de l'utilisateur concernant la liste du matériel fournie ci-dessous. "
                "Utilise le format Markdown pour structurer tes réponses lorsque c'est pertinent (par exemple, listes à puces, texte en gras, italique). "
                "Sois clair et concis. Voici l'inventaire actuel :"
            ]
            for item in items_list:
                inventory_context_parts.append(
                    f"- Nom: {item.name}, Fournisseur : {item.supplier}, Emplacement: {item.location_info or 'N/A'}"
                )
            inventory_context = "\n".join(inventory_context_parts)
        
        prompt = f"{inventory_context}\n\nQuestion utilisateur : {user_query}"
        payload = {
            'model': self.model_completion,
            'prompt': prompt,
            'stream': False
        }
        
        try:
            response = requests.post(self.completion_url, json=payload)
            response.raise_for_status()
            return self._parse_ollama_response(response.json(), return_str=True)
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de l'appel à l'API Ollama (Chat): {e}")
            raise Exception(f"Erreur de communication avec l'API Ollama: {e}")
    
    def process_audio_file(self, audio_file, audio_mime_type='audio/webm', is_inventory=False, locations_context=None, temporary_only=False):
        """
        Traite un fichier audio et en extrait les informations (articles ou articles+emplacements)
        Utilise faster-whisper-server pour la transcription.
        Args:
            audio_file: Fichier audio à traiter
            is_inventory (bool): Si True, extrait les articles avec leurs emplacements
            locations_context (dict): Contexte des emplacements (requis si is_inventory=True)
        Returns:
            list: Liste d'articles (ou articles avec emplacements)
        """
        try:
            mime_to_suffix = {
                'audio/webm': '.webm',
                'audio/mp4': '.mp4',
                'audio/mpeg': '.mp3', # ou .mpeg
                'audio/ogg': '.ogg', # ou .oga
                'audio/wav': '.wav',
                'audio/flac': '.flac',
                'audio/x-m4a': '.m4a', # Pour être sûr
                'audio/m4a': '.m4a'
            }
            # Extraire le type MIME de base sans les paramètres (ex: 'audio/webm' de 'audio/webm;codecs=opus')
            base_mime_type = audio_mime_type.split(';')[0].strip()
            suffix = mime_to_suffix.get(base_mime_type, '.raw') # Default à .raw si inconnu
            logger.debug(f"Utilisation du suffixe '{suffix}' pour le mimeType '{audio_mime_type}' (base: '{base_mime_type}')")

            # Créer un fichier temporaire pour stocker l'audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                audio_path = temp_file.name
                audio_file.save(audio_path)

            # Transcription via faster-whisper-server
            transcription = self.transcribe_audio(audio_path, audio_mime_type)

            # Nettoyer le fichier temporaire
            if os.path.exists(audio_path):
                os.unlink(audio_path)

            # Extraction des articles
            if is_inventory:
                if not locations_context:
                    raise ValueError("Le contexte des emplacements est requis pour l'extraction d'inventaire.")
                return self.extract_items_with_locations(transcription, locations_context)
            else:
                return self.extract_items_from_text(transcription)
        except Exception as e:
            # En cas d'erreur, s'assurer que le fichier temporaire est supprimé
            if 'audio_path' in locals() and os.path.exists(audio_path):
                os.unlink(audio_path)
            raise e
    
    def _parse_ollama_response(self, response_json, return_str=False):
        """
        Analyse la réponse Ollama pour en extraire le contenu
        
        Args:
            response_json (dict): Réponse JSON d'Ollama
            
        Returns:
            list: Liste d'articles ou d'articles avec emplacements
        """
        try:
            logger.debug(f"Réponse brute d'Ollama: {response_json}")
            # Ollama retourne {'response': '...'}
            content = response_json.get('response', '').strip()
            logger.debug(f"Contenu extrait: {content}")
            
            if not content:
                logger.error("ERREUR: Contenu vide dans la réponse Ollama")
                return [] if not return_str else ""
            
            if return_str:
                return content
            
            # Nettoyage du contenu avant parsing
            content = content.replace('```json', '').replace('```', '').strip()
            try:
                items = json.loads(content)
                
                # Vérifier si le résultat est bien une liste
                if not isinstance(items, list):
                    logger.error(f"ERREUR: Le résultat n'est pas une liste mais {type(items)}")
                    # Essayer de voir si le résultat est un dictionnaire contenant la liste
                    if isinstance(items, dict) and any(isinstance(items.get(k), list) for k in items):
                        for k, v in items.items():
                            if isinstance(v, list):
                                logger.debug(f"Extraction de la liste depuis la clé '{k}'")
                                items = v
                                break
                    else:
                        return []
                
                # Mettre une majuscule à la première lettre de chaque article
                for item in items:
                    if 'name' in item and item['name']:
                        item['name'] = item['name'][0].upper() + item['name'][1:] if len(item['name']) > 1 else item['name'].upper()
                
                # Vérifier que tous les items ont les champs requis
                valid_items = []
                for item in items:
                    # Pour les articles temporaires, seul le nom est requis
                    if 'name' in item and item['name']:
                        # Si c'est un article avec emplacement, vérifier les champs requis
                        if all(k in item for k in ['zone_id', 'furniture_id', 'drawer_id']):
                            valid_items.append(item)
                        # Si c'est un article temporaire (sans emplacement), l'ajouter tel quel
                        elif not any(k in item for k in ['zone_id', 'furniture_id', 'drawer_id']):
                            valid_items.append(item)
                        else:
                            logger.warning(f"AVERTISSEMENT: Article avec emplacement incomplet ignoré: {item}")
                    else:
                        logger.warning(f"AVERTISSEMENT: Article sans nom ignoré: {item}")
                
                logger.debug(f"Nombre d'items valides après vérification: {len(valid_items)}")
                return valid_items
            except json.JSONDecodeError as e:
                logger.debug(f"Erreur JSON direct: {e}. Essai d'extraction par regex...")
                # Si ça échoue, essayer d'extraire le JSON de la réponse
                pattern = r'\[\s*{.*}\s*\]'
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    items_json = match.group(0)
                    logger.debug(f"JSON extrait par regex: {items_json}")
                    try:
                        items = json.loads(items_json)
                        for item in items:
                            if 'name' in item and item['name']:
                                item['name'] = item['name'][0].upper() + item['name'][1:] if len(item['name']) > 1 else item['name'].upper()
                        
                        valid_items = []
                        for item in items:
                            if 'name' in item and item['name']:
                                if all(k in item for k in ['zone_id', 'furniture_id', 'drawer_id']):
                                    valid_items.append(item)
                                elif not any(k in item for k in ['zone_id', 'furniture_id', 'drawer_id']):
                                    valid_items.append(item)
                                else:
                                    logger.warning(f"AVERTISSEMENT: Article avec emplacement incomplet ignoré: {item}")
                            else:
                                logger.warning(f"AVERTISSEMENT: Article sans nom ignoré: {item}")
                        
                        logger.debug(f"Nombre d'items valides après vérification: {len(valid_items)}")
                        return valid_items
                    except json.JSONDecodeError as e:
                        logger.error(f"Erreur lors du parsing du JSON extrait: {e}")
                        return []
                else:
                    logger.debug("Aucun JSON trouvé dans la réponse par regex")
                    return []
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de la réponse Ollama: {e}")
            return [] if not return_str else ""
    
    def _format_zones_context(self, zones):
        """
        Formate les données de zone pour le contexte
        """
        if not zones:
            logger.warning("Aucune zone fournie dans le contexte")
            return "Aucune zone disponible"
            
        formatted = '\n'.join([f"{zone['id']}: {zone['name']}" for zone in zones])
        logger.debug(f"Contexte de zones formaté: {formatted}")
        return formatted
    
    def _format_furniture_context(self, furniture):
        """
        Formate les données de meuble pour le contexte
        """
        if not furniture:
            logger.warning("Aucun meuble fourni dans le contexte")
            return "Aucun meuble disponible"
            
        formatted = '\n'.join([f"{item['id']}: {item['name']} (Zone: {item['zone_id']})" for item in furniture])
        logger.debug(f"Contexte de meubles formaté: {formatted}")
        return formatted
    
    def _format_drawers_context(self, drawers):
        """
        Formate les données de tiroir pour le contexte
        """
        if not drawers:
            logger.warning("Aucun tiroir fourni dans le contexte")
            return "Aucun tiroir disponible"
            
        formatted = '\n'.join([f"{drawer['id']}: {drawer['name']} (Meuble: {drawer['furniture_id']})" for drawer in drawers])
        logger.debug(f"Contexte de tiroirs formaté: {formatted}")
        return formatted



    def _build_batch_comparison_prompt(self, recognized_names, db_items):
        """
        Construit le prompt pour la comparaison sémantique en batch.
        """
        recognized_names_json = json.dumps(recognized_names, indent=2, ensure_ascii=False)
        db_items_json = json.dumps(db_items, indent=2, ensure_ascii=False)

        return (
            f"Vous êtes un assistant IA expert en gestion d'inventaire. Votre tâche est de comparer une liste d'articles dictés par un utilisateur avec une liste d'articles existants dans une base de données. "
            f"Vous devez identifier quels articles dictés correspondent à des articles existants, même en cas de différences mineures comme les pluriels, les fautes de frappe ou des variations de formulation.\n\n"
            f"Voici la liste des articles dictés par l'utilisateur :\n{recognized_names_json}\n\n"
            f"Voici la liste des articles conventionnels de la base de données :\n{db_items_json}\n\n"
            f"Veuillez analyser ces deux listes et retourner un objet JSON. Cet objet doit contenir une seule clé, 'matched_items', qui est une liste de résultats pour CHAQUE article dicté. "
            f"Chaque objet dans la liste doit avoir la structure suivante :\n"
            f"- \"original_name\": Le nom de l'article tel qu'il a été dicté.\n"
            f"- \"is_conventional\": Un booléen (true/false) indiquant s'il correspond à un article conventionnel.\n"
            f"- \"db_id\": L'ID de l'article de la base de données correspondant (null si aucune correspondance).\n"
            f"- \"db_name\": Le nom officiel de l'article de la base de données (null si aucune correspondance).\n\n"
            f"Si un article dicté comme 'Gauffres au sesames' correspond à 'Gaufre au sésame' (ID 12) dans la base de données, le résultat doit être :\n"
            f"{{\"original_name\": \"Gauffres au sesames\", \"is_conventional\": true, \"db_id\": 12, \"db_name\": \"Gaufre au sésame\"}}\n\n"
            f"Si un article dicté n'a pas de correspondance claire, marquez-le comme non conventionnel. Ne renvoyez que l'objet JSON, sans texte ou explication supplémentaire."
        )

    def compare_with_existing_items(self, items):
        """
        Compare une liste d'articles reconnus avec des articles conventionnels de la base de données en un seul appel API, 
        en utilisant l'IA pour trouver des correspondances sémantiques.
        """

        recognized_item_names = [item['name'] for item in items if item.get('name')]
        if not recognized_item_names:
            logger.info("Aucun article reconnu avec un nom à comparer.")
            for item in items:
                item['is_conventional'] = False
            return items

        try:
            db_conventional_items = Item.query.filter_by(is_temporary=False).all()
            if not db_conventional_items:
                logger.info("Aucun article conventionnel dans la BD. Tous les articles sont marqués comme temporaires.")
                for item in items:
                    item['is_conventional'] = False
                return items

            db_items_for_prompt = [{"id": item.id, "name": item.name} for item in db_conventional_items]
            prompt = self._build_batch_comparison_prompt(recognized_item_names, db_items_for_prompt)

            payload = {
                'model': self.model_completion,
                'prompt': (
                    "Vous êtes un assistant IA expert en JSON qui ne répond que par du JSON valide.\n" + prompt
                ),
                'stream': False
            }

            logger.info("Envoi de la requête de comparaison en batch à Ollama...")
            response = requests.post(self.completion_url, json=payload, timeout=45)
            response.raise_for_status()

            ai_results_str = response.json().get('response', '')
            logger.debug(f"Réponse JSON brute de l'IA: {ai_results_str}")

            matched_results = json.loads(ai_results_str).get("matched_items", [])
            match_map = {str(result['original_name']).lower(): result for result in matched_results}

            for item in items:
                item_name_lower = str(item.get('name', '')).lower()
                ai_match = match_map.get(item_name_lower)

                if ai_match and ai_match.get('is_conventional'):
                    item['is_conventional'] = True
                    item['db_id'] = ai_match['db_id']
                    item['name'] = ai_match['db_name']

                    matched_db_item = next((db_item for db_item in db_conventional_items if db_item.id == ai_match['db_id']), None)
                    if matched_db_item:
                        item['zone_id'] = matched_db_item.zone_id
                        item['furniture_id'] = matched_db_item.furniture_id
                        item['drawer_id'] = matched_db_item.drawer_id
                        item['location_info'] = matched_db_item.location_info
                        logger.debug(f"Correspondance trouvée: '{item_name_lower}' -> '{item['name']}' (ID: {item['db_id']})")
                else:
                    item['is_conventional'] = False
                    logger.debug(f"Aucune correspondance trouvée pour: '{item_name_lower}'")

            conventional_count = sum(1 for item in items if item.get('is_conventional'))
            logger.info(f"Comparaison terminée: {len(items)} articles traités, {conventional_count} conventionnels.")
            return items

        except requests.exceptions.Timeout:
            logger.error("Erreur: La requête vers l'API Ollama a expiré.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur: Problème de connexion avec l'API Ollama: {e}")
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Erreur: Impossible de parser la réponse JSON de l'IA: {e}")
        except Exception as e:
            logger.error(f"Erreur majeure inattendue lors de la comparaison en batch: {e}")

        logger.warning("Fallback: tous les articles sont marqués comme temporaires en raison d'une erreur.")
        for item in items:
            item['is_conventional'] = False
        return items

# Instance singleton du service
ai_service = AIService()
