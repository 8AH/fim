from flask import Blueprint, request, jsonify, session
from src.models import db
from src.models.item import Item
from src.models.supplier import Supplier
from src.models.location import Zone, Furniture, Drawer

# Création du blueprint
items_api_bp = Blueprint('items_api', __name__, url_prefix='/api/items')

# Liste des articles
@items_api_bp.route('', methods=['GET'])
def get_items():
    """
    Retourne la liste des articles (filtrable)
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    
    # Récupérer les paramètres de filtrage
    search = request.args.get('search', '')
    
    # Construire la requête de base
    query = db.session.query(Item)
    
    # Appliquer les filtres
    if search:
        query = query.filter(Item.name.ilike(f'%{search}%'))
    
    # Récupérer les résultats
    items = query.order_by(Item.name).all()
    
    # Formater les résultats
    results = []
    for item in items:
        results.append({
            'id': item.id,
            'name': item.name,
            'supplier': item.supplier_id,
            'zone_id': item.zone_id,
            'furniture_id': item.furniture_id,
            'drawer_id': item.drawer_id,
            'location_info': item.location_info,
            'is_temporary': item.is_temporary
        })
    
    return jsonify(results)

# Détails d'un article
@items_api_bp.route('/<int:item_id>', methods=['GET'])
def get_item(item_id):
    """
    Retourne les détails d'un article
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    
    item = db.session.get(Item, item_id)
    if not item:
        return jsonify({'error': 'Article non trouvé'}), 404
    
    result = {
        'id': item.id,
        'name': item.name,
        'supplier_id': item.supplier_id,
        'zone_id': item.zone_id,
        'furniture_id': item.furniture_id,
        'drawer_id': item.drawer_id,
        'location_info': item.location_info,
        'is_temporary': item.is_temporary
    }

    # Ajouter les noms de zone/mobilier/tiroir pour la cohérence avec l'API d'ajout
    # et pour faciliter l'affichage côté client.
    if item.supplier_id:
        result['supplier_name'] = item.supplier_rel.name if item.supplier_rel else None

    if item.zone_rel:
        result['zone_name'] = item.zone_rel.name
    if item.furniture_rel:
        result['furniture_name'] = item.furniture_rel.name
    if item.drawer_rel:
        result['drawer_name'] = item.drawer_rel.name
            
    return jsonify({'item': result}) # Renvoyer l'objet sous la clé 'item'

