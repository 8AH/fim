"""
Routes unifiées pour les fonctionnalités d'IA et de reconnaissance vocale
"""
import json
from flask import Blueprint, request, jsonify, current_app, session # Ajout de session
from src.services.ai_service import ai_service # ai_service est l'instance, AIService est la classe
from src.services.ai_service import AIService # Import de la classe pour instanciation si nécessaire ailleurs
from src.models import db
from src.models.item import Item # Item est déjà importé
from src.models.supplier import Supplier  # Import du modèle Supplier
from sqlalchemy import func

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai') # Ajout du préfixe d'URL

@ai_bp.route('/voice-recognition', methods=['POST']) # Suppression de /api/ du chemin
def voice_recognition():
    """
    Endpoint pour traiter l'audio et extraire les noms d'articles
    """
    if 'audio' not in request.files:
        return jsonify({'error': 'Aucun fichier audio n\'a été fourni'}), 400
    
    audio_file = request.files['audio']
    audio_mime_type = request.form.get('mimeType', 'audio/webm') # Default au cas où
    
    if audio_file.filename == '':
        return jsonify({'error': 'Nom de fichier audio invalide'}), 400
    
    temporary_only = request.form.get('temporary_only', 'false').lower() == 'true'
    current_app.logger.debug(f"[voice_recognition] temporary_only flag from form: {request.form.get('temporary_only')}, parsed as: {temporary_only}")
    
    try:
        # Log du type MIME pour le débogage
        current_app.logger.info(f"Utilisation du suffixe '{ai_service.getFileExtension(audio_mime_type)}' pour le mimeType '{audio_mime_type}' (base: '{audio_mime_type.split(';')[0] if ';' in audio_mime_type else audio_mime_type}')")
        
        # Préparer le contexte avec les fournisseurs
        context = {
            'zones': [],
            'furniture': [],
            'drawers': [],
            'suppliers': [],
        }
        current_app.logger.debug(f"Contexte préparé pour l'extraction: {json.dumps(context, indent=2)}")
        
        # Utiliser le service AI pour traiter l'audio avec le contexte
        items = ai_service.process_audio_file(audio_file, audio_mime_type=audio_mime_type, locations_context=context)
        
        # Log détaillé du résultat pour le débogage
        current_app.logger.info(f"Reconnaissance vocale réussie: {len(items)} articles identifiés")
        
        # Vérifier la structure des données
        import json
        current_app.logger.info(f"Structure des données: {json.dumps(items, indent=2)}")
        
        # Vérifier que chaque article a un ID et un nom
        for i, item in enumerate(items):
            current_app.logger.info(f"Article {i}: id={item.get('id', 'MANQUANT')}, name={item.get('name', 'MANQUANT')}")
        
        # Créer la réponse JSON
        response_data = {'items': items}
        current_app.logger.info(f"Réponse JSON finale: {json.dumps(response_data, indent=2)}")
        
        return jsonify(response_data)
    
    except Exception as e:
        error_message = str(e)
        error_type = "server_error"
        
        # Catégoriser les erreurs pour une meilleure gestion côté client
        if "API OpenAI" in error_message or "service d'IA" in error_message:
            error_type = "ai_service_error"
        elif "fichier audio" in error_message:
            error_type = "audio_format_error"
        
        current_app.logger.error(f"Erreur dans voice_recognition: {error_message}", exc_info=True)
        return jsonify({
            'error': error_message,
            'error_type': error_type
        }), 500

