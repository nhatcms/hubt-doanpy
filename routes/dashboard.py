from flask import render_template
from flask_login import current_user, login_required
from models import Transaction
from datetime import datetime
from routes import dashboard_bp


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
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

    # Calculate for income pie chart
    income_by_cat = {}
    for t in transactions:
        if t.category.type == 'Income':
            income_by_cat[t.category.name] = income_by_cat.get(t.category.name, 0) + t.amount

    # Calculate monthly income & expense for bar chart, show all 12 months of current year
    now = datetime.utcnow()
    current_year = now.year

    # Build list of all 12 months for current year
    months = [(current_year, month) for month in range(1, 13)]  # Months 1-12 for current year

    # Group transactions by (year, month)
    monthly_income = {}
    monthly_expense = {}
    for t in transactions:
        key = (t.date.year, t.date.month)
        if t.category.type == 'Income':
            monthly_income[key] = monthly_income.get(key, 0) + t.amount
        else:
            monthly_expense[key] = monthly_expense.get(key, 0) + t.amount

    # Build labels (Vietnamese month names) and data arrays
    month_names = ['', 'Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5',
                   'Tháng 6', 'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10',
                   'Tháng 11', 'Tháng 12']
    bar_labels = []
    bar_income = []
    bar_expense = []
    for yr, m in months:
        bar_labels.append(f'{month_names[m]} {yr}')
        bar_income.append(round(monthly_income.get((yr, m), 0), 2))
        bar_expense.append(round(monthly_expense.get((yr, m), 0), 2))

    return render_template('dashboard.html',
                           title='Dashboard',
                           total_income=total_income,
                           total_expense=total_expense,
                           balance=balance,
                           expenses_labels=list(expenses_by_cat.keys()),
                           expenses_data=list(expenses_by_cat.values()),
                           income_labels=list(income_by_cat.keys()),
                           income_data=list(income_by_cat.values()),
                           bar_labels=bar_labels,
                           bar_income=bar_income,
                           bar_expense=bar_expense)
