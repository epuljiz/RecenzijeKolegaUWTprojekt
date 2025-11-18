from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from flask_principal import Permission, RoleNeed
from bson import ObjectId
from datetime import datetime
import bleach
from . import admin_bp
from ..extensions import mongo
from ..models import User
from ..auth.forms import RegistrationForm

admin_permission = Permission(RoleNeed('admin'))

@admin_bp.before_request
@login_required
def restrict_admin():
    """Restrict admin routes to admin users only"""
    if not admin_permission.can():
        abort(403)

@admin_bp.route('/')
def dashboard():
    """Admin dashboard"""
    # Statistike
    total_users = mongo.db.users.count_documents({})
    total_reviews = mongo.db.reviews.count_documents({})
    total_admins = mongo.db.users.count_documents({'role': 'admin'})

    # Zadnje aktivnosti
    recent_users = list(mongo.db.users.find().sort(
        'date_created', -1).limit(5))
    recent_reviews = list(mongo.db.reviews.find().sort(
        'date_created', -1).limit(5))

    # Pripremi podatke
    for review in recent_reviews:
        reviewer = mongo.db.users.find_one({'_id': review['reviewer_user_id']})
        reviewed_user = mongo.db.users.find_one(
            {'_id': review['reviewed_user_id']})
        review['reviewer_name'] = reviewer['name'] if reviewer else 'Nepoznat'
        review['reviewed_user_name'] = reviewed_user['name'] if reviewed_user else 'Nepoznat'
        review['formatted_date'] = review['date_created'].strftime('%d.%m.%Y.')

    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           total_reviews=total_reviews,
                           total_admins=total_admins,
                           recent_users=recent_users,
                           recent_reviews=recent_reviews)


@admin_bp.route('/users')
def users():
    """List all users"""
    page = request.args.get('page', 1, type=int)
    per_page = 15
    skip = (page - 1) * per_page

    search_query = request.args.get('search', '')
    role_filter = request.args.get('role', '')

    query = {}
    if search_query:
        query['$or'] = [
            {'name': {'$regex': search_query, '$options': 'i'}},
            {'email': {'$regex': search_query, '$options': 'i'}}
        ]

    if role_filter:
        query['role'] = role_filter

    users_list = list(mongo.db.users.find(query)
                      .sort('date_created', -1)
                      .skip(skip)
                      .limit(per_page))

    total_users = mongo.db.users.count_documents(query)
    total_pages = (total_users + per_page - 1) // per_page

    # Dohvati statistiku za svakog korisnika
    for user in users_list:
        reviews_received = mongo.db.reviews.count_documents(
            {'reviewed_user_id': user['_id']})
        reviews_written = mongo.db.reviews.count_documents(
            {'reviewer_user_id': user['_id']})
        user['reviews_received'] = reviews_received
        user['reviews_written'] = reviews_written

    return render_template('admin/users.html',
                           users=users_list,
                           page=page,
                           total_pages=total_pages,
                           search_query=search_query,
                           role_filter=role_filter)


@admin_bp.route('/users/create', methods=['GET', 'POST'])
def create_user():
    """Create new user"""
    form = RegistrationForm()

    if form.validate_on_submit():
        # Provjeri postoji li korisnik
        if mongo.db.users.find_one({'email': form.email.data}):
            flash('Korisnik s ovom email adresom već postoji.', 'danger')
            return render_template('admin/create_user.html', form=form)

        # Kreiraj novog korisnika
        user_data = {
            'email': form.email.data,
            'name': form.name.data,
            'password': generate_password_hash(form.password.data),
            'faculty': form.faculty.data,
            'department': form.department.data,
            'role': 'user',
            'email_verified': True,  # korisnik kreiran od admina je odmah verificiran
            'date_created': datetime.utcnow()
        }

        mongo.db.users.insert_one(user_data)
        flash('Korisnik uspješno kreiran!', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/create_user.html', form=form)


@admin_bp.route('/users/<user_id>/edit', methods=['GET', 'POST'])
def edit_user(user_id):
    """Edit user"""
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})

    if not user:
        abort(404)

    # Spriječi admina da uredi samog sebe (da netko ne bi mijenjao permisiju admina)
    if user['_id'] == ObjectId(current_user.id):
        flash('Ne možete uređivati vlastiti profil preko admin panela.', 'warning')
        return redirect(url_for('admin.users'))

    if request.method == 'POST':
        update_data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'faculty': request.form.get('faculty'),
            'department': request.form.get('department'),
            'role': request.form.get('role'),
            'email_verified': request.form.get('email_verified') == 'on'
        }

        # Ažuriraj lozinku samo ako je unesena nova
        new_password = request.form.get('password')
        if new_password:
            update_data['password'] = generate_password_hash(new_password)

        mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': update_data}
        )

        flash('Korisnik uspješno ažuriran!', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/edit_user.html', user=user)


@admin_bp.route('/users/<user_id>/delete', methods=['POST'])
def delete_user(user_id):
    """Delete user"""
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})

    if not user:
        abort(404)

    # Spriječi brisanje samog sebe
    if user['_id'] == ObjectId(current_user.id):
        flash('Ne možete obrisati vlastiti profil.', 'danger')
        return redirect(url_for('admin.users'))

    # Obriši sve recenzije povezane s korisnikom
    mongo.db.reviews.delete_many({
        '$or': [
            {'reviewer_user_id': ObjectId(user_id)},
            {'reviewed_user_id': ObjectId(user_id)}
        ]
    })

    # Obriši korisnika
    mongo.db.users.delete_one({'_id': ObjectId(user_id)})

    flash('Korisnik i sve povezane recenzije uspješno obrisani!', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/reviews')
def manage_reviews():
    """Manage all reviews"""
    page = request.args.get('page', 1, type=int)
    per_page = 15
    skip = (page - 1) * per_page

    reviews_list = list(mongo.db.reviews.find()
                        .sort('date_created', -1)
                        .skip(skip)
                        .limit(per_page))

    total_reviews = mongo.db.reviews.count_documents({})
    total_pages = (total_reviews + per_page - 1) // per_page

    # Pripremi podatke
    for review in reviews_list:
        reviewer = mongo.db.users.find_one({'_id': review['reviewer_user_id']})
        reviewed_user = mongo.db.users.find_one(
            {'_id': review['reviewed_user_id']})
        review['reviewer_name'] = reviewer['name'] if reviewer else 'Nepoznat'
        review['reviewed_user_name'] = reviewed_user['name'] if reviewed_user else 'Nepoznat'
        review['formatted_date'] = review['date_created'].strftime(
            '%d.%m.%Y. %H:%M')

    return render_template('admin/reviews.html',
                           reviews=reviews_list,
                           page=page,
                           total_pages=total_pages)


@admin_bp.route('/reviews/<review_id>/delete', methods=['POST'])
def delete_review_admin(review_id):
    """Delete review (admin)"""
    review = mongo.db.reviews.find_one({'_id': ObjectId(review_id)})

    if not review:
        abort(404)

    mongo.db.reviews.delete_one({'_id': ObjectId(review_id)})
    flash('Recenzija uspješno obrisana!', 'success')
    return redirect(url_for('admin.manage_reviews'))
