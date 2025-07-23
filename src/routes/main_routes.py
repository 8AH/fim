from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from src.models import db
from src.models.user import User
from src.models.item import Item
from src.models.borrow import Borrow
from src.models.supplier import Supplier
from datetime import datetime

# Création du blueprint
main_bp = Blueprint('main', __name__)

# Route principale
@main_bp.route('/')
def index():
    """
    Page d'accueil - Redirige vers le tableau de bord si l'utilisateur est connecté,
    ou vers la page de login sinon
    """
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    
    users = db.session.query(User).order_by(User.name).all()
    return render_template('index.html', users=users)

# Page de connexion
@main_bp.route('/login', methods=['POST'])
def login():
    """
    Gère la connexion d'un utilisateur
    """
    user_name = request.form.get('user_name')
    user_id = request.form.get('user_id')  # Pour compatibilité avec le formulaire de sélection
    
    # Priorité à user_id s'il est fourni
    if user_id:
        user = db.session.get(User, user_id)
    elif user_name:
        # Rechercher l'utilisateur par son nom
        user = db.session.query(User).filter(User.name == user_name).first()
    else:
        flash('Veuillez entrer votre nom', 'danger')
        return redirect(url_for('main.index'))
    
    if not user:
        # Créer un nouvel utilisateur si le nom n'existe pas
        if user_name:
            user = User(name=user_name)
            db.session.add(user)
            db.session.commit()
        else:
            flash('Utilisateur non trouvé', 'danger')
            return redirect(url_for('main.index'))
    
    # Connecter l'utilisateur
    session['user_id'] = user.id
    session['user_name'] = user.name
    
    flash(f'Bienvenue, {user.name}!', 'success')
    return redirect(url_for('main.dashboard'))

# Connexion rapide avec ID
@main_bp.route('/login/<int:user_id>')
def login_with_id(user_id):
    """
    Connexion rapide avec l'ID de l'utilisateur
    """
    user = db.session.get(User, user_id)
    if not user:
        flash('Utilisateur non trouvé', 'danger')
        return redirect(url_for('main.index'))
    
    session['user_id'] = user.id
    session['user_name'] = user.name
    
    flash(f'Bienvenue, {user.name}!', 'success')
    return redirect(url_for('main.dashboard'))

# Tableau de bord
@main_bp.route('/dashboard')
def dashboard():
    """
    Tableau de bord principal de l'application
    """
    if 'user_id' not in session:
        flash('Veuillez vous connecter', 'danger')
        return redirect(url_for('main.index'))
    
    user_id = session['user_id']
    user = db.session.get(User, user_id)
    
    if not user:
        flash('Utilisateur non trouvé', 'danger')
        session.clear()
        return redirect(url_for('main.index'))
    
    # Récupérer les articles disponibles (non empruntés)
    subquery = db.session.query(Borrow.item_id).filter(Borrow.return_date == None)
    available_items = db.session.query(Item).filter(
        ~Item.id.in_(subquery)
    ).order_by(Item.name).all()
    
    return render_template('dashboard.html', 
                           user=user, 
                           available_items=available_items)

# Mes emprunts
@main_bp.route('/my-borrows')
def my_borrows():
    """
    Page affichant tous les emprunts en cours de l'utilisateur
    """
    if 'user_id' not in session:
        flash('Veuillez vous connecter', 'danger')
        return redirect(url_for('main.index'))
    
    user_id = session['user_id']
    user = db.session.get(User, user_id)
    
    if not user:
        flash('Utilisateur non trouvé', 'danger')
        session.clear()
        return redirect(url_for('main.index'))
    
    # Récupérer les emprunts en cours de l'utilisateur
    current_borrows = db.session.query(Borrow).filter(
        Borrow.user_id == user_id,
        Borrow.return_date == None
    ).all()
    
    return render_template('my_borrows.html', 
                           user=user, 
                           current_borrows=current_borrows)

# Déconnexion
@main_bp.route('/logout')
def logout():
    """
    Déconnecte l'utilisateur et nettoie la session
    """
    session.clear()
    flash('Vous avez été déconnecté', 'info')
    return redirect(url_for('main.index'))

# Page Chat Inventaire
@main_bp.route('/chat-inventaire')
def chat_inventaire():
    """
    Page pour interagir avec l'IA concernant l'inventaire.
    """
    if 'user_id' not in session:
        flash('Veuillez vous connecter pour accéder à cette fonctionnalité.', 'warning')
        return redirect(url_for('main.index'))
    
    return render_template('chat_inventaire.html')
