from flask import render_template, redirect, url_for, flash, request, Response
from flask_login import current_user, login_required
from extensions import db
from models import Category, Transaction
from datetime import datetime, date, timedelta
from pdf_generator import build_pdf
from routes import transactions_bp


@transactions_bp.route('/transactions')
@login_required
def transactions():
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


@transactions_bp.route('/add_transaction', methods=['POST'])
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
    return redirect(url_for('transactions.transactions'))


@transactions_bp.route('/edit_transaction/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(id):
    txn = Transaction.query.get_or_404(id)
    if txn.user_id != current_user.id:
        flash('You do not have permission to edit this transaction.', 'error')
        return redirect(url_for('transactions.transactions'))

    if request.method == 'POST':
        txn.amount = float(request.form['amount'])
        txn.category_id = int(request.form['category_id'])
        txn.note = request.form['note']
        date_str = request.form['date']
        if date_str:
            txn.date = datetime.strptime(date_str, '%Y-%m-%d').date()
        db.session.commit()
        flash('Transaction updated successfully.', 'success')
        return redirect(url_for('transactions.transactions'))

    categories = Category.query.all()
    return render_template('edit_transaction.html', title='Edit Transaction', txn=txn, categories=categories)


@transactions_bp.route('/delete_transaction/<int:id>', methods=['POST'])
@login_required
def delete_transaction(id):
    txn = Transaction.query.get_or_404(id)
    if txn.user_id != current_user.id:
        flash('You do not have permission to delete this transaction.', 'error')
        return redirect(url_for('transactions.transactions'))
    db.session.delete(txn)
    db.session.commit()
    flash('Transaction deleted successfully.', 'success')
    return redirect(url_for('transactions.transactions'))


@transactions_bp.route('/export_transactions_pdf')
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
        return redirect(url_for("transactions.transactions"))

    pdf_buf = build_pdf(user_transactions, current_user.username)
    return Response(
        pdf_buf,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=transactions_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        },
    )
