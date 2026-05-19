from extensions import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(256))
    transactions = db.relationship('Transaction', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    type = db.Column(db.String(20)) # 'Income' or 'Expense'
    icon = db.Column(db.String(64)) # Bootstrap icon name
    transactions = db.relationship('Transaction', backref='category', lazy='dynamic')

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    amount = db.Column(db.Float)
    note = db.Column(db.String(200))
    date = db.Column(db.Date, index=True, default=datetime.utcnow().date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
