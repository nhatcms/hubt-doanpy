from flask import Blueprint

auth_bp = Blueprint('auth', __name__)
dashboard_bp = Blueprint('dashboard', __name__)
transactions_bp = Blueprint('transactions', __name__)

from routes import auth, dashboard, transactions
