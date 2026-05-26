from flask import Flask
from extensions import db, login
from config import Config
from models import Category

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    login.init_app(app)
    
    from routes import auth_bp, dashboard_bp, transactions_bp
    for bp in (auth_bp, dashboard_bp, transactions_bp):
        app.register_blueprint(bp)
    
    return app

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not Category.query.first():
            # Seed default categories
            db.session.bulk_save_objects([
                Category(name='Lương', type='Income', icon='bi-cash-stack'),
                Category(name='Thưởng', type='Income', icon='bi-gift'),
                Category(name='Ăn uống', type='Expense', icon='bi-cup-hot'),
                Category(name='Di chuyển', type='Expense', icon='bi-car-front'),
                Category(name='Mua sắm', type='Expense', icon='bi-bag'),
            ])
            db.session.commit()
    app.run(debug=True, host='0.0.0.0', port=5001)