# Ajout d'articles en batch
@items_api_bp.route('/batch', methods=['POST'])
def add_items_batch():
    """
    Endpoint pour ajouter plusieurs articles à l'inventaire en une seule requête
    """
    data = request.json
    
    if not data or 'items' not in data or not isinstance(data['items'], list):
        return jsonify({'error': 'Données invalides'}), 400
    
    items = data['items']
    added_count = 0
    
    try:
        for item_data in items:
            # Vérifier que toutes les informations requises sont présentes
            if not all(key in item_data for key in ['name', 'zone_id', 'furniture_id', 'drawer_id']):
                continue
            
            # Créer un nouvel article
            new_item = Item(
                name=item_data['name'],
                is_temporary=False,  # Articles ajoutés par batch sont toujours permanents
                zone_id=item_data['zone_id'],
                furniture_id=item_data['furniture_id'],
                drawer_id=item_data['drawer_id'],
                # Champs texte pour la compatibilité
                zone=item_data.get('zone_name', ''),
                mobilier=item_data.get('furniture_name', ''),
                niveau_tiroir=item_data.get('drawer_name', '')
            )
            
            db.session.add(new_item)
            added_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{added_count} article(s) ajouté(s) avec succès',
            'added_count': added_count
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Route principale pour ajouter des articles
@items_api_bp.route('/add', methods=['POST'])
def add_item():
    """
    API unifiée pour ajouter des articles (temporaires ou permanents)
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    
    data = request.json
    name = data.get('name', '').strip()
    is_temporary = data.get('is_temporary', False)
    
    if not name:
        return jsonify({'error': 'Le nom de l\'article est requis'}), 400
    
    try:
        if is_temporary:
            # Création d'un article temporaire avec le modèle unifié
            new_item = Item(
                name=name,
                is_temporary=True
            )
            db.session.add(new_item)
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'item': {
                    'id': new_item.id,
                    'name': new_item.name,
                    'is_temporary': True,
                    'location_info': new_item.location_info
                }
            })
        else:
            # Création d'un article permanent avec emplacement
            supplier_id = data.get('supplier_id')
            zone_id = data.get('zone_id')
            furniture_id = data.get('furniture_id')
            drawer_id = data.get('drawer_id')
            
            # Vérifier que les IDs de localisation sont présents
            if not supplier_id or not zone_id or not furniture_id or not drawer_id:
                return jsonify({'error': 'Les informations de localisation et du fournisseur sont obligatoires pour un article permanent'}), 400
            
            # Convertir les IDs de localisation en entiers
            try:
                supplier_id = int(supplier_id)
                zone_id = int(zone_id)
                furniture_id = int(furniture_id)
                drawer_id = int(drawer_id)
            except (ValueError, TypeError):
                return jsonify({'error': 'Les IDs de localisation (zone, meuble, tiroir) ou du fournisseur doivent être des entiers valides.'}), 400

            # Vérifier si un article conventionnel identique existe déjà
            existing_item = Item.query.filter_by(
                name=name,
                supplier_id=supplier_id,
                zone_id=zone_id,
                furniture_id=furniture_id,
                drawer_id=drawer_id,
                is_temporary=False
            ).first()

            if existing_item:
                return jsonify({
                    'error': f"Un article nommé '{name}' existe déjà à cet emplacement.",
                    'item': { # Renvoyer l'article existant peut être utile pour le client
                        'id': existing_item.id,
                        'name': existing_item.name,
                        'supplier_id': existing_item.supplier_id,
                        'zone_id': existing_item.zone_id,
                        'furniture_id': existing_item.furniture_id,
                        'drawer_id': existing_item.drawer_id,
                        'is_temporary': False,
                        'location_info': existing_item.location_info
                    }
                }), 409 # HTTP 409 Conflict
            
            # Vérifier que le fournisseur existe
            supplier_obj = db.session.get(Supplier, supplier_id)
            if not supplier_obj:
                return jsonify({'error': f'Le fournisseur avec l\'ID {supplier_id} n\'existe pas'}), 400

            # Vérifier que les entités de localisation existent
            zone_obj = db.session.get(Zone, zone_id)
            if not zone_obj:
                return jsonify({'error': f'La zone avec l\'ID {zone_id} n\'existe pas'}), 400
            
            furniture_obj = db.session.get(Furniture, furniture_id)
            if not furniture_obj:
                return jsonify({'error': f'Le meuble avec l\'ID {furniture_id} n\'existe pas'}), 400
            
            drawer_obj = db.session.get(Drawer, drawer_id)
            if not drawer_obj:
                return jsonify({'error': f'Le tiroir avec l\'ID {drawer_id} n\'existe pas'}), 400
            
            # Créer l'article permanent avec le modèle unifié
            new_item = Item(
                name=name,
                is_temporary=False,
                supplier_id=supplier_id,
                # Clés étrangères pour les emplacements
                zone_id=zone_id,
                furniture_id=furniture_id,
                drawer_id=drawer_id,
                # Champs texte pour la compatibilité
                zone=zone_obj.name,
                mobilier=furniture_obj.name,
                niveau_tiroir=drawer_obj.name
            )
            
            db.session.add(new_item)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'item': {
                    'id': new_item.id,
                    'name': new_item.name,
                    'supplier_id': new_item.supplier_id,
                    'zone_id': new_item.zone_id,
                    'furniture_id': new_item.furniture_id,
                    'drawer_id': new_item.drawer_id,
                    'is_temporary': False,
                    'location_info': new_item.location_info
                }
            })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Note: Nous utilisons la route /add avec le paramètre is_temporary=true pour les articles temporaires
# de la reconnaissance vocale, ce qui évite la duplication de code

# Route pour obtenir le nombre d'articles ajoutés aujourd'hui
@items_api_bp.route('/count-today', methods=['GET'])
def count_items_today():
    """
    Retourne le nombre d'articles ajoutés aujourd'hui
    """
    from datetime import datetime, time
    
    # Obtenir la date d'aujourd'hui (début et fin de journée)
    today_start = datetime.combine(datetime.today(), time.min)
    today_end = datetime.combine(datetime.today(), time.max)
    
    # Compter les articles ajoutés aujourd'hui
    count = db.session.query(Item).filter(
        Item.created_at >= today_start,
        Item.created_at <= today_end
    ).count()
    
    return jsonify({'count': count})
