from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file, Response, current_app
from functools import wraps
import csv
import io
import os
import tempfile
from datetime import datetime
from fpdf import FPDF
from src.models import db
from src.models.user import User
from src.models.item import Item

# Création du blueprint
reports_bp = Blueprint('reports', __name__)

# Export de la liste des articles en CSV
@reports_bp.route('/export_items_csv')
def export_items_csv():
    """
    Exporte la liste des articles au format CSV
    """
    if 'user_id' not in session:
        flash('Veuillez vous connecter', 'danger')
        return redirect(url_for('main.index'))
    
    # Récupérer tous les articles
    items = db.session.query(Item).order_by(Item.name).all()
    
    # Créer un fichier CSV en mémoire
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Écrire l'en-tête
    writer.writerow(['ID', 'Nom', 'Zone', 'Meuble', 'Tiroir/Niveau', 'Temporaire'])
    
    # Écrire les lignes de données
    for item in items:
        writer.writerow([
            item.id,
            item.name,
            item.supplier,
            item.zone or '',
            item.mobilier or '',
            item.niveau_tiroir or '',
            'Oui' if item.is_temporary else 'Non'
        ])
    
    # Préparer la réponse
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=articles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

# Décorateur pour supprimer un fichier après la réponse
def after_this_request(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        request._after_this_request_functions.append(lambda: func(*args, **kwargs))
        return response
    return wrapper

@reports_bp.route('/all_items_pdf')
def generate_all_items_pdf():
    """Génère un PDF listant tous les articles (matériel)."""
    if 'user_id' not in session: # Ajout de la vérification de session
        flash('Veuillez vous connecter pour accéder à cette fonctionnalité.', 'warning')
        return redirect(url_for('main.login')) # Ou une autre page de login appropriée
    try:
        items = Item.query.order_by(Item.name).all()

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Titre
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Liste de tout le matériel', 0, 1, 'C')
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 10, f'Date de génération: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}', 0, 1, 'C')
        pdf.ln(10)

        if not items:
            pdf.set_font('Arial', '', 12)
            pdf.cell(0, 10, 'Aucun article trouvé.', 0, 1)
        else:
            # En-têtes de tableau
            pdf.set_font('Arial', 'B', 10)
            header_height = 7
            col_widths = {'id': 15, 'name': 50, 'supplier': 35, 'location': 60, 'type': 20, 'created_at': 25}

            pdf.cell(col_widths['id'], header_height, 'ID', 1, 0, 'C')
            pdf.cell(col_widths['name'], header_height, 'Nom', 1, 0, 'C')
            pdf.cell(col_widths['supplier'], header_height, 'Fournisseur', 1, 0, 'C')
            pdf.cell(col_widths['location'], header_height, 'Emplacement', 1, 0, 'C')
            pdf.cell(col_widths['type'], header_height, 'Type', 1, 0, 'C')
            pdf.cell(col_widths['created_at'], header_height, 'Créé le', 1, 1, 'C')

            # Données du tableau
            pdf.set_font('Arial', '', 9)
            row_height = 6
            for item in items:
                item_type = "Temporaire" if item.is_temporary else "Permanent"
                created_date = item.created_at.strftime("%d/%m/%y") if item.created_at else "N/A"
                location_text = item.location_info if item.location_info else "N/A"
                supplier = item.supplier if hasattr(item, 'supplier') and item.supplier else "N/A"

                # On prépare les contenus susceptibles d'être longs
                cell_values = [
                    str(item.id),
                    item.name,
                    supplier,
                    location_text,
                    item_type,
                    created_date
                ]
                # Largeurs dans l'ordre
                widths = [col_widths['id'], col_widths['name'], col_widths['supplier'], col_widths['location'], col_widths['type'], col_widths['created_at']]
                aligns = ['C', 'L', 'L', 'L', 'C', 'C']

                # Calculer la hauteur maximale nécessaire pour cette ligne
                # On utilise multi_cell pour les colonnes texte (name, supplier, location)
                # On découpe la ligne en 3 parties : id, puis les 3 colonnes longues, puis type et date
                y_before = pdf.get_y()
                x_start = pdf.get_x()

                # ID
                pdf.multi_cell(widths[0], row_height, cell_values[0], border=1, align=aligns[0], max_line_height=row_height)
                x_after_id = x_start + widths[0]
                pdf.set_xy(x_after_id, y_before)

                # Nom
                y_nom = pdf.get_y()
                pdf.multi_cell(widths[1], row_height, cell_values[1], border=1, align=aligns[1], max_line_height=row_height)
                h_nom = pdf.get_y() - y_nom
                x_after_nom = x_after_id + widths[1]
                pdf.set_xy(x_after_nom, y_before)

                # Fournisseur
                y_fourn = pdf.get_y()
                pdf.multi_cell(widths[2], row_height, cell_values[2], border=1, align=aligns[2], max_line_height=row_height)
                h_fourn = pdf.get_y() - y_fourn
                x_after_fourn = x_after_nom + widths[2]
                pdf.set_xy(x_after_fourn, y_before)

                # Emplacement
                y_loc = pdf.get_y()
                pdf.multi_cell(widths[3], row_height, cell_values[3], border=1, align=aligns[3], max_line_height=row_height)
                h_loc = pdf.get_y() - y_loc
                x_after_loc = x_after_fourn + widths[3]
                # Hauteur max des colonnes multi_cell
                max_h = max(h_nom, h_fourn, h_loc, row_height)

                # Type
                pdf.set_xy(x_after_loc, y_before)
                pdf.multi_cell(widths[4], max_h, cell_values[4], border=1, align=aligns[4], max_line_height=row_height)

                # Date
                x_after_type = x_after_loc + widths[4]
                pdf.set_xy(x_after_type, y_before)
                pdf.multi_cell(widths[5], max_h, cell_values[5], border=1, align=aligns[5], max_line_height=row_height)

                # Se placer à la ligne suivante
                pdf.set_y(y_before + max_h)

        # Générer le PDF dans un fichier temporaire
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            pdf_path = tmp.name
            pdf.output(pdf_path)

        # Envoyer le fichier PDF au client
        response = send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'liste_materiel_{datetime.now().strftime("%Y%m%d")}.pdf'
        )
        # Nettoyage après l'envoi (nécessaire sur certains systèmes)
        @response.call_on_close
        def cleanup_file():
            try:
                os.unlink(pdf_path)
            except Exception as e_clean:
                current_app.logger.error(f"Erreur lors du nettoyage du fichier PDF temporaire {pdf_path}: {e_clean}")
        return response

    except Exception as e:
        current_app.logger.error(f'Erreur lors de la génération du PDF de tous les articles: {e}', exc_info=True)
        flash(f'Erreur lors de la génération du PDF: {str(e)}', 'danger')
        return redirect(url_for('admin.items_list')) # Rediriger vers la liste des articles en cas d'erreur)
