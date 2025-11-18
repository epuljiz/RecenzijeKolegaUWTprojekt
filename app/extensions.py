from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_mail import Mail
from flask_principal import Principal
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Inicijaliziraj ekstenzije
mongo = PyMongo()
login_manager = LoginManager()
mail = Mail()
principal = Principal()
limiter = Limiter(key_func=get_remote_address)
