from flask import Blueprint

bp = Blueprint('new_study', __name__)

from app.new_study import routes
