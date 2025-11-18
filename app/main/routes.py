from flask import render_template, current_app
from . import main_bp
from ..extensions import mongo
from bson import ObjectId

@main_bp.route('/')
def index():
    # Dohvati nove recenzije za prikaz na početnoj stranici
    recent_reviews = list(mongo.db.reviews.find().sort('date_created', -1).limit(3))
    
    # Pripremi podatke za prikaz
    for review in recent_reviews:
        reviewed_user = mongo.db.users.find_one({'_id': review['reviewed_user_id']})
        reviewer_user = mongo.db.users.find_one({'_id': review['reviewer_user_id']})
        
        review['reviewed_user_name'] = reviewed_user['name'] if reviewed_user else 'Nepoznat korisnik'
        review['reviewer_name'] = reviewer_user['name'] if reviewer_user else 'Nepoznat korisnik'
        review['formatted_date'] = review['date_created'].strftime('%d.%m.%Y.')
    
    # Dohvati broj korisnika i recenzija za statistiku
    users_count = mongo.db.users.count_documents({})
    reviews_count = mongo.db.reviews.count_documents({})
    
    return render_template('main/index.html', 
                         recent_reviews=recent_reviews,
                         users_count=users_count,
                         reviews_count=reviews_count)

@main_bp.route('/about')
def about_page():
    return render_template('main/about.html')

@main_bp.route('/contact')
def contact_page():
    return render_template('main/contact.html')

# Error handlers
@main_bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@main_bp.app_errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403

@main_bp.app_errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

@main_bp.app_errorhandler(429)
def too_many_requests(error):
    return render_template('errors/429.html'), 429