from flask import Flask, render_template, redirect, url_for, flash, request
from extensions import db, login
from flask_login import current_user, login_user, logout_user, login_required
from config import Config
from datetime import datetime
from models import User, Category, Transaction

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login.init_app(app)

@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    total_income = sum(t.amount for t in transactions if t.category.type == 'Income')
    total_expense = sum(t.amount for t in transactions if t.category.type == 'Expense')
    balance = total_income - total_expense
    
    # Calculate for doughnut chart
    expenses_by_cat = {}
    for t in transactions:
        if t.category.type == 'Expense':
            expenses_by_cat[t.category.name] = expenses_by_cat.get(t.category.name, 0) + t.amount

    return render_template('dashboard.html', 
                           title='Dashboard', 
                           total_income=total_income,
                           total_expense=total_expense,
                           balance=balance,
                           expenses_labels=list(expenses_by_cat.keys()),
                           expenses_data=list(expenses_by_cat.values()))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user is None or not user.check_password(request.form['password']):
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))
        login_user(user)
        return redirect(url_for('dashboard'))
    return render_template('login.html', title='Sign In')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        user = User(username=request.form['username'], email=request.form['email'])
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register')

@app.route('/transactions')
@login_required
def transactions():
    user_transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).all()
    categories = Category.query.all()
    return render_template('transactions.html', title='Transactions', transactions=user_transactions, categories=categories)

@app.route('/add_transaction', methods=['POST'])
@login_required
def add_transaction():
    amount = float(request.form['amount'])
    category_id = int(request.form['category_id'])
    note = request.form['note']
    date_str = request.form['date']
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.utcnow().date()
    
    txn = Transaction(user_id=current_user.id, category_id=category_id, amount=amount, note=note, date=date_obj)
    db.session.add(txn)
    db.session.commit()
    flash('Transaction added successfully.', 'success')
    return redirect(url_for('transactions'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not Category.query.first():
            categories = [
                Category(name='Lương', type='Income', icon='bi-cash-stack'),
                Category(name='Thưởng', type='Income', icon='bi-gift'),
                Category(name='Ăn uống', type='Expense', icon='bi-cup-hot'),
                Category(name='Di chuyển', type='Expense', icon='bi-car-front'),
                Category(name='Mua sắm', type='Expense', icon='bi-bag'),
            ]
            db.session.bulk_save_objects(categories)
            db.session.commit()
    app.run(debug=True)
