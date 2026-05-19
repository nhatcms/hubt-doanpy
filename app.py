from flask import Flask, render_template, redirect, url_for, flash, request, Response
from extensions import db, login
from flask_login import current_user, login_user, logout_user, login_required
from config import Config
from datetime import datetime
from models import User, Category, Transaction
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import re

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

    # Calculate monthly income & expense for bar chart, starting from May
    now = datetime.utcnow()
    current_year = now.year
    current_month = now.month

    # Build list of months from May of current_year up to current_month
    months = []
    for m in range(5, current_month + 1):
        months.append((current_year, m))

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
                           bar_labels=bar_labels,
                           bar_income=bar_income,
                           bar_expense=bar_expense)

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
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        errors = []

        # Validate username
        if not username:
            errors.append('Username is required.')
        elif not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            errors.append('Username must be 3-20 characters and can only contain letters, numbers, and underscores.')

        # Validate email
        if not email:
            errors.append('Email is required.')
        elif not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            errors.append('Invalid email format.')

        # Validate password
        if not password:
            errors.append('Password is required.')
        else:
            if len(password) < 6:
                errors.append('Password must be at least 6 characters.')
            if ' ' in password:
                errors.append('Password must not contain spaces.')

        # Check for existing user
        if not errors and User.query.filter_by(username=username).first():
            errors.append('Username already exists.')
        if not errors and User.query.filter_by(email=email).first():
            errors.append('Email already registered.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('register.html', title='Register')

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register')

@app.route('/transactions')
@login_required
def transactions():
    from datetime import date, timedelta

    # --- Read filter query parameters ---
    date_from_str = request.args.get('date_from', '').strip()
    date_to_str = request.args.get('date_to', '').strip()
    type_filter = request.args.get('type', 'All')
    category_id = request.args.get('category_id', '').strip()
    amount_min_str = request.args.get('amount_min', '').strip()
    amount_max_str = request.args.get('amount_max', '').strip()
    note_search = request.args.get('note_search', '').strip()

    # --- Default date range: last 7 days ---
    today = date.today()
    if date_from_str:
        date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
    else:
        date_from = today - timedelta(days=7)
        date_from_str = date_from.strftime('%Y-%m-%d')

    if date_to_str:
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
    else:
        date_to = today
        date_to_str = date_to.strftime('%Y-%m-%d')

    # --- Build query with filters ---
    query = Transaction.query.filter_by(user_id=current_user.id).join(Category)

    # Date range
    query = query.filter(Transaction.date >= date_from, Transaction.date <= date_to)

    # Type filter (Income / Expense)
    if type_filter in ('Income', 'Expense'):
        query = query.filter(Category.type == type_filter)

    # Category filter
    if category_id:
        query = query.filter(Transaction.category_id == int(category_id))

    # Amount range filter
    if amount_min_str:
        query = query.filter(Transaction.amount >= float(amount_min_str))
    if amount_max_str:
        query = query.filter(Transaction.amount <= float(amount_max_str))

    # Note text search (case-insensitive)
    if note_search:
        query = query.filter(Transaction.note.ilike(f'%{note_search}%'))

    user_transactions = query.order_by(Transaction.date.desc()).all()
    categories = Category.query.all()

    return render_template('transactions.html',
                           title='Transactions',
                           transactions=user_transactions,
                           categories=categories,
                           date_from=date_from_str,
                           date_to=date_to_str,
                           type_filter=type_filter,
                           category_id=category_id,
                           amount_min=amount_min_str,
                           amount_max=amount_max_str,
                           note_search=note_search)

def register_font():
    """Register a Unicode-capable font for PDF. Falls back to Helvetica if no TTF found."""
    font_candidates = [
        # Common Vietnamese-supporting font names across platforms
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ]
    for path in font_candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("UnicodeFont", path))
                return "UnicodeFont"
            except Exception:
                continue
    return "Helvetica"

FONT_NAME = register_font()