@ai_bp.route('/voice-quantity-update', methods=['POST'])
def voice_quantity_update():
    """
    Endpoint to update item quantity via voice command.
    """
    if 'audio' not in request.files:
        return jsonify({'error': 'Aucun fichier audio n\'a été fourni'}), 400

    audio_file = request.files['audio']
    audio_mime_type = request.form.get('mimeType', 'audio/webm')

    try:
        import difflib
        # Process audio to get action details
        update_data = ai_service.process_audio_for_quantity_update(audio_file, audio_mime_type)
        current_app.logger.info(f"Données de mise à jour de quantité extraites: {update_data}")

        if not update_data or 'error' in update_data:
            return jsonify({'error': update_data.get('error', 'Impossible d\'extraire les informations de la commande vocale.')}), 400

        item_name = update_data.get('name')
        action = update_data.get('action')
        quantity_change = update_data.get('quantity')

        if not all([item_name, action, isinstance(quantity_change, int)]):
            return jsonify({'error': 'Informations manquantes ou invalides (nom, action, quantité) pour la mise à jour.'}), 400

        # Recherche exacte (insensible à la casse)
        item = Item.query.filter(func.lower(Item.name) == func.lower(item_name), Item.is_temporary == False).first()

        # Si non trouvé, recherche tolérante (similarité)
        if not item:
            # Récupérer tous les articles non temporaires
            all_items = Item.query.filter(Item.is_temporary == False).all()
            # Calculer la similarité avec chaque nom d'article
            names = [i.name for i in all_items]
            matches = difflib.get_close_matches(item_name, names, n=1, cutoff=0.8)
            if matches:
                # Prendre le premier match
                matched_name = matches[0]
                item = next((i for i in all_items if i.name == matched_name), None)
                current_app.logger.info(f"Aucune correspondance exacte, mais correspondance approchée trouvée: '{item_name}' ≈ '{matched_name}' (ID: {item.id})")
            else:
                return jsonify({'error': f"L'article '{item_name}' n\'a pas été trouvé dans l'inventaire (même en recherche approchée)."}), 404

        # Déterminer la nouvelle quantité et le message
        new_quantity = original_quantity
        if action == 'add':
            new_quantity += quantity_change
            action_text = f"Ajout de {quantity_change}"
        elif action == 'reduce':
            if original_quantity >= quantity_change:
                new_quantity -= quantity_change
                action_text = f"Réduction de {quantity_change}"
            else:
                return jsonify({'error': f"Quantité insuffisante pour '{item.name}'. Quantité actuelle : {original_quantity}, Réduction demandée : {quantity_change}."}), 400
        elif action == 'set':
            new_quantity = quantity_change
            action_text = f"Fixé à {quantity_change}"
        else:
            return jsonify({'error': f"Action '{action}' non reconnue."}), 400

        # Rediriger vers la page de confirmation au lieu de commiter directement
        return jsonify({
            'success': True,
            'redirect_url': url_for('admin.quantity_update_confirmation', 
                                    item_id=item.id, 
                                    new_quantity=new_quantity,
                                    old_quantity=original_quantity,
                                    action_text=action_text)
        })

    except Exception as e:
        current_app.logger.error(f"Erreur dans voice_quantity_update: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/inventory-voice', methods=['POST']) # Suppression de /api/ du chemin
def inventory_voice_recognition():
    """
    Endpoint pour traiter l'audio et extraire les articles avec leurs emplacements
    """
    if 'audio' not in request.files:
        return jsonify({'error': 'Aucun fichier audio n\'a été fourni'}), 400
    
    audio_file = request.files['audio']
    audio_mime_type = request.form.get('mimeType', 'audio/webm') # Default au cas où
    
    if audio_file.filename == '':
        return jsonify({'error': 'Nom de fichier audio invalide'}), 400
    
    # Récupérer le contexte des emplacements
    context = {}
    if 'context' in request.form:
        try:
            context = json.loads(request.form['context'])
        except:
            pass

    try:
        # Utiliser le service AI pour traiter l'audio avec contexte d'emplacements et fournisseurs
        items = ai_service.process_audio_file(audio_file, is_inventory=True, locations_context=context, audio_mime_type=audio_mime_type)
        return jsonify({'items': items})

    except Exception as e:
        current_app.logger.error(f"Erreur dans inventory_voice_recognition: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500



@ai_bp.route('/chat/inventory', methods=['POST'])
def handle_inventory_chat():
    if 'user_id' not in session:
        return jsonify({'error': 'Authentification requise'}), 401

    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({'error': 'Données de requête invalides ou manquantes'}), 400
        
    user_query = data.get('query')

    if not user_query:
        return jsonify({'error': 'La requête ne peut pas être vide'}), 400

    # ai_service est déjà l'instance de AIService importée au niveau du module
    try:
        all_items = Item.query.all() # Item est déjà importé
        ai_response_text = ai_service.get_inventory_chat_response(all_items, user_query)
        return jsonify({'response': ai_response_text})

    except Exception as e:
        current_app.logger.error(f"Erreur lors de l'appel à AIService pour le chat: {e}", exc_info=True)
        return jsonify({'error': f'Erreur du service IA: {str(e)}'}), 500
