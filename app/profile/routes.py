from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import mongo

from . import profile_bp

@profile_bp.route('/profile')
@login_required
def profile():
    # Dohvati korisnikove recenzije
    user_reviews = list(mongo.db.reviews.find({'reviewed_user_id': ObjectId(current_user.id)}).sort('date_created', -1))
    
    # Izračunaj prosječnu ocjenu
    total_rating = sum(review['rating'] for review in user_reviews)
    avg_rating = total_rating / len(user_reviews) if user_reviews else 0
    
    # Dohvati recenzije koje je korisnik napisao
    reviews_written = list(mongo.db.reviews.find({'reviewer_user_id': ObjectId(current_user.id)}).sort('date_created', -1).limit(5))
    
    # Pripremi podatke za recenzije
    for review in reviews_written:
        reviewed_user = mongo.db.users.find_one({'_id': review['reviewed_user_id']})
        review['reviewed_user_name'] = reviewed_user['name'] if reviewed_user else 'Nepoznat korisnik'
        review['formatted_date'] = review['date_created'].strftime('%d.%m.%Y. %H:%M')
    
    return render_template('profile/profile.html', 
                         reviews=user_reviews, 
                         avg_rating=avg_rating,
                         reviews_written=reviews_written)

@profile_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        name = request.form.get('name')
        faculty = request.form.get('faculty')
        department = request.form.get('department')
        
        # Validacija
        if not name or len(name.strip()) < 2:
            flash('Ime mora imati najmanje 2 znaka.', 'danger')
            return render_template('profile/edit_profile.html')
        
        # Ažuriraj korisnika
        mongo.db.users.update_one(
            {'_id': ObjectId(current_user.id)},
            {'$set': {
                'name': name.strip(),
                'faculty': faculty,
                'department': department
            }}
        )
        
        flash('Profil uspješno ažuriran!', 'success')
        return redirect(url_for('profile.profile'))
    
    # GET request - prikaži formu s trenutnim podacima
    user_data = mongo.db.users.find_one({'_id': ObjectId(current_user.id)})
    return render_template('profile/edit_profile.html', user=user_data)

@profile_bp.route('/profile/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # Validacija
    if not current_password or not new_password:
        flash('Sva polja su obavezna.', 'danger')
        return redirect(url_for('profile.profile'))
    
    if new_password != confirm_password:
        flash('Nove lozinke se ne podudaraju.', 'danger')
        return redirect(url_for('profile.profile'))
    
    if len(new_password) < 6:
        flash('Nova lozinka mora imati najmanje 6 znakova.', 'danger')
        return redirect(url_for('profile.profile'))
    
    # Provjeri trenutnu lozinku
    user_data = mongo.db.users.find_one({'_id': ObjectId(current_user.id)})
    if not check_password_hash(user_data['password'], current_password):
        flash('Trenutna lozinka nije točna.', 'danger')
        return redirect(url_for('profile.profile'))
    
    # Ažuriraj lozinku
    mongo.db.users.update_one(
        {'_id': ObjectId(current_user.id)},
        {'$set': {'password': generate_password_hash(new_password)}}
    )
    
    flash('Lozinka uspješno promijenjena!', 'success')
    return redirect(url_for('profile.profile'))