def build_pdf(transactions, user_name):
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        topMargin=15*mm,
        bottomMargin=15*mm,
        leftMargin=15*mm,
        rightMargin=15*mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontName=FONT_NAME,
        fontSize=16,
        spaceAfter=6*mm,
        textColor=colors.HexColor("#18181b"),
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=9,
        spaceAfter=4*mm,
        textColor=colors.HexColor("#71717a"),
    )
    cell_style = ParagraphStyle(
        "Cell",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=8,
        leading=11,
        alignment=1,  # CENTER
    )
    cell_left = ParagraphStyle(
        "CellLeft", parent=cell_style, alignment=0
    )
    elements = []

    # Title row
    elements.append(Paragraph("Transaction Report", title_style))
    elements.append(
        Paragraph(
            f"User: {user_name} &nbsp;|&nbsp; "
            f"Total transactions: {len(transactions)} &nbsp;|&nbsp; "
            f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC",
            subtitle_style,
        )
    )
    elements.append(Spacer(1, 3*mm))

    # Table data
    header = ["Date", "Category", "Note", "Amount", "Type"]
    data = [header]

    total_income = 0.0
    total_expense = 0.0

    for txn in transactions:
        amt = txn.amount
        txn_type = txn.category.type
        if txn_type == "Income":
            total_income += amt
            amount_str = f"+${amt:,.2f}"
        else:
            total_expense += amt
            amount_str = f"-${amt:,.2f}"

        data.append([
            Paragraph(txn.date.strftime("%Y-%m-%d"), cell_style),
            Paragraph(f"{txn.category.name}", cell_style),
            Paragraph(txn.note or "—", cell_left),
            Paragraph(amount_str, cell_style),
            Paragraph(txn_type, cell_style),
        ])

    # Summary row
    balance = total_income - total_expense
    data.append([
        Paragraph("<b>Summary</b>", cell_style),
        Paragraph("", cell_style),
        Paragraph("", cell_style),
        Paragraph(
            f"Income: <font color='#15803d'>+${total_income:,.2f}</font><br/>"
            f"Expense: <font color='#dc2626'>-${total_expense:,.2f}</font><br/>"
            f"Balance: ${balance:,.2f}",
            ParagraphStyle("SummaryCell", parent=cell_style, alignment=1, fontSize=8, leading=13),
        ),
        Paragraph("", cell_style),
    ])

    col_widths = [55*mm, 45*mm, 65*mm, 45*mm, 40*mm]
    table = Table(data, colWidths=col_widths, repeatRows=1)

    table_style = TableStyle([
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#18181b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), FONT_NAME),
        ("FONTSIZE", (0, 0), (-1, 0), 8.5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        # Body
        ("FONTNAME", (0, 1), (-1, -1), FONT_NAME),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("TOPPADDING", (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -2), 0.5, colors.HexColor("#e4e4e7")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        # Summary row
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f4f4f5")),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor("#18181b")),
        # Zebra stripes
        *[
            (("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fafafa")))
            for i in range(2, len(data) - 1, 2)
        ],
    ])
    table.setStyle(table_style)

    elements.append(table)
    doc.build(elements)
    buf.seek(0)
    return buf


@app.route('/export_transactions_pdf')
@login_required
def export_transactions_pdf():
    user_transactions = (
        Transaction.query
        .filter_by(user_id=current_user.id)
        .order_by(Transaction.date.desc())
        .all()
    )

    if not user_transactions:
        flash("No transactions to export.", "info")
        return redirect(url_for("transactions"))

    pdf_buf = build_pdf(user_transactions, current_user.username)
    return Response(
        pdf_buf,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=transactions_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        },
    )


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

@app.route('/edit_transaction/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(id):
    txn = Transaction.query.get_or_404(id)
    if txn.user_id != current_user.id:
        flash('You do not have permission to edit this transaction.', 'error')
        return redirect(url_for('transactions'))
    
    if request.method == 'POST':
        txn.amount = float(request.form['amount'])
        txn.category_id = int(request.form['category_id'])
        txn.note = request.form['note']
        date_str = request.form['date']
        if date_str:
            txn.date = datetime.strptime(date_str, '%Y-%m-%d').date()
        db.session.commit()
        flash('Transaction updated successfully.', 'success')
        return redirect(url_for('transactions'))
    
    categories = Category.query.all()
    return render_template('edit_transaction.html', title='Edit Transaction', txn=txn, categories=categories)

@app.route('/delete_transaction/<int:id>', methods=['POST'])
@login_required
def delete_transaction(id):
    txn = Transaction.query.get_or_404(id)
    if txn.user_id != current_user.id:
        flash('You do not have permission to delete this transaction.', 'error')
        return redirect(url_for('transactions'))
    db.session.delete(txn)
    db.session.commit()
    flash('Transaction deleted successfully.', 'success')
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
    app.run(debug=True, host='0.0.0.0', port=5001)
