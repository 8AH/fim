from flask import Blueprint, render_template, request, redirect, url_for, flash
from src.models import db
from src.models.supplier import Supplier

supplier_bp = Blueprint('supplier', __name__, url_prefix='/admin/suppliers')

@supplier_bp.route('/')
def supplier_list():
    search_term = request.args.get('search', '').strip()
    query = db.session.query(Supplier)
    if search_term:
        query = query.filter(Supplier.name.ilike(f'%{search_term}%'))
    suppliers = query.order_by(Supplier.name).all()
    return render_template('admin/supplier_list.html', suppliers=suppliers, search_term=search_term)

@supplier_bp.route('/add', methods=['GET', 'POST'])
def add_supplier():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        site = request.form.get('site', '').strip() or None
        mail = request.form.get('mail', '').strip() or None
        comment = request.form.get('comment', '').strip() or None
        if not name:
            flash("Le nom du fournisseur est requis.", "danger")
            return render_template('admin/add_supplier.html', name=name, site=site, mail=mail, comment=comment)
        if db.session.query(Supplier).filter_by(name=name).first():
            flash("Ce fournisseur existe déjà.", "warning")
            return render_template('admin/add_supplier.html', name=name, site=site, mail=mail, comment=comment)
        if mail and db.session.query(Supplier).filter_by(mail=mail).first():
            flash("Cet email est déjà utilisé par un autre fournisseur.", "warning")
            return render_template('admin/add_supplier.html', name=name, site=site, mail=mail, comment=comment)
        if site and db.session.query(Supplier).filter_by(site=site).first():
            flash("Ce site web est déjà utilisé par un autre fournisseur.", "warning")
            return render_template('admin/add_supplier.html', name=name, site=site, mail=mail, comment=comment)
        new_supplier = Supplier(name=name, site=site, mail=mail, comment=comment)
        db.session.add(new_supplier)
        db.session.commit()
        flash("Fournisseur ajouté avec succès.", "success")
        return redirect(url_for('supplier.supplier_list'))
    return render_template('admin/add_supplier.html')

@supplier_bp.route('/edit/<int:supplier_id>', methods=['GET', 'POST'])
def edit_supplier(supplier_id):
    supplier = db.session.get(Supplier, supplier_id)
    if not supplier:
        flash("Fournisseur non trouvé.", "danger")
        return redirect(url_for('supplier.supplier_list'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        site = request.form.get('site', '').strip() or None
        mail = request.form.get('mail', '').strip() or None
        comment = request.form.get('comment', '').strip() or None
        if not name:
            flash("Le nom du fournisseur est requis.", "danger")
            return render_template('admin/edit_supplier.html', supplier=supplier)
        if db.session.query(Supplier).filter(Supplier.name == name, Supplier.id != supplier_id).first():
            flash("Un autre fournisseur porte déjà ce nom.", "warning")
            return render_template('admin/edit_supplier.html', supplier=supplier)
        if mail and db.session.query(Supplier).filter(Supplier.mail == mail, Supplier.id != supplier_id).first():
            flash("Un autre fournisseur utilise déjà cet email.", "warning")
            return render_template('admin/edit_supplier.html', supplier=supplier)
        if site and db.session.query(Supplier).filter(Supplier.site == site, Supplier.id != supplier_id).first():
            flash("Un autre fournisseur utilise déjà ce site web.", "warning")
            return render_template('admin/edit_supplier.html', supplier=supplier)
        supplier.name = name
        supplier.site = site
        supplier.mail = mail
        supplier.comment = comment
        db.session.commit()
        flash("Fournisseur modifié avec succès.", "success")
        return redirect(url_for('supplier.supplier_list'))
    return render_template('admin/edit_supplier.html', supplier=supplier)

@supplier_bp.route('/delete/<int:supplier_id>', methods=['POST'])
def delete_supplier(supplier_id):
    supplier = db.session.get(Supplier, supplier_id)
    if not supplier:
        flash("Fournisseur non trouvé.", "danger")
        return redirect(url_for('supplier.supplier_list'))
    if supplier.items:
        flash("Impossible de supprimer un fournisseur lié à des articles.", "danger")
        return redirect(url_for('supplier.supplier_list'))
    db.session.delete(supplier)
    db.session.commit()
    flash("Fournisseur supprimé avec succès.", "success")
    return redirect(url_for('supplier.supplier_list'))
