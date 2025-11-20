from flask import Flask
from .extensions import mongo, login_manager, mail, principal, limiter
from config import config
from datetime import datetime
from werkzeug.security import generate_password_hash

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Inicijalizacija ekstenzija
    mongo.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    principal.init_app(app)
    limiter.init_app(app)
    
    # Konfiguracija login managera
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Molimo prijavite se za pristup ovoj stranici.'
    login_manager.login_message_category = 'warning'
    
    # Korisnički loader callback
    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        try:
            from bson import ObjectId
            user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
            if user_data:
                return User(user_data)
            return None
        except Exception as e:
            print(f"⚠️ Error loading user: {e}")
            return None
    
    # Registracija blueprintova
    from .auth import auth_bp
    from .main import main_bp
    from .reviews import reviews_bp
    from .admin import admin_bp
    from .profile import profile_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(profile_bp)
    
    # Kreiranje admin korisnika pri prvom pokretanju
    with app.app_context():
        try:
            create_admin_user()
        except Exception as e:
            # Ne prekida aplikaciju ako kreiranje admina fejla
            print(f"⚠️ Admin user creation skipped: {e}")
    
    return app

def create_admin_user():
    from bson import ObjectId
    
    try:
        # Test MongoDB veze
        mongo.db.command('ping')
        print("✅ MongoDB connection successful")
        
        admin_email = 'admin@kolegarecenzije.hr'
        admin_exists = mongo.db.users.find_one({'email': admin_email})
        
        if not admin_exists:
            admin_data = {
                'email': admin_email,
                'name': 'Administrator',
                'password': generate_password_hash('admin123'),
                'role': 'admin',
                'email_verified': True,
                'date_created': datetime.utcnow()
            }
            mongo.db.users.insert_one(admin_data)
            print("✅ Admin user created: admin@kolegarecenzije.hr / admin123")
        else:
            print("✅ Admin user already exists")
            
    except Exception as e:
        print(f"⚠️ Could not create admin user: {e}")
        # NE prekida aplikaciju ako kreiranje admina fejla

def create_admin_user():
    from bson import ObjectId
    
    admin_email = 'admin@kolegarecenzije.hr'
    admin_exists = mongo.db.users.find_one({'email': admin_email})
    
    if not admin_exists:
        admin_data = {
            'email': admin_email,
            'name': 'Administrator',
            'password': generate_password_hash('admin123'),
            'role': 'admin',
            'email_verified': True,
            'date_created': datetime.utcnow()
        }
        mongo.db.users.insert_one(admin_data)
        print("Admin user created: admin@kolegarecenzije.hr / 1admin1")