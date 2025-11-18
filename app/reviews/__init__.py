from flask import Blueprint

reviews_bp = Blueprint('reviews', __name__, template_folder='templates')

from . import routes