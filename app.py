from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_pymongo import PyMongo
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/recenzijska_platforma')

mongo = PyMongo(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.email = user_data['email']
        self.name = user_data['name']
        self.faculty = user_data.get('faculty', '')
        self.department = user_data.get('department', '')

@login_manager.user_loader
def load_user(user_id):
    user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None

# Routes
@app.route('/')
def index():
    # Dohvati zadnje recenzije za prikaz na početnoj stranici
    recent_reviews = list(mongo.db.reviews.find().sort('date_created', -1).limit(3))
    
    # Pripremi podatke za prikaz
    for review in recent_reviews:
        reviewed_user = mongo.db.users.find_one({'_id': review['reviewed_user_id']})
        review['reviewed_user_name'] = reviewed_user['name'] if reviewed_user else 'Nepoznat korisnik'
        review['formatted_date'] = review['date_created'].strftime('%d.%m.%Y.')
    
    return render_template('index.html', recent_reviews=recent_reviews)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        faculty = request.form.get('faculty')
        department = request.form.get('department')
        
        # Provjeri postoji li korisnik
        if mongo.db.users.find_one({'email': email}):
            flash('Korisnik s ovom email adresom već postoji.', 'danger')
            return redirect(url_for('register'))
        
        # Kreiraj novog korisnika
        user_data = {
            'email': email,
            'name': name,
            'password': generate_password_hash(password),
            'faculty': faculty,
            'department': department,
            'date_created': datetime.utcnow()
        }
        
        result = mongo.db.users.insert_one(user_data)
        user = User(user_data)
        login_user(user)
        
        flash('Registracija uspješna!', 'success')
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_data = mongo.db.users.find_one({'email': email})
        if user_data and check_password_hash(user_data['password'], password):
            user = User(user_data)
            login_user(user)
            flash('Prijava uspješna!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Pogrešna email adresa ili lozinka.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Odjava uspješna.', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    # Dohvati korisnikove recenzije
    user_reviews = list(mongo.db.reviews.find({'reviewed_user_id': ObjectId(current_user.id)}))
    
    # Izračunaj prosječnu ocjenu
    total_rating = sum(review['rating'] for review in user_reviews)
    avg_rating = total_rating / len(user_reviews) if user_reviews else 0
    
    return render_template('profile.html', reviews=user_reviews, avg_rating=avg_rating)

@app.route('/add_review', methods=['GET', 'POST'])
@login_required
def add_review():
    if request.method == 'POST':
        reviewed_user_email = request.form.get('reviewed_user_email')
        rating = int(request.form.get('rating'))
        comment = request.form.get('comment')
        project_type = request.form.get('project_type')
        
        # Pronađi korisnika koji se recenzira
        reviewed_user = mongo.db.users.find_one({'email': reviewed_user_email})
        if not reviewed_user:
            flash('Korisnik s ovom email adresom ne postoji.', 'danger')
            return redirect(url_for('add_review'))
        
        # Provjeri da li je korisnik pokušao ocijeniti samog sebe
        if reviewed_user['_id'] == ObjectId(current_user.id):
            flash('Ne možete ocijeniti samog sebe.', 'danger')
            return redirect(url_for('add_review'))
        
        # Spremi recenziju
        review_data = {
            'reviewer_user_id': ObjectId(current_user.id),
            'reviewed_user_id': reviewed_user['_id'],
            'rating': rating,
            'comment': comment,
            'project_type': project_type,
            'date_created': datetime.utcnow()
        }
        
        mongo.db.reviews.insert_one(review_data)
        flash('Recenzija uspješno dodana!', 'success')
        return redirect(url_for('reviews'))
    
    return render_template('add_review.html')

@app.route('/reviews')
def reviews():
    # Dohvati sve recenzije s podacima o korisnicima
    all_reviews = list(mongo.db.reviews.find().sort('date_created', -1))
    
    for review in all_reviews:
        reviewer = mongo.db.users.find_one({'_id': review['reviewer_user_id']})
        reviewed_user = mongo.db.users.find_one({'_id': review['reviewed_user_id']})
        
        review['reviewer_name'] = reviewer['name'] if reviewer else 'Nepoznat korisnik'
        review['reviewed_user_name'] = reviewed_user['name'] if reviewed_user else 'Nepoznat korisnik'
        review['formatted_date'] = review['date_created'].strftime('%d.%m.%Y. %H:%M')
    
    return render_template('reviews.html', reviews=all_reviews)

@app.route('/api/users/search')
def search_users():
    query = request.args.get('q', '')
    if query:
        users = list(mongo.db.users.find({
            '$or': [
                {'name': {'$regex': query, '$options': 'i'}},
                {'email': {'$regex': query, '$options': 'i'}}
            ]
        }).limit(10))
        
        users_data = [{
            'id': str(user['_id']),
            'name': user['name'],
            'email': user['email'],
            'faculty': user.get('faculty', ''),
            'department': user.get('department', '')
        } for user in users]
        
        return jsonify(users_data)
    
    return jsonify([])

if __name__ == '__main__':
    app.run(debug=True)