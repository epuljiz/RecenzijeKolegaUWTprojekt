from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from datetime import datetime
from ..extensions import mongo, mail, limiter
from ..models import User
from . import auth_bp
from .forms import LoginForm, RegistrationForm
from .utils import generate_verification_token, send_verification_email

@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Provjeri postoji li korisnik
        if mongo.db.users.find_one({'email': form.email.data}):
            flash('Korisnik s ovom email adresom već postoji.', 'danger')
            return render_template('auth/register.html', form=form)
        
        # Kreiraj novog korisnika
        user_data = {
            'email': form.email.data,
            'name': form.name.data,
            'password': generate_password_hash(form.password.data),
            'faculty': form.faculty.data,
            'department': form.department.data,
            'role': 'user',
            'email_verified': True, # za verifikaciju mailom, postavi na false
            'date_created': datetime.utcnow()
        }
        
        result = mongo.db.users.insert_one(user_data)
        user = User(user_data)
        
        # Pokušaj slanje emaila, ali ako ne uspije, molim te aplikacija ne moj se srušiti već po 100ti put
        try:
            user_data['verification_token'] = generate_verification_token()
            mongo.db.users.update_one(
                {'_id': result.inserted_id},
                {'$set': {'verification_token': user_data['verification_token'], 'email_verified': False}}
            )
            user.verification_token = user_data['verification_token']
            send_verification_email(user)
            flash('Registracija uspješna! Provjerite email za verifikaciju.', 'success')
        except Exception as e:
            # Ako email ne radi, automatski verificiraj korisnika
            print(f"Email error: {e}")
            flash('Registracija uspješna! Automatski ste verificirani (email servis trenutno nedostupan).', 'success')
        
        login_user(user)
        return redirect(url_for('main.index'))
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user_data = mongo.db.users.find_one({'email': form.email.data})
        
        if user_data and check_password_hash(user_data['password'], form.password.data):
            # U dev, dopusti prijavu ne-verificiranim korisnicima
            if not user_data.get('email_verified', False) and current_app.config.get('DEBUG'):
                flash('Prijava uspješna! (Development mode: email verificiran automatski)', 'info')
                # Automatski verificiraj u developmentu
                mongo.db.users.update_one(
                    {'_id': user_data['_id']},
                    {'$set': {'email_verified': True}}
                )
            
            user = User(user_data)
            login_user(user)
            flash('Prijava uspješna!', 'success')
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Pogrešna email adresa ili lozinka.', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Odjava uspješna.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    user_data = mongo.db.users.find_one({'verification_token': token})
    
    if not user_data:
        flash('Verifikacijski token je nevažeći ili je istekao.', 'danger')
        return redirect(url_for('main.index'))
    
    # Ažuriraj korisnika kao verificiranog
    mongo.db.users.update_one(
        {'_id': user_data['_id']},
        {'$set': {'email_verified': True}, '$unset': {'verification_token': ''}}
    )
    
    flash('Email je uspješno verificiran! Sada se možete prijaviti.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/resend-verification')
@login_required
def resend_verification():
    if current_user.email_verified:
        flash('Vaš email je već verificiran.', 'info')
        return redirect(url_for('main.index'))
    
    # Generiraj novi token
    new_token = generate_verification_token()
    mongo.db.users.update_one(
        {'_id': ObjectId(current_user.id)},
        {'$set': {'verification_token': new_token}}
    )
    
    # Pošalji email
    try:
        send_verification_email(current_user)
        flash('Verifikacijski email je ponovno poslan.', 'success')
    except Exception as e:
        flash('Greška pri slanju verifikacijskog emaila.', 'danger')
    
    return redirect(url_for('main.index'))