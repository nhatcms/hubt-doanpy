from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_user, logout_user, login_required
from extensions import db
from models import User
from routes import auth_bp
import re


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user is None or not user.check_password(request.form['password']):
            flash('Invalid username or password', 'error')
            return redirect(url_for('auth.login'))
        login_user(user)
        return redirect(url_for('dashboard.dashboard'))
    return render_template('login.html', title='Sign In')


@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
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
        return redirect(url_for('auth.login'))
    return render_template('register.html', title='Register')


@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    data = request.get_json()
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')

    errors = []

    # Validate current password
    if not current_user.check_password(current_password):
        errors.append('Current password is incorrect.')

    # Validate new password (same rules as registration)
    if not new_password:
        errors.append('New password is required.')
    else:
        if len(new_password) < 6:
            errors.append('Password must be at least 6 characters.')
        if ' ' in new_password:
            errors.append('Password must not contain spaces.')

    # Validate confirm password
    if new_password != confirm_password:
        errors.append('New password and confirm password do not match.')

    if errors:
        return {'success': False, 'errors': errors}, 400

    # Update password
    current_user.set_password(new_password)
    db.session.commit()

    logout_user()
    return {'success': True, 'message': 'Password changed successfully. Please sign in again.'}